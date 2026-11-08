r"""Spreiding van de voorbeelden: hoe ver liggen de foto's van één persoon uit elkaar, en hoe dicht liggen verschillende personen?

Voor drie sets (out-of-character: de gewone foto's; in-character: de stills; en de totale set) wordt berekend, met FaceNet standaard
en de genormaliseerde Euclidische afstand:
- de maximale afstand tussen twee foto's van dezelfde persoon (de spreiding), en welke twee foto's dat zijn;
- de minimale afstand tussen twee foto's van verschillende personen, en welke twee foto's dat zijn.

Daarnaast een test van het idee dat FaceNet bij een onherkenbaar kader kiest voor de persoon met de grootste spreiding. Een onherkenbaar
kader is hier een kader dat niet op het gezicht van een van de vier personen ligt (figuranten en dingen die geen gezicht zijn). Per set
wordt geteld welke persoon voor die kaders het dichtstbij is.

Uitvoer in resultaten/: spreiding.csv, kleinste_afstand.csv, onherkenbaar.csv en afstanden.png.

Gebruik (vanuit de map experimenten, na basis/draai_alles.py en alleen_in_karakter/draai.py):
    Mac:     .venv/bin/python spreiding/draai.py
    Windows: .venv\Scripts\python spreiding\draai.py
"""

import itertools
import sys
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.facenet import cut, load_detections, unit
from gedeeld.meten import hit_matrix
from gedeeld.paden import EXPERIMENTEN, GROUND_TRUTH, NAMES, PICTURES

HERE = Path(__file__).resolve().parent
SETS = {"out-of-character (foto's)": EXPERIMENTEN / "basis" / "resultaten" / "fotos",
        "in-character (stills)": EXPERIMENTEN / "alleen_in_karakter" / "resultaten",
        "totale set": EXPERIMENTEN / "basis" / "resultaten" / "fotos_en_kostuum"}


def short(path: str) -> str:
    return path.split("/")[-1]


def main() -> None:
    out = HERE / "resultaten"
    out.mkdir(parents=True, exist_ok=True)
    detections = load_detections()
    hit = hit_matrix(detections, pd.read_csv(GROUND_TRUTH))
    spread, closest, unknown, matrices, pairs = [], [], [], {}, []
    for set_name, folder in SETS.items():
        examples = pd.read_csv(folder / "voorbeelden.csv")
        names, photos = examples["persoon"].to_numpy(), examples["bestand"].to_numpy()
        vectors = unit(examples[[f"v{i}" for i in range(128)]].to_numpy(dtype=np.float32))
        distance = np.linalg.norm(vectors[:, None] - vectors[None], axis=2)
        matrix = np.zeros((4, 4))
        for a, b in itertools.product(range(4), range(4)):
            ia, ib = np.flatnonzero(names == NAMES[a]), np.flatnonzero(names == NAMES[b])
            part = distance[np.ix_(ia, ib)]
            if a == b:
                part = part.copy()
                np.fill_diagonal(part, -1)
                i, j = np.unravel_index(part.argmax(), part.shape)
                matrix[a, b] = part[i, j]
                spread.append({"set": set_name, "persoon": NAMES[a], "voorbeelden": len(ia), "maximale_afstand": round(float(part[i, j]), 3),
                               "gemiddelde_afstand": round(float(distance[np.ix_(ia, ia)][np.triu_indices(len(ia), 1)].mean()), 3),
                               "foto_1": short(photos[ia[i]]), "foto_2": short(photos[ia[j]])})
                pairs.append((set_name, f"{NAMES[a]}: grootste afstand {part[i, j]:.2f}".replace(".", ","), examples, int(ia[i]), int(ia[j])))
            else:
                i, j = np.unravel_index(part.argmin(), part.shape)
                matrix[a, b] = part[i, j]
                if a < b:
                    closest.append({"set": set_name, "persoon_1": NAMES[a], "persoon_2": NAMES[b], "minimale_afstand": round(float(part[i, j]), 3),
                                    "foto_1": short(photos[ia[i]]), "foto_2": short(photos[ib[j]])})
                    pairs.append((set_name, f"{NAMES[a]} / {NAMES[b]}: kleinste afstand {part[i, j]:.2f}".replace(".", ","), examples, int(ia[i]), int(ib[j])))
        matrices[set_name] = matrix

        found = pd.read_csv(folder / "voorspellingen.csv")
        nobody = (hit < 0).all(axis=1)                      # kaders die op geen van de vier gezichten liggen
        share = found.loc[nobody, "dichtstbij"].value_counts(normalize=True).reindex(NAMES, fill_value=0.0)
        named = found.loc[nobody, "facenet"].value_counts().reindex(NAMES, fill_value=0)
        for person in NAMES:
            row = next(s for s in spread if s["set"] == set_name and s["persoon"] == person)
            unknown.append({"set": set_name, "persoon": person, "maximale_afstand": row["maximale_afstand"], "aandeel_dichtstbij_procent": round(100 * float(share[person]), 1),
                            "keer_benoemd_onder_drempel": int(named[person])})

    spread, closest, unknown = pd.DataFrame(spread), pd.DataFrame(closest), pd.DataFrame(unknown)
    spread.to_csv(out / "spreiding.csv", index=False, lineterminator="\n")
    closest.to_csv(out / "kleinste_afstand.csv", index=False, lineterminator="\n")
    unknown.to_csv(out / "onherkenbaar.csv", index=False, lineterminator="\n")

    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.5), facecolor="white")
    for ax, (set_name, matrix) in zip(axes, matrices.items()):
        ax.imshow(matrix, cmap="Blues", vmin=0, vmax=1.6)
        for r, c in itertools.product(range(4), range(4)):
            ax.text(c, r, f"{matrix[r, c]:.2f}".replace(".", ","), ha="center", va="center", fontsize=10.5, color="white" if matrix[r, c] > 0.95 else "#0b0b0b",
                    fontweight="bold" if r == c else "normal")
        ax.set_xticks(range(4), NAMES, fontsize=8.5, rotation=20)
        ax.set_yticks(range(4), NAMES, fontsize=8.5)
        ax.set_title(set_name, fontsize=11, fontweight="bold", color="#0b0b0b", loc="left")
        ax.tick_params(length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
    fig.suptitle("Dikgedrukt op de diagonaal: de grootste afstand binnen een persoon. Daarbuiten: de kleinste afstand tussen twee personen.", x=0.01, ha="left", fontsize=11, color="#52514e")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out / "afstanden.png", dpi=140)
    plt.close(fig)
    tiles = []
    for set_name, text, examples, i, j in pairs:
        if set_name != "totale set":
            continue
        faces = []
        for k in (i, j):
            r = examples.iloc[k]
            faces.append(cv2.resize(cut(cv2.imread(str(PICTURES / r["bestand"])), r["x"], r["y"], r["w"], r["h"]), (130, 130), interpolation=cv2.INTER_AREA))
        bar = np.full((30, 266, 3), 255, np.uint8)
        cv2.putText(bar, text, (4, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
        tiles.append(np.vstack([bar, np.hstack([faces[0], np.full((130, 6, 3), 255, np.uint8), faces[1]]), np.full((10, 266, 3), 255, np.uint8)]))
    grid = [np.hstack(tiles[n:n + 5] + [np.full_like(tiles[0], 255)] * (5 - len(tiles[n:n + 5]))) for n in range(0, len(tiles), 5)]
    cv2.imwrite(str(out / "verste_en_dichtste_fotos.jpg"), np.vstack(grid), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(spread.drop(columns=["foto_1", "foto_2"]).to_string(index=False))
    print(unknown.to_string(index=False))


if __name__ == "__main__":
    main()
