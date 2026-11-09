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


NAMES = {"fotos": ("alleen foto's", "alleen de gewone foto's van de acteurs"), "fotos_en_kostuum": ("foto's + stills", "de gewone foto's en de stills uit de film"),
         "alleen_kostuum": ("alleen stills", "alleen de stills uit de film")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--voorbeelden", choices=EXAMPLE_SETS, default="fotos", help="welke set voorbeeldfoto's")
    args = parser.parse_args()
    out, title = folder(args.voorbeelden), EXAMPLE_SETS[args.voorbeelden]
    name = NAMES[args.voorbeelden]
    home = "../../basis/README.md" if args.voorbeelden == "alleen_kostuum" else "../../README.md"
    write(out, f"De uitkomsten van FaceNet standaard: {name[0]}",
          f"Dit zijn de uitkomsten van FaceNet met de standaardinstellingen. FaceNet krijgt hier als voorbeelden {name[1]}. "
          f"Waarom we dit doen en hoe het werkt, staat in [de uitleg van de basis]({home}).",
          [("Model", MODEL), ("Extra ruimte om het kader", f"{MARGIN:.0%}"), ("Afstand", METRIC.replace("euclidean_l2", "genormaliseerde Euclidische afstand")),
           ("Drempel", f"{DREMPEL:.2f}".replace(".", ",")), ("Vergelijken met", "de beste foto van elke persoon"), ("Naam in een beeld", "mag vaker"), ("Beslissen", "per kader"), ("Voorbeelden", name[0])],
          f"basis/draai_alles.py --voorbeelden {args.voorbeelden}")


if __name__ == "__main__":
    main()
