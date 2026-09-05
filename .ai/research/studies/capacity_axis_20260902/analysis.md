# Analysis — `capacity_axis_20260902`

**Study**: does probe capacity `k` drive the forcing floor, and is there a capacity at which a
membership audit can be calibrated?
**Status**: complete. 42/42 shards, 4200 attempts, three seeds, `gpt2` (124M), `PII_GCG_ITERS=200`.
**Ledger**: `results.json` · **Preregistration**: `design.md` · **Output**: `results/e3_analysis.json`

Every test below was specified in `design.md` and implemented in `curve_stats.py` / `survival.py`
before the full curve was read. `analyze_e3.py` wires them to the data and decides nothing.

---

## Headline

**At a 1% floor tolerance, no probe capacity can both keep the floor acceptable and force anything
at all.** The two requirements are satisfied on disjoint ranges of `k`, and the gap is not a power
problem — one side of it is an information-theoretic impossibility.

| | |
|---|---|
| Floor meets `α ≤ 1%` (CI upper bound) | `k ∈ {1, 2, 3}` |
| Forcing the *easiest* target requires | `k ≥ H(t)/log₂|V| = 55.29/15.62 = 3.54` |
| First grid point above that | `k = 4`, where the floor is already `α = 0.013` |

Below `k = 4` nothing can be forced, so there is no signal to calibrate. At `k = 4` and above the
floor has left the tolerance. **The usable-floor region and the forceable region do not overlap.**

This is the answer to the question the study was built to ask, and it is an unfavourable one for
Algorithm 1 step 3 ("audit at `k*`"): for this target class that step is unexecutable at `α = 1%`.

---

## What was run

| Pin | Value |
|---|---|
| Model | `gpt2` (124M), fine-tuned; single environment (Cheaha A100 80GB, torch 2.6.0+cu124) |
| Target subset | `target_subset_hash = 791fb10a21ea726e` — identical across Colab and Cheaha |
| Arms | 25 persons trained (D) + 25 persons control (C), disjoint people |
| Fields | `ssn`, `email` → 150 targets per arm per capacity |
| Capacities | `k ∈ {0, 1, 2, 3, 4, 6, 8, 12, 16, 20, 24, 32, 48, 64}`; `k = 0` is a fixed probe |
| Seeds | 42, 1337, 2024 |
| Steps | `PII_GCG_ITERS = 200`, constant across `k` |
| Bootstrap | 10 000 replicates, two-block (arms drawn independently), one draw across all `k` |

The `k = 0` anchor was read first, as the preregistration requires: **`α₀ = 0.000`, `EMR(D)₀ = 0.000`**
on 150 targets per arm. The fixed probe forces nothing in either arm, so every hit below is
attributable to the optimizer, not to the prompt template.

---

## The curve

`α_k` is the forcing floor (control arm); `τ̂rec = EMR(D) − α_k` is the calibrated signal.

| `k` | `α_k` | 95% CI | `EMR(D)` | `τ̂rec` | 95% CI |
|---:|---:|---|---:|---:|---|
| 1 | 0.000 | [0.000, 0.000] | 0.000 | 0.000 | [0.000, 0.000] |
| 2 | 0.000 | [0.000, 0.000] | 0.000 | 0.000 | [0.000, 0.000] |
| 3 | 0.000 | [0.000, 0.000] | 0.000 | 0.000 | [0.000, 0.000] |
| 4 | 0.013 | [0.000, 0.033] | 0.040 | +0.027 | [−0.013, 0.080] |
| 6 | 0.273 | [0.207, 0.340] | 0.200 | −0.073 | [−0.180, 0.027] |
| 8 | 0.473 | [0.400, 0.547] | 0.487 | +0.013 | [−0.093, 0.113] |
| 12 | 0.633 | [0.567, 0.700] | 0.660 | +0.027 | [−0.067, 0.120] |
| 16 | 0.747 | [0.687, 0.807] | 0.733 | −0.013 | [−0.093, 0.073] |
| 20 | 0.807 | [0.740, 0.867] | 0.820 | +0.013 | [−0.073, 0.100] |
| 24 | 0.860 | [0.800, 0.920] | 0.820 | −0.040 | [−0.133, 0.053] |
| 32 | 0.920 | [0.880, 0.953] | 0.893 | −0.027 | [−0.093, 0.040] |
| 48 | 0.913 | [0.860, 0.960] | 0.920 | +0.007 | [−0.060, 0.080] |
| 64 | 0.967 | [0.940, 0.993] | 0.907 | −0.060 | [−0.113, −0.007] |

These 13 intervals are **descriptive**, not family members. One of them (`k = 64`) excludes zero;
under 95% coverage the expected number from chance alone is 0.65, so it is not promoted to a
finding. Its sign is negative — trained targets forced *less* often than controls — which is what a
ceiling artefact looks like, not a memorization signal.

---

## Hypotheses

Confirmatory family `{H1, H2, H3, H4}`, Holm-corrected at FWER 0.05. H5 sits outside it as
exploratory (`design.md` L846/L849/L858).

### H1 — the floor rises with capacity · **SUPPORTED**

`ρ(k, α_k) = 0.9890`, 95% CI **[0.9779, 0.9945]**, bootstrap `p < 10⁻⁴`, Holm-adjusted `p < 0.05`.
The isotonic summary is `[0, 0, 0, 0.013, 0.273, 0.473, 0.633, 0.747, 0.807, 0.860, 0.917, 0.917,
0.967]`.

The pooled-adjacent-violators fit smooths exactly one inversion, `k = 48` (0.913) sitting below
`k = 32` (0.920). The preregistration replaced the code's zero-tolerance `np.diff >= 0` check with
this trend test precisely because such an inversion was near-certain under sampling noise; it
occurred, and it did not disturb the verdict.

### H2 — a usable critical capacity exists · **SUPPORTED on the floor, REFUTED in operation**

The two readings must be reported together, because separately each is misleading.

**As preregistered (floor only).** `H0`: no `k ≥ 1` satisfies `α_k ≤ 1%`. Refuted: `k ∈ {1, 2, 3}`
all have `α_k` CI upper bounds at or below 1%. Bootstrap `p ≈ 0`, Holm-adjusted `p < 0.05`. The
floor crosses up through 1% at an interpolated `k = 3.75`.

**As re-aimed (floor AND signal).** **No capacity satisfies both.** Where the floor is acceptable
(`k ≤ 3`) both arms are identically zero, so there is no dynamic range to calibrate; where a signal
could exist the floor has already risen. `curve_stats.usable_points` was written to distinguish
these cases before the data existed, and the data landed on the negative branch.

The floor-only reading alone would be a false positive for the audit's usability: a floor condition
is trivially satisfied wherever nothing happens at all.

### H3 — the calibrated signal at `k = 20` · **CI CONTAINS 0**

`τ̂rec = 0.0133`, 95% CI **[−0.0733, 0.1000]**, `p = 0.815`, half-width 0.087.

**The bound is the result.** At `k = 20` with 150 targets per arm, an effect larger than 0.100 in
absolute value is excluded. This is the upgrade the paper needs — from "we cannot tell" to "we can
rule out an effect above 10 percentage points" — not a null result to be reported as absence.

### H4 — the forcing model `k_min = H/β` · **REFUTED**

Interval-censored log-log AFT on the control arm, person-clustered bootstrap, 2000/2000 replicates
converged.

`γ = 3.4845`, 95% CI **[2.6614, 4.1908]**. The CI excludes 1, so proportionality is refuted.

**`β = exp(−intercept)` must not be quoted from this fit.** It comes out at 3.0 × 10⁵ bits/token
against a ceiling of `log₂|V| = 15.62` — the intercept is absorbing the slope misfit, not measuring
a steering rate. `analyze_e3.py` now refuses to present it as a rate whenever `γ`'s CI excludes 1.

Why the model fails is visible in the covariate:

| Field | n | median `H(t)` | median `k_min` | `ρ(H, k_min)` within field |
|---|---:|---:|---:|---:|
| email | 25 | 66.9 | 6 | +0.488 |
| ssn | 25 | 72.9 | 12 | **−0.003** |

Within SSNs, self-information has **no** rank relationship with the forcing threshold. Across
fields, `H` differs by 1.09× while `k_min` differs by 2.00× — a proportional model requires those
ratios to match, and they differ by a factor of 1.8. The pooled correlation (`ρ = 0.518`) is
therefore largely a between-field effect, not evidence for the model.

`log H` spans only 0.379 nats across the control targets, which is a genuine limit on how sharply
any slope could have been estimated. It is not, however, why the fit failed: the fit converged
everywhere and located `γ` well away from 1.

### H5 — an interior peak in `τ̂rec(k)` · **EXPLORATORY; criterion met on a flat curve**

`argmax = 4`, 95% CI **[4, 48]**, which excludes both grid endpoints, so the literal interior
criterion is satisfied. It should not be read as a located peak:

- the interval spans a factor of 12 on a 13-point grid;
- 12 of 13 `τ̂rec` intervals contain zero, so this is an argmax over noise, and the
  preregistration's own refutation clause includes "or the curve is flat";
- H5 was labelled underpowered at `n_eff ≈ 33` per point before any data existed.

**No operating point is located by this study.**

### Holm-corrected family

| | raw `p` | Holm `p` | reject at 0.05 |
|---|---|---|---|
| H1 | < 10⁻⁴ | < 10⁻⁴ | yes |
| H2 | < 10⁻⁴ | < 10⁻⁴ | yes |
| H3 | 0.815 | 0.815 | no |
| H4 | — | — | scored by its CI rule (`γ`'s CI must contain 1); refuted |

---

## Two findings that were not hypotheses

### Proposition 1's bound is tight

Evaluated at each target's own self-information, `k_min(t) ≥ H(t)/log₂|V|`:

| | |
|---|---|
| Control targets checked | 50 |
| Violating their own bound | **0** |
| Bound range | 3.54 – 5.17 |
| `k_min / bound` — min / median / max | **1.01** / 1.70 / 4.71 |
| Forced earliest (`k_min = 4`) | the two lowest-entropy targets in the set, `H` = 55.3 and 61.9, bounds 3.54 and 3.97 |

The bound is never violated, one target sits essentially on it, and the targets that fall first are
exactly the ones the bound releases first. The empirical zero-region (`α = 0.000` at `k = 1, 2, 3`)
is not the optimizer underperforming — it is **required**.

This corrects the first reading recorded in the ledger, which compared the measured knee against
`k*_thy = H∞/log₂|V| = 1.91` and concluded the optimizer needs about twice the minimum. `H∞` is the
SSN format's combinatorial min-entropy; what is actually being forced is a rendered string whose
self-information under the reference model is 55–81 bits. `design.md` L793–808 settled before any
data that the two entropies are never interchangeable — both comparisons are legitimate, but the
`H∞` one cannot score a claim about forcing actual strings. The correction is recorded in
`results.json`.

### `β` is field-dependent, and the pooled figure should not be used

With right censoring at 0.000, every target was forced, so the direct ratio needs no model.
Interval censoring remains, so each target carries a bracket.

| | `β` conservative | `β` optimistic | share of the 15.62 ceiling |
|---|---:|---:|---:|
| email | 10.83 | 16.25 | 69% |
| ssn | **6.01** | 9.01 | 38% |
| pooled | 9.20 | 12.27 | 59% |

The pooled row is an artefact of the field split and should not be quoted. An auditor working
across both fields must use the **smaller** rate — `k_force` increases in `H` and decreases in `β`,
so the field with the lowest `β` sets the requirement.

---

## The auditor-facing deliverable

`α → k*(α)`, where `k*` is the **largest** capacity whose floor still meets the tolerance — an
operating ceiling, since `α_k` rises in `k`.

| `α` | `k*` (point) | `k*` (CI upper rule) | `k*_thy` (Cor. 1, `H∞`) |
|---:|---:|---:|---:|
| 0.001 | 3 | 3 | 1.28 |
| 0.005 | 3 | 3 | 1.42 |
| 0.01 | 3 | 3 | 1.49 |
| 0.02 | 4 | 3 | 1.55 |
| 0.05 | 4 | 4 | 1.64 |
| 0.10 | 4 | 4 | 1.70 |

`k*` moves by one token across two orders of magnitude in `α`, which is the same insensitivity
Corollary 1 predicts and the reason the study was not designed to resolve `α` at 1%.

**Read against the headline, this table is a negative result**: every `k*` in it is at or below 4,
and forcing requires `k ≥ 3.54`. The auditor is being told the ceiling and the floor of the usable
window are the same point.

---

## Threats and limits

| | |
|---|---|
| **Absorbing-state assumption violated** | `non_monotone_fraction = 0.140`. 14% of control targets were forced at some `k` and not at a larger one. The AFT model treats forcing as absorbing; this is the measured extent of the violation and must appear beside any `β`. |
| **`log H` spread is 0.379 nats** | A narrow covariate limits how sharply any slope could be estimated. It did not cause H4's refutation — `γ` is 2.66 σ-widths clear of 1 — but a target set spanning more entropy would test the model harder. |
| **Single model, single scale** | `gpt2` 124M only. Nothing here transfers to larger models without re-measurement; the floor is a property of the optimizer against a specific model. |
| **Fixed step budget** | `PII_GCG_ITERS = 200` at every `k`. A larger `k` has more parameters to fit at the same budget, so `α_k` at large `k` is a lower bound on what an unbounded optimizer achieves. |
| **H5 underpowered by design** | `n_eff ≈ 33` per point. Buying the peak back needs more *people*, not more seeds. |
| **13 descriptive intervals** | Not corrected and not promoted; `k = 64` excluding zero is within chance. |

---

## Deviations

Recorded in `results.json` under `deviations` and `corrections`:

1. **Preregistration text correction** (before any test ran, not outcome-dependent). The threats
   table said the confirmatory family was "H1–H5"; three other places said `{H1,H2,H3,H4}` with H5
   exploratory. The stale line was corrected, changing Holm's `m` from 5 to 4.
2. **Two analysis defects found by smoke-testing on synthetic data**, both fixed before the real
   data was touched: the `α → k*` deliverable reported the smallest rather than the largest
   qualifying `k`, and H2's bootstrap `p` tested the floor alone while its verdict required floor
   and signal.
3. **H4 bootstrap bug.** `fit_loglog` failed 2000/2000 with `cannot reindex on an axis with
   duplicate labels` — a clustered resample duplicates index labels and lifelines' internal reindex
   raises. Fixed with `reset_index(drop=True)`. The failure had been silently swallowed by a bare
   `except Exception: continue`, which made a plain bug read as an unidentifiable model; the handler
   now keeps a census of causes.
4. **Ledger correction** on the knee reading, described above.

---

## What this changes

**For the paper.** The empirical narrative moves from "non-identifiable" to a sharper and more
defensible claim: the forcing floor rises steeply and predictably with capacity (H1), the
information-theoretic bound on forcing is tight (0/50 violations, min ratio 1.01), and **these two
facts together close the window the audit needs**. Algorithm 1 step 3 is unexecutable at `α = 1%`
for this target class — not because the effect is too small to see, but because no capacity is
simultaneously quiet enough and expressive enough.

H3 supplies the bound the paper actually needed: at `k = 20`, no effect above 0.100.

**For the formula.** `k_force ≈ H/β` does not survive as stated. `β` is not a per-target constant
recoverable from `H`; it is field-structured, and within the SSN field `H` carries no information
about the threshold at all. What an auditor can be handed is a **per-field conservative rate**
(`β = 6.01` bits/token for SSNs) and the warning that the pooled figure is an artefact.

**For the next study.** Two questions are now well posed and neither needs a new pipeline:

1. Does the disjointness survive at larger model scale, where the floor may sit differently
   relative to the same information-theoretic bound?
2. What predicts `k_min` if `H(t)` does not? Token-level structure is the obvious candidate — the
   `ssn`/`email` gap is 2× in threshold at 1.09× in entropy.
