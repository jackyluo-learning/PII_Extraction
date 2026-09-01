# Lab Methodology

> The rules of the game. `research-run` defers to this document on every task; where this file and a
> skill disagree, this file wins. Customize the thresholds in §Parameters; the lifecycle is fixed.

## Guiding Principles

1.  **Predict Before You Run:** every task records its expected outcome and its falsification
    criterion *before* execution. A run whose result cannot surprise you was not worth its compute.
2.  **The Preregistration Is the Contract:** `design.md` fixes the hypotheses, the arms, the metric,
    and the analysis before any result is seen. Anything else is exploratory and is labelled so.
3.  **The Plan Is the Source of Truth** for progress; **`results.json` is the source of truth for
    evidence.** No number is ever reported from a log tail or from memory.
4.  **Pilot Before Sweep:** no full sweep is launched where a pilot has not run and its sanity
    checks have not passed.
5.  **No Single-Seed Claims:** a comparison carries at least `min_seeds` seeds and is reported with
    an effect size and an interval.
6.  **Baselines Get Equal Care:** same tuning budget, same data, same evaluation path.
7.  **Compute Is Spent, Not Free:** every run records its cost; every launch above
    `confirm_above` is approved by a human first.
8.  **Null Results Ship:** a refuted hypothesis is a completed study and is written up identically.

## Parameters

Two kinds of number live here, and confusing them is how a lab ends up running on values nobody
actually chose.

- **Floors and policies** are lab-wide. Set them once, here. They exist to stop a mistake slipping
  through when nobody is paying attention.
- **Study parameters** are marked `per study` below. This file carries only a *provisional* value for
  them, because the information needed to choose properly does not exist at setup time: nothing has
  been run yet, so nobody knows what a run costs, how much seed variance this benchmark has, or how
  far an identical re-run drifts. Each is confirmed at the stage named in the third column, against a
  **measured** number rather than a guess.

**A skill that silently uses a provisional value without asking is violating this file.** The
provisional values are there so that an unattended run cannot be reckless, not so that the question
can be skipped.

| Parameter | Provisional | Decided at | Meaning |
|-----------|-------------|------------|---------|
| `min_seeds` | 5 (hard floor: 3) | **per study — protocol** | Seeds per arm for a confirmatory comparison. The floor is lab-wide and not negotiable; the value is chosen per study where MDE and budget collide. |
| `repro_tolerance` | 1e-3 relative | **per study — run, measured in the pilot** | Allowed drift on the headline metric in the reproducibility check. The provisional value is a fallback for when no drift measurement exists yet. |
| `confirm_above` | 4 accelerator-hours | **per study — protocol** | Launch cost above which explicit user approval is required. Provisional until a pilot measures the real per-run cost. |
| `determinism_level` | `statistical` | **per study — design** | `bitwise` / `statistical` / `distributional` |
| `correction` | Holm | **per study — design** | Multiple-comparison correction within a family |
| `practical_threshold` | study-specific | **per study — design** | Minimum effect worth acting on |
| `pilot_seeds` | 1 | lab-wide | Seeds in a pilot run |
| `alpha` | 0.05 | lab-wide | Significance level, after correction |
| `retry_policy` | **preemption: up to 3; OOM/divergence: 1 then block** | lab-wide | See §Retry policy below |
| `test_split_touches` | **n/a — see §Target-set discipline** | lab-wide | This project has no conventional test split |

**Lab-wide values confirmed at setup (2026-08-31):** seed floor **3**, `alpha` **0.05**,
correction default **Holm**, commit frequency **once per task**, `pilot_seeds` **1**.

## Project-specific rules (PII_Extraction)

These three exist because this project does not fit the framework's default assumptions. They are
lab-wide and were confirmed at setup.

### Retry policy

Colab session preemption is **routine here, not an anomaly** — it is the expected cost of the primary
compute environment.

- **Preemption:** resume from checkpoint up to **3 times** without blocking. Every interruption is
  still recorded in `results.json` with `run_status: "preempted"`. Beyond 3, the job is cut too large
  for the session length — block and re-shard it, do not retry a 4th time.
- **OOM / divergence:** 1 retry (OOM with a smaller batch), then **block**. These are signals about
  the configuration, not about the environment.

### Target-set discipline (replaces `test_split_touches`)

This project has no conventional train/test split. The analogous asset is the **attack target set** —
the `(person, field)` targets in arms D and C.

- **Forbidden:** tuning GCG hyperparameters (`prompt_length_k`, `candidates_per_position_B`,
  `max_iterations_N`, `n_candidates_per_step`) against EMR measured on the study's target set. That
  turns the reported rate into "the best number after 50 attempts on these particular targets".
- **Permitted:** sweeping an independent variable across the same targets. E3 (13 values of `k`) and
  E5 (frequency tiers) are *designed* to reuse one fixed target subset — that is a paired design, not
  repeated trial-and-error.
- **To tune:** draw a separate held-out set of targets, tune there, then freeze the hyperparameters
  before touching the study's target set.

### Evidence persistence (Colab)

A task is **not complete** until `results.json` and the attempt-log parquet shards are written back to
mounted Drive. A preempted session destroys anything unflushed, and the compute is already spent.

Every run additionally records the **actual GPU model** it landed on (`a100_80` / `a100_40` / `l4` /
`t4` / `p100`). Colab assigns different accelerators per session; without this field
`accelerator_hours` cannot be aggregated across runs.

## Study Lifecycle

Every study moves through a fixed sequence of stages. The order is **mandatory** and exists so that
the design is criticized while it is still cheap to change:

1.  **Design (Preregistration) — `research-design`:** ALWAYS first. Define the question, the
    falsifiable hypotheses, the variables, the arms, the metric, and the analysis plan; then have
    them contributed **and verified** across the five domains — **methodology, statistics, baselines,
    reproducibility, and data** — by their specialist reviewers. Output: an approved `design.md`.
    A study MUST NOT proceed to protocol without one.
2.  **Protocol & Plan — `research-protocol`:** Only after the design is approved. Refine `design.md`
    into an executable `protocol.md` (configs, sweep grid, commands, budget) and a phased
    `plan.json`, with a compute budget the user has approved.
3.  **Run — `research-run`:** Execute the plan's tasks following the **Run Workflow** below,
    appending every run to `results.json`.
4.  **Analyze — `research-analyze`:** Apply the **preregistered** analysis, declare any deviation,
    label exploratory findings, and produce `analysis.md` with a verdict per hypothesis.
5.  **Review & Close Out — `research-review`:** Peer-review the study against its preregistration,
    fold its validity threats into `VALIDITY.md`, write the `LAB_NOTEBOOK.md` entry, archive the
    evidence, and delete the working files.

**Exception:** an `exploration` study may skip the full design stage and use a lightweight one, but
its results may never be reported as confirmatory. An exploration that finds something becomes the
*hypothesis* of a new confirmatory study.

## Run Workflow

All tasks follow this lifecycle. It replaces the red-green-refactor loop of software development;
step 3 is the direct analog of writing a failing test.

1.  **Select Task:** the next task in `plan.json` in sequential order (first task whose `status` is
    not `done`).

2.  **Mark In Progress:** set the task's `status` to `"doing"` in `plan.json` and sync to
    `studies.json` (the `phases_summary` entry and, if this is the first active task, the study
    `status`). Refresh `updated_at`.

3.  **Predict (the analog of a failing test):**
    -   Write the task's `prediction`: what you expect the numbers to be, with a rough magnitude.
    -   Write its `falsification`: the observation that would show the prediction wrong.
    -   **CRITICAL:** both are written into `plan.json` **before** the run is launched. A task that
        reaches execution with an empty `prediction` is a protocol violation — stop and fill it in.
    -   If you cannot state a prediction, the task is not yet well-defined. Say so and refine it.

4.  **Pin:** capture the five pins (code commit, config hash, environment lock, dataset version,
    seed) per the harness's reproducibility contract. Verify the tree is clean; a
    dirty tree means `code_dirty: true` and the run cannot back a confirmatory claim. Write the
    resolved config to `configs/<config_hash8>.yaml` and commit it.

5.  **Pilot (first task of a study, and after any harness change):**
    -   Run one arm at one seed with a shortened budget.
    -   Check the sanity conditions from `design.md`: the trivial baseline behaves as expected, the
        metric is in range, the loss moves in the right direction, the shapes and counts are right.
    -   **Do not proceed to the sweep until the sanity checks pass.** A sweep on a broken harness
        produces a full, self-consistent, entirely fictional results table — the most expensive
        failure mode in this framework.

6.  **Reproducibility check (once per study, before the main sweep):**
    -   Re-execute one completed run from its pins alone and compare the headline metric.
    -   **Measure the tolerance; do not assume it.** The drift between two executions of an identical
        config and seed *is* this study's floating-point and kernel noise. Report the observed drift,
        propose a tolerance a few times larger, and have the user confirm it. Record the confirmed
        value in `repro_check.tolerance`. Fall back to the provisional `repro_tolerance` only when no
        measurement is available.
    -   Within the confirmed tolerance → record `repro_check` and continue. Outside → **block** and
        find the unpinned source of variation.
    -   Why measure: a tolerance fixed in advance either fails a healthy study — bf16, non-
        deterministic kernels, and multi-device reduction order can drift well past 1e-3 — or passes
        a broken one. The measurement costs one run that was going to happen anyway.

7.  **Budget check:** estimate the task's cost (arms x seeds x per-run cost measured in the pilot).
    If it exceeds `confirm_above`, or would push the study past its `compute_budget`, state the
    estimate and get explicit approval before launching.

8.  **Execute:** launch the runs. Monitor for divergence, OOM, and preemption. Apply `retry_policy`;
    beyond it, record the outcome and block.

9.  **Log:** append one row per run to `results.json` — including failed ones. A run that failed is
    recorded with its `run_status`, not deleted. Attach the artifact manifest (path, role, bytes,
    sha256). Never edit an existing row except to set `excluded` / `exclusion_reason`.

10. **Verify:** confirm the ledger matches reality — every launched run has a row, every completed
    row has the headline metric, no duplicate `run_id`, compute totals updated. Then compare the
    outcome against step 3's prediction and **state plainly whether the prediction held**. A
    prediction that failed is information; record it in the task notes rather than quietly moving on.

11. **Commit:**
    -   Stage configs, `results.json`, `plan.json`, and any harness code changed for the task.
    -   Commit with a clear message, e.g. `exp(sweep): lr sweep arm=proposed seeds=0-4`.
    -   Attach a git note with the task summary: prediction, what ran, headline numbers, whether the
        prediction held, and cost. `git notes add -m "<summary>" <commit_hash>`

12. **Record Completion:** set the task `status` to `"done"` in `plan.json`, set `commit_sha` to the
    short hash, fill `run_ids`, and recalculate the study's `progress` and `compute` in
    `studies.json`. Refresh `updated_at`.

13. **Commit Plan Update:** stage `plan.json` and `studies.json` and commit, e.g.
    `research(plan): Mark task 'lr sweep' as complete`.

### Correction & Amendment Workflows

1.  **In-flight refinements:** minor harness fixes while a task is `doing` are made in the active
    stream; if the fix changes results already logged, those runs are re-run, not patched.
2.  **Review corrections (`research-review`):** issues found in review are appended to `plan.json` as
    a `Review Fixes` phase so corrections are tracked and checkpointed.
3.  **Reversions (`research-revert`):** a task whose runs are invalid (wrong config, wrong data
    version, broken harness) is reverted: commits rolled back, its runs marked `excluded` with a
    reason, and its `status` reset to `backlog` for a clean re-run. Ledger rows are never deleted.
4.  **Declared deviations:** if the executed study must differ from the preregistration, append a
    dated **Deviations** entry to `design.md` stating what changed, why, and when it was decided —
    ideally before seeing the affected results. `research-analyze` surfaces every deviation.

## Phase Checkpoint Protocol

**Trigger:** immediately after a task completes that also concludes a phase in `plan.json`.

1.  **Announce** that the phase is complete and the checkpoint protocol has begun.
2.  **Ledger integrity:** every task in the phase has its `run_ids` in `results.json`; no run is
    missing a pin; failed runs are recorded with `run_status`; compute totals reconcile.
3.  **Interim aggregation:** compute the per-arm mean, dispersion, and n **for the runs so far**, and
    present them as a short table. Mark them explicitly as interim — the preregistered test is not
    run until the analysis stage, and reporting a p-value here would be optional stopping.
4.  **Sanity review:** state whether the phase's results are consistent with the predictions recorded
    in step 3 of the Run Workflow. Flag any arm whose variance is far larger than the others.
5.  **Manual verification plan:** present concrete steps for the user to verify the phase, e.g.:

    ```
    Phase 2 (main sweep) is complete. To verify:
    1. Open artifacts/<study_id>/figures/phase2_curves.png — training curves for all 10 runs.
    2. Confirm: all runs converged; no curve is flat or NaN after step 500.
    3. Run: python -m harness.report --study <study_id> --phase main
    4. Confirm: 10 rows, 2 arms x 5 seeds, no run_status other than "completed".
    ```

6.  **Await explicit user feedback:** ask *"Does this look right, or should anything be re-run?"* and
    **PAUSE**. Do not proceed without an explicit confirmation.
7.  **Attach a verification report** as a git note on the phase's last functional commit (do not
    create an empty commit): the ledger integrity result, the interim table, and the user's
    confirmation.
8.  **Record the checkpoint:** set the phase `status` to `"done"` and `checkpoint_sha` to the short
    hash; sync `phases_summary` in `studies.json`.
9.  **Commit:** `research(plan): Mark phase '<PHASE NAME>' as complete`.

## Quality Gates

Before marking any task complete, verify:

-   [ ] `prediction` and `falsification` were recorded before execution
-   [ ] All five pins present on every run in the task
-   [ ] Tree was clean at launch (or the run is marked `code_dirty` and backs no confirmatory claim)
-   [ ] Seeds >= `min_seeds` for any task backing a comparison
-   [ ] Failed/preempted runs recorded with `run_status`, not dropped
-   [ ] Artifact manifest complete (path, role, bytes, sha256); no checkpoint committed to git
-   [ ] Compute recorded: `wall_clock_s`, `accelerator_hours`, `est_cost_usd`
-   [ ] No GCG hyperparameter was tuned against this study's target-set EMR (§Target-set discipline)
-   [ ] `results.json` + attempt-log shards flushed to persistent storage (Drive, on Colab)
-   [ ] Actual GPU model recorded on every run
-   [ ] Config committed under `configs/<config_hash8>.yaml`
-   [ ] `plan.json` and `studies.json` in sync; `updated_at` refreshed
-   [ ] `.ai/research/studies.json`'s `project.path` equals `git rev-parse --show-toplevel`

## Experiment Code Standards

Research code is allowed to be scrappy in places, but not in these:

-   **One evaluation function**, shared by every arm. No per-arm metric implementations.
-   **Config in, no hidden globals.** Everything that affects a result is in the resolved config, or
    it will not be in the config hash and the run is unreproducible.
-   **Seed every RNG the stack exposes**, dataloader workers included.
-   **Fail loudly.** No silent `except: pass` around a metric computation; a NaN must stop the run,
    not become a 0.0 in the ledger.
-   **Log to the ledger, not only to the tracker.** W&B/MLflow are convenient views; `results.json`
    is the record.
-   **Type hints and docstrings on anything reused across studies.** The harness is infrastructure
    even when the experiment is throwaway.

## Definition of Done

A task is complete when:

1.  Prediction and falsification were recorded before the run
2.  Every run is pinned, executed, and logged to `results.json`
3.  Sanity checks passed (pilot) or the reproducibility check passed (pre-sweep)
4.  The prediction was compared against the outcome and the comparison stated
5.  Compute is recorded and within budget
6.  Configs and ledger are committed with a descriptive message
7.  A git note carries the task summary
8.  Task marked `done` with `commit_sha` and `run_ids` in `plan.json`, synced to `studies.json`

## Commit Guidelines

```
<type>(<scope>): <description>
```

| Type | Use |
|------|-----|
| `exp` | A run or sweep that produced evidence |
| `harness` | Experiment/infrastructure code |
| `data` | Dataset preparation, splits, filtering |
| `analysis` | Aggregation, statistics, figures |
| `research` | Harness bookkeeping (plan, registry, study lifecycle) |
| `docs` | Write-ups, notebook, register |
| `fix` | Correcting a harness or analysis bug |

```bash
git commit -m "exp(sweep): adapter rank {4,16,64} x 5 seeds on v3"
git commit -m "harness(eval): single shared macro-F1 implementation for all arms"
git commit -m "analysis(main): bootstrap CI + Holm correction over 5 comparisons"
git commit -m "fix(data): group split by patient_id, was leaking across rows"
```

## Incident Procedures

### A published or shared number turns out to be wrong
1.  Stop citing it immediately and say so to whoever received it.
2.  Mark the affected runs `excluded` with the reason; never delete the rows.
3.  Open a correction study that cites the archived `study_id`.
4.  Append the cause to `VALIDITY.md` as an `open` threat.
5.  Correct the `LAB_NOTEBOOK.md` entry in place with a dated correction line beneath it.

### Leakage discovered mid-study
1.  Halt the sweep — do not spend more compute on a contaminated split.
2.  Mark every affected run `excluded` with `exclusion_reason: "leakage: <detail>"`.
3.  Fix the split, bump `dataset_version`, and re-run from the pilot. Old and new runs are never
    pooled.

### Budget exhausted mid-sweep
1.  Stop launching and report actual versus estimated cost, with the gap explained.
2.  Present the cheapest completion that still answers the preregistered question — usually fewer
    sweep points at full seeds, never fewer seeds at full sweep points.
3.  Block for a decision. Do not quietly reduce seeds; that silently invalidates the analysis plan.
