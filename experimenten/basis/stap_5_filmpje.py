r"""Stap 5: het filmpje. Alle filmpjes achter elkaar, met een vierkantje en een naam waar FaceNet een van de vier ziet.

Uitvoer: resultaten/<set>/filmpje.mp4. Hiervoor is ffmpeg nodig (Mac: brew install ffmpeg, Windows: winget install Gyan.FFmpeg).

Gebruik (vanuit de map experimenten, na stap 2):
    Mac:     .venv/bin/python basis/stap_5_filmpje.py --voorbeelden fotos
    Windows: .venv\Scripts\python basis\stap_5_filmpje.py --voorbeelden fotos
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.filmpje import make
from gedeeld.paden import EXAMPLE_SETS
from instellingen import DREMPEL, folder


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--voorbeelden", choices=EXAMPLE_SETS, default="fotos", help="welke set voorbeeldfoto's")
    args = parser.parse_args()
    out, title = folder(args.voorbeelden), EXAMPLE_SETS[args.voorbeelden]
    make(pd.read_csv(out / "voorspellingen.csv"), out / "filmpje.mp4", f"FaceNet standaard, drempel {DREMPEL:.2f}, {title}")


if __name__ == "__main__":
    main()
