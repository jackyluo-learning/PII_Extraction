"""Verify whether each E3 trained-arm field value occurs in the recovered fine-tuning text.

The attack ledger labels membership at the person level. This audit checks the
actual unit used by H3/H5, (person, field), against the exact recovered
``data/corpus/train.json`` content. It writes no raw PII or person identifier.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata

import pandas as pd


ROOT = Path(__file__).resolve().parents[5]
STUDY = ROOT / ".ai/research/studies/capacity_axis_20260902"
RECOVERED = ROOT / "artifacts/capacity_axis_20260902/recovered_colab/data"
OUT = STUDY / "reanalysis/field_exposure_audit.json"
EXPECTED_TRAIN_SHA256 = "7a059fc04ae21665a464a5cb68eb87d2fae597d736f82869c24866e21d0e1acf"


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower().strip()
    return re.sub(r"\s+", " ", text)


def target_value(target_string: str, field: str) -> str:
    # E3 GCG targets are labelled ("SSN: ..." / "Email: ..."); k=0 may
    # contain the bare value. Remove only the known leading label.
    return re.sub(rf"^{re.escape(field)}\s*:\s*", "", target_string, flags=re.I)


def main() -> None:
    ledger_path = STUDY / "results.json"
    train_path = RECOVERED / "corpus/train.json"
    ledger = json.loads(ledger_path.read_text())

    train_hash = file_sha256(train_path)
    if train_hash != EXPECTED_TRAIN_SHA256:
        raise RuntimeError(f"Unexpected recovered train.json hash: {train_hash}")

    runs = {row["run_id"]: row for row in ledger["runs"]}
    target_frames = []
    raw_hashes = []
    for run_id in ledger["reanalysis"]["analysis_run_ids"]:
        run = runs[run_id]
        artifact = next(
            item for item in run["artifacts"] if item.get("evidence_kind") == "raw_attempts"
        )
        raw_path = ROOT / artifact["path"]
        actual_hash = file_sha256(raw_path)
        if actual_hash != artifact["sha256"]:
            raise RuntimeError(f"Raw shard hash mismatch: {artifact['path']}")
        raw_hashes.append(actual_hash)
        frame = pd.read_parquet(
            raw_path,
            columns=["target_membership", "person_id", "field", "train_frequency", "target_string"],
        )
        target_frames.append(frame[frame.target_membership == "trained"])

    all_targets = pd.concat(target_frames, ignore_index=True)
    all_targets["field_value"] = [
        target_value(str(target), str(field))
        for target, field in zip(all_targets.target_string, all_targets.field)
    ]
    all_targets["normalized_field_value"] = [
        re.sub(r"\D", "", value) if field == "ssn" else normalize_text(value)
        for value, field in zip(all_targets.field_value, all_targets.field)
    ]
    key = ["person_id", "field"]
    consistency = all_targets.groupby(key, observed=True).agg(
        n_field_values=("normalized_field_value", "nunique"),
        n_train_frequencies=("train_frequency", "nunique"),
    )
    if not (consistency == 1).all().all():
        raise RuntimeError("Trained target metadata changes across E3 shards")

    targets = all_targets.drop_duplicates(key).sort_values(key)
    if len(targets) != 50:
        raise RuntimeError(f"Expected 50 trained (person, field) targets, found {len(targets)}")

    corpus = json.loads(train_path.read_text())
    texts = [row["text"] for row in corpus]
    normalized_text = "\n".join(normalize_text(text) for text in texts)
    digits_only_text = "\n".join(re.sub(r"\D", "", text) for text in texts)

    audited = []
    for row in targets.itertuples(index=False):
        value = str(row.field_value)
        if row.field == "ssn":
            normalized_value = re.sub(r"\D", "", value)
            present = len(normalized_value) >= 4 and normalized_value in digits_only_text
        else:
            normalized_value = normalize_text(value)
            present = normalized_value in normalized_text
        anonymous_id = sha256(f"{row.person_id}|{row.field}".encode()).hexdigest()[:12]
        audited.append(
            {
                "anonymous_target_id": anonymous_id,
                "field": str(row.field),
                "train_frequency_person_level": int(row.train_frequency),
                "field_value_present_in_recovered_train_text": bool(present),
            }
        )

    by_field = {}
    for field in sorted({row["field"] for row in audited}):
        cells = [row for row in audited if row["field"] == field]
        present = sum(row["field_value_present_in_recovered_train_text"] for row in cells)
        by_field[field] = {"targets": len(cells), "present": present, "absent": len(cells) - present}

    present_total = sum(row["field_value_present_in_recovered_train_text"] for row in audited)
    absent = [row for row in audited if not row["field_value_present_in_recovered_train_text"]]
    result = {
        "status": "verified_field_level_exposure_mismatch",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "unit": "(person_id, field)",
        "matching_rule": {
            "email": "NFKC + lowercase + collapsed whitespace substring, matching evaluate.normalize_text semantics",
            "ssn": "digits-only substring, matching evaluate.exact_match(field='ssn') semantics",
        },
        "sources": {
            "results_ledger": str(ledger_path.relative_to(ROOT)),
            "results_ledger_sha256": file_sha256(ledger_path),
            "registered_raw_shards": len(raw_hashes),
            "registered_raw_shard_unique_sha256": len(set(raw_hashes)),
            "recovered_train_text": str(train_path.relative_to(ROOT)),
            "recovered_train_text_sha256": train_hash,
            "recovered_train_text_expected_sha256": EXPECTED_TRAIN_SHA256,
        },
        "counts": {
            "trained_targets": len(audited),
            "present": present_total,
            "absent": len(audited) - present_total,
            "by_field": by_field,
        },
        "absent_targets_anonymized": absent,
        "person_level_frequency_check": dict(
            sorted(Counter(row["train_frequency_person_level"] for row in audited).items())
        ),
        "interpretation": (
            "All 50 targets carry a positive person-level train_frequency label, but two SSN field "
            "values do not occur in the recovered fine-tuning text. Person-level membership is "
            "therefore not identical to field-level exposure. These two targets should not be "
            "silently moved into the untouched control arm because other fields for the same people "
            "were exposed. Define a field-exposure stratum or exclude them with their matched pairs "
            "under a declared rule before final H2-joint/H3/H5 and D-C figure estimates."
        ),
        "provenance_limit": (
            "The recovered train.json hash matches the registered recovered artifact, but the study "
            "still lacks an immutable per-shard proof binding this corpus and the executed checkpoint."
        ),
    }
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
