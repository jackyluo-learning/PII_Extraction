# Analysis — `capacity_axis_20260902`

**Question**: does probe capacity `k` drive the forcing floor, and is there a capacity at which a
membership audit can be calibrated?
**Status**: complete. 42/42 shards, 4200 attempts, three seeds, `gpt2` (124M), `PII_GCG_ITERS=200`.
**Preregistration**: `design.md` · **Ledger**: `results.json` · **Output**: `results/e3_analysis.json`
**Raw evidence, in the repo**: `results/attempts/e3a__*.parquet`, `results/e3_hit_matrix.csv`,
`results/e3_nll_matrix.csv`, `results/e3_kmin.csv`

Every preregistered test was specified in `design.md` and implemented in `curve_stats.py` /
`survival.py` before the full curve was read. `analyze_e3.py` wires them to the data.

---

## Headline

**Under the paper's binary decision rule, no probe capacity can both keep the false-positive floor
acceptable and force anything at all.** The two requirements hold on disjoint ranges of `k`, and one
side of the gap is an information-theoretic impossibility rather than a power problem.

| | |
|---|---|
| Floor meets `α ≤ 1%` (CI upper bound) | `k ∈ {1, 2, 3}` |
| Forcing the *easiest* target requires | `k ≥ H(t)/log₂\|V\| = 55.29/15.62 = 3.54` |
| First grid point above that | `k = 4`, where the floor is already `α = 0.013` |

**This is a claim about `exact_match`, and it does not carry to the continuous score.** On the
balanced field, the AUC of `final_target_nll` — the paper's own §3.6 estimator — is 0.67 at
`k = 1, 2, 3`, precisely where `exact_match` is uniformly zero in both arms. See
`## The signal the binary rule cannot see`.

---

## What was run

| Pin | Value |
|---|---|
| Model | `gpt2` (124M), fine-tuned. No base-model arm |
| Environment | Cheaha A100 80GB, torch 2.6.0+cu124, single environment |
| Target subset | `target_subset_hash = 791fb10a21ea726e`, identical across Colab and Cheaha |
| Arms | 25 trained persons + 25 control persons, disjoint people |
| Fields | `ssn`, `email` → 100 targets, 150 attempts per arm per capacity |
| Capacities | `k ∈ {0, 1, 2, 3, 4, 6, 8, 12, 16, 20, 24, 32, 48, 64}` |
| Seeds | 42, 1337, 2024 |
| Bootstrap | 10 000 replicates, two-block, one person draw across all `k` |

**`k = 0` is not a point on this curve.** The `fixed` probe targets a different string from
`gcg_free`: `'qjohnson@example.com'` (7 tokens) versus `'Email: qjohnson@example.com'` (9 tokens,
with the field prefix). It is therefore a different probe *and* a different target, and every `H(t)`
the sweep uses must be read from `k ≥ 1`. Both arms are 0/150 there.

---

## The curve

Pooled, then split by field — because pooling averages a saturated field with an unsaturated one.

| `k` | `α_k` | 95% CI | `EMR(D)` | `τ̂rec` | 95% CI |
|---:|---:|---|---:|---:|---|
| 1–3 | 0.000 | [0.000, 0.000] | 0.000 | 0.000 | [0.000, 0.000] |
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

Raw counts by field, hits out of 75 attempts per cell:

| `k` | ssn D | ssn C | email D | email C |
|---:|---:|---:|---:|---:|
| 1–4 | 0/75 | 0/75 | 0–6/75 | 0–2/75 |
| 6 | 1/75 | 0/75 | 29/75 | 41/75 |
| 8 | 11/75 | 9/75 | 62/75 | 62/75 |
| 12 | 25/75 | 21/75 | 74/75 | 74/75 |
| **16** | 35/75 | 37/75 | **75/75** | **75/75** |
| 20 | 48/75 | 46/75 | 75/75 | 75/75 |
| 24 | 48/75 | 54/75 | 75/75 | 75/75 |
| 32 | 59/75 | 63/75 | 75/75 | 75/75 |
| 48 | 63/75 | 62/75 | 75/75 | 75/75 |
| 64 | 61/75 | 70/75 | 75/75 | 75/75 |

**Email saturates at `k = 16` and stays there.** Five of the thirteen capacities are pure ceiling
for that field: `τ̂rec` is structurally zero there, not measured as zero. SSN never saturates,
reaching 0.933 at most. Every pooled figure at `k ≥ 16` is half ceiling by construction.

The 13 per-`k` intervals are **descriptive**, not family members. One (`k = 64`) excludes zero
against 0.65 expected by chance, and its sign is negative.

---

## Hypotheses

Confirmatory family `{H1, H2, H3, H4}`, Holm-corrected at FWER 0.05; H5 exploratory.

### H1 — the floor rises with capacity · **SUPPORTED**

`ρ(k, α_k) = 0.9890`, 95% CI **[0.9779, 0.9945]**, Holm `p < 0.05`. The isotonic fit smooths one
inversion, `k = 48` (0.913) below `k = 32` (0.920) — exactly the sampling blip that motivated
replacing the code's zero-tolerance `np.diff` check with a trend test before any data existed.

### H2 — a usable critical capacity exists · **SUPPORTED on the floor, REFUTED in operation**

**Preregistered (floor only).** `k ∈ {1, 2, 3}` all have `α_k` CI upper bounds ≤ 1%. Bootstrap
`p ≈ 0`, Holm `p < 0.05`. The floor crosses up through 1% at an interpolated `k = 3.75`.

**Re-aimed (floor AND signal).** **No capacity satisfies both.** Where the floor is acceptable both
arms are identically zero under `exact_match`; where a signal could exist the floor has risen. The
floor-only reading alone is a false positive for usability — a floor condition is trivially met
wherever nothing happens.

### H3 — the calibrated signal at `k = 20` · **CI CONTAINS 0**

Pooled `τ̂rec = 0.0133`, 95% CI **[−0.0733, 0.1000]**, `p = 0.815`.

**The pooled bound is not the honest one.** Split by field:

| | `α` | `EMR(D)` | `τ̂rec` | MOVER CI | balanced |
|---|---:|---:|---:|---|---|
| ssn | 0.613 | 0.640 | +0.027 | [−0.158, +0.209] | yes |
| email | 1.000 | 1.000 | 0.000 | [−0.071, +0.071] | no |

Email contributes a structural zero at ceiling, which narrows the pooled interval without adding
information. **On the only field that can carry signal at `k = 20`, the bound is ±0.2, not ±0.1.**

### H4 — the forcing model `k_min = H/β` · **REFUTED**

Interval-censored log-log AFT, control arm, person-clustered bootstrap, **2000/2000 replicates
converged**. `γ = 3.4845`, 95% CI **[2.661, 4.191]**, excluding 1.

`β = exp(−intercept)` from this fit is **not quotable**: at 3.0 × 10⁵ bits/token against a ceiling of
15.62, the intercept is absorbing the slope misfit. `analyze_e3.py` refuses to present it as a rate
whenever `γ`'s CI excludes 1.

Why the model fails is visible in the covariate:

| Field | n | median `H(t)` | median `k_min` | `ρ(H, k_min)` within field |
|---|---:|---:|---:|---:|
| email | 25 | 66.9 | 6 | +0.488 |
| ssn | 25 | 72.9 | 12 | **−0.003** |

Within SSNs, self-information has **no** rank relationship with the forcing threshold. Across fields
`H` differs by 1.09× while `k_min` differs by 2.00×; a proportional model requires those to match.
The pooled `ρ = 0.518` is largely a between-field effect.

### H5 — an interior peak in `τ̂rec(k)` · **EXPLORATORY; criterion met on a flat curve**

`argmax = 4`, 95% CI **[4, 48]**, which excludes both endpoints. It is not a located peak: the
interval spans a factor of 12, 12 of 13 `τ̂rec` intervals contain zero, and the preregistration's own
refutation clause includes "or the curve is flat".

### Holm-corrected family

| | raw `p` | Holm `p` | reject at 0.05 |
|---|---|---|---|
| H1 | < 10⁻⁴ | < 10⁻⁴ | yes |
| H2 | < 10⁻⁴ | < 10⁻⁴ | yes |
| H3 | 0.815 | 0.815 | no |
| H4 | — | — | scored by its CI rule; refuted |

---

## Findings outside the hypotheses

### Proposition 1's bound is tight

Evaluated at each target's own self-information, `k_min(t) ≥ H(t)/log₂|V|`, on the control arm:

| | |
|---|---|
| Targets checked | 50 |
| Violating their own bound | **0** |
| Bound range | 3.54 – 5.17 |
| `k_min / bound` — min / median / max | **1.01** / 1.70 / 4.71 |
| Forced earliest (`k_min = 4`) | the two lowest-entropy targets, `H` = 55.3 and 61.9 |

The bound is never violated, one target sits on it, and the targets that fall first are the ones the
bound releases first. The empirical zero-region at `k = 1, 2, 3` is **required**, not a shortfall.

This corrects the first ledger reading, which compared the knee against `k*_thy = H∞/log₂|V| = 1.91`.
`H∞` is the format's combinatorial min-entropy; what is forced is a rendered string at 55–81 bits.
`design.md` L793–808 settled before any data that the two are never interchangeable.

### `β` is the paper's Def. 3, and it is field-dependent

`CODE_MAP.md` mismatch #1 records that **Paper Def. 3 is `median H(t)/k_min(t)` in bits/token**,
while `capacity_e3` computes `linregress(H_bits → k_min).slope` — the reciprocal, in tokens/bit. The
quantity below is the paper's definition, not a fallback improvised after H4 failed:

| | `β` (conservative) | `β` (optimistic) | share of the 15.62 ceiling |
|---|---:|---:|---:|
| email | 10.83 | 16.25 | 69% |
| ssn | **6.01** | 9.01 | 38% |
| pooled | 9.20 | 12.27 | 59% |

Right censoring is 0.000 — every target was forced — so the direct ratio needs no model; interval
censoring remains, hence the bracket. **The pooled row is a between-field artefact and must not be
quoted.** An auditor spanning both fields must use the smaller rate, since `k_force` increases in `H`
and decreases in `β`.

So E3 does deliver the paper's `β`. What it refutes is that `β` is a *constant* — the premise
`k_force = H/β` needs. Per target it ranges 3.32 to 15.48, a 4.7× spread.

### The signal the binary rule cannot see

`final_target_nll` is the paper's §3.6 continuous score (`score = −nll`, Mann-Whitney U,
`make_tables._auc`, Table 4's AUC column). E3's preregistered plan used `exact_match` only; the
column was collected but never read. Reading it:

| `k` | AUC (ssn, balanced) | 95% CI | `α` under `exact_match` |
|---:|---:|---|---:|
| 1 | 0.670 | [0.510, 0.821] | 0.000 |
| 2 | 0.672 | [0.517, 0.819] | 0.000 |
| 3 | 0.678 | [0.528, 0.826] | 0.000 |
| 4 | 0.656 | [0.498, 0.806] | 0.000 |
| 6 | 0.616 | [0.448, 0.771] | 0.000 |
| 8 | 0.557 | [0.386, 0.714] | 0.120 |
| 12 | 0.517 | [0.352, 0.683] | 0.280 |
| 64 | 0.422 | [0.267, 0.586] | 0.933 |

Person-clustered bootstrap, 4000 replicates. **The signal is strongest exactly where `exact_match`
is uniformly zero and the floor is 0.000.**

**This is not yet a finding.** The intervals are wide at 25 persons per arm; the three excluding 0.5
do so barely (lower bounds 0.510, 0.517, 0.528); they are 3 of 26 uncorrected intervals against 1.3
expected by chance; and adjacent capacities on the same targets are close to one independent test.

What makes it worth chasing is the shape, not any interval: a smooth monotone decay toward 0.5, in
the balanced field, with email pointing the same way (0.598 / 0.597 / 0.578) **despite an imbalance
that biases its AUC downward** — its trained targets are the higher-entropy, longer ones.

A mechanism fits: at `k = 1–3` the optimizer has almost no freedom, so the residual loss is
dominated by the model's own prior over the target, which is where memorization should show. At
large `k` the optimizer drives the loss down regardless and the signal washes out.

---

## Defects found, and their reach

| Defect | Reach |
|---|---|
| **`_matched_control_entries` discards E17's pairing** — it keeps only the control *names* from the `(trained, control)` pairs, and the arms are then subset to 25 independently. Balance does not survive: email `SMD = +0.51` on entropy, `+0.61` on token length; ssn passes at `+0.08` / `−0.07`. | Every D-vs-C quantity in the affected field. **Pre-existing and broader than E3**: `CODE_MAP.md` records E17's balance table as "not reported", so run2's Table 4, Figure 2, `τ̂rec` and AUC rest on the same unchecked function. |
| **The balance check read `k = 0`'s `target_H_bits`** — a different target string, giving SSN entropy 49.7 instead of 73.4. | The SMDs published in the first analysis run. Corrected here. |
| **`fit_loglog` failed 2000/2000** with `cannot reindex on an axis with duplicate labels`; a bare `except Exception: continue` hid the cause, making a pandas indexing bug read as an unidentifiable model. | H4 was unscoreable until fixed. Now 2000/2000 converge. |
| **`α → k*` reported the smallest qualifying `k`** — trivially 1 at every tolerance, since `α_k` rises. | The auditor deliverable. Corrected to the operating ceiling. |
| **H2's bootstrap `p` tested the floor while its verdict required floor and signal.** | The number entering Holm. Split into the two readings. |

---

## Threats and limits

| | |
|---|---|
| **Absorbing-state assumption violated** | 13/100 targets (7 control, 6 trained) were forced at some `k` and not at a larger one. The AFT model treats forcing as absorbing; this is the measured violation and belongs beside any `β`. |
| **Email saturates from `k = 16`** | Five of thirteen capacities carry no information for that field. Pooled figures there are half ceiling. |
| **`log H` spread is 0.379 nats** | Limits how sharply any slope could be estimated. Did not cause H4's refutation — `γ` is far from 1 — but a wider-entropy target set would test the model harder. |
| **`k = 4` is the soft spot** | `α = 0.013`, CI [0.000, 0.033], which *contains* 1%. The disjointness claim has no statistical support at the one point that matters. `n = 150` is too few at this rate. |
| **Single model, single scale** | `gpt2` 124M, no base-model arm. The floor is a property of model plus optimizer; nothing transfers without re-measurement. |
| **Fixed step budget** | 200 GCG iterations at every `k`. Larger `k` has more parameters at the same budget, so `α_k` there is a lower bound on an unbounded optimizer. |
| **Four outcome columns unread** | `steps_to_first_success`, `random_record_match`, `gen_len_tokens`, and the generations themselves. |

---

## Deviations

Recorded in `results.json` under `deviations`, `corrections` and `exploratory_findings`:

1. **Preregistration text correction**, before any test ran and not outcome-dependent: the threats
   table said the family was "H1–H5" where three other places said `{H1,H2,H3,H4}`. Holm's `m`
   changed from 5 to 4.
2. **Two analysis defects found by smoke-testing on synthetic data**, fixed before the real data was
   touched (the `α → k*` direction, and H2's `p`).
3. **The H4 bootstrap bug**, and the silent-`except` that hid it.
4. **The `k = 0` entropy misread** in the balance gate.
5. **Ledger correction** on the knee reading.
6. **The NLL/AUC reading**, filed as exploratory.

---

## What this changes

**For the paper's binary narrative.** The forcing floor rises steeply and predictably with capacity
(H1), the information-theoretic bound on forcing is tight (0/50 violations, min ratio 1.01), and
together these close the window an `exact_match` audit needs. Algorithm 1 step 3 is unexecutable at
`α = 1%` for this target class — not because the effect is too small to see, but because no capacity
is simultaneously quiet enough and expressive enough.

**For the formula.** `k_force ≈ H/β` does not survive. `β` is not a constant recoverable from `H`;
it is field-structured, and within SSNs `H` carries no information about the threshold. What can be
handed to an auditor is a per-field conservative rate (6.01 bits/token for SSNs), the free
information-theoretic go/no-go check `H_min/log₂|V|`, and the instruction to measure their own floor.

**For what E3 actually settled.** The certifiable `ε ≥ ln(TPR/FPR)` is 0.016 at `k = 20` — the audit
certifies essentially nothing there. The only non-trivial value on the whole axis is 1.099 at
`k = 4`, on 6 versus 2 hits out of 150.

**For the next study.** Two questions are now well posed:

1. **Is the disjointness an artefact of the decision rule?** The AUC evidence says the arms may
   separate at `k = 1–3` where `exact_match` is blind. This needs people, not capacity: the same
   grid at `k ∈ [1, 6]` with enough persons to put a usable interval on an AUC near 0.67.
2. **What predicts `k_min` if `H(t)` does not?** Token-level structure is the candidate — a 2×
   difference in threshold at 1.09× in entropy between two fields.

Neither needs a new pipeline. Both are cheap relative to the sweep already spent, because the
interesting region is small-`k`, which is the cheapest part of the axis.
