"""Van vectoren naar namen: de afstand van elk kader tot elke persoon, en welke naam een kader krijgt."""

import numpy as np
import pandas as pd

from gedeeld.film import fragments
from gedeeld.paden import FRAMES, NAMES, OTHER


def _unit(vectors: np.ndarray) -> np.ndarray:
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


def example_distances(boxes: np.ndarray, refs: np.ndarray, metric: str) -> np.ndarray:
    """De afstand van elk kader tot elk voorbeeld (kaders x voorbeelden), in stukjes, zodat het in het geheugen past."""
    if metric != "euclidean":
        boxes, refs = _unit(boxes), _unit(refs)
    parts = []
    for start in range(0, len(boxes), 2048):
        chunk = boxes[start:start + 2048]
        if metric == "cosine":
            parts.append(1 - chunk @ refs.T)
        else:
            parts.append(np.linalg.norm(chunk[:, None, :] - refs[None, :, :], axis=2))
    return np.concatenate(parts).astype(np.float32)


def person_distances(boxes: np.ndarray, names: np.ndarray, refs: np.ndarray, metric: str, per_person: str) -> np.ndarray:
    """De afstand van elk kader tot elk van de vier personen (kaders x 4): tot het dichtstbijzijnde voorbeeld van die
    persoon, of tot het gemiddelde van de voorbeelden van die persoon."""
    result = np.empty((len(boxes), len(NAMES)), dtype=np.float32)
    if per_person == "dichtstbij":
        d = example_distances(boxes, refs, metric)
        for k, name in enumerate(NAMES):
            result[:, k] = d[:, names == name].min(axis=1)
        return result
    unit_refs = refs if metric == "euclidean" else _unit(refs)
    for k, name in enumerate(NAMES):
        own = unit_refs[names == name].mean(axis=0, keepdims=True)
        result[:, k] = example_distances(boxes, own if metric == "euclidean" else _unit(own), metric)[:, 0]
    return result


def by_track(d: np.ndarray, track_id: np.ndarray) -> np.ndarray:
    """Per track één beslissing: elk kader krijgt de gemiddelde afstand van alle kaders in zijn track."""
    total = np.zeros((track_id.max() + 1, d.shape[1]), dtype=np.float64)
    np.add.at(total, track_id, d)
    count = np.bincount(track_id)[:, None]
    return (total / count)[track_id].astype(np.float32)


def assigned(d: np.ndarray, frame_id: np.ndarray, assign: str) -> tuple:
    """Per kader de persoon die FaceNet kiest (0-3, of -1 als er geen persoon overblijft) en de afstand. "los": elk kader
    kiest zelf. "uniek": per beeld krijgt elke persoon hoogstens één kader, de kaders met de kleinste afstand eerst."""
    if assign == "los":
        k = d.argmin(axis=1)
        return k, d[np.arange(len(d)), k]
    person, dist = np.full(len(d), -1), np.full(len(d), np.inf, dtype=np.float32)
    boxes, people = np.unravel_index(np.argsort(d, axis=None), d.shape)
    order = np.lexsort((d[boxes, people], frame_id[boxes]))   # per beeld, kleinste afstand eerst
    used_box, used_person, current = set(), set(), -1
    for b, p in zip(boxes[order], people[order]):
        f = frame_id[b]
        if f != current:
            current, used_box, used_person = f, set(), set()
        if b in used_box or p in used_person:
            continue
        used_box.add(b)
        used_person.add(p)
        person[b], dist[b] = p, d[b, p]
    return person, dist


def predictions(detections: pd.DataFrame, nearest: np.ndarray, distance: np.ndarray, threshold: float,
                photo: np.ndarray) -> pd.DataFrame:
    """De tabel met voorspellingen. `nearest` is de naam van de dichtstbijzijnde persoon, `photo` de voorbeeldfoto die de
    doorslag gaf. Is de afstand kleiner dan de drempel, dan krijgt het kader die naam; anders is het "iemand anders"."""
    parts = fragments(pd.read_csv(FRAMES)).set_index("video")
    return pd.DataFrame({
        "fragment": detections["video"].map(parts["fragment"]),
        "bestand": detections["video"],
        "beeld": detections["frame"],
        "tijd_s": (detections["time_s"] + detections["video"].map(parts["offset"])).round(3),
        "track": detections["track"], "x": detections["x"], "y": detections["y"], "w": detections["w"], "h": detections["h"],
        "facenet": np.where(distance < threshold, nearest, OTHER),
        "dichtstbij": nearest,
        "afstand": np.round(distance, 4),
        "foto": photo,
    })
