"""Intermediate results as images, so every processing step can be checked by eye.

Written to results/intermediate/:
    detections/            every picture with a numbered box per detected face
    gallery_overview*.jpg  all reference faces exactly as FaceNet receives them
    stress_test_*/         one sheet per still: the still under every condition
                           of the stress test, side by side, with a box and a
                           name for every face the system found

Colours of the boxes on the sheets:
    green   a named person, recognised correctly
    red     a wrong name (a named person mixed up, or an extra given a name)
    grey    "unknown": rejected because no reference was close enough
    orange  a named person the face detector did not find at all

Drawing is done with OpenCV, so only ASCII text is used.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

import config

TILE = config.FACE_SIZE   # face tiles are shown at model-input size
CAPTION_HEIGHT = 34       # white band below a tile with two lines of text
THUMBNAIL_WIDTH = 420     # width of a still on a stress-test sheet
ROW_TITLE_WIDTH = 200     # space for the row titles on the left of a sheet
HEADER_HEIGHT = 26        # space for the column titles above a sheet
GAP = 6                   # white space between tiles

# Colours in BGR order.
WHITE = (255, 255, 255)
INK = (11, 11, 11)
INK_SECONDARY = (78, 81, 82)
CORRECT = (0, 131, 0)        # green
WRONG = (72, 73, 227)        # red
REJECTED = (150, 150, 150)   # grey
MISSED = (0, 140, 255)       # orange
FONT = cv2.FONT_HERSHEY_SIMPLEX

OUTCOME_COLOURS = {
    "correct": CORRECT,
    "wrong": WRONG,
    "false_identity": WRONG,
    "rejected": REJECTED,
    "missed": MISSED,
}


def save_image(image: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), image, [cv2.IMWRITE_JPEG_QUALITY, 90])


def _text(image: np.ndarray, text: str, origin: tuple[int, int], scale: float = 0.42,
          color=INK, thickness: int = 1) -> None:
    cv2.putText(image, text, origin, FONT, scale, color, thickness, cv2.LINE_AA)


def _labelled_box(image: np.ndarray, box, text: str, color, scale: float, thickness: int) -> None:
    """Rectangle with a small white label above it."""
    x, y, w, h = (int(round(v)) for v in box)
    cv2.rectangle(image, (x, y), (x + w, y + h), color, thickness)
    (text_w, text_h), _ = cv2.getTextSize(text, FONT, scale, 1)
    label_y = max(y - 3, text_h + 3)
    cv2.rectangle(image, (x, label_y - text_h - 3), (x + text_w + 4, label_y + 2), WHITE, -1)
    _text(image, text, (x + 2, label_y - 1), scale=scale, color=color if color != REJECTED else INK)


def tile(image: np.ndarray, lines: list[str]) -> np.ndarray:
    """A face at model-input size with up to two caption lines below it."""
    face = cv2.resize(image, (TILE, TILE), interpolation=cv2.INTER_NEAREST)
    caption = np.full((CAPTION_HEIGHT, TILE, 3), WHITE, dtype=np.uint8)
    for index, line in enumerate(lines[:2]):
        _text(caption, line, (4, 14 + 16 * index), color=INK if index == 0 else INK_SECONDARY)
    return np.vstack([face, caption])


def sheet(cells: list[list[np.ndarray | None]], row_titles: list[str], column_titles: list[str],
          title: str) -> np.ndarray:
    """Arrange images in a grid with a title, row titles and column titles."""
    present = [cell for row in cells for cell in row if cell is not None]
    cell_height = max(cell.shape[0] for cell in present)
    cell_width = max(cell.shape[1] for cell in present)
    n_rows, n_cols = len(cells), max(len(row) for row in cells)
    top = 30 + HEADER_HEIGHT
    height = top + n_rows * (cell_height + GAP)
    width = ROW_TITLE_WIDTH + n_cols * (cell_width + GAP)
    canvas = np.full((height, width, 3), WHITE, dtype=np.uint8)

    _text(canvas, title, (8, 20), scale=0.55)
    for col, column_title in enumerate(column_titles):
        _text(canvas, column_title, (ROW_TITLE_WIDTH + col * (cell_width + GAP) + 4, top - 8),
              color=INK_SECONDARY)
    for row_index, (row, row_title) in enumerate(zip(cells, row_titles)):
        y = top + row_index * (cell_height + GAP)
        _text(canvas, row_title, (8, y + 20), color=INK_SECONDARY)
        for col, cell in enumerate(row):
            if cell is not None:
                x = ROW_TITLE_WIDTH + col * (cell_width + GAP)
                canvas[y:y + cell.shape[0], x:x + cell.shape[1]] = cell
    return canvas


def annotate_detections(image: np.ndarray, faces: list[tuple[tuple[int, int, int, int], str]]) -> np.ndarray:
    """Draw a numbered box and label for every detected face on a copy of `image`."""
    canvas = image.copy()
    thickness = max(2, round(max(image.shape[:2]) / 400))
    scale = max(0.5, max(image.shape[:2]) / 1200)
    for box, text in faces:
        _labelled_box(canvas, box, text, CORRECT, scale, thickness)
    return canvas


def gallery_overview(faces, images: dict[str, np.ndarray], title: str) -> np.ndarray:
    """All reference faces, one row per identity."""
    rows, titles = [], []
    for identity in config.IDENTITIES:
        subset = faces[faces["label"] == identity]
        rows.append([tile(images[face_id], [source, face_id.split("/")[-1][:20]])
                     for face_id, source in zip(subset["face_id"], subset["source"])])
        titles.append(f"{identity} ({len(subset)})")
    width = max((len(row) for row in rows), default=1)
    rows = [row + [None] * (width - len(row)) for row in rows]
    return sheet(rows, titles, [], title)


def scene_thumbnail(frame: np.ndarray, rows: list[dict]) -> np.ndarray:
    """The still as the system saw it, with every face and its outcome.

    `rows` are the result rows of one still under one condition (see
    run_stress_tests.evaluate_scene); each has a box, a prediction and an outcome.
    """
    factor = THUMBNAIL_WIDTH / frame.shape[1]
    height = max(1, round(frame.shape[0] * factor))
    thumb = cv2.resize(frame, (THUMBNAIL_WIDTH, height), interpolation=cv2.INTER_AREA)
    for row in rows:
        if row["box"] is None:
            continue
        box = [value * factor for value in row["box"]]
        if row["outcome"] == "missed":
            text = f"missed: {row['true_label']}"
        elif row["predicted_label"] == config.UNKNOWN:
            text = f"? {row['distance']:.2f}"
        else:
            text = f"{row['predicted_label']} {row['distance']:.2f}"
        _labelled_box(thumb, box, text, OUTCOME_COLOURS[row["outcome"]], 0.35, 1)

    named = [row for row in rows if row["true_label"] in config.IDENTITIES]
    found = sum(row["outcome"] == "correct" for row in named)
    false_names = sum(row["outcome"] in ("wrong", "false_identity") for row in rows)
    detected = sum(row["detected"] for row in rows)
    caption = np.full((CAPTION_HEIGHT, THUMBNAIL_WIDTH, 3), WHITE, dtype=np.uint8)
    _text(caption, f"recognised {found}/{len(named)}   wrong names {false_names}", (4, 14))
    _text(caption, f"faces found {detected}", (4, 30), color=INK_SECONDARY)
    return np.vstack([thumb, caption])


class SceneSheets:
    """Collects the annotated stills and writes one sheet per still and stress test."""

    def __init__(self) -> None:
        # (experiment, picture) -> {(variant, mitigation, level): thumbnail}
        self.cells: dict[tuple[str, str], dict] = defaultdict(dict)

    def add(self, experiment: str, picture: str, key: tuple, thumbnail: np.ndarray) -> None:
        self.cells[(experiment, picture)][key] = thumbnail

    def write(self) -> None:
        for (experiment, picture), cells in self.cells.items():
            name = picture.replace("/", "__") + ".jpg"
            if experiment == "resolution":
                rows = [("downscaled", method) for method in config.UPSCALE_METHODS]
                image = self._grid(cells, rows, config.IMAGE_SCALES, lambda v, m: m,
                                   lambda scale: f"scale 1/{round(1 / scale)}", picture)
                save_image(image, config.INTERMEDIATE_DIR / "stress_test_1_resolution" / name)
            elif experiment == "lighting":
                rows = [(lighting, m) for lighting in config.LIGHTING_TYPES for m in ("none", "clahe")]
                image = self._grid(cells, rows, config.LIGHTING_SEVERITIES, lambda v, m: f"{v} / {m}",
                                   lambda severity: f"severity {severity}", picture)
                save_image(image, config.INTERMEDIATE_DIR / "stress_test_3_lighting" / name)
            else:
                keys = list(cells)
                image = sheet([[cells[key] for key in keys]], [""], [key[1] for key in keys], picture)
                save_image(image, config.INTERMEDIATE_DIR / "stress_test_2_appearance" / name)

    @staticmethod
    def _grid(cells, row_keys, levels, row_title, column_title, title) -> np.ndarray:
        rows = [[cells.get((variant, mitigation, level)) for level in levels]
                for variant, mitigation in row_keys]
        return sheet(rows, [row_title(v, m) for v, m in row_keys], [column_title(level) for level in levels], title)
