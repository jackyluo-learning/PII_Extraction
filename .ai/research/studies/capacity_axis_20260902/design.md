# Preregistration — capacity_axis_20260902

_The E3 capacity sweep. Type: `experiment`. Status: in design._

> Written section by section during the design stage; each confirmed section replaces one
> `_pending_` marker. Preregistration exists because once results are visible, every human being
> alive — including the author — will find a story that fits them. Fixing the hypothesis, the metric,
> and the test beforehand costs nothing now and cannot be done afterwards.

## Lineage — this is a revival, not a new design

This experiment was designed once before, as `capacity_response_20260831`, and abandoned on
2026-09-01 without spending compute. That archive's own closing instruction was explicit:

> "If the capacity sweep is revived, start from this design and fix the two problems above — do not
> rewrite the hypotheses from scratch."

**H1, H2, H3, the prediction, and `## What the Answer Changes` below are carried over verbatim from
that design.** They were fixed in advance, and rewriting them now — after a month of intervening
analysis — would destroy the only thing that makes a recorded prediction worth anything.

What has changed is that all three abandonment reasons now have concrete fixes:

| Abandonment reason (2026-09-01) | Status now |
|---|---|
| **1.** H2 needed `α_k ≤ 1%`, but 50 control individuals cap the rule-of-three upper bound at 2.95% — the threshold could be neither met nor refuted | **Fixed, at zero compute cost.** Controls never enter the training corpus (`corpus = pii_docs + public`; `neg_controls` go only into `target_registry`), so raising `PII_N_CONTROLS` to 150 requires **no retraining**. 150 individuals x 2 fields = 300 control targets ⇒ rule-of-three bound 1.0%, exactly at the threshold |
| **2.** Scope was ~3x the budget: 4 models x 13 k x 3 seeds ≈ 1040 accelerator-hours against ~312 available (never validated by a pilot) | **Fixed by scope, and now costed bottom-up.** The 13-point grid costs **12.3x one k=20 attack** per target, not 13x, because per-attack cost scales with sequence length `k+T`. GPT-2 124M alone at 50/arm x 3 seeds = **~33 A100-h**; adding GPT-2-medium = **~130 A100-h** |
| **3.** The study mixed a new experiment (the sweep) with densifying `k=20` to ≥3 seeds, which carried H3; the project then shifted to breadth over depth | **Dissolved.** `k=20` is *in* the grid, so running the sweep at 3 seeds densifies `k=20` as a **by-product at no additional cost**. H3 is now free rather than a competing objective |

It also inherits the codebase corrections established and verified in
`archive/convergent_validity_20260902` — see `## Reproducibility & Execution`.

## Question

In language models fine-tuned on a controlled synthetic corpus, how does the **number of free tokens
`k` in a GCG probe** affect

1. the extraction rate on never-trained records, `EMR(C)` — the forcing floor `α_k`
2. the extraction rate on trained records, `EMR(D)`
3. their difference, `τ̂rec = EMR(D) − EMR(C)`

and does an operating point `k⋆` exist that satisfies `α_k ≤ 1%` while retaining dynamic range?

**Population**: SSN and email targets across four self-fine-tuned models (GPT-2 124M/355M,
Pythia 1.4B/2.8B).
**Comparison**: across levels of `k`, paired design (one fixed target subset carried through every
`k`).

## Hypotheses

### H1 — the forcing floor rises monotonically with capacity

| | |
|---|---|
| **H0** | `α_k` is independent of `k` (a flat curve) |
| **Direction** | `α_k` is **monotone non-decreasing** in `k` |
| **Metric** | `EMR(C)`, grouped by `k` |
| **Refuted by** | No upward trend in `α_k` over `k ∈ [1, 64]` (Spearman rho's CI contains 0), or a significant decrease |

Refuting H1 **refutes the empirical claim that capacity drives forcing**. Proposition 1's bound would
still hold (it is an upper bound and predicts no particular value), but §7.2's narrative — "more
expressive probes force more" — would lose its support.

### H2 — a usable critical capacity k* exists

| | |
|---|---|
| **H0** | No `k ≥ 1` satisfies `α_k ≤ 1%` |
| **Direction** | Some `k⋆ ≥ 1` exists |
| **Metric** | The smallest `k` at which `α_k`'s 95% CI upper bound falls below 1% |
| **Refuted by** | At the smallest `k = 1`, `α_1`'s CI **lower** bound still exceeds 1% |

Refuting H2 means Corollary 1's `k*_thy ≈ 1.5` is empirically unreachable — **an unfavourable but
highly valuable result**: it would say this class of audit cannot be calibrated to a usable dynamic
range at any capacity, and Algorithm 1's step 3 ("audit at k*") becomes unexecutable.

### H3 — the calibrated signal is bounded at adequate power

| | |
|---|---|
| **H0** | `τ̂rec = 0` |
| **Direction** | None assumed |
| **Metric** | `τ̂rec`'s 95% CI at the densified `k=20` point |
| **Refuted by** | The CI **excludes** 0 |

**The only one of the three that could directly rewrite the paper's conclusion.** If the CI excludes
0, a measurable memorization signal exists and the empirical narrative must change from
"non-identifiable" to "small but measurable at this capacity". If the CI contains 0 **and is
narrow**, the claim upgrades from "we cannot tell" to "we can rule out an effect larger than X" —
which is what the paper actually needs (see `## What the Answer Changes`).

H1 and H2 are publishable findings whether supported or refuted.



## What the Answer Changes`).

H1 and H2 are publishable findings whether supported or refuted.

## Prediction

_Recorded before any run. Its value lies precisely in being falsifiable after the fact._

### The researcher's prior

- **Curve shape / inflection point: no strong prior.** The researcher does not commit to where
  `α_k` begins to rise. This is recorded as "no prior" rather than defaulting to the designer's
  estimate.
- **H3 (`τ̂rec` at the densified `k=20`): the CI still contains 0, but narrows.** That is, the
  paper's existing narrative holds, and upgrades from "cannot be measured" to "an effect larger than
  X can be excluded".

### The designer's estimate (for post-hoc comparison only; not the researcher's position)

| Quantity | Estimate | Basis |
|---|---|---|
| `α_1` | 0–5%, likely near 0 | 15.6 bits < the SSN's 29.9 bits, so Proposition 1's bound is tight here (`2^(15.6−29.9)` is about 5e-5) |
| `α_2` | < 10% | 31.2 bits only just clears the threshold |
| Curve shape | Sigmoid, inflection at `k` = 4–12 | The bound goes vacuous at `k=2`, but the realized steering rate `β` should sit below the theoretical ceiling, so the rise lags the theory |
| `α_20` | about 39% | Reproducing run2's single-seed observation |
| `α_64` | 60–85%, short of 100% | Only the unbounded soft prompt reaches 100%; 64 discrete tokens remain constrained by vocabulary discreteness |
| `k⋆(1%)` | 1 or 2, slightly above `k*_thy = 1.49` | The theoretical bound is a worst-case upper bound |
| `τ̂rec` CI width | Narrows to about 0.58x (1/sqrt(3)) | Three times the seeds |

### The least certain, most informative quantity

**The inflection point.** If it sits tight against the theoretical threshold (`k` = 2–3), `β` is
close to `log2|V|` and the optimizer nearly saturates the nominal channel. If it sits far out at
`k` = 16–32, `β` is a small fraction of the theoretical value. **That gap is `β` (Def. 3), and it is
this study's highest-information output.**

## What the Answer Changes

**The core: H2 decides whether the paper offers a prescription or only a warning.**

§9's prescription to auditors is "choose the probe's capacity rather than inheriting `k=20` from
jailbreaking". That sentence **is actionable advice only if `k*` exists and is measurable**;
otherwise the paper can say "your current practice is broken" but offer no replacement.

| Outcome | Effect on the paper |
|---|---|
| **H1 supported** | §7.2's qualitative claim gains quantitative support; Figure 4 goes from "analytic curve + 1 isolated point" to a measured curve |
| **H1 refuted** | The "capacity drives forcing" claim collapses and the whole capacity-axis framing needs rewriting. Proposition 1 survives as a bound but loses empirical meaning |
| **H2 supported** | Algorithm 1's step 3 becomes executable; the paper can name a concrete operating point, upgrading from warning to prescription |
| **H2 refuted** | **The more important negative result**: this class of audit cannot be calibrated to a usable dynamic range at any capacity. The contribution shifts from "how to fix it" to "why it cannot be fixed" — still publishable, but a different conclusion |
| **H3 CI excludes 0** | The "non-identifiable" empirical narrative must be rewritten as "small but measurable" |
| **H3 CI contains 0 and is narrow** | Upgrades from "absence of evidence" to "a bounded measurement" — necessary to support Proposition 2's empirical face |

**What the next study depends on**: once `β` and `k*` are measured, E13 (the ACR head-to-head)
becomes computable immediately (it depends on `k_min`), and `Mem(t)` (Def. 5) moves from
unimplemented to computable.

### Deviations from the carried-over text

The hypotheses above are verbatim. Two things they say are no longer true of this study's scope, and
are corrected here rather than by editing the preregistered text:

1. **Population.** The carried text says "four self-fine-tuned models (GPT-2 124M/355M, Pythia
   1.4B/2.8B)". This study runs **GPT-2 124M first (~33 A100-h), with GPT-2-medium gated on the
   pilot (+~97 A100-h)**. Both Pythia models are out of scope — they are 86% of the cost of a
   four-model sweep and `pythia-2.8b` alone exceeds Cheaha's 48-hour cap fivefold. Any claim about
   model-size dependence of `α_k` is therefore **out of scope for this study**, and must not be made
   from it.
2. **H3's mechanism.** The carried text frames H3 as depending on "the densified `k=20` point",
   which was originally a separate, competing objective. It is now a by-product: `k=20` is in the
   grid, so running the sweep at 3 seeds densifies it for free. H3's null, direction, metric, and
   refutation criterion are unchanged.

Everything else — including the recorded prediction and its designer-estimate table — stands as
written on 2026-08-31.

## Variables

_pending_

## Arms

_pending_

## Experiment Pipeline

_pending_

## Data

_pending_

## Analysis Plan

_pending_

## Baselines & Prior Art

_pending_

## Reproducibility & Execution

_pending_

## Threats to Validity

_pending_

## Success Criteria

_pending_

## Open Questions for the Protocol

_pending_

## Deviations

_pending_

