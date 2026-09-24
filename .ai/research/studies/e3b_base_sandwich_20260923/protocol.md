# Execution protocol

Use the pinned runner and SLURM file at commit
`7d95b22e2bb4b8357d6be027141675c8f86c811e`. The accepted E3b frozen
target manifest, original GPT-2 snapshot, GCG settings, exact-match rule, and
three seeds are specified in
[`../capacity_axis_20260902/e3b_base_followup_plan.md`](../capacity_axis_20260902/e3b_base_followup_plan.md).

Pilot: two D/C person pairs, both fields, seed 42, one A100, job 40460942.
Accept only with scheduler `COMPLETED`/`0:0`, eight attempt rows, clean commit,
frozen hashes, and A100 manifest. Repeat that coordinate with a new pilot run
ID for the reproducibility check. The three formal jobs each use all 25 D/C
pairs; submit only after measured pilot cost and reproducibility gates. If the
measured projected cost exceeds four accelerator-hours, obtain explicit budget
approval before formal submission.

Formal acceptance requires three complete base manifests and parquets, 300
rows total, exact frozen targets, 100 rows per seed, and matching attack and
scoring settings against the accepted fine-tuned E3b `k=20` shards. Failed
jobs and retries remain in the ledger. No formal result is inferred from pilot
data.
