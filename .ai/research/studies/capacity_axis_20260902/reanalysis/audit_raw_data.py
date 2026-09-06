"""Audit E3 raw evidence without fitting models or testing hypotheses.

Run from the repository root. Outputs contain file hashes and aggregate integrity
checks, not target strings or person names. The launch-version matching function
is extracted by AST to avoid importing model-loading modules.
"""
from __future__ import annotations

import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Optional
import unicodedata

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
GRID = [0, 1, 2, 3, 4, 6, 8, 12, 16, 20, 24, 32, 48, 64]
SEEDS = [42, 1337, 2024]
ARMS = ["control", "trained"]
FIELDS = ["email", "ssn"]
KEY = ["seed", "capacity_k", "target_membership", "person_id", "field"]
TARGET = ["target_membership", "person_id", "field"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit():
    raw_paths = sorted((ROOT / "results/attempts").glob("e3a__*.parquet"))
    manifest_paths = sorted((ROOT / "results/manifests").glob("e3a__*.json"))
    led = json.loads((ROOT / ".ai/research/studies/capacity_axis_20260902/results.json").read_text())
    frames, shard_rows, problems = [], [], []
    expected_cells = {(s, k) for s in SEEDS for k in GRID}
    observed_cells = []
    for path in raw_paths:
        df = pd.read_parquet(path)
        mp = ROOT / "results/manifests" / (path.stem + ".json")
        if not mp.exists():
            problems.append({"file": str(path.relative_to(ROOT)), "error": "missing_manifest"})
            continue
        m = json.loads(mp.read_text())
        s, k = m["shard"]["seed"], m["shard"]["capacity_k"]
        observed_cells.append((s, k))
        pairs = sorted(tuple(str(x) for x in row) for row in df[TARGET].itertuples(index=False, name=None))
        subset_hash = hashlib.sha256(json.dumps(pairs, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()[:16]
        counts = df.groupby(["target_membership", "field"], observed=True).size()
        checks = {
            "rows_100": len(df) == 100,
            "no_duplicate_keys": not bool(df.duplicated(KEY).any()),
            "filename_matches_manifest": path.stem == f"e3a__E3__gpt2_{s}_field-ssn-email_k{k}",
            "seed_matches": set(df.seed) == {s},
            "capacity_matches": set(df.capacity_k) == {k},
            "run_exp_model_state_match": all(set(df[col]) == {val} for col, val in [("run_id", "e3a"), ("exp_id", "E3"), ("model_name", "gpt2"), ("model_state", "finetuned")]),
            "probe_matches": set(df.probe) == {"fixed" if k == 0 else "gcg_free"},
            "four_arm_field_cells_25": set(counts.index) == {(a, f) for a in ARMS for f in FIELDS} and bool((counts == 25).all()),
            "subset_hash_matches_raw": subset_hash == m["target_subset_hash"],
            "configured_steps_200": m["gcg_iters"] == 200 and m["config"].get("PII_GCG_ITERS") == "200",
            "positive_wallclock": bool((df.wallclock_s > 0).all()),
            "steps_within_budget": bool(((df.steps_run >= 1) & (df.steps_run <= (1 if k == 0 else 200))).all()),
            "prompt_length_equals_k": True if k == 0 else all(len(ids) == k for ids in df.prompt_token_ids),
        }
        for key, ok in checks.items():
            if not ok:
                problems.append({"file": str(path.relative_to(ROOT)), "error": key})
        shard_rows.append({
            "artifact": str(path.relative_to(ROOT)), "sha256": sha(path),
            "manifest": str(mp.relative_to(ROOT)), "manifest_sha256": sha(mp),
            "seed": s, "capacity_k": k, "rows": len(df),
            "raw_subset_hash": subset_hash, "code_commit": m["code"]["commit"],
            "code_dirty": m["code"]["dirty"], "env_lock_hash": m["env"]["pip_freeze_sha256_16"],
            "attempt_wallclock_s": float(df.wallclock_s.sum()),
            "attempt_wallclock_s_by_arm": {str(a): float(g.wallclock_s.sum()) for a, g in df.groupby("target_membership", observed=True)},
            "checks": checks,
        })
        frames.append(df)
    raw = pd.concat(frames, ignore_index=True)
    gcg = raw[raw.capacity_k >= 1]
    anchor = raw[raw.capacity_k == 0]
    required = [c for c in raw.columns if c not in ["softprompt_norm", "lambda_fluency", "steps_to_first_success"]]
    nulls = {c: int(raw[c].isna().sum()) for c in required}
    nonfinite = {c: int((~np.isfinite(raw[c].astype(float))).sum()) for c in ["target_H_bits", "final_target_nll", "wallclock_s"]}
    consistency = {}
    for c in ["target_string", "target_H_bits", "target_len_tokens", "train_frequency"]:
        consistency[c] = int((gcg.groupby(TARGET, observed=True)[c].nunique(dropna=False) != 1).sum())
    arm_ids = {a: set(raw.loc[raw.target_membership == a, "person_id"]) for a in ARMS}
    base_values = anchor.drop_duplicates(TARGET).set_index(TARGET).target_string.to_dict()
    anchor_consistency = int((anchor.groupby(TARGET, observed=True).target_string.nunique() != 1).sum())
    raw_value_overlap = {}
    for f in FIELDS:
        vals = {a: {str(v) for (aa, _, ff), v in base_values.items() if aa == a and ff == f} for a in ARMS}
        raw_value_overlap[f] = len(vals["trained"] & vals["control"])
    launch_commits = sorted({r["code_commit"] for r in shard_rows})
    if len(launch_commits) != 1:
        raise RuntimeError("Matching-rule audit requires adjudicating differing launch commits first")
    source = subprocess.check_output(["git", "show", f"{launch_commits[0]}:evaluate.py"], cwd=ROOT, text=True)
    tree = ast.parse(source)
    keep_names = {"normalize_text", "_digits_only", "exact_match"}
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in keep_names]
    ns = {"re": re, "unicodedata": unicodedata, "Optional": Optional}
    exec(compile(ast.Module(body=funcs, type_ignores=[]), "launch_evaluate_functions", "exec"), ns)
    ns["_FIELD_NORMALIZERS"] = {f: ns["_digits_only"] for f in ["ssn", "phone", "credit_card"]}
    mismatch = 0
    for row in raw.itertuples(index=False):
        val = base_values[(row.target_membership, row.person_id, row.field)]
        mismatch += int(ns["exact_match"](row.generation, val, row.field) != row.exact_match)
    # The raw CSV is an export, not independent evidence. Compare scalar columns
    # after sorting by keys; stringified token arrays are explicitly excluded.
    csv_path = ROOT / "results/e3_raw_attempts.csv.gz"
    csv = pd.read_csv(csv_path, keep_default_na=False)
    l = raw.sort_values(KEY).reset_index(drop=True)
    r = csv.sort_values(KEY).reset_index(drop=True)
    csv_checks = {}
    for c in raw.columns:
        if c == "prompt_token_ids":
            continue
        if pd.api.types.is_numeric_dtype(l[c].dtype) and not pd.api.types.is_bool_dtype(l[c].dtype):
            x = pd.to_numeric(l[c], errors="coerce").to_numpy(dtype=float, na_value=np.nan)
            y = pd.to_numeric(r[c], errors="coerce").to_numpy(dtype=float, na_value=np.nan)
            csv_checks[c] = bool(np.allclose(x, y, rtol=1e-12, atol=1e-12, equal_nan=True))
        else:
            csv_checks[c] = l[c].fillna("").astype(str).tolist() == r[c].fillna("").astype(str).tolist()
    membership_frequency_errors = int(((raw.target_membership == "control") != (raw.train_frequency == 0)).sum())
    target_counts = raw.groupby(TARGET, observed=True).size()
    first_success_inconsistent = int((raw.exact_match != raw.steps_to_first_success.notna()).sum())
    report = {
        "audit_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Raw evidence integrity only; no hypothesis tests, confidence intervals, or model fits",
        "study_id": "capacity_axis_20260902",
        "expected": {"seeds": SEEDS, "capacities": GRID, "shards": 42, "arm_seed_capacity_cells": 84, "arm_field_seed_capacity_cells": 168, "attempts": 4200},
        "observed": {"parquet_files": len(raw_paths), "manifest_files": len(manifest_paths), "attempts": len(raw), "persons_by_arm": {a: len(v) for a,v in arm_ids.items()}, "targets": len(target_counts)},
        "missing_shards": sorted(expected_cells - set(observed_cells)),
        "unexpected_shards": sorted(set(observed_cells) - expected_cells),
        "duplicate_shard_cells": [list(k) for k,v in Counter(observed_cells).items() if v > 1],
        "duplicate_attempt_keys": int(raw.duplicated(KEY).sum()),
        "targets_without_all_42_measurements": int((target_counts != 42).sum()),
        "required_column_nulls": nulls, "nonfinite_numeric": nonfinite,
        "gcg_target_covariate_inconsistencies": consistency,
        "anchor_value_inconsistencies": anchor_consistency,
        "person_id_overlap_between_arms": len(arm_ids["trained"] & arm_ids["control"]),
        "raw_target_value_overlap_between_arms": raw_value_overlap,
        "membership_frequency_errors": membership_frequency_errors,
        "exact_match_recheck": {"mismatches": mismatch, "rows": len(raw), "implementation_commit": launch_commits[0], "target_source": "k=0 raw value; verifies internal consistency, not independent registry ground truth"},
        "success_step_presence_errors": first_success_inconsistent,
        "anchor_control_success_count": int(anchor.loc[anchor.target_membership == "control", "exact_match"].sum()),
        "anchor_control_attempts": int((anchor.target_membership == "control").sum()),
        "csv_export_checks": csv_checks,
        "csv_export_sha256": sha(csv_path),
        "ledger_run_status_counts": dict(Counter(r.get("run_status", "missing") for r in led["runs"])),
        "ledger_exclusions": [{"run_id": r["run_id"], "reason": r.get("exclusion_reason")} for r in led["runs"] if r.get("excluded")],
        "ledger_repro_check_passed": led.get("repro_check", {}).get("passed"),
        "ledger_only_note": "Pilot rows and reproducibility summary are historical assertions; original pilot/repro artifacts are not present locally. Local shard paths with the same names refer to Cheaha main runs, not Colab pilot runs.",
        "timing_note": "Summed wallclock_s is attack-call elapsed time, not scheduler GPU allocation time; excludes training, loading, failed launches, and other overhead.",
        "shards": shard_rows, "problems": problems,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "raw_data_audit.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    summary = {k:v for k,v in report.items() if k not in ["shards", "required_column_nulls", "csv_export_checks"]}
    summary["required_nulls_total"] = sum(nulls.values())
    summary["csv_export_mismatching_columns"] = [k for k,v in csv_checks.items() if not v]
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    audit()
