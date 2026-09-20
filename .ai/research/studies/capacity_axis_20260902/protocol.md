# Protocol — capacity_axis_20260902

_What will actually be run. The science is fixed in [`design.md`](./design.md); nothing here changes
a hypothesis, a metric, or an analysis. Where this document and the design disagree, the design wins
and this file is wrong._

**Approved by the researcher on 2026-09-03**: 3 seeds · `confirm_above = 6` accelerator-hours ·
budget **~24 A100-h**.

## Overview

One fine-tuned GPT-2 124M is attacked with `gcg_free` at every capacity `k` in a 13-point grid, plus
a `k = 0` anchor run with the `fixed` probe, on a **single fixed target subset** carried unchanged
through every level. The sweep is sharded by `k`, so the unit of execution is a
`(k, seed)` shard: 14 levels × 3 seeds = **42 shards**, 100 attacks each.

| | |
|---|---|
| Model | `gpt2` (124M), fine-tuned — **must be retrained, the run2 checkpoint is gone** |
| Probe | `gcg_free` at `k ≥ 1`; `fixed` at `k = 0` |
| Arms | 25 trained persons + 25 E17-matched control persons |
| Fields | `ssn`, `email` (2) |
| Steps | `PII_GCG_ITERS = 200`, **identical at every `k`** |
| Grid | `k ∈ {0, 1, 2, 3, 4, 6, 8, 12, 16, 20, 24, 32, 48, 64}` |
| Seeds | **42, 1337, 2024** |
| Total | 42 shards · 4,200 attacks · ~24 A100-h approved |

## Arms & Configs

Two arms, distinguished only by registry membership. **Everything else is held identical** — same
model, same probe, same budget, same decision rule, same subset, at every `k`.

| Arm | Selection | n | Targets |
|---|---|---|---|
| **D** (trained) | stratified over the trained registry — **not** `trained[:25]`, see the gate below | 25 persons | 50 |
| **C** (control) | `matched[:25]` — the E17-matched subset, run2's rule | ≤25 persons | ≤50 |

`|C|` may fall below 25 because E17 de-duplicates by person. **The realized `|D|` and `|C|` are
reported by the pilot and recorded per shard; they are never assumed equal.**

### The independent variable is `k`, and only `k`

| Held constant | Value | Enforced by |
|---|---|---|
| Step budget | `PII_GCG_ITERS=200` | read outside the `k` loop; asserted identical across shards from the manifest |
| Target subset | one fixed set | built before the `k` loop; asserted identical via `target_subset_hash` |
| Candidates per position | `B = 256` | `GCGConfig` |
| Evaluations per step | 512 (**256 at `k=1`**, where the pool is smaller than `eval_batch`) | `_eval_candidates` |
| Decision rule | greedy generate `T+20`, `exact_match` | `InstrumentedGCG._check` |
| Fields | `ssn,email` | `PII_FIELDS` |

## Sweep Grid

```
14 k-levels  ×  3 seeds  =  42 shards
   each shard: (25 trained + 25 control) persons × 2 fields = 100 attacks
   total: 4,200 attacks  (3,900 gcg_free + 300 fixed-probe)
```

Per-shard cost scales with sequence length `k + T`, `T ≈ 10`:

| Shard | Attacks | Est. walltime (A100) |
|---|---|---|
| `k=0` (fixed probe) | 100 | ~0.01 h |
| `k=1` | 100 | ~0.16 h |
| `k=20` | 100 | ~0.44 h |
| `k=64` | 100 | ~1.10 h |
| **All 42** | **4,200** | **~16.4 h** |

> **The estimate omits an `O(k)` term and is therefore a floor, not a bound.**
> `_get_top_candidates` builds `k·B = 256k` candidate tensors per iteration in a nested Python loop
> and discards all but 512. At `k=64` that is 16,384 built to keep 512. The overhead grows faster
> than the compute term across the grid, so **large-`k` shards may cost materially more than the
> table says**. This is what the pilot measures.

## Seeds

**42, 1337, 2024** — fixed here, in advance, shared across arms and across every `k`.

`42` is run2's seed and is retained so the `k=20` point sits on the same seed as the published
number, even though the retrained model makes exact reproduction impossible.

**Why 3 and not the lab default of 5** (this is at the hard floor and needs its justification on the
record): the resampling unit is `person_id`, and seeds add repeat attempts on the *same* 25 persons
rather than new persons. Under `ICC ≈ 0.5`, going 3 → 5 seeds moves `DEFF` from 3.5 to 5.5 and
`n_eff` from 42.9 to only 45.5 — **+67% compute for a 3% narrower interval**. The same compute spent
on persons instead (42 persons × 3 seeds, ~27.6 h) would narrow it by 23%, but that would change the
design's run2 alignment and is therefore out of scope here, recorded as the preferred direction for
any future extension.

## Commands

Every command is copy-runnable. `PII_RUN_ID` names the sweep; `_shard_tag` encodes `k`, so shards
never collide.

**Corpus (once).** Halts if C4 contributed anything:

```bash
PII_N_CONTROLS=50 python data_generation.py
```

**Retrain (once, ~0.3 A100-h):**

```bash
PII_MODELS=gpt2 python train.py
```

**`PII_MODELS` is not optional.** `train.py` has no CLI — `--model` does not exist and is silently
ignored — so a bare invocation trains every model in `model_cfg.models`, gated Llama-2-7b included.

**One shard** — this is the unit of execution:

```bash
PII_RUN_ID=e3a PII_CAP_K=20 PII_CAP_SWEEP_N=25 PII_GCG_ITERS=200 \
PII_FIELDS=ssn,email PII_DEVICE_PROFILE=auto \
  python experiments.py --exp E3 --model gpt2 --seed 42
```

**Full sweep** — 42 shards, submitted to Cheaha. Large-`k` shards go to `amperenodes-medium` (48 h)
rather than `amperenodes` (11:45), because `slurm/exp_capacity.slurm` currently requests the hard cap
with zero margin:

```bash
for seed in 42 1337 2024; do
  for k in 0 1 2 3 4 6 8 12 16 20 24 32 48 64; do
    PARTITION=$([ "$k" -ge 32 ] && echo amperenodes-medium || echo amperenodes) \
    PII_RUN_ID=e3a PII_CAP_K=$k PII_CAP_SWEEP_N=25 PII_GCG_ITERS=200 \
    PII_FIELDS=ssn,email sbatch slurm/exp_capacity.slurm
  done
done
```

**Tables** (CPU, seconds — gated on the analysis code existing):

```bash
python make_tables.py --run-id e3a
```

## Compute Budget

| Item | A100-h |
|---|---|
| Corpus regeneration | ~0 (CPU + network) |
| Retrain `gpt2` 124M | 0.3 |
| Pilot — `k ∈ {1, 20, 64}` × seed 42 | ~1.7 |
| Reproducibility check — re-run `k=20`, seed 42 | 0.5 |
| Main sweep — 42 shards | 16.4 |
| Retry / preemption margin (30%) | 5.0 |
| **Total** | **~24** |

`est_cost_usd = 0` — academic cluster and an already-paid subscription. Accelerator-hours is the
accounting unit and the **GPU model is recorded on every shard**, or the hours cannot be aggregated.

Against the ~480-hour window before the 2026-09-24 experiment deadline this leaves ~20× headroom.

**`confirm_above = 6` accelerator-hours** (approved). One seed's full 14-point curve costs ~5.5 h, so
the main sweep stops for approval three times — once per seed. That matches the natural checkpoint:
after seed 42 the first complete `α_k` curve exists and can be inspected before spending the rest.

## Acceptance Criteria

### Phase 0 — harness (no GPU beyond the retrain)

All eight pre-launch code gates land and are unit-tested where testable:

1. **Stratified trained-subset selection** replacing `trained[:n_t]`, which contains **zero** f=20
   persons — 60% of the trained population.
2. **`k = 0` anchor code path**: branch on `k == 0` to `_run_fixed_probe`, `capacity_k=0` passed
   explicitly.
3. **Per-person `AttemptLogger` flushing** inside the subset loop.
4. **Run manifest**: git SHA + dirty flag, resolved config, Faker version, GPU model, `pip freeze`
   hash, realized tier composition, and **`target_subset_hash`**.
5. **`effective_eval_batch` / `effective_minibatch`** read `HW["gpu_mem_gb"]`, not the literal string
   `"colab_free"`.
6. **Faker disjointness assertion** over SSNs and emails at corpus build.
7. **C4 halt** raised inside `fetch_public_passages`, not left to human memory.
8. **`lifelines` pinned to an exact version**; the analysis hard-fails if it is absent.

**Gate**: corpus regenerates with **zero C4 contribution**; `train.py` reaches its usual PII eval
loss; the 42 shards' `target_subset_hash` values are identical.

### Phase 1 — pilot (`k ∈ {1, 20, 64}`, seed 42)

| Check | Criterion |
|---|---|
| **`α_0 ≈ 0`** (read first) | The `k=0` control EMR is not detectably above 0. A non-trivial value means `exact_match` is firing spuriously and **blocks the study** |
| Per-attack cost | Measured at **both grid extremes**, not only mid-grid — the `O(k)` term means the ratio is not constant |
| Budget | Extrapolated total within the approved 24 A100-h, or re-scope |
| Realized `|D|`, `|C|` | Reported. If `|C| < 15` the control arm is too thin and the protocol pauses |
| Reproducibility | Re-run `k=20` seed 42; **per-arm** flip rate does not exceed `2p̂(1−p̂)` beyond its bootstrap CI |

### Phase 2 — main sweep

- All 42 shards complete, or every incomplete shard is recorded with a `run_status` and a reason.
- `target_subset_hash` identical across all 42; configured `PII_GCG_ITERS = 200` identical across all
  42. **Either failing blocks analysis** — these are the invariants the whole capacity contrast rests
  on.
- Accelerator-hours and GPU model recorded per shard; preempted-shard cost reported separately.

### Phase 3 — analysis

Gated on the five pre-table code items: the two-block joint bootstrap **retaining raw replicate
vectors**; Wilson wired on `n_eff` plus Newcombe/MOVER; the interval- and right-censored **log-log**
AFT for `k_min` (bootstrapped, not sandwich-SE'd); the `_crossing_k` sentinel; the Spearman/isotonic
replacement for the monotonicity check.

## Failure Handling

| Condition | Action |
|---|---|
| Preemption | Retry up to **3** times (lab policy). A 4th means the shard does not fit the session — re-shard, do not retry |
| OOM | **1** retry with a smaller `effective_eval_batch`, then **block**. On Colab, check the batch-size gate landed |
| Walltime kill | **Do not retry blindly.** Move that `k` to `amperenodes-medium` — the estimate is a floor, not a bound |
| `α_0` detectably > 0 | **Block.** The decision rule is matching spuriously; nothing above it is interpretable |
| C4 contributed to the corpus | **Block.** Real PII may be present; regenerate |
| `target_subset_hash` mismatch | **Block analysis.** Do not "use the shards that agree" — the paired design is gone |
| Right-censoring > 60–70% of `k_min` | Pre-committed fallback: Turnbull nonparametric summary instead of a point estimate for `β` |
| `lifelines` absent or wrong version | **Hard-fail.** Never silently fall back to the complete-case `linregress` |

## Artifacts

| Path | Content | Size |
|---|---|---|
| `results/attempts/e3a__E3__gpt2_seed*_field-ssn-email_k*.parquet` | 42 shards, ~100 rows × 27 cols each | ~5 MB total |
| `results/manifests/e3a__*.json` | per-shard manifest (pins, GPU, subset hash, tier composition) | < 1 MB |
| `results/e17_matches_e3a_seed*.json` | matching pairs — input to the balance table | < 1 MB |
| `results/tables/` | generated by `make_tables.py` alone; **no hand-transcribed numbers** | small |
| `models/gpt2/` | retrained checkpoint + `train_meta.json` | ~500 MB |
| `data/corpus/`, `data/*_registry.json`, `data/corpus_metadata.json` | regenerated corpus and ground truth | ~1 GB |

Retention: parquet shards and manifests are the raw evidence and are kept indefinitely; the
checkpoint is kept until the study closes out.

## Out of Scope

Fixed by the design, restated so the protocol cannot quietly widen:

- **One model.** No claim about model-size dependence of `α_k`.
- **Two fields.** `β`'s cross-field transferability **cannot** be established — `beta_disp` would be
  the standard deviation of two numbers.
- **`gcg_free` only.** The curve is `α_k(gcg_free)`; run2 shows `gcg_anchored` differs by 23 points at
  the same nominal `k`.
- **No comparison of new `α_20` to run2's published value** without the checkpoint-identity caveat.
- **H5 is exploratory**, reported with its argmax CI and an underpowered caveat, outside the
  confirmatory family.

## Prospective Amendment — E3b Field-Exposure Repair (2026-09-20)

This amendment was written before any E3b outcome. It repairs the discovered field-level exposure
and target-pairing defects without retraining: the recovered corpus and fine-tuned GPT-2 checkpoint
must match their frozen byte hashes. E3a remains in the ledger as the historical run; E3b may
supersede it for D/C interpretation only after every acceptance gate below passes.

The researcher authorized use of all practical Cheaha A100 resources on 2026-09-20 to complete the
repair quickly. The estimate is approximately 30 additional A100-hours, based on the completed E3a
runtime, and the former per-seed approval stop does not apply to this explicitly authorized rerun.

### Target selection and matching, fixed before outcomes

The sole target input is `results/target_sets/e3b.json`. The builder reads the registry, fine-tuning
corpus, recovered checkpoint, and held-out GPT-2 reference model; it never reads attempt logs or
outcome columns.

1. A D person is eligible only when both evaluated field values, SSN and email, actually occur in
   the fine-tuning text under the registered field-specific normalization.
2. From the complete eligible pool in registry order, deterministic even subsampling selects exact
   quotas `f=1:3`, `f=5:7`, and `f=20:15`. No E3a success or failure is used.
3. Each person is represented jointly by six covariates: character length, token length, and
   held-out self-information for SSN and for email.
4. A standardized squared-distance cost matrix is solved by a person-level Hungarian assignment.
   It assigns 25 different control people without replacement; every selected control SSN and email
   must be absent from the fine-tuning corpus.
5. Before the file can be written, all six marginal standardized mean differences—character length,
   token length, and held-out self-information for each of SSN and email—must satisfy
   `|SMD| <= 0.1`. An undefined value or any violation is a hard failure that reports each offending
   field and covariate; there is no post-outcome waiver.
6. The builder records the 25 D/C pairs, field exposure flags, covariates, balance diagnostics,
   execution contract, and complete content fingerprints for the registry, corpus, and checkpoint.
   It refuses to overwrite a different frozen manifest and refuses to build after an `e3b` outcome
   or shard manifest exists.

Freeze and independently verify once on Cheaha:

```bash
python e3_target_manifest.py build \
  --registry data/target_registry.json \
  --corpus data/corpus/train.json \
  --checkpoint models/gpt2 \
  --output results/target_sets/e3b.json \
  --target-set-id e3b \
  --tier-quotas 1:3,5:7,20:15 \
  --k-grid '0 1 2 3 4 6 8 12 16 20 24 32 48 64' \
  --seeds '42 1337 2024' \
  --gcg-iters 200 --model gpt2 --reference-model gpt2

python e3_target_manifest.py verify \
  --manifest results/target_sets/e3b.json \
  --registry data/target_registry.json \
  --corpus data/corpus/train.json \
  --checkpoint models/gpt2
```

Expected pre-outcome gate from the recovered data: 92 fully exposed D people with eligible tier
counts `{1:3, 5:29, 20:60}`; the selected set must be `{1:3, 5:7, 20:15}`, with 50/50 D fields
present, 0/50 C fields present, 25 unique controls, and all six marginal `|SMD|` values at most 0.1.
Any discrepancy blocks launch and is
investigated as an input-version problem rather than repaired by changing the quotas after outcomes.

### Execution contract and per-shard provenance

Every E3 invocation now requires `PII_E3_TARGET_MANIFEST`. It validates the target payload and the
current registry, corpus, and full checkpoint directory before allocating either model. The frozen
contract is one checkpoint, fields `ssn,email`, `N=200`, the 14-point grid, seeds
`42,1337,2024`, and 25 people per arm. Runtime subsampling and E17 reconstruction are forbidden.

Each shard writes its manifest before the first attack. Besides the original subset and step hashes,
it records hashes of the frozen target file and payload, target values, pair assignment, registry,
corpus, checkpoint directory, and resolved sweep configuration, plus code commit/dirty state,
environment lock, exact accelerator, and Slurm identifiers. Formal E3b evidence requires one value
for every cross-shard invariant and `code.dirty=false` everywhere. The target file separately records
the clean, non-empty Git commit that built it. That builder commit may differ from the one used by
formal shards, but both are retained explicitly; the formal-run commit must itself be identical and
clean across all 42 shards.

### Pilot, reproducibility, and release gate

Run the formal `k=0, seed=42` shard first. It must contain exactly 100 rows, retain the same manifest
hash, and produce no control exact match. Next run formal `k=20, seed=42` and one explicitly
excluded `e3b_repro` duplicate. Report the person-level per-arm flip rate using the earlier
reproducibility criterion. A failure or provenance mismatch blocks the remaining 40 formal shards.

After that gate, submit all remaining coordinates at once with no `%N` array throttle; Cheaha may
use every available A100. The exact environment is:

```bash
export PII_RUN_ID=e3b
export PII_E3_TARGET_MANIFEST="$PWD/results/target_sets/e3b.json"
export PII_MODELS=gpt2
export PII_SEEDS='42 1337 2024'
export PII_KGRID='0 1 2 3 4 6 8 12 16 20 24 32 48 64'
export PII_CAP_SWEEP_N=25
export PII_GCG_ITERS=200
export PII_FIELDS=ssn,email
export PII_DEVICE_PROFILE=a100_80
```

The pilot coordinates are not repeated in the formal array. All other coordinates may run
concurrently, with `k>=32` submitted to the longer A100 partition if the short partition cannot
cover their observed wall time. No P100 or mixed accelerator class is admissible.

### Prospective prediction and acceptance

This is a repair/replication after E3a, so its C-curve prediction is explicitly informed by E3a:
Spearman `rho>0.9`, `alpha_20>=0.70`, and `alpha_64>=0.90`. `rho<=0` or either high-capacity
threshold failing contradicts that replication prediction. No directional prediction is registered
for D-C; the purpose of E3b is to remove the exposure and pairing defects before estimating it.

Before any E3b outcome analysis, require all of the following: 42 distinct formal `(k,seed)`
coordinates; 4,200 attempt rows; 100 rows per coordinate; the exact 14 x 3 grid; one value for every
strict provenance hash; clean committed code; one A100 accelerator class; 25 unique people per arm;
the registered 3/7/15 D tiers; 50/50 exposed D targets; and 0/50 exposed C targets. Missing or
duplicated shards, dirty or absent code state, input/config/hash disagreement, incomplete rows, or an
exposure or six-variable marginal-balance failure blocks confirmatory D/C analysis. Old rows are never deleted; E3b is appended to the
ledger and marked as superseding E3a only after this gate succeeds.
