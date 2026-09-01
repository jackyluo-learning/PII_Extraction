# Preregistration — capacity_response_20260831

_Capacity–forcing response curve. Type: `experiment`. Status: in design._

> This file is written section by section during the design stage; each confirmed section replaces
> one `_pending_` marker.
> Preregistration exists because once results are visible, every human being alive — including the
> author — will find a story that fits them. Fixing the hypothesis, the metric, and the test
> beforehand costs nothing now and cannot be done afterwards.

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

_(Empty at design time. If execution must depart from this preregistration, append a dated entry
here.)_
