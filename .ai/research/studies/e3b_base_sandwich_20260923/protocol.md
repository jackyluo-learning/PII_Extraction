# Execution protocol

Use the pinned runner and SLURM file at commit
`7d95b22e2bb4b8357d6be027141675c8f86c811e`. The accepted E3b frozen
target manifest, original GPT-2 snapshot, GCG settings, exact-match rule, and
three seeds are specified in
[`../capacity_axis_20260902/e3b_base_followup_plan.md`](../capacity_axis_20260902/e3b_base_followup_plan.md).

Pilot: two D/C person pairs, both fields, seed 42, one A100. Jobs 40460942
and 40461115 both completed `0:0` in 00:06:20 and 00:05:24. All eight
formatted targets, outcomes, prompts, generations, step counts, and NLL values
matched exactly; observed drift is zero. The proposed 0.001 relative
tolerance and 5.0 A100-hour ceiling were authorized before formal submission.
The three formal jobs each used all 25 D/C pairs and completed successfully;
their identities and outcomes are recorded in `results.json`.

Formal acceptance requires three complete base manifests and parquets, 300
rows total, exact frozen targets, 100 rows per seed, and matching attack and
scoring settings against the accepted fine-tuned E3b `k=20` shards. Failed
jobs and retries remain in the ledger. No formal result is inferred from pilot
data.

The fail-closed analysis entrypoint is `analyze_e3b_base_followup.py`. It
requires three base and three accepted E3b manifests/parquets, all 600 exact
targets and outcomes, the fixed code and checkpoint pins, and A100 hardware.
It clusters uncertainty by matched person pair across two fields and three
attack seeds; it does not estimate a leave-one-out causal effect.
