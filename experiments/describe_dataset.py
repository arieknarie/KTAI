"""Describe the face data set: how many faces, how small and how dark.

Gives the numbers for the "Datasets" section of the paper and shows how the
real film material compares with the actors' personal photos.

Writes results/dataset_summary.csv and results/figures/dataset_faces.(pdf|png).

Usage:
    python describe_dataset.py
"""

from __future__ import annotations

import pandas as pd

import config
import labels
import plots

SMALL_FACE_PX = 48  # faces narrower than this count as "small"
DARK_FACE = 60      # faces with a mean grey value below this count as "dark"
SOURCES = ("personal", "inCharacter", "movie")
SOURCE_NAMES = {"personal": "Actor photos", "inCharacter": "Film stills", "movie": "Movie clips"}


def main() -> None:
    faces = labels.load_labels()
    faces["face_px"] = faces[["w", "h"]].max(axis=1)
    faces["labelled"] = faces["label"].isin(config.IDENTITIES)

    summary = (
        faces.groupby("source")
        .agg(faces=("face_id", "size"),
             labelled_faces=("labelled", "sum"),
             median_face_px=("face_px", "median"),
             share_small=("face_px", lambda px: (px < SMALL_FACE_PX).mean()),
             median_brightness=("brightness", "median"),
             share_dark=("brightness", lambda value: (value < DARK_FACE).mean()))
        .reindex([source for source in SOURCES if source in set(faces["source"])])
        .round(3)
    )
    per_identity = (faces[faces["labelled"]].groupby(["source", "label"]).size()
                    .unstack(fill_value=0))

    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(config.RESULTS_DIR / "dataset_summary.csv")
    per_identity.to_csv(config.RESULTS_DIR / "dataset_per_identity.csv")
    print(summary.to_string(), "\n")
    print("Labelled faces per identity:\n" + per_identity.to_string())

    plot_distributions(faces)


def plot_distributions(faces: pd.DataFrame) -> None:
    """Cumulative distributions of face size and brightness per source."""
    fig, (size_ax, light_ax) = plots.plt.subplots(1, 2, figsize=(plots.TWO_COLUMNS, 2.5))
    for source, color in zip(SOURCES, plots.SERIES_COLORS):
        subset = faces[faces["source"] == source]
        if subset.empty:
            continue
        for ax, column in ((size_ax, "face_px"), (light_ax, "brightness")):
            values = subset[column].sort_values().to_numpy()
            share = (pd.RangeIndex(1, len(values) + 1) / len(values)).to_numpy()
            ax.step(values, share, where="post", color=color,
                    label=f"{SOURCE_NAMES[source]} (n={len(values)})")

    size_ax.set_xscale("log", base=2)
    size_ax.set_xticks([16, 32, 64, 128, 256, 512], ["16", "32", "64", "128", "256", "512"])
    size_ax.minorticks_off()
    size_ax.set_xlabel("Face width in pixels (log scale)")
    light_ax.set_xlabel("Mean brightness of the face (0-255)")
    for ax in (size_ax, light_ax):
        ax.set_ylim(0, 1.02)
        ax.yaxis.set_major_formatter(plots.PercentFormatter(1.0))
    size_ax.set_ylabel("Share of faces (cumulative)")
    handles, labels_ = size_ax.get_legend_handles_labels()
    fig.legend(handles, labels_, loc="lower center", ncol=3, fontsize=7)
    plots.save_figure(fig, "dataset_faces", bottom=0.27)


if __name__ == "__main__":
    main()
