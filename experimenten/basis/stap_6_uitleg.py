r"""Stap 6: de uitleg bij de uitkomsten: resultaten/<set>/README.md, met de echte getallen.

Gebruik (vanuit de map experimenten, na stap 3, 4 en 5):
    Mac:     .venv/bin/python basis/stap_6_uitleg.py --voorbeelden fotos
    Windows: .venv\Scripts\python basis\stap_6_uitleg.py --voorbeelden fotos
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.paden import EXAMPLE_SETS
from gedeeld.uitleg import write
from instellingen import DREMPEL, MARGIN, METRIC, MODEL, folder


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--voorbeelden", choices=EXAMPLE_SETS, default="fotos", help="welke set voorbeeldfoto's")
    args = parser.parse_args()
    out, title = folder(args.voorbeelden), EXAMPLE_SETS[args.voorbeelden]
    write(out, f"Basis ({title})",
          "Dit is het basisexperiment: FaceNet staat zo standaard mogelijk ingesteld en vergelijkt elk gezicht in de filmpjes met de "
          "voorbeelden uit deze set. De uitleg van het experiment staat in [de README van de basis](../../README.md).",
          [("Model", MODEL), ("Extra ruimte om het kader", f"{MARGIN:.0%}"), ("Afstand", METRIC.replace("euclidean_l2", "genormaliseerde Euclidische afstand")),
           ("Drempel", f"{DREMPEL:.2f}".replace(".", ",")), ("Per persoon", "de afstand tot de meest gelijkende voorbeeldfoto"),
           ("Toewijzen", "elk kader los"), ("Voorbeelden", title.removeprefix("voorbeelden: "))],
          f"basis/draai_alles.py --voorbeelden {args.voorbeelden}")


if __name__ == "__main__":
    main()
