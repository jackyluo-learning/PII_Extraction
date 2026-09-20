"""Recompute D/C comparisons after field-level exposure correction.

Two trained-arm SSNs do not occur in the recovered fine-tuning text.  This
analysis removes those targets and one control SSN per target.  The preserved
E17 pair is used when that control was actually attacked; otherwise the nearest
available attacked control is selected with the same three E17 covariates.  The
rule is a disclosed post-result correction, not a preregistered exclusion.

H1, H2, and H4 retain the full control population because they are control-only
estimands.  This script supersedes the uncorrected D/C estimates for H3, H5, and
the D/C descriptive figures.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import csv
import json
import os
from pathlib import Path
import re
import unicodedata

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[5]
STUDY = ROOT / ".ai/research/studies/capacity_axis_20260902"
OUT = STUDY / "reanalysis"
ART = ROOT / "artifacts/capacity_axis_20260902"
GRID = np.array([0, 1, 2, 3, 4, 6, 8, 12, 16, 20, 24, 32, 48, 64])
POS = GRID[1:]
SEEDS = [42, 1337, 2024]
B = 10000
BOOT_SEED = 20240601


def clean(value):
    if isinstance(value, dict):
        return {str(key): clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [clean(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    return value


def save(value, path: Path) -> None:
    path.write_text(json.dumps(clean(value), indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def interval(values: np.ndarray) -> np.ndarray:
    return np.percentile(values, [2.5, 97.5], axis=0)


def wilson(proportion: float, effective_n: float) -> np.ndarray:
    z = 1.959963984540054
    denominator = 1 + z * z / effective_n
    center = (proportion + z * z / (2 * effective_n)) / denominator
    radius = z * np.sqrt(
        proportion * (1 - proportion) / effective_n
        + z * z / (4 * effective_n * effective_n)
    ) / denominator
    return np.array(
        [
            0.0 if proportion == 0 else max(0.0, center - radius),
            1.0 if proportion == 1 else min(1.0, center + radius),
        ]
    )


def mover(d_rate: float, c_rate: float, d_n: float, c_n: float) -> np.ndarray:
    d_low, d_high = wilson(d_rate, d_n)
    c_low, c_high = wilson(c_rate, c_n)
    return np.array(
        [
            d_rate - c_rate - np.hypot(d_rate - d_low, c_high - c_rate),
            d_rate - c_rate + np.hypot(d_high - d_rate, c_rate - c_low),
        ]
    )


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load() -> tuple[dict, pd.DataFrame]:
    ledger = json.loads((STUDY / "results.json").read_text())
    assert ledger["reanalysis"]["post_recovery_audit"]["repro_check"]["passed"] is True
    runs = {row["run_id"]: row for row in ledger["runs"]}
    frames = []
    for run_id in ledger["reanalysis"]["analysis_run_ids"]:
        run = runs[run_id]
        assert run["run_status"] == "completed" and not run["excluded"]
        artifact = next(
            item
            for item in run["artifacts"]
            if isinstance(item, dict) and item.get("evidence_kind") == "raw_attempts"
        )
        path = ROOT / artifact["path"]
        assert file_sha256(path) == artifact["sha256"]
        frames.append(pd.read_parquet(path))
    frame = pd.concat(frames, ignore_index=True)
    key = ["seed", "capacity_k", "target_membership", "person_id", "field"]
    assert len(frame) == 4200 and not frame.duplicated(key).any()
    assert set(frame.seed) == set(SEEDS) and set(frame.capacity_k) == set(GRID)
    return ledger, frame


PAIR_PATH = (
    STUDY
    / "reanalysis/cheaha-e3-evidence/e3-evidence.7JJ8Gj/results/e17_matches_e3a_seed42.json"
)
TRAIN_PATH = ART / "recovered_colab/data/corpus/train.json"
FIGURE_DIR = ART / "figures/field_exposure_corrected"
RESULT_PATH = OUT / "field_exposure_corrected.json"
CURVE_CSV = OUT / "field_exposure_corrected_curve.csv"
EXCLUSION_CSV = OUT / "field_exposure_exclusions.csv"


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower().strip()
    return re.sub(r"\s+", " ", text)


def target_value(target_string: str, field: str) -> str:
    return re.sub(rf"^{re.escape(field)}\s*:\s*", "", target_string, flags=re.I)


def anon(value: str) -> str:
    return sha256(str(value).encode()).hexdigest()[:12]


def exposure_and_pair_filter(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    base = df[df.capacity_k == 1].drop_duplicates(
        ["target_membership", "person_id", "field"]
    ).copy()
    base["char_len"] = base.target_string.str.len().astype(float)

    corpus = json.loads(TRAIN_PATH.read_text())
    normalized_corpus = "\n".join(normalize_text(row["text"]) for row in corpus)
    digit_corpus = "\n".join(re.sub(r"\D", "", row["text"]) for row in corpus)

    absent = []
    trained = base[base.target_membership == "trained"]
    for row in trained.itertuples(index=False):
        value = target_value(str(row.target_string), str(row.field))
        present = (
            re.sub(r"\D", "", value) in digit_corpus
            if row.field == "ssn"
            else normalize_text(value) in normalized_corpus
        )
        if not present:
            absent.append((str(row.person_id), str(row.field)))
    assert len(absent) == 2 and {field for _, field in absent} == {"ssn"}

    pairs = json.loads(PAIR_PATH.read_text())
    attacked_controls = set(
        base.loc[base.target_membership == "control", "person_id"].astype(str)
    )
    selected_controls: set[tuple[str, str]] = set()
    exclusions = []

    # Standardization over the actual attacked D/C SSN population.  It is used
    # only for the fallback because the original E17 nearest target is absent
    # from the attacked C subset.
    ssn = base[base.field == "ssn"].copy()
    columns = ["char_len", "target_len_tokens", "target_H_bits"]
    scale = ssn[columns].std(ddof=0).replace(0, 1)
    controls = ssn[ssn.target_membership == "control"].copy()

    for d_person, field in absent:
        exact_rows = [
            pair
            for pair in pairs
            if str(pair["trained"]["person_id"]) == d_person
            and pair["trained"]["field"] == field
        ]
        assert len(exact_rows) == 1
        exact_c = str(exact_rows[0]["control"]["person_id"])
        exact_key = (exact_c, field)
        if exact_c in attacked_controls and exact_key not in selected_controls:
            chosen = exact_c
            method = "original_E17_pair"
            distance = None
        else:
            drow = ssn[
                (ssn.target_membership == "trained") & (ssn.person_id.astype(str) == d_person)
            ].iloc[0]
            candidates = controls[
                ~controls.apply(
                    lambda row: (str(row.person_id), field) in selected_controls, axis=1
                )
            ].copy()
            distances = (((candidates[columns] - drow[columns]) / scale) ** 2).sum(axis=1)
            chosen_index = distances.idxmin()
            chosen = str(candidates.loc[chosen_index, "person_id"])
            method = "posthoc_nearest_attacked_C_same_E17_covariates"
            distance = float(distances.loc[chosen_index])
        selected_controls.add((chosen, field))
        exclusions.append(
            {
                "trained_person_id_internal": d_person,
                "trained_target_id": anon(f"trained|{d_person}|{field}"),
                "field": field,
                "control_person_id_internal": chosen,
                "control_target_id": anon(f"control|{chosen}|{field}"),
                "pair_method": method,
                "original_e17_control_was_attacked": exact_c in attacked_controls,
                "fallback_standardized_squared_distance": distance,
            }
        )

    drop_keys = {
        ("trained", row["trained_person_id_internal"], row["field"])
        for row in exclusions
    } | {
        ("control", row["control_person_id_internal"], row["field"])
        for row in exclusions
    }
    keep = [
        (str(arm), str(person), str(field)) not in drop_keys
        for arm, person, field in zip(df.target_membership, df.person_id, df.field)
    ]
    filtered = df.loc[keep].copy()
    assert len(filtered) == 4032
    target_counts = filtered.drop_duplicates(
        ["target_membership", "person_id", "field"]
    ).groupby(["target_membership", "field"], observed=True).size().to_dict()
    assert target_counts == {
        ("control", "email"): 25,
        ("control", "ssn"): 23,
        ("trained", "email"): 25,
        ("trained", "ssn"): 23,
    }
    return filtered, exclusions


def arm_bootstrap(frame: pd.DataFrame, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, list[str]]:
    people = sorted(frame.person_id.astype(str).unique())
    success = np.zeros((len(people), len(GRID)), dtype=float)
    count = np.zeros_like(success)
    for person_index, person in enumerate(people):
        group = frame[frame.person_id.astype(str) == person]
        by_k = group.groupby("capacity_k", observed=True).exact_match.agg(["sum", "count"])
        success[person_index] = by_k.reindex(GRID)["sum"].to_numpy(float)
        count[person_index] = by_k.reindex(GRID)["count"].to_numpy(float)
    assert np.all(count > 0)
    point = success.sum(axis=0) / count.sum(axis=0)
    indices = rng.integers(0, len(people), size=(B, len(people)))
    replicate = success[indices].sum(axis=1) / count[indices].sum(axis=1)
    return point, replicate, people


def corrected_curves(df: pd.DataFrame) -> tuple[dict, dict, dict]:
    curves = {}
    bootstraps = {}
    for scope_index, scope in enumerate(("pooled", "ssn", "email")):
        subset = df if scope == "pooled" else df[df.field == scope]
        points = {}
        reps = {}
        people = {}
        for arm_index, arm in enumerate(("control", "trained")):
            arm_frame = subset[subset.target_membership == arm]
            rng = np.random.default_rng(BOOT_SEED + 100 * scope_index + arm_index)
            points[arm], reps[arm], people[arm] = arm_bootstrap(arm_frame, rng)
        tau_reps = reps["trained"] - reps["control"]
        rows = []
        for column, k in enumerate(GRID):
            row = {"k": int(k), "n_seeds": len(SEEDS)}
            degenerate = False
            for arm in ("control", "trained"):
                cell = subset[
                    (subset.target_membership == arm) & (subset.capacity_k == k)
                ]
                n_targets = cell.drop_duplicates(["person_id", "field"]).shape[0]
                estimate = float(points[arm][column])
                mean_targets_per_person = n_targets / len(people[arm])
                effective_n = n_targets / (1 + (mean_targets_per_person - 1) * 0.5)
                is_degenerate = estimate in (0.0, 1.0)
                degenerate = degenerate or is_degenerate
                row[arm] = {
                    "estimate": estimate,
                    "ci": wilson(estimate, effective_n) if is_degenerate else interval(reps[arm][:, column]),
                    "interval_method": "Wilson with target-cluster ICC=0.5 effective n" if is_degenerate else "person-clustered percentile bootstrap",
                    "n_persons": len(people[arm]),
                    "n_targets": n_targets,
                    "n_attempts": len(cell),
                    "successes": int(cell.exact_match.sum()),
                    "n_eff_if_wilson": effective_n,
                }
            row["tau"] = row["trained"]["estimate"] - row["control"]["estimate"]
            row["tau_ci"] = (
                mover(
                    row["trained"]["estimate"],
                    row["control"]["estimate"],
                    row["trained"]["n_eff_if_wilson"],
                    row["control"]["n_eff_if_wilson"],
                )
                if degenerate
                else interval(tau_reps[:, column])
            )
            row["tau_interval_method"] = (
                "Newcombe/MOVER from Wilson intervals with target-cluster ICC=0.5 effective n"
                if degenerate
                else "independent-arm person-clustered percentile bootstrap"
            )
            rows.append(row)
        curves[scope] = rows
        bootstraps[scope] = {
            "control": reps["control"],
            "trained": reps["trained"],
            "tau": tau_reps,
        }
    return curves, bootstraps, people


def bootstrap_p(replicates: np.ndarray, point: float) -> float:
    return float(
        (np.count_nonzero(np.abs(replicates - point) >= abs(point) - 1e-12) + 1)
        / (len(replicates) + 1)
    )


def corrected_hypotheses(curves: dict, bootstraps: dict, ledger: dict) -> tuple[dict, dict]:
    pooled = curves["pooled"]
    tau_reps = bootstraps["pooled"]["tau"]
    k20_index = list(GRID).index(20)
    h3_point = pooled[k20_index]["tau"]
    h3 = {
        "status": "post-result field-exposure correction; supersedes unfiltered H3 for D/C interpretation",
        "tau": h3_point,
        "ci": pooled[k20_index]["tau_ci"],
        "p_raw": bootstrap_p(tau_reps[:, k20_index], h3_point),
        "n_persons_per_arm": 25,
        "n_targets_per_arm": 48,
        "n_seeds": 3,
        "rule": "same H3 k=20 estimator and person-clustered interval after declared post-result field-exposure correction",
    }

    positive_tau = tau_reps[:, 1:]
    maxima = positive_tau.max(axis=1)
    ties = np.isclose(positive_tau, maxima[:, None], atol=1e-12, rtol=0)
    earliest = POS[np.argmax(ties, axis=1)]
    latest = POS[len(POS) - 1 - np.argmax(ties[:, ::-1], axis=1)]
    observed = np.array([row["tau"] for row in pooled[1:]])
    observed_maxima = POS[np.isclose(observed, observed.max(), atol=1e-12, rtol=0)]
    design = np.stack([np.ones(len(POS)), np.log(POS), np.log(POS) ** 2], axis=1)
    inverse = np.linalg.pinv(design).T
    coefficient = observed @ inverse
    coefficient_reps = positive_tau @ inverse
    h5 = {
        "label": "(exploratory), field-exposure corrected, underpowered",
        "observed_maximizers": observed_maxima,
        "argmax_envelope_ci": [np.percentile(earliest, 2.5), np.percentile(latest, 97.5)],
        "first_argmax_ci": interval(earliest),
        "tied_maximum_replicates": int((ties.sum(axis=1) > 1).sum()),
        "quadratic_logk_coefficient": float(coefficient[2]),
        "quadratic_ci": interval(coefficient_reps[:, 2]),
        "quadratic_one_sided_p": float(
            (np.count_nonzero(coefficient_reps[:, 2] - coefficient[2] <= coefficient[2] + 1e-12) + 1)
            / (B + 1)
        ),
        "status": "post-result field-exposure correction; supersedes unfiltered H5 for D/C interpretation",
    }

    original = ledger["reanalysis"]["estimates"]
    raw_ps = {
        "H1": original["hypotheses"]["H1"]["p_raw"],
        "H2": 1.0,
        "H3": h3["p_raw"],
        "H4": original["hypotheses"]["H4"]["p_raw"],
    }
    order = sorted(raw_ps, key=raw_ps.get)
    last = 0.0
    holm = {}
    for position, hypothesis in enumerate(order):
        last = max(last, min(1.0, (4 - position) * raw_ps[hypothesis]))
        holm[hypothesis] = {
            "p_raw_or_reserved": raw_ps[hypothesis],
            "p_holm": last,
            "reject_at_0_05": last < 0.05,
            "H2_reserved_not_tested": hypothesis == "H2",
        }
    return {"H3": h3, "H5": h5}, holm


def write_tables(result: dict) -> None:
    rows = []
    for scope, curve in result["curves"].items():
        for row in curve:
            for arm in ("trained", "control"):
                cell = row[arm]
                rows.append(
                    {
                        "scope": scope,
                        "k": row["k"],
                        "arm": arm,
                        "n_persons": cell["n_persons"],
                        "n_targets": cell["n_targets"],
                        "n_seeds": row["n_seeds"],
                        "n_attempts": cell["n_attempts"],
                        "successes": cell["successes"],
                        "rate": cell["estimate"],
                        "ci_lower": cell["ci"][0],
                        "ci_upper": cell["ci"][1],
                        "tau": row["tau"],
                        "tau_lower": row["tau_ci"][0],
                        "tau_upper": row["tau_ci"][1],
                    }
                )
    with CURVE_CSV.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    public_exclusions = [
        {key: value for key, value in row.items() if not key.endswith("_internal")}
        for row in result["exclusions"]
    ]
    with EXCLUSION_CSV.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(public_exclusions[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(public_exclusions)


def fallback_control_sensitivity(frame: pd.DataFrame, exclusions: list[dict]) -> dict:
    """Vary the second removed C-SSN over every eligible attacked control.

    This checks whether the post-hoc nearest-covariate choice determines H3. It
    does not restore target-level E17 pairing and is not used to choose a C.
    """
    removed_d = {row["trained_person_id_internal"] for row in exclusions}
    exact_c = next(
        row["control_person_id_internal"]
        for row in exclusions
        if row["original_e17_control_was_attacked"]
    )
    chosen_fallback = next(
        row["control_person_id_internal"]
        for row in exclusions
        if not row["original_e17_control_was_attacked"]
    )
    candidates = sorted(
        set(
            frame.loc[
                (frame.target_membership == "control") & (frame.field == "ssn"),
                "person_id",
            ].astype(str)
        )
        - {exact_c}
    )
    k20 = frame[frame.capacity_k == 20]
    d = k20[
        (k20.target_membership == "trained")
        & ~((k20.field == "ssn") & k20.person_id.astype(str).isin(removed_d))
    ]
    d_rate = float(d.exact_match.mean())
    values = []
    for candidate in candidates:
        c = k20[
            (k20.target_membership == "control")
            & ~(
                (k20.field == "ssn")
                & k20.person_id.astype(str).isin({exact_c, candidate})
            )
        ]
        assert len(c) == 144 and len(d) == 144
        values.append((candidate, d_rate - float(c.exact_match.mean())))
    selected = next(value for candidate, value in values if candidate == chosen_fallback)
    return {
        "label": "post-hoc fallback-C robustness diagnostic; does not restore E17 pairing",
        "n_eligible_attacked_C_SSN_choices": len(values),
        "k20_tau_min": min(value for _, value in values),
        "k20_tau_max": max(value for _, value in values),
        "selected_fallback_k20_tau": selected,
    }


def make_figures(df: pd.DataFrame, result: dict) -> list[Path]:
    os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/e3-field-exposure-mpl")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
    from matplotlib.ticker import PercentFormatter

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 300}
    )
    positions = np.arange(len(GRID))
    styles = {
        "trained": ("D (field exposed)", "#0072B2", "o", "-"),
        "control": ("C (field-count-balanced control set)", "#D55E00", "s", "--"),
    }
    titles = {"pooled": "Overall: 48 targets/arm", "ssn": "SSN: 23 targets/arm", "email": "Email: 25 targets/arm"}
    fig, axes = plt.subplots(1, 3, figsize=(15.8, 4.8), sharey=True, constrained_layout=True)
    for ax, scope in zip(axes, ("pooled", "ssn", "email")):
        curve = result["curves"][scope]
        for arm, offset in (("trained", 0.07), ("control", -0.07)):
            label, color, marker, linestyle = styles[arm]
            y = np.array([row[arm]["estimate"] for row in curve])
            ci = np.array([row[arm]["ci"] for row in curve])
            yerr = np.vstack((y - ci[:, 0], ci[:, 1] - y))
            ax.errorbar(positions[0] + offset, y[0], yerr=yerr[:, :1], color=color, marker="D", linestyle="none", capsize=3)
            ax.errorbar(positions[1:] + offset, y[1:], yerr=yerr[:, 1:], label=label, color=color, marker=marker, linestyle=linestyle, capsize=2.5)
        ax.axvspan(-0.55, 0.5, color="#eeeeee", zorder=0)
        ax.axvline(0.5, color="#777777", linestyle=":", linewidth=1)
        ax.set_xticks(positions, [str(int(k)) for k in GRID])
        ax.set_title(titles[scope])
        ax.set_xlabel("Free prompt tokens k")
        ax.set_ylim(-0.03, 1.05)
        ax.yaxis.set_major_formatter(PercentFormatter(1.0))
        ax.grid(axis="y", alpha=0.2)
        ax.tick_params(axis="x", labelsize=8)
    axes[0].set_ylabel("Exact-match rate")
    axes[0].legend(frameon=False, fontsize=9)
    fig.suptitle("Field-exposure-corrected D/C curves (post-result field-count-balanced exclusion)")
    outputs = []
    for suffix in ("png", "pdf"):
        path = FIGURE_DIR / f"extraction_rates_by_k_field_exposure_corrected.{suffix}"
        fig.savefig(path, bbox_inches="tight", metadata={"CreationDate": None, "ModDate": None} if suffix == "pdf" else None)
        outputs.append(path)
    plt.close(fig)

    pooled = result["curves"]["pooled"]
    y = np.array([row["tau"] for row in pooled])
    ci = np.array([row["tau_ci"] for row in pooled])
    fig, ax = plt.subplots(figsize=(9.5, 4.6), constrained_layout=True)
    ax.errorbar(positions[0], y[0], yerr=np.array([[y[0] - ci[0, 0]], [ci[0, 1] - y[0]]]), marker="D", linestyle="none", color="#555555", capsize=3)
    ax.errorbar(positions[1:], y[1:], yerr=np.vstack((y[1:] - ci[1:, 0], ci[1:, 1] - y[1:])), marker="o", color="#555555", capsize=3)
    ax.axhline(0, color="#777777", linewidth=1)
    ax.axvspan(-0.55, 0.5, color="#eeeeee", zorder=0)
    ax.axvline(0.5, color="#777777", linestyle=":", linewidth=1)
    ax.set_xticks(positions, [str(int(k)) for k in GRID])
    ax.set_xlabel("Free prompt tokens k")
    ax.set_ylabel("D − C exact-match rate")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_title("Field-exposure-corrected D/C difference (48 targets/arm, 25 people/arm, 3 attack seeds)")
    ax.grid(axis="y", alpha=0.2)
    for suffix in ("png", "pdf"):
        path = FIGURE_DIR / f"tau_by_k_field_exposure_corrected.{suffix}"
        fig.savefig(path, bbox_inches="tight", metadata={"CreationDate": None, "ModDate": None} if suffix == "pdf" else None)
        outputs.append(path)
    plt.close(fig)

    row_specs = (("ssn", "control", "SSN | C"), ("ssn", "trained", "SSN | D"), ("email", "control", "Email | C"), ("email", "trained", "Email | D"))
    matrix = np.array([[row[arm]["successes"] for row in result["curves"][field]] for field, arm, _ in row_specs])
    denominators = np.array([[row[arm]["n_attempts"] for row in result["curves"][field]] for field, arm, _ in row_specs])
    fig, ax = plt.subplots(figsize=(15.2, 4.0), constrained_layout=True)
    image = ax.imshow(matrix, aspect="auto", cmap="Blues", vmin=0, vmax=75)
    ax.set_xticks(positions, [str(int(k)) for k in GRID])
    ax.set_yticks(np.arange(4), [label for _, _, label in row_specs])
    ax.set_xlabel("Free prompt tokens k")
    ax.set_title("Field-exposure-corrected exact-match counts (SSN denominator 69; email denominator 75)")
    for row_index in range(4):
        for column in range(len(GRID)):
            value = matrix[row_index, column]
            ax.text(column, row_index, f"{value}/{denominators[row_index, column]}", ha="center", va="center", fontsize=7, color="white" if value >= 42 else "#111111")
    fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02).set_label("Exact-match successes")
    for suffix in ("png", "pdf"):
        path = FIGURE_DIR / f"extraction_counts_by_field_field_exposure_corrected.{suffix}"
        fig.savefig(path, bbox_inches="tight", metadata={"CreationDate": None, "ModDate": None} if suffix == "pdf" else None)
        outputs.append(path)
    plt.close(fig)

    labels = {}
    for arm in ("trained", "control"):
        people = sorted(df.loc[df.target_membership == arm, "person_id"].astype(str).unique(), key=lambda p: sha256(f"{arm}|{p}".encode()).hexdigest())
        labels.update({(arm, person): f"{'D' if arm == 'trained' else 'C'}{index:02d}" for index, person in enumerate(people, 1)})
    grouped = df.groupby(["target_membership", "person_id", "field", "capacity_k"], observed=True).exact_match.sum()
    cmap = ListedColormap(("#f7f7f7", "#c6dbef", "#6baed6", "#08519c"))
    norm = BoundaryNorm(np.arange(-0.5, 4.5, 1), cmap.N)
    fig, axes = plt.subplots(2, 2, figsize=(16.2, 11.4), constrained_layout=True)
    image = None
    for row_index, field in enumerate(("ssn", "email")):
        for column_index, arm in enumerate(("trained", "control")):
            ax = axes[row_index, column_index]
            targets = sorted({str(person) for a, person, f, _ in grouped.index if a == arm and f == field}, key=lambda person: labels[(arm, person)])
            matrix = np.array([[int(grouped.loc[(arm, person, field, int(k))]) for k in GRID] for person in targets])
            image = ax.imshow(matrix, aspect="auto", cmap=cmap, norm=norm, interpolation="nearest")
            target_labels = [f"{labels[(arm, person)]}-{'S' if field == 'ssn' else 'E'}" for person in targets]
            ax.set_xticks(positions, [str(int(k)) for k in GRID])
            ax.set_yticks(np.arange(len(targets)), target_labels)
            ax.set_title(f"{'D' if arm == 'trained' else 'C'} — {field.upper()} | {len(targets)} targets")
            ax.set_xlabel("Free prompt tokens k")
            ax.set_ylabel("Anonymous target ID")
            ax.tick_params(axis="x", labelsize=8)
            ax.tick_params(axis="y", labelsize=6.5)
    fig.colorbar(image, ax=axes, ticks=(0, 1, 2, 3), shrink=0.62, pad=0.02).set_label("Successful attack seeds (out of 3)")
    fig.suptitle("Field-exposure-corrected target success across k")
    for suffix in ("png", "pdf"):
        path = FIGURE_DIR / f"target_success_by_k_field_exposure_corrected.{suffix}"
        fig.savefig(path, bbox_inches="tight", metadata={"CreationDate": None, "ModDate": None} if suffix == "pdf" else None)
        outputs.append(path)
    plt.close(fig)
    return outputs


def main() -> None:
    ledger, frame = load()
    filtered, exclusions = exposure_and_pair_filter(frame)
    curves, bootstraps, _ = corrected_curves(filtered)
    hypotheses, holm = corrected_hypotheses(curves, bootstraps, ledger)
    fallback_sensitivity = fallback_control_sensitivity(frame, exclusions)
    result = {
        "status": "post-result_field_exposure_corrected_D_C_analysis",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "supersedes": "unfiltered H3, H5, and D/C descriptive figures for membership interpretation",
        "does_not_supersede": "H1, H2, and H4, which retain the full control population",
        "deviation": "Two SSN field values labelled trained at person level were absent from the recovered fine-tuning text. The exclusion was decided after inspection and is not preregistered.",
        "pairing_limitation": "E17 field pairs were discarded by the executed control-person deduplication/capping path. One original E17 paired C was not attacked, so the nearest actually attacked C-SSN under the same three covariates was substituted post hoc.",
        "source_rows_before": len(frame),
        "source_rows_after": len(filtered),
        "n_targets_per_arm": 48,
        "n_people_per_arm": 25,
        "n_attack_seeds": 3,
        "exclusions": exclusions,
        "curves": curves,
        "hypotheses": hypotheses,
        "holm": holm,
        "fallback_control_sensitivity": fallback_sensitivity,
    }
    write_tables(result)
    figure_paths = make_figures(filtered, result)
    result["artifacts"] = [
        {
            "path": str(path.relative_to(STUDY.parents[3])),
            "bytes": path.stat().st_size,
            "sha256": sha256(path.read_bytes()).hexdigest(),
        }
        for path in (CURVE_CSV, EXCLUSION_CSV, *figure_paths)
    ]
    # Do not persist raw synthetic identifiers in public derived artifacts.
    public_result = clean(result)
    for row in public_result["exclusions"]:
        row.pop("trained_person_id_internal", None)
        row.pop("control_person_id_internal", None)
    save(public_result, RESULT_PATH)
    ledger["reanalysis"]["field_exposure_corrected"] = public_result
    ledger["reanalysis"]["status"] = "computed_conditionally_with_field_exposure_corrected_D_C_and_independent_review_complete_pending_final_acceptance"
    save(ledger, STUDY / "results.json")
    print(
        json.dumps(
            clean(
                {
                    "excluded_pairs": public_result["exclusions"],
                    "H3": hypotheses["H3"],
                    "H5": hypotheses["H5"],
                    "holm": holm,
                    "artifacts": public_result["artifacts"],
                }
            ),
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
