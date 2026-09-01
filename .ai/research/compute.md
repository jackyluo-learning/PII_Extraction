# Compute Environment

_Measured 2026-08-31. The local section was probed directly; the two remote environments come from
the `slurm/` job scripts plus user confirmation._

## Three environments and their division of labour

| Environment | Role | Suited to |
|---|---|---|
| **Colab Pro / Pro+** | **primary** (current preference) | training, short attacks, single E-experiments |
| **UAB Cheaha (SLURM)** | long sweeps | E3 capacity sweep, E7 budget matching — anything needing `afterok` chains |
| Local MacBook (M3 Max) | writing and analysis | `make_tables.py` / `dump_all_results.py` (CPU, seconds), git, the paper |

**Why split this way**: Colab sessions are preemptible and its filesystem is not persistent. E3 is a
grid of 13 k-values × models × seeds and will almost certainly be interrupted partway on Colab,
whereas Cheaha's job arrays and `afterok` dependencies are built for exactly that. Short tasks (the
E2 base arm, E5 on existing data, all pure analysis) run faster on Colab.

## Colab Pro / Pro+ (primary)

- **Accelerator**: varies with availability — A100 40GB / L4 / T4 16GB. **The model is not guaranteed
  to be the same across sessions.**
- **Constraints**: sessions can be preempted; the filesystem is not persistent
- **Persistence**: **mount Google Drive**. `results/`, `models/`, and `data/` all live on Drive
- **Cost**: subscription plus compute units; billed in units rather than directly in dollars

**The codebase already targets Colab natively**: `config.py`'s `_PROFILES` contains `colab_free`
(15 GB / batch 8) and `colab_pro` (40 GB / batch 32), and `colab_free` is the default.

> **`PII_DEVICE_PROFILE=auto` is mandatory here.** Because the assigned GPU differs per session,
> `_auto_hw()` picks a profile from measured VRAM (≥70 GB → the 80G profile, ≥38 → 40G, ≥20 → 24G,
> otherwise the smallest). Hardcoding `colab_pro` and landing on a T4 will OOM.

> **Flush `results.json` and the attempt-log parquet shards back to Drive as each task completes.**
> Anything unflushed is destroyed when a session is reclaimed, and the compute has already been spent.
> This is a hard gate in the methodology.

> **Record the actual GPU model on every run.** Colab assigns different accelerators per session;
> without that field `accelerator_hours` cannot be aggregated across runs.

## UAB Cheaha (SLURM, long sweeps)

Read off the `#SBATCH` directives in `slurm/*.slurm`:

| Partition | GPU | Walltime cap | Note |
|---|---|---|---|
| `amperenodes` | **A100 80GB** | 11:45:00 | main GPU queue |
| `amperenodes-medium` | A100 80GB | 48:00:00 | large models (Pythia 1.4B/2.8B) go here |
| `pascalnodes` | **P100 16GB** | 12:00:00 | **roughly 3× slower**; usable for backfilling small models |
| `express` | none | 00:30:00 | aggregation / table-building tasks |

Every GPU job: `--gres=gpu:1 --cpus-per-task=8 --mem=64G`.

- **Scheduler**: Slurm. The submitters accept `PARTITION` / `GRES` / `ACCOUNT` environment
  variables; `ACCOUNT` defaults to empty (no `--account` passed). Fill it in if the cluster requires
  an allocation string.
- **Cost**: academic cluster, **free at the point of use**. The real constraint is queue time and
  walltime, not money.
- **Job-sizing strategy**: `submit_per_model.sh` already right-sizes scope per model so jobs can
  backfill into free slots (small models are submitted to `amperenodes,pascalnodes` simultaneously).
  Keep that strategy.

## Local machine (writing and analysis)

```
Apple M3 Max · 36 GB unified memory · macOS arm64 · Python 3.14.2
no torch · no uv · no Slurm client · no .venv
disk 926 GB, 93% used, 68 GB free
```

Used only for `make_tables.py` / `dump_all_results.py` (pure pandas/numpy, seconds) and writing.
**Do not train or attack here** — there is no CUDA, and 68 GB will not hold checkpoints.

> Note: `make_tables.py` needs `pandas` / `numpy` / `scipy` / `statsmodels`, none of which are
> currently installed locally. Analysing here means first building a lightweight analysis-only
> environment.

## Cost accounting

Neither remote environment charges dollars at the point of use, so:

| Field | Convention |
|---|---|
| `est_cost_usd` in `results.json` | record **0** (academic cluster / already-paid subscription); the real cost goes on the next line |
| **accelerator-hours** | the **primary accounting unit** = walltime × GPU count |
| GPU model | recorded on every run (`a100_80` / `a100_40` / `l4` / `t4` / `p100`); without it the hours are not comparable |
| Colab compute units | recorded when readable from the Colab side; otherwise accelerator-hours is authoritative |

### `confirm_above` threshold (**provisional**)

**4 accelerator-hours** — any launch above this needs explicit approval.

This is a **placeholder, not a conclusion**. No run has been measured yet, so neither of us knows
what one GCG attack actually costs. **It is confirmed at the protocol stage against the pilot's
measured per-run cost.** Until then it is a coarse guardrail against burning a day of queue on a
slip.

## Storage layout

| Location | Contents |
|---|---|
| Drive (Colab) / project dir (Cheaha) | `data/` (corpus + registry), `models/<name>/` (fine-tuned checkpoints + `train_meta.json`), `results/attempts/*.parquet`, `results/tables/` |
| `.hf_cache/` (in-project) | prefetched base-model weights, populated by `setup_env.sh` |
| Repo (git) | code, `.ai/research/`, optionally `results/tables/*.txt`; **`data/`, `models/`, and `results/` are already gitignored** |

## Environment and dependencies — an open reproducibility gap

Current practice: `slurm/setup_env.sh` runs `python -m venv .venv` plus
`pip install -r requirements.txt`, and `requirements.txt` uses lower bounds only:

```
torch>=2.0.0
datasets>=2.14.0
faker>=18.0.0
...
```

**This does not satisfy the reproducibility contract.** `torch>=2.0.0` resolves to different
versions today and three months from now; identical code at an identical seed can produce different
numbers, and no field in `results.json` records the difference. The fifth pin (environment) is
effectively missing.

**Recommended migration to uv**: dependencies declared in `pyproject.toml`, a committed `uv.lock`,
and a `.venv/` in the project root. Both Colab and Cheaha support uv.

> But **this is a standalone chore, not a side effect of setup**. Migrating touches every job script
> and the Colab notebook, and needs an end-to-end verification pass. Start it as its own task.
> Until it is done, the environment pin in `results.json` can only be a `pip freeze` snapshot hash,
> and "environment not pinned" must be listed as a validity threat at analysis time.

## To confirm

- [ ] Whether Cheaha requires `--account=<allocation>` (the submitters support it; default is unset)
- [ ] Colab compute-unit balance and burn rate (needed if budget gating is to be enforced)
- [ ] The final `confirm_above` value — **confirmed at the protocol stage from a measured pilot**
