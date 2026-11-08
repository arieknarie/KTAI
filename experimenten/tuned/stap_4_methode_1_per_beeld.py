r"""Stap 4: meten met methode 1 (per beeld), op precies dezelfde manier als bij de basis. Zie gedeeld/meten.py.

Gebruik (vanuit de map experimenten, na stap 3):
    Mac:     .venv/bin/python tuned/stap_4_methode_1_per_beeld.py --voorbeelden fotos
    Windows: .venv\Scripts\python tuned\stap_4_methode_1_per_beeld.py --voorbeelden fotos
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.meten import method_1
from gedeeld.paden import EXAMPLE_SETS
from instellingen import SETS, folder


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--voorbeelden", choices=SETS, default="fotos", help="welke set voorbeeldfoto's")
    args = parser.parse_args()
    out, title = folder(args.voorbeelden), f"tuned, {EXAMPLE_SETS[args.voorbeelden]}"
    print(method_1(pd.read_csv(out / "voorspellingen.csv"), out, title).to_string(index=False))


if __name__ == "__main__":
    main()
