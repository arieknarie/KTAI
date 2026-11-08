r"""Stap 1: de vectoren. FaceNet maakt van elk kader en elk voorbeeld een vector, voor elk model en elke manier van uitsnijden.

Invoer:  de kaders uit het labelen, de filmpjes en de voorbeeldfoto's.
Uitvoer: tussenbestanden/ (gaat niet mee naar GitHub) en resultaten/<set>/voorbeelden.jpg.
Dit is het langzame deel (ongeveer een uur); elke combinatie wordt maar één keer uitgerekend.

Gebruik (vanuit de map experimenten):
    Mac:     .venv/bin/python tuned/stap_1_vectoren.py
    Windows: .venv\Scripts\python tuned\stap_1_vectoren.py
"""

import itertools
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.facenet import box_vectors, cut, lighten, load_detections, represent
from gedeeld.paden import PICTURES
from gedeeld.voorbeelden import rows, sheet
from instellingen import LIGHT, MARGINS, MODELS, SETS, example_path, folder


def main() -> None:
    combinations = list(itertools.product(MODELS, MARGINS, LIGHT))
    box_vectors(load_detections(), combinations)
    for example_set in SETS:
        table = rows(example_set)
        folder(example_set).mkdir(parents=True, exist_ok=True)
        images = [cv2.imread(str(PICTURES / r.bestand)) for r in table.itertuples()]
        sheet(table, [cut(image, r.x, r.y, r.w, r.h) for image, r in zip(images, table.itertuples())], folder(example_set) / "voorbeelden.jpg")
        for model, margin, light in combinations:
            path = example_path(example_set, model, margin, light)
            if not path.exists():
                faces = [cut(image, r.x, r.y, r.w, r.h, margin) for image, r in zip(images, table.itertuples())]
                np.save(path, represent([lighten(f) for f in faces] if light else faces, model))
        print(f"{example_set}: {len(table)} voorbeelden", flush=True)


if __name__ == "__main__":
    main()
