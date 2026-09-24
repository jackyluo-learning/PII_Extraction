#!/usr/bin/env bash
# One-shot status report for the frozen-target base-model formal run.
# Run manually on Cheaha; this script does not poll or change jobs.
set -euo pipefail

root=/data/user/jluo/PII_Extraction_e3b_base
job_ids=40461513,40461514,40461515

echo '=== Current queue (blank means no listed job remains queued/running) ==='
squeue -j "$job_ids" -o '%.18i %.10T %.10M %.10l %.20R'

echo '=== Final/recorded states (accept only COMPLETED with 0:0 for all three) ==='
sacct -j "$job_ids" -X -n -P --format=JobIDRaw,State,ExitCode,Elapsed,NodeList

echo '=== Formal artifact and log presence ==='
for entry in 42:40461513 1337:40461514 2024:40461515; do
  seed=${entry%%:*}
  job=${entry##*:}
  stem="e3b_base__E2B__gpt2_${seed}_field-ssn-email_k20"
  printf 'seed=%s job=%s ' "$seed" "$job"
  for path in \
    "$root/results/manifests/$stem.json" \
    "$root/results/attempts/$stem.parquet"; do
    if [[ -f "$path" ]]; then
      printf '%s=present ' "${path##*/}"
    else
      printf '%s=missing ' "${path##*/}"
    fi
  done
  printf '\n'
  if [[ -f "$root/slurm/logs/pii-e3b-base-$job.out" ]]; then
    tail -n 2 "$root/slurm/logs/pii-e3b-base-$job.out"
  fi
  if [[ -s "$root/slurm/logs/pii-e3b-base-$job.err" ]]; then
    tail -n 2 "$root/slurm/logs/pii-e3b-base-$job.err"
  fi
done

echo 'When all three jobs finish, send me this output so I can retrieve and validate the results.'
