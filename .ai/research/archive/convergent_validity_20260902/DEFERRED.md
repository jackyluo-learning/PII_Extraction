# Deferred at design stage — 2026-09-02

**Deferred, not abandoned.** The design is verified and sound; it lost on cost-effectiveness, not on
validity. It remains the only candidate that can light up `τ̂mod` in Table 2, and it should be
revived once the capacity axis is measured.

| | |
|---|---|
| Study ID | `convergent_validity_20260902` |
| Type | `experiment` |
| Created | 2026-09-02T18:28:49-05:00 |
| Deferred | 2026-09-02 |
| Status reached | `backlog` — design complete and **verified across all five domains** |
| Design sections | **14 of 14 confirmed**, no `_pending_` markers |
| Protocol / plan / runs | none |
| Superseded by | `capacity_axis_20260902` (the E3 capacity sweep) |

No protocol, no plan, no runs. No evidence exists; only the design and its verification record.

## Provenance

| Commit | Date | What it did |
|---|---|---|
| `6130585` | 2026-09-02 | Preregistered the study; dropped E5 with recorded rationale |
| `cde8730` | 2026-09-02 | Applied methodology / statistics / baselines verification findings |
| `07dede9` | 2026-09-02 | Applied reproducibility / data verification findings |
| `fdeb0b4` | 2026-09-02 | Recorded checkpoint loss; costed retraining at ~9 A100-h |

## Verification record

All five specialist domains reviewed the completed design. Every finding was resolved in the
document before deferral.

| Domain | Verdict | Findings resolved |
|---|---|---|
| Statistics | **FAIL** | 4 (unpassable sanity gate, two-block bootstrap, missing Newcombe, Holm family) |
| Reproducibility | **FAIL** | 6 (four unrecorded pins, flush-once preemption loss, `auto` batch gate, compute estimate) |
| Methodology | CONCERNS | 4 |
| Baselines | CONCERNS | 3 |
| Data | CONCERNS | 6 (C4 fallback, control-arm cap, provenance error, balance-table tautology) |

Both FAIL verdicts were resolved, not waived. The design as deferred is the corrected version.

## Why deferred

**Cost-effectiveness against E3, decided by the researcher on 2026-09-02.** Not a validity problem.

1. **The compute is dominated by two models that buy little.** The first bottom-up estimate put the
   recommended scope at **~430 A100-hours** against a ~480-hour window, with `pythia-2.8b` alone at
   ~247 h (57% of the budget) — a model that exceeds Cheaha's 48-hour cap fivefold and whose run2
   arm held 12 people (49.5 pp MDE). The estimate additionally carries a ~10x uncertainty band
   against run2's own SLURM walltime requests.
2. **It is monolithic, so it schedules badly.** The expensive cells cannot be sharded; `pythia-2.8b`
   needs six-plus chained `afterok` jobs on the busiest queue.
3. **E3 buys more per hour.** The capacity sweep moves three formal objects from ◦ to ✓
   (`β`, `k⋆`, `Mem(t)`) against this study's one (`τ̂mod`), turns Figure 4 from an analytic curve
   plus a single point into a measured curve, unblocks E13, and answers the auditor-facing question
   ("at a given α, how large may k be?") that this study cannot touch. It also shards cleanly by `k`.

None of these is a defect in this design. Every one is a statement about what else the same hours
could buy.

## What is reusable — and most of it already has been

This design's corrections were **not** archived away; they were carried into
`capacity_axis_20260902` because they are properties of the codebase, not of this study:

| Carried forward | Why it transfers |
|---|---|
| **The two-block joint bootstrap** | D-persons and C-persons are disjoint while repeated measures are paired — the same structure the capacity sweep has across `k` |
| **Degenerate-arm intervals** (Wilson / Newcombe-MOVER / paired exact) | `grep` confirms no implementation exists anywhere; any study with a 0/n cell needs all three |
| **The four unrecorded pins and the run manifest** | Nothing in pipeline B records git SHA, config, environment or GPU model |
| **Per-person `AttemptLogger` flushing** | `flush()` runs once per sweep, so a Colab preemption destroys the whole shard |
| **The `effective_eval_batch` fix** | `auto` gates on a literal string `_auto_hw()` never sets, so it guards training but not GCG |
| **`PII_N_CONTROLS=150`** | Controls never enter the corpus, so enlarging the pool is free of retraining |
| **The C4 halt condition** | The public-passage fallback is Common-Crawl-derived and can introduce real PII |
| **The contamination posture** | Faker's SSN space and reserved email domains, plus why a non-zero `EMR_base` is forcing rather than contamination |
| **The covariate balance table, with two SMDs** | The matched-pair SMD is near-tautological; the deduplicated-marginal SMD is the real test of A1 |

## What is NOT carried forward, and remains only here

The 2 x 2 itself — the base-model row, `τ̂mod`, the A3 test (`Δ_A3`), the `τ̂_base` sanity cell, and
the identity `τ̂mod = τ̂rec + Δ_A3 − τ̂_base`. **`τ̂mod` is still the only route to lighting up
Proposition 4 in Table 2**, and no other planned experiment touches assumption A3.

## Reviving it

Start from `design.md` as it stands — it is verified, not a draft. Two things to re-decide:

1. **Model count.** The unresolved question at deferral. `pythia-2.8b` should almost certainly be
   dropped; `pythia-1.4b` at reduced n preserves the LoRA-vs-full-fine-tune contrast for ~49 h.
2. **The compute estimate.** `capacity_axis_20260902`'s pilot measures real per-attack cost and
   collapses the 10x band. Re-price this study from that measurement rather than from the
   assumptions in its Analysis Plan.

The recorded predictions (H1 "会，且两者接近"; H2 "会") stand and must not be rewritten on revival —
they are only worth something because they were fixed in advance.
