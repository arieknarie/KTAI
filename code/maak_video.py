"""Eén video van alle fragmenten achter elkaar, met een vierkantje om elk gezicht dat FaceNet als een van de vier
personen herkent, en de naam erbij.

Gebruikt wordt de algemeen beste configuratie uit results/configuraties/beste_algemeen.csv (eerste rij), met de
embeddings uit data/embeddings/ (maak die eerst met code/facenet_configuraties.py). Het vierkantje is het kader dat
de computer vond. Linksboven staat welk fragment en welk beeld het is.

Alle fragmenten worden 1280 x 720 pixels en 25 beelden per seconde (fragment 6 en 7 zijn 23,976 beelden per seconde
en lopen dus 4% sneller). Zonder geluid. De video gaat niet mee naar GitHub (te groot; results/video/ staat in .gitignore).

Gebruik (vanuit de map KTAI, met de pakketten uit requirements_herkenning.txt, en ffmpeg):
    .venv-herkenning/bin/python code/maak_video.py <uitvoer.mp4>
"""

import subprocess
import sys

import cv2
import numpy as np
import pandas as pd

import facenet_configuraties as fc
from basischeck import REPO, example_rows

WIDTH, HEIGHT = 1280, 720
COLOURS = {"Der Alte": (77, 77, 255), "Fritz Grade": (255, 166, 77), "Johann": (26, 209, 255), "Werner": (102, 204, 51)}


def predictions(detections: pd.DataFrame, best: pd.Series) -> np.ndarray:
    """Per kader de naam volgens de beste configuratie, of None."""
    margin = int(best["marge"].rstrip("%")) / 100
    boxes = np.load(fc.CACHE / f"kaders_{best['model']}_marge{int(margin * 100)}.npy")
    rows = example_rows(best["voorbeelden"] != "foto's")
    faces = [fc.crop(cv2.imread(str(REPO / r.source)), r.x, r.y, r.w, r.h, margin) for r in rows.itertuples()]
    names = rows["label"].map(fc.PERSONS).to_numpy()
    d = fc.distances(boxes, names, fc.represent(faces, best["model"]), best["afstand"], best["per_persoon"])
    who = np.array(fc.NAMES, dtype=object)[d.argmin(axis=1)]
    who[d.min(axis=1) >= best["drempel"]] = None
    if best["toewijzen"] == "uniek":                      # per beeld elke persoon hoogstens één keer
        keep = np.zeros(len(d), dtype=bool)
        for _, g in detections.assign(d=d.min(axis=1), who=who).dropna(subset=["who"]).sort_values("d") \
                .groupby(["video", "frame", "who"]):
            keep[g.index[0]] = True
        who[~keep] = None
    return who


def main() -> None:
    out = sys.argv[1]
    best = pd.read_csv(REPO / "results" / "configuraties" / "beste_algemeen.csv").iloc[0]
    detections = pd.read_csv(REPO / "data" / "tracks" / "detections_0.3.csv") \
        .sort_values(["video", "frame"], kind="stable").reset_index(drop=True)   # zelfde volgorde als de embeddings
    detections["who"] = predictions(detections, best)
    shown = detections.dropna(subset=["who"])
    ffmpeg = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                               "-s", f"{WIDTH}x{HEIGHT}", "-r", "25", "-i", "-", "-c:v", "libx264", "-crf", "26",
                               "-preset", "veryfast", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    caption = f"{best['model']}, marge {best['marge']}, {best['voorbeelden']}, {best['afstand']} < {best['drempel']}"
    for video in sorted(pd.read_csv(REPO / "data" / "tracks" / "frames.csv")["video"].unique()):
        boxes = {f: g for f, g in shown[shown["video"] == video].groupby("frame")}
        capture, index = cv2.VideoCapture(str(REPO / "movies" / video)), 0
        while True:                                       # op volgorde lezen, nooit naar een beeld springen
            ok, image = capture.read()
            if not ok:
                break
            scale = WIDTH / image.shape[1]
            image = cv2.resize(image, (WIDTH, HEIGHT), interpolation=cv2.INTER_AREA)
            for b in (boxes[index].itertuples() if index in boxes else []):
                x, y, w, h = (int(round(v * scale)) for v in (b.x, b.y, b.w, b.h))
                colour = COLOURS[b.who]
                cv2.rectangle(image, (x, y), (x + w, y + h), colour, 3)
                (tw, th), _ = cv2.getTextSize(b.who, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                top = y - th - 10 if y - th - 10 > 0 else y
                cv2.rectangle(image, (x - 1, top), (x + tw + 10, top + th + 10), colour, -1)
                cv2.putText(image, b.who, (x + 4, top + th + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2)
            label = f"{video.split(' [')[0]}  beeld {index + 1}   |   {caption}"
            cv2.putText(image, label, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 4)
            cv2.putText(image, label, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            ffmpeg.stdin.write(image.tobytes())
            index += 1
        capture.release()
        print(f"  {video}: {index} beelden")
    ffmpeg.stdin.close()
    ffmpeg.wait()
    print(f"klaar: {out}")


if __name__ == "__main__":
    main()
