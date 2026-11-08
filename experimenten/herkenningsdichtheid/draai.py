r"""Herkenningsdichtheid: een convolutiefilter over de herkenningen op de tijdlijn.

Per persoon en per beeld is het signaal 1 als FaceNet die persoon in dat beeld ziet, anders 0. Een convolutie met een blokvormig venster geeft
de gemiddelde herkenning per tijdseenheid: de dichtheid. Een dichtheid van 0,8 betekent: in 80% van de beelden in het venster ziet FaceNet deze
persoon. Het venster is 10, 15 of 20 beelden (ongeveer een halve tot een hele seconde).

Uitvoer in resultaten/<set>/: dichtheid_venster_<n>.csv (per beeld de dichtheid van elke persoon) en dichtheid_venster_<n>.png (per persoon een
strook die donkerder is naarmate de dichtheid hoger is, met de ground truth als zwarte lijn eronder). In resultaten/ dichtheid_samenvatting.csv.

Gebruik (vanuit de map experimenten, na basis/draai_alles.py):
    Mac:     .venv/bin/python herkenningsdichtheid/draai.py
    Windows: .venv\Scripts\python herkenningsdichtheid\draai.py
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.film import fragments
from gedeeld.meten import presence
from gedeeld.paden import EXAMPLE_SETS, EXPERIMENTEN, FRAMES, GROUND_TRUTH, NAMES

HERE = Path(__file__).resolve().parent
WINDOWS = [10, 15, 20]
SETS = ["fotos", "fotos_en_kostuum"]


def density(signal: np.ndarray, window: int) -> np.ndarray:
    """De convolutie met een blokvormig venster, gedeeld door het aantal beelden dat in het venster valt."""
    weights = np.ones(window)
    return np.convolve(signal, weights, "same") / np.convolve(np.ones(len(signal)), weights, "same")


def main() -> None:
    frames = pd.read_csv(FRAMES)
    parts = fragments(frames).set_index("video")
    frames["fragment"] = frames["video"].map(parts["fragment"])
    frames["tijd_s"] = (frames["time_s"] + frames["video"].map(parts["offset"])).round(3)
    frames = frames.sort_values(["fragment", "tijd_s"], kind="stable").reset_index(drop=True)
    groups = sorted(frames["fragment"].unique(), key=lambda g: int(g.split()[-1]))
    truth = pd.read_csv(GROUND_TRUTH)
    summary = []
    for example_set in SETS:
        out = HERE / "resultaten" / example_set
        out.mkdir(parents=True, exist_ok=True)
        found = pd.read_csv(EXPERIMENTEN / "basis" / "resultaten" / example_set / "voorspellingen.csv")
        seen = presence(found)
        ai = {p: set(map(tuple, seen.loc[seen["persoon"] == p, ["bestand", "beeld"]].to_numpy())) for p in NAMES}
        gt = {p: set(map(tuple, truth.loc[truth["persoon"] == p, ["bestand", "beeld"]].to_numpy())) for p in NAMES}
        keys = list(zip(frames["video"], frames["frame"]))
        for window in WINDOWS:
            table = frames[["fragment", "video", "frame", "tijd_s"]].rename(columns={"video": "bestand", "frame": "beeld"}).copy()
            truth_density = {}
            for person in NAMES:
                values, reference = np.zeros(len(frames)), np.zeros(len(frames))
                for group in groups:
                    index = np.flatnonzero((frames["fragment"] == group).to_numpy())
                    values[index] = density(np.array([keys[i] in ai[person] for i in index], dtype=float), window)
                    reference[index] = density(np.array([keys[i] in gt[person] for i in index], dtype=float), window)
                table[person] = values.round(3)
                truth_density[person] = reference
                summary.append({"voorbeelden": EXAMPLE_SETS[example_set].removeprefix("voorbeelden: "), "venster": window, "persoon": person,
                                "gemiddelde_dichtheid_facenet": round(float(values.mean()), 3), "gemiddelde_dichtheid_ground_truth": round(float(reference.mean()), 3),
                                "gemiddeld_absoluut_verschil": round(float(np.abs(values - reference).mean()), 3)})
            table.to_csv(out / f"dichtheid_venster_{window}.csv", index=False, lineterminator="\n")
            fig, axes = plt.subplots(len(groups), 1, figsize=(12, 1.45 * len(groups) + 0.9), squeeze=False, facecolor="white", gridspec_kw={"hspace": 0.55})
            for ax, group in zip(axes[:, 0], groups):
                mask = (frames["fragment"] == group).to_numpy()
                t = frames.loc[mask, "tijd_s"].to_numpy()
                strip = np.array([table.loc[mask, person].to_numpy() for person in NAMES])
                image = ax.imshow(strip, aspect="auto", cmap="Blues", vmin=0, vmax=1, extent=(t[0], t[-1], len(NAMES) - 0.5, -0.5), interpolation="nearest")
                for y, person in enumerate(NAMES):                # de zwarte lijn: wanneer de persoon volgens de ground truth in beeld is
                    present = truth_density[person][mask] > 0.5
                    ax.fill_between(t, y + 0.38, y + 0.5, where=present, color="#111111", linewidth=0, step="mid")
                ax.set_yticks(range(len(NAMES)), NAMES, fontsize=8)
                ax.set_title(group, fontsize=9.5, loc="left", fontweight="bold", color="#0b0b0b")
                ax.tick_params(length=0, labelsize=8, colors="#52514e")
                for spine in ax.spines.values():
                    spine.set_visible(False)
            axes[-1, 0].set_xlabel("tijd in het filmpje (seconden); de zwarte lijn onder een strook is de ground truth", fontsize=9, color="#52514e")
            fig.colorbar(image, ax=axes[:, 0], fraction=0.015, pad=0.01, label="dichtheid: aandeel herkende beelden in het venster")
            fig.suptitle(f"Herkenningsdichtheid, venster {window} beelden ({EXAMPLE_SETS[example_set]})", x=0.01, ha="left", fontsize=11, fontweight="bold", color="#0b0b0b")
            fig.savefig(out / f"dichtheid_venster_{window}.png", dpi=125, bbox_inches="tight")
            plt.close(fig)
    summary = pd.DataFrame(summary)
    summary.to_csv(HERE / "resultaten" / "dichtheid_samenvatting.csv", index=False, lineterminator="\n")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
