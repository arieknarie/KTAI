"""Zet alles klaar wat in de labelapp (map labeling/) gelabeld moet worden.

Wat dit script doet:

1. Foto's van de acteurs (pictures/personal/<naam>/). De mapnaam is het label.
   - Foto met precies één gezicht: het label van de map wordt automatisch
     toegekend (labeling/automatic_labels.csv). Deze foto's hoeven niet in de
     labelapp.
   - Foto met meer dan één gezicht: gaat naar de labelapp.
   - Foto zonder gezicht of een bestand dat niet te lezen is: wordt gemeld en
     overgeslagen.
2. Stills uit de film (pictures/inCharacter/). Alle gezichten worden gezocht en
   gaan naar de labelapp. Een still die als exact hetzelfde bestand twee keer
   in de map staat, wordt maar één keer getoond. De stills stonden al in mappen
   met een naam erop, maar die indeling is niet gecontroleerd. Daarom krijgt de
   labelaar de bestandsnaam en de mapnaam niet te zien: een still heet in de
   labelapp "Still 1 van 33" enzovoort, de volgorde is los van de mappen
   (gesorteerd op de md5-controlesom van het bestand, dus elke keer hetzelfde),
   en ook in items.json en labels.csv heet een still alleen still_01 enzovoort.
   Welk bestand bij welke still hoort, staat in data/stills_index.csv (buiten de
   map van de labelaar).
3. Video's (movies/). Per track (uit code/track_faces.py, detectiescore 0,3)
   wordt één frame getoond: het frame met de hoogste detectiescore x
   kaderbreedte. De video's heten in de labelapp Video 1, Video 2 en Video 3,
   omdat de titel van een video een naam kan bevatten. Bij elke track staan ook
   de kaders van de andere tracks in hetzelfde frame (others): de labelapp toont
   die dun en grijs, zodat de labelaar ziet welke gezichten de computer daar ook
   gevonden heeft.
4. Referentiestrook: uitsneden van de gezichten op de foto's van de acteurs
   met precies één gezicht. Die labels staan vast en helpen bij het herkennen.

Gezichten in foto's en stills worden gezocht met dezelfde MediaPipe Face
Detector als in de video's (full range, detectiescore vanaf 0,3).

Uitvoer in labeling/:
    items.json             alles wat de labelapp toont, in de volgorde waarin het getoond wordt
    images/                de plaatjes die de labelapp toont
    automatic_labels.csv   de automatisch gelabelde foto's van de acteurs
In data/:
    stills_index.csv       welk bestand bij welke still hoort (still, bestand, ook_als), en of een still
                           (bijna) hetzelfde beeld is als een frame uit de testvideo's
                           (uit_video, uit_frame, gelijkenis)

Het script rekent eerst alles uit en schrijft pas aan het eind iets weg:
- Bestaan er al labels (labeling/labels.csv) die bij de nieuwe items niet meer
  zouden passen (een ander bestand, frame of kader bij hetzelfde gezicht-id), dan
  schrijft het script niets en stopt het, tenzij --forceer gegeven wordt: anders
  gaat labelwerk verloren.
- items.json, automatic_labels.csv, data/stills_index.csv en de plaatjes in
  labeling/images/ zijn vastgelegd in checksums.sha256 (zie code/frozen.py). Is de
  nieuwe uitkomst anders, dan worden die bestanden niet overschreven: de nieuwe
  uitkomst komt ernaast als
  <naam>.nieuw.<ext>, en de plaatjes in labeling/images/ blijven zoals ze waren
  (die horen bij de vastgelegde items.json). Alleen met --overschrijven worden ze
  vervangen.

Gebruik (vanuit de map KTAI, na code/track_faces.py):
    .venv/bin/python code/make_label_items.py
"""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

import cv2
import numpy as np
import mediapipe as mp
import pandas as pd
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from frozen import check_frozen, frozen, write_frozen

REPO = Path(__file__).resolve().parent.parent
PERSONAL = REPO / "pictures" / "personal"
STILLS = REPO / "pictures" / "inCharacter"
MOVIES = REPO / "movies"
MODEL = REPO / "models" / "blaze_face_full_range.tflite"
TRACKS = REPO / "data" / "tracks"
LABELING = REPO / "labeling"
IMAGES = LABELING / "images"

MIN_SCORE = 0.3        # dezelfde detectiedrempel als bij de video's
MIN_TRACK_FRAMES = 1   # tracks met minder frames worden niet getoond (zie README, stap 1)
JPEG_QUALITY = 88

CHOICES = [
    {"key": "DerAlte", "name": "Der Alte", "shortcut": "1"},
    {"key": "FritzGrade", "name": "Fritz Grade", "shortcut": "2"},
    {"key": "Johann", "name": "Johann", "shortcut": "3"},
    {"key": "Werner", "name": "Werner", "shortcut": "4"},
    {"key": "other", "name": "Figurant", "shortcut": "5"},
    {"key": "no_face", "name": "Geen gezicht", "shortcut": "6"},
    {"key": "unknown", "name": "Weet niet", "shortcut": "7"},
]
PERSON_NAMES = {c["key"]: c["name"] for c in CHOICES[:4]}
AUTOMATIC_COLUMNS = ["face", "item", "label", "labeler", "source", "frame", "x", "y", "w", "h"]   # automatic_labels.csv
VIDEO_GROUPS = {   # neutrale naam per video in de labelapp (een videotitel kan een naam bevatten)
    "Das Boot - die Auferstehung [Oqek9Ktuwy8].mp4": "Video 1",
    "Das Boot Mon Gars Filmmusik [LnFceG2lL3U].mp4": "Video 2",
    "Go Back Johann [qa3jt_GXMts].mp4": "Video 3",
}
STILLS_INDEX = REPO / "data" / "stills_index.csv"
SAME_FRAME = 0.8   # gelijkenis vanaf waar een still hetzelfde beeld is als een frame uit een testvideo


def make_detector():
    options = vision.FaceDetectorOptions(
        # altijd de processor (CPU), net als in code/track_faces.py
        base_options=mp_python.BaseOptions(model_asset_path=str(MODEL), delegate=mp_python.BaseOptions.Delegate.CPU),
        running_mode=vision.RunningMode.IMAGE,
        min_detection_confidence=MIN_SCORE,
    )
    return vision.FaceDetector.create_from_options(options)


def find_faces(detector, image):
    """Kaders [x, y, breedte, hoogte] en scores van alle gezichten, van links naar rechts."""
    result = detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB)))
    faces = []
    height, width = image.shape[:2]
    for detection in result.detections:
        box = detection.bounding_box
        # MediaPipe gaf in onze proef nooit een negatieve x of y: valt een gezicht links of boven voor een deel buiten
        # het beeld, dan staat het kader tegen de rand en houdt het ongeveer de maat van het hele gezicht (het kader steekt
        # dan rechts of onder voorbij het gezicht uit). Rechts en onder wordt het kader hier afgekapt aan de rand.
        x, y = max(0, box.origin_x), max(0, box.origin_y)
        w = min(box.origin_x + box.width, width) - x
        h = min(box.origin_y + box.height, height) - y
        if w >= 2 and h >= 2:
            faces.append({"box": [int(x), int(y), int(w), int(h)], "score": round(detection.categories[0].score, 3)})
    return sorted(faces, key=lambda face: face["box"][0])


def read_image(path):
    """Een plaatje lezen, ook als het pad letters als é bevat (cv2.imread kan dat op Windows niet)."""
    data = np.fromfile(str(path), np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None


PENDING_IMAGES = {}   # plaatjes die pas aan het eind geschreven worden: {pad: jpeg-bytes}


def save_image(image, relative):
    """Zet een plaatje klaar voor labeling/images/ en geef het pad ten opzichte van labeling/. Het plaatje
    wordt pas geschreven in write_images, als vaststaat dat er geschreven mag worden."""
    ok, data = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    PENDING_IMAGES[IMAGES / relative] = data.tobytes()
    return (IMAGES / relative).relative_to(LABELING).as_posix()


def images_digest():
    """Het controlegetal van de klaargezette plaatjes, op dezelfde manier berekend als code/check_setup.py
    (folder_digest) het controlegetal van labeling/images/ berekent."""
    digest = hashlib.sha256()
    for path in sorted(PENDING_IMAGES, key=lambda p: p.relative_to(REPO).as_posix()):
        sha = hashlib.sha256(PENDING_IMAGES[path]).hexdigest()
        digest.update(f"{path.relative_to(REPO).as_posix()} {sha}\n".encode("utf-8"))
    return digest.hexdigest()


def write_images():
    """Schrijf de klaargezette plaatjes. Een bestand dat al precies zo bestaat, wordt niet opnieuw geschreven."""
    written = 0
    for path, data in PENDING_IMAGES.items():
        if not path.exists() or path.read_bytes() != data:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            written += 1
    return written


def remove_unused_images(used):
    """Verwijder plaatjes in labeling/images/ die niet (meer) gebruikt worden. Zo wordt de map niet
    eerst helemaal leeggemaakt: in een map die met een clouddienst gesynchroniseerd wordt, kan dat
    kopieën geven als "000010 2.jpg"."""
    removed = 0
    for path in sorted(IMAGES.rglob("*"), reverse=True):  # bestanden voor hun mappen
        relative = path.relative_to(LABELING).as_posix()
        if path.is_file() and relative not in used:
            path.unlink()
            removed += 1
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    return removed


def picture_item(kind, group, name, image, faces, title, image_name):
    """Een foto of still met al zijn gezichten. `name` komt in het item-id en het gezicht-id: bij een
    foto het pad van het bestand, bij een still alleen de neutrale naam (still_01). De labelaar ziet
    in de app alleen `title`."""
    stored = save_image(image, f"{kind}s/{image_name}.jpg")
    return {
        "id": f"{kind}:{name}", "kind": kind, "group": group, "title": title,
        "image": stored, "width": image.shape[1], "height": image.shape[0],
        "faces": [{"face": f"{name}#{i}", "box": f["box"], "score": f["score"], "source": name}
                  for i, f in enumerate(faces)],
    }


def personal_photos(detector):
    """Foto's van de acteurs: automatische labels, items voor de labelapp en de referentiestrook."""
    items, automatic, references = [], [], {key: [] for key in PERSON_NAMES}
    counts = {"automatisch": 0, "labelapp": 0, "overgeslagen": 0}
    for folder in sorted(PERSONAL.iterdir()):
        if folder.name not in PERSON_NAMES:
            continue
        for path in sorted(folder.iterdir()):
            relative = path.relative_to(REPO).as_posix()
            image = read_image(path)
            if image is None:
                print(f"  {relative}: kan niet gelezen worden, overgeslagen")
                counts["overgeslagen"] += 1
                continue
            faces = find_faces(detector, image)
            if len(faces) == 1:
                x, y, w, h = faces[0]["box"]
                automatic.append({"face": f"{relative}#0", "item": f"photo:{relative}", "label": folder.name,
                                  "labeler": "mapnaam", "source": relative, "frame": "", "x": x, "y": y, "w": w, "h": h})
                margin = int(0.35 * max(w, h))
                crop = image[max(0, y - margin):y + h + margin, max(0, x - margin):x + w + margin]
                crop = cv2.resize(crop, (round(140 * crop.shape[1] / crop.shape[0]), 140), interpolation=cv2.INTER_AREA)
                image_name = f"{path.stem}_{path.suffix[1:].lower()}"  # werner4.jpg en werner4.png krijgen elk een eigen plaatje
                references[folder.name].append(save_image(crop, f"references/{folder.name}/{image_name}.jpg"))
                counts["automatisch"] += 1
            elif faces:
                print(f"  {relative}: {len(faces)} gezichten, gaat naar de labelapp")
                # deze foto's zijn wel gecontroleerd: de mapnaam mag de labelaar zien
                title = f"Foto uit de map {folder.name} van de foto's van de acteurs ({path.name})"
                items.append(picture_item("photo", "Foto's van de acteurs", relative, image, faces,
                                          title, f"{folder.name}_{path.stem}_{path.suffix[1:].lower()}"))
                counts["labelapp"] += 1
            else:
                print(f"  {relative}: geen gezicht gevonden, wordt niet gelabeld")
                counts["overgeslagen"] += 1
    print(f"  {sum(counts.values())} foto's: {counts['automatisch']} automatisch gelabeld, "
          f"{counts['labelapp']} in de labelapp, {counts['overgeslagen']} overgeslagen")
    return items, automatic, references


def thumbnail(image):
    """Klein grijs beeld (64 x 36), genormaliseerd, om hele beelden met elkaar te vergelijken."""
    gray = cv2.resize(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), (64, 36), interpolation=cv2.INTER_AREA).astype(np.float32)
    return ((gray - gray.mean()) / (gray.std() + 1e-6)).ravel()


def stills_in_videos(paths):
    """Voor elke still het frame uit de testvideo's dat het meest op de still lijkt (frames op volgorde
    gelezen). Geeft {pad: (video, frame, gelijkenis)}. Een still met een gelijkenis vanaf SAME_FRAME is
    (bijna) hetzelfde beeld als dat frame; zo'n still mag later niet als extra referentie dienen zonder
    dat frame uit de test te halen."""
    thumbs = np.stack([thumbnail(read_image(path)) for path in paths])
    best = {path: ("", -1, -1.0) for path in paths}
    for video in sorted(MOVIES.glob("*.mp4")):
        capture, index = cv2.VideoCapture(str(video)), 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            similarity = thumbs @ thumbnail(frame) / thumbs.shape[1]
            for path, value in zip(paths, similarity):
                if value > best[path][2]:
                    best[path] = (video.name, index, float(value))
            index += 1
        capture.release()
    return best


def stills(detector):
    """Alle stills, zonder dubbele bestanden, in een volgorde die los staat van de mappen. Elke still
    krijgt een neutrale naam (still_01, still_02, ...); de koppeling met het bestand komt in
    data/stills_index.csv."""
    unique, duplicates = {}, {}
    for path in sorted(STILLS.glob("*/*")):
        if path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        digest = hashlib.md5(path.read_bytes()).hexdigest()
        if digest in unique:
            print(f"  {path.relative_to(REPO)}: zelfde bestand als {unique[digest].relative_to(REPO)}, één keer getoond")
            duplicates[digest] = path
            continue
        unique[digest] = path

    with_faces = []
    for digest in sorted(unique):  # volgorde op controlesom: vast, maar los van de mapnamen
        path = unique[digest]
        image = read_image(path)
        if image is None:
            print(f"  {path.relative_to(REPO)}: kan niet gelezen worden, overgeslagen")
            continue
        faces = find_faces(detector, image)
        if faces:
            with_faces.append((digest, path, image, faces))
        else:
            print(f"  {path.relative_to(REPO)}: geen gezicht gevonden, wordt niet gelabeld")

    in_video = stills_in_videos([path for _, path, _, _ in with_faces])
    items, index_rows = [], []
    for n, (digest, path, image, faces) in enumerate(with_faces, start=1):
        name = f"still_{n:02d}"
        items.append(picture_item("still", "Stills uit de film", name, image, faces, f"Still {n} van {len(with_faces)}", name))
        video, frame, similarity = in_video[path]
        same = similarity >= SAME_FRAME
        index_rows.append({"still": name, "bestand": path.relative_to(REPO).as_posix(),
                           "ook_als": duplicates[digest].relative_to(REPO).as_posix() if digest in duplicates else "",
                           "uit_video": video if same else "", "uit_frame": frame if same else "",
                           "gelijkenis": round(similarity, 3)})
        if same:
            print(f"  {name} is (bijna) hetzelfde beeld als frame {frame} van {video} (gelijkenis {similarity:.2f})")
    print(f"  {len(items)} stills in de labelapp; welk bestand bij welke still hoort: {STILLS_INDEX.relative_to(REPO)}")
    return items, pd.DataFrame(index_rows).to_csv(index=False, lineterminator="\n").encode("utf-8")


def video_tracks():
    """Eén item per track: het beste frame van die track."""
    detections = pd.read_csv(TRACKS / "detections_0.3.csv")
    tracks = pd.read_csv(TRACKS / "tracks_0.3.csv")
    tracks = tracks[tracks["faces"] >= MIN_TRACK_FRAMES]
    detections = detections[detections["track"].isin(tracks["track"])]
    detections["quality"] = detections["score"] * detections["w"]
    best = detections.loc[detections.groupby("track")["quality"].idxmax()]
    # de andere kaders in hetzelfde frame (van andere tracks): de labelapp toont die dun en grijs, zodat de
    # labelaar ziet welke gezichten de computer daar ook gevonden heeft (en die niet als gemist tekent)
    boxes_in_frame = {key: [(row.track, [int(row.x), int(row.y), int(row.w), int(row.h)]) for row in group.itertuples()]
                      for key, group in detections.groupby(["video", "frame"])}
    tracks = tracks.set_index("track")

    items = []
    for video, group_rows in best.groupby("video", sort=False):
        wanted = {}
        for row in group_rows.itertuples():
            wanted.setdefault(row.frame, []).append(row)
        capture = cv2.VideoCapture(str(MOVIES / video))
        frame_index, stored = 0, {}
        while wanted and frame_index <= max(wanted):
            ok, frame = capture.read()
            if not ok:
                raise SystemExit(f"{video}: frame {frame_index} kon niet gelezen worden. Controleer de installatie met "
                                 "code/check_setup.py.")
            if frame_index in wanted:
                stored[frame_index] = (save_image(frame, f"frames/{Path(video).stem}/{frame_index:06d}.jpg"), frame.shape)
            frame_index += 1
        capture.release()
        for row in sorted(group_rows.itertuples(), key=lambda r: tracks.loc[r.track, "start_s"]):
            image, shape = stored[row.frame]
            info = tracks.loc[row.track]
            minutes, tenths = divmod(round(float(info["start_s"]) * 10), 600)  # eerst afronden, dan nooit "2:60.0"
            items.append({
                "id": f"track:{video}#{row.track}", "kind": "track", "group": VIDEO_GROUPS.get(video, video),
                "title": f"{VIDEO_GROUPS.get(video, video)}, vanaf {minutes}:{tenths / 10:04.1f}"
                         f" ({int(info['faces'])} {'frame' if int(info['faces']) == 1 else 'frames'})",
                "image": image, "width": shape[1], "height": shape[0],
                "faces": [{"face": f"{video}#track{row.track}", "box": [int(row.x), int(row.y), int(row.w), int(row.h)],
                           "score": float(row.score), "source": video, "frame": int(row.frame),
                           "track": int(row.track), "first_frame": int(info["first_frame"]),
                           "last_frame": int(info["last_frame"]), "faces": int(info["faces"])}],
                "others": [box for track, box in boxes_in_frame[(video, row.frame)] if track != row.track],
            })
        print(f"  {video}: {len(group_rows)} tracks, {len(stored)} frames opgeslagen")
    return items


def stale_labels(items):
    """Labels in labeling/labels.csv die bij de nieuwe items niet meer passen: hetzelfde gezicht-id, maar een
    ander bestand, frame of kader; bij een zelf getekend gezicht: het item bestaat niet meer of toont een ander
    beeld (zie labeling/app.py, matches_items)."""
    labels_file = LABELING / "labels.csv"
    if not labels_file.exists():
        return []
    faces = {face["face"]: face for item in items for face in item["faces"]}
    by_item = {item["id"]: item for item in items}
    stale = []
    with labels_file.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("how") == "getekend":   # een zelf getekend gezicht: het item moet nog bestaan, met hetzelfde beeld
                item = by_item.get(row.get("item"))
                first = item and item["faces"][0]
                if not item or [str(first["source"]), str(first.get("frame", ""))] != [row.get("source", ""), row.get("frame", "")]:
                    stale.append(row["face"])
                continue
            face = faces.get(row["face"])
            place = face and [face["source"], face.get("frame", ""), *face["box"]]
            if not face or [str(v) for v in place] != [row.get(k, "") for k in ("source", "frame", "x", "y", "w", "h")]:
                stale.append(row["face"])
    return stale


def automatic_csv(automatic):
    text = io.StringIO()
    writer = csv.DictWriter(text, fieldnames=AUTOMATIC_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(automatic)
    return text.getvalue().encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description="Zet alles klaar voor de labelapp")
    parser.add_argument("--forceer", action="store_true", help="ook schrijven als bestaande labels niet meer passen")
    parser.add_argument("--overschrijven", action="store_true",
                        help="vastgelegde bestanden vervangen als de nieuwe uitkomst anders is")
    args = parser.parse_args()
    check_frozen("data/tracks/detections_0.3.csv", "data/tracks/tracks_0.3.csv")
    detector = make_detector()
    print("Foto's van de acteurs ...")
    photo_items, automatic, references = personal_photos(detector)
    print("Stills ...")
    still_items, stills_index = stills(detector)
    print("Video's ...")
    track_items = video_tracks()
    detector.close()

    data = {
        # de labels horen bij precies deze gevonden gezichten; een andere detections_0.3.csv geeft andere tracks
        "detections_sha256": hashlib.sha256((TRACKS / "detections_0.3.csv").read_bytes()).hexdigest(),
        "choices": CHOICES,
        "references": [{"label": key, "name": name, "images": references[key]} for key, name in PERSON_NAMES.items()],
        "items": photo_items + still_items + track_items,
    }
    stale = stale_labels(data["items"])
    if stale and not args.forceer:
        raise SystemExit(f"{len(stale)} label(s) in labeling/labels.csv passen niet bij de nieuwe items (bijvoorbeeld "
                         f"{stale[0]}). Er is niets geschreven. Gebruik --forceer alleen als die labels weg mogen.")

    outputs = {LABELING / "items.json": (json.dumps(data, ensure_ascii=False, indent=1) + "\n").encode("utf-8"),
               LABELING / "automatic_labels.csv": automatic_csv(automatic),
               STILLS_INDEX: stills_index}
    known = frozen()
    changed = [path.relative_to(REPO).as_posix() for path, content in outputs.items()
               if path.relative_to(REPO).as_posix() in known
               and hashlib.sha256(content).hexdigest() != known[path.relative_to(REPO).as_posix()]]
    # de plaatjes zijn ook vastgelegd: een andere computer kan bij een gelijke items.json andere jpg-bytes maken
    if "labeling/images/" in known and images_digest() != known["labeling/images/"]:
        changed.append("labeling/images/")
    if changed and not args.overschrijven:
        for path, content in outputs.items():
            write_frozen(path, content)   # een andere uitkomst komt in <naam>.nieuw.<ext>
        raise SystemExit("De nieuwe uitkomst is anders dan de vastgelegde bestanden (" + ", ".join(changed) + "). Die "
                         "bestanden en de plaatjes in labeling/images/ zijn niet veranderd. Gebruik --overschrijven "
                         "alleen als je bewust een nieuwe versie wilt (de labels horen bij de vastgelegde versie).")

    written = write_images()
    for path, content in outputs.items():
        write_frozen(path, content, overwrite=True)
    used = {item["image"] for item in data["items"]} | {image for person in data["references"] for image in person["images"]}
    removed = remove_unused_images(used)

    faces = sum(len(item["faces"]) for item in data["items"])
    print(f"\n{len(data['items'])} items met {faces} gezichten om te labelen:"
          f" {len(photo_items)} foto's, {len(still_items)} stills, {len(track_items)} tracks")
    print(f"{len(automatic)} foto's van de acteurs automatisch gelabeld via de mapnaam")
    print(f"{len(used)} plaatjes in {IMAGES.relative_to(REPO)}/ ({written} nieuw of veranderd, "
          f"{removed} niet meer gebruikte plaatjes verwijderd)")


if __name__ == "__main__":
    main()
