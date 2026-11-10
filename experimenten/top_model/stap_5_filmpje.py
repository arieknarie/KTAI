r"""Stap 5: het filmpje met de namen van Periskop. Hiervoor is ffmpeg nodig (Mac: brew install ffmpeg, Windows: winget install Gyan.FFmpeg).

Gebruik (vanuit de map experimenten, na stap 3):
    Mac:     .venv/bin/python top_model/stap_5_filmpje.py
    Windows: .venv\Scripts\python top_model\stap_5_filmpje.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.filmpje import make
from instellingen import OUT, winner


def main() -> None:
    make(pd.read_csv(OUT / "voorspellingen.csv"), OUT / "filmpje.mp4", f"Periskop, drempel {winner()['drempel']:.2f}, voorbeelden: foto's + stills in kostuum")


if __name__ == "__main__":
    main()
