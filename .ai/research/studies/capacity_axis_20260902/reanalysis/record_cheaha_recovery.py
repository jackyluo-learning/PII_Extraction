"""Record the provenance recovered from the authenticated Cheaha project.

This script records only hashes, counts, scheduler summaries, and configuration
metadata. It deliberately does not copy raw PII into the audit ledger.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
STUDY = ROOT / ".ai/research/studies/capacity_axis_20260902"
OUT = STUDY / "reanalysis"
ARCHIVE = OUT / "cheaha-e3-evidence.tar.gz"
EVIDENCE = next(OUT.glob("cheaha-e3-evidence/*"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load(path: Path):
    return json.loads(path.read_text())


manifests = [load(p) for p in sorted((EVIDENCE / "results/manifests").glob("*.json"))]
assert len(manifests) == 42, len(manifests)
local_manifests = ROOT / "results/manifests"
same_as_local = sum(
    (local_manifests / p.name).read_bytes() == p.read_bytes()
    for p in sorted((EVIDENCE / "results/manifests").glob("*.json"))
)

e17 = {}
for path in sorted((EVIDENCE / "results").glob("e17_matches_e3a_seed*.json")):
    rows = load(path)
    seed = int(path.stem.rsplit("seed", 1)[1])
    fields = sorted({row["trained"]["field"] for row in rows})
    trained_ids = {row["trained"]["person_id"] for row in rows}
    control_ids = {row["control"]["person_id"] for row in rows}
    control_repeated = any(
        sum(1 for row in rows if row["control"]["field"] == field and row["control"]["person_id"] == pid) > 1
        for field in fields
        for pid in control_ids
    )
    e17[str(seed)] = {
        "path": str(path.relative_to(ROOT)),
        "rows": len(rows),
        "sha256": sha256(path),
        "fields": fields,
        "trained_unique_people": len(trained_ids),
        "control_unique_people": len(control_ids),
        "control_matching_with_replacement_observed": control_repeated,
    }

dirty = Counter(str(m["code"].get("dirty")) for m in manifests)
commits = Counter(m["code"].get("commit") for m in manifests)
python_versions = Counter(m["env"].get("python") for m in manifests)
torch_versions = Counter(m["env"].get("torch") for m in manifests)
transformers_versions = Counter(m["env"].get("transformers") for m in manifests)
lifelines_versions = Counter(m["env"].get("lifelines") for m in manifests)
subset_hashes = Counter(m["target_subset_hash"] for m in manifests)
pip_freeze = EVIDENCE / "pip_freeze_now.txt"

with (EVIDENCE / "sacct.tsv").open() as f:
    lines = f.read().splitlines()
header = lines[0].split("|")
jobs = [dict(zip(header, line.split("|"))) for line in lines[1:] if line.strip()]
top = [j for j in jobs if "." not in j["JobIDRaw"] and "_" not in j["JobIDRaw"]]
exp = [j for j in top if j.get("JobName") == "pii-expcap"]
exp_states = Counter(j.get("State") for j in exp)
exp_elapsed_all = sum(int(j.get("ElapsedRaw") or 0) for j in exp)
exp_completed = [j for j in exp if j.get("State") == "COMPLETED"]
exp_elapsed_completed = sum(int(j.get("ElapsedRaw") or 0) for j in exp_completed)

audit = {
    "retrieved_at": datetime.now(timezone.utc).isoformat(),
    "source": {
        "host": "cheaha.rc.uab.edu",
        "user": "jluo",
        "project_root": "/data/user/jluo/PII_Extraction",
        "archive": {
            "path": str(ARCHIVE.relative_to(ROOT)),
            "bytes": ARCHIVE.stat().st_size,
            "sha256": sha256(ARCHIVE),
        },
    },
    "e17_matching": {
        "files": e17,
        "all_three_files_byte_identical": len({x["sha256"] for x in e17.values()}) == 1,
        "interpretation": "Recovered from Cheaha. The three seed-named files are byte-identical, so they document matching inputs but are not independent seed evidence.",
    },
    "manifests": {
        "files": len(manifests),
        "same_as_local": same_as_local,
        "code_dirty_counts": dict(dirty),
        "commit_counts": dict(commits),
        "python_versions": dict(python_versions),
        "torch_versions": dict(torch_versions),
        "transformers_versions": dict(transformers_versions),
        "lifelines_versions": dict(lifelines_versions),
        "subset_hash_counts": dict(subset_hashes),
        "pip_freeze_lines": len(pip_freeze.read_text().splitlines()),
        "pip_freeze_sha256": sha256(pip_freeze),
        "pip_freeze_sha256_16": sha256(pip_freeze)[:16],
        "config": {
            "PII_ADAPTIVE_LAMBDA": manifests[0]["config"]["PII_ADAPTIVE_LAMBDA"],
            "PII_CAP_SWEEP_N": manifests[0]["config"]["PII_CAP_SWEEP_N"],
            "PII_DEVICE_PROFILE": manifests[0]["config"]["PII_DEVICE_PROFILE"],
            "PII_FIELDS": manifests[0]["config"]["PII_FIELDS"],
            "PII_GCG_ITERS": manifests[0]["config"]["PII_GCG_ITERS"],
            "PII_KGRID": manifests[0]["config"]["PII_KGRID"],
            "PII_MODELS": manifests[0]["config"]["PII_MODELS"],
            "PII_RUN_ID": manifests[0]["config"]["PII_RUN_ID"],
            "PII_SEEDS": manifests[0]["config"]["PII_SEEDS"],
        },
        "interpretation": "Manifests resolve the recorded PII_* launch fields and exact environment hash. Six manifests retain dirty=null; this is unknown historical cleanliness, not clean evidence.",
    },
    "current_content_hashes": load(EVIDENCE / "current_content_hashes.json"),
    "scheduler": {
        "source": str((EVIDENCE / "sacct.tsv").relative_to(ROOT)),
        "top_level_rows": len(top),
        "pii_expcap_jobs": len(exp),
        "pii_expcap_states": dict(exp_states),
        "pii_expcap_elapsed_seconds_all": exp_elapsed_all,
        "pii_expcap_elapsed_seconds_completed": exp_elapsed_completed,
        "pii_expcap_alloc_tres": sorted({j.get("AllocTRES") for j in exp if j.get("AllocTRES")}),
        "completed_billing_gpu_hours_lower_bound": round(exp_elapsed_completed * 8 / 3600, 3),
        "mapping_to_shards": "Aggregate scheduler accounting recovered; the export does not bind every completed job one-to-one to a manifest/shard or identify the failed retry attribution.",
    },
    "historical_binding": {
        "checkpoint": "unresolved: current_content_hashes.json is a current snapshot and does not bind the executed checkpoint to each shard",
        "git_cleanliness": "unresolved for six dirty=null manifests; current git status is dirty because the collection directory was added during recovery",
        "launch_configuration": "PII_* fields and the generic Slurm scripts recovered; a fully immutable resolved launch record was not recovered",
        "environment_lock": "resolved: exact pip freeze recovered and its 16-character hash matches every manifest",
    },
}

(OUT / "cheaha_recovery_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")

post_path = OUT / "post_recovery_audit.json"
post = load(post_path)
post["created_at"] = audit["retrieved_at"]
post["cheaha_recovery"] = audit
post["remaining_missing"] = [
    "历史执行 checkpoint 内容指纹并与每个 Cheaha 分片绑定",
    "超出 manifest PII_* 字段的不可变完整 launch 记录",
    "6 个 code.dirty=null 主 manifest 的历史清洁证据",
    "分片与 Slurm 作业的一对一映射及失败/重试归属",
    "49 条导入运行记录的历史 started_at 时间戳",
]
post["source_materials_recovered"] = [
    "Cheaha E17 matching records for seeds 42, 1337, and 2024",
    "42 Cheaha manifests and their resolved PII_* fields",
    "Exact pip freeze with manifest-matching hash",
    "Slurm sacct export with pii-expcap terminal states and elapsed allocations",
]
post_path.write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n")

results_path = STUDY / "results.json"
results = load(results_path)
results["reanalysis"]["status"] = "computed_conditionally_reviewed_numerically_source_recovered_historical_binding_blocked"
results["reanalysis"]["post_recovery_audit"] = post
results["reanalysis"]["cheaha_recovery_audit_path"] = str((OUT / "cheaha_recovery_audit.json").relative_to(ROOT))
results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"e17_files": len(e17), "manifest_files": len(manifests), "pii_expcap_jobs": len(exp), "remaining_missing": len(post["remaining_missing"])}, ensure_ascii=False))
