# Abandoned at design stage — 2026-09-01

| | |
|---|---|
| Study ID | `capacity_response_20260831` |
| Type | `experiment` |
| Created | 2026-08-31T22:04:53-05:00 |
| Abandoned | 2026-09-01 |
| Status reached | `backlog` — design only |
| Design sections confirmed | 4 of 14 (Question, Hypotheses, Prediction, What the Answer Changes) |
| Protocol / plan / runs | none |

Never registered a protocol, a plan, or a single run. No evidence exists; only the design below.

## Why

Three reasons. The first two surfaced during a design review before any compute was spent; the third
was a change of research direction:

1. **H2 was unanswerable at the available sample size.** It required demonstrating `α_k ≤ 1%`, but
   the corpus holds only 50 negative-control individuals (100 control targets at 2 fields). With
   zero observed successes the 95% upper bound is 2.95% (rule of three) — the 1% threshold could
   neither be met nor refuted. Reaching it needs ~300 control targets, i.e. `PII_N_CONTROLS=150`.

2. **The scope exceeded the budget by roughly 3×.** Estimated from run2's allocated walltimes,
   4 models × 13 k-values × 3 seeds ≈ 1040 accelerator-hours against ~312 available in the
   pre-submission window. (That estimate was never validated by a pilot.)

3. **The research direction changed.** The study mixed a genuinely new experiment (the E3 capacity
   sweep) with a strengthening of an existing one (densifying `k=20` to ≥3 seeds, which carried H3).
   The project then shifted to prioritising **breadth across unrun experiments** over deepening E1,
   which removes H3's rationale and de-prioritises the expensive sweep.

## What is still reusable

H1 (monotonicity of `α_k` in `k`) and H2 (existence of a usable `k⋆`), with their refutation
criteria, plus the recorded prediction. If the capacity sweep is revived, start from this design and
fix the two problems above — do not rewrite the hypotheses from scratch.

The design as it stood at abandonment is preserved verbatim in `design.md` beside this file.


## What this directory holds

Normal close-out archives four evidence documents (`design.md`, `protocol.md`, `results.json`,
`analysis.md`) and deletes the working files. This study only ever produced the first of those, so
the archive also carries the metadata and registry entry that would otherwise be lost — for an
abandoned study there is no results ledger to carry the provenance, and the creation timestamp is
what makes "this was preregistered in advance" checkable.

| File | Role |
|---|---|
| `design.md` | The preregistration verbatim as it stood at abandonment |
| `ABANDONED.md` | This file — why it stopped, and what is reusable |
| `metadata.json` | Study type and timestamps, recovered from commit `a35aa6d` |
| `registry_entry.json` | The `studies.json` entry as it stood, recovered from `a35aa6d` |

Everything here is also recoverable from git at `a35aa6d`; these copies exist so the archive is
readable without git archaeology.

Archived documents are immutable. Correcting anything here means opening a new study that cites this
`study_id`, not editing this directory.
