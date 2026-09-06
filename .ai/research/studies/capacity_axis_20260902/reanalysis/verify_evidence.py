"""Verify raw evidence, result/table agreement and explicitly incomplete schemas."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import re
import sys

import jsonschema
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[5]
STUDY = ROOT / '.ai/research/studies/capacity_axis_20260902'
OUT = STUDY / 'reanalysis'
ART = ROOT / 'artifacts/capacity_axis_20260902'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def check_file(item):
    path = ROOT / item['path']
    assert path.is_file(), path
    assert sha(path) == item['sha256'], path
    assert path.stat().st_size == item['bytes'], path
    return path


def main():
    ledger = read(STUDY / 'results.json')
    runs = {r['run_id']: r for r in ledger['runs']}
    assert len(runs) == len(ledger['runs']) == 52
    main_ids = ledger['reanalysis']['analysis_run_ids']
    assert len(main_ids) == len(set(main_ids)) == 42
    R = ledger['reanalysis']['estimates']
    assert R == read(OUT / 'recomputed_results.json')
    assert R['n_boot'] == 10000 and R['bootstrap_seed'] == 20240601
    checked = set()
    frames = []
    for run in ledger['runs']:
        if not run.get('source_scope'):
            assert run['excluded'] is True
            continue
        cfg = run['config']
        assert 'seed' not in cfg['shard']
        digest = hashlib.sha256(json.dumps(cfg, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        assert digest == run['config_hash']
        assert run['run_id'].endswith(f"__{digest[:8]}__s{run['seed']}")
        for item in run['artifacts']:
            path = check_file(item)
            checked.add(str(path.relative_to(ROOT)))
            if item.get('evidence_kind') == 'raw_attempts':
                df = pd.read_parquet(path)
                for arm, group in df.groupby('target_membership', observed=True):
                    m = run['arm_metrics'][arm]
                    assert int(group.exact_match.sum()) == m['hits']
                    assert len(group) == m['attempts']
                    assert np.isclose(group.wallclock_s.sum(), m['attempt_wallclock_s'])
                if run['run_id'] in main_ids:
                    assert run['run_status'] == 'completed' and not run['excluded']
                    assert run.get('code_dirty') is not True
                    assert run['confirmatory_eligible'] is False
                    frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    assert len(df) == 4200
    assert not df.duplicated(['seed', 'capacity_k', 'target_membership', 'person_id', 'field']).any()
    assert len(df.groupby(['seed', 'capacity_k', 'target_membership', 'field'], observed=True)) == 168
    assert (df.groupby(['target_membership', 'person_id', 'field'], observed=True).size() == 42).all()
    assert Counter(runs[i].get('code_dirty') for i in main_ids) == {False: 36, None: 6}
    with (OUT / 'curve_table.csv').open() as stream:
        table = list(csv.DictReader(stream))
    assert len(table) == 42
    for cell in table:
        row = next(x for x in R['curves'][cell['field']] if x['k'] == int(cell['k']))
        for key, value in [('alpha', row['control']['estimate']), ('emr_D', row['trained']['estimate']),
                           ('tau', row['tau']), ('tau_lower', row['tau_ci'][0]), ('tau_upper', row['tau_ci'][1])]:
            assert np.isclose(float(cell[key]), value)
        assert cell['allocated_GPU_h'] == 'unknown'
    joint = np.load(ART / 'bootstrap/joint_bootstrap.npz')
    fitted = np.load(ART / 'bootstrap/censored_bootstrap.npz')
    assert joint['tau'].shape == (10000, 14)
    assert fitted['gamma'].shape == (10000,)
    assert fitted['tobit'].shape[0] == 10000
    assert np.isfinite(fitted['gamma']).all() and np.isfinite(fitted['tobit']).all()
    assert np.allclose(np.percentile(fitted['gamma'], [2.5, 97.5]), R['hypotheses']['H4']['gamma_ci'])
    assert all(r['joint_capacities'] == [] for r in R['hypotheses']['H2']['mapping'] if r['tolerance'] <= .9)
    # An empty feasible set is represented by null, not a spurious first-grid crossing.
    assert all(r['largest_joint_capacity'] is None for r in R['hypotheses']['H2']['mapping'] if not r['joint_capacities'])
    iso = R['hypotheses']['H1']['isotonic_summary']
    assert len(iso) == 13 and np.all(np.diff([r['isotonic_alpha'] for r in iso]) >= 0)
    assert len(R['holm']) == 4 and R['holm']['H2']['H2_reserved_not_tested'] is True
    assert R['hypotheses']['H5']['quadratic_one_sided_p'] > .05
    # Validate the visible report links, including generated figures, without opening the network.
    report = (STUDY / 'analysis.md').read_text()
    assert '__PREDICTIONS__' not in report and '## What This Does Not Show' in report
    link_count = 0
    for href in re.findall(r'\]\(([^)]+)\)', report):
        if href.startswith(('http:', 'https:', '#')):
            continue
        assert (STUDY / href).resolve().exists(), href
        link_count += 1
    # Strict schema failures caused by absent historical evidence remain visible.
    schemas = Path.home() / '.codex/skills/research-status/references/schemas'
    schema_report = {}
    for name, path in [('studies', ROOT / '.ai/research/studies.json'), ('plan', STUDY / 'plan.json'), ('results', STUDY / 'results.json')]:
        validator = jsonschema.Draft202012Validator(read(schemas / f'{name}.schema.json'))
        errors = list(validator.iter_errors(read(path)))
        schema_report[name] = [{'path': '/'.join(map(str, e.absolute_path)), 'message': e.message} for e in errors]
        if name != 'results':
            assert not errors, schema_report[name]
        else:
            imported = [e for e in errors if len(e.absolute_path) >= 2 and list(e.absolute_path)[0] == 'runs' and list(e.absolute_path)[1] >= 3]
            assert len(imported) == 49
            assert all(e.message == "'started_at' is a required property" for e in imported)
    paths = {ROOT / p for p in checked}
    recovered = read(OUT / 'recovery_manifest.json')
    for item in recovered:
        paths.add(check_file(item))
    paths.update(p for p in ART.glob('figures/*') if p.is_file())
    paths.update(ART.glob('bootstrap/*.npz'))
    artifact_manifest = [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(paths)]
    (OUT / 'artifact_manifest.json').write_text(json.dumps(artifact_manifest, indent=2) + '\n')
    result = {
        'numerical_artifact_checks': 'PASS',
        'checked_raw_and_manifest_files': len(checked), 'main_rows': len(df),
        'recovered_colab_files_checked': len(recovered),
        'main_grid_cells_by_arm_field': 168, 'curve_table_rows': len(table),
        'bootstrap_draws': 10000, 'report_local_links_checked': link_count,
        'registry_and_plan_schema': 'PASS',
        'strict_results_schema': 'INCOMPLETE: 49 imported rows lack historical started_at; excluded legacy rows retain original schema errors',
        'schema_errors': schema_report,
        'final_analysis_acceptance': 'BLOCKED: see data_audit.md; numerical checks do not establish missing provenance',
    }
    (OUT / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'schema_errors'}, indent=2))


if __name__ == '__main__':
    main()
