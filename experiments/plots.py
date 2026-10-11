"""Figures for the paper, made from the result tables of run_stress_tests.py.

Each figure is saved as PDF (vector, for LaTeX) and PNG in results/figures/.
Sizes match the ICML two-column layout: 3.25 inch for one column,
6.75 inch for a figure that spans both columns.

The figures can be redrawn from the CSV files without running the
experiment again:
    python plots.py
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # draw to files only, no window needed

import matplotlib.pyplot as plt  # noqa: E402  (must come after matplotlib.use)
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import PercentFormatter  # noqa: E402

import config  # noqa: E402

ONE_COLUMN, TWO_COLUMNS = 3.25, 6.75  # figure widths in inches

# Colour-blind safe categorical colours, always used in this fixed order, each
# with its own marker so that overlapping lines stay distinguishable.
SERIES_COLORS = ("#2a78d6", "#eb6834", "#1baf7a")
SERIES_MARKERS = ("o", "s", "^")
INK, INK_SECONDARY, GRID = "#0b0b0b", "#52514e", "#e4e3df"

# Readable names for the values used in the result tables.
NAMES = {
    "personal_only": "Actor photos only",
    "personal_plus_in_character": "Actor photos + film references",
    "nearest": "Nearest neighbour (no interpolation)",
    "bicubic": "Bicubic interpolation",
    "lanczos": "Lanczos interpolation",
    "none": "Without CLAHE",
    "clahe": "With CLAHE",
    "dark": "Darkness",
    "red_alarm": "Red alarm light",
    "DerAlte": "Der Alte",
    "FritzGrade": "Fritz",
    "Johann": "Johann",
    "Werner": "Werner",
    "recognised": "Recognised",
    "closest_correct": "Closest\ncorrect",
    "extras_named": "Extras\nnamed",
}

plt.rcParams.update({
    "font.size": 8,
    "axes.titlesize": 8,
    "axes.edgecolor": INK_SECONDARY,
    "axes.labelcolor": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "xtick.color": INK_SECONDARY,
    "ytick.color": INK_SECONDARY,
    "legend.frameon": False,
    "lines.linewidth": 1.5,
    "lines.markersize": 5,
})


def _percent_axis(ax: plt.Axes) -> None:
    """Y-axis from 0 to 100 %."""
    ax.set_ylim(0, 1.02)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))


def _legend_below(fig: plt.Figure, ax: plt.Axes, ncol: int) -> None:
    """One legend for the whole figure, below the panels, away from the data."""
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=ncol, fontsize=7)


def save_figure(fig: plt.Figure, name: str, bottom: float | None = None) -> None:
    fig.tight_layout()
    if bottom is not None:  # leave room for a legend below the panels
        fig.subplots_adjust(bottom=bottom)
    for extension in ("pdf", "png"):
        fig.savefig(config.FIGURES_DIR / f"{name}.{extension}", dpi=200)
    plt.close(fig)


def _grouped_bars(ax: plt.Axes, table: pd.DataFrame) -> None:
    """Bars per row of `table`, one colour per column."""
    x = np.arange(len(table.index))
    width = 0.8 / len(table.columns)
    for i, (column, color) in enumerate(zip(table.columns, SERIES_COLORS)):
        offset = (i - (len(table.columns) - 1) / 2) * width
        ax.bar(x + offset, table[column], width, color=color, edgecolor="white", linewidth=1,
               label=NAMES.get(column, column))
    ax.set_xticks(x, [NAMES.get(label, label) for label in table.index])
    ax.grid(axis="x", visible=False)
    _percent_axis(ax)


def plot_appearance(by_identity: pd.DataFrame, summary: pd.DataFrame) -> None:
    """Stress Test 2: the two galleries compared.

    Left: share of named faces recognised, per person. Right: overall,
    recognised vs. closest reference correct (ignoring the threshold) vs.
    extras that were wrongly given a name.
    """
    rows = by_identity[by_identity["experiment"] == "appearance"]
    overall = summary[summary["experiment"] == "appearance"].assign(identity="All")
    per_person = (pd.concat([rows, overall])
                  .pivot(index="identity", columns="mitigation", values="recognised")
                  .reindex([*config.IDENTITIES, "All"]))
    metrics = (overall.set_index("mitigation")[["recognised", "closest_correct", "extras_named"]].T)

    fig, (left, right) = plt.subplots(1, 2, figsize=(TWO_COLUMNS, 2.4), gridspec_kw={"width_ratios": [5, 3]})
    _grouped_bars(left, per_person)
    left.set_title("Named faces recognised, per person", color=INK)
    _grouped_bars(right, metrics)
    right.set_title("All stills", color=INK)
    _legend_below(fig, left, ncol=2)
    save_figure(fig, "stress_test_2_appearance", bottom=0.24)


def plot_resolution(summary: pd.DataFrame) -> None:
    """Stress Test 1: recognised and missed faces against image scale, per upscaling method.

    Two panels, to separate recognition errors from faces the detector no
    longer finds at all.
    """
    rows = summary[summary["experiment"] == "resolution"]
    fig, axes = plt.subplots(1, 2, figsize=(TWO_COLUMNS, 2.5))
    for ax, metric, title in zip(axes, ("recognised", "missed"),
                                 ("Named faces recognised", "Named faces not detected")):
        for method, color, marker in zip(config.UPSCALE_METHODS, SERIES_COLORS, SERIES_MARKERS):
            line = rows[rows["mitigation"] == method].sort_values("level")
            ax.plot(line["level"], line[metric], marker=marker, color=color, label=NAMES.get(method, method))
        ax.set_xscale("log", base=2)
        ax.set_xticks(config.IMAGE_SCALES, [f"1/{round(1 / scale)}" if scale < 1 else "1"
                                            for scale in config.IMAGE_SCALES])
        ax.minorticks_off()
        ax.invert_xaxis()  # from the original still on the left to the smallest on the right
        ax.set_xlabel("Image scale (1 = original still)")
        ax.set_title(title, color=INK)
        _percent_axis(ax)
    _legend_below(fig, axes[0], ncol=3)
    save_figure(fig, "stress_test_1_resolution", bottom=0.27)


def plot_lighting(summary: pd.DataFrame) -> None:
    """Stress Test 3: recognised faces against lighting severity, without and with CLAHE."""
    rows = summary[summary["experiment"] == "lighting"]
    fig, axes = plt.subplots(1, len(config.LIGHTING_TYPES), figsize=(TWO_COLUMNS, 2.5), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, lighting in zip(axes, config.LIGHTING_TYPES):
        for mitigation, color, marker in zip(("none", "clahe"), SERIES_COLORS, SERIES_MARKERS):
            line = rows[(rows["variant"] == lighting) & (rows["mitigation"] == mitigation)].sort_values("level")
            ax.plot(line["level"], line["recognised"], marker=marker, color=color, label=NAMES[mitigation])
        ax.set_title(NAMES.get(lighting, lighting), color=INK)
        ax.set_xlabel("Severity (0 = original still)")
        ax.set_xticks(config.LIGHTING_SEVERITIES)
        _percent_axis(ax)
    axes[0].set_ylabel("Named faces recognised")
    _legend_below(fig, axes[0], ncol=2)
    save_figure(fig, "stress_test_3_lighting", bottom=0.27)


def plot_lighting_brightness(summary: pd.DataFrame) -> None:
    """Stress Test 3: recognised faces against how dark the stills really were.

    At the same severity the red alarm light is darker than "dark" (pure red
    light is dimmer). Plotting against the measured brightness lets the two
    be compared at equal brightness, so the effect of losing colour can be
    told apart from the effect of less light.
    """
    rows = summary[(summary["experiment"] == "lighting") & (summary["mitigation"] == "none")]
    fig, ax = plt.subplots(figsize=(ONE_COLUMN, 2.5))
    for lighting, color, marker in zip(config.LIGHTING_TYPES, SERIES_COLORS, SERIES_MARKERS):
        line = rows[rows["variant"] == lighting].sort_values("frame_brightness")
        ax.plot(line["frame_brightness"], line["recognised"], marker=marker, color=color,
                label=NAMES.get(lighting, lighting))
    ax.set_xlabel("Mean brightness of the stills (0-255)")
    ax.set_ylabel("Named faces recognised")
    _percent_axis(ax)
    ax.legend(loc="upper left", fontsize=7)
    save_figure(fig, "lighting_brightness")


def plot_distances(per_face: pd.DataFrame) -> None:
    """Distance to the closest reference on the original stills, per gallery.

    Shows why the threshold matters: with actor photos only, the faces of the
    four are mostly further away than the threshold; with film references,
    the extras come closer than the threshold.
    """
    rows = per_face[(per_face["experiment"] == "appearance") & per_face["detected"]]
    bins = np.arange(0, 1.65, 0.05)
    fig, axes = plt.subplots(1, 2, figsize=(TWO_COLUMNS, 2.4), sharey=True)
    for ax, gallery in zip(axes, ("personal_only", "personal_plus_in_character")):
        subset = rows[rows["mitigation"] == gallery]
        named = subset[subset["true_label"].isin(config.IDENTITIES)]["distance"]
        extras = subset[subset["true_label"] == config.OTHER_LABEL]["distance"]
        ax.hist(named, bins=bins, color=SERIES_COLORS[0], alpha=0.75, label=f"Faces of the four (n={len(named)})")
        ax.hist(extras, bins=bins, color=SERIES_COLORS[1], alpha=0.75, label=f"Extras (n={len(extras)})")
        ax.axvline(config.DISTANCE_THRESHOLD, color=INK_SECONDARY, linewidth=1, linestyle="--")
        ax.annotate(f"threshold {config.DISTANCE_THRESHOLD:.2f}", xy=(config.DISTANCE_THRESHOLD, 1),
                    xycoords=("data", "axes fraction"), xytext=(3, -10), textcoords="offset points",
                    color=INK_SECONDARY, fontsize=7)
        ax.set_title(NAMES[gallery], color=INK)
        ax.set_xlabel("Distance to the closest reference")
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("Number of faces")
    _legend_below(fig, axes[0], ncol=2)
    save_figure(fig, "distances", bottom=0.25)


def make_figures(summary: pd.DataFrame, by_identity: pd.DataFrame, per_face: pd.DataFrame) -> None:
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plot_appearance(by_identity, summary)
    plot_resolution(summary)
    plot_lighting(summary)
    plot_lighting_brightness(summary)
    plot_distances(per_face)


if __name__ == "__main__":
    make_figures(pd.read_csv(config.RESULTS_DIR / "summary.csv"),
                 pd.read_csv(config.RESULTS_DIR / "summary_by_identity.csv"),
                 pd.read_csv(config.RESULTS_DIR / "per_face.csv"))
    print(f"Figures written to {config.FIGURES_DIR.relative_to(config.REPO_ROOT)}/")
