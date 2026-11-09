r"""Stap 7: de uitleg bij de uitkomsten: resultaten/<set>/README.md, met de echte getallen.

Gebruik (vanuit de map experimenten, na stap 4, 5 en 6):
    Mac:     .venv/bin/python tuned/stap_7_uitleg.py --voorbeelden fotos
    Windows: .venv\Scripts\python tuned\stap_7_uitleg.py --voorbeelden fotos
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.meten import comma
from gedeeld.paden import EXAMPLE_SETS
from gedeeld.uitleg import write
from instellingen import SETS, folder, winner


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--voorbeelden", choices=SETS, default="fotos", help="welke set voorbeeldfoto's")
    args = parser.parse_args()
    out, title = folder(args.voorbeelden), f"tuned, {EXAMPLE_SETS[args.voorbeelden]}"
    best = winner(args.voorbeelden)
    name = EXAMPLE_SETS[args.voorbeelden].removeprefix("voorbeelden: ")
    write(out, f"De uitkomsten van tuned: {name}",
          f"Dit zijn de uitkomsten van FaceNet met de best gevonden instellingen. Als voorbeelden krijgt FaceNet hier: {name}. "
          "Waarom we dit doen en hoe we hebben afgesteld, staat in [de uitleg van tuned](../../README.md).",
          [("Model", best["model"]), ("Extra ruimte om het kader", f"{best['marge']:.0%}"), ("Donkere gezichten lichter maken", "ja" if best["lichter"] else "nee"),
           ("Afstand", best["afstand"].replace("euclidean_l2", "genormaliseerde Euclidische afstand").replace("cosine", "cosinusafstand").replace("euclidean", "Euclidische afstand")),
           ("Per persoon", "de afstand tot de meest gelijkende voorbeeldfoto" if best["per_persoon"] == "dichtstbij" else "de afstand tot het gemiddelde van de voorbeeldfoto's"),
           ("Toewijzen", "elk kader los" if best["toewijzen"] == "los" else "per beeld elke persoon hoogstens één keer"),
           ("Beslissen", "per kader" if best["beslissen"] == "kader" else "per track"), ("Drempel", comma(best["drempel"], 4))],
          f"tuned/draai_alles.py --voorbeelden {args.voorbeelden}",
          extra=f"**Een eerlijke schatting.** De instellingen zijn gekozen op dezelfde beelden als waarop we meten. Daardoor is de score hierboven wat te gunstig. "
                f"Bij de eerlijke schatting kiezen we de instellingen steeds op zeven filmpjes en meten we op het achtste. Dan is de score **{comma(best['f1_eerlijke_schatting'])}** (zie `eerlijke_schatting.csv`). "
                f"Alle geprobeerde instellingen staan in `alle_instellingen.csv`, en per filmpje de beste instelling in `beste_per_filmpje.csv`.\n\n"
                f"![De hoogste score per keuze bij het afstellen](afstellen_per_instelling.png)\n\n"
                f"*Zo lees je dit plaatje: elk blok is één instelling. De balken laten zien hoe hoog de score kan worden met elke keuze. De blauwe balk is de keuze van de winnaar.*")


if __name__ == "__main__":
    main()
