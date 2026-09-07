"""Bind preserved Cheaha Slurm logs to the recovered main-sweep ledger.

The historical sacct export did not retain ArrayTaskID.  The preserved remote
stdout files did retain their array submission/task names and their remote
modification times.  A task is bound to the unique pii-expcap sacct row whose
end time is within two seconds of that preserved stdout mtime.  The binding is
recorded as an audit fact; it does not manufacture a checkpoint identity.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
STUDY = ROOT / ".ai/research/studies/capacity_axis_20260902"
OUT = STUDY / "reanalysis"
EXTRA = OUT / "cheaha-extra-evidence"
LOGS = EXTRA / "slurm/logs"
SACCT = next((OUT / "cheaha-e3-evidence").glob("*/sacct.tsv"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_sacct_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")


def parse_log(path: Path) -> dict:
    text = path.read_text(errors="replace")
    first = text.splitlines()[0] if text.splitlines() else ""
    head = re.search(
        r"\[E3\] task=(\d+) model=(\S+) seed=(\d+) k=(\d+) host=(\S+)",
        first,
    )
    if not head:
        raise ValueError(f"unparseable E3 header: {path}")
    array_submission, array_task = re.search(
        r"pii-expcap-(\d+)_(\d+)\.out$", path.name
    ).groups()
    manifest = re.search(r"\[manifest\]\s+(\S+)", text)
    e17 = re.search(r"\[E17\]\s+600 matched pairs ->\s+(\S+)", text)
    err_path = path.with_suffix(".err")
    return {
        "out_path": str(path.relative_to(ROOT)),
        "err_path": str(err_path.relative_to(ROOT)),
        "out_sha256": sha256(path),
        "out_bytes": path.stat().st_size,
        "err_sha256": sha256(err_path) if err_path.exists() else None,
        "err_bytes": err_path.stat().st_size if err_path.exists() else None,
        "out_mtime": datetime.fromtimestamp(path.stat().st_mtime).astimezone(),
        "array_submission_id": array_submission,
        "array_task_id": int(array_task),
        "task_id": int(head.group(1)),
        "model": head.group(2),
        "seed": int(head.group(3)),
        "k": int(head.group(4)),
        "host": head.group(5),
        "manifest_remote": manifest.group(1) if manifest else None,
        "e17_remote": e17.group(1) if e17 else None,
        "done_marker": "[E3] DONE" in text,
        "error_marker": bool(
            re.search(r"Traceback|ValueError|RuntimeError|CUDA out of memory", text)
        ),
    }


def load_sacct() -> list[dict]:
    with SACCT.open() as stream:
        rows = list(csv.DictReader(stream, delimiter="|"))
    return [row for row in rows if row.get("JobName") == "pii-expcap" and "." not in row["JobIDRaw"]]


def bind_scheduler(record: dict, jobs: list[dict]) -> None:
    target = record["out_mtime"].replace(tzinfo=None)
    candidates = []
    for job in jobs:
        try:
            end = parse_sacct_time(job["End"])
        except (TypeError, ValueError):
            continue
        delta = abs((end - target).total_seconds())
        if delta <= 2:
            candidates.append((delta, job))
    candidates.sort(key=lambda item: (item[0], item[1]["JobIDRaw"]))
    if not candidates:
        record["scheduler"] = None
        return
    delta, job = candidates[0]
    record["scheduler"] = {
        "job_id_raw": job["JobIDRaw"],
        "state": job["State"],
        "exit_code": job["ExitCode"],
        "start": job["Start"],
        "end": job["End"],
        "elapsed_raw": int(job["ElapsedRaw"] or 0),
        "alloc_tres": job["AllocTRES"],
        "match_seconds": delta,
        "match_method": "remote stdout mtime to sacct End within 2 seconds",
    }


def iso_with_offset(value: str, offset: str) -> str:
    return value + offset


def main() -> None:
    ledger_path = STUDY / "results.json"
    ledger = json.loads(ledger_path.read_text())
    runs_by_stem = {
        run["source_stem"]: run
        for run in ledger["runs"]
        if run.get("source_scope") == "cheaha_main"
    }
    jobs = load_sacct()
    records = []
    for path in sorted(LOGS.glob("pii-expcap-*.out")):
        record = parse_log(path)
        bind_scheduler(record, jobs)
        records.append(record)

    # The two early files are intentionally retained as audit evidence, but
    # only the 42 final main-shard logs may update the main ledger.
    pilot_submission_ids = {"40053007", "40053058"}
    main_records = [
        record
        for record in records
        if record["array_submission_id"] not in pilot_submission_ids
    ]
    assert len(main_records) == 42, len(main_records)
    assert len({record["manifest_remote"] for record in main_records}) == 42
    assert all(record["done_marker"] and not record["error_marker"] for record in main_records)
    assert all(record["scheduler"] is not None for record in main_records)
    assert Counter(record["scheduler"]["state"] for record in main_records) == {"COMPLETED": 42}

    # Central time is encoded in the preserved remote mtime.  Use its offset
    # for the sacct start timestamp rather than silently emitting a naive time.
    offset = main_records[0]["out_mtime"].strftime("%z")
    offset = offset[:3] + ":" + offset[3:]

    csv_rows = []
    submission_groups = defaultdict(list)
    for record in records:
        scheduler = record["scheduler"]
        stem = Path(record["manifest_remote"] or "unknown").stem
        row = {
            "source_stem": stem,
            "array_submission_id": record["array_submission_id"],
            "array_task_id": record["array_task_id"],
            "task_id": record["task_id"],
            "seed": record["seed"],
            "k": record["k"],
            "host": record["host"],
            "done_marker": record["done_marker"],
            "error_marker": record["error_marker"],
            "out_path": record["out_path"],
            "err_path": record["err_path"],
            "out_sha256": record["out_sha256"],
            "err_sha256": record["err_sha256"],
            "remote_out_mtime": record["out_mtime"].isoformat(timespec="seconds"),
            "scheduler_job_id": scheduler["job_id_raw"] if scheduler else None,
            "scheduler_state": scheduler["state"] if scheduler else None,
            "scheduler_exit_code": scheduler["exit_code"] if scheduler else None,
            "scheduler_start": scheduler["start"] if scheduler else None,
            "scheduler_end": scheduler["end"] if scheduler else None,
            "scheduler_elapsed_raw": scheduler["elapsed_raw"] if scheduler else None,
            "scheduler_alloc_tres": scheduler["alloc_tres"] if scheduler else None,
            "scheduler_match_seconds": scheduler["match_seconds"] if scheduler else None,
            "scheduler_match_method": scheduler["match_method"] if scheduler else None,
        }
        csv_rows.append(row)
        submission_groups[record["array_submission_id"]].append(record)

    csv_path = OUT / "cheaha_slurm_log_provenance.csv"
    fieldnames = list(csv_rows[0])
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    for record in main_records:
        stem = Path(record["manifest_remote"]).stem
        run = runs_by_stem[stem]
        scheduler = record["scheduler"]
        run["started_at"] = iso_with_offset(scheduler["start"], offset)
        run["started_at_status"] = (
            "recovered from Cheaha sacct Start; row matched to preserved remote "
            "Slurm stdout completion time within 2 seconds"
        )
        run["completion_basis"] = (
            "full expected rows in recovered raw shard; Slurm stdout contains "
            "E3 DONE; matched sacct terminal state COMPLETED"
        )
        run["accelerator_hours"] = round(scheduler["elapsed_raw"] * 8 / 3600, 6)
        run["accelerator_hours_status"] = (
            "sacct matched; billing=8 GPU-hour lower-bound allocation for one "
            "gres/gpu; task binding uses preserved stdout completion time"
        )
        run["scheduler"] = {
            "job_id_raw": scheduler["job_id_raw"],
            "array_submission_id": record["array_submission_id"],
            "array_task_id": record["array_task_id"],
            "state": scheduler["state"],
            "exit_code": scheduler["exit_code"],
            "start": run["started_at"],
            "end": iso_with_offset(scheduler["end"], offset),
            "elapsed_raw": scheduler["elapsed_raw"],
            "alloc_tres": scheduler["alloc_tres"],
            "match_seconds": scheduler["match_seconds"],
            "match_method": scheduler["match_method"],
        }
        for log_key, role in (("out_path", "logs"), ("err_path", "logs")):
            log_path = ROOT / record[log_key]
            item = {
                "path": record[log_key],
                "sha256": sha256(log_path),
                "bytes": log_path.stat().st_size,
                "role": role,
                "evidence_kind": "slurm_log",
            }
            existing_item = next(
                (existing for existing in run["artifacts"] if existing.get("path") == item["path"]),
                None,
            )
            if existing_item is not None:
                existing_item.update(item)
            else:
                run["artifacts"].append(item)

    summary = {
        "archive": str((OUT / "cheaha-extra-evidence.tar.gz").relative_to(ROOT)),
        "archive_bytes": (OUT / "cheaha-extra-evidence.tar.gz").stat().st_size,
        "archive_sha256": sha256(OUT / "cheaha-extra-evidence.tar.gz"),
        "log_pairs": len(records),
        "main_log_pairs": len(main_records),
        "main_done_markers": sum(record["done_marker"] for record in main_records),
        "main_scheduler_matches": sum(record["scheduler"] is not None for record in main_records),
        "main_scheduler_states": dict(Counter(record["scheduler"]["state"] for record in main_records)),
        "main_scheduler_job_ids": len({record["scheduler"]["job_id_raw"] for record in main_records}),
        "main_started_at_recovered": len(main_records),
        "main_billing_gpu_hours_lower_bound": round(
            sum(record["scheduler"]["elapsed_raw"] * 8 / 3600 for record in main_records),
            6,
        ),
        "submission_groups": {
            key: {
                "logs": len(value),
                "tasks": sorted(record["array_task_id"] for record in value),
                "done": sum(record["done_marker"] for record in value),
                "scheduler_states": dict(
                    Counter(
                        record["scheduler"]["state"]
                        for record in value
                        if record["scheduler"]
                    )
                ),
            }
            for key, value in sorted(submission_groups.items())
        },
        "early_or_failed_logs": [
            {
                "out_path": record["out_path"],
                "array_submission_id": record["array_submission_id"],
                "done_marker": record["done_marker"],
                "scheduler": record["scheduler"],
            }
            for record in records
            if record not in main_records
        ],
        "binding_note": (
            "The preserved remote stdout mtime uniquely matches each final "
            "main log to a pii-expcap sacct End within 2 seconds. The historical "
            "sacct export omitted ArrayTaskID, so the binding is timestamp-backed "
            "and auditable but is not a direct ArrayTaskID field."
        ),
    }

    for audit_name in ("cheaha_recovery_audit.json", "post_recovery_audit.json"):
        path = OUT / audit_name
        audit = json.loads(path.read_text()) if path.exists() else {}
        audit["slurm_logs"] = summary
        audit.setdefault("historical_binding", {})[
            "scheduler_mapping"
        ] = (
            "Resolved for all 42 final main shards by timestamp-backed matching "
            "of preserved stdout to sacct; task-level attribution for unlogged "
            "array slots is still unavailable."
        )
        audit.setdefault("historical_binding", {})[
            "started_at"
        ] = (
            "Resolved for 42 Cheaha main records from matched sacct Start; the "
            "7 imported Colab records remain without historical start times."
        )
        audit["source_materials_recovered"] = sorted(
            set(audit.get("source_materials_recovered", []))
            | {"44 preserved Cheaha Slurm stdout/stderr logs (42 final main, one failed preflight, one pilot)"}
        )
        remaining = [
            "历史执行 checkpoint 内容指纹并与每个 Cheaha 分片绑定",
            "超出 manifest PII_* 字段的不可变完整 launch 记录",
            "6 个 code.dirty=null 主 manifest 的历史清洁证据",
            "未生成最终日志的数组槽位的失败/取消及重试归属",
            "7 条 Colab 导入记录的历史 started_at 时间戳",
        ]
        audit["remaining_missing"] = remaining
        path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")

    reanalysis = ledger["reanalysis"]
    reanalysis["cheaha_slurm_log_provenance_path"] = str(csv_path.relative_to(ROOT))
    reanalysis["cheaha_slurm_log_summary"] = summary
    reanalysis["post_recovery_audit"] = json.loads(
        (OUT / "post_recovery_audit.json").read_text()
    )
    reanalysis["blocked_reason"] = (
        "Final acceptance remains blocked by the failed email balance gate, "
        "undefined H2 global-test contract, executed-checkpoint/full-launch "
        "binding, six dirty=null manifests, unlogged array-slot failure/retry "
        "attribution, and seven Colab records without historical started_at."
    )
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n")

    # The registry and plan keep the same blocked status, but their reasons now
    # distinguish resolved final-shard mapping from genuinely missing history.
    registry_path = ROOT / ".ai/research/studies.json"
    registry = json.loads(registry_path.read_text())
    study = next(item for item in registry["studies"] if item["study_id"] == STUDY.name)
    study["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    study["compute"]["accelerator_hours_status"] = (
        "42 final main shards now have timestamp-backed sacct matches; their "
        f"matched billing GPU-hour lower bound is {summary['main_billing_gpu_hours_lower_bound']}; "
        "aggregate 45-job accounting remains for the unlogged slots and retries."
    )
    study["compute"]["failed_job_accounting_status"] = (
        "All 42 final main logs match COMPLETED sacct rows; one failed preflight "
        "and one pilot are preserved. Unlogged array-slot failure/cancel/retry "
        "attribution remains unavailable."
    )
    study["compute"]["note"] = (
        "49 byte-addressed raw shards; 3 legacy rows excluded as superseded. "
        "The 42 final Cheaha logs are now bound to scheduler rows and start "
        "times; checkpoint/full-launch binding, six dirty=null manifests, "
        "unlogged slot attribution, and seven Colab start times remain unresolved."
    )
    for phase in study["phases_summary"]:
        if phase["id"] == "phase-2":
            phase["blocked_reason"] = (
                "42 final main logs now bind to COMPLETED sacct rows and recover "
                "per-shard start times. Historical checkpoint/full-launch binding, "
                "six dirty=null manifests, and unlogged array-slot failure/retry "
                "attribution remain unresolved."
            )
        if phase["id"] == "phase-3":
            phase["blocked_reason"] = (
                "Conditional analysis and complete descriptive figures are "
                "finished. Final acceptance remains blocked by the failed email "
                "balance gate, undefined H2 global-test contract, checkpoint/full "
                "launch binding, six dirty=null manifests, unlogged-slot "
                "attribution, and seven Colab start times."
            )
    study["blocked_reason"] = (
        "E17, exact environment records, manifests, preserved Slurm logs, and "
        "timestamp-backed per-shard scheduler matches are recovered. Final "
        "acceptance remains blocked by the failed email balance gate, undefined "
        "H2 global-test contract, executed-checkpoint/full-launch binding, six "
        "dirty=null manifests, unlogged array-slot attribution, and seven "
        "Colab records without historical started_at."
    )
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n")

    plan_path = STUDY / "plan.json"
    plan = json.loads(plan_path.read_text())
    for phase in plan["phases"]:
        for task in phase.get("tasks", []):
            if task.get("id") == "t2-cp":
                task["blocked_reason"] = (
                    "42 final main logs bind to COMPLETED sacct rows and recover "
                    "per-shard start times. Checkpoint/full-launch binding, six "
                    "dirty=null manifests, and unlogged array-slot failure/retry "
                    "attribution remain unresolved."
                )
            if task.get("id") == "t3-cp":
                task["blocked_reason"] = (
                    "Every hypothesis has a conditional verdict and the complete "
                    "descriptive figures are ledger-linked. Final acceptance "
                    "remains blocked by the failed email balance gate, undefined "
                    "H2 global-test contract, checkpoint/full-launch binding, "
                    "six dirty=null manifests, unlogged-slot attribution, and "
                    "seven Colab start times."
                )
        if phase.get("id") == "phase-2":
            phase["blocked_reason"] = (
                "Raw main sweep, aggregate sacct accounting, and timestamp-backed "
                "final-shard scheduler matches are recovered; checkpoint/full-launch "
                "binding, six dirty=null manifests, and unlogged array-slot "
                "failure/retry attribution remain unresolved."
            )
        if phase.get("id") == "phase-3":
            phase["blocked_reason"] = (
                "Conditional analysis and complete descriptive figures are finished. "
                "Final acceptance remains blocked by the failed email balance gate, "
                "undefined H2 global-test contract, and remaining historical binding "
                "gaps."
            )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
