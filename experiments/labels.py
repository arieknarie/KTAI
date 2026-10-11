"""Reading and writing data/labels.csv: one row per detected face.

Columns
    face_id          unique id, e.g. "inCharacter/Johann/johann7_jpg_f2"
                     (face number 2 in johann7.jpg)
    crop_path        face crop, relative to the experiments folder
    source           "personal", "inCharacter" or "movie"
    source_path      original picture or movie, relative to the repository
    frame_time_s     time in the movie (empty for pictures)
    x, y, w, h       bounding box of the face in the source, in pixels
    confidence       face detector score
    brightness       mean grey value of the face crop (0-255)
    label            identity of the face (see config.IDENTITIES),
                     config.OTHER_LABEL, or empty = not used
    label_source     "filename" (filled in automatically), "visual" (checked
                     by eye on the detection images), "quiz" or "manual"

Labels are filled in automatically only when it is unambiguous: the file
name of a picture names exactly one person, and exactly one face was found
in it. All other faces (group pictures, pictures with extras in the
background, movie frames) are labelled by hand or with label_quiz.py.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

import config
from image_ops import match_boxes

COLUMNS = [
    "face_id", "crop_path", "source", "source_path", "frame_time_s",
    "x", "y", "w", "h", "confidence", "brightness", "label", "label_source",
]
VALID_LABELS = set(config.IDENTITIES) | {config.OTHER_LABEL}

# Old and new detections of the same face overlap at least this much.
SAME_FACE_OVERLAP = 0.5


def identities_in_filename(path: Path) -> set[str]:
    """Who is in a picture according to its file name.

    "alte_and_werner2.png" -> {"DerAlte", "Werner"}; "derAlte1.jpeg" -> {"DerAlte"}.
    """
    words = re.findall(r"[a-z]+", path.stem.lower())
    return {config.NAME_TOKENS[word] for word in words if word in config.NAME_TOKENS}


def load_labels() -> pd.DataFrame:
    """Load labels.csv and check that every filled-in label is valid."""
    if not config.LABELS_CSV.exists():
        raise FileNotFoundError(f"{config.LABELS_CSV} not found; run prepare_faces.py first")
    faces = pd.read_csv(config.LABELS_CSV, dtype={"label": str, "label_source": str})
    faces[["label", "label_source"]] = faces[["label", "label_source"]].fillna("")
    faces["label"] = faces["label"].str.strip()

    invalid = sorted(set(faces["label"]) - VALID_LABELS - {""})
    if invalid:
        raise ValueError(
            f"invalid label(s) in {config.LABELS_CSV.name}: {invalid}; "
            f"use one of {sorted(VALID_LABELS)} or leave the cell empty"
        )
    return faces


def save_labels(faces: pd.DataFrame) -> None:
    config.LABELS_CSV.parent.mkdir(parents=True, exist_ok=True)
    faces[COLUMNS].to_csv(config.LABELS_CSV, index=False)


def _boxes(faces: pd.DataFrame) -> list:
    return faces[["x", "y", "w", "h"]].to_numpy(dtype=float).tolist()


def keep_manual_labels(new: pd.DataFrame, old: pd.DataFrame) -> pd.DataFrame:
    """Copy labels that were filled in by hand from `old` into `new`.

    Faces are matched by the overlap of their boxes within the same picture
    (or movie frame), not by face number: after an update of the detector the
    numbering can change, and a label must never move to another face.
    Automatic labels ("filename") are not copied; they are recomputed.
    Labelled faces that cannot be found again are reported and dropped.
    """
    old = old[(old["label"] != "") & (old["label_source"] != "filename")]
    frame = ["source_path", "frame_time_s"]
    for key, old_faces in old.groupby(frame, dropna=False, sort=False):
        in_frame = (new["source_path"] == key[0]) & (
            new["frame_time_s"].isna() if pd.isna(key[1]) else new["frame_time_s"] == key[1])
        new_faces = new[in_frame]
        matches = match_boxes(_boxes(new_faces), _boxes(old_faces), SAME_FACE_OVERLAP)
        for position, row in enumerate(old_faces.itertuples()):
            if position not in matches:
                print(f"  warning: labelled face {row.face_id} ({row.label}) not found again; label dropped")
                continue
            target = new_faces.index[matches[position]]
            new.loc[target, ["label", "label_source"]] = [row.label, row.label_source or "manual"]
    return new
