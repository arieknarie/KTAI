"""Figures for the paper, made from the summary tables of run_stress_tests.py.

Each figure is saved as PDF (vector, for LaTeX) and PNG in results/figures/.
Sizes match the ICML two-column layout: 3.25 inch for one column,
6.75 inch for a figure that spans both columns.
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

# Colour-blind safe categorical colours, always used in this fixed order.
SERIES_COLORS = ("#2a78d6", "#eb6834", "#1baf7a")
INK, INK_SECONDARY, GRID = "#0b0b0b", "#52514e", "#e4e3df"

# Readable names for the values used in the result tables.
NAMES = {
    "personal_only": "Personal photos only",
    "personal_plus_in_character": "+ in-character references",
    "nearest": "Nearest neighbour (no interpolation)",
    "bicubic": "Bicubic interpolation",
    "lanczos": "Lanczos interpolation",
    "none": "Without CLAHE",
    "clahe": "With CLAHE",
    "dark": "Darkness",
    "red_alarm": "Red alarm light",
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


def save_figure(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    for extension in ("pdf", "png"):
        fig.savefig(config.FIGURES_DIR / f"{name}.{extension}", dpi=200)
    plt.close(fig)


def plot_appearance(by_identity: pd.DataFrame, summary: pd.DataFrame) -> None:
    """Stress Test 2: share of named faces recognised, per person and gallery."""
    rows = by_identity[by_identity["experiment"] == "appearance"]
    overall = summary[summary["experiment"] == "appearance"].assign(true_label="All")
    table = pd.concat([rows, overall]).pivot(index="true_label", columns="mitigation", values="recognised")
    table = table.reindex([*config.IDENTITIES, "All"])

    fig, ax = plt.subplots(figsize=(ONE_COLUMN, 2.3))
    x = np.arange(len(table.index))
    width = 0.38
    for offset, (gallery, color) in zip((-width / 2, width / 2), zip(table.columns, SERIES_COLORS)):
        ax.bar(x + offset, table[gallery], width, color=color, edgecolor="white", linewidth=1,
               label=NAMES.get(gallery, gallery))
    ax.set_xticks(x, table.index)
    ax.grid(axis="x", visible=False)
    _percent_axis(ax)
    ax.set_ylabel("Named faces recognised")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=7)
    save_figure(fig, "stress_test_2_appearance")


def plot_resolution(summary: pd.DataFrame) -> None:
    """Stress Test 1: recognised and missed faces against image scale, per upscaling method.

    Two panels, to separate recognition errors from faces the detector no
    longer finds at all.
    """
    rows = summary[summary["experiment"] == "resolution"]
    fig, axes = plt.subplots(1, 2, figsize=(TWO_COLUMNS, 2.3))
    for ax, metric, title in zip(axes, ("recognised", "missed"),
                                 ("Named faces recognised", "Named faces not detected")):
        for method, color in zip(config.UPSCALE_METHODS, SERIES_COLORS):
            line = rows[rows["mitigation"] == method].sort_values("level")
            ax.plot(line["level"], line[metric], marker="o", color=color, label=NAMES.get(method, method))
        ax.set_xscale("log", base=2)
        ax.set_xticks(config.IMAGE_SCALES, [f"1/{round(1 / scale)}" if scale < 1 else "1"
                                            for scale in config.IMAGE_SCALES])
        ax.minorticks_off()
        ax.invert_xaxis()  # from the original still on the left to the smallest on the right
        ax.set_xlabel("Image scale (1 = original still)")
        ax.set_title(title, color=INK)
        _percent_axis(ax)
    axes[0].legend(loc="lower left", fontsize=7)
    save_figure(fig, "stress_test_1_resolution")


def plot_lighting(summary: pd.DataFrame) -> None:
    """Stress Test 3: recognised faces against lighting severity, without and with CLAHE."""
    rows = summary[summary["experiment"] == "lighting"]
    fig, axes = plt.subplots(1, len(config.LIGHTING_TYPES), figsize=(TWO_COLUMNS, 2.3), sharey=True)
    for ax, lighting in zip(np.atleast_1d(axes), config.LIGHTING_TYPES):
        for mitigation, color in zip(("none", "clahe"), SERIES_COLORS):
            line = rows[(rows["variant"] == lighting) & (rows["mitigation"] == mitigation)].sort_values("level")
            ax.plot(line["level"], line["recognised"], marker="o", color=color, label=NAMES[mitigation])
        ax.set_title(NAMES.get(lighting, lighting), color=INK)
        ax.set_xlabel("Severity (0 = original still)")
        ax.set_xticks(config.LIGHTING_SEVERITIES)
        _percent_axis(ax)
    np.atleast_1d(axes)[0].set_ylabel("Named faces recognised")
    np.atleast_1d(axes)[0].legend(loc="lower left", fontsize=7)
    save_figure(fig, "stress_test_3_lighting")


def make_figures(summary: pd.DataFrame, by_identity: pd.DataFrame) -> None:
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plot_appearance(by_identity, summary)
    plot_resolution(summary)
    plot_lighting(summary)
