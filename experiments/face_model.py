"""Face detection and FaceNet embeddings, via the deepface library.

All images in this project are OpenCV arrays: uint8, BGR channel order,
shape (height, width, 3).

deepface is imported inside the functions on purpose: importing it loads
TensorFlow, which takes several seconds, and the other modules do not need it.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

import config


@dataclass
class DetectedFace:
    """One face found in an image."""

    crop: np.ndarray   # aligned face crop at native resolution (uint8 BGR)
    x: int             # bounding box of the face in the source image, in pixels
    y: int
    w: int
    h: int
    confidence: float  # detector score in [0, 1]


def detect_faces(image: np.ndarray) -> list[DetectedFace]:
    """Detect and align every face in `image`, largest face first.

    Returns an empty list when no face is found.
    """
    from deepface import DeepFace

    try:
        results = DeepFace.extract_faces(
            img_path=image,
            detector_backend=config.DETECTOR_BACKEND,
            enforce_detection=True,  # raise instead of returning the whole image
            align=True,              # rotate so that the eyes are horizontal
        )
    except ValueError:  # deepface's way of saying "no face found"
        return []

    faces = []
    for result in results:
        if result["confidence"] < config.MIN_FACE_CONFIDENCE:
            continue
        # deepface returns the crop as RGB floats in [0, 1]; convert to uint8 BGR.
        crop_rgb = np.clip(result["face"] * 255.0, 0, 255).round().astype(np.uint8)
        area = result["facial_area"]
        faces.append(
            DetectedFace(
                crop=cv2.cvtColor(crop_rgb, cv2.COLOR_RGB2BGR),
                x=int(area["x"]),
                y=int(area["y"]),
                w=int(area["w"]),
                h=int(area["h"]),
                confidence=float(result["confidence"]),
            )
        )
    faces.sort(key=lambda face: face.w * face.h, reverse=True)
    return faces


def embed(face: np.ndarray) -> np.ndarray:
    """Return the L2-normalised 128-d FaceNet embedding of a face crop.

    `face` must already be a FACE_SIZE x FACE_SIZE crop (see
    image_ops.to_model_input), so deepface does not resize it again and every
    resizing step stays under our control.
    """
    from deepface import DeepFace

    if face.shape[:2] != (config.FACE_SIZE, config.FACE_SIZE):
        raise ValueError(f"expected a {config.FACE_SIZE}x{config.FACE_SIZE} crop, got {face.shape[:2]}")

    result = DeepFace.represent(
        img_path=face,
        model_name=config.MODEL_NAME,
        detector_backend="skip",  # the input is already a cropped, aligned face
        enforce_detection=False,
        align=False,
    )
    vector = np.asarray(result[0]["embedding"], dtype=np.float32)
    return vector / np.linalg.norm(vector)
