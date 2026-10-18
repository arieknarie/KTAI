"""Gezichten zoeken en volgen (tracken) in alle video's.

Wat dit script doet, per video in movies/, frame voor frame op volgorde:

1. Gezichten zoeken. Elk frame gaat door de MediaPipe Face Detector (model:
   full range, zie models/). Alle gezichten met een detectiescore van minstens
   0,3 worden bewaard, met hun kader en score. Daarnaast gaat elk frame nog een
   keer los door de detector met de grens 0,2. Een kader met een score van 0,2
   tot 0,3 dat niet over een kader van 0,3 of hoger ligt, wordt ook bewaard
   (kolom verlengd): zo'n kader mag een bestaande track alleen verlengen (zie
   punt 3), nooit een nieuwe track beginnen.

2. Beeldwissels markeren. Van elk frame wordt gemeten hoeveel het hele beeld
   lijkt op het vorige frame, op twee manieren:
     - kleur: de kleurverdeling van het hele beeld;
     - structuur: het licht-donkerpatroon van het hele beeld.
   Is de kleur-gelijkenis lager dan 0,9 of de structuur-gelijkenis lager dan
   0,7, dan geldt het frame als beeldwissel (een harde overgang naar een ander
   shot). Bij een beeldwissel stoppen alle tracks.

3. Gezichten koppelen tot tracks. Een track is hetzelfde gezicht in
   opeenvolgende frames. Een gezicht hoort bij een bestaande track als
     - het kader minstens 30% overlapt met het laatste kader van die track
       (intersection over union), en
     - dezelfde plek in het beeld (een ruim gebied rond het kader) nog lijkt
       op die plek in het frame waarin de track het laatst gezien is: de
       correlatie van de grijswaarden is minstens 0,6. Bij een donkere, egale
       plek, waar correlatie niets zegt, mag het gemiddelde verschil in
       helderheid hooguit 6 zijn (op een schaal van 0 tot 255).
   Binnen een doorlopend shot verandert dezelfde plek nauwelijks; bij een
   montagewissel verandert die plek sterk, ook als de kleuren gelijk blijven.
   Omdat steeds dezelfde plek in beide frames wordt vergeleken, maakt het niet
   uit als het kader van de detector een paar pixels verschuift.
   Mist de detector een gezicht hooguit 12 frames (een halve seconde), dan
   loopt de track door: dezelfde plek wordt dan vergeleken met het frame waarin
   de track het laatst gezien is. Nooit over een beeldwissel heen. Eerst
   worden de kaders van 0,3 of hoger gekoppeld, daarna de kaders van 0,2 tot
   0,3 aan de tracks die dan nog over zijn. Een kader van 0,3 of hoger dat bij
   geen enkele track past, begint een nieuwe track; een kader van 0,2 tot 0,3
   dat nergens bij past, vervalt.

4. Dit gebeurt twee keer: met alle gezichten vanaf score 0,3 (plus de
   verlengingen vanaf 0,2), en met alleen de gezichten vanaf score 0,5 (de
   standaardwaarde van MediaPipe, zonder verlengingen).

5. Correcties uit de controle (alleen bij score 0,3). In de controle van alle
   tracks (data/audit/controle_alle_tracks.csv, kolom probleemframes) staan de
   frames waarin een track deels op een ander gezicht of op iets anders staat.
   Op die plekken wordt de track geknipt: elk stuk wordt een eigen track, met
   een nieuw nummer achter de bestaande nummers (zo houden alle andere tracks
   hun nummer). De kolom track_ongeknipt bewaart het nummer van voor het
   knippen.

Uitvoer in data/tracks/:
    frames.csv                 per frame: video, frame, tijd, gelijkenis met het vorige frame, beeldwissel ja/nee
    detections_<drempel>.csv   elk gevonden gezicht: video, frame, tijd, kader, score, verlengd, track, track_ongeknipt
    tracks_<drempel>.csv       elke track: video, begin, einde, aantal kaders (waarvan verlengd)
    run_info.json              waarmee de uitkomsten gemaakt zijn: versies, instellingen en controlegetallen
    raw/                       de gevonden gezichten per video en de vergelijking van dezelfde plek (regel 3);
                               bij een volgende run wordt het zoeken (het langzame deel) overgeslagen. Het
                               bestand bewaart ook de instellingen, de controlegetallen van model en video en
                               de versies van MediaPipe en OpenCV; is daar iets van veranderd, dan zoekt het
                               script vanzelf opnieuw.

De uitkomsten in data/tracks/ zijn vastgelegd in checksums.sha256 (zie code/frozen.py): de labels en
de controle horen bij precies die bestanden. Geeft een nieuwe run een andere uitkomst, dan
overschrijft het script de vastgelegde bestanden niet, maar schrijft het de nieuwe uitkomst ernaast
(.nieuw.csv), tenzij --overschrijven gegeven wordt.

Gebruik (vanuit de map KTAI):
    .venv/bin/python code/track_faces.py
"""

import argparse
import json
import sys
from importlib import metadata
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from frozen import sha256, write_frozen

REPO = Path(__file__).resolve().parent.parent
MOVIES = REPO / "movies"
MODEL = REPO / "models" / "blaze_face_full_range.tflite"
OUTPUT = REPO / "data" / "tracks"
AUDIT_FILE = REPO / "data" / "audit" / "controle_alle_tracks.csv"
EXPECTED_FRAMES = {   # zoveel frames leest OpenCV van elke video; een ander aantal geeft andere framenummers
    "Das Boot - die Auferstehung [Oqek9Ktuwy8].mp4": 8817,
    "Das Boot Mon Gars Filmmusik [LnFceG2lL3U].mp4": 3730,
    "Go Back Johann [qa3jt_GXMts].mp4": 2565,
}

MIN_SCORE = 0.3                 # alle gezichten vanaf deze detectiescore worden bewaard
LOW_SCORE = 0.2                 # kaders vanaf deze score mogen een bestaande track verlengen (punt 1 en 3)
SCORE_THRESHOLDS = (0.3, 0.5)   # voor beide drempels worden tracks gemaakt
CUT_COLOUR = 0.9                # kleur-gelijkenis met het vorige frame lager dan dit: beeldwissel
CUT_STRUCTURE = 0.7             # structuur-gelijkenis met het vorige frame lager dan dit: beeldwissel
MIN_OVERLAP = 0.3               # minimale overlap (IoU) met het laatste kader van de track
MIN_PLACE_SIMILARITY = 0.6      # minimale correlatie van dezelfde plek in beide frames
FLAT_STD = 6                    # spreiding (grijswaarden) waaronder een plek als egaal geldt
MAX_FLAT_DIFFERENCE = 6         # maximaal gemiddeld verschil in helderheid bij een egale plek
MAX_GAP = 12                    # zoveel frames (een halve seconde) mag een gezicht ontbreken zonder dat de track stopt
CACHE_VERSION = 5               # verhogen als de manier van zoeken of de inhoud van raw/ verandert


def normalised(gray: np.ndarray, size: tuple) -> np.ndarray:
    """Grijsbeeld verkleind tot `size`, met gemiddelde 0 en spreiding 1 (voor correlatie)."""
    small = cv2.resize(gray, size, interpolation=cv2.INTER_AREA).astype(np.float32)
    return (small - small.mean()) / (small.std() + 1e-6)


def correlation(a: np.ndarray, b: np.ndarray) -> float:
    """Correlatie van twee genormaliseerde grijsbeelden: 1 = gelijk, 0 = niets gemeen."""
    return float((a * b).mean())


def place(gray: np.ndarray, box: tuple) -> np.ndarray:
    """Ruim gebied rond een kader (het kader plus een halve kaderbreedte aan elke kant),
    licht vervaagd en verkleind tot 48 x 48, om dezelfde plek in twee frames te vergelijken."""
    x, y, w, h = box
    margin = int(0.5 * max(w, h))
    height, width = gray.shape
    region = gray[max(0, y - margin):min(height, y + h + margin), max(0, x - margin):min(width, x + w + margin)]
    region = cv2.GaussianBlur(region, (5, 5), 0)
    return cv2.resize(region, (48, 48), interpolation=cv2.INTER_AREA).astype(np.float32)


def same_place(a: np.ndarray, b: np.ndarray) -> bool:
    """Lijkt dezelfde plek in twee frames nog op elkaar? (zie de uitleg bovenaan)"""
    if a.std() < FLAT_STD or b.std() < FLAT_STD:
        return float(np.abs(a - b).mean()) <= MAX_FLAT_DIFFERENCE
    ncc = float(((a - a.mean()) * (b - b.mean())).mean() / (a.std() * b.std()))
    return ncc >= MIN_PLACE_SIMILARITY


def colour_histogram(frame: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [16, 16], [0, 180, 0, 256])
    return cv2.normalize(hist, hist)


def overlap(a: tuple, b: tuple) -> float:
    """Intersection over union van twee kaders (x, y, breedte, hoogte)."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    iw = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    ih = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = iw * ih
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def boxes(result, frame: np.ndarray) -> list:
    """De kaders (x, y, breedte, hoogte) en scores uit een uitkomst van de detector."""
    found = []
    for detection in result.detections:
        box = detection.bounding_box
        # MediaPipe gaf in onze proef nooit een negatieve x of y: valt een gezicht links of boven voor een deel buiten
        # het beeld, dan staat het kader tegen de rand en houdt het ongeveer de maat van het hele gezicht (het kader steekt
        # dan rechts of onder voorbij het gezicht uit). Rechts en onder wordt het kader hier afgekapt aan de rand.
        x, y = max(0, box.origin_x), max(0, box.origin_y)
        w = min(box.width, frame.shape[1] - x)
        h = min(box.height, frame.shape[0] - y)
        if w >= 2 and h >= 2:
            found.append(((x, y, w, h), round(detection.categories[0].score, 4)))
    return found


def analyse_video(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Zoek de gezichten en meet de beeldwissels in elk frame van één video, op volgorde.

    Geeft (frames, detections). Het resultaat wordt bewaard in raw/.
    """
    # De cache bevat ook de vergelijking van dezelfde plek (regel 3); die hangt af van de instellingen hieronder.
    settings = {"cache_version": CACHE_VERSION, "min_score": MIN_SCORE, "low_score": LOW_SCORE, "max_gap": MAX_GAP,
                "flat_std": FLAT_STD,
                "max_flat_difference": MAX_FLAT_DIFFERENCE, "min_place_similarity": MIN_PLACE_SIMILARITY,
                "model_sha256": sha256(MODEL), "video_sha256": sha256(path),
                "mediapipe": metadata.version("mediapipe"), "opencv": cv2.__version__}
    cache = OUTPUT / "raw" / f"{path.stem}.pkl"
    if cache.exists():
        stored = pd.read_pickle(cache)
        if len(stored) == 3 and stored[2] == settings:
            frames, detections, _ = stored
            print(f"  {path.name}: {len(frames)} frames, {len(detections)} gezichten (eerder gevonden)")
            return frames, detections
        print(f"  {cache.name}: gemaakt met andere instellingen of versies, opnieuw zoeken")

    options = vision.FaceDetectorOptions(
        # altijd de processor (CPU): de grafische kaart (GPU) vindt andere gezichten
        base_options=mp_python.BaseOptions(model_asset_path=str(MODEL), delegate=mp_python.BaseOptions.Delegate.CPU),
        running_mode=vision.RunningMode.VIDEO,  # vereist frames op volgorde
        min_detection_confidence=MIN_SCORE,
    )
    detector = vision.FaceDetector.create_from_options(options)
    # een tweede, losse detector (elk frame apart) met de lagere grens, voor de verlengingen (punt 1)
    low_detector = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(MODEL), delegate=mp_python.BaseOptions.Delegate.CPU),
        running_mode=vision.RunningMode.IMAGE,
        min_detection_confidence=LOW_SCORE,
    ))
    video = cv2.VideoCapture(str(path))
    fps = video.get(cv2.CAP_PROP_FPS)
    if not video.isOpened() or fps <= 0:
        raise SystemExit(f"{path.name}: OpenCV kan deze video niet openen. Controleer de installatie met "
                         "code/check_setup.py (zie docs/zelf_draaien.md).")
    frame_rows, face_rows = [], []
    previous_hist = previous_structure = None
    recent = []   # grijsbeelden van de laatste MAX_GAP + 1 frames, nieuwste eerst
    frame_index = 0
    while True:
        ok, frame = video.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hist, structure = colour_histogram(frame), normalised(gray, (64, 36))
        colour_sim = 1.0 if previous_hist is None else float(cv2.compareHist(previous_hist, hist, cv2.HISTCMP_CORREL))
        structure_sim = 1.0 if previous_structure is None else correlation(previous_structure, structure)
        previous_hist, previous_structure = hist, structure
        frame_rows.append({
            "video": path.name, "frame": frame_index, "time_s": round(frame_index / fps, 3),
            "colour_similarity": round(colour_sim, 4), "structure_similarity": round(structure_sim, 4),
            "cut": colour_sim < CUT_COLOUR or structure_sim < CUT_STRUCTURE,
        })

        timestamp_ms = int(round(frame_index * 1000 / fps))
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        found = [(box, score, False) for box, score in boxes(detector.detect_for_video(image, timestamp_ms), frame)]
        strong = [box for box, _, _ in found]
        found += [(box, score, True) for box, score in boxes(low_detector.detect(image), frame)
                  if score < MIN_SCORE and all(overlap(box, other) < MIN_OVERLAP for other in strong)]
        for (x, y, w, h), score, extension in found:
            here = place(gray, (x, y, w, h))
            face_rows.append({
                "video": path.name, "frame": frame_index, "time_s": round(frame_index / fps, 3),
                "x": x, "y": y, "w": w, "h": h, "score": score, "verlengd": extension,
                # unchanged[g-1]: lijkt deze plek nog op dezelfde plek g frames eerder? (voor het koppelen)
                "unchanged": [same_place(here, place(old, (x, y, w, h))) for old in recent],
            })
        recent = [gray] + recent[:MAX_GAP]
        frame_index += 1
    video.release()
    detector.close()
    low_detector.close()
    expected = EXPECTED_FRAMES.get(path.name)
    if frame_index == 0:
        raise SystemExit(f"{path.name}: OpenCV kan geen enkel frame uit deze video lezen. Controleer de installatie "
                         "met code/check_setup.py.")
    if expected is not None and frame_index != expected:
        raise SystemExit(f"{path.name}: OpenCV las {frame_index} frames, verwacht {expected}. Dan kloppen de "
                         "framenummers niet. Controleer de installatie met code/check_setup.py.")

    frames, detections = pd.DataFrame(frame_rows), pd.DataFrame(face_rows)
    cache.parent.mkdir(parents=True, exist_ok=True)
    pd.to_pickle((frames, detections, settings), cache)
    print(f"  {path.name}: {len(frames)} frames, {int(frames['cut'].sum())} beeldwissels, "
          f"{int((~detections['verlengd']).sum())} gezichten (score >= {MIN_SCORE}) en "
          f"{int(detections['verlengd'].sum())} mogelijke verlengingen (score {LOW_SCORE} tot {MIN_SCORE})")
    return frames, detections


def make_tracks(frames: pd.DataFrame, detections: pd.DataFrame) -> list[int]:
    """Geef elk gezicht een tracknummer (-1: een verlenging die nergens bij past). Frames worden op volgorde
    afgelopen. Eerst worden de kaders van 0,3 of hoger gekoppeld, daarna de verlengingen (zie punt 3 bovenaan)."""
    track_ids = [-1] * len(detections)
    by_frame = {frame: rows for frame, rows in detections.groupby("frame")}
    active = []   # per track: [tracknummer, laatste frame, laatste kader]
    next_id = 0
    for frame, is_cut in zip(frames["frame"], frames["cut"]):
        if is_cut:
            active = []  # beeldwissel: alle tracks stoppen
        active = [t for t in active if frame - t[1] <= MAX_GAP + 1]
        rows = by_frame.get(frame)
        if rows is None:
            continue
        used_rows, used_tracks = set(), set()
        for extensions in (False, True):   # eerst de gewone kaders, daarna de verlengingen
            candidates = []
            for i, row in rows[rows["verlengd"] == extensions].iterrows():
                box = (row["x"], row["y"], row["w"], row["h"])
                for k, track in enumerate(active):
                    gap = frame - track[1]  # 1 = vorige frame
                    iou = overlap(box, track[2])
                    if iou >= MIN_OVERLAP and gap <= len(row["unchanged"]) and row["unchanged"][gap - 1]:
                        candidates.append((iou, i, k))
            for iou, i, k in sorted(candidates, reverse=True):  # beste overlap eerst
                if i in used_rows or k in used_tracks:
                    continue
                used_rows.add(i)
                used_tracks.add(k)
                row = rows.loc[i]
                active[k][1:] = [frame, (row["x"], row["y"], row["w"], row["h"])]
                track_ids[detections.index.get_loc(i)] = active[k][0]
        for i, row in rows.iterrows():
            if i not in used_rows and not row["verlengd"]:   # een verlenging begint nooit een track
                active.append([next_id, frame, (row["x"], row["y"], row["w"], row["h"])])
                track_ids[detections.index.get_loc(i)] = next_id
                next_id += 1
    return track_ids


def split_audited_tracks(detections: pd.DataFrame) -> pd.DataFrame:
    """Knip de tracks waarvan de controle liet zien dat ze deels op iets anders staan (zie punt 5 bovenaan).
    Een stuk dat een nieuw nummer krijgt, begint bij het eerste frame van een probleemstuk, of bij het eerste
    frame na een probleemstuk."""
    detections["track_ongeknipt"] = detections["track"]
    if not AUDIT_FILE.exists():
        return detections
    audit = pd.read_csv(AUDIT_FILE)
    # De controle hoort bij precies deze tracks: video, eerste en laatste frame en aantal frames moeten kloppen.
    # (Na een bewust andere run kunnen de tracks andere nummers hebben; dan zouden de knippen op de verkeerde
    # tracks vallen.)
    tracks = detections.groupby("track").agg(video=("video", "first"), first=("frame", "min"),
                                               last=("frame", "max"), faces=("frame", "size"))
    mismatch = [row.track for row in audit.itertuples()
                if row.track not in tracks.index or tuple(tracks.loc[row.track]) !=
                (row.video, row.eerste_frame, row.laatste_frame, row.frames)]
    if mismatch:
        print(f"  LET OP: de controle in {AUDIT_FILE.name} hoort niet bij deze tracks ({len(mismatch)} tracks kloppen "
              f"niet, bijvoorbeeld track {mismatch[0]}). De knippen uit de controle worden niet toegepast; de controle "
              "moet opnieuw.")
        return detections
    starts = []  # (track, eerste frame van een nieuw stuk)
    for row in audit[audit["probleemframes"].notna()].itertuples():
        frames = detections.loc[detections["track"] == row.track, "frame"]
        for part in str(row.probleemframes).split(","):
            first, _, last = part.strip().partition("-")
            first, last = int(first), int(last or first)
            if first > frames.min():
                starts.append((row.track, first))
            if last < frames.max():
                starts.append((row.track, last + 1))
    next_id = detections["track"].max() + 1
    for track, start in sorted(set(starts)):
        rows = (detections["track_ongeknipt"] == track) & (detections["frame"] >= start)
        detections.loc[rows, "track"] = next_id
        next_id += 1
    print(f"  {len(set(starts))} knippen in {audit['probleemframes'].notna().sum()} tracks uit de controle")
    return detections


def write_table(table: pd.DataFrame, name: str, overwrite: bool) -> Path:
    """Schrijf een tabel als CSV (altijd met Unix-regeleinden, ook op Windows), zonder een vastgelegd
    bestand te overschrijven als de inhoud anders is (zie code/frozen.py)."""
    return write_frozen(OUTPUT / name, table.to_csv(index=False, lineterminator="\n").encode("utf-8"), overwrite)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gezichten zoeken en volgen in alle video's")
    parser.add_argument("--overschrijven", action="store_true",
                        help="ook bij bestaande labels de uitkomsten vervangen (de labels passen dan misschien niet meer)")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    print("Gezichten zoeken en beeldwissels meten, frame voor frame ...")
    analysed = [analyse_video(path) for path in sorted(MOVIES.glob("*.mp4"))]
    for frames, _ in analysed:  # beeldwissel opnieuw bepalen met de huidige grenzen (de cache bevat de gelijkenis)
        frames["cut"] = (frames["colour_similarity"] < CUT_COLOUR) | (frames["structure_similarity"] < CUT_STRUCTURE)
    written = [write_table(pd.concat([frames for frames, _ in analysed], ignore_index=True), "frames.csv",
                           args.overschrijven)]

    for threshold in SCORE_THRESHOLDS:
        all_detections, offset = [], 0
        for frames, detections in analysed:
            # bij 0,3 ook de verlengingen; bij 0,5 alleen de gewone kaders vanaf 0,5
            wanted = (detections["score"] >= threshold) & ~detections["verlengd"]
            if threshold == MIN_SCORE:
                wanted |= detections["verlengd"]
            kept = detections[wanted].reset_index(drop=True)
            if kept.empty:
                continue
            kept["track"] = make_tracks(frames, kept)
            kept = kept[kept["track"] >= 0].reset_index(drop=True)   # verlengingen die nergens bij passen vervallen
            kept["track"] += offset
            offset = kept["track"].max() + 1
            all_detections.append(kept.drop(columns="unchanged"))
        detections = pd.concat(all_detections, ignore_index=True)
        if threshold == MIN_SCORE:
            detections = split_audited_tracks(detections)
        else:
            detections["track_ongeknipt"] = detections["track"]
        tracks = (detections.groupby("track")
                  .agg(video=("video", "first"), first_frame=("frame", "min"), last_frame=("frame", "max"),
                       start_s=("time_s", "min"), end_s=("time_s", "max"), faces=("frame", "size"),
                       verlengd=("verlengd", "sum"), mean_width=("w", "mean"), mean_score=("score", "mean"),
                       max_score=("score", "max"), track_ongeknipt=("track_ongeknipt", "first"))
                  .round(3).reset_index())
        written.append(write_table(detections, f"detections_{threshold}.csv", args.overschrijven))
        written.append(write_table(tracks, f"tracks_{threshold}.csv", args.overschrijven))

        print(f"\nDetectiescore >= {threshold}: {len(detections)} kaders (waarvan {int(detections['verlengd'].sum())} "
              f"verlengingen), {len(tracks)} tracks")
        for video, group in tracks.groupby("video"):
            print(f"  {video}: {len(group)} tracks"
                  f" (minstens 5 frames: {int((group['faces'] >= 5).sum())},"
                  f" minstens 25 frames: {int((group['faces'] >= 25).sum())})")

    # waarmee deze uitkomsten gemaakt zijn (zonder tijdstip, zodat dit bestand bij dezelfde uitkomst gelijk blijft)
    info = {
        "python": sys.version.split()[0],
        "packages": {name: metadata.version(name) for name in ("mediapipe", "opencv-contrib-python", "numpy", "pandas")},
        "settings": {"min_score": MIN_SCORE, "low_score": LOW_SCORE, "score_thresholds": list(SCORE_THRESHOLDS), "cut_colour": CUT_COLOUR,
                     "cut_structure": CUT_STRUCTURE, "min_overlap": MIN_OVERLAP,
                     "min_place_similarity": MIN_PLACE_SIMILARITY, "flat_std": FLAT_STD,
                     "max_flat_difference": MAX_FLAT_DIFFERENCE, "max_gap": MAX_GAP, "cache_version": CACHE_VERSION},
        "inputs": {p.relative_to(REPO).as_posix(): sha256(p) for p in [MODEL, *sorted(MOVIES.glob("*.mp4"))]},
        "frames": EXPECTED_FRAMES,
        "outputs": {p.relative_to(REPO).as_posix(): sha256(p) for p in written},
    }
    write_frozen(OUTPUT / "run_info.json", (json.dumps(info, indent=1, ensure_ascii=False) + "\n").encode("utf-8"),
                 args.overschrijven)


if __name__ == "__main__":
    main()
