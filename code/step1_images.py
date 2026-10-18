"""Plaatjes voor de uitleg van stap 1 (docs/stap1_gezichten_vinden_en_volgen.md en docs/stap1_controle.md).

Maakt in docs/:
    stap1_drempel.jpg      hetzelfde frame met de gezichten bij detectiescore 0,5
                           en bij detectiescore 0,3, naast elkaar
    stap1_beeldwissel.jpg  twee opeenvolgende frames rond een gemarkeerde
                           beeldwissel, met de gemeten gelijkenis
    stap1_track.jpg        zes frames uit één track, zodat te zien is dat een
                           track hetzelfde gezicht volgt
    stap1_controle_wissel.jpg       24 uitsneden van track 1583 (nummer van vóór het knippen), een
                                    track die van het ene gezicht naar een ander gezicht verschuift
    stap1_controle_geen_gezicht.jpg 24 uitsneden van track 263, een track die
                                    nooit op een gezicht staat (een meter)

Gebruik (vanuit de map KTAI, na code/track_faces.py):
    .venv/bin/python code/step1_images.py
"""

from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from frozen import check_frozen

REPO = Path(__file__).resolve().parent.parent
MOVIES = REPO / "movies"
TRACKS = REPO / "data" / "tracks"
DOCS = REPO / "docs"

GREEN, GREY, WHITE, BLACK = (0, 170, 0), (170, 170, 170), (255, 255, 255), (0, 0, 0)
FONT = cv2.FONT_HERSHEY_SIMPLEX


def read_frame(video: str, frame_index: int) -> np.ndarray:
    """Frame nummer `frame_index`, gevonden door de video vanaf het begin op volgorde te lezen,
    net als in track_faces.py. Direct naar een frame springen (CAP_PROP_POS_FRAMES) geeft in
    'die Auferstehung' vanaf frame 4523 het frame ervoor."""
    capture = cv2.VideoCapture(str(MOVIES / video))
    for _ in range(frame_index + 1):
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError(f"frame {frame_index} van {video} niet gelezen")
    capture.release()
    return frame


def save_jpg(path: Path, image: np.ndarray, quality: int) -> None:
    """Een plaatje opslaan, ook als het pad letters als é bevat (cv2.imwrite kan dat op Windows niet)."""
    ok, data = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise SystemExit(f"{path}: plaatje kon niet gemaakt worden")
    path.write_bytes(data.tobytes())


def label(image: np.ndarray, text: str, x: int, y: int, color, scale: float = 0.45) -> None:
    """Tekst met een witte achtergrond, zodat de tekst op elk beeld leesbaar is."""
    (w, h), _ = cv2.getTextSize(text, FONT, scale, 1)
    cv2.rectangle(image, (x, y - h - 4), (x + w + 4, y + 2), WHITE, -1)
    cv2.putText(image, text, (x + 2, y - 2), FONT, scale, color, 1, cv2.LINE_AA)


def caption(image: np.ndarray, text: str) -> np.ndarray:
    """Witte balk met tekst boven een beeld."""
    bar = np.full((28, image.shape[1], 3), 255, np.uint8)
    cv2.putText(bar, text, (6, 19), FONT, 0.55, BLACK, 1, cv2.LINE_AA)
    return np.vstack([bar, image])


def threshold_image() -> None:
    """Frame 1:13 uit 'die Auferstehung': gezichten bij score 0,5 en bij score 0,3."""
    video = "Das Boot - die Auferstehung [Oqek9Ktuwy8].mp4"
    frame_index = 73 * 25  # 1:13, de video heeft 25 frames per seconde
    detections = pd.read_csv(TRACKS / "detections_0.3.csv")
    # alleen de gewone kaders (vanaf 0,3); de verlengingen (0,2 tot 0,3) horen niet bij deze vergelijking
    faces = detections[(detections["video"] == video) & (detections["frame"] == frame_index) & ~detections["verlengd"]]
    frame = read_frame(video, frame_index)
    panels = []
    for threshold in (0.5, 0.3):
        panel = frame.copy()
        shown = faces[faces["score"] >= threshold]
        for face in shown.itertuples():
            cv2.rectangle(panel, (face.x, face.y), (face.x + face.w, face.y + face.h), GREEN, 2)
            label(panel, f"{face.score:.2f}", face.x, face.y, GREEN)
        panels.append(caption(panel, f"detectiescore >= {threshold}: {len(shown)} gezichten"))
    gap = np.full((panels[0].shape[0], 10, 3), 255, np.uint8)
    save_jpg(DOCS / "stap1_drempel.jpg", np.hstack([panels[0], gap, panels[1]]), 90)


def track_image() -> None:
    """Zes frames uit een lange, duidelijke track in 'Go Back Johann'."""
    video = "Go Back Johann [qa3jt_GXMts].mp4"
    detections = pd.read_csv(TRACKS / "detections_0.3.csv")
    tracks = pd.read_csv(TRACKS / "tracks_0.3.csv")
    # de langste track die in elk frame duidelijk gedetecteerd is (score minstens 0,5), zodat het
    # voorbeeld goed te volgen is
    clear = detections.groupby("track")["score"].min()
    candidates = tracks[(tracks["video"] == video) & tracks["track"].map(clear).ge(0.5)]
    longest = candidates.sort_values("faces", ascending=False).iloc[0]
    track_faces = detections[detections["track"] == longest["track"]]
    chosen = track_faces.iloc[np.linspace(0, len(track_faces) - 1, 6).round().astype(int)]
    panels = []
    for face in chosen.itertuples():
        frame = read_frame(video, face.frame)
        # andere tracks in hetzelfde frame grijs, de gekozen track groen
        others = detections[(detections["video"] == video) & (detections["frame"] == face.frame)
                            & (detections["track"] != face.track)]
        for other in others.itertuples():
            cv2.rectangle(frame, (other.x, other.y), (other.x + other.w, other.y + other.h), GREY, 3)
        cv2.rectangle(frame, (face.x, face.y), (face.x + face.w, face.y + face.h), GREEN, 4)
        label(frame, f"track {face.track}", face.x, face.y, GREEN, scale=0.9)
        small = cv2.resize(frame, (400, round(frame.shape[0] * 400 / frame.shape[1])), interpolation=cv2.INTER_AREA)
        minutes, seconds = divmod(face.time_s, 60)
        panels.append(caption(small, f"frame {face.frame}  ({int(minutes)}:{seconds:04.1f})"))
    rows = [np.hstack(panels[i:i + 3]) for i in (0, 3)]
    save_jpg(DOCS / "stap1_track.jpg", np.vstack(rows), 90)
    print(f"track {longest['track']}: {longest['faces']} frames, {longest['start_s']} s tot {longest['end_s']} s")


def cut_image() -> None:
    """Twee opeenvolgende frames rond een gemarkeerde beeldwissel, met de gemeten gelijkenis."""
    video = "Go Back Johann [qa3jt_GXMts].mp4"
    frames = pd.read_csv(TRACKS / "frames.csv")
    frames = frames[frames["video"] == video].set_index("frame")
    frame_index = 1712 if bool(frames.loc[1712, "cut"]) else int(frames.index[frames["cut"]][0])
    row = frames.loc[frame_index]
    panels = []
    for index, title in ((frame_index - 1, f"frame {frame_index - 1}"),
                         (frame_index, f"frame {frame_index}: kleur {row['colour_similarity']:.2f}, "
                                       f"structuur {row['structure_similarity']:.2f} -> beeldwissel")):
        image = read_frame(video, index)
        small = cv2.resize(image, (560, round(image.shape[0] * 560 / image.shape[1])), interpolation=cv2.INTER_AREA)
        panels.append(caption(small, title))
    gap = np.full((panels[0].shape[0], 10, 3), 255, np.uint8)
    save_jpg(DOCS / "stap1_beeldwissel.jpg", np.hstack([panels[0], gap, panels[1]]), 90)


def strip_image(track: int, filename: str) -> None:
    """24 uitsneden van één track, gelijk verdeeld van begin tot eind, met wat omgeving en lichter
    gemaakt, zoals bij de controle van de tracks (zie docs/stap1_controle.md)."""
    detections = pd.read_csv(TRACKS / "detections_0.3.csv")
    # de hele oorspronkelijke track, ook als die na de controle geknipt is (zie code/track_faces.py)
    faces = detections[detections["track_ongeknipt"] == track].sort_values("frame").reset_index(drop=True)
    chosen = faces.iloc[np.unique(np.linspace(0, len(faces) - 1, min(24, len(faces))).round().astype(int))]
    wanted = {face.frame: face for face in chosen.itertuples()}
    capture = cv2.VideoCapture(str(MOVIES / faces["video"].iloc[0]))
    tiles = []
    for index in range(max(wanted) + 1):  # op volgorde lezen, zie read_frame
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError(f"frame {index} niet gelezen")
        if index not in wanted:
            continue
        face = wanted[index]
        margin = int(0.6 * max(face.w, face.h))
        top, left = max(0, face.y - margin), max(0, face.x - margin)
        crop = frame[top:face.y + face.h + margin, left:face.x + face.w + margin].astype(np.float32)
        crop = np.clip(crop * (220 / max(20.0, float(np.percentile(crop, 97)))), 0, 255).astype(np.uint8)  # lichter
        cv2.rectangle(crop, (face.x - left, face.y - top), (face.x - left + face.w, face.y - top + face.h), (0, 255, 0), 1)
        crop = cv2.resize(crop, (170, 170), interpolation=cv2.INTER_CUBIC)
        label(crop, f"frame {index}", 2, 16, BLACK, scale=0.45)
        tiles.append(crop)
    capture.release()
    while len(tiles) % 8:
        tiles.append(np.full_like(tiles[0], 255))
    rows = [np.hstack(tiles[i:i + 8]) for i in range(0, len(tiles), 8)]
    save_jpg(DOCS / filename, np.vstack(rows), 88)


def main() -> None:
    check_frozen("data/tracks/detections_0.3.csv", "data/tracks/tracks_0.3.csv", "data/tracks/frames.csv")
    DOCS.mkdir(exist_ok=True)
    threshold_image()
    cut_image()
    track_image()
    strip_image(1583, "stap1_controle_wissel.jpg")
    strip_image(263, "stap1_controle_geen_gezicht.jpg")
    print(f"plaatjes in {DOCS.relative_to(REPO)}/")


if __name__ == "__main__":
    main()
