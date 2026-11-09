"""Het getunde model voor de losse experimenten.

Elk los experiment kan draaien met FaceNet standaard of met het getunde model: de beste instellingen uit experimenten/tuned.
De uitkomsten staan in de map resultaten/ (standaard) en resultaten_tuned/ (getuned) van dat experiment.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from gedeeld.facenet import vector_path
from gedeeld.herkennen import assigned, by_track, example_distances, person_distances, predictions
from gedeeld.paden import EXPERIMENTEN, NAMES
from gedeeld.voorbeelden import rows
from tuned.instellingen import example_path, folder as tuned_folder, winner

OUTPUT = {"standaard": "resultaten", "tuned": "resultaten_tuned"}     # de map met uitkomsten, per model


def model_choice() -> str:
    """Welk model dit experiment gebruikt: --model standaard (dat is de standaard) of --model tuned."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=OUTPUT, default="standaard", help="FaceNet standaard of het getunde model")
    return parser.parse_args().model


def results_of(model: str, example_set: str) -> Path:
    """De map met de uitkomsten van FaceNet voor een set voorbeelden, met dit model."""
    if model == "tuned":
        return tuned_folder(example_set)
    if example_set == "alleen_kostuum":
        return EXPERIMENTEN / "alleen_in_karakter" / "resultaten"
    return EXPERIMENTEN / "basis" / "resultaten" / example_set


class Tuned:
    """Herkennen met de instellingen van het getunde model, voor een set voorbeelden. Met `settings_of` gebruik je de instellingen van
    een andere set voorbeelden."""

    def __init__(self, example_set: str, detections: pd.DataFrame, settings_of: str = None):
        self.settings = winner(settings_of or example_set)
        s = self.settings
        self.table = rows(example_set)
        self.names = self.table["persoon"].to_numpy()
        self.photos = self.table["bestand"].to_numpy()
        self.detections = detections
        self.boxes = np.load(vector_path(s["model"], s["marge"], s["lichter"]))
        self.refs = np.load(example_path(example_set, s["model"], s["marge"], s["lichter"]))
        self.frame_id = detections.groupby(["video", "frame"], sort=False).ngroup().to_numpy()
        self.track_id = detections.groupby(["video", "track"], sort=False).ngroup().to_numpy()
        self.threshold = s["drempel"]
        self._each = None

    def each(self) -> np.ndarray:
        """De afstand van elk kader tot elk voorbeeld. Dit wordt één keer uitgerekend."""
        if self._each is None:
            self._each = example_distances(self.boxes, self.refs, self.settings["afstand"])
        return self._each

    def person_matrix(self, active=None, per_person: str = None) -> np.ndarray:
        """De afstand van elk kader tot elk van de vier personen, met alleen de voorbeelden in `active` (zonder `active`: alle voorbeelden)."""
        active = np.arange(len(self.names)) if active is None else np.asarray(active)
        how = per_person or self.settings["per_persoon"]
        if how == "dichtstbij":
            names, part = self.names[active], self.each()[:, active]
            return np.column_stack([part[:, names == person].min(axis=1) for person in NAMES])
        return person_distances(self.boxes, self.names[active], self.refs[active], self.settings["afstand"], how)

    def decide(self, matrix: np.ndarray) -> tuple:
        """Per kader de persoon (0-3, of -1 als er geen persoon overblijft) en de afstand. Geeft ook de afstanden terug waarop besloten is."""
        if self.settings["beslissen"] == "track":
            matrix = by_track(matrix, self.track_id)
        person, distance = assigned(matrix, self.frame_id, self.settings["toewijzen"])
        return matrix, person, distance

    def found(self, matrix: np.ndarray, person: np.ndarray, distance: np.ndarray, threshold: float) -> pd.DataFrame:
        """De tabel met voorspellingen, met dezelfde kolommen als bij de basis."""
        names = np.array(NAMES, dtype=object)
        shown = np.where(person >= 0, person, matrix.argmin(axis=1))     # voor een kader zonder persoon: de dichtstbijzijnde persoon
        index = np.where(self.names[None, :] == names[shown][:, None], self.each(), np.inf).argmin(axis=1)
        table = predictions(self.detections, names[shown], distance, threshold, self.photos[index])
        table["afstand"] = table["afstand"].where(np.isfinite(table["afstand"]))
        return table
