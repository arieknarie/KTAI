"""Wat er bij het afstellen geprobeerd wordt. Alle stappen van tuned halen hun instellingen hier vandaan."""

import json
from pathlib import Path

MODELS = ["Facenet", "Facenet512"]                   # 128 of 512 getallen per gezicht
MARGINS = [0.0, 0.1, 0.2, 0.3]                       # hoeveel extra ruimte aan elke kant van het kader
LIGHT = [False, True]                                # een donker gezicht eerst lichter maken
METRICS = ["euclidean_l2", "cosine", "euclidean"]    # de afstanden van deepface; bij gelijke uitkomst wint de eerste
PER_PERSON = ["dichtstbij", "gemiddelde"]            # afstand tot de meest gelijkende foto, of tot het gemiddelde van de foto's
ASSIGN = ["los", "uniek"]                            # elk kader los, of per beeld elke persoon hoogstens één keer
DECIDE = ["kader", "track"]                          # per kader beslissen, of per track (gemiddelde afstand van de hele track)
THRESHOLDS = 200                                     # zoveel drempels worden per instelling geprobeerd
SETS = ["fotos", "fotos_en_kostuum", "alleen_kostuum"]

TUNED = Path(__file__).resolve().parent
KEYS = ["model", "marge", "lichter", "afstand", "per_persoon", "toewijzen", "beslissen"]


def folder(example_set: str) -> Path:
    """De map met de uitkomsten van een set voorbeelden. De set "alleen_kostuum" hoort bij een eigen experiment."""
    if example_set == "alleen_kostuum":
        return TUNED.parent / "alleen_in_karakter" / "resultaten_tuned"
    return TUNED / "resultaten" / example_set


def example_path(example_set: str, model: str, margin: float, light: bool) -> Path:
    return TUNED.parent / "tussenbestanden" / f"voorbeelden_{example_set}_{model}_marge{round(margin * 100)}{'_licht' if light else ''}.npy"


def winner(example_set: str) -> dict:
    return json.loads((folder(example_set) / "beste_instelling.json").read_text(encoding="utf-8"))
