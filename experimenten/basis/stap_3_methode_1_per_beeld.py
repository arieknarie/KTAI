r"""Stap 3: meten met methode 1 (per beeld). Zie gedeeld/meten.py.

Uitvoer in resultaten/<set>/: methode_1_tabel.csv, methode_1_tabel.png (visualisatie 1 van de opdracht) en
methode_1_tijdlijn.png (visualisatie 2 van de opdracht).

Gebruik (vanuit de map experimenten, na stap 2):
    Mac:     .venv/bin/python basis/stap_3_methode_1_per_beeld.py --voorbeelden fotos
    Windows: .venv\Scripts\python basis\stap_3_methode_1_per_beeld.py --voorbeelden fotos
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.meten import method_1
from gedeeld.paden import EXAMPLE_SETS
from instellingen import folder


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--voorbeelden", choices=EXAMPLE_SETS, default="fotos", help="welke set voorbeeldfoto's")
    args = parser.parse_args()
    out, title = folder(args.voorbeelden), EXAMPLE_SETS[args.voorbeelden]
    print(method_1(pd.read_csv(out / "voorspellingen.csv"), out, title).to_string(index=False))


if __name__ == "__main__":
    main()
