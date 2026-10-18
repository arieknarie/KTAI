"""Maakt de plaatjes waarmee álle tracks gecontroleerd worden: blijft het kader van begin tot eind op hetzelfde
gezicht (of op hetzelfde ding)?

Van elke track van twee of meer kaders (uit data/tracks/detections_0.3.csv, met het tracknummer van vóór de
correctie uit de controle: kolom track_ongeknipt) komt een strook uitsneden op een vel:
- een track van hoogstens 16 kaders: elk kader;
- een langere track: 16 kaders gelijk verdeeld over de track, plus de kaders rond de vier plekken waar het
  kader het meest verspringt (in plaats of in grootte), want daar gaat het volgen het eerst mis.
Elke uitsnede toont het kader met wat ruimte eromheen, lichter gemaakt als het gezicht donker is, met het
framenummer eronder. Een gewoon kader is groen; een verlenging (score 0,2 tot 0,3) is oranje en heeft een v
achter het framenummer.

Uitvoer:
    data/audit/alle_tracks/vel_0001.jpg ...   de vellen (gaan niet mee naar GitHub; dit programma maakt ze opnieuw)
    data/audit/alle_tracks_index.csv           welke track op welk vel staat, en welke frames getoond zijn

Met --track <nummer> --van <frame> --tot <frame> maakt het programma een strook met álle kaders van één track
tussen twee frames, om een vondst precies na te kijken (standaard in data/audit/alle_tracks/, of waar --out zegt). Met --stappen <aantal> komen er in plaats
daarvan zoveel kaders op, gelijk verdeeld maar steeds midden tussen de kaders van het gewone vel in (voor een
tweede, onafhankelijke blik op dezelfde track).

De frames worden altijd op volgorde gelezen (OpenCV springt soms een frame verkeerd bij het zoeken naar een
framenummer).

Gebruik (vanuit de map KTAI):
    .venv/bin/python code/check_all_tracks.py
"""

import argparse
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from frozen import check_frozen, write_frozen

REPO = Path(__file__).resolve().parent.parent
MOVIES = REPO / "movies"
DETECTIONS = REPO / "data" / "tracks" / "detections_0.3.csv"
AUDIT = REPO / "data" / "audit"
SHEETS = AUDIT / "alle_tracks"

CROP = 112            # grootte van een uitsnede in pixels
PER_ROW = 12          # uitsneden per rij
EVEN = 16             # bij een lange track: zoveel gelijk verdeelde kaders
JUMPS = 4             # en de kaders rond zoveel plekken waar het kader het meest verspringt
SHEET_HEIGHT = 1400   # een vel wordt niet hoger dan dit (pixels)
GREEN, ORANGE = (60, 200, 60), (0, 150, 255)


def shown_frames(track: pd.DataFrame) -> list:
    """De frames van een track die op het vel komen (zie de uitleg bovenaan)."""
    frames = track["frame"].tolist()
    if len(frames) <= EVEN:
        return frames
    picked = {frames[round(k * (len(frames) - 1) / (EVEN - 1))] for k in range(EVEN)}
    # verspringen: afstand tussen de middens van twee opeenvolgende kaders (gedeeld door de breedte), plus de
    # verandering in grootte
    x = (track["x"] + track["w"] / 2).to_numpy()
    y = (track["y"] + track["h"] / 2).to_numpy()
    w = track["w"].to_numpy().astype(float)
    jump = np.hypot(np.diff(x), np.diff(y)) / w[:-1] + np.abs(np.log(w[1:] / w[:-1]))
    for k in np.argsort(-jump)[:JUMPS]:
        picked.update(frames[max(0, k - 1):k + 3])   # het kader ervoor, de sprong zelf en het kader erna
    return sorted(picked)


def lighter(image: np.ndarray, box: tuple) -> np.ndarray:
    """Maak een donkere uitsnede lichter, net als 'Beeld lichter' in de labelapp (factor 1 tot 5)."""
    x, y, w, h = box
    face = cv2.cvtColor(image[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)
    factor = min(5.0, max(1.0, 120 / max(float(face.mean()) if face.size else 120, 8)))
    return np.clip(image.astype(np.float32) * factor, 0, 255).astype(np.uint8)


def crop(frame: np.ndarray, row) -> np.ndarray:
    """Een vierkante uitsnede rond het kader (1,8 keer het kader), met het kader erin getekend en het framenummer eronder."""
    x, y, w, h = int(row.x), int(row.y), int(row.w), int(row.h)
    side = int(1.8 * max(w, h))
    pad = side
    padded = cv2.copyMakeBorder(frame, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(0, 0, 0))
    cx, cy = x + w // 2 + pad, y + h // 2 + pad
    region = padded[cy - side // 2:cy - side // 2 + side, cx - side // 2:cx - side // 2 + side]
    box_in_region = (x + pad - (cx - side // 2), y + pad - (cy - side // 2), w, h)
    region = lighter(region, box_in_region)
    scale = CROP / side
    tile = cv2.resize(region, (CROP, CROP), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    bx, by = int(box_in_region[0] * scale), int(box_in_region[1] * scale)
    cv2.rectangle(tile, (bx, by), (bx + int(w * scale), by + int(h * scale)), ORANGE if row.verlengd else GREEN, 2)
    label = np.full((18, CROP, 3), 255, np.uint8)
    cv2.putText(label, f"{int(row.frame)}{' v' if row.verlengd else ''}", (4, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                (0, 0, 0), 1, cv2.LINE_AA)
    return np.vstack([tile, label])


def collect_crops(wanted: dict) -> dict:
    """{(video, frame): [rijen]} -> {(track, frame): uitsnede}. Elke video wordt één keer op volgorde gelezen."""
    crops = {}
    for video in sorted({video for video, _ in wanted}):
        frames = {frame: rows for (v, frame), rows in wanted.items() if v == video}
        capture = cv2.VideoCapture(str(MOVIES / video))
        index, last = 0, max(frames)
        while index <= last:
            ok, frame = capture.read()
            if not ok:
                raise SystemExit(f"{video}: frame {index} kon niet gelezen worden. Controleer de installatie met "
                                 "code/check_setup.py.")
            for row in frames.get(index, []):
                crops[(row.track_ongeknipt, index)] = crop(frame, row)
            index += 1
        capture.release()
        print(f"  {video}: {len(frames)} frames gelezen")
    return crops


def track_block(track: int, rows: pd.DataFrame, frames: list, crops: dict, title: str) -> np.ndarray:
    """De strook van één track: een kopregel en rijen van hoogstens PER_ROW uitsneden."""
    tiles = [crops[(track, frame)] for frame in frames]
    while len(tiles) % PER_ROW:
        tiles.append(np.full_like(tiles[0], 255))
    rows_img = [np.hstack([np.pad(t, ((2, 2), (2, 2), (0, 0)), constant_values=255) for t in tiles[i:i + PER_ROW]])
                for i in range(0, len(tiles), PER_ROW)]
    head = np.full((26, rows_img[0].shape[1], 3), 255, np.uint8)
    cv2.putText(head, title, (4, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
    return np.vstack([head, *rows_img, np.full((10, rows_img[0].shape[1], 3), 255, np.uint8)])


def save_jpg(path: Path, image: np.ndarray) -> None:
    ok, data = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 88])
    if not path.exists() or path.read_bytes() != data.tobytes():   # een vel dat al zo bestaat, blijft staan
        path.write_bytes(data.tobytes())


def video_number(video: str) -> int:
    return sorted(DETECTIONS_VIDEOS).index(video) + 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Maak de controleplaatjes van alle tracks")
    parser.add_argument("--track", type=int, help="alleen deze track (tracknummer van vóór de correctie)")
    parser.add_argument("--van", type=int, help="eerste frame (met --track)")
    parser.add_argument("--tot", type=int, help="laatste frame (met --track)")
    parser.add_argument("--out", type=Path, help="bestand voor de strook (met --track)")
    parser.add_argument("--stappen", type=int, help="zoveel gelijk verdeelde kaders in plaats van alle (met --track)")
    args = parser.parse_args()
    check_frozen("data/tracks/detections_0.3.csv")
    detections = pd.read_csv(DETECTIONS)
    global DETECTIONS_VIDEOS
    DETECTIONS_VIDEOS = sorted(detections["video"].unique())

    if args.track is not None:   # één strook met alle kaders tussen twee frames
        rows = detections[detections["track_ongeknipt"] == args.track].sort_values("frame")
        rows = rows[(rows["frame"] >= (args.van if args.van is not None else -1)) &
                    (rows["frame"] <= (args.tot if args.tot is not None else 10 ** 9))]
        if rows.empty:
            raise SystemExit("Geen kaders gevonden voor deze track en deze frames.")
        if args.stappen and len(rows) > args.stappen:   # gelijk verdeeld, midden tussen de stappen in
            rows = rows.iloc[sorted({min(len(rows) - 1, int((k + 0.5) * len(rows) / args.stappen))
                                     for k in range(args.stappen)})]
        crops = collect_crops({key: list(group.itertuples()) for key, group in rows.groupby(["video", "frame"])})
        title = (f"track {args.track}, frames {rows['frame'].min()}-{rows['frame'].max()} "
                 f"({'alle kaders' if not args.stappen else f'{len(rows)} kaders gelijk verdeeld'})")
        SHEETS.mkdir(parents=True, exist_ok=True)   # standaard bij de vellen, die niet naar GitHub gaan
        out = args.out or SHEETS / f"track_{args.track}_{rows['frame'].min()}_{rows['frame'].max()}.jpg"
        save_jpg(out, track_block(args.track, rows, rows["frame"].tolist(), crops, title))
        print(f"strook in {out}")
        return

    tracks = {track: rows.sort_values("frame") for track, rows in detections.groupby("track_ongeknipt") if len(rows) >= 2}
    shown = {track: shown_frames(rows) for track, rows in tracks.items()}
    wanted = {}
    for track, rows in tracks.items():
        keep = rows[rows["frame"].isin(shown[track])]
        for row in keep.itertuples():
            wanted.setdefault((row.video, row.frame), []).append(row)
    print(f"{len(tracks)} tracks van twee of meer kaders; uitsneden maken ...")
    crops = collect_crops(wanted)

    SHEETS.mkdir(parents=True, exist_ok=True)
    index_rows, blocks, sheet, height = [], [], 1, 0
    order = sorted(tracks, key=lambda t: (video_number(tracks[t]["video"].iloc[0]), tracks[t]["frame"].min()))

    def flush():
        nonlocal blocks, sheet, height
        if not blocks:
            return
        width = max(b.shape[1] for b in blocks)
        image = np.vstack([np.pad(b, ((0, 0), (0, width - b.shape[1]), (0, 0)), constant_values=255) for b in blocks])
        save_jpg(SHEETS / f"vel_{sheet:04d}.jpg", image)
        blocks, height, sheet = [], 0, sheet + 1

    for track in order:
        rows = tracks[track]
        video = rows["video"].iloc[0]
        title = (f"track {track} | Video {video_number(video)} | {len(rows)} kaders | frames "
                 f"{rows['frame'].min()}-{rows['frame'].max()}" + ("" if len(shown[track]) == len(rows)
                                                                    else f" | {len(shown[track])} getoond"))
        block = track_block(track, rows, shown[track], crops, title)
        if height and height + block.shape[0] > SHEET_HEIGHT:
            flush()
        blocks.append(block)
        height += block.shape[0]
        index_rows.append({"vel": f"vel_{sheet:04d}.jpg", "track": track, "video": video,
                           "eerste_frame": rows["frame"].min(), "laatste_frame": rows["frame"].max(),
                           "kaders": len(rows), "getoonde_frames": " ".join(map(str, shown[track]))})
    flush()
    for old in sorted(SHEETS.glob("vel_*.jpg")):   # vellen van een eerdere, langere run
        if int(old.stem.split("_")[1]) >= sheet:
            old.unlink()
    write_frozen(AUDIT / "alle_tracks_index.csv",
                 pd.DataFrame(index_rows).to_csv(index=False, lineterminator="\n").encode("utf-8"))
    print(f"{len(index_rows)} tracks op {sheet - 1} vellen in {SHEETS.relative_to(REPO)}/")


DETECTIONS_VIDEOS = []

if __name__ == "__main__":
    main()
