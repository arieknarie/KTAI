"""De instellingen van het top model, Periskop. Alle stappen halen hun instellingen hier vandaan.

Een *blik* is een manier waarop FaceNet naar een gezicht kijkt: met welk model, met hoeveel extra ruimte om het kader, en of het gezicht gespiegeld
is. Elk gezicht wordt eerst lichter gemaakt. Periskop neemt het gemiddelde van de afstanden van alle blikken.
"""

import json
from pathlib import Path

TOP = Path(__file__).resolve().parent
OUT = TOP / "resultaten"
EXAMPLE_SET = "fotos_en_kostuum"                     # de voorbeelden van Periskop: de gewone foto's en de stills
OTHER_SETS = ["fotos", "alleen_kostuum"]             # alleen om te kijken hoe het zonder de stills of zonder de foto's gaat

F512, F128 = "Facenet512", "Facenet"
ONE = [(F512, 0.2, False)]                                                            # zoals het getunde model
TWO_MODELS = [(F512, 0.2, False), (F128, 0.2, False)]
TWO_CROPS = TWO_MODELS + [(F512, 0.3, False), (F128, 0.3, False)]
MIRROR = TWO_CROPS + [(model, margin, True) for model, margin, _ in TWO_CROPS]

VIEWS = {"twee modellen": TWO_MODELS, "twee modellen, twee uitsneden": TWO_CROPS, "ook gespiegeld": MIRROR}
BEST_PART = [1.0, 0.5, 0.3]                          # welk deel van de beelden van een track meetelt: alleen de beste beelden
MARGINS = [0.0, 0.03, 0.05]                          # zoveel moet de beste persoon dichterbij zijn dan de tweede
SCORES = [0.0, 0.35]                                 # zo zeker moet de detector gemiddeld zijn van een track
GAPS = [False, True]                                 # of gaten binnen een track worden opgevuld
THRESHOLDS = 200                                     # zoveel drempels worden per instelling geprobeerd


def winner() -> dict:
    return json.loads((OUT / "beste_instelling.json").read_text(encoding="utf-8"))
