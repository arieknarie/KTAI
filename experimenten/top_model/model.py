"""Periskop, het top model: zo krijgt een kader een naam.

1. Elke blik (model, extra ruimte, gespiegeld of niet) geeft per kader de afstand tot het gemiddelde van de voorbeelden van elke persoon.
2. De afstanden van alle blikken worden gemiddeld.
3. Per track en per persoon tellen alleen de beste beelden mee: het deel van de beelden met de kleinste afstand tot die persoon.
4. Per beeld krijgt elke persoon hoogstens één kader.
5. Een track krijgt geen naam als de detector te onzeker is, of als de tweede persoon bijna even dichtbij is.
6. Gaten binnen een track met een naam worden opgevuld met bijgemaakte kaders.

Er worden geen beelden uit de filmpjes als voorbeeld gebruikt: de voorbeelden zijn alleen de foto's en de stills.
"""

import numpy as np
import pandas as pd

from gedeeld.facenet import load_detections, vector_path
from gedeeld.film import fragments
from gedeeld.herkennen import assigned, example_distances, person_distances
from gedeeld.meten import IOU, hit_matrix, overlap
from gedeeld.paden import FRAMES, GROUND_TRUTH, NAMES, VECTORS
from gedeeld.voorbeelden import rows
from tuned.instellingen import example_path


def view_paths(example_set: str, view: tuple) -> tuple:
    """De bestanden met de vectoren van de kaders en de voorbeelden voor een blik. Elk gezicht is lichter gemaakt."""
    model, margin, mirror = view
    if not mirror:
        return vector_path(model, margin, True), example_path(example_set, model, margin, True)
    stem = f"{model}_marge{round(margin * 100)}_licht_spiegel.npy"
    return VECTORS / f"kaders_{stem}", VECTORS / f"voorbeelden_{example_set}_{stem}"


class Data:
    """Alles wat het model en het meten nodig hebben, voor één set voorbeelden."""

    def __init__(self, example_set: str):
        self.example_set = example_set
        self.detections = load_detections()
        self.truth = pd.read_csv(GROUND_TRUTH)
        self.hit = hit_matrix(self.detections, self.truth)
        self.frame_id = self.detections.groupby(["video", "frame"], sort=False).ngroup().to_numpy()
        self.track_id = self.detections.groupby(["video", "track"], sort=False).ngroup().to_numpy()
        self.names = rows(example_set)["persoon"].to_numpy()
        frames = pd.read_csv(FRAMES)
        parts = fragments(frames).set_index("video")
        self.groups = sorted(parts["fragment"].unique(), key=lambda g: int(g.split()[-1]))
        self.part_of_video = {v: self.groups.index(g) for v, g in parts["fragment"].items()}
        self.box_part = self.detections["video"].map(self.part_of_video).to_numpy()
        self.face_part = self.truth["fragment"].map(self.groups.index).to_numpy()
        self.faces = np.bincount(self.face_part, minlength=len(self.groups))
        self.score = pd.Series(self.detections["score"].to_numpy()).groupby(self.track_id).transform("mean").to_numpy()
        frames["shot"] = frames.groupby("video")["cut"].cumsum()
        self.shot = {(v, int(f)): int(s) for v, f, s in zip(frames["video"], frames["frame"], frames["shot"])}
        self.tracks = {t: np.flatnonzero(self.track_id == t) for t in np.unique(self.track_id)}
        self.truth_at = {}
        for i, r in enumerate(self.truth.itertuples()):
            self.truth_at.setdefault((r.bestand, r.beeld, NAMES.index(r.persoon)), []).append((i, (r.x, r.y, r.w, r.h)))
        self._views = {}

    def view(self, view: tuple) -> np.ndarray:
        """De afstand van elk kader tot het gemiddelde van de voorbeelden van elke persoon, voor één blik. Dit wordt één keer uitgerekend."""
        if view not in self._views:
            boxes, refs = view_paths(self.example_set, view)
            self._views[view] = person_distances(np.load(boxes), self.names, np.load(refs), "euclidean_l2", "gemiddelde")
        return self._views[view]

    def distances(self, views: list) -> np.ndarray:
        return np.mean([self.view(tuple(v)) for v in views], axis=0)

    def best_part(self, matrix: np.ndarray, part: float) -> np.ndarray:
        """Per track en per persoon het gemiddelde over het beste deel van de beelden: de beelden met de kleinste afstand."""
        out = matrix.copy()
        for index in self.tracks.values():
            count = max(1, int(round(part * len(index)))) if len(index) >= 4 else len(index)
            out[index] = np.sort(matrix[index], axis=0)[:count].mean(axis=0)
        return out

    def decide(self, settings: dict) -> tuple:
        """Per kader de afstanden per persoon, de persoon (0-3, of -1 als er geen naam is) en de afstand tot die persoon."""
        matrix = self.best_part(self.distances(settings["blikken"]), settings["deel_van_de_track"])
        person, distance = assigned(matrix, self.frame_id, "uniek")
        ordered = np.sort(matrix, axis=1)
        keep = (ordered[:, 1] - ordered[:, 0] >= settings["verschil_met_tweede"]) & (self.score >= settings["zekerheid_detector"])
        return matrix, np.where(keep, person, -1), np.where(keep, distance, np.inf)

    def filled(self, person: np.ndarray, distance: np.ndarray) -> list:
        """Bijgemaakte kaders voor de gaten binnen een track: daar waar de detector een gezicht even kwijt was, tussen twee kaders met dezelfde naam."""
        videos, frames = self.detections["video"].to_numpy(), self.detections["frame"].to_numpy()
        boxes = self.detections[["x", "y", "w", "h"]].to_numpy(dtype=float)
        tracks = self.detections["track"].to_numpy()
        taken = set(zip(videos[person >= 0], frames[person >= 0], person[person >= 0]))
        new = []
        for index in self.tracks.values():
            index = index[person[index] >= 0]
            index = index[np.argsort(frames[index])]
            for a, b in zip(index[:-1], index[1:]):
                video = videos[a]
                if frames[b] - frames[a] > 1 and person[a] == person[b] and self.shot[(video, int(frames[a]))] == self.shot[(video, int(frames[b]))]:
                    for f in range(int(frames[a]) + 1, int(frames[b])):
                        if (video, f, person[a]) not in taken:
                            w = (f - frames[a]) / (frames[b] - frames[a])
                            new.append({"video": video, "frame": f, "track": tracks[a], "bron": a, "persoon": int(person[a]), "afstand": float(distance[a]),
                                        **dict(zip("xywh", boxes[a] * (1 - w) + boxes[b] * w))})
                            taken.add((video, f, person[a]))
        return new

    def with_filled(self, person: np.ndarray, distance: np.ndarray) -> tuple:
        """De personen en afstanden van alle kaders samen met de bijgemaakte kaders, met de ground truth erbij."""
        new = self.filled(person, distance)
        if not new:
            return person, distance, self.hit, self.box_part
        extra = np.full((len(new), len(NAMES)), -1, dtype=np.int32)
        for j, b in enumerate(new):
            for i, face in self.truth_at.get((b["video"], b["frame"], b["persoon"]), []):
                if overlap((b["x"], b["y"], b["w"], b["h"]), face) >= IOU:
                    extra[j, b["persoon"]] = i
        return (np.r_[person, [b["persoon"] for b in new]], np.r_[distance, [b["afstand"] for b in new]], np.vstack([self.hit, extra]),
                np.r_[self.box_part, [self.part_of_video[b["video"]] for b in new]])

    def closest_photo(self, view: tuple, matrix: np.ndarray, person: np.ndarray) -> np.ndarray:
        """Per kader de voorbeeldfoto van de gekozen persoon die het meest op het kader lijkt, volgens de eerste blik."""
        boxes, refs = view_paths(self.example_set, view)
        each = example_distances(np.load(boxes), np.load(refs), "euclidean_l2")
        shown = np.where(person >= 0, person, matrix.argmin(axis=1))
        names = np.array(NAMES, dtype=object)
        index = np.where(self.names[None, :] == names[shown][:, None], each, np.inf).argmin(axis=1)
        return rows(self.example_set)["bestand"].to_numpy()[index]


def sweep(data: Data, person, distance, hit, box_part, thresholds) -> tuple:
    """Per filmpje en per drempel hoeveel gezichten goed zijn en hoeveel kaders een naam op de verkeerde plek hebben (de meting per gezicht)."""
    named = person >= 0
    face = np.full(len(person), -1)
    face[named] = hit[np.flatnonzero(named), person[named]]
    right = face >= 0
    best = np.full(len(data.face_part), np.inf)
    np.minimum.at(best, face[right], distance[right])
    parts = len(data.groups)
    good, wrong = np.zeros((parts, len(thresholds)), dtype=int), np.zeros((parts, len(thresholds)), dtype=int)
    for part in range(parts):
        good[part] = np.searchsorted(np.sort(best[data.face_part == part]), thresholds)
        wrong[part] = np.searchsorted(np.sort(distance[named & ~right & (box_part == part)]), thresholds)
    return good, wrong


def f1(good, wrong, faces):
    return 2 * good / np.maximum(1, 2 * good + wrong + (faces - good))
