# Independent statistics review — field-exposure-corrected E3 analysis

## Verdict

**CONCERNS.** The corrected H3 and H5 numbers are reproducible from the recorded attempts, and the
person-clustered bootstrap follows the study's two-block resampling plan. The correction is still a
post-result analysis, and it does **not** restore the E17 target-level pairing that the executed E3
control-selection path discarded. The corrected result may be reported as a disclosed sensitivity
analysis. It must not be described as a preregistered, fully matched D/C comparison.

## Independent recomputation

- Input: 4,200 checksum-verified attempt rows, covering 25 D people, 25 C people, 14 values of `k`,
  two fields, and the three fixed attack seeds `{42, 1337, 2024}`.
- Exclusion accounting: removing two D-SSN targets and two C-SSN targets at every `k` and seed removes
  exactly 168 rows, leaving 4,032. Each arm then has 48 targets: 23 SSNs and 25 emails, distributed
  over 25 people.
- H3 at `k=20`: D = 118/144 = **81.944%**; C = 118/144 = **81.944%**; therefore
  `D-C = 0.000` percentage points. The recorded 10,000-replicate person-clustered 95% interval is
  **[-8.958, +9.255] percentage points**, with raw centered-bootstrap `p=1.000`. An independent
  100,000-replicate bootstrap with a different random seed gave **[-9.058, +9.064]**, confirming
  the reported interval up to Monte Carlo variation. There are 25 people and 48 targets per arm;
  the three attack seeds are repeat measurements, not three independent model-training replicates.
- Field split at `k=20`: SSN D = C = 43/69 = **62.319%**, difference interval
  **[-18.841, +18.841] points**; email D = C = 75/75 = **100%**, with the conservative
  Wilson/Newcombe difference interval **[-13.319, +13.319] points**.
- H5: the observed pooled maximum of `D-C` is at `k=4`. The all-tied-maximizer bootstrap envelope is
  **[4, 48]**. The log-`k` quadratic coefficient is **-0.002132**, 95% interval
  **[-0.016068, +0.012101]**, one-sided exploratory `p=0.384`; 405/10,000 replicates have tied
  maxima. An independent 100,000-replicate run produced an argmax envelope of `[4,48]`, coefficient
  interval `[-0.015843,+0.011971]`, and `p=0.385`.
- Holm calculation: using the fixed four-slot family `{H1,H2,H3,H4}`, with the undefined H2 global
  test conservatively reserved at `p=1`, gives H1/H4 adjusted `p=0.00039996` and H2/H3 adjusted
  `p=1.000`. The arithmetic is correct. Because H3 was redefined after inspecting the data, this is
  a conditional sensitivity calculation; the correction does not recreate pristine confirmatory
  status.

## Findings requiring changes

1. **High — “paired C” is an inaccurate label.** Only one removed C target is the original E17 pair.
   The other original E17 control was never attacked, so the analysis removes the nearest attacked
   C-SSN under the three E17 covariates. More broadly, the executed E3 path reduced E17 pairs to a
   deduplicated and capped set of control people, discarding target-level pair links. Equal field
   counts after exclusion are not target pairing. Replace labels such as “C (paired target set)” and
   “post-result paired exclusion” with “C (field-count-balanced control set)” and “post-result
   field-exposure correction.”

2. **High — the preregistered balance gate still fails for email.** After correction, SSN balance is
   acceptable on the three recorded covariates: SMDs are `0.000`, `-0.079`, and `0.082`. Email SMDs
   remain **0.503 for character length, 0.613 for token length, and 0.513 for H(t)**, all far above
   the planned `|SMD|<0.1` criterion. The pooled SMDs are `0.110`, `0.359`, and `0.347`. Thus H5's
   low- and mid-`k` D/C curve can reflect target-difficulty imbalance as well as membership. At
   `k=20`, both email arms are saturated and the SSN covariates are balanced, so the numerical H3
   equality is less sensitive to this specific imbalance; it still does not license a general
   causal claim about membership.

3. **Medium — H3 is a null detection, not proof of equivalence.** The point difference is exactly
   zero, but the interval remains compatible with effects of roughly nine percentage points in
   either direction. State “no D/C difference was detected at `k=20`; under this analysis, effects
   outside approximately `[-9,+9]` points are excluded.” Do not state that D and C are
   indistinguishable unless an equivalence margin and equivalence test are specified.

4. **Medium — H5 needs a two-part verdict.** Its prespecified exploratory primary rule is met because
   the argmax interval `[4,48]` excludes endpoints `{1,64}`. The secondary curvature analysis does
   not corroborate a peak because its interval contains zero. Report: “the exploratory argmax rule
   suggests an interior maximum, but does not localize a reliable optimum; the quadratic diagnostic
   is inconclusive, and the D/C balance failure further limits interpretation.” Neither “H5 proved”
   nor an unqualified “H5 failed” matches the recorded evidence.

5. **Medium — the fallback C choice is post hoc but does not drive H3.** Across every eligible
   actually attacked C-SSN used as the fallback exclusion, the `k=20` pooled difference ranges only
   from **-1.389 to +0.694 percentage points**; the chosen nearest-covariate fallback yields 0. This
   supports numerical robustness of H3's null detection, but not target-level matching. Record this
   as a sensitivity result if the fallback rule is discussed in the manuscript.

6. **Low — boundary intervals depend on an assumed ICC.** Degenerate 0%/100% cells use Wilson and
   Newcombe/MOVER intervals with an assumed within-person ICC of 0.5 and a conservative target-only
   effective sample size. Their labels currently disclose this. Keep those intervals as method
   sensitivities and do not describe the assumed ICC as estimated from E3.

## Confirmations

- The exclusion rule does not inspect attack outcomes when choosing the fallback control; it uses
  character length, token length, and `H(t)`. The standardized squared distance for the selected
  fallback is `0.001133`.
- D and C people are resampled independently, while each person's single draw is reused over all
  values of `k`. This matches the preregistered two-block bootstrap and preserves within-person and
  across-`k` dependence.
- H1, H2, and H4 are control-only estimands and need not drop the four D/C targets. Their point
  estimates are therefore unaffected by this correction. H3, H5, and D/C descriptive figures are
  the appropriate outputs to supersede.
- H5 remains outside the confirmatory Holm family, as preregistered. Its quadratic p-value is an
  explicitly post-result diagnostic and is correctly left unadjusted.

## Claims warranted by this analysis

The corrected data support a narrow statement: after removing the two unexposed D-SSNs and two
control SSNs, no D/C difference was detected at `k=20` (`0.0` points, 95% CI approximately
`[-9.0,+9.3]`). The observed D/C curve reaches its largest value at `k=4`, and the exploratory
bootstrap places the maximizer somewhere from `k=4` to `k=48`; it does not identify `k=4` as a
stable optimum. The analysis does not support claims that the arms are equivalent, that E3 retained
full target-level matching, or that the curve isolates a pure membership effect independently of
target difficulty.
