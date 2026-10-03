"""Step 2: run the baseline and the three stress tests on complete film stills.

The system gets every in-character still as a whole, exactly as in practice:
it must find all faces itself (including extras in the background), and name
each face, or call it "unknown" when no reference face is close enough
(open-set recognition, threshold config.DISTANCE_THRESHOLD).

Recognition: every face is mapped to a 128-d FaceNet embedding and gets the
name of the reference (gallery) face at the smallest Euclidean distance.
References from the same still, or copies of its faces, are never used
(leave-one-out).

Scoring: the detected faces are matched (by box overlap) with the labelled
faces of the still in data/labels.csv, which gives one outcome per face:

    a named person (Der Alte, Fritz, Johann, Werner):
        correct          recognised as the right person
        wrong            recognised as another of the four
        rejected         found, but "unknown"
        missed           not found by the face detector at all
    an extra ("other", or a face not found in the original still):
        rejected         correctly "unknown"
        false_identity   wrongly named as one of the four

Experiments (one per sub-question of the paper)
    appearance  Stress Test 2 + baseline: original stills, recognised with
                (a) only the actors' personal photos as references, and
                (b) personal photos + in-character reference faces.
    resolution  Stress Test 1: the still shrunk to 1/2 ... 1/16 and enlarged
                again with nearest neighbour (no interpolation), bicubic
                or Lanczos interpolation.
    lighting    Stress Test 3: the still darkened ("dark") or lit by red
                light ("red_alarm") at increasing severity, without/with CLAHE.

Besides the tables and figures, every still is saved as the system saw it,
with its faces and their outcomes, in results/intermediate/ (see
intermediate.py), and the scores of every condition are printed while running.

Usage:
    python run_stress_tests.py                  # all stills (takes a while)
    python run_stress_tests.py --max-stills 3   # quick test run on 3 stills
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

import config
import labels
import plots
from face_model import DetectedFace, detect_faces, embed
from image_ops import (apply_clahe, read_image, reduce_resolution,
                       simulate_low_light, to_model_input)
from intermediate import SceneSheets, gallery_overview, save_image, scene_thumbnail


@dataclass
class Scene:
    """One in-character still with its labelled faces."""

    picture: str           # e.g. "inCharacter/Johann/johann7_jpg"
    source_path: str       # picture file, relative to the repository
    image: np.ndarray
    truth: pd.DataFrame    # the labelled faces (boxes and labels) of this still
    # Analysed versions of this still, so identical images are processed once:
    # image key -> (image, detected faces); (image key, upscale) -> embeddings.
    detections: dict = field(default_factory=dict)
    embeddings: dict = field(default_factory=dict)


class Gallery:
    """Reference faces with known identity that the faces in a still are compared with."""

    def __init__(self, name: str, faces: pd.DataFrame, images: dict[str, np.ndarray]):
        self.name = name
        self.face_ids = faces["face_id"].to_numpy()
        self.labels = faces["label"].to_numpy()
        self.groups = faces["duplicate_group"].to_numpy()
        self.source_paths = faces["source_path"].to_numpy()
        self.vectors = np.stack([embed(images[face_id]) for face_id in faces["face_id"]])

    def identify(self, vector: np.ndarray, scene: Scene) -> dict:
        """Nearest-neighbour identification of one face from `scene`."""
        # Leave-one-out: skip references from this still and copies of its faces.
        allowed = ((self.source_paths != scene.source_path)
                   & ~np.isin(self.groups, scene.truth["duplicate_group"].to_numpy()))
        distances = np.linalg.norm(self.vectors[allowed] - vector, axis=1)
        best = int(distances.argmin())
        closest, distance = self.labels[allowed][best], float(distances[best])
        return {
            "closest_label": closest,  # nearest reference, ignoring the threshold
            "predicted_label": closest if distance < config.DISTANCE_THRESHOLD else config.UNKNOWN,
            "distance": round(distance, 4),
            "matched_face_id": self.face_ids[allowed][best],
        }


def box_overlap(a, b) -> float:
    """Intersection over union of two (x, y, w, h) boxes."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    inter_w = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    inter_h = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    intersection = inter_w * inter_h
    union = aw * ah + bw * bh - intersection
    return intersection / union if union > 0 else 0.0


def match_faces(detected: list[DetectedFace], truth: pd.DataFrame) -> dict[int, int]:
    """Pair detected faces with labelled faces: {truth position: detection index}.

    Greedy: the pair with the largest overlap first, every face used once.
    """
    truth_boxes = truth[["x", "y", "w", "h"]].to_numpy(dtype=float)
    pairs = sorted(
        ((box_overlap((face.x, face.y, face.w, face.h), truth_box), d, t)
         for d, face in enumerate(detected) for t, truth_box in enumerate(truth_boxes)),
        reverse=True,
    )
    matches: dict[int, int] = {}
    used = set()
    for overlap, d, t in pairs:
        if overlap < config.MIN_BOX_OVERLAP:
            break
        if t not in matches and d not in used:
            matches[t] = d
            used.add(d)
    return matches


def outcome(true_label: str, prediction: dict | None) -> str:
    """Score one face (see the module docstring)."""
    if prediction is None:
        return "missed"
    predicted = prediction["predicted_label"]
    if true_label in config.IDENTITIES:
        if predicted == true_label:
            return "correct"
        return "rejected" if predicted == config.UNKNOWN else "wrong"
    return "rejected" if predicted == config.UNKNOWN else "false_identity"


def analyse(scene: Scene, key: tuple, make_frame, upscale: str = "bicubic"):
    """Detect and embed all faces in one version of the still.

    `key` names the version of the image (e.g. ("clean",)); detection is done
    once per image, embedding once per image and upscaling method.
    """
    if key not in scene.detections:
        frame = make_frame()
        scene.detections[key] = (frame, detect_faces(frame))
    frame, faces = scene.detections[key]
    if (key, upscale) not in scene.embeddings:
        scene.embeddings[(key, upscale)] = [embed(to_model_input(face.crop, upscale)) for face in faces]
    return frame, faces, scene.embeddings[(key, upscale)]


def evaluate_scene(experiment: str, variant: str, mitigation: str, level, scene: Scene,
                   analysed, gallery: Gallery, sheets: SceneSheets, scale: float = 1.0) -> list[dict]:
    """Score every face of one still under one condition; one result row per face."""
    frame, detected, vectors = analysed
    predictions = [gallery.identify(vector, scene) for vector in vectors]
    matches = match_faces(detected, scene.truth)

    base = {"experiment": experiment, "variant": variant, "mitigation": mitigation,
            "level": level, "gallery": gallery.name, "picture": scene.picture}
    rows = []
    for position, truth in enumerate(scene.truth.itertuples()):
        if truth.label == "":
            continue  # not labelled ("weet niet"): not scored
        d = matches.get(position)
        if d is None and truth.label not in config.IDENTITIES:
            continue  # an extra that is not found is not an error
        prediction = predictions[d] if d is not None else None
        face = detected[d] if d is not None else None
        rows.append({
            **base,
            "face_id": truth.face_id,
            "true_label": truth.label,
            "face_px": round(max(truth.w, truth.h) * scale, 1),  # face size the system had
            "detected": d is not None,
            **(prediction or {"closest_label": "", "predicted_label": "", "distance": np.nan,
                              "matched_face_id": ""}),
            "outcome": outcome(truth.label, prediction),
            "box": (face.x, face.y, face.w, face.h) if face else (truth.x, truth.y, truth.w, truth.h),
        })
    # Faces found now but not in the original still count as extras.
    for d in sorted(set(range(len(detected))) - set(matches.values())):
        face = detected[d]
        rows.append({
            **base, "face_id": "", "true_label": config.OTHER_LABEL,
            "face_px": max(face.w, face.h), "detected": True, **predictions[d],
            "outcome": outcome(config.OTHER_LABEL, predictions[d]),
            "box": (face.x, face.y, face.w, face.h),
        })

    sheets.add(experiment, scene.picture, (variant, mitigation, level), scene_thumbnail(frame, rows))
    return rows


def summarise(results: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Scores per group of conditions (see README for the definitions)."""
    def scores(group: pd.DataFrame) -> pd.Series:
        named = group[group["true_label"].isin(config.IDENTITIES)]
        extras = group[group["true_label"] == config.OTHER_LABEL]
        named_predictions = group["predicted_label"].isin(config.IDENTITIES)
        return pd.Series({
            "named_faces": len(named),
            "recognised": (named["outcome"] == "correct").mean(),
            "wrong": (named["outcome"] == "wrong").mean(),
            "rejected": (named["outcome"] == "rejected").mean(),
            "missed": (named["outcome"] == "missed").mean(),
            "closest_correct": (named["closest_label"] == named["true_label"]).mean(),
            "extras_found": len(extras),
            "extras_named": (extras["outcome"] == "false_identity").mean() if len(extras) else np.nan,
            "precision": ((group["outcome"] == "correct").sum() / named_predictions.sum()
                          if named_predictions.any() else np.nan),
        })
    return (results.groupby(by, dropna=False, sort=False)[list(results.columns)]
            .apply(scores).round(4).reset_index())


def report(rows: list[dict], label: str) -> None:
    """Print the scores of one condition right away."""
    named = [row for row in rows if row["true_label"] in config.IDENTITIES]
    extras = [row for row in rows if row["true_label"] == config.OTHER_LABEL]
    recognised = np.mean([row["outcome"] == "correct" for row in named]) if named else np.nan
    missed = np.mean([row["outcome"] == "missed" for row in named]) if named else np.nan
    named_extras = sum(row["outcome"] == "false_identity" for row in extras)
    print(f"  {label:<46} recognised {recognised:6.1%}   missed {missed:6.1%}   "
          f"extras named {named_extras}/{len(extras)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--max-stills", type=int, help="only use the first N stills (quick test run)")
    args = parser.parse_args()

    faces = labels.load_labels()
    labelled = faces[faces["label"].isin(config.IDENTITIES)]
    personal = labelled[labelled["source"] == "personal"]
    in_character = labelled[labelled["source"] == "inCharacter"]

    scenes = []
    for source_path, truth in faces[faces["source"] == "inCharacter"].groupby("source_path", sort=False):
        if truth["label"].isin(config.IDENTITIES).any():
            picture = truth["face_id"].iloc[0].rsplit("_f", 1)[0]
            scenes.append(Scene(picture, source_path, read_image(config.REPO_ROOT / source_path),
                                truth.reset_index(drop=True)))
    if not scenes or personal.empty:
        raise SystemExit("No labelled faces found; run prepare_faces.py and label the faces first.")
    scenes = scenes[:args.max_stills]

    n_named = sum(scene.truth["label"].isin(config.IDENTITIES).sum() for scene in scenes)
    print(f"{len(scenes)} stills with {n_named} named faces; references: "
          f"{len(personal)} personal + {len(in_character)} in-character faces\n")

    reference_faces = pd.concat([personal, in_character])
    clean = {row.face_id: to_model_input(read_image(config.EXPERIMENTS_DIR / row.crop_path))
             for row in reference_faces.itertuples()}
    clean_clahe = {face_id: apply_clahe(image) for face_id, image in clean.items()}
    save_image(gallery_overview(reference_faces, clean, "Reference faces (model input)"),
               config.INTERMEDIATE_DIR / "gallery_overview.jpg")
    save_image(gallery_overview(reference_faces, clean_clahe, "Reference faces after CLAHE"),
               config.INTERMEDIATE_DIR / "gallery_overview_clahe.jpg")

    print("Embedding reference faces ...")
    personal_only = Gallery("personal_only", personal, clean)
    extended = Gallery("personal_plus_in_character", reference_faces, clean)
    extended_clahe = (Gallery("personal_plus_in_character_clahe", reference_faces, clean_clahe)
                      if config.CLAHE_ON_GALLERY else extended)

    results: list[dict] = []
    sheets = SceneSheets()

    def run(label: str, condition_rows: list[dict]) -> None:
        report(condition_rows, label)
        results.extend(condition_rows)

    # --- Baseline and Stress Test 2: changing faces --------------------------
    print("\nStress Test 2: changing faces (original stills)")
    for gallery in (personal_only, extended):
        rows = []
        for scene in scenes:
            analysed = analyse(scene, ("clean",), lambda s=scene: s.image)
            rows += evaluate_scene("appearance", "clean", gallery.name, np.nan, scene, analysed, gallery, sheets)
        run(gallery.name, rows)

    # --- Stress Test 1: low resolution ---------------------------------------
    print("\nStress Test 1: low resolution")
    for method in config.UPSCALE_METHODS:
        for scale in config.IMAGE_SCALES:
            rows = []
            for scene in scenes:
                key = ("clean",) if scale == 1 else ("scale", scale, method)  # scale 1: unchanged
                analysed = analyse(scene, key, lambda s=scene: reduce_resolution(s.image, scale, method), method)
                rows += evaluate_scene("resolution", "downscaled", method, scale, scene, analysed,
                                       extended, sheets, scale)
            run(f"{method:<8} scale 1/{round(1 / scale)}", rows)

    # --- Stress Test 3: poor lighting ----------------------------------------
    print("\nStress Test 3: poor lighting")
    for lighting_index, lighting in enumerate(config.LIGHTING_TYPES):
        for severity in config.LIGHTING_SEVERITIES:
            for mitigation in ("none", "clahe"):
                rows = []
                for index, scene in enumerate(scenes):
                    def make_frame(s=scene, i=index):
                        # The same seed per still, so "none" and "clahe" see identical noise.
                        rng = np.random.default_rng([config.RANDOM_SEED, lighting_index, i, round(severity * 100)])
                        frame = simulate_low_light(s.image, severity, lighting, rng)
                        return apply_clahe(frame) if mitigation == "clahe" else frame
                    if severity == 0:  # untouched still: share the analysis between lighting types
                        key = ("clean",) if mitigation == "none" else ("clahe",)
                    else:
                        key = ("light", lighting, severity, mitigation)
                    gallery = extended_clahe if mitigation == "clahe" else extended
                    rows += evaluate_scene("lighting", lighting, mitigation, severity, scene,
                                           analyse(scene, key, make_frame), gallery, sheets)
                run(f"{lighting:<9} severity {severity:<4} {mitigation}", rows)

    # --- Write results ---------------------------------------------------------
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    results = pd.DataFrame(results).drop(columns="box")
    results.to_csv(config.RESULTS_DIR / "per_face.csv", index=False)

    keys = ["experiment", "variant", "mitigation", "level"]
    summary = summarise(results, keys)
    named = results[results["true_label"].isin(config.IDENTITIES)]
    by_identity = summarise(named, keys + ["true_label"])
    summary.to_csv(config.RESULTS_DIR / "summary.csv", index=False)
    by_identity.to_csv(config.RESULTS_DIR / "summary_by_identity.csv", index=False)

    plots.make_figures(summary, by_identity)
    print("\nWriting intermediate result images ...")
    sheets.write()

    print("\n" + summary.to_string(index=False))
    print(f"\nResults written to {config.RESULTS_DIR.relative_to(config.REPO_ROOT)}/")


if __name__ == "__main__":
    main()
