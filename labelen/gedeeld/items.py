"""Wat er nagekeken wordt en welke kaders daarbij horen. Stap 2, stap 3 en de ground truth gebruiken dit allemaal.

Een item is alles wat één oordeel krijgt: een beeld uit een filmpje, een gelabelde foto of een gelabelde still.
"""

import csv

import cv2
import pandas as pd

from gedeeld.paden import CORRECTIONS, DETECTIONS, FRAMES, INPUT, LABELS, MOVIES, STILLS_INDEX, VERDICTS

NAMES = {"DerAlte": "Der Alte", "FritzGrade": "Fritz Grade", "Johann": "Johann", "Werner": "Werner"}


def merge(boxes: list) -> list:
    """Per persoon één kader (naam, x, y, w, h), om al de kaders van die persoon in het beeld heen."""
    found = {}
    for name, x, y, w, h in boxes:
        if name in found:
            a = found[name]
            x0, y0 = min(a[0], x), min(a[1], y)
            x, y, w, h = x0, y0, max(a[0] + a[2], x + w) - x0, max(a[1] + a[3], y + h) - y0
        found[name] = [x, y, w, h]
    return [[name, *box] for name, box in found.items()]


def items() -> list:
    """Alles wat nagelopen wordt, op volgorde: elk beeld van elk fragment, daarna de foto's en stills."""
    labels = pd.read_csv(LABELS)
    choice = labels.set_index("face")["label"]
    detections = pd.read_csv(DETECTIONS)
    frames = pd.read_csv(FRAMES)
    boxes = {}
    for b in detections.itertuples():
        name = NAMES.get(choice.get(f"{b.video}#track{b.track}"))
        if name:
            boxes.setdefault((b.video, int(b.frame)), []).append((name, b.x, b.y, b.w, b.h))
    for b in labels[labels["how"] == "getekend"].itertuples():      # gezichten die de labelaar zelf tekende
        if b.label in NAMES:
            boxes.setdefault((b.source, int(b.frame)), []).append((NAMES[b.label], b.x, b.y, b.w, b.h))
    result, before = [], (None, set())
    for video, f in frames.groupby("video", sort=True):
        capture = cv2.VideoCapture(str(MOVIES / video))
        w, h = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        capture.release()
        fragment = video.split(" [")[0].rstrip("abc")     # Das Boot 2a en 2b zijn samen één fragment
        for frame in sorted(f["frame"]):
            here = merge(boxes.get((video, int(frame)), []))
            names = {b[0] for b in here}
            gone = sorted(before[1] - names) if before[0] == fragment else []
            result.append({"key": f"{video}#beeld{frame}", "video": video, "frame": int(frame),
                           "title": f"{video.split(' [')[0]}, beeld {frame + 1} van {len(f)}", "w": w, "h": h,
                           "boxes": here, "gone": gone})
            before = (fragment, names)
    stills = pd.read_csv(STILLS_INDEX).set_index("still")["bestand"]
    rest = labels[~labels["item"].str.startswith("track:") & (labels["how"] != "getekend")]
    kinds = rest["item"].drop_duplicates().str.split(":").str[0]
    number = {"photo": 0, "still": 0}
    for item, g in rest.groupby("item", sort=False):
        kind, source = item.split(":", 1)
        number[kind] += 1
        path = INPUT / (source if kind == "photo" else stills[source])
        h, w = cv2.imread(str(path)).shape[:2]
        result.append({"key": item, "path": str(path), "w": w, "h": h,
                       "title": f"{'foto' if kind == 'photo' else 'still'} {number[kind]} van {(kinds == kind).sum()}",
                       "boxes": merge([(NAMES[b.label], b.x, b.y, b.w, b.h) for b in g.itertuples() if b.label in NAMES]),
                       "gone": []})
    return result


def judged(path=VERDICTS) -> dict:
    """Het laatste oordeel per item uit de uitkomst van stap 2: {item: "goed" of "fout"}."""
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {row["item"]: row["oordeel"] for row in csv.DictReader(f)}


def corrected(path=CORRECTIONS) -> dict:
    """De laatste verbetering per item uit de uitkomst van stap 3: {item: [[persoon, x, y, w, h], ...]}."""
    if not path.exists():
        return {}
    rows = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            last = rows.setdefault(r["item"], {"tijd": r["tijd"], "boxes": []})
            if r["persoon"] == "-":                         # gewist met Backspace
                del rows[r["item"]]
                continue
            if r["tijd"] != last["tijd"]:                    # een nieuwere keer opslaan vervangt de oudere
                last["tijd"], last["boxes"] = r["tijd"], []
            if r["persoon"]:
                last["boxes"].append([r["persoon"], int(r["x"]), int(r["y"]), int(r["w"]), int(r["h"])])
    return {item: r["boxes"] for item, r in rows.items()}
