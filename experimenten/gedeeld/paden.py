"""Waar alle bestanden staan, en wie we zoeken. Alle experimenten halen dit hier vandaan."""

from pathlib import Path

EXPERIMENTEN = Path(__file__).resolve().parent.parent
REPO = EXPERIMENTEN.parent
MOVIES = REPO / "filmpjes"
LABELEN = REPO / "labelen"
PICTURES = LABELEN / "invoer"                  # de namen van de foto's en stills zijn ten opzichte van deze map
STEP0 = LABELEN / "output" / "stap_0_voorbereiding"
DETECTIONS = STEP0 / "tracks" / "detections_0.3.csv"
FRAMES = STEP0 / "tracks" / "frames.csv"
AUTOMATIC_LABELS = STEP0 / "automatic_labels.csv"
STILLS_INDEX = STEP0 / "stills_index.csv"
GROUND_TRUTH = LABELEN / "output" / "stap_3_fouten_verbeteren" / "ground_truth.csv"
GROUND_TRUTH_PHOTOS = LABELEN / "output" / "stap_3_fouten_verbeteren" / "ground_truth_fotos_en_stills.csv"
VECTORS = EXPERIMENTEN / "tussenbestanden"     # de vectoren van alle kaders (gaan niet mee naar GitHub)

PERSONS = {"DerAlte": "Der Alte", "FritzGrade": "Fritz Grade", "Johann": "Johann", "Werner": "Werner"}
NAMES = list(PERSONS.values())
OTHER = "iemand anders"     # de uitkomst als een kader niet genoeg op een van de vier personen lijkt

# de drie sets voorbeeldfoto's: de naam, en hoe de set in de titels van de grafieken heet
EXAMPLE_SETS = {"fotos": "voorbeelden: foto's",
                "fotos_en_kostuum": "voorbeelden: foto's + stills in kostuum",
                "alleen_kostuum": "voorbeelden: alleen stills in kostuum"}
