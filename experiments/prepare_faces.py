"""Step 1: detect all faces and write data/labels.csv.

Detects the faces in pictures/personal and pictures/inCharacter (and, with
--movies, in one frame per second of every clip in movies/), saves every face
crop in data/faces/ and lists them in data/labels.csv.

Faces that cannot be labelled automatically (group pictures, movie frames)
get an empty label; fill those in by hand afterwards (see README.md).
Running this script again keeps all labels that were already filled in.

Usage:
    python prepare_faces.py            # pictures only
    python prepare_faces.py --movies   # pictures and movie frames
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
from pathlib import Path

import cv2
import pandas as pd

import config
import labels
from face_model import DetectedFace, detect_faces
from image_ops import brightness, difference_hash, hamming_distance, read_image
from intermediate import annotate_detections, save_image

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")


def face_row(face: DetectedFace, face_id: str, source: str, source_path: Path,
             frame_time_s: float | None = None) -> dict:
    """Save the crop of one face and return its row for labels.csv."""
    crop_path = config.FACES_DIR / f"{face_id}.png"
    crop_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(crop_path), face.crop)
    return {
        "face_id": face_id,
        "crop_path": crop_path.relative_to(config.EXPERIMENTS_DIR).as_posix(),
        "source": source,
        "source_path": source_path.relative_to(config.REPO_ROOT).as_posix(),
        "frame_time_s": frame_time_s,
        "x": face.x, "y": face.y, "w": face.w, "h": face.h,
        "confidence": round(face.confidence, 4),
        "brightness": round(brightness(face.crop), 1),
        "label": "",
        "label_source": "",
    }


def process_pictures() -> list[dict]:
    """Detect faces in all pictures; label single-person pictures automatically."""
    rows = []
    seen_files: dict[str, Path] = {}     # file content hash -> first file with that content
    seen_pictures: dict[int, Path] = {}  # perceptual hash of the picture -> first file
    for source, folder in (("personal", config.PERSONAL_DIR), ("inCharacter", config.IN_CHARACTER_DIR)):
        for path in sorted(folder.glob("*/*")):
            if path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            # The same file is sometimes stored in two person folders; using
            # it twice would let a picture be compared with its own copy.
            content_hash = hashlib.md5(path.read_bytes()).hexdigest()
            if content_hash in seen_files:
                print(f"  skip {path.relative_to(config.REPO_ROOT)} (same file as "
                      f"{seen_files[content_hash].relative_to(config.REPO_ROOT)})")
                continue
            seen_files[content_hash] = path

            # A still saved again at another size is a copy as well.
            image = read_image(path)
            picture_hash = difference_hash(image)
            copy_of = next((first for value, first in seen_pictures.items()
                            if hamming_distance(value, picture_hash) <= config.DUPLICATE_PICTURE_DISTANCE), None)
            if copy_of is not None:
                print(f"  skip {path.relative_to(config.REPO_ROOT)} (near-identical to "
                      f"{copy_of.relative_to(config.REPO_ROOT)})")
                continue
            seen_pictures[picture_hash] = path

            faces = detect_faces(image)
            names = labels.identities_in_filename(path)
            # The extension is part of the name: werner4.jpg and werner4.png both exist.
            name = f"{path.stem}_{path.suffix.lstrip('.').lower()}"
            print(f"  {path.relative_to(config.REPO_ROOT)}: {len(faces)} face(s)")
            for index, face in enumerate(faces):
                face_id = f"{source}/{path.parent.name}/{name}_f{index}"
                row = face_row(face, face_id, source, path)
                # Only when unambiguous: one person named in the file name and
                # exactly one face found. (The largest face is not reliable: in
                # johann7.jpg it is an extra in the foreground.)
                if len(names) == 1 and len(faces) == 1:
                    row["label"], row["label_source"] = next(iter(names)), "filename"
                rows.append(row)
            save_detections(image, rows[len(rows) - len(faces):],
                            f"{source}/{path.parent.name}/{name}.jpg")
    return rows


def save_detections(image, rows: list[dict], name: str) -> None:
    """Intermediate result: the source image with a numbered box per face.

    The number (f0, f1, ...) matches the end of the face_id in labels.csv,
    which makes labelling group pictures and movie frames easy.
    """
    boxes = [((row["x"], row["y"], row["w"], row["h"]),
              f"{row['face_id'].rsplit('_', 1)[-1]} {row['label'] or '?'}") for row in rows]
    save_image(annotate_detections(image, boxes), config.INTERMEDIATE_DIR / "detections" / name)


def slug(text: str) -> str:
    """File-system friendly version of a movie name."""
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")


def process_movies() -> list[dict]:
    """Detect faces in one frame per MOVIE_SAMPLE_SECONDS of every movie clip."""
    rows = []
    for path in sorted(config.MOVIES_DIR.iterdir()):
        if path.suffix.lower() not in config.MOVIE_EXTENSIONS:
            continue
        video = cv2.VideoCapture(str(path))
        fps = video.get(cv2.CAP_PROP_FPS) or 25.0
        step = max(1, round(fps * config.MOVIE_SAMPLE_SECONDS))
        found = sampled = frame_index = 0
        while True:
            ok, frame = video.read()
            if not ok:
                break
            if frame_index % step == 0:
                sampled += 1
                time_s = frame_index / fps
                faces = detect_faces(frame)
                for index, face in enumerate(faces):
                    face_id = f"movie/{slug(path.stem)}/t{time_s:07.1f}_f{index}"
                    rows.append(face_row(face, face_id, "movie", path, round(time_s, 2)))
                    found += 1
                if faces:
                    save_detections(frame, rows[len(rows) - len(faces):],
                                    f"movie/{slug(path.stem)}/t{time_s:07.1f}.jpg")
            frame_index += 1
        video.release()
        print(f"  {path.name}: {found} face(s) in {sampled} sampled frames")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--movies", action="store_true", help="also detect faces in the movie clips")
    args = parser.parse_args()

    sources = ["personal", "inCharacter"] + (["movie"] if args.movies else [])
    old = labels.load_labels() if config.LABELS_CSV.exists() else pd.DataFrame(columns=labels.COLUMNS)

    # Crops and detection images of the sources processed now are rebuilt from scratch.
    for source in sources:
        shutil.rmtree(config.FACES_DIR / source, ignore_errors=True)
        shutil.rmtree(config.INTERMEDIATE_DIR / "detections" / source, ignore_errors=True)

    print("Detecting faces in pictures ...")
    rows = process_pictures()
    if args.movies:
        print("Detecting faces in movie frames ...")
        rows += process_movies()

    new = pd.DataFrame(rows, columns=labels.COLUMNS)
    # Rows of sources that were not processed now (e.g. movies) are kept as they are.
    untouched = old[~old["source"].isin(sources)]
    faces = pd.concat([untouched, new], ignore_index=True)
    faces = labels.keep_manual_labels(faces, old)
    labels.save_labels(faces)

    unlabelled = faces[faces["label"] == ""]
    print(f"\nWrote {len(faces)} faces to {config.LABELS_CSV.relative_to(config.REPO_ROOT)}")
    print(faces.groupby("source").size().to_string())
    print(f"{len(unlabelled)} face(s) still need a manual label (empty 'label' column).")


if __name__ == "__main__":
    main()
