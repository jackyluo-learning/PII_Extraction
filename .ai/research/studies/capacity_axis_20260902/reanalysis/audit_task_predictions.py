"""Recover task-level observations from already archived, checksummed sources."""
from pathlib import Path
import hashlib
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[5]
STUDY = ROOT / '.ai/research/studies/capacity_axis_20260902'
OUT = STUDY / 'reanalysis'


def main():
    ledger = json.loads((STUDY / 'results.json').read_text())
    recovered = {x['path']: x for x in json.loads((OUT / 'recovery_manifest.json').read_text())}

    def checked(relative):
        path = ROOT / relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == recovered[relative]['sha256'], relative
        return path, {'path': relative, 'sha256': digest}

    path, source = checked('artifacts/capacity_axis_20260902/recovered_colab/models/gpt2/train_meta.json')
    meta = json.loads(path.read_text())
    losses = meta['pii_eval_losses']
    training = {
        'source': source,
        'scope': 'Recovered Colab training metadata; not proof of the executed Cheaha checkpoint identity.',
        'pii_eval_losses': losses,
        'decreases_each_epoch': all(b < a for a, b in zip(losses, losses[1:])),
        'near_zero_threshold_preregistered': None,
        'interpretation': 'PII eval loss decreases. The record does not support the near-zero wording or prove memorization.',
    }
    costs = []
    for run in ledger['runs']:
        if not run.get('source_stem', '').startswith('e3a_cost__'):
            continue
        artifact = next(x for x in run['artifacts'] if x.get('evidence_kind') == 'raw_attempts')
        path, source = checked(artifact['path'])
        assert source['sha256'] == artifact['sha256']
        df = pd.read_parquet(path)
        assert df.capacity_k.nunique() == 1
        costs.append({
            'source': source, 'run_id': run['run_id'], 'k': int(df.capacity_k.iloc[0]),
            'n_attempts': len(df), 'mean_attempt_seconds': float(df.wallclock_s.mean()),
            'total_attempt_seconds': float(df.wallclock_s.sum()),
            'mean_steps_run': float(df.steps_run.mean()),
        })
    assert sorted(x['k'] for x in costs) == [1, 20, 64]
    notebook_path = ROOT / 'colab/phase0_pilot.ipynb'
    notebook = json.loads(notebook_path.read_text())
    formula_source = ''.join(notebook['cells'][17]['source'])
    assert 'linear = (k+10)/30' in formula_source and 'linear*1.25' in formula_source
    mean_by_k = {x['k']: x['mean_attempt_seconds'] for x in costs}
    measured_ratio = mean_by_k[64] / mean_by_k[20]
    linear_ratio = (64 + 10) / (20 + 10)
    cost_comparison = {
        'formula_source': {
            'path': str(notebook_path.relative_to(ROOT)),
            'sha256': hashlib.sha256(notebook_path.read_bytes()).hexdigest(),
            'cell_index_zero_based': 17,
            'scope': 'Archived notebook formula; does not prove a pre-result statistical test was preregistered.',
        },
        'formula': '(mean_wallclock_k64 / mean_wallclock_k20) / ((64 + 10) / (20 + 10))',
        'measured_k64_over_k20': measured_ratio,
        'linear_k64_over_k20_T10': linear_ratio,
        'observed_over_linear': measured_ratio / linear_ratio,
        'notebook_overhead_flag_threshold': 1.25,
        'exceeds_notebook_flag': measured_ratio > linear_ratio * 1.25,
        'candidate_count_verified': False,
    }
    ledger['reanalysis']['task_prediction_evidence'] = {
        'training': training,
        'cost_pilot': sorted(costs, key=lambda x: x['k']),
        'cost_comparison': cost_comparison,
        'cost_scope': 'Colab cost pilots only, dirty manifests. Mean wallclock over recorded attacks with different actual early stopping. The notebook T=10 comparison is not a fixed-step complexity test; per-step candidate count is not inferred from timings.',
    }
    (STUDY / 'results.json').write_text(json.dumps(ledger, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    print(json.dumps(ledger['reanalysis']['task_prediction_evidence'], indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
