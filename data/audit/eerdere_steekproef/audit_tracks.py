"""LET OP: dit programma hoort bij de vorige manier van volgen (versie 4) en werkt niet meer met de
huidige tracks en mappen; het staat hier alleen als verslag van de eerdere steekproef (zie README.md in deze map).

Controleplaatjes om de kwaliteit van de tracks met het oog te controleren.

Maakt in data/audit/:
    tracks_<n>.jpg   filmstroken: per track 8 uitsneden van het gezicht, gelijk
                     verdeeld van het begin tot het einde van de track. Zo is te
                     zien of een track van begin tot eind hetzelfde gezicht volgt.
    short_<n>.jpg    rasters met uitsneden van korte tracks (1 tot 4 frames). Zo is
                     te zien of de korte tracks echte gezichten zijn.
    audit_index.csv  welke track op welk plaatje in welke rij of vak staat.

Steekproef (detectiescore 0,3):
    - alle tracks van minstens 100 frames;
    - 60 willekeurige tracks van 25 tot 99 frames;
    - 60 willekeurige tracks van 5 tot 24 frames;
    - 150 willekeurige tracks van 1 tot 4 frames.
De steekproef ligt vast in data/audit/audit_index.csv: bestaat dat bestand al, dan
maakt het script de plaatjes opnieuw voor precies dezelfde tracks, in dezelfde
volgorde, zodat de oordelen in data/audit/controle_tracks.csv en
controle_korte_tracks.csv blijven kloppen. Alleen als audit_index.csv ontbreekt,
wordt een nieuwe steekproef getrokken (vaste toevalsgenerator).

Gebruik (vanuit de map KTAI, na code/track_faces.py):
    .venv/bin/python code/audit_tracks.py
    .venv/bin/python code/audit_tracks.py --track 123 --out strook.jpg            # één track, 24 uitsneden
    .venv/bin/python code/audit_tracks.py --track 123 --lichter --out strook.jpg  # idem, lichter gemaakt
      (zo zijn de plaatjes voor controleronde 2 en 3 gemaakt)
"""

import argparse
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from frozen import check_frozen, write_frozen

REPO = Path(__file__).resolve().parent.parent
MOVIES = REPO / "movies"
TRACKS = REPO / "data" / "tracks"
AUDIT = REPO / "data" / "audit"
SEED = 1
STRIP_CROPS = 8          # uitsneden per filmstrook
TRACKS_PER_SHEET = 10    # filmstroken per plaatje
SHORT_PER_SHEET = 30     # uitsneden per raster
CROP = 96                # hoogte van een uitsnede in pixels


def lighter(image):
    """Een donker beeld lichter maken: de lichtste 3% van de pixels wordt ongeveer 220 (van 255)."""
    image = image.astype(np.float32)
    return np.clip(image * (220 / max(20.0, float(np.percentile(image, 97)))), 0, 255).astype(np.uint8)


def crop_face(frame, x, y, w, h, light=False):
    """Het gezicht met een kwart kaderbreedte rand, vierkant en CROP x CROP pixels groot. Een gezicht aan
    de rand van het beeld krijgt een zwarte rand erbij, zodat de uitsnede niet uitgerekt wordt."""
    side = int(max(w, h) * 1.5)
    cx, cy = x + w // 2, y + h // 2
    x0, y0 = cx - side // 2, cy - side // 2
    padded = cv2.copyMakeBorder(frame, side, side, side, side, cv2.BORDER_CONSTANT, value=(0, 0, 0))
    region = padded[y0 + side:y0 + 2 * side, x0 + side:x0 + 2 * side]
    if light:
        region = lighter(region)
    out = cv2.resize(region, (CROP, CROP), interpolation=cv2.INTER_AREA)
    # het kader van de detector, zodat te zien is waar het gezicht precies zat
    scale = CROP / side
    cv2.rectangle(out, (int((x - x0) * scale), int((y - y0) * scale)),
                  (int((x + w - x0) * scale), int((y + h - y0) * scale)), (0, 200, 0), 1)
    return out


def read_frames(video, wanted):
    """De gevraagde frames van één video, op volgorde gelezen."""
    frames, capture, index = {}, cv2.VideoCapture(str(MOVIES / video)), 0
    last = max(wanted) if wanted else -1
    while index <= last:
        ok, frame = capture.read()
        if not ok:
            raise SystemExit(f"{video}: frame {index} kon niet gelezen worden. Controleer de installatie met "
                             "code/check_setup.py.")
        if index in wanted:
            frames[index] = frame
        index += 1
    capture.release()
    return frames


def save_jpg(path, image, quality=90):
    """Een plaatje opslaan, ook als het pad letters als é bevat (cv2.imwrite kan dat op Windows niet)."""
    ok, data = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise SystemExit(f"{path}: plaatje kon niet gemaakt worden")
    Path(path).write_bytes(data.tobytes())


def text(image, value, x, y, scale=0.45):
    cv2.putText(image, value, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 1, cv2.LINE_AA)


def original_tracks(detections):
    """De tracks zoals ze waren vóór het knippen uit de controle (kolom track_ongeknipt; zie
    code/track_faces.py). De controle is op deze tracks gedaan."""
    detections = detections.assign(track=detections["track_ongeknipt"]) if "track_ongeknipt" in detections else detections
    tracks = (detections.groupby("track").agg(video=("video", "first"), faces=("frame", "size")).reset_index())
    return detections, tracks


def dense_strip(track, out, crops=24, light=False):
    """Eén track van dichtbij: `crops` uitsneden, gelijk verdeeld, in 3 rijen, met framenummers. Een
    tracknummer van vóór het knippen toont de hele oorspronkelijke track."""
    detections = pd.read_csv(TRACKS / "detections_0.3.csv")
    if "track_ongeknipt" in detections and track in set(detections["track_ongeknipt"]):
        detections = detections.assign(track=detections["track_ongeknipt"])
    rows = detections[detections["track"] == track].sort_values("frame")
    chosen = rows.iloc[np.unique(np.linspace(0, len(rows) - 1, crops).round().astype(int))]
    frames = read_frames(chosen["video"].iloc[0], set(chosen["frame"]))
    tiles = []
    for r in chosen.itertuples():
        tile = np.vstack([crop_face(frames[r.frame], r.x, r.y, r.w, r.h, light), np.full((18, CROP, 3), 255, np.uint8)])
        text(tile, f"frame {r.frame}", 3, CROP + 13, 0.38)
        tiles.append(np.pad(tile, ((2, 2), (2, 2), (0, 0)), constant_values=255))
    while len(tiles) % 8:
        tiles.append(np.full_like(tiles[0], 255))
    save_jpg(out, np.vstack([np.hstack(tiles[i:i + 8]) for i in range(0, len(tiles), 8)]))
    print(f"track {track}: {len(rows)} frames, {len(chosen)} uitsneden in {out}")


def main():
    parser = argparse.ArgumentParser(description="Controleplaatjes van de tracks")
    parser.add_argument("--track", type=int, help="maak alleen een dichte filmstrook van deze track")
    parser.add_argument("--out", default="strook.jpg", help="bestandsnaam voor --track")
    parser.add_argument("--lichter", action="store_true", help="bij --track: de uitsneden lichter maken")
    args = parser.parse_args()
    check_frozen("data/tracks/detections_0.3.csv", "data/tracks/tracks_0.3.csv", "data/audit/audit_index.csv")
    if args.track is not None:
        dense_strip(args.track, Path(args.out), light=args.lichter)
        return

    AUDIT.mkdir(parents=True, exist_ok=True)
    detections, tracks = original_tracks(pd.read_csv(TRACKS / "detections_0.3.csv"))
    index_file = AUDIT / "audit_index.csv"
    if index_file.exists():
        # de vastgelegde steekproef: dezelfde tracks in dezelfde volgorde
        fixed = pd.read_csv(index_file)
        by_id = tracks.set_index("track")
        long_sample = by_id.loc[fixed[fixed["plaatje"].str.startswith("tracks_")]["track"]].reset_index()
        short_sample = by_id.loc[fixed[fixed["plaatje"].str.startswith("short_")]["track"]].reset_index()
        print(f"steekproef uit {index_file.relative_to(REPO)}")
    else:
        rng = np.random.default_rng(SEED)

        def sample(low, high, n):
            pool = tracks[(tracks["faces"] >= low) & (tracks["faces"] <= high)]
            return pool.iloc[rng.choice(len(pool), min(n, len(pool)), replace=False)]

        long_sample = pd.concat([tracks[tracks["faces"] >= 100], sample(25, 99, 60), sample(5, 24, 60)])
        short_sample = sample(1, 4, 150)

    # welke frames zijn nodig
    picks = {}
    for t in long_sample.itertuples():
        rows = detections[detections["track"] == t.track].sort_values("frame")
        chosen = rows.iloc[np.linspace(0, len(rows) - 1, STRIP_CROPS).round().astype(int)]
        picks[("long", t.track)] = chosen
    for t in short_sample.itertuples():
        picks[("short", t.track)] = detections[detections["track"] == t.track].sort_values("frame").iloc[:1]
    wanted = {}
    for rows in picks.values():
        for r in rows.itertuples():
            wanted.setdefault(r.video, set()).add(r.frame)
    frames = {video: read_frames(video, frames_needed) for video, frames_needed in wanted.items()}

    index_rows = []
    # filmstroken
    long_tracks = list(long_sample.itertuples())
    for sheet, start in enumerate(range(0, len(long_tracks), TRACKS_PER_SHEET), 1):
        strips = []
        for row_number, t in enumerate(long_tracks[start:start + TRACKS_PER_SHEET], 1):
            rows = picks[("long", t.track)]
            crops = [crop_face(frames[r.video][r.frame], r.x, r.y, r.w, r.h) for r in rows.itertuples()]
            label = np.full((CROP, 150, 3), 255, np.uint8)
            text(label, f"rij {row_number}", 4, 20, 0.6)
            text(label, f"track {t.track}", 4, 44)
            text(label, f"{t.faces} frames", 4, 64)
            strips.append(np.hstack([label] + [np.pad(c, ((0, 0), (2, 2), (0, 0)), constant_values=255) for c in crops]))
            strips.append(np.full((6, strips[-1].shape[1], 3), 255, np.uint8))
            index_rows.append({"plaatje": f"tracks_{sheet:02d}.jpg", "plek": f"rij {row_number}", "track": t.track,
                               "video": t.video, "frames": t.faces})
        save_jpg(AUDIT / f"tracks_{sheet:02d}.jpg", np.vstack(strips))
    # rasters met korte tracks
    short_tracks = list(short_sample.itertuples())
    for sheet, start in enumerate(range(0, len(short_tracks), SHORT_PER_SHEET), 1):
        tiles = []
        for cell, t in enumerate(short_tracks[start:start + SHORT_PER_SHEET], 1):
            r = next(picks[("short", t.track)].itertuples())
            tile = np.vstack([crop_face(frames[r.video][r.frame], r.x, r.y, r.w, r.h), np.full((20, CROP, 3), 255, np.uint8)])
            text(tile, f"vak {cell}", 4, CROP + 15)
            tiles.append(np.pad(tile, ((3, 3), (3, 3), (0, 0)), constant_values=255))
            index_rows.append({"plaatje": f"short_{sheet:02d}.jpg", "plek": f"vak {cell}", "track": t.track,
                               "video": t.video, "frames": t.faces})
        while len(tiles) % 6:
            tiles.append(np.full_like(tiles[0], 255))
        grid = np.vstack([np.hstack(tiles[i:i + 6]) for i in range(0, len(tiles), 6)])
        save_jpg(AUDIT / f"short_{sheet:02d}.jpg", grid)
    write_frozen(AUDIT / "audit_index.csv", pd.DataFrame(index_rows).to_csv(index=False, lineterminator="\n").encode("utf-8"))
    print(f"{len(long_tracks)} filmstroken en {len(short_tracks)} korte tracks in {AUDIT.relative_to(REPO)}/")


if __name__ == "__main__":
    main()
