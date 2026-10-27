"""Maakt de plaatjes waarmee álle tracks gecontroleerd worden: blijft het kader van begin tot eind op hetzelfde
gezicht (of op hetzelfde ding)?

Van elke track van twee of meer kaders (uit data/tracks/detections_0.3.csv, met het tracknummer van vóór de
correctie uit de controle: kolom track_ongeknipt) komt een strook met ÁLLE kaders van die track op volgorde, zodat
elk frame nagelopen wordt; een lange track loopt door over meer vellen. Elke uitsnede toont het kader met wat ruimte eromheen, lichter gemaakt als het gezicht donker is, met het
framenummer eronder. Een gewoon kader is groen; een verlenging (score 0,2 tot 0,3) is oranje en heeft een v
achter het framenummer.

Uitvoer:
    data/audit/alle_tracks/vel_0001.jpg ...   de vellen (gaan niet mee naar GitHub; dit programma maakt ze opnieuw)
    data/audit/alle_tracks_index.csv           welke track op welk vel (of welke vellen) staat

Met --beelden maakt het programma een plaatje van ÉLK beeld van elk fragment (1280 pixels breed, lichter gemaakt als
het beeld donker is), met alle kaders erin, genummerd per beeld. Daarmee wordt elk beeld nagelopen op gezichten zonder
kader (die de computer gemist heeft), ook in beelden waarin de computer niets vond. Uitvoer: data/audit/alle_beelden/
(de plaatjes, en kaders.csv: welk nummer bij welk kader en welke track hoort; gaat niet mee naar GitHub).

Met --uitvoer <map> komen de vellen en de plaatjes in <map>/alle_tracks/ en <map>/alle_beelden/ in plaats van in
data/audit/. Dat is handig als de projectmap in iCloud of OneDrive staat: alle plaatjes samen zijn een paar gigabyte,
en die hoeven niet naar de cloud.

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

CROP = 96             # grootte van een uitsnede op de vellen, in pixels
PER_ROW = 14          # uitsneden per rij op de vellen
STRIP_CROP = 120      # grootte van een uitsnede in een losse strook (--track), om een vondst precies na te kijken
STRIP_PER_ROW = 11
SHEET_HEIGHT = 820    # een vel wordt niet hoger dan dit (pixels), zodat het op een gewoon scherm past zonder te verkleinen
GREEN, ORANGE = (60, 200, 60), (0, 150, 255)


def lighter(image: np.ndarray, box: tuple) -> np.ndarray:
    """Maak een donkere uitsnede lichter, net als 'Beeld lichter' in de labelapp (factor 1 tot 5)."""
    x, y, w, h = box
    face = cv2.cvtColor(image[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)
    factor = min(5.0, max(1.0, 120 / max(float(face.mean()) if face.size else 120, 8)))
    return np.clip(image.astype(np.float32) * factor, 0, 255).astype(np.uint8)


def crop(frame: np.ndarray, row, size: int = CROP) -> np.ndarray:
    """Een vierkante uitsnede rond het kader (1,8 keer het kader), met het kader erin getekend en het framenummer eronder."""
    x, y, w, h = int(row.x), int(row.y), int(row.w), int(row.h)
    side = int(1.8 * max(w, h))
    pad = side
    padded = cv2.copyMakeBorder(frame, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(0, 0, 0))
    cx, cy = x + w // 2 + pad, y + h // 2 + pad
    region = padded[cy - side // 2:cy - side // 2 + side, cx - side // 2:cx - side // 2 + side]
    box_in_region = (x + pad - (cx - side // 2), y + pad - (cy - side // 2), w, h)
    region = lighter(region, box_in_region)
    scale = size / side
    tile = cv2.resize(region, (size, size), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    bx, by = int(box_in_region[0] * scale), int(box_in_region[1] * scale)
    cv2.rectangle(tile, (bx, by), (bx + int(w * scale), by + int(h * scale)), ORANGE if row.verlengd else GREEN, 2)
    label = np.full((18, size, 3), 255, np.uint8)
    cv2.putText(label, f"{int(row.frame)}{' v' if row.verlengd else ''}", (4, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                (0, 0, 0), 1, cv2.LINE_AA)
    return np.vstack([tile, label])


def collect_crops(wanted: dict, size: int = CROP) -> dict:
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
                crops[(row.track_ongeknipt, index)] = crop(frame, row, size)
            index += 1
        capture.release()
        print(f"  {video}: {len(frames)} frames gelezen")
    return crops


def track_rows(track: int, frames: list, crops: dict, per_row: int = PER_ROW) -> list:
    """De rijen uitsneden van één track, op volgorde, met hoogstens per_row uitsneden per rij."""
    tiles = [crops[(track, frame)] for frame in frames]
    while len(tiles) % per_row:
        tiles.append(np.full_like(tiles[0], 255))
    return [np.hstack([np.pad(t, ((2, 2), (2, 2), (0, 0)), constant_values=255) for t in tiles[i:i + per_row]])
            for i in range(0, len(tiles), per_row)]


def head_row(title: str, width: int) -> np.ndarray:
    head = np.full((26, width, 3), 255, np.uint8)
    cv2.putText(head, title, (4, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
    return head


def track_block(track: int, rows: pd.DataFrame, frames: list, crops: dict, title: str, per_row: int = PER_ROW) -> np.ndarray:
    """De strook van één track: een kopregel en rijen uitsneden."""
    rows_img = track_rows(track, frames, crops, per_row)
    return np.vstack([head_row(title, rows_img[0].shape[1]), *rows_img,
                      np.full((10, rows_img[0].shape[1], 3), 255, np.uint8)])


def save_jpg(path: Path, image: np.ndarray) -> None:
    ok, data = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not path.exists() or path.read_bytes() != data.tobytes():   # een vel dat al zo bestaat, blijft staan
        path.write_bytes(data.tobytes())


def short_name(video: str) -> str:
    """De korte naam van een video op de vellen, bijvoorbeeld "Das Boot 2a"."""
    return Path(video).stem.split(" [")[0]


def shown(path: Path) -> str:
    """Een pad om te tonen: ten opzichte van de map KTAI als het daarin ligt."""
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


FRAMES_DIR = AUDIT / "alle_beelden"
FRAME_WIDTH = 1280


def every_frame(detections: pd.DataFrame) -> None:
    """Eén beeld per plaatje, met alle kaders genummerd (groen gewoon, oranje verlenging)."""
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(MOVIES.glob("*.mp4")):   # alle fragmenten, ook een beeld zonder enig kader
        video = path.name
        mine = detections[detections["video"] == video]
        by_frame = {frame: group.sort_values("x") for frame, group in mine.groupby("frame")}
        capture, index = cv2.VideoCapture(str(path)), 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            scale = FRAME_WIDTH / frame.shape[1]
            small = cv2.resize(frame, (FRAME_WIDTH, round(frame.shape[0] * scale)), interpolation=cv2.INTER_AREA)
            mean = float(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).mean())
            factor = min(3.0, max(1.0, 90 / max(mean, 8)))   # een donker beeld lichter, zoals in de labelapp
            small = np.clip(small.astype(np.float32) * factor, 0, 255).astype(np.uint8)
            numbered = []
            for number, row in enumerate((by_frame[index].itertuples() if index in by_frame else []), 1):
                x, y, w, h = (round(v * scale) for v in (row.x, row.y, row.w, row.h))
                colour = ORANGE if row.verlengd else GREEN
                cv2.rectangle(small, (x, y), (x + w, y + h), colour, 2)
                cv2.putText(small, str(number), (x + 2, max(14, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3)
                cv2.putText(small, str(number), (x + 2, max(14, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, colour, 1)
                numbered.append((number, row))
            bar = np.full((24, FRAME_WIDTH, 3), 255, np.uint8)
            cv2.putText(bar, f"{short_name(video)} | beeld {index} | {len(numbered)} kaders" +
                        (f" | lichter x{factor:.1f}" if factor > 1.05 else ""), (6, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        (0, 0, 0), 1, cv2.LINE_AA)
            name = f"{short_name(video).replace(' ', '_')}_{index:05d}.jpg"
            save_jpg(FRAMES_DIR / name, np.vstack([bar, small]))
            if not numbered:
                rows.append({"plaatje": name, "video": video, "frame": index, "nummer": 0})
            for number, row in numbered:
                rows.append({"plaatje": name, "video": video, "frame": index, "nummer": number,
                             "track_ongeknipt": int(row.track_ongeknipt), "verlengd": bool(row.verlengd),
                             "x": int(row.x), "y": int(row.y), "w": int(row.w), "h": int(row.h)})
            index += 1
        capture.release()
        print(f"  {video}: {index} beelden")
    pd.DataFrame(rows).to_csv(FRAMES_DIR / "kaders.csv", index=False, lineterminator="\n")
    print(f"plaatjes van alle beelden in {shown(FRAMES_DIR)}/")


def main() -> None:
    parser = argparse.ArgumentParser(description="Maak de controleplaatjes van alle tracks")
    parser.add_argument("--track", type=int, help="alleen deze track (tracknummer van vóór de correctie)")
    parser.add_argument("--van", type=int, help="eerste frame (met --track)")
    parser.add_argument("--tot", type=int, help="laatste frame (met --track)")
    parser.add_argument("--out", type=Path, help="bestand voor de strook (met --track)")
    parser.add_argument("--stappen", type=int, help="zoveel gelijk verdeelde kaders in plaats van alle (met --track)")
    parser.add_argument("--beelden", action="store_true", help="plaatjes van elk beeld van elk fragment, met alle kaders")
    parser.add_argument("--uitvoer", type=Path, help="map voor de vellen (alle_tracks/) en de plaatjes van de beelden "
                        "(alle_beelden/) in plaats van data/audit/, bijvoorbeeld een map buiten iCloud of OneDrive")
    args = parser.parse_args()
    global SHEETS, FRAMES_DIR
    if args.uitvoer:
        SHEETS, FRAMES_DIR = args.uitvoer / "alle_tracks", args.uitvoer / "alle_beelden"
    check_frozen("data/tracks/detections_0.3.csv")
    detections = pd.read_csv(DETECTIONS)

    if args.beelden:
        every_frame(detections)
        return

    if args.track is not None:   # één strook met alle kaders tussen twee frames
        rows = detections[detections["track_ongeknipt"] == args.track].sort_values("frame")
        rows = rows[(rows["frame"] >= (args.van if args.van is not None else -1)) &
                    (rows["frame"] <= (args.tot if args.tot is not None else 10 ** 9))]
        if rows.empty:
            raise SystemExit("Geen kaders gevonden voor deze track en deze frames.")
        if args.stappen and len(rows) > args.stappen:   # gelijk verdeeld, midden tussen de stappen in
            rows = rows.iloc[sorted({min(len(rows) - 1, int((k + 0.5) * len(rows) / args.stappen))
                                     for k in range(args.stappen)})]
        crops = collect_crops({key: list(group.itertuples()) for key, group in rows.groupby(["video", "frame"])},
                              STRIP_CROP)
        title = (f"track {args.track}, frames {rows['frame'].min()}-{rows['frame'].max()} "
                 f"({'alle kaders' if not args.stappen else f'{len(rows)} kaders gelijk verdeeld'})")
        SHEETS.mkdir(parents=True, exist_ok=True)   # standaard bij de vellen, die niet naar GitHub gaan
        out = args.out or SHEETS / f"track_{args.track}_{rows['frame'].min()}_{rows['frame'].max()}.jpg"
        save_jpg(out, track_block(args.track, rows, rows["frame"].tolist(), crops, title, STRIP_PER_ROW))
        print(f"strook in {out}")
        return

    tracks = {track: rows.sort_values("frame") for track, rows in detections.groupby("track_ongeknipt") if len(rows) >= 2}
    print(f"{len(tracks)} tracks van twee of meer kaders, samen {sum(len(r) for r in tracks.values())} kaders")
    SHEETS.mkdir(parents=True, exist_ok=True)
    index_rows, blocks, sheet, height = [], [], 1, 0

    def flush():
        nonlocal blocks, sheet, height
        if not blocks:
            return
        width = max(b.shape[1] for b in blocks)
        image = np.vstack([np.pad(b, ((0, 0), (0, width - b.shape[1]), (0, 0)), constant_values=255) for b in blocks])
        save_jpg(SHEETS / f"vel_{sheet:04d}.jpg", image)
        blocks, height, sheet = [], 0, sheet + 1

    # video voor video, zodat er nooit te veel uitsneden tegelijk in het geheugen staan
    for video in sorted(detections["video"].unique()):
        mine = sorted((t for t, r in tracks.items() if r["video"].iloc[0] == video), key=lambda t: tracks[t]["frame"].min())
        wanted = {}
        for track in mine:
            for row in tracks[track].itertuples():
                wanted.setdefault((row.video, row.frame), []).append(row)
        if not wanted:
            continue
        crops = collect_crops(wanted)
        for track in mine:
            rows = tracks[track]
            frames = rows["frame"].tolist()
            title = (f"track {track} | {short_name(video)} | {len(rows)} kaders | frames {frames[0]}-{frames[-1]}")
            parts, sheets_of_track = track_rows(track, frames, crops), []
            row_height = parts[0].shape[0]
            while parts:
                room = (SHEET_HEIGHT - height - 36) // row_height
                if room < 1 or (height and room < min(len(parts), 3)):   # liever een nieuw vel dan een paar rijen onderaan
                    flush()
                    room = (SHEET_HEIGHT - 36) // row_height
                chunk, parts = parts[:room], parts[room:]
                label = title if not sheets_of_track else f"{title} | vervolg"
                if parts:
                    label += " | gaat verder op het volgende vel"
                block = np.vstack([head_row(label, chunk[0].shape[1]), *chunk, np.full((10, chunk[0].shape[1], 3), 255, np.uint8)])
                blocks.append(block)
                height += block.shape[0]
                sheets_of_track.append(f"vel_{sheet:04d}.jpg")
            index_rows.append({"vel": " ".join(dict.fromkeys(sheets_of_track)), "track": track, "video": video,
                               "eerste_frame": frames[0], "laatste_frame": frames[-1], "kaders": len(rows)})
        del crops
    flush()
    for old in sorted(SHEETS.glob("vel_*.jpg")):   # vellen van een eerdere, langere run
        if int(old.stem.split("_")[1]) >= sheet:
            old.unlink()
    write_frozen(AUDIT / "alle_tracks_index.csv",
                 pd.DataFrame(index_rows).to_csv(index=False, lineterminator="\n").encode("utf-8"))
    print(f"{len(index_rows)} tracks op {sheet - 1} vellen in {shown(SHEETS)}/")


if __name__ == "__main__":
    main()
