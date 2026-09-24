# Prospective E3b base-model follow-up (formal jobs submitted)

## Question and scope

Complete the model-state axis of the E3b comparison at the prespecified
`k=20` setting on GPT-2 124M. This is a focused, within-model follow-up, not
the four-model E2 study and not a leave-one-out retraining experiment. Keep the
E3b fine-tuned checkpoint, frozen D/C target assignments, 25 people per arm,
SSN and email fields, and seeds 42/1337/2024. The existing E3b fine-tuned
shards at `k=20` supply the upper row; the new work attacks the *same* 100
person-field targets against the original GPT-2 base checkpoint for each seed.

| Model state | Trained targets D | Matched controls C |
| --- | --- | --- |
| E3b fine-tuned | Existing formal `k=20` shards | Existing formal `k=20` shards |
| Original GPT-2 base | New, 50 attempts per seed | New, 50 attempts per seed |

Thus the minimum formal new evidence is three complete base shards, 100 rows
each, or 300 new attempt rows. Reusing the E3b fine-tuned rows is justified
only if target IDs, target strings, tokenizer, optimizer settings, decoding,
success rule, and source fingerprints pass exact checks. `run_E2_control_model`
cannot be used as-is because its generic E17 selection does not guarantee the
frozen E3b target pairs.

## Predicted outcomes and interpretation fixed before execution

The primary diagnostic is whether the base-model control rate differs from
the fine-tuned-model control rate at `k=20`. We predict a nonnegative
`Delta_A3 = EMR_ft(C) - EMR_base(C)` but allow a null or negative result.
The full four-cell outputs also give
`tau_rec = EMR_ft(D) - EMR_ft(C)`,
`tau_mod = EMR_ft(D) - EMR_base(D)`, and
`tau_base = EMR_base(D) - EMR_base(C)`.
The exact identity is `tau_mod - tau_rec = Delta_A3 - tau_base`.
A negative `Delta_A3` or a reversed population ordering beyond uncertainty
would challenge the proposed sandwich assumptions. A favorable ordering alone
would not identify the leave-one-out causal effect, because the base checkpoint
is not a model fine-tuned on the corpus with one record removed.

This is a prospective focused analysis. Report person-clustered uncertainty
with all three attack seeds retained as repeats on the same checkpoint and
target people; do not treat seeds as independent training replicates. Do not
report a causal sandwich interval or privacy parameter epsilon solely from
these four observed cells.

## Pinned execution and acceptance gates

- Use the accepted frozen target manifest
  `results/target_sets/e3b.json` (SHA-256
  `ee6be0755717502b750264f51681431134c5f55360f1f4777d6d64a3ee4f1628`),
  with its original registry, corpus, and E3b fine-tuned checkpoint fingerprints.
- Freeze the base model to a specific Hugging Face snapshot revision and record
  its resolved file hashes. Verify the tokenizer vocabulary and encoding of
  every target match those used for the E3b fine-tuned model.
- Keep `gcg_free`, `k=20`, 200 optimization steps, 256 candidates per
  position, 512 candidate evaluations per step, 64-candidate minibatches,
  greedy decoding, 10-step extraction checks, early stop on exact match,
  and the same field-normalized substring exact-match rule.
- Record a clean code commit, resolved config hash, environment hash, A100
  model, scheduler job and exit status, target hashes, and base-weight hashes
  in each new manifest. Do not overwrite any E3a/E3b shard.
- Run a small pilot and a repeated-coordinate reproducibility check before
  the three formal shards. A pilot is not a formal outcome. Require 3/3
  `COMPLETED` and `ExitCode 0:0`, exactly 300 formal rows, exact target IDs
  and strings in both model states, and no missing/duplicate coordinate.
- Analyze the four cells only after all gates pass. Retain all failures and
  retries in the run ledger.

## Compute estimate and gate

The *matched E3b* `k=20` jobs, each with 100 attempts, finished on one A100
in 00:34:47, 00:31:48, and 00:34:52 (Slurm `sacct` job IDs 40388851,
40394475, 40397191): **1.691 A100 GPU-hours total**. These are measured
GPU allocations for the accepted corrected run, not merely summed attack-call
durations. They supersede the much slower E3a reference jobs for planning.
Base-model attacks may stop less often, so provisionally allow roughly
2-4 A100 GPU-hours for the three formal base shards, plus a small pilot,
reproducibility check, and 20-40% retry margin. The pilot must replace this
estimate before the formal array is submitted. The current lab `confirm_above`
gate is 4 GPU-hours; a pilot-measured full-array budget above it needs
explicit approval.

The older four-model E2 design is a different and much larger study. Its
pre-pilot Option B estimate is about 430 A100 GPU-hours worst case, with
large uncertainty, because the old top-row attack budgets differ by model and
must be rerun for a like-for-like comparison. It is not being silently
substituted for this focused E3b follow-up.

## Current execution state

The manuscript clarification is complete. The user restored authenticated SSH
after an interrupted checkout. The isolated base-follow-up checkout at
`/data/user/jluo/PII_Extraction_e3b_base` was repaired and verified clean at
commit `7d95b22e2bb4b8357d6be027141675c8f86c811e`; data, models, the
Python environment, and Hugging Face cache are linked from the existing
workspace. The no-GPU preflight passed with frozen target manifest SHA-256
`ee6be0755717502b750264f51681431134c5f55360f1f4777d6d64a3ee4f1628`,
base snapshot fingerprint
`90265451371a973b9e890f08e56100447117fe838d1b037f0ba8d0c3f48c017b`,
and the registered optimizer parameters. The two-pair pilot, seed 42,
`run_id=e3b_base_pilot_a`, ran as Slurm job **40460942** on A100 node c0238 and
finished `COMPLETED`, `ExitCode 0:0`, in **00:06:20** (0.1056 GPU-hours). Its
clean code pin, base-weight fingerprint, frozen target hash, all eight attempt
rows, exact target-string hashes, and artifact checksums passed local
verification. The four attempts per arm are pilot evidence only, not a formal
estimate. The identical-coordinate repeat, `run_id=e3b_base_pilot_b`,
finished as job **40461115**, `COMPLETED/0:0` on the same A100 class in
**00:05:24** (0.0900 GPU-hours). All eight target strings, exact-match
outcomes, generations, prompts, step counts, and recorded NLL values match
the first pilot exactly; observed relative drift is zero. The mean pilot time projects
**3.67 A100-hours** for three 100-row formal shards, or **3.86 hours**
including both completed pilots. The slower pilot alone projects **4.15
total hours**; a 20% margin on the formal projection plus pilots is about
**4.60 hours**. The user instructed the experiment to start after receiving
the proposed 0.001 reproducibility tolerance and **5.0 A100-hour ceiling**;
both gates were recorded as approved. Three formal jobs were then submitted
from the clean pinned checkout: seed 42 = **40461513**, seed 1337 =
**40461514**, seed 2024 = **40461515**. Each has a 01:35:00 walltime cap,
limiting their combined maximum to 4.75 A100-hours, or 4.95 hours including
both completed pilots. Submission does not imply completion or acceptance.
The user requested no monitoring; the one-shot status script is
`/data/user/jluo/check_e3b_base_followup.sh` on Cheaha. The clean accepted
E3b checkout is
`/data/user/jluo/PII_Extraction_e3b_fast` at commit
`c7e4416dd151c810a5badd4aaae74ccc06176885`. Its target manifest matches
the frozen SHA-256 above, the original corpus and fine-tuned checkpoint are
present through symlinks, and the original GPT-2 base snapshot is cached at
revision `607a30d783dfa663caf39e06633721c8d4cfcd7e` in the shared HF cache.
No formal result has been produced by this follow-up.
