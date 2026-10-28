"""Basischeck (run 1.1 in de projectdefinitie): herken de vier personen in de fragmenten met FaceNet, en zet het
resultaat naast de keuzes van de labelaar (het antwoordenblad).

1. Voorbeelden. Van elke foto van de acteurs in pictures/personal/ maakt FaceNet een embedding: een rij van 128
   getallen die het gezicht beschrijft. Het gezicht is het kader uit labeling/automatic_labels.csv (foto's met één
   gezicht), of bij de twee foto's met meer mensen het gezicht dat de labelaar als een van de vier personen aanwees
   (labels/labels.csv).
2. Herkennen. Van elk kader in de fragmenten (data/tracks/detections_0.3.csv) maakt FaceNet ook een embedding. Het
   kader krijgt de naam van het voorbeeld met de kleinste genormaliseerde Euclidische afstand, als die afstand
   kleiner is dan DREMPEL; anders is het "iemand anders".
3. Antwoordenblad. Elk kader krijgt de keuze die de labelaar voor zijn track maakte (labels/labels.csv).
4. Per beeld. Een persoon is in een beeld te zien als minstens één kader in dat beeld die persoon is: volgens de
   labelaar, en apart volgens FaceNet. Twee kaders op hetzelfde hoofd tellen zo maar één keer.

Uitvoer in results/basischeck/:
    voorspellingen.csv  per kader: fragment, bestand, beeld, tijd, track, kader, keuze van de labelaar,
                        voorspelling van FaceNet, het dichtstbijzijnde voorbeeld en de afstand
    tabel.csv, tabel.png  visualisatie 1: per persoon in hoeveel beelden die persoon te zien is
    tijdlijn.png        visualisatie 2: de tijd (x) tegen de personen (y), per fragment

Met --kostuum komen er voorbeelden bij: de gezichten van de vier personen op de stills (beelden uit de film, met de
personen in kostuum, in pictures/inCharacter/), zoals de labelaar ze aanwees. De drie stills die (bijna) een beeld
uit een van de fragmenten zijn (data/stills_index.csv, kolom uit_video), doen niet mee: een beeld uit de video mag
geen voorbeeld zijn. De uitvoer komt dan in results/basischeck_kostuum/.

Gebruik (vanuit de map KTAI, met de pakketten uit requirements_herkenning.txt):
    .venv-herkenning/bin/python code/basischeck.py [--kostuum]
"""

import argparse
import os
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")   # geen meldingen van TensorFlow op het scherm

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from deepface import DeepFace

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "results" / "basischeck"
TITLE = "voorbeelden: foto's"
PERSONS = {"DerAlte": "Der Alte", "FritzGrade": "Fritz Grade", "Johann": "Johann", "Werner": "Werner"}
OTHER = "iemand anders"
DREMPEL = 0.80   # de grens die deepface voor FaceNet met de genormaliseerde Euclidische afstand gebruikt
SIZE = 160       # FaceNet bekijkt een gezicht van 160 x 160 pixels
BATCH = 128
CHOICES = {**PERSONS, "other": "figurant", "no_face": "geen gezicht", "unknown": "weet niet"}


def small(face: np.ndarray) -> np.ndarray:
    """Het gezicht verkleind tot hoogstens 160 pixels breed en hoog (FaceNet maakt het daarna zelf 160 x 160)."""
    scale = SIZE / max(face.shape[:2])
    if scale < 1:
        face = cv2.resize(face, (max(1, round(face.shape[1] * scale)), max(1, round(face.shape[0] * scale))),
                          interpolation=cv2.INTER_AREA)
    return face


def cut(image: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
    x0, y0 = max(0, int(x)), max(0, int(y))
    return small(image[y0:y0 + int(h), x0:x0 + int(w)])


def embed(faces: list) -> np.ndarray:
    """Een embedding per gezicht, met lengte 1 (dan is de Euclidische afstand de genormaliseerde afstand)."""
    vectors = []
    for start in range(0, len(faces), BATCH):
        answer = DeepFace.represent(img_path=faces[start:start + BATCH], model_name="Facenet", detector_backend="skip",
                                    enforce_detection=False, align=False)
        for item in answer:
            vectors.append((item[0] if isinstance(item, list) else item)["embedding"])
    vectors = np.asarray(vectors, dtype=np.float32)
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


def examples(kostuum: bool = False) -> tuple:
    """De voorbeelden: naam van de persoon per foto, en de embeddings."""
    auto = pd.read_csv(REPO / "labeling" / "automatic_labels.csv")
    labels = pd.read_csv(REPO / "labels" / "labels.csv")
    chosen = labels[labels["item"].str.startswith("photo:") & labels["label"].isin(PERSONS)]
    rows = pd.concat([auto, chosen])[["source", "label", "x", "y", "w", "h"]]
    if kostuum:   # de gezichten op de stills, behalve de stills die een beeld uit een fragment zijn
        stills = pd.read_csv(REPO / "data" / "stills_index.csv").set_index("still")
        faces = labels[labels["item"].str.startswith("still:") & labels["label"].isin(PERSONS)].copy()
        faces["still"] = faces["item"].str.removeprefix("still:")
        faces = faces[stills.loc[faces["still"], "uit_video"].isna().to_numpy()]
        faces["source"] = stills.loc[faces["still"], "bestand"].to_numpy()
        rows = pd.concat([rows, faces[["source", "label", "x", "y", "w", "h"]]])
    faces = [cut(cv2.imread(str(REPO / r.source)), r.x, r.y, r.w, r.h) for r in rows.itertuples()]
    print(f"{len(faces)} voorbeelden: " + ", ".join(f"{PERSONS[k]} {n}" for k, n in rows["label"].value_counts().items()))
    return rows["label"].map(PERSONS).tolist(), embed(faces)


def fragments(frames: pd.DataFrame) -> pd.DataFrame:
    """Per bestand: bij welk fragment het hoort en hoeveel seconden het bestand na het begin van het fragment begint
    (fragment 2, 4 en 8 staan in delen, zie movies/List_of_URLS)."""
    rows, start = [], {}
    for video, f in frames.groupby("video", sort=True):
        name = Path(video).stem.split(" [")[0]                  # bijvoorbeeld "Das Boot 2b"
        number = name.split()[-1].rstrip("abc")
        group = f"Video {number}"
        fps = 1 / np.median(np.diff(f["time_s"]))
        rows.append({"video": video, "fragment": group, "offset": start.get(group, 0.0)})
        start[group] = start.get(group, 0.0) + len(f) / fps
    return pd.DataFrame(rows)


def recognise(names: list, refs: np.ndarray) -> pd.DataFrame:
    detections = pd.read_csv(REPO / "data" / "tracks" / "detections_0.3.csv")
    frames = pd.read_csv(REPO / "data" / "tracks" / "frames.csv")
    labels = pd.read_csv(REPO / "labels" / "labels.csv").set_index("face")["label"]
    parts = fragments(frames).set_index("video")
    rows = []
    for video, boxes in detections.groupby("video", sort=True):
        wanted = {f: g for f, g in boxes.groupby("frame")}
        capture, index, faces, meta = cv2.VideoCapture(str(REPO / "movies" / video)), 0, [], []
        while wanted and index <= max(wanted):            # op volgorde lezen, nooit naar een beeld springen
            ok, image = capture.read()
            if not ok:
                raise SystemExit(f"{video}: beeld {index} kon niet gelezen worden")
            for b in (wanted[index].itertuples() if index in wanted else []):
                faces.append(cut(image, b.x, b.y, b.w, b.h))
                meta.append(b)
            index += 1
        capture.release()
        vectors = embed(faces)
        distance = np.linalg.norm(vectors[:, None, :] - refs[None, :, :], axis=2)
        nearest = distance.argmin(axis=1)
        times = frames[frames["video"] == video].set_index("frame")["time_s"]
        for b, k, d in zip(meta, nearest, distance[np.arange(len(meta)), nearest]):
            choice = labels.get(f"{video}#track{int(b.track)}")
            rows.append({"fragment": parts.loc[video, "fragment"], "bestand": video, "beeld": int(b.frame),
                         "tijd_s": round(float(times[b.frame]) + parts.loc[video, "offset"], 3), "track": int(b.track),
                         "x": int(b.x), "y": int(b.y), "w": int(b.w), "h": int(b.h),
                         "labelaar": CHOICES.get(choice, "geen label"),
                         "facenet": names[k] if d < DREMPEL else OTHER,
                         "dichtstbij": names[k], "afstand": round(float(d), 4)})
        print(f"  {video}: {len(meta)} kaders herkend")
    return pd.DataFrame(rows)


def per_frame(found: pd.DataFrame, column: str) -> pd.DataFrame:
    """Welke persoon in welk beeld te zien is (elke combinatie één keer)."""
    seen = found[found[column].isin(PERSONS.values())]
    return seen[["fragment", "bestand", "beeld", "tijd_s", column]].drop_duplicates(["bestand", "beeld", column]) \
        .rename(columns={column: "persoon"})


def table(truth: pd.DataFrame, ai: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for person in PERSONS.values():
        gt, pred = int((truth["persoon"] == person).sum()), int((ai["persoon"] == person).sum())
        rows.append({"acteur": person, "ground_truth": gt, "ai_voorspelling": pred,
                     "foutmarge_procent": round(100 * abs(pred - gt) / gt, 1) if gt else None})
    result = pd.DataFrame(rows)
    result.to_csv(OUT / "tabel.csv", index=False, lineterminator="\n")
    fig, ax = plt.subplots(figsize=(7, 2.2))
    ax.axis("off")
    cells = [[r.acteur, r.ground_truth, r.ai_voorspelling,
              "-" if pd.isna(r.foutmarge_procent) else f"{r.foutmarge_procent:.1f}%".replace(".", ",")]
             for r in result.itertuples()]
    grid = ax.table(cellText=cells, colLabels=["Acteur", "Ground truth (beelden)", "AI-voorspelling (beelden)",
                                               "Foutmarge"], loc="center", cellLoc="center")
    grid.scale(1, 1.6)
    ax.set_title(f"Visualisatie 1: in hoeveel beelden elke acteur te zien is (alle acht fragmenten; {TITLE})", fontsize=10)
    fig.savefig(OUT / "tabel.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return result


def segments(times: np.ndarray, step: float) -> list:
    """Opeenvolgende beelden samen als één stuk (begin, lengte), voor de tijdlijn."""
    if len(times) == 0:
        return []
    times = np.sort(times)
    breaks = np.where(np.diff(times) > 1.5 * step)[0]
    starts, ends = np.r_[times[0], times[breaks + 1]], np.r_[times[breaks], times[-1]]
    return [(s, e - s + step) for s, e in zip(starts, ends)]


def timeline(truth: pd.DataFrame, ai: pd.DataFrame) -> None:
    groups = sorted(set(truth["fragment"]) | set(ai["fragment"]), key=lambda g: int(g.split()[-1]))
    people = list(PERSONS.values())
    fig, axes = plt.subplots(len(groups), 1, figsize=(12, 1.6 * len(groups)), squeeze=False)
    for ax, group in zip(axes[:, 0], groups):
        for y, person in enumerate(people):
            for data, shift, colour in ((truth, 0.18, "#333333"), (ai, -0.18, "#d1495b")):
                t = data[(data["fragment"] == group) & (data["persoon"] == person)]["tijd_s"].to_numpy()
                ax.broken_barh(segments(t, 0.04), (y + shift - 0.15, 0.3), color=colour)
        ax.set_yticks(range(len(people)), people, fontsize=8)
        ax.set_ylim(-0.6, len(people) - 0.4)
        ax.invert_yaxis()
        ax.set_title(group, fontsize=9, loc="left")
        ax.tick_params(axis="x", labelsize=8)
    axes[-1, 0].set_xlabel("tijd in het fragment (seconden)")
    fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color="#333333"), plt.Rectangle((0, 0), 1, 1, color="#d1495b")],
               labels=["ground truth (labelaar)", "AI-voorspelling (FaceNet)"], loc="upper right", fontsize=8)
    fig.suptitle(f"Visualisatie 2: wanneer elke acteur te zien is ({TITLE})", x=0.01, ha="left", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUT / "tijdlijn.png", dpi=130)
    plt.close(fig)


def main() -> None:
    global OUT, TITLE
    parser = argparse.ArgumentParser(description="Basischeck: FaceNet-herkenning naast de labels")
    parser.add_argument("--kostuum", action="store_true", help="ook de gezichten op de stills (in kostuum) als voorbeeld")
    args = parser.parse_args()
    if args.kostuum:
        OUT, TITLE = REPO / "results" / "basischeck_kostuum", "voorbeelden: foto's + stills in kostuum"
    OUT.mkdir(parents=True, exist_ok=True)
    names, refs = examples(args.kostuum)
    found = recognise(names, refs)
    found.to_csv(OUT / "voorspellingen.csv", index=False, lineterminator="\n")
    truth, ai = per_frame(found, "labelaar"), per_frame(found, "facenet")
    print(table(truth, ai).to_string(index=False))
    timeline(truth, ai)
    print(f"klaar: {OUT.relative_to(REPO)}/")


if __name__ == "__main__":
    main()
