r"""Stap 3: herkennen met de beste instellingen uit stap 2.

Uitvoer: resultaten/voorspellingen.csv, met dezelfde kolommen als bij de andere experimenten, plus de kolom bijgemaakt: True voor een kader dat
Periskop heeft bijgemaakt om een gat in een track te vullen.

Gebruik (vanuit de map experimenten, na stap 2):
    Mac:     .venv/bin/python top_model/stap_3_herkennen.py
    Windows: .venv\Scripts\python top_model\stap_3_herkennen.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.film import fragments
from gedeeld.herkennen import predictions
from gedeeld.paden import FRAMES, NAMES, OTHER
from instellingen import EXAMPLE_SET, OUT, winner
from model import Data


def main() -> None:
    best = winner()
    data = Data(EXAMPLE_SET)
    matrix, person, distance = data.decide(best)
    names = np.array(NAMES, dtype=object)
    shown = np.where(person >= 0, person, matrix.argmin(axis=1))
    photos = data.closest_photo(tuple(best["blikken"][0]), matrix, person)
    found = predictions(data.detections, names[shown], distance, best["drempel"], photos)
    found["afstand"] = found["afstand"].where(np.isfinite(found["afstand"]))
    found["bijgemaakt"] = False
    if best["gaten_vullen"]:
        frames = pd.read_csv(FRAMES)
        parts = fragments(frames).set_index("video")
        times = {(v, int(f)): t for v, f, t in zip(frames["video"], frames["frame"], frames["time_s"])}
        extra = pd.DataFrame([{"fragment": parts.loc[b["video"], "fragment"], "bestand": b["video"], "beeld": b["frame"],
                               "tijd_s": round(times[(b["video"], b["frame"])] + parts.loc[b["video"], "offset"], 3), "track": b["track"],
                               "x": int(round(b["x"])), "y": int(round(b["y"])), "w": int(round(b["w"])), "h": int(round(b["h"])),
                               "facenet": NAMES[b["persoon"]] if b["afstand"] < best["drempel"] else OTHER, "dichtstbij": NAMES[b["persoon"]],
                               "afstand": round(b["afstand"], 4), "foto": photos[b["bron"]], "bijgemaakt": True} for b in data.filled(person, distance)])
        found = pd.concat([found, extra], ignore_index=True)
    found.to_csv(OUT / "voorspellingen.csv", index=False, lineterminator="\n")
    print(found["facenet"].value_counts().to_string())
    print("bijgemaakte kaders:", int(found["bijgemaakt"].sum()))


if __name__ == "__main__":
    main()
