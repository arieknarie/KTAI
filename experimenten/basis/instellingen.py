"""De standaardinstellingen van FaceNet in dit experiment. Alle stappen halen hun instellingen hier vandaan.

FaceNet staat standaard ingesteld: het model en de drempel zoals deepface (de programmacode waarmee we FaceNet draaien) die
zelf gebruikt, met de genormaliseerde Euclidische afstand die de opdracht voorschrijft.
"""

from pathlib import Path

from gedeeld.paden import EXPERIMENTEN

MODEL = "Facenet"        # de standaardversie van FaceNet in deepface: 128 getallen per gezicht
MARGIN = 0.0             # het kader precies zoals de detector het vond, zonder extra ruimte eromheen
METRIC = "euclidean_l2"  # de genormaliseerde Euclidische afstand
DREMPEL = 0.80           # de grens die deepface voor FaceNet met deze afstand gebruikt
SETS = ["fotos", "fotos_en_kostuum"]

BASIS = Path(__file__).resolve().parent


def folder(example_set: str) -> Path:
    """De map met de uitkomsten van een set voorbeelden. De set "alleen_kostuum" hoort bij een eigen experiment."""
    if example_set == "alleen_kostuum":
        return EXPERIMENTEN / "alleen_in_karakter" / "resultaten"
    return BASIS / "resultaten" / example_set
