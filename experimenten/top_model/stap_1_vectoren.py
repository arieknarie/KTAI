r"""Stap 1: de vectoren. Periskop kijkt ook naar het spiegelbeeld van elk gezicht. Die vectoren worden hier één keer uitgerekend.

De vectoren van de andere blikken komen uit tuned/stap_1_vectoren.py. Dat script draait hier eerst, en is snel als de vectoren er al zijn.
Uitvoer: tussenbestanden/ (gaat niet mee naar GitHub) en resultaten/voorbeelden.jpg.

Gebruik (vanuit de map experimenten):
    Mac:     .venv/bin/python top_model/stap_1_vectoren.py
    Windows: .venv\Scripts\python top_model\stap_1_vectoren.py
"""

import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.facenet import cut, lighten, load_detections, represent
from gedeeld.paden import MOVIES, PICTURES
from gedeeld.voorbeelden import rows, sheet
from instellingen import EXAMPLE_SET, MIRROR, OTHER_SETS, OUT, TOP
from model import view_paths


def mirrored(face: np.ndarray, margin: float, image_box: tuple) -> np.ndarray:
    return cv2.flip(lighten(cut(face, *image_box, margin)), 1)


def main() -> None:
    subprocess.run([sys.executable, str(TOP.parent / "tuned" / "stap_1_vectoren.py")], check=True)
    OUT.mkdir(parents=True, exist_ok=True)
    table = rows(EXAMPLE_SET)
    sheet(table, [cut(cv2.imread(str(PICTURES / r.bestand)), r.x, r.y, r.w, r.h) for r in table.itertuples()], OUT / "voorbeelden.jpg")
    views = [view for view in MIRROR if view[2]]
    missing = [view for view in views if not view_paths(EXAMPLE_SET, view)[0].exists()]
    if missing:
        detections = load_detections()
        margins = sorted({view[1] for view in missing})
        parts = {view: [] for view in missing}
        for video, boxes in detections.groupby("video", sort=False):
            frames, faces = {f: g for f, g in boxes.groupby("frame")}, {m: [] for m in margins}
            capture, index = cv2.VideoCapture(str(MOVIES / video)), 0
            while index <= max(frames):                   # op volgorde lezen, nooit naar een beeld springen
                ok, image = capture.read()
                if not ok:
                    raise SystemExit(f"{video}: beeld {index} kon niet gelezen worden")
                for b in (frames[index].itertuples() if index in frames else []):
                    for m in margins:
                        faces[m].append(mirrored(image, m, (b.x, b.y, b.w, b.h)))
                index += 1
            capture.release()
            for view in missing:
                parts[view].append(represent(faces[view[1]], view[0]))
            print(f"  {video}: {len(boxes)} kaders", flush=True)
        for view, vectors in parts.items():
            np.save(view_paths(EXAMPLE_SET, view)[0], np.concatenate(vectors))
    for example_set in [EXAMPLE_SET] + OTHER_SETS:
        table = rows(example_set)
        images = [cv2.imread(str(PICTURES / r.bestand)) for r in table.itertuples()]
        for view in views:
            path = view_paths(example_set, view)[1]
            if not path.exists():
                np.save(path, represent([mirrored(im, view[1], (r.x, r.y, r.w, r.h)) for im, r in zip(images, table.itertuples())], view[0]))
    print("klaar")


if __name__ == "__main__":
    main()
