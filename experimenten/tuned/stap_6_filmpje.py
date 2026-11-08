r"""Stap 6: het filmpje met de beste instellingen. Hiervoor is ffmpeg nodig (Mac: brew install ffmpeg, Windows: winget install Gyan.FFmpeg).

Gebruik (vanuit de map experimenten, na stap 3):
    Mac:     .venv/bin/python tuned/stap_6_filmpje.py --voorbeelden fotos
    Windows: .venv\Scripts\python tuned\stap_6_filmpje.py --voorbeelden fotos
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.filmpje import make
from gedeeld.paden import EXAMPLE_SETS
from instellingen import SETS, folder, winner


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--voorbeelden", choices=SETS, default="fotos", help="welke set voorbeeldfoto's")
    args = parser.parse_args()
    out, title = folder(args.voorbeelden), f"tuned, {EXAMPLE_SETS[args.voorbeelden]}"
    best = winner(args.voorbeelden)
    make(pd.read_csv(out / "voorspellingen.csv"), out / "filmpje.mp4",
         f"{best['model']}, marge {best['marge']:.0%}, drempel {best['drempel']:.2f}, {EXAMPLE_SETS[args.voorbeelden]}")


if __name__ == "__main__":
    main()
