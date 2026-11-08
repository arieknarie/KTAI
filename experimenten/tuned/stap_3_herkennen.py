r"""Stap 3: herkennen met de beste instellingen uit stap 2.

Uitvoer: resultaten/<set>/voorspellingen.csv, met dezelfde kolommen als bij de basis.
De kolom foto is de meest gelijkende voorbeeldfoto van de gekozen persoon. Bij "gemiddelde" of "track" geeft niet één foto de
doorslag, maar is dit de foto die het meest op het kader lijkt.

Gebruik (vanuit de map experimenten, na stap 2):
    Mac:     .venv/bin/python tuned/stap_3_herkennen.py --voorbeelden fotos
    Windows: .venv\Scripts\python tuned\stap_3_herkennen.py --voorbeelden fotos
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.facenet import load_detections, vector_path
from gedeeld.herkennen import assigned, by_track, example_distances, person_distances, predictions
from gedeeld.paden import EXAMPLE_SETS, NAMES
from gedeeld.voorbeelden import rows
from instellingen import SETS, example_path, folder, winner


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--voorbeelden", choices=SETS, default="fotos", help="welke set voorbeeldfoto's")
    args = parser.parse_args()
    out, title = folder(args.voorbeelden), f"tuned, {EXAMPLE_SETS[args.voorbeelden]}"
    best = winner(args.voorbeelden)
    table = rows(args.voorbeelden)
    names, photos = table["persoon"].to_numpy(), table["bestand"].to_numpy()
    detections = load_detections()
    boxes = np.load(vector_path(best["model"], best["marge"], best["lichter"]))
    refs = np.load(example_path(args.voorbeelden, best["model"], best["marge"], best["lichter"]))
    d = person_distances(boxes, names, refs, best["afstand"], best["per_persoon"])
    frame_id = detections.groupby(["video", "frame"], sort=False).ngroup().to_numpy()
    if best["beslissen"] == "track":
        d = by_track(d, detections.groupby(["video", "track"], sort=False).ngroup().to_numpy())
    person, distance = assigned(d, frame_id, best["toewijzen"])

    shown = np.where(person >= 0, person, d.argmin(axis=1))     # voor een kader zonder persoon: de dichtstbijzijnde persoon
    each = example_distances(boxes, refs, best["afstand"])
    index = np.where(names[None, :] == np.array(NAMES, dtype=object)[shown][:, None], each, np.inf).argmin(axis=1)
    found = predictions(detections, np.array(NAMES, dtype=object)[shown], distance, best["drempel"], photos[index])
    found["afstand"] = found["afstand"].where(np.isfinite(found["afstand"]))
    found.to_csv(out / "voorspellingen.csv", index=False, lineterminator="\n")
    print(found["facenet"].value_counts().to_string())


if __name__ == "__main__":
    main()
