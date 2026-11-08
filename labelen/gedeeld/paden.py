"""Alle mappen en bestanden van het labelen op één plek. De programma's van alle stappen halen hun paden hier vandaan.

De uitkomst van elke stap staat in een eigen map in output/, en is de invoer van de volgende stap:

    filmpjes/ + invoer/  -> stap 0 -> output/stap_0_voorbereiding/
                            stap 1 -> output/stap_1_tracks_labelen/labels.csv
                            stap 2 -> output/stap_2_beelden_nakijken/controle_labels.csv
                            stap 3 -> output/stap_3_fouten_verbeteren/correcties.csv en de ground truth
"""

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent   # de hoofdmap van het project: hierin staan filmpjes/ en labelen/
LABELEN = REPO / "labelen"
MOVIES = REPO / "filmpjes"

# wat erin gaat: het model van de detector, de foto's van de acteurs en de stills uit de film. De namen van de foto's
# en stills in de uitkomsten (bijvoorbeeld pictures/personal/Werner/werner4.jpg) zijn ten opzichte van de map invoer/.
INPUT = LABELEN / "invoer"
MODEL = INPUT / "model" / "blaze_face_full_range.tflite"
PERSONAL = INPUT / "pictures" / "personal"
STILLS = INPUT / "pictures" / "inCharacter"

CHECKSUMS = LABELEN / "checksums.sha256"
REQUIREMENTS = LABELEN / "requirements.txt"

# stap 0: de gezichten vinden en volgen, de tracks controleren, en alles klaarzetten voor de labelapp
OUTPUT = LABELEN / "output"
STEP0 = OUTPUT / "stap_0_voorbereiding"
TRACKS = STEP0 / "tracks"
DETECTIONS = TRACKS / "detections_0.3.csv"
TRACK_LIST = TRACKS / "tracks_0.3.csv"
FRAMES = TRACKS / "frames.csv"
AUDIT = STEP0 / "controle"
STILLS_INDEX = STEP0 / "stills_index.csv"
AUTOMATIC_LABELS = STEP0 / "automatic_labels.csv"

# stap 1: de labelapp. De app staat met alles wat de app laat zien (items.json, images/) in één map.
LABELING = LABELEN / "stap_1_tracks_labelen"
LABELS = OUTPUT / "stap_1_tracks_labelen" / "labels.csv"

# stap 2: elk beeld nakijken
VERDICTS = OUTPUT / "stap_2_beelden_nakijken" / "controle_labels.csv"

# stap 3: de foute beelden verbeteren, en de ground truth (het eindresultaat van het labelen)
STEP3 = OUTPUT / "stap_3_fouten_verbeteren"
CORRECTIONS = STEP3 / "correcties.csv"
GROUND_TRUTH = STEP3 / "ground_truth.csv"
GROUND_TRUTH_PHOTOS = STEP3 / "ground_truth_fotos_en_stills.csv"
