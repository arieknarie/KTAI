r"""Stap 4: meten met methode 2 (per gezicht). Zie gedeeld/meten.py.

Uitvoer in resultaten/<set>/: methode_2_tabel.csv/.png, methode_2_verwarring.csv/.png, methode_2_overlap.csv en
gebruik_per_foto.csv (welke voorbeeldfoto de doorslag gaf, en hoe vaak dat klopte).

Gebruik (vanuit de map experimenten, na stap 2):
    Mac:     .venv/bin/python basis/stap_4_methode_2_per_gezicht.py --voorbeelden fotos
    Windows: .venv\Scripts\python basis\stap_4_methode_2_per_gezicht.py --voorbeelden fotos
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.meten import method_2
from gedeeld.paden import EXAMPLE_SETS
from instellingen import folder


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--voorbeelden", choices=EXAMPLE_SETS, default="fotos", help="welke set voorbeeldfoto's")
    args = parser.parse_args()
    out, title = folder(args.voorbeelden), EXAMPLE_SETS[args.voorbeelden]
    print(method_2(pd.read_csv(out / "voorspellingen.csv"), out, title).to_string(index=False))


if __name__ == "__main__":
    main()
