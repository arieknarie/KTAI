r"""Wie wordt als Johann herkend op plekken waar Johann er niet is?

Telt alle kaders waaraan FaceNet (standaard, drempel 0,80) de naam Johann geeft, terwijl het kader niet op het gezicht van Johann ligt. Voor
die kaders staat in de ground truth wie het echt is: een van de andere drie personen, of geen van de vier (een figurant of iets dat geen
gezicht is). Dat wordt per filmpje geteld, voor de drie sets voorbeelden, en ook welke voorbeeldfoto de doorslag gaf.

Uitvoer in resultaten/: johann_per_filmpje.csv, johann_per_foto.csv en wie_wordt_johann.png.

Gebruik (vanuit de map experimenten, na basis/draai_alles.py en alleen_in_karakter/draai.py):
    Mac:     .venv/bin/python wie_wordt_johann/draai.py
    Windows: .venv\Scripts\python wie_wordt_johann\draai.py
"""

import sys
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.facenet import cut, load_detections
from gedeeld.meten import hit_matrix
from gedeeld.paden import EXPERIMENTEN, GROUND_TRUTH, NAMES, PICTURES

HERE = Path(__file__).resolve().parent
SETS = {"foto's": EXPERIMENTEN / "basis" / "resultaten" / "fotos",
        "alleen stills": EXPERIMENTEN / "alleen_in_karakter" / "resultaten",
        "foto's + stills": EXPERIMENTEN / "basis" / "resultaten" / "fotos_en_kostuum"}
WHO = ["Der Alte", "Fritz Grade", "Werner", "geen van de vier"]
COLOURS = {"Der Alte": "#2a78d6", "Fritz Grade": "#eb6834", "Werner": "#1baf7a", "geen van de vier": "#8a8983"}


def main() -> None:
    out = HERE / "resultaten"
    out.mkdir(parents=True, exist_ok=True)
    detections = load_detections()
    truth = pd.read_csv(GROUND_TRUTH)
    hit = hit_matrix(detections, truth)
    johann = NAMES.index("Johann")
    has_johann = set(truth.loc[truth["persoon"] == "Johann", "fragment"])
    per_film, per_photo = [], []
    for set_name, folder in SETS.items():
        found = pd.read_csv(folder / "voorspellingen.csv")
        wrong = (found["facenet"] == "Johann").to_numpy() & (hit[:, johann] < 0)
        real = np.array(["geen van de vier"] * len(found), dtype=object)
        for k, name in enumerate(NAMES):
            real[hit[:, k] >= 0] = name
        table = found[wrong].assign(echt=real[wrong])
        for group, g in table.groupby("fragment"):
            row = {"voorbeelden": set_name, "filmpje": group, "johann_in_dit_filmpje": group in has_johann, "kaders_ten_onrechte_johann": len(g)}
            row.update({who: int((g["echt"] == who).sum()) for who in WHO})
            per_film.append(row)
        by_photo = table.groupby("foto").size().sort_values(ascending=False)
        per_photo += [{"voorbeelden": set_name, "foto": photo, "keer_ten_onrechte_johann": int(n)} for photo, n in by_photo.items()]
    per_film, per_photo = pd.DataFrame(per_film), pd.DataFrame(per_photo)
    per_film.to_csv(out / "johann_per_filmpje.csv", index=False, lineterminator="\n")
    per_photo.to_csv(out / "johann_per_foto.csv", index=False, lineterminator="\n")

    films = sorted(set(per_film["filmpje"]), key=lambda g: int(g.split()[-1]))
    shown = [name for name in SETS if (per_film["voorbeelden"] == name).any()]      # met alleen foto's zegt FaceNet nergens ten onrechte Johann
    fig, axes = plt.subplots(1, len(shown), figsize=(4.6 * len(shown) + 1.2, 4.2), sharey=True, facecolor="white", squeeze=False)
    axes = axes[0]
    for ax, set_name in zip(axes, shown):
        part = per_film[per_film["voorbeelden"] == set_name].set_index("filmpje").reindex(films).fillna(0)
        left = np.zeros(len(films))
        for who in WHO:
            ax.barh(films, part[who].to_numpy(), left=left, height=0.6, color=COLOURS[who], label=who, edgecolor="white", linewidth=1)
            left += part[who].to_numpy()
        ax.invert_yaxis() if ax is axes[0] else None
        ax.set_title(f"voorbeelden: {set_name}", fontsize=11, fontweight="bold", color="#0b0b0b", loc="left")
        ax.set_xlabel("kaders die FaceNet ten onrechte Johann noemt", fontsize=9, color="#52514e")
        ax.tick_params(length=0, labelsize=9, colors="#52514e")
        ax.grid(axis="x", color="#e4e3de", linewidth=0.8)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_visible(False)
    axes[0].legend(frameon=False, fontsize=9, loc="lower right", title="wie het echt is", title_fontsize=9)
    fig.tight_layout()
    fig.savefig(out / "wie_wordt_johann.png", dpi=140)
    plt.close(fig)
    examples = pd.read_csv(SETS["foto's + stills"] / "voorbeelden.csv")
    tiles = []
    for row in per_photo[per_photo["voorbeelden"] == "foto's + stills"].head(5).itertuples():
        r = examples[(examples["bestand"] == row.foto) & (examples["persoon"] == "Johann")].iloc[0]
        face = cv2.resize(cut(cv2.imread(str(PICTURES / r["bestand"])), r["x"], r["y"], r["w"], r["h"]), (170, 170), interpolation=cv2.INTER_AREA)
        bar = np.full((48, 170, 3), 255, np.uint8)
        cv2.putText(bar, row.foto.split("/")[-1][:22], (3, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(bar, f"{row.keer_ten_onrechte_johann} keer ten onrechte", (3, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1, cv2.LINE_AA)
        tiles.append(np.vstack([bar, face]))
    cv2.imwrite(str(out / "johann_fotos.jpg"), np.hstack(tiles), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(per_film.to_string(index=False))
    print(per_photo.groupby("voorbeelden").head(4).to_string(index=False))


if __name__ == "__main__":
    main()
