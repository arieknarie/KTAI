r"""Stap 2: afstellen. Alle combinaties van instellingen worden geprobeerd; de beste volgens methode 2 (per gezicht) wint.

Invoer:  de vectoren uit stap 1 en de ground truth van het labelen.
Uitvoer in resultaten/<set>/:
    alle_instellingen.csv        elke combinatie met de beste drempel, en de F1, precisie en recall daarbij
    beste_instelling.json        de winnende combinatie
    eerlijke_schatting.csv       de score als de instelling gekozen wordt op de andere filmpjes (zie hieronder)
    beste_per_filmpje.csv        per filmpje de beste instelling voor alleen dat filmpje, en de score van de algemeen beste instelling
    afstellen_per_instelling.png de beste F1 per keuze, per instelling

Elke instelling is met 200 drempels geprobeerd. De winnaar is gekozen op dezelfde beelden als waarop gemeten wordt; de score
is daardoor te gunstig. Daarom staat er ook een eerlijke schatting bij: voor elk filmpje wordt de beste combinatie en drempel
gekozen op de andere zeven filmpjes, en daarna gemeten op dat ene filmpje (leave-one-fragment-out).

Gebruik (vanuit de map experimenten, na stap 1):
    Mac:     .venv/bin/python tuned/stap_2_afstellen.py --voorbeelden fotos
    Windows: .venv\Scripts\python tuned\stap_2_afstellen.py --voorbeelden fotos
"""

import argparse
import itertools
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.facenet import load_detections, vector_path
from gedeeld.film import fragments
from gedeeld.herkennen import assigned, by_track, person_distances
from gedeeld.meten import hit_matrix, rates
from gedeeld.paden import EXAMPLE_SETS, FRAMES, GROUND_TRUTH
from gedeeld.voorbeelden import rows
from instellingen import ASSIGN, DECIDE, KEYS, LIGHT, MARGINS, METRICS, MODELS, PER_PERSON, SETS, THRESHOLDS, example_path, folder


SETTINGS = {"model": "Model", "marge": "Extra ruimte", "lichter": "Lichter maken", "afstand": "Soort afstand", "per_persoon": "Vergelijken met",
            "toewijzen": "Naam in een beeld", "beslissen": "Beslissen"}
CHOICES = {"euclidean_l2": "genormaliseerd", "cosine": "cosinus", "euclidean": "gewoon", "dichtstbij": "beste foto", "gemiddelde": "gemiddelde",
           "uniek": "elk één keer", "los": "mag vaker", "track": "per track", "kader": "per kader"}


def sweep(person, distance, hit, face_part, box_part, parts, thresholds):
    """Per filmpje en per drempel hoeveel gezichten goed zijn en hoeveel kaders fout benoemd zijn (methode 2)."""
    named = person >= 0
    face = np.full(len(person), -1)
    face[named] = hit[np.flatnonzero(named), person[named]]
    right = face >= 0
    best = np.full(len(face_part), np.inf)
    np.minimum.at(best, face[right], distance[right])
    good, wrong = np.zeros((parts, len(thresholds)), dtype=int), np.zeros((parts, len(thresholds)), dtype=int)
    missed = named & ~right
    for part in range(parts):
        good[part] = np.searchsorted(np.sort(best[face_part == part]), thresholds)
        wrong[part] = np.searchsorted(np.sort(distance[missed & (box_part == part)]), thresholds)
    return good, wrong


def f1(good, wrong, faces):
    return 2 * good / np.maximum(1, 2 * good + wrong + (faces - good))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--voorbeelden", choices=SETS, default="fotos", help="welke set voorbeeldfoto's")
    args = parser.parse_args()
    out, title = folder(args.voorbeelden), f"tuned, {EXAMPLE_SETS[args.voorbeelden]}"
    table = rows(args.voorbeelden)
    names = table["persoon"].to_numpy()
    detections = load_detections()
    truth = pd.read_csv(GROUND_TRUTH)
    hit = hit_matrix(detections, truth)
    frame_id = detections.groupby(["video", "frame"], sort=False).ngroup().to_numpy()
    track_id = detections.groupby(["video", "track"], sort=False).ngroup().to_numpy()
    parts_table = fragments(pd.read_csv(FRAMES)).set_index("video")
    groups = sorted(parts_table["fragment"].unique(), key=lambda g: int(g.split()[-1]))
    box_part = detections["video"].map(parts_table["fragment"]).map(groups.index).to_numpy()
    face_part = truth["fragment"].map(groups.index).to_numpy()
    faces = np.bincount(face_part, minlength=len(groups))

    results = []
    for model, margin, light in itertools.product(MODELS, MARGINS, LIGHT):
        boxes = np.load(vector_path(model, margin, light))
        refs = np.load(example_path(args.voorbeelden, model, margin, light))
        for metric, per_person in itertools.product(METRICS, PER_PERSON):
            d = person_distances(boxes, names, refs, metric, per_person)
            for decide in DECIDE:
                matrix = by_track(d, track_id) if decide == "track" else d
                for assign in ASSIGN:
                    person, distance = assigned(matrix, frame_id, assign)
                    finite = distance[np.isfinite(distance)]
                    thresholds = np.quantile(finite, np.linspace(0.005, 1, THRESHOLDS)) * 1.0001
                    good, wrong = sweep(person, distance, hit, face_part, box_part, len(groups), thresholds)
                    score = f1(good.sum(0), wrong.sum(0), faces.sum())
                    k = int(score.argmax())
                    results.append({"config": (model, margin, light, metric, per_person, assign, decide),
                                    "thresholds": thresholds, "good": good, "wrong": wrong, "best": k, "f1": float(score[k])})
        print(f"  {model}, marge {margin:.0%}, lichter {light}: beste F1 tot nu toe {max(r['f1'] for r in results):.3f}", flush=True)

    # de hele tabel, en de winnaar
    table_rows = []
    for r in results:
        k = r["best"]
        g, w = int(r["good"].sum(0)[k]), int(r["wrong"].sum(0)[k])
        precision, recall, score = rates(g, w, int(faces.sum()) - g)
        table_rows.append({**dict(zip(KEYS, r["config"])), "drempel": round(float(r["thresholds"][k]), 4), "goed": g, "fout_benoemd": w,
                           "gemist": int(faces.sum()) - g, "precisie": precision, "recall": recall, "f1": score, "f1_precies": r["f1"]})
    overview = pd.DataFrame(table_rows).sort_values("f1_precies", ascending=False, kind="stable")
    overview.drop(columns="f1_precies").to_csv(out / "alle_instellingen.csv", index=False, lineterminator="\n")
    top = max(results, key=lambda r: r["f1"])
    k = top["best"]
    best = {**dict(zip(KEYS, top["config"])), "drempel": float(top["thresholds"][k]), "f1": round(top["f1"], 3)}

    # de eerlijke schatting: kies op de andere filmpjes, meet op dit filmpje
    honest = []
    for part, group in enumerate(groups):
        others = [i for i in range(len(groups)) if i != part]
        chosen = max(results, key=lambda r: f1(r["good"][others].sum(0), r["wrong"][others].sum(0), faces[others].sum()).max())
        t = int(f1(chosen["good"][others].sum(0), chosen["wrong"][others].sum(0), faces[others].sum()).argmax())
        g, w = int(chosen["good"][part, t]), int(chosen["wrong"][part, t])
        precision, recall, score = rates(g, w, int(faces[part]) - g)
        honest.append({"filmpje": group, **dict(zip(KEYS, chosen["config"])), "drempel": round(float(chosen["thresholds"][t]), 4),
                       "gezichten": int(faces[part]), "goed": g, "fout_benoemd": w, "gemist": int(faces[part]) - g, "precisie": precision, "recall": recall, "f1": score})
    honest = pd.DataFrame(honest)
    honest.to_csv(out / "eerlijke_schatting.csv", index=False, lineterminator="\n")

    # per filmpje: de beste instelling voor alleen dat filmpje, naast de score van de algemeen beste instelling
    per_film = []
    for part, group in enumerate(groups):
        chosen = max(results, key=lambda r: f1(r["good"][part], r["wrong"][part], faces[part]).max())
        t = int(f1(chosen["good"][part], chosen["wrong"][part], faces[part]).argmax())
        g_own, w_own = int(chosen["good"][part, t]), int(chosen["wrong"][part, t])
        g_top, w_top = int(top["good"][part, k]), int(top["wrong"][part, k])
        per_film.append({"filmpje": group, **dict(zip(KEYS, chosen["config"])), "drempel": round(float(chosen["thresholds"][t]), 4),
                         "f1": rates(g_own, w_own, int(faces[part]) - g_own)[2], "f1_algemeen_beste": rates(g_top, w_top, int(faces[part]) - g_top)[2]})
    pd.DataFrame(per_film).to_csv(out / "beste_per_filmpje.csv", index=False, lineterminator="\n")
    g, w = int(honest["goed"].sum()), int(honest["fout_benoemd"].sum())
    best["f1_eerlijke_schatting"] = rates(g, w, int(faces.sum()) - g)[2]
    (out / "beste_instelling.json").write_text(json.dumps(best, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    # per instelling: de hoogste score die met elke keuze te halen is; de keuze van de winnaar staat in blauw
    fig, axes = plt.subplots(1, len(KEYS), figsize=(2.25 * len(KEYS), 3.5), sharey=True, facecolor="white")
    for ax, key in zip(axes, KEYS):
        values = overview.groupby(key, sort=False)["f1"].max()
        labels = [("ja" if v is True else "nee" if v is False else f"{v:.0%}" if isinstance(v, float) else CHOICES.get(str(v), str(v))) for v in values.index]
        ax.bar(labels, values.to_numpy(), width=0.6, color=["#eb6834"] + ["#c9c8c2"] * (len(values) - 1))
        for i, v in enumerate(values):
            ax.text(i, v + 0.012, f"{v:.3f}".replace(".", ","), ha="center", fontsize=8, color="#0b0b0b")
        ax.set_title(SETTINGS[key], fontsize=10, color="#0b0b0b", fontweight="bold")
        ax.tick_params(axis="x", labelsize=8.5, rotation=35, length=0, colors="#52514e")
        ax.tick_params(axis="y", labelsize=8, length=0, colors="#52514e")
        ax.grid(axis="y", color="#e4e3de", linewidth=0.8)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_visible(False)
    axes[0].set_ylabel("hoogste score (F1 per gezicht)", fontsize=9, color="#52514e")
    axes[0].set_ylim(0, 1.08)
    axes[0].set_yticks(np.arange(0, 1.01, 0.2))
    fig.suptitle(f"Hoe hoog komt de score met elke keuze? Oranje is de keuze van de winnaar ({EXAMPLE_SETS[args.voorbeelden]}).", x=0.01, ha="left", fontsize=11, fontweight="bold", color="#0b0b0b")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out / "afstellen_per_instelling.png", dpi=140)
    plt.close(fig)
    print(json.dumps(best, ensure_ascii=False))
    print(honest[["filmpje", "model", "marge", "afstand", "f1"]].to_string(index=False))


if __name__ == "__main__":
    main()
