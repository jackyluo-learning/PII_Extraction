"""
Per-shard run manifest: the pins that the attempt log cannot carry.

The parquet schema records run_id / exp_id / seed / model_name / model_state and
nothing else, so four of the five reproducibility pins (code, config,
environment, data) are recorded by nothing at all in this pipeline. The
`results.json` that other tooling refers to belongs to the legacy pipeline.

Two fields here are not bookkeeping but load-bearing invariants for the E3
capacity sweep:

  * `gcg_iters` -- the CONFIGURED step ceiling. It is not recoverable from the
    log, because `steps_run` records steps actually taken after early stop. On a
    target that succeeded early, N is simply gone. If it differed across k, the
    whole capacity contrast would be uninterpretable.

  * `target_subset_hash` -- a hash of the sorted (person_id, field) pairs in
    BOTH arms. Recording a count ("25") does not prove that the k=1 shard and
    the k=64 shard attacked the SAME 25 people. E17's matching has no RNG, but
    its distance features come from a forward pass through a reference model,
    and the accelerator varies between sessions; floating-point drift could flip
    a near-tied nearest neighbour with no randomness involved. That is exactly
    the divergence "the code is deterministic" will not catch and a hash will.

Compare the manifests across shards before trusting any table.
"""

import hashlib
import json
import os
import subprocess
import sys
from typing import Dict, List, Optional, Sequence, Tuple


def _git(*args: str) -> Optional[str]:
    try:
        return subprocess.run(("git",) + args, capture_output=True, text=True,
                              timeout=10, check=True).stdout.strip()
    except Exception:
        return None


def git_state() -> Dict:
    """Commit SHA plus a dirty flag. A dirty tree cannot back a confirmatory claim."""
    sha = _git("rev-parse", "HEAD")
    porcelain = _git("status", "--porcelain")
    return {
        "commit": sha,
        "dirty": bool(porcelain) if porcelain is not None else None,
        "dirty_files": porcelain.splitlines()[:20] if porcelain else [],
    }


def env_lock() -> Dict:
    """A hash of the resolved environment, plus the versions that can change a number."""
    try:
        freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                                capture_output=True, text=True, timeout=120,
                                check=True).stdout
        freeze_hash = hashlib.sha256(freeze.encode()).hexdigest()[:16]
    except Exception:
        freeze, freeze_hash = "", None

    def _ver(mod: str) -> Optional[str]:
        try:
            return __import__(mod).__version__
        except Exception:
            return None

    return {
        "python": sys.version.split()[0],
        "pip_freeze_sha256_16": freeze_hash,
        # Faker governs whether the same seed reproduces the same ground truth,
        # so it is named explicitly rather than buried in the freeze hash.
        "faker": _ver("faker"),
        "torch": _ver("torch"),
        "transformers": _ver("transformers"),
        "lifelines": _ver("lifelines"),
    }


def accelerator() -> Dict:
    """GPU model and memory. Without the model, accelerator-hours cannot be aggregated."""
    try:
        import torch
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            return {"device": "cuda", "name": props.name,
                    "total_mem_gb": round(props.total_memory / (1024 ** 3), 1),
                    "count": torch.cuda.device_count()}
        return {"device": "mps" if getattr(torch.backends, "mps", None)
                and torch.backends.mps.is_available() else "cpu",
                "name": None, "total_mem_gb": None, "count": 0}
    except Exception:
        return {"device": "unknown", "name": None, "total_mem_gb": None, "count": 0}


def target_subset_hash(pairs: Sequence[Tuple[str, str, str]]) -> str:
    """
    Hash the exact target set: (arm, person_id, field) triples, sorted.

    Sorted so shard-to-shard ordering differences do not register as a change;
    the arm is included so a person moving between arms is caught.
    """
    canon = json.dumps(sorted(tuple(map(str, t)) for t in pairs),
                       separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canon.encode()).hexdigest()[:16]


def build(*, study_id: str, run_id: str, exp_id: str, model_name: str,
          model_state: str, seed: int, fields: List[str],
          capacity_k: Optional[int], gcg_iters: int,
          subset_pairs: Sequence[Tuple[str, str, str]],
          tier_composition: Dict[int, int], arm_sizes: Dict[str, int],
          extra: Optional[Dict] = None) -> Dict:
    """Assemble the manifest for one shard."""
    return {
        "schema": "run-manifest-v1",
        "study_id": study_id,
        "run_id": run_id,
        "exp_id": exp_id,
        "shard": {"model_name": model_name, "model_state": model_state,
                  "seed": seed, "capacity_k": capacity_k, "fields": list(fields)},
        # --- the invariants that must agree across every shard ---
        "gcg_iters": gcg_iters,
        "target_subset_hash": target_subset_hash(subset_pairs),
        "n_targets": len(subset_pairs),
        "arm_sizes": dict(arm_sizes),
        "tier_composition": {str(k): v for k, v in sorted(tier_composition.items())},
        # --- pins ---
        "code": git_state(),
        "env": env_lock(),
        "accelerator": accelerator(),
        "config": {k: v for k, v in sorted(os.environ.items()) if k.startswith("PII_")},
        **(extra or {}),
    }


def write(manifest: Dict, out_dir: str, stem: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{stem}.json")
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"  [manifest] {path}  subset={manifest['target_subset_hash']} "
          f"N={manifest['gcg_iters']} arms={manifest['arm_sizes']}")
    return path


def compare(paths: Sequence[str]) -> Dict:
    """
    Check the cross-shard invariants. Returns {"ok": bool, ...}.

    A mismatch BLOCKS analysis. Do not fall back to "use the shards that agree"
    -- if the target set moved, the paired design across k is gone, and the
    surviving agreement is a subset chosen after seeing the data.
    """
    seen: Dict[str, set] = {"target_subset_hash": set(), "gcg_iters": set()}
    rows = []
    for p in paths:
        with open(p) as f:
            m = json.load(f)
        rows.append({"path": p, "k": m["shard"]["capacity_k"],
                     "seed": m["shard"]["seed"],
                     "target_subset_hash": m["target_subset_hash"],
                     "gcg_iters": m["gcg_iters"]})
        for key in seen:
            seen[key].add(m[key])
    ok = all(len(v) == 1 for v in seen.values())
    return {"ok": ok, "n_shards": len(rows),
            "distinct": {k: sorted(v) for k, v in seen.items()}, "shards": rows}


# ---------------------------------------------------------------------------
# Data pin: content hashes for the corpus and the target registry.
#
# The design's five-pins table lists Data as "not recorded". Matching
# source_counts between two environments is suggestive but not proof -- it says
# how many passages came from where, not which ones, and says nothing about the
# Faker-generated ground truth that every metric is scored against. These
# hashes are the actual pin, and comparing them across environments is what
# turns "the corpus regenerates" from a hope into a checked fact.
# ---------------------------------------------------------------------------

# target_registry.json is THE registry: _load_registry() reads exactly this file
# (experiments.py:644). real_target_registry.json is written only by the real-PII
# (Enron) path in data_generation.py and is correctly absent on synthetic data --
# an earlier version of this module treated it as canonical and silently skipped
# the registry statistics whenever it was missing, i.e. always.
_REGISTRY = "target_registry.json"
_DATA_FILES = (
    _REGISTRY,
    "individuals.json",
    "negative_controls.json",
    "corpus/train.json",
    "real_target_registry.json",   # present only under use_real_pii=True
)


def data_fingerprint(data_dir: str = "data") -> Dict:
    """sha256 of each ground-truth artefact, plus the registry's arm counts."""
    out: Dict = {"files": {}}
    for rel in _DATA_FILES:
        path = os.path.join(data_dir, rel)
        if not os.path.exists(path):
            out["files"][rel] = None
            continue
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        out["files"][rel] = {"sha256_16": h.hexdigest()[:16],
                             "bytes": os.path.getsize(path)}

    reg = os.path.join(data_dir, _REGISTRY)
    if os.path.exists(reg):
        with open(reg) as f:
            entries = json.load(f)
        trained = [e for e in entries if not e.get("is_negative_control")]
        tiers: Dict[int, int] = {}
        for e in trained:
            tiers[int(e["frequency"])] = tiers.get(int(e["frequency"]), 0) + 1
        out["registry"] = {
            "file": _REGISTRY,
            "n_total": len(entries),
            "n_trained": len(trained),
            "n_control": len(entries) - len(trained),
            "frequency_tiers": {str(k): v for k, v in sorted(tiers.items())},
        }
        # What even_subset() will actually hand E3 at the configured cap. The
        # raw prefix is shown beside it because that is what the code did before
        # the t0-1 gate, and the difference is the gate's whole point.
        n = int(os.environ.get("PII_CAP_SWEEP_N", 25))
        if len(trained) > n >= 2:
            picks = sorted({round(i * (len(trained) - 1) / (n - 1)) for i in range(n)})
            even = {}
            for i in picks:
                f = int(trained[i]["frequency"]); even[f] = even.get(f, 0) + 1
            pre = {}
            for e in trained[:n]:
                f = int(e["frequency"]); pre[f] = pre.get(f, 0) + 1
            out["trained_subset_at_n"] = {
                "n": n,
                "even_subset": {str(k): v for k, v in sorted(even.items())},
                "raw_prefix_before_t0_1": {str(k): v for k, v in sorted(pre.items())},
            }
    meta = os.path.join(data_dir, "corpus_metadata.json")
    if os.path.exists(meta):
        with open(meta) as f:
            out["source_counts"] = json.load(f).get(
                "public_passages", {}).get("source_counts")
    return out


if __name__ == "__main__":
    import sys
    print(json.dumps(data_fingerprint(sys.argv[1] if len(sys.argv) > 1 else "data"),
                     indent=2, sort_keys=True))
