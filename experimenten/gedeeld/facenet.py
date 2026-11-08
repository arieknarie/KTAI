"""FaceNet aanroepen: van een stukje beeld een vector maken (een rij getallen die het gezicht beschrijft)."""

import os

import cv2
import numpy as np
import pandas as pd

from gedeeld.paden import DETECTIONS, MOVIES, VECTORS

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")   # geen meldingen van TensorFlow op het scherm

SIZE = 160          # FaceNet bekijkt een gezicht van 160 x 160 pixels
BATCH = 128         # zoveel gezichten tegelijk door FaceNet (dit verandert de uitkomst niet, alleen de snelheid)


def small(face: np.ndarray) -> np.ndarray:
    """Het gezicht verkleind tot hoogstens 160 pixels breed en hoog (FaceNet maakt het daarna zelf 160 x 160)."""
    scale = SIZE / max(face.shape[:2])
    if scale < 1:
        face = cv2.resize(face, (max(1, round(face.shape[1] * scale)), max(1, round(face.shape[0] * scale))),
                          interpolation=cv2.INTER_AREA)
    return face


def cut(image: np.ndarray, x, y, w, h, margin: float = 0.0) -> np.ndarray:
    """Het stukje beeld binnen het kader, met aan elke kant `margin` keer de maat van het kader extra."""
    x0, y0 = max(0, int(x - margin * w)), max(0, int(y - margin * h))
    return small(image[y0:int(y + h + margin * h), x0:int(x + w + margin * w)])


def represent(faces: list, model: str) -> np.ndarray:
    """De ruwe vector van elk gezicht. deepface zoekt zelf geen gezicht meer (de kaders hebben we al), en zet het gezicht
    niet recht."""
    from deepface import DeepFace      # pas hier: het laden duurt even en niet elke stap heeft FaceNet nodig
    vectors = []
    for start in range(0, len(faces), BATCH):
        answer = DeepFace.represent(img_path=faces[start:start + BATCH], model_name=model, detector_backend="skip",
                                    enforce_detection=False, align=False)
        vectors += [(item[0] if isinstance(item, list) else item)["embedding"] for item in answer]
    return np.asarray(vectors, dtype=np.float32)


def unit(vectors: np.ndarray) -> np.ndarray:
    """Vectoren met lengte 1: dan is de Euclidische afstand de genormaliseerde afstand."""
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


def load_detections() -> pd.DataFrame:
    """Alle kaders uit het labelen, op volgorde van bestand en beeld (de volgorde van de bewaarde vectoren)."""
    return pd.read_csv(DETECTIONS).sort_values(["video", "frame"], kind="stable").reset_index(drop=True)


def lighten(face: np.ndarray) -> np.ndarray:
    """Maak een donker gezicht lichter (factor 1 tot 5), net als "Beeld lichter" in de labelapp."""
    factor = min(5.0, max(1.0, 120 / max(float(cv2.cvtColor(face, cv2.COLOR_BGR2GRAY).mean()), 8)))
    return np.clip(face.astype(np.float32) * factor, 0, 255).astype(np.uint8)


def vector_path(model: str, margin: float, light: bool = False):
    return VECTORS / f"kaders_{model}_marge{round(margin * 100)}{'_licht' if light else ''}.npy"


def box_vectors(detections: pd.DataFrame, wanted: list) -> dict:
    """De ruwe vector van elk kader voor elke (model, marge) of (model, marge, lichter maken) in `wanted`. Elke combinatie wordt
    één keer uitgerekend en bewaard; de beelden worden op volgorde uit de video gelezen."""
    missing = [key for key in wanted if not vector_path(*key).exists()]
    if missing:
        VECTORS.mkdir(exist_ok=True)
        crops = sorted({(key[1], len(key) > 2 and key[2]) for key in missing})
        parts = {key: [] for key in missing}
        for video, boxes in detections.groupby("video", sort=False):
            frames, faces = {f: g for f, g in boxes.groupby("frame")}, {c: [] for c in crops}
            capture, index = cv2.VideoCapture(str(MOVIES / video)), 0
            while index <= max(frames):                   # op volgorde lezen, nooit naar een beeld springen
                ok, image = capture.read()
                if not ok:
                    raise SystemExit(f"{video}: beeld {index} kon niet gelezen worden")
                for b in (frames[index].itertuples() if index in frames else []):
                    for margin, light in crops:
                        face = cut(image, b.x, b.y, b.w, b.h, margin)
                        faces[(margin, light)].append(lighten(face) if light else face)
                index += 1
            capture.release()
            for key in missing:
                parts[key].append(represent(faces[(key[1], len(key) > 2 and key[2])], key[0]))
            print(f"  {video}: {len(boxes)} kaders", flush=True)
        for key, vectors in parts.items():
            np.save(vector_path(*key), np.concatenate(vectors))
    return {key: np.load(vector_path(*key)) for key in wanted}
