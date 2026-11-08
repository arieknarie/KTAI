r"""Het plaatje dat het verschil tussen de twee meetmethodes laat zien, met een echt beeld uit de resultaten.

Gezocht wordt een beeld waarin FaceNet een persoon ziet die er echt is, maar op een ander gezicht. Methode 1 rekent dat goed, methode 2 fout.
Uitvoer: fotos/twee_methodes.jpg.

Gebruik (vanuit de map experimenten, na basis/draai_alles.py):
    Mac:     .venv/bin/python basis/maak_foto.py
    Windows: .venv\Scripts\python basis\maak_foto.py
"""

import sys
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.meten import IOU, overlap
from gedeeld.paden import GROUND_TRUTH, MOVIES, NAMES

HERE = Path(__file__).resolve().parent
COLOURS = {"Der Alte": "#ff4d4d", "Fritz Grade": "#4da6ff", "Johann": "#ffd11a", "Werner": "#33cc66"}


def main() -> None:
    found = pd.read_csv(HERE / "resultaten" / "fotos_en_kostuum" / "voorspellingen.csv")
    truth = pd.read_csv(GROUND_TRUTH)
    faces = {key: g for key, g in truth.groupby(["bestand", "beeld"])}
    named = found[found["facenet"].isin(NAMES)]
    best, score = None, -1
    for key, g in named.groupby(["bestand", "beeld"]):
        if key not in faces or len(faces[key]) < 2 or not key[0].startswith(("Das Boot 1 ", "Das Boot 4", "Das Boot 3")):
            continue
        for b in g.itertuples():
            same = faces[key][faces[key]["persoon"] == b.facenet]
            if len(same) and overlap((b.x, b.y, b.w, b.h), tuple(same[["x", "y", "w", "h"]].iloc[0])) < IOU and b.w > score:
                best, score = (key, b.facenet), b.w
    (video, frame), person = best
    capture, image = cv2.VideoCapture(str(MOVIES / video)), None
    for _ in range(frame + 1):                                 # op volgorde lezen, nooit naar een beeld springen
        ok, image = capture.read()
    capture.release()
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w = image.shape[:2]
    small = cv2.resize(image, (1280, round(1280 * h / w)), interpolation=cv2.INTER_AREA)
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.5), facecolor="white")
    rows = [(r.facenet, r.x, r.y, r.w, r.h) for r in named[(named["bestand"] == video) & (named["beeld"] == frame)].itertuples()]
    panels = ((axes[0], rows, "Wat FaceNet zegt"), (axes[1], [(r.persoon, r.x, r.y, r.w, r.h) for r in faces[(video, frame)].itertuples()], "De ground truth"))
    for ax, boxes, title in panels:
        ax.imshow(small, extent=(0, w, h, 0))
        ax.set_xlim(0, w); ax.set_ylim(h, 0); ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        for name, x, y, bw, bh in boxes:
            ax.add_patch(Rectangle((x, y), bw, bh, fill=False, edgecolor=COLOURS[name], linewidth=2.4))
            ax.text(x, y, name, fontsize=10, fontweight="bold", color="#111111", va="bottom", ha="left", bbox={"facecolor": COLOURS[name], "edgecolor": "none", "pad": 1.5})
        ax.set_title(title, loc="left", fontsize=12, fontweight="bold", color="#0b0b0b")
    fig.suptitle(f"{video.split(' [')[0]}, beeld {frame + 1}. FaceNet zet de naam {person} op een kader dat niet op het gezicht van {person} ligt. "
                 "Methode 1 rekent dat goed, methode 2 fout.", x=0.012, ha="left", fontsize=11, color="#0b0b0b")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    (HERE / "fotos").mkdir(exist_ok=True)
    fig.savefig(HERE / "fotos" / "twee_methodes.jpg", dpi=110, pil_kwargs={"quality": 90})
    plt.close(fig)
    print(video, frame, person)


if __name__ == "__main__":
    main()
