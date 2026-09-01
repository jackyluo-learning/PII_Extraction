# General Style Guide — Research Repositories

Applies to every language in a research repo.

## Repository hygiene

- `artifacts/`, checkpoints (`*.ckpt`, `*.pt`, `*.safetensors`, `*.bin`), and raw data are
  **gitignored**. Their manifests (path, size, sha256) are committed.
- `.ai/research/` is **always** committed — the ledger, configs, and preregistrations are the
  scientific record.
- No secrets, tokens, or dataset access keys in the repo. Read them from the environment and record
  only that they were present, never their values.
- One README section explaining how to reproduce any single run from its `run_id`. If that section
  cannot be written, the harness is not finished.

## Naming

- Files and directories: `lower_snake_case`. Study ids: `shortname_YYYYMMDD`.
- Metrics carry their split: `test_macro_f1`, not `f1`. Costs carry their unit: `wall_clock_s`.
- Never name a file `final`, `final2`, `new`, or `v2_real`. Version by content hash or by study id.

## Comments and documentation

- Comment the *why*, especially for anything that looks wrong but is deliberate: a magic constant
  matching a paper, a workaround for a framework bug, an intentionally unusual hyperparameter.
- Every non-obvious constant cites its source — a paper, an issue, or the study id that measured it.
- When you disable a check, say what you traded away and under what condition it should come back.

## Commits

- One logical change per commit; evidence-producing commits use the `exp` type and name the arms.
- Never amend or force-push a commit whose SHA is recorded in `plan.json` or `results.json` — those
  SHAs are the provenance of a result.

## Reviews

Ask of every experiment change: *what result would this silently alter, and would we notice?*
