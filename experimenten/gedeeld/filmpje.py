"""Eén filmpje van alle fragmenten achter elkaar, met een vierkantje om elk gezicht dat FaceNet als een van de vier
personen herkent, en de naam erbij. Het vierkantje is het kader van de detector. Linksboven staat welk fragment en welk
beeld het is, en welke instellingen gebruikt zijn.

Alle fragmenten worden 1280 x 720 pixels en 25 beelden per seconde (fragment 6 en 7 hebben 23,976 beelden per seconde en
lopen dus 4% sneller). Zonder geluid. Hiervoor is het programma ffmpeg nodig (zie de README).
"""

import shutil
import subprocess

import cv2
import pandas as pd

from gedeeld.paden import FRAMES, MOVIES, NAMES

WIDTH, HEIGHT = 1280, 720
COLOURS = {"Der Alte": (77, 77, 255), "Fritz Grade": (255, 166, 77), "Johann": (26, 209, 255), "Werner": (102, 204, 51)}


def make(found: pd.DataFrame, path, caption: str) -> None:
    if shutil.which("ffmpeg") is None:
        raise SystemExit("Het programma ffmpeg is niet gevonden. Installeren: op een Mac met brew install ffmpeg, op Windows "
                         "met winget install Gyan.FFmpeg. Open daarna een nieuw terminalvenster.")
    shown = found[found["facenet"].isin(NAMES)]
    ffmpeg = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{WIDTH}x{HEIGHT}",
                               "-r", "25", "-i", "-", "-c:v", "libx264", "-crf", "28", "-preset", "medium", "-pix_fmt", "yuv420p",
                               "-movflags", "+faststart", str(path)], stdin=subprocess.PIPE)
    for video in sorted(pd.read_csv(FRAMES)["video"].unique()):
        boxes = {f: g for f, g in shown[shown["bestand"] == video].groupby("beeld")}
        capture, index = cv2.VideoCapture(str(MOVIES / video)), 0
        while True:                                       # op volgorde lezen, nooit naar een beeld springen
            ok, image = capture.read()
            if not ok:
                break
            scale = WIDTH / image.shape[1]
            image = cv2.resize(image, (WIDTH, HEIGHT), interpolation=cv2.INTER_AREA)
            for b in (boxes[index].itertuples() if index in boxes else []):
                x, y, w, h = (int(round(v * scale)) for v in (b.x, b.y, b.w, b.h))
                colour = COLOURS[b.facenet]
                cv2.rectangle(image, (x, y), (x + w, y + h), colour, 3)
                (tw, th), _ = cv2.getTextSize(b.facenet, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                top = y - th - 10 if y - th - 10 > 0 else y
                cv2.rectangle(image, (x - 1, top), (x + tw + 10, top + th + 10), colour, -1)
                cv2.putText(image, b.facenet, (x + 4, top + th + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2)
            label = f"{video.split(' [')[0]}  beeld {index + 1}   |   {caption}"
            cv2.putText(image, label, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 4)
            cv2.putText(image, label, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            ffmpeg.stdin.write(image.tobytes())
            index += 1
        capture.release()
        print(f"  {video}: {index} beelden")
    ffmpeg.stdin.close()
    ffmpeg.wait()
