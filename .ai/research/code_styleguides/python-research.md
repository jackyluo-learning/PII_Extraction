# Python Style Guide — Research Code

> For experiment, harness, and analysis code. Research code has a different failure mode from
> product code: it does not crash, it quietly produces a plausible wrong number. These rules target
> that failure mode specifically.

## Toolchain

- **uv** for everything: `pyproject.toml` for dependencies, a committed `uv.lock`, a project-root
  `.venv/`. `uv run python -m ...` is the canonical way to execute anything.
- **ruff** for lint and format; **mypy** on `harness/` and `analysis/` (experiment scripts may be
  exempt, shared code may not).
- Python >= 3.11.

## Layout

```
harness/          # reusable experiment infrastructure — typed, tested, reviewed
  config.py       # config resolution + canonical hashing
  seeding.py      # one set_seed() covering every RNG, dataloader workers included
  ledger.py       # append-only results.json writer
  eval.py         # THE evaluation function, shared by every arm
experiments/      # per-study entry points — may be scrappy, must be pinned
analysis/         # aggregation, statistics, figures — deterministic, re-runnable
configs/          # resolved configs, committed, named by config hash
tests/            # tests for harness/ and analysis/, not for experiments/
```

## Non-negotiables

1. **One evaluation function.** `harness/eval.py` computes each metric once, for every arm. A metric
   re-implemented per arm is how two arms end up measured differently.
2. **Everything that affects a result lives in the config.** No module-level constants that change
   behaviour, no env-var-dependent branches, no `if hostname == ...`. Anything outside the config is
   outside the config hash, and the run is then unreproducible.
3. **Seed every RNG.** `random`, `numpy`, the framework, CUDA, dataloader `worker_init_fn`,
   augmentation pipelines, and distributed samplers. Write it once in `harness/seeding.py` and call
   only that.
4. **Fail loudly.** Never wrap a metric computation in a bare `except`. A NaN loss raises; it does
   not become `0.0` in the ledger. Assert shapes and label ranges at the boundaries.
5. **The ledger is the record.** Write to `results.json` through `harness/ledger.py`. W&B/MLflow/
   TensorBoard are views, not sources of truth.
6. **No test-split access outside analysis.** Guard it in code: the test loader raises unless an
   explicit `allow_test=True` is passed, and only `analysis/` passes it.

## Style

- Type hints on every function in `harness/` and `analysis/`; docstrings stating units and shapes.
- Dataclasses (or Pydantic) for configs, never bare dicts passed five levels deep.
- Pure functions for anything in `analysis/` — same inputs, same figure, every time.
- `pathlib.Path` over string paths; f-strings over `%`/`.format`.
- Name variables for their units: `wall_clock_s`, `lr`, `batch_tokens`, `macro_f1` — not `t`, `x`, `m`.
- Log at the boundaries (run start, epoch end, run end), not inside inner loops.
- Determinism flags are set in one place and reported in the run record, not sprinkled per script.

## Testing

Experiments are not unit-tested; the harness is.

- `harness/`: config hashing is stable and order-independent; seeding reproduces a tensor; the
  ledger appends without corrupting existing rows; the eval function matches a hand-computed value
  on a tiny fixture.
- `analysis/`: the statistics are checked against a known example (a bootstrap CI on a fixed array,
  a Holm correction on a fixed p-vector) — these are the functions whose bugs change conclusions.
- A **golden micro-run**: a 30-second end-to-end run on 50 examples with a fixed seed, asserting the
  headline metric to within tolerance. This catches harness breakage before a sweep does.
