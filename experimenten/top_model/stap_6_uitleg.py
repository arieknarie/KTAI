r"""Stap 6: de README bij de uitkomsten: resultaten/README.md, met de getallen uit de metingen.

Gebruik (vanuit de map experimenten, na stap 4 en 5):
    Mac:     .venv/bin/python top_model/stap_6_uitleg.py
    Windows: .venv\Scripts\python top_model\stap_6_uitleg.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.meten import comma
from gedeeld.uitleg import write
from instellingen import OUT, winner


def main() -> None:
    best = winner()
    write(OUT, "De uitkomsten van Periskop",
          "Dit zijn de uitkomsten van Periskop, ons top model. FaceNet krijgt hier als voorbeelden de gewone foto's en de stills uit de film. "
          "Hoe Periskop werkt, staat in [de uitleg van het top model](../README.md).",
          [("Blikken", best["naam_blikken"]), ("Deel van de track dat meetelt", f"de beste {best['deel_van_de_track']:.0%} van de beelden"),
           ("Verschil met de tweede persoon", f"minstens {comma(best['verschil_met_tweede'], 2)}"), ("Zekerheid van de detector", f"gemiddeld minstens {comma(best['zekerheid_detector'], 2)}"),
           ("Gaten in een track vullen", "ja" if best["gaten_vullen"] else "nee"), ("Drempel", comma(best["drempel"], 4))],
          "top_model/draai_alles.py",
          extra=f"**Een eerlijke schatting.** De instellingen zijn gekozen op dezelfde beelden als waarop we meten. Daardoor is de score hierboven iets te gunstig. "
                f"Bij de eerlijke schatting kiezen we de combinatie en de drempel steeds op zeven filmpjes en meten we op het achtste. Dan is de score **{comma(best['f1_eerlijke_schatting'])}** (zie `eerlijke_schatting.csv`).")


if __name__ == "__main__":
    main()
