# Independent statistics-reviewer — Results Audit

Verdict: numerical recomputation agrees; CONCERNS remain on confirmatory eligibility.
The reviewer independently read the contract and ledger-linked raw artifacts, verified their SHA256s, and did not import the new analyzer for the recomputation.

- H3: D=123/150, C=121/150, difference 0.0133333333; person-clustered 95% CI [-0.0733333333, 0.1000000000]. Same C-first/D-second draws, 10,000 replicates, seed20240601, lexicographic persons. Integer success-count comparison confirms centered p=8257/10001=0.8256174383. Naive floating comparisons can lose equal-boundary draws; this was reconciled before finalization.
- H1: rho=0.9889653700, 95% CI [0.97791548, 0.99449032], directional add-one p=1/10001. Zero-cell Wilson upper=0.103335045 at conservative n_eff=33.333; repeated-ICC sensitivity=0.082260682 at n_eff=42.857. Neither resolves1%.
- H5: all-tied-maximizer envelope [4,48]; 1121/10000 replicates tied. Exploratory and underpowered.
- H4: rebuilt first-any-hit CONTROL k_min from raw, 25persons/50targets. Independent lifelines0.30 point gamma=3.484492157, difference from fast solver=6.43e-6. Independently fit bootstrap draws0,10,50,6203,9999; max gamma difference8.61e-7, all parameter differences<1e-4. Independently recalculated the percentile CI [2.811469486,4.209359666] and centered p=.00009999 from saved10000 estimates. This is a point plus five-fit independent validation, not a claim of independently refitting all10000.
- Fixed-four Holm: H1/H4=.000399960004; H3/H2=1, with H2 explicitly untestable and reserved at1.

No material numerical disagreement. H4 rejects proportionality only under the disclosed working distribution and threshold-collapse rule. H2 is unresolved at1%; a negative contrast at an almost100% tolerance is not positive detection. H3 is not equivalence. Source pins, matching and accounting gaps remain; independent arithmetic verification does not fix them.

## Additional independent H2 method-consistency check

The hypothesis-mapping reviewer independently recomputed the post-hoc Wilson sensitivity from the recorded control rates, using z=1.959964 and effective n=100/3 or 300/7. Its k=4 upper bounds, 0.125980782 and 0.105182583, agree with the added ledger output. Under n=100/3 there are no floor-only points at tolerances 1%, 5%, 9%, or 10%; k={1,2,3,4} enter at 15% and 20%. Under n=300/7, k={1,2,3} enter at 9% and 10%, and k=4 joins at 15%. Neither convention produces a positive-tau joint point using the main tau intervals. Applying Wilson/MOVER consistently to tau also leaves every interval containing zero. This is an independent check of the sensitivity calculation, not a new confirmatory analysis or a resolution of the provenance gaps.

## Report clarification review

A separate read-only reviewer checked the four requested clarifications. Corrections distinguish the carried 1% H2, the literal two-sided joint rule, and the desired positive signal; name the CI used in the sensitivity table; keep the live plan's later status/description separate from pre-run predictions; and distinguish task-prediction success from final study acceptance. The beta task is no longer judged by an inverse-unit slope, and zero observed hits are not treated as proof against a zero population rate.

The reviewer separately read and checksummed recovered train_meta and cost parquets. PII eval losses agree with the added task evidence: 2.676068874, 2.204664511, 2.088893150. The cost-pilot means are 25.551559031, 31.002434393, 80.803665360 seconds at k=1,20,64. Notebook cell 17's T=10 formula gives 1.056634531 times its linear prediction at k=64, below its 1.25 overhead flag. These are recorded pilot observations, not a fixed-step complexity test or proof of the per-step candidate count. They support a falling loss, not the original near-zero claim, and do not support the predicted large cost excess. The script audit_task_predictions.py carries their file hashes and the calculation into results.json.
