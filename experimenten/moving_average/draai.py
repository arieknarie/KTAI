r"""Moving average filter op de detectie, met een ondergrens en een bovengrens: onder 0,2 geen detectie, boven 0,7 wel, daartussen blijft het
zoals het was (hysterese).

Het filter is op twee plekken geprobeerd, omdat "detectie" twee dingen kan betekenen:
A. op de score van de detector, per track. Het signaal is de score van het kader in elk beeld van de track (0 als er even geen kader is).
   Kaders in beelden waar het filter "uit" staat, tellen niet meer mee.
B. op de herkenning, per persoon. Het signaal is 1 als FaceNet die persoon in dat beeld ziet, en anders 0. Het filter zegt per beeld of de
   persoon in beeld is. Het venster loopt nooit over een beeldwissel heen.
Het gemiddelde is steeds gecentreerd (evenveel beelden ervoor als erna), met verschillende vensters.

Variant A meet met beide methodes, variant B alleen met methode 1 (per beeld), want variant B levert geen kaders op.
Uitvoer in resultaten/<set>/: filter_A_detector.csv, filter_B_herkenning.csv, filter_vensters.png en filter_B_tijdlijn.png; in resultaten/ uitleg_filter.png.

Gebruik (vanuit de map experimenten, na basis/draai_alles.py):
    Mac:     .venv/bin/python moving_average/draai.py
    Windows: .venv\Scripts\python moving_average\draai.py
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.facenet import load_detections
from gedeeld.meten import COLUMNS, method_1_table, method_2_counts, method_2_table, presence, rates, timeline
from gedeeld.paden import EXAMPLE_SETS, EXPERIMENTEN, FRAMES, GROUND_TRUTH, NAMES

HERE = Path(__file__).resolve().parent
LOW, HIGH = 0.2, 0.7
WINDOWS = [5, 9, 15, 25, 41]
SHOWN = 15                                                # dit venster staat in de tijdlijn
SETS = ["fotos", "fotos_en_kostuum"]


def smooth(signal: np.ndarray, window: int) -> np.ndarray:
    """Het gecentreerde lopende gemiddelde. Aan de randen tellen alleen de beelden die er zijn."""
    weights = np.ones(window)
    return np.convolve(signal, weights, "same") / np.convolve(np.ones(len(signal)), weights, "same")


def hysteresis(values: np.ndarray) -> np.ndarray:
    """Onder LOW uit, boven HIGH aan, daartussen blijft het zoals het was. Het filter begint uit."""
    state, result = False, np.zeros(len(values), dtype=bool)
    for i, value in enumerate(values):
        if value > HIGH:
            state = True
        elif value < LOW:
            state = False
        result[i] = state
    return result


def variant_a(detections: pd.DataFrame, window: int) -> np.ndarray:
    """Welke kaders overblijven als het filter op de score van de detector per track werkt."""
    keep = np.zeros(len(detections), dtype=bool)
    for _, g in detections.groupby(["video", "track"], sort=False):
        first, last = int(g["frame"].min()), int(g["frame"].max())
        signal = np.zeros(last - first + 1)
        signal[g["frame"].to_numpy() - first] = g["score"].to_numpy()
        state = hysteresis(smooth(signal, window))
        keep[g.index.to_numpy()] = state[g["frame"].to_numpy() - first]
    return keep


def variant_b(found: pd.DataFrame, window: int) -> pd.DataFrame:
    """Per persoon in welke beelden die persoon volgens het filter te zien is. Per shot (tussen twee beeldwissels) apart."""
    frames = pd.read_csv(FRAMES)
    parts = found[["bestand", "fragment"]].drop_duplicates().set_index("bestand")["fragment"]
    seen = presence(found)
    result = []
    frames = frames[frames["video"].isin(parts.index)].copy()
    frames["fragment"] = frames["video"].map(parts)
    frames["shot"] = frames.groupby("fragment")["cut"].cumsum()
    shifts = {}
    for video, g in found.groupby("bestand"):
        row = g.iloc[0]
        shifts[video] = row.tijd_s - float(frames.loc[(frames["video"] == video) & (frames["frame"] == row.beeld), "time_s"].iloc[0])
    for person in NAMES:
        marks = set(map(tuple, seen.loc[seen["persoon"] == person, ["bestand", "beeld"]].to_numpy()))
        for (group, shot), g in frames.groupby(["fragment", "shot"], sort=False):
            signal = np.array([(v, f) in marks for v, f in zip(g["video"], g["frame"])], dtype=float)
            state = hysteresis(smooth(signal, window))
            for v, f, t, on in zip(g["video"], g["frame"], g["time_s"], state):
                if on:
                    result.append((group, v, int(f), round(float(t) + shifts[v], 3), person))
    return pd.DataFrame(result, columns=COLUMNS + ["persoon"])


def main() -> None:
    truth = pd.read_csv(GROUND_TRUTH)
    detections = load_detections()
    names = {"fotos": EXAMPLE_SETS["fotos"], "fotos_en_kostuum": EXAMPLE_SETS["fotos_en_kostuum"]}
    for example_set in SETS:
        out = HERE / "resultaten" / example_set
        out.mkdir(parents=True, exist_ok=True)
        found = pd.read_csv(EXPERIMENTEN / "basis" / "resultaten" / example_set / "voorspellingen.csv")
        base_two = method_2_table(method_2_counts(found, truth)[0]).set_index("acteur").loc["samen"]
        base_one = method_1_table(truth[COLUMNS + ["persoon"]], presence(found)).set_index("acteur").loc["samen"]

        rows_a = [{"venster": 0, "kaders_over": len(found), "methode_1_f1": base_one["f1"], "methode_2_precisie": base_two["precisie"], "methode_2_recall": base_two["recall"], "methode_2_f1": base_two["f1"]}]
        for window in WINDOWS:
            kept = found[variant_a(detections, window)]
            two = method_2_table(method_2_counts(kept, truth)[0]).set_index("acteur").loc["samen"]
            one = method_1_table(truth[COLUMNS + ["persoon"]], presence(kept)).set_index("acteur").loc["samen"]
            rows_a.append({"venster": window, "kaders_over": len(kept), "methode_1_f1": one["f1"], "methode_2_precisie": two["precisie"], "methode_2_recall": two["recall"], "methode_2_f1": two["f1"]})
        rows_a = pd.DataFrame(rows_a)
        rows_a.to_csv(out / "filter_A_detector.csv", index=False, lineterminator="\n")

        rows_b = [{"venster": 0, "beelden_in_beeld": int(base_one["ai_voorspelling"]), "precisie": base_one["precisie"], "recall": base_one["recall"], "f1": base_one["f1"]}]
        for window in WINDOWS:
            ai = variant_b(found, window)
            one = method_1_table(truth[COLUMNS + ["persoon"]], ai).set_index("acteur").loc["samen"]
            rows_b.append({"venster": window, "beelden_in_beeld": int(one["ai_voorspelling"]), "precisie": one["precisie"], "recall": one["recall"], "f1": one["f1"]})
            if window == SHOWN:
                timeline(truth[COLUMNS + ["persoon"]], ai, out / "filter_B_tijdlijn.png", f"filter op de herkenning, venster {window} beelden, {names[example_set]}", "AI na het filter")
        rows_b = pd.DataFrame(rows_b)
        rows_b.to_csv(out / "filter_B_herkenning.csv", index=False, lineterminator="\n")

        fig, ax = plt.subplots(figsize=(7.6, 3.8), facecolor="white")
        for table, column, colour, label in ((rows_b, "f1", "#2a78d6", "B: op de herkenning (methode 1)"), (rows_a, "methode_1_f1", "#eb6834", "A: op de detectorscore (methode 1)"), (rows_a, "methode_2_f1", "#1baf7a", "A: op de detectorscore (methode 2)")):
            ax.plot(range(len(table)), table[column], marker="o", markersize=5, linewidth=2, color=colour, label=label)
        ax.set_xticks(range(len(rows_b)), ["geen filter"] + [str(w) for w in WINDOWS])
        ax.set_xlabel("venster van het gemiddelde (beelden)", fontsize=9.5, color="#52514e")
        ax.set_ylabel("F1", fontsize=9.5, color="#52514e")
        ax.set_ylim(0, 1)
        ax.tick_params(length=0, labelsize=9, colors="#52514e")
        ax.grid(axis="y", color="#e4e3de", linewidth=0.8)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.legend(frameon=False, fontsize=8.5)
        ax.set_title(f"Effect van het filter ({names[example_set]})", loc="left", fontsize=11, fontweight="bold", color="#0b0b0b")
        fig.tight_layout()
        fig.savefig(out / "filter_vensters.png", dpi=140)
        plt.close(fig)
        print(example_set); print(rows_a.to_string(index=False)); print(rows_b.to_string(index=False))

    # een plaatje dat laat zien wat het filter doet, op een echt stukje herkenning
    found = pd.read_csv(EXPERIMENTEN / "basis" / "resultaten" / "fotos_en_kostuum" / "voorspellingen.csv")
    seen = presence(found)
    part = seen[(seen["fragment"] == "Video 1") & (seen["persoon"] == "Der Alte")]
    frames = pd.read_csv(FRAMES)
    g = frames[frames["video"].str.startswith("Das Boot 1 ")]
    marks = set(part["beeld"])
    signal = np.array([f in marks for f in g["frame"]], dtype=float)
    average = smooth(signal, SHOWN)
    state = hysteresis(average)
    fig, ax = plt.subplots(figsize=(10, 3.4), facecolor="white")
    t = g["time_s"].to_numpy()
    ax.fill_between(t, 0, signal, step="mid", color="#c9c8c2", linewidth=0, label="ruwe herkenning: FaceNet ziet de persoon (ja of nee)")
    ax.plot(t, average, color="#2a78d6", linewidth=2, label=f"lopend gemiddelde over {SHOWN} beelden")
    ax.fill_between(t, 1.04, 1.1, where=state, color="#eb6834", linewidth=0, step="mid", label="uitkomst van het filter: in beeld")
    ax.axhline(HIGH, color="#52514e", linewidth=1, linestyle="--")
    ax.axhline(LOW, color="#52514e", linewidth=1, linestyle=":")
    for y, text in ((HIGH, "bovengrens 0,7"), (LOW, "ondergrens 0,2")):
        ax.text(t[0] + 0.4, y + 0.02, text, ha="left", fontsize=8.5, color="#0b0b0b", bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5})
    ax.set_xlim(t[0], t[-1])
    ax.set_ylim(0, 1.14)
    ax.set_xlabel("tijd in Video 1 (seconden)", fontsize=9.5, color="#52514e")
    ax.tick_params(length=0, labelsize=9, colors="#52514e")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(frameon=False, fontsize=8.5, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3)
    fig.tight_layout()
    fig.savefig(HERE / "resultaten" / "uitleg_filter.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
