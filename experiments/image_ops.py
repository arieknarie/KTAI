"""Image operations: model-input preparation, degradations and mitigations.

Degradations (what the stress tests simulate, applied to the whole still):
    reduce_resolution   -- Stress Test 1: faces far away / a low-resolution camera
    simulate_low_light  -- Stress Test 3: a dark submarine / red alarm light

Mitigations (what the stress tests evaluate as a fix):
    reduce_resolution(method=...) -- Stress Test 1: interpolation when upscaling
    apply_clahe                   -- Stress Test 3: local contrast enhancement

All functions take and return uint8 BGR images and never modify their input.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

import config

# OpenCV flags for the upscaling methods named in config.UPSCALE_METHODS.
INTERPOLATION = {
    "nearest": cv2.INTER_NEAREST,   # repeats pixels: no interpolation at all
    "bilinear": cv2.INTER_LINEAR,
    "bicubic": cv2.INTER_CUBIC,
    "lanczos": cv2.INTER_LANCZOS4,
}


def read_image(path: Path) -> np.ndarray:
    """Read an image from disk as uint8 BGR (an alpha channel is dropped)."""
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise OSError(f"cannot read image: {path}")
    return image


def to_model_input(face: np.ndarray, upscale: str = "bicubic") -> np.ndarray:
    """Turn a face crop of any size into a FACE_SIZE x FACE_SIZE model input.

    The crop is first padded with black to a square, so the face is not
    stretched. Shrinking uses area averaging; enlarging a face that is
    smaller than the model input uses the `upscale` method.
    """
    height, width = face.shape[:2]
    side = max(height, width)
    top, left = (side - height) // 2, (side - width) // 2
    square = cv2.copyMakeBorder(
        face, top, side - height - top, left, side - width - left,
        cv2.BORDER_CONSTANT, value=(0, 0, 0),
    )
    size = config.FACE_SIZE
    interpolation = cv2.INTER_AREA if side >= size else INTERPOLATION[upscale]
    return cv2.resize(square, (size, size), interpolation=interpolation)


def reduce_resolution(image: np.ndarray, scale: float, method: str) -> np.ndarray:
    """Shrink a still by `scale`, then enlarge it to its original size again.

    Area averaging mimics a camera that captures the scene with fewer pixels
    (every face becomes `scale` times as wide). Enlarging it again with
    `method` is the mitigation: "nearest" repeats pixels, the others
    interpolate. Detection, alignment and recognition all see the result.
    """
    if scale >= 1:
        return image.copy()
    height, width = image.shape[:2]
    small_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    small = cv2.resize(image, small_size, interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (width, height), interpolation=INTERPOLATION[method])


def simulate_low_light(
    picture: np.ndarray, severity: float, lighting: str, rng: np.random.Generator
) -> np.ndarray:
    """Simulate poor submarine lighting with a strength `severity` in [0, 1].

    lighting = "dark":      less exposure, crushed shadows and sensor noise.
    lighting = "red_alarm": the same, but lit by red light, so colour
                            information is lost and only red remains.
    """
    if lighting not in config.LIGHTING_TYPES:
        raise ValueError(f"unknown lighting type: {lighting}")
    image = picture.astype(np.float32) / 255.0

    if lighting == "red_alarm":
        # Under (nearly) monochromatic red light only the brightness of the
        # scene is visible, and it is seen through red. Blend towards that.
        gray = cv2.cvtColor(picture, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        red_light = gray[..., None] * np.array([0.05, 0.10, 1.0], dtype=np.float32)  # B, G, R
        image = (1.0 - severity) * image + severity * red_light

    # Darkness: a lower exposure (gain) and a gamma above 1, which makes the
    # shadows (eye sockets, beard) disappear first.
    gain = 1.0 - 0.8 * severity
    gamma = 1.0 + 1.5 * severity
    image = gain * np.power(image, gamma)

    # A camera amplifies a dark signal, which adds visible sensor noise.
    image = image + rng.normal(0.0, 0.03 * severity, size=image.shape)

    return np.clip(image * 255.0, 0, 255).round().astype(np.uint8)


def apply_clahe(image: np.ndarray) -> np.ndarray:
    """Contrast Limited Adaptive Histogram Equalization (Zuiderveld, 1994).

    CLAHE is applied to the lightness channel of the LAB colour space only,
    so the local contrast increases without shifting the colours.
    """
    clahe = cv2.createCLAHE(clipLimit=config.CLAHE_CLIP_LIMIT, tileGridSize=config.CLAHE_TILE_GRID)
    lightness, a, b = cv2.split(cv2.cvtColor(image, cv2.COLOR_BGR2LAB))
    return cv2.cvtColor(cv2.merge((clahe.apply(lightness), a, b)), cv2.COLOR_LAB2BGR)


def brightness(image: np.ndarray) -> float:
    """Mean grey value of an image, from 0 (black) to 255 (white)."""
    return float(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).mean())


def difference_hash(image: np.ndarray) -> int:
    """64-bit perceptual hash; near-identical images give near-identical hashes.

    Used to find copies of the same face (e.g. one film still saved twice at
    different sizes), which must never be compared with each other.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
    bits = (small[:, 1:] > small[:, :-1]).flatten()
    return int("".join("1" if bit else "0" for bit in bits), 2)


def hamming_distance(hash_a: int, hash_b: int) -> int:
    """Number of bits in which two hashes differ."""
    return bin(hash_a ^ hash_b).count("1")
