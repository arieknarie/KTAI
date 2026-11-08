r"""Stap 1: de voorbeelden. Van elke voorbeeldfoto maakt FaceNet een vector: 128 getallen die het gezicht beschrijven.

Invoer:  de foto's en stills in labelen/invoer/pictures/, met de kaders uit het labelen (zie gedeeld/voorbeelden.py).
Uitvoer in resultaten/<set>/:
    voorbeelden.csv   per voorbeeld de persoon, het bestand, het kader en de vector (kolommen v0 tot en met v127)
    voorbeelden.jpg   alle voorbeelden als kleine plaatjes, per persoon

Gebruik (vanuit de map experimenten):
    Mac:     .venv/bin/python basis/stap_1_voorbeelden.py --voorbeelden fotos
    Windows: .venv\Scripts\python basis\stap_1_voorbeelden.py --voorbeelden fotos
De sets zijn: fotos, fotos_en_kostuum en alleen_kostuum.
"""

import argparse
import sys
from pathlib import Path

import cv2
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.facenet import cut, represent
from gedeeld.paden import EXAMPLE_SETS, PICTURES
from gedeeld.voorbeelden import rows, sheet
from instellingen import MARGIN, MODEL, folder


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--voorbeelden", choices=EXAMPLE_SETS, default="fotos", help="welke set voorbeeldfoto's")
    args = parser.parse_args()
    out, title = folder(args.voorbeelden), EXAMPLE_SETS[args.voorbeelden]
    out.mkdir(parents=True, exist_ok=True)
    table = rows(args.voorbeelden)
    faces = [cut(cv2.imread(str(PICTURES / r.bestand)), r.x, r.y, r.w, r.h, MARGIN) for r in table.itertuples()]
    vectors = pd.DataFrame(represent(faces, MODEL), columns=[f"v{i}" for i in range(128)])
    pd.concat([table, vectors], axis=1).to_csv(out / "voorbeelden.csv", index=False, float_format="%.9g", lineterminator="\n")
    sheet(table, faces, out / "voorbeelden.jpg")
    print(f"{len(table)} voorbeelden: " + ", ".join(f"{p} {n}" for p, n in table["persoon"].value_counts().items()))


if __name__ == "__main__":
    main()
