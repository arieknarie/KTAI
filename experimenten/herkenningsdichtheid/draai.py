r"""Herkenningsdichtheid: een convolutiefilter over de herkenningen op de tijdlijn.

Per persoon en per beeld is het signaal 1 als FaceNet de naam van die persoon op het juiste gezicht zet, anders 0. Een tweede signaal is 1 als de naam
op een verkeerde plek staat. Een convolutie met een blokvormig venster geeft de gemiddelde herkenning per tijdseenheid: de dichtheid. Een dichtheid van
0,8 betekent: in 80% van de beelden in het venster staat de naam op het juiste gezicht. Het venster is 10, 15 of 20 beelden (ongeveer een halve tot een hele seconde).

Uitvoer in resultaten/<set>/ (met --model tuned in resultaten_tuned/<set>/): dichtheid_venster_<n>.csv (per beeld de dichtheid van elke persoon) en dichtheid_venster_<n>.png (per persoon een groene strook
voor de juiste naam en een rode strook voor een naam op een verkeerde plek, met de ground truth als zwarte lijn eronder). Ook dichtheid_samenvatting.csv.

Gebruik (vanuit de map experimenten, na basis/draai_alles.py; voor --model tuned na tuned/draai_alles.py):
    Mac:     .venv/bin/python herkenningsdichtheid/draai.py
             .venv/bin/python herkenningsdichtheid/draai.py --model tuned
    Windows: .venv\Scripts\python herkenningsdichtheid\draai.py
             .venv\Scripts\python herkenningsdichtheid\draai.py --model tuned
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
from gedeeld.getuned import OUTPUT, model_choice, results_of
from gedeeld.meten import method_2_counts, right_and_wrong
from gedeeld.paden import EXAMPLE_SETS, FRAMES, GROUND_TRUTH, NAMES

HERE = Path(__file__).resolve().parent
WINDOWS = [10, 15, 20]
SETS = ["fotos", "fotos_en_kostuum"]


def density(signal: np.ndarray, window: int) -> np.ndarray:
    """De convolutie met een blokvormig venster, gedeeld door het aantal beelden dat in het venster valt."""
    weights = np.ones(window)
    return np.convolve(signal, weights, "same") / np.convolve(np.ones(len(signal)), weights, "same")


def main() -> None:
    model = model_choice()
    output = HERE / OUTPUT[model]
    label = "getuned, " if model == "tuned" else ""
    frames = pd.read_csv(FRAMES)
    parts = fragments(frames).set_index("video")
    frames["fragment"] = frames["video"].map(parts["fragment"])
    frames["tijd_s"] = (frames["time_s"] + frames["video"].map(parts["offset"])).round(3)
    frames = frames.sort_values(["fragment", "tijd_s"], kind="stable").reset_index(drop=True)
    groups = sorted(frames["fragment"].unique(), key=lambda g: int(g.split()[-1]))
    truth = pd.read_csv(GROUND_TRUTH)
    summary = []
    for example_set in SETS:
        out = output / example_set
        out.mkdir(parents=True, exist_ok=True)
        found = pd.read_csv(results_of(model, example_set) / "voorspellingen.csv")
        good, wrong = right_and_wrong(found, method_2_counts(found, truth)[2])
        ai = {p: set(map(tuple, good.loc[good["persoon"] == p, ["bestand", "beeld"]].to_numpy())) for p in NAMES}
        false = {p: set(map(tuple, wrong.loc[wrong["persoon"] == p, ["bestand", "beeld"]].to_numpy())) for p in NAMES}
        gt = {p: set(map(tuple, truth.loc[truth["persoon"] == p, ["bestand", "beeld"]].to_numpy())) for p in NAMES}
        keys = list(zip(frames["video"], frames["frame"]))
        for window in WINDOWS:
            table = frames[["fragment", "video", "frame", "tijd_s"]].rename(columns={"video": "bestand", "frame": "beeld"}).copy()
            truth_density = {}
            for person in NAMES:
                values, misplaced, reference = np.zeros(len(frames)), np.zeros(len(frames)), np.zeros(len(frames))
                for group in groups:
                    index = np.flatnonzero((frames["fragment"] == group).to_numpy())
                    values[index] = density(np.array([keys[i] in ai[person] for i in index], dtype=float), window)
                    misplaced[index] = density(np.array([keys[i] in false[person] for i in index], dtype=float), window)
                    reference[index] = density(np.array([keys[i] in gt[person] for i in index], dtype=float), window)
                table[person] = values.round(3)
                table[f"{person} (verkeerde plek)"] = misplaced.round(3)
                truth_density[person] = reference
                summary.append({"voorbeelden": EXAMPLE_SETS[example_set].removeprefix("voorbeelden: "), "venster": window, "persoon": person,
                                "gemiddelde_dichtheid_juiste_naam": round(float(values.mean()), 3), "gemiddelde_dichtheid_verkeerde_plek": round(float(misplaced.mean()), 3),
                                "gemiddelde_dichtheid_ground_truth": round(float(reference.mean()), 3)})
            table.to_csv(out / f"dichtheid_venster_{window}.csv", index=False, lineterminator="\n")
            fig, axes = plt.subplots(len(groups), 1, figsize=(12, 1.75 * len(groups) + 0.9), squeeze=False, facecolor="white", gridspec_kw={"hspace": 0.55})
            for ax, group in zip(axes[:, 0], groups):
                mask = (frames["fragment"] == group).to_numpy()
                t = frames.loc[mask, "tijd_s"].to_numpy()
                strip = np.zeros((2 * len(NAMES), mask.sum(), 4))
                for k, person in enumerate(NAMES):
                    strip[2 * k] = plt.cm.Greens(table.loc[mask, person].to_numpy())
                    strip[2 * k + 1] = plt.cm.Reds(table.loc[mask, f"{person} (verkeerde plek)"].to_numpy())
                ax.imshow(strip, aspect="auto", extent=(t[0], t[-1], 2 * len(NAMES), 0), interpolation="nearest")
                for k, person in enumerate(NAMES):                # de zwarte lijn: wanneer de persoon volgens de ground truth in beeld is
                    present = truth_density[person][mask] > 0.5
                    ax.fill_between(t, 2 * k + 1.72, 2 * k + 2, where=present, color="#111111", linewidth=0, step="mid")
                ax.set_yticks([2 * k + 1 for k in range(len(NAMES))], NAMES, fontsize=8)
                ax.set_title(group, fontsize=9.5, loc="left", fontweight="bold", color="#0b0b0b")
                ax.tick_params(length=0, labelsize=8, colors="#52514e")
                for spine in ax.spines.values():
                    spine.set_visible(False)
            axes[-1, 0].set_xlabel("tijd in het filmpje (seconden)", fontsize=9, color="#52514e")
            fig.suptitle(f"Herkenningsdichtheid, venster {window} beelden ({label}{EXAMPLE_SETS[example_set]})\ngroen: de juiste naam op het juiste gezicht, rood: de naam op een verkeerde plek, zwart: de persoon is echt in beeld; hoe donkerder, hoe vaker",
                         x=0.01, y=0.945, ha="left", fontsize=10.5, color="#0b0b0b")
            fig.savefig(out / f"dichtheid_venster_{window}.png", dpi=125, bbox_inches="tight")
            plt.close(fig)
    summary = pd.DataFrame(summary)
    summary.to_csv(output / "dichtheid_samenvatting.csv", index=False, lineterminator="\n")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
