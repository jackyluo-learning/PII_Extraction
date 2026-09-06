"""Build complete descriptive E3 tables and figures from ledger-linked raw attempts.

The script first verifies and aggregates the raw artifacts named by results.json,
writes the derived target-level cells back into the authoritative estimates section,
then reloads results.json and renders every visible number from that ledger state.
"""

from __future__ import annotations

from collections import defaultdict
import csv
import hashlib
import json
import os
from pathlib import Path

import numpy as np

from recompute import ART, GRID, OUT, SEEDS, STUDY, clean, load, save


ARM_ORDER = ("trained", "control")
ARM_CODE = {"trained": "D", "control": "C"}
FIELD_CODE = {"ssn": "S", "email": "E"}


def stable_person_labels(df, study_id: str) -> dict[tuple[str, str], str]:
    """Assign deterministic anonymous labels without retaining names in outputs."""
    labels = {}
    for arm in ARM_ORDER:
        people = sorted(
            df.loc[df.target_membership == arm, "person_id"].unique(),
            key=lambda person: hashlib.sha256(
                f"{study_id}|{arm}|{person}".encode()
            ).hexdigest(),
        )
        assert len(people) == 25
        for position, person in enumerate(people, start=1):
            labels[(arm, person)] = f"{ARM_CODE[arm]}{position:02d}"
    return labels


def aggregate_targets(df, study_id: str) -> dict:
    labels = stable_person_labels(df, study_id)
    cells = []
    summaries = []

    for (arm, person, field), group in df.groupby(
        ["target_membership", "person_id", "field"], sort=True, observed=True
    ):
        target_id = f"{labels[(arm, person)]}-{FIELD_CODE[field]}"
        by_k = []
        for k, cell in group.groupby("capacity_k", sort=True, observed=True):
            assert len(cell) == len(SEEDS)
            assert set(int(seed) for seed in cell.seed) == set(SEEDS)
            successful_seeds = sorted(
                int(seed) for seed in cell.loc[cell.exact_match, "seed"]
            )
            by_k.append(
                {
                    "arm": arm,
                    "arm_code": ARM_CODE[arm],
                    "field": field,
                    "target_id": target_id,
                    "k": int(k),
                    "n_seeds": len(SEEDS),
                    "successes_out_of_3": len(successful_seeds),
                    "successful_seeds": successful_seeds,
                }
            )

        assert [row["k"] for row in by_k] == list(GRID)
        hit_ks = [row["k"] for row in by_k if row["successes_out_of_3"] > 0]
        first_success = min(hit_ks) if hit_ks else None
        total_successes = sum(row["successes_out_of_3"] for row in by_k)
        for row in by_k:
            row["success_rate"] = row["successes_out_of_3"] / len(SEEDS)
        cells.extend(by_k)
        summaries.append(
            {
                "arm": arm,
                "arm_code": ARM_CODE[arm],
                "field": field,
                "target_id": target_id,
                "first_observed_success_k": first_success,
                "total_successes_out_of_42": total_successes,
                "k_values_with_any_success": len(hit_ks),
            }
        )

    assert len(summaries) == 100
    assert len(cells) == 100 * len(GRID)
    field_counts = []
    for (arm, field, k), group in df.groupby(
        ["target_membership", "field", "capacity_k"], sort=True, observed=True
    ):
        per_target = group.groupby("person_id", observed=True).exact_match.sum()
        assert len(group) == 75 and len(per_target) == 25
        field_counts.append(
            {
                "arm": arm,
                "arm_code": ARM_CODE[arm],
                "field": field,
                "k": int(k),
                "successful_attempts": int(group.exact_match.sum()),
                "attempts": len(group),
                "exact_match_rate": float(group.exact_match.mean()),
                "targets_any_seed": int((per_target >= 1).sum()),
                "targets_majority_seeds": int((per_target >= 2).sum()),
                "targets_all_seeds": int((per_target == 3).sum()),
                "n_targets": len(per_target),
                "n_seeds": len(SEEDS),
            }
        )
    assert len(field_counts) == 2 * 2 * len(GRID)

    return {
        "status": "exploratory_descriptive",
        "source": "checksum-verified raw_attempts artifacts named by results.json",
        "scope": "42 Cheaha main-sweep shards only; Colab pilot/cost/repro excluded",
        "created_from_rows": len(df),
        "n_targets": len(summaries),
        "n_persons_per_arm": 25,
        "n_fields": 2,
        "n_seeds": len(SEEDS),
        "k_grid": [int(k) for k in GRID],
        "target_id_method": (
            "Within each arm, people receive stable sequence labels from a SHA-256 "
            "ordering of study_id, arm, and person_id; S/E identifies the field. "
            "No person name or target string is retained."
        ),
        "figure_row_order": (
            "Within each arm-field panel: first observed k with any successful seed "
            "ascending (never-successful last), then total successes descending, then "
            "stable anonymous target_id. This ordering is post-result and descriptive."
        ),
        "cell_definition": (
            "Number of exact-match successes among the three fixed attack seeds at "
            "one target and one k; no monotonic completion or interpolation is applied."
        ),
        "field_counts": field_counts,
        "target_summaries": summaries,
        "target_by_k": cells,
    }


def validate_against_curves(df, estimates: dict, descriptive: dict) -> None:
    assert len(df) == 4200
    assert set(int(k) for k in df.capacity_k.unique()) == set(int(k) for k in GRID)
    assert set(int(seed) for seed in df.seed.unique()) == set(SEEDS)
    assert (
        df.groupby(
            ["target_membership", "person_id", "field"], observed=True
        ).size()
        == len(GRID) * len(SEEDS)
    ).all()

    target_totals = defaultdict(int)
    for row in descriptive["target_by_k"]:
        target_totals[(row["arm"], row["field"], row["k"])] += row[
            "successes_out_of_3"
        ]

    for field in ("ssn", "email"):
        for curve_row in estimates["curves"][field]:
            k = curve_row["k"]
            for arm in ("trained", "control"):
                raw = df[
                    (df.target_membership == arm)
                    & (df.field == field)
                    & (df.capacity_k == k)
                ]
                assert len(raw) == 75
                expected = int(raw.exact_match.sum())
                assert expected == curve_row[arm]["successes"]
                assert expected == target_totals[(arm, field, k)]
                count_row = next(
                    row
                    for row in descriptive["field_counts"]
                    if row["arm"] == arm and row["field"] == field and row["k"] == k
                )
                assert expected == count_row["successful_attempts"]
                assert count_row["attempts"] == 75

    for curve_row in estimates["curves"]["pooled"]:
        k = curve_row["k"]
        for arm in ("trained", "control"):
            raw = df[
                (df.target_membership == arm) & (df.capacity_k == k)
            ]
            assert len(raw) == 150
            assert int(raw.exact_match.sum()) == curve_row[arm]["successes"]


def write_csv_tables(estimates: dict, descriptive: dict) -> None:
    rate_rows = []
    for scope in ("pooled", "ssn", "email"):
        for row in estimates["curves"][scope]:
            for arm in ARM_ORDER:
                value = row[arm]
                rate_rows.append(
                    {
                        "scope": scope,
                        "k": row["k"],
                        "arm": arm,
                        "arm_code": ARM_CODE[arm],
                        "n_persons": value["n_persons"],
                        "n_targets": value["n_targets"],
                        "n_seeds": row["n_seeds"],
                        "n_attempts": value["n_attempts"],
                        "exact_match_successes": value["successes"],
                        "exact_match_rate": value["estimate"],
                        "ci_lower": value["ci"][0],
                        "ci_upper": value["ci"][1],
                        "interval_method": value["interval_method"],
                    }
                )

    with (OUT / "extraction_rates_and_counts_full.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rate_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rate_rows)

    field_rows = descriptive["field_counts"]
    with (OUT / "extraction_counts_by_field_full.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(field_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(field_rows)

    summaries = {
        (row["arm"], row["field"], row["target_id"]): row
        for row in descriptive["target_summaries"]
    }
    target_rows = []
    for row in descriptive["target_by_k"]:
        summary = summaries[(row["arm"], row["field"], row["target_id"])]
        target_rows.append(
            {
                **{key: row[key] for key in (
                    "arm", "arm_code", "field", "target_id", "k", "n_seeds",
                    "successes_out_of_3", "success_rate"
                )},
                "successful_seeds": ";".join(map(str, row["successful_seeds"])),
                "first_observed_success_k": summary["first_observed_success_k"],
                "total_successes_out_of_42": summary["total_successes_out_of_42"],
            }
        )
    with (OUT / "target_success_by_k_full.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(target_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(target_rows)


def categorical_axis(ax, *, shade_anchor: bool = True) -> None:
    positions = np.arange(len(GRID))
    ax.set_xlim(-0.55, len(GRID) - 0.45)
    ax.set_xticks(positions, [str(int(k)) for k in GRID])
    ax.set_xlabel("Free prompt tokens k")
    if shade_anchor:
        ax.axvspan(-0.55, 0.5, color="#eeeeee", zorder=0)
        ax.axvline(0.5, color="#777777", linestyle=":", linewidth=1)


def plot_rates(estimates: dict, figure_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "savefig.dpi": 300,
        }
    )
    styles = {
        "trained": {"label": "D (trained)", "color": "#0072B2", "marker": "o", "linestyle": "-"},
        "control": {"label": "C (control)", "color": "#D55E00", "marker": "s", "linestyle": "--"},
    }
    titles = {
        "pooled": "Overall (preregistered D/C curve)",
        "ssn": "SSN (exploratory field split)",
        "email": "Email (exploratory field split)",
    }
    fig, axes = plt.subplots(1, 3, figsize=(15.8, 4.8), sharey=True, constrained_layout=True)
    positions = np.arange(len(GRID), dtype=float)
    for ax, scope in zip(axes, ("pooled", "ssn", "email")):
        rows = estimates["curves"][scope]
        for arm, offset in (("trained", 0.07), ("control", -0.07)):
            y = np.array([row[arm]["estimate"] for row in rows])
            intervals = np.array([row[arm]["ci"] for row in rows])
            yerr = np.vstack((y - intervals[:, 0], intervals[:, 1] - y))
            style = styles[arm]
            # k=0 is a fixed-probe anchor; do not connect it to the GCG sweep.
            ax.errorbar(
                positions[0] + offset,
                y[0],
                yerr=yerr[:, :1],
                color=style["color"],
                marker="D",
                linestyle="none",
                capsize=3,
                markersize=5,
                zorder=4,
            )
            ax.errorbar(
                positions[1:] + offset,
                y[1:],
                yerr=yerr[:, 1:],
                label=style["label"],
                color=style["color"],
                marker=style["marker"],
                linestyle=style["linestyle"],
                linewidth=1.5,
                markersize=4.5,
                capsize=2.5,
                zorder=3,
            )
        categorical_axis(ax)
        ax.set_title(titles[scope], fontsize=10.5)
        ax.set_ylim(-0.03, 1.05)
        ax.yaxis.set_major_formatter(PercentFormatter(1.0))
        ax.grid(axis="y", alpha=0.2)
        ax.tick_params(axis="x", labelsize=8)
    axes[0].set_ylabel("Exact-match extraction rate")
    axes[0].legend(loc="upper left", ncol=1, frameon=False, fontsize=9)
    fig.suptitle(
        "Conditional extraction rates across the complete capacity grid\n"
        "Diamonds in the shaded column: k=0 fixed-probe anchor; k≥1: GCG sweep",
        fontsize=12,
    )
    for suffix in ("png", "pdf"):
        options = {"bbox_inches": "tight"}
        if suffix == "pdf":
            options["metadata"] = {"CreationDate": None, "ModDate": None}
        fig.savefig(figure_dir / f"extraction_rates_by_k_full.{suffix}", **options)
    plt.close(fig)


def plot_counts(estimates: dict, figure_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    row_specs = (
        ("ssn", "control", "SSN | C"),
        ("ssn", "trained", "SSN | D"),
        ("email", "control", "Email | C"),
        ("email", "trained", "Email | D"),
    )
    matrix = np.array(
        [
            [row[arm]["successes"] for row in estimates["curves"][field]]
            for field, arm, _ in row_specs
        ],
        dtype=int,
    )
    assert matrix.shape == (4, len(GRID))
    fig, ax = plt.subplots(figsize=(15.2, 4.0), constrained_layout=True)
    image = ax.imshow(matrix, aspect="auto", cmap="Blues", vmin=0, vmax=75)
    ax.set_xticks(np.arange(len(GRID)), [str(int(k)) for k in GRID])
    ax.set_yticks(np.arange(4), [label for _, _, label in row_specs])
    ax.set_xlabel("Free prompt tokens k")
    ax.set_title(
        "Exploratory descriptive exact-match counts by field and arm\n"
        "Each cell is successful attempts / 75 (25 people × 3 fixed attack seeds)"
    )
    ax.axvspan(-0.5, 0.5, color="#dddddd", alpha=0.35)
    ax.axvline(0.5, color="#555555", linestyle=":", linewidth=1.2)
    ax.axhline(1.5, color="white", linewidth=2)
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            value = matrix[row, column]
            color = "white" if value >= 42 else "#111111"
            ax.text(column, row, str(value), ha="center", va="center", color=color, fontsize=8)
    bar = fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
    bar.set_label("Exact-match successes (out of 75)")
    for suffix in ("png", "pdf"):
        options = {"bbox_inches": "tight", "dpi": 300}
        if suffix == "pdf":
            options["metadata"] = {"CreationDate": None, "ModDate": None}
        fig.savefig(figure_dir / f"extraction_counts_by_field_full.{suffix}", **options)
    plt.close(fig)


def plot_targets(descriptive: dict, figure_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap

    cells = descriptive["target_by_k"]
    summaries = descriptive["target_summaries"]
    by_summary = {
        (row["arm"], row["field"], row["target_id"]): row for row in summaries
    }
    by_cell = {
        (row["arm"], row["field"], row["target_id"], row["k"]): row[
            "successes_out_of_3"
        ]
        for row in cells
    }
    cmap = ListedColormap(("#f7f7f7", "#c6dbef", "#6baed6", "#08519c"))
    norm = BoundaryNorm(np.arange(-0.5, 4.5, 1), cmap.N)
    fig, axes = plt.subplots(2, 2, figsize=(16.2, 11.8), constrained_layout=True)
    image = None
    for row_index, field in enumerate(("ssn", "email")):
        for column_index, arm in enumerate(ARM_ORDER):
            ax = axes[row_index, column_index]
            panel = [
                row for row in summaries if row["arm"] == arm and row["field"] == field
            ]
            panel.sort(
                key=lambda row: (
                    row["first_observed_success_k"] is None,
                    row["first_observed_success_k"] if row["first_observed_success_k"] is not None else 10**9,
                    -row["total_successes_out_of_42"],
                    row["target_id"],
                )
            )
            target_ids = [row["target_id"] for row in panel]
            matrix = np.array(
                [
                    [by_cell[(arm, field, target_id, int(k))] for k in GRID]
                    for target_id in target_ids
                ],
                dtype=int,
            )
            assert matrix.shape == (25, len(GRID))
            image = ax.imshow(matrix, aspect="auto", cmap=cmap, norm=norm, interpolation="nearest")
            ax.set_xticks(np.arange(len(GRID)), [str(int(k)) for k in GRID])
            ax.set_yticks(np.arange(25), target_ids)
            ax.tick_params(axis="x", labelsize=8)
            ax.tick_params(axis="y", labelsize=6.5)
            ax.set_xlabel("Free prompt tokens k")
            ax.set_ylabel("Anonymous target ID")
            ax.set_title(f"{ARM_CODE[arm]} ({arm}) — {field.upper()} | 25 targets")
            ax.axvspan(-0.5, 0.5, color="#cccccc", alpha=0.25)
            ax.axvline(0.5, color="#555555", linestyle=":", linewidth=1.1)
            ax.set_xticks(np.arange(-0.5, len(GRID), 1), minor=True)
            ax.set_yticks(np.arange(-0.5, 25, 1), minor=True)
            ax.grid(which="minor", color="white", linewidth=0.35)
            ax.tick_params(which="minor", bottom=False, left=False)
            # Validate the panel against its summaries while material is in memory.
            for summary in panel:
                key = (arm, field, summary["target_id"])
                assert summary == by_summary[key]
    assert image is not None
    bar = fig.colorbar(image, ax=axes, ticks=(0, 1, 2, 3), shrink=0.62, pad=0.02)
    bar.set_label("Successful attack seeds (out of 3)")
    fig.suptitle(
        "Exploratory descriptive target success across k (conditional on recovered rows)\n"
        "Rows ordered by first observed success, then total successes; no monotonic filling",
        fontsize=13,
    )
    for suffix in ("png", "pdf"):
        options = {"bbox_inches": "tight", "dpi": 300}
        if suffix == "pdf":
            options["metadata"] = {"CreationDate": None, "ModDate": None}
        fig.savefig(figure_dir / f"target_success_by_k_full.{suffix}", **options)
    plt.close(fig)


def main() -> None:
    os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/e3-mpl-cache")
    ledger, frame = load()
    estimates = ledger["reanalysis"]["estimates"]
    descriptive = aggregate_targets(frame, ledger["study_id"])
    validate_against_curves(frame, estimates, descriptive)
    estimates["descriptive_figures"] = clean(descriptive)
    # Keep the checked snapshot and authoritative ledger exactly synchronized.
    save(estimates, OUT / "recomputed_results.json")
    save(ledger, STUDY / "results.json")

    # Every table cell and plotted value below comes from the reloaded ledger.
    ledger = json.loads((STUDY / "results.json").read_text())
    estimates = ledger["reanalysis"]["estimates"]
    descriptive = estimates["descriptive_figures"]
    write_csv_tables(estimates, descriptive)
    figure_dir = ART / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    plot_rates(estimates, figure_dir)
    plot_counts(estimates, figure_dir)
    plot_targets(descriptive, figure_dir)

    artifact_paths = [
        OUT / "extraction_rates_and_counts_full.csv",
        OUT / "extraction_counts_by_field_full.csv",
        OUT / "target_success_by_k_full.csv",
    ]
    for stem in (
        "extraction_rates_by_k_full",
        "extraction_counts_by_field_full",
        "target_success_by_k_full",
    ):
        artifact_paths.extend((figure_dir / f"{stem}.png", figure_dir / f"{stem}.pdf"))
    artifact_rows = []
    for path in artifact_paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        artifact_rows.append(
            {
                "path": str(path.relative_to(STUDY.parents[3])),
                "bytes": path.stat().st_size,
                "sha256": digest,
            }
        )
    estimates["descriptive_figures"]["artifacts"] = artifact_rows
    save(estimates, OUT / "recomputed_results.json")
    save(ledger, STUDY / "results.json")
    print(
        json.dumps(
            {
                "source_rows": descriptive["created_from_rows"],
                "targets": descriptive["n_targets"],
                "target_by_k_cells": len(descriptive["target_by_k"]),
                "rate_count_csv_rows": 3 * len(GRID) * 2,
                "field_count_csv_rows": len(descriptive["field_counts"]),
                "figures": [
                    "extraction_rates_by_k_full",
                    "extraction_counts_by_field_full",
                    "target_success_by_k_full",
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
