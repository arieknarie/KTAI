r"""Stap 4: meten per gezicht, op precies dezelfde manier als bij de andere experimenten. Zie gedeeld/meten.py.

Gebruik (vanuit de map experimenten, na stap 3):
    Mac:     .venv/bin/python top_model/stap_4_meten_per_gezicht.py
    Windows: .venv\Scripts\python top_model\stap_4_meten_per_gezicht.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.meten import method_2
from instellingen import OUT


def main() -> None:
    print(method_2(pd.read_csv(OUT / "voorspellingen.csv"), OUT, "Periskop, voorbeelden: foto's + stills in kostuum").to_string(index=False))


if __name__ == "__main__":
    main()
