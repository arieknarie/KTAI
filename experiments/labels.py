"""Reading and writing data/labels.csv: one row per detected face.

Columns
    face_id          unique id, e.g. "inCharacter/Johann/johann3_f0"
    crop_path        face crop, relative to the experiments folder
    source           "personal", "inCharacter" or "movie"
    source_path      original picture or movie, relative to the repository
    frame_time_s     time in the movie (empty for pictures)
    x, y, w, h       bounding box of the face in the source, in pixels
    confidence       face detector score
    brightness       mean grey value of the face crop (0-255)
    face_hash        perceptual hash of the crop (hex), see image_ops
    duplicate_group  faces with the same value are copies of each other
    label            identity of the face (see config.IDENTITIES),
                     config.OTHER_LABEL, or empty = not labelled yet
    label_source     "filename" (filled in automatically) or "manual"

Labels are filled in automatically only when it is unambiguous: the file
name of a picture names exactly one person, and exactly one face was found
in it. All other faces (group pictures, pictures with extras in the
background, movie frames) must be labelled by hand by typing a name in the
"label" column.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

import config
from image_ops import hamming_distance

COLUMNS = [
    "face_id", "crop_path", "source", "source_path", "frame_time_s",
    "x", "y", "w", "h", "confidence", "brightness",
    "face_hash", "duplicate_group", "label", "label_source",
]
VALID_LABELS = set(config.IDENTITIES) | {config.OTHER_LABEL}


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
    faces = pd.read_csv(config.LABELS_CSV, dtype={"label": str, "label_source": str, "face_hash": str})
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


def keep_manual_labels(new: pd.DataFrame, old: pd.DataFrame) -> pd.DataFrame:
    """Copy labels that were already filled in from `old` into `new`.

    This way, running prepare_faces.py again never throws away manual work.
    A label typed by hand without a label_source is marked as "manual".
    """
    filled = old[old["label"] != ""].set_index("face_id")
    for column in ("label", "label_source"):
        previous = new["face_id"].map(filled[column])
        new[column] = previous.where(previous.notna(), new[column])
    new.loc[(new["label"] != "") & (new["label_source"] == ""), "label_source"] = "manual"
    return new


def assign_duplicate_groups(faces: pd.DataFrame) -> pd.DataFrame:
    """Give near-identical face crops the same duplicate_group.

    Each face is compared with the first face of every existing group; it
    joins the first group whose hash is close enough, otherwise it starts a
    new group named after its own face_id.
    """
    representatives: list[tuple[int, str]] = []  # (hash, group name)
    groups = []
    for face_id, face_hash in zip(faces["face_id"], faces["face_hash"]):
        value = int(face_hash, 16)
        for representative_hash, group in representatives:
            if hamming_distance(value, representative_hash) <= config.DUPLICATE_HASH_DISTANCE:
                groups.append(group)
                break
        else:
            representatives.append((value, face_id))
            groups.append(face_id)
    faces["duplicate_group"] = groups
    return faces
