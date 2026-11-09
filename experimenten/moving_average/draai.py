r"""Moving average filter op de detectie, met een ondergrens en een bovengrens: onder 0,2 geen detectie, boven 0,7 wel, daartussen blijft het
zoals het was (hysterese).

Het filter is op twee plekken geprobeerd, omdat "detectie" twee dingen kan betekenen:
A. op de score van de detector, per track. Het signaal is de score van het kader in elk beeld van de track (0 als er even geen kader is).
   Kaders in beelden waar het filter "uit" staat, tellen niet meer mee.
B. op de herkenning, per persoon. Het signaal is 1 als FaceNet die persoon in dat beeld noemt, en anders 0. Een kader houdt zijn naam alleen in de
   beelden waar het filter van die persoon aan staat. Het venster loopt nooit over een beeldwissel heen.
Het gemiddelde is steeds gecentreerd (evenveel beelden ervoor als erna), met verschillende vensters. Gemeten wordt per gezicht (methode 2).

Uitvoer in resultaten/<set>/ (met --model tuned in resultaten_tuned/<set>/): filter_A_detector.csv, filter_B_herkenning.csv, filter_vensters.png en
filter_B_tijdlijn.png; in resultaten/ uitleg_filter.png.

Gebruik (vanuit de map experimenten, na basis/draai_alles.py; voor --model tuned na tuned/draai_alles.py):
    Mac:     .venv/bin/python moving_average/draai.py
             .venv/bin/python moving_average/draai.py --model tuned
    Windows: .venv\Scripts\python moving_average\draai.py
             .venv\Scripts\python moving_average\draai.py --model tuned
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
from gedeeld.getuned import OUTPUT, model_choice, results_of
from gedeeld.meten import face_timeline, method_2_counts, method_2_table, presence
from gedeeld.paden import EXAMPLE_SETS, EXPERIMENTEN, FRAMES, GROUND_TRUTH, NAMES, OTHER

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
    """De voorspellingen na het filter op de herkenning. Per persoon en per shot (tussen twee beeldwissels) zegt het filter in welke beelden die persoon
    in beeld is. Een kader houdt zijn naam alleen in die beelden; anders wordt het "iemand anders"."""
    frames = pd.read_csv(FRAMES)
    parts = found[["bestand", "fragment"]].drop_duplicates().set_index("bestand")["fragment"]
    seen = presence(found)
    frames = frames[frames["video"].isin(parts.index)].copy()
    frames["fragment"] = frames["video"].map(parts)
    frames["shot"] = frames.groupby("fragment")["cut"].cumsum()
    on = set()
    for person in NAMES:
        marks = set(map(tuple, seen.loc[seen["persoon"] == person, ["bestand", "beeld"]].to_numpy()))
        for _, g in frames.groupby(["fragment", "shot"], sort=False):
            signal = np.array([(v, f) in marks for v, f in zip(g["video"], g["frame"])], dtype=float)
            on |= {(v, int(f), person) for v, f, state in zip(g["video"], g["frame"], hysteresis(smooth(signal, window))) if state}
    keep = np.array([name not in NAMES or (v, int(f), name) in on for v, f, name in zip(found["bestand"], found["beeld"], found["facenet"])])
    result = found.copy()
    result.loc[~keep, "facenet"] = OTHER
    return result


def scores(found: pd.DataFrame, truth: pd.DataFrame) -> dict:
    """De score per gezicht (methode 2)."""
    two = method_2_table(method_2_counts(found, truth)[0]).set_index("acteur").loc["samen"]
    return {"precisie": two["precisie"], "recall": two["recall"], "f1": two["f1"]}


def main() -> None:
    model = model_choice()
    truth = pd.read_csv(GROUND_TRUTH)
    detections = load_detections()
    prefix = "getuned, " if model == "tuned" else ""
    names = {key: prefix + EXAMPLE_SETS[key] for key in SETS}
    for example_set in SETS:
        out = HERE / OUTPUT[model] / example_set
        out.mkdir(parents=True, exist_ok=True)
        found = pd.read_csv(results_of(model, example_set) / "voorspellingen.csv")
        base = scores(found, truth)

        rows_a = [{"venster": 0, "kaders_over": len(found), **base}]
        for window in WINDOWS:
            kept = found[variant_a(detections, window)]
            rows_a.append({"venster": window, "kaders_over": len(kept), **scores(kept, truth)})
        rows_a = pd.DataFrame(rows_a)
        rows_a.to_csv(out / "filter_A_detector.csv", index=False, lineterminator="\n")

        rows_b = [{"venster": 0, "namen_over": int(found["facenet"].isin(NAMES).sum()), **base}]
        for window in WINDOWS:
            filtered = variant_b(found, window)
            rows_b.append({"venster": window, "namen_over": int(filtered["facenet"].isin(NAMES).sum()), **scores(filtered, truth)})
            if window == SHOWN:
                face_timeline(truth, filtered, method_2_counts(filtered, truth)[2], out / "filter_B_tijdlijn.png", f"filter op de herkenning, venster {window} beelden, {names[example_set]}")
        rows_b = pd.DataFrame(rows_b)
        rows_b.to_csv(out / "filter_B_herkenning.csv", index=False, lineterminator="\n")

        fig, ax = plt.subplots(figsize=(7.6, 3.8), facecolor="white")
        for table, colour, label in ((rows_a, "#eb6834", "A: op de score van de detector"), (rows_b, "#1baf7a", "B: op de herkenning")):
            ax.plot(range(len(table)), table["f1"], marker="o", markersize=5, linewidth=2, color=colour, label=label)
        ax.set_xticks(range(len(rows_b)), ["geen filter"] + [str(w) for w in WINDOWS])
        ax.set_xlabel("venster van het gemiddelde (beelden)", fontsize=9.5, color="#52514e")
        ax.set_ylabel("score (F1 per gezicht)", fontsize=9.5, color="#52514e")
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

    if model == "tuned":                                  # het uitlegplaatje hoort bij de standaarduitkomsten
        return

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
