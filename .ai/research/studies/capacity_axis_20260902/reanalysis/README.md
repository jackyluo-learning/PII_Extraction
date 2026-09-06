# E3 audited reanalysis

The computation is conditional on the recorded raw artifacts. Final analysis acceptance
is **blocked**; the study is not ready for closeout. The main execution checkpoint is
also reopened because completed raw files do not establish historical pins or total cost.

## Start here

- [Raw-data requirements and current audit](data_audit.md)
- [Current report](../analysis.md), generated from `../results.json → reanalysis.estimates`
- [Analysis choices and deviations](method_choices.md)
- [Independent numerical review](statistics_review.md)
- [Compatibility audit and artifact integrity checks](verification.json)

`prior_analysis.md`, `prior_results.json` and `prior_plan.json` preserve the rejected
completion state. `initial_provenance_audit.md` and `raw_data_audit.json` are snapshots
before Drive recovery; `post_recovery_audit.json` records what was subsequently recovered.
Legacy root-level `curve`, `analysis_notes` and `exploratory_findings` in the ledger are
superseded history; the authoritative current results are explicitly namespaced above.

## Required raw evidence

| Needed source | Expected coverage / why needed | Available | Still unresolved |
|---|---|---|---|
| Main attack parquet, raw target/generation, exact match, NLL, H, timings | 14 capacities × 3 seeds, both arms, 2 fields; recompute outcomes and statistics | 42 shards, 4,200 rows, complete fixed-target matrix, checksums verified | These records alone cannot establish model identity or scheduler exit |
| Main launch manifests | One per shard; code, configuration, environment, seed, subset | 42 manifests; one recorded code/environment/subset | 6 unknown dirty states; full resolved launch configuration and full environment lock absent |
| Training checkpoint identity and data snapshot | Bind measured attacks to the intended trained model and corpus | Recovered Colab data and current model hash; registry labels rechecked | Historical executed Cheaha checkpoint hash, training/log lineage and per-run data binding absent |
| E17 original matching records | Main seeds 42/1337/2024; pair-weighted and deduplicated marginal SMD | Colab seed42 recovered; actual attacked sample balance computed | Cheaha E17 for all three seeds missing; Colab is not substituted |
| Original pilot/cost/repro raw data | Audit pilot gates, costs and target-level decision flips | 7 Colab shards plus manifests recovered; zero flip comparison rechecked | Dirty original/code boundary disclosed; not a clean Cheaha replay |
| Scheduler and failure evidence | Every main/smoke/failed/interrupted job, state, allocation, elapsed time | Per-attack main elapsed totals 26.251 h | Slurm terminal states, allocation totals, complete failed/preempted job costs absent |
| Historical start timestamps | Required by the strict run-ledger schema | Not present in recovered manifests | Never substitute file mtime or import time for launch time |

The three legacy rows stay excluded and retain their original schema. The 49 new
byte-addressed imports use canonical hashes of **observed** configuration fields with
the per-run seed excluded. This is retrospective identity, not proof of a complete
launch-time configuration. Known scalar fields follow the harness schema. Missing
historical `started_at` keeps these imports from passing strict run-schema validation;
`verification.json` records the exact remaining errors. Unknown optional pins are
omitted with explicit status fields, never replaced by false, zero or invented dates.

## Reproduce the available-data calculations

Run from the repository root. Restore the raw artifacts to their ledger paths first;
`recompute.py` fails on changed bytes, missing matrix cells or invalid main-run selection.
The 42 main shards remain under `results/`; the recovered Colab files live separately
under `artifacts/capacity_axis_20260902/recovered_colab/` so same names do not collide.
Artifact bytes are gitignored; `artifact_manifest.json` and `recovery_manifest.json`
record their paths, sizes and hashes.

The recorded local interpreter is Python 3.13; use an isolated environment with the
versions in [analysis_environment.txt](analysis_environment.txt), including
lifelines 0.30.0 and matplotlib 3.10.6. This analysis environment is distinct from the
historical Cheaha execution environment.

```bash
python .ai/research/studies/capacity_axis_20260902/reanalysis/verify_models.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python .ai/research/studies/capacity_axis_20260902/reanalysis/recompute.py
python .ai/research/studies/capacity_axis_20260902/reanalysis/audit_task_predictions.py
python .ai/research/studies/capacity_axis_20260902/reanalysis/write_report.py
python .ai/research/studies/capacity_axis_20260902/reanalysis/verify_evidence.py
```

`audit_raw_data.py` documents the initial audit. `import_evidence.py` documents the
one-time recovery import; it refuses to overwrite an already analyzed ledger. Do not
use it as the normal reproduction entry point. The retired `analyze_e3.py` CLI fails
with a pointer to the replacement, rather than regenerating the withdrawn results.

Bootstrap vectors are preserved in `artifacts/capacity_axis_20260902/bootstrap/`.
The main curve and censored models each use all 10,000 prescribed draws. The
independent reviewer refitted the full H4 case and five selected bootstrap cases;
this does not mean all 10,000 fits were independently duplicated. Final visual QA
checked the three PNG figures; matching PDF versions are available for export.

## Complete the Cheaha evidence

Local batch SSH reached Cheaha but authentication failed. The computer-use tool also
disallowed Terminal access; no authenticated UI session was inspected or bypassed.
If these files already exist locally, supply their directory and continue the audit.
Otherwise, [collect_cheaha_evidence.sh](collect_cheaha_evidence.sh) can be copied to an
authenticated Cheaha session and run with:

```bash
bash collect_cheaha_evidence.sh
```

It reads `/data/user/jluo/PII_Extraction`, scoped scheduler records and relevant logs,
and prints a `/tmp/e3-evidence.*.tar.gz` path. It launches no GPU jobs and modifies no
source data; only the temporary bundle is created. Current hashes/configurations are
clearly labelled current and cannot alone prove historical per-shard identity. Copy
the resulting archive back into this workspace for the next audit. The script starts
no experiments; it only collects existing records.

The missing evidence may support or weaken the recorded study; the acceptance gates
must be reevaluated from it. Do not automatically change `blocked` to `done` when an
archive arrives, and do not infer a valid preregistered global H2 test retroactively.
