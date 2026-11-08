r"""Werner met baard: wat gebeurt er als er meer stills van Werner met baard in de in-karakter set zitten?

De in-karakter set bestaat uit de stills. Van de 12 stills van Werner zijn er 6 met een baard, 5 zonder baard en 1 waarop dat niet te zien is
(te donker; die doet hier niet mee). De andere drie personen blijven hetzelfde. Begonnen wordt met de 5 stills zonder baard. Daarna komen er 1
tot en met 6 stills met baard bij; elke combinatie wordt geprobeerd. Er zijn geen beelden uit de filmpjes gebruikt.

FaceNet staat standaard (drempel 0,80). Gemeten wordt met methode 2 (per gezicht).
Uitvoer in resultaten/: alle_combinaties.csv, per_aantal.csv en werner_baard.png.

Gebruik (vanuit de map experimenten, na alleen_in_karakter/draai.py):
    Mac:     .venv/bin/python werner_baard/draai.py
    Windows: .venv\Scripts\python werner_baard\draai.py
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

from gedeeld.facenet import box_vectors, cut, load_detections
from gedeeld.herkennen import example_distances
from gedeeld.meten import fast_per_person, fast_setup, rates
from gedeeld.paden import EXPERIMENTEN, NAMES, PICTURES

HERE = Path(__file__).resolve().parent
DREMPEL = 0.80
WITH_BEARD = {"pictures/inCharacter/FritzGrade/alte_and_fritz_and_werner.png", "pictures/inCharacter/FritzGrade/alte_and_fritz_and_werner2.png",
              "pictures/inCharacter/FritzGrade/werner_and_fritz.png", "pictures/inCharacter/Werner/werner3.jpg",
              "pictures/inCharacter/Werner/alte_and_werner3.jpg", "pictures/inCharacter/Werner/werner_and_johann.jpg"}
UNCLEAR = "pictures/inCharacter/FritzGrade/Fritz1.jpg"


def main() -> None:
    out = HERE / "resultaten"
    out.mkdir(parents=True, exist_ok=True)
    examples = pd.read_csv(EXPERIMENTEN / "alleen_in_karakter" / "resultaten" / "voorbeelden.csv")
    names, photos = examples["persoon"].to_numpy(), examples["bestand"].to_numpy()
    refs = examples[[f"v{i}" for i in range(128)]].to_numpy(dtype=np.float32)
    detections = load_detections()
    boxes = box_vectors(detections, [("Facenet", 0.0)])[("Facenet", 0.0)]
    setup = fast_setup(detections)
    distance = example_distances(boxes, refs, "euclidean_l2")
    person_of = np.array([NAMES.index(n) for n in names])

    beard = [i for i in np.flatnonzero(names == "Werner") if photos[i] in WITH_BEARD]
    unclear = [i for i in np.flatnonzero(names == "Werner") if photos[i] == UNCLEAR]
    base = [i for i in range(len(names)) if i not in beard and i not in unclear]
    print(f"Werner: {len(beard)} met baard, {int((names == 'Werner').sum()) - len(beard) - len(unclear)} zonder baard, {len(unclear)} niet te zien")

    rows = []
    for size in range(len(beard) + 1):
        for chosen in itertools.combinations(beard, size):
            active = base + list(chosen)
            part = distance[:, active]
            nearest = part.argmin(axis=1)
            person = person_of[np.array(active)][nearest]
            counts = fast_per_person(person, part[np.arange(len(part)), nearest], setup["hit"], setup["faces_per_person"], DREMPEL)
            werner = counts[NAMES.index("Werner")]
            total = counts.sum(axis=0)
            rows.append({"stills_met_baard": size, "welke": " + ".join(photos[i].split("/")[-1] for i in chosen) or "geen",
                         "werner_goed": int(werner[0]), "werner_fout_benoemd": int(werner[1]), "werner_gemist": int(werner[2]),
                         **dict(zip(("werner_precisie", "werner_recall", "werner_f1"), rates(*map(int, werner)))),
                         **dict(zip(("alle_precisie", "alle_recall", "alle_f1"), rates(*map(int, total))))})
    table = pd.DataFrame(rows)
    table.to_csv(out / "alle_combinaties.csv", index=False, lineterminator="\n")
    mean = table.groupby("stills_met_baard").agg(combinaties=("welke", "size"), werner_precisie=("werner_precisie", "mean"), werner_recall=("werner_recall", "mean"),
                                                 werner_f1=("werner_f1", "mean"), werner_f1_laagste=("werner_f1", "min"), werner_f1_hoogste=("werner_f1", "max"),
                                                 alle_f1=("alle_f1", "mean")).round(3).reset_index()
    mean.to_csv(out / "per_aantal.csv", index=False, lineterminator="\n")

    no_beard = [i for i in np.flatnonzero(names == "Werner") if i not in beard and i not in unclear]
    lines = []
    for text, group in (("met baard", beard), ("zonder baard", no_beard), ("niet te zien, doet niet mee", unclear)):
        tiles = [cv2.resize(cut(cv2.imread(str(PICTURES / photos[i])), examples["x"][i], examples["y"][i], examples["w"][i], examples["h"][i]), (130, 130), interpolation=cv2.INTER_AREA) for i in group]
        row = np.hstack(tiles + [np.full((130, 130, 3), 255, np.uint8)] * (6 - len(tiles)))
        bar = np.full((28, row.shape[1], 3), 255, np.uint8)
        cv2.putText(bar, f"Stills van Werner, {text}: {len(group)}", (4, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 0, 0), 1, cv2.LINE_AA)
        lines += [bar, row]
    cv2.imwrite(str(out / "werner_stills.jpg"), np.vstack(lines), [cv2.IMWRITE_JPEG_QUALITY, 88])

    fig, ax = plt.subplots(figsize=(8.2, 4.6), facecolor="white")
    x = mean["stills_met_baard"]
    ax.fill_between(x, mean["werner_f1_laagste"], mean["werner_f1_hoogste"], color="#2a78d6", alpha=0.15, linewidth=0, label="F1 van Werner: laagste tot hoogste combinatie")
    for column, colour, label in (("werner_f1", "#2a78d6", "F1 van Werner"), ("werner_precisie", "#eb6834", "precisie van Werner"), ("werner_recall", "#1baf7a", "recall van Werner"), ("alle_f1", "#8a8983", "F1 van alle vier")):
        ax.plot(x, mean[column], marker="o", markersize=5, linewidth=2, color=colour, label=label)
    ax.set_xlabel("aantal stills van Werner met baard in de in-karakter set", fontsize=9.5, color="#52514e")
    ax.set_ylabel("gemiddelde over alle combinaties", fontsize=9.5, color="#52514e")
    ax.set_xticks(x)
    ax.set_ylim(0, 1)
    ax.tick_params(length=0, labelsize=9, colors="#52514e")
    ax.grid(axis="y", color="#e4e3de", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(frameon=False, fontsize=8.5, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.17))
    ax.set_title("Meer stills van Werner met baard in de in-karakter set", loc="left", fontsize=11, fontweight="bold", color="#0b0b0b")
    fig.tight_layout()
    fig.savefig(out / "werner_baard.png", dpi=140)
    plt.close(fig)
    print(mean.to_string(index=False))


if __name__ == "__main__":
    main()
