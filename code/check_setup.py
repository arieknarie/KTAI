"""Controleert in een paar seconden of deze computer en deze map klaar zijn om de scripts te draaien.

Wat het script controleert:
1. de versie van Python en van de pakketten in requirements.txt;
2. de controlegetallen (sha256) in checksums.sha256: de video's, het model en de vastgelegde uitkomsten;
3. dat OpenCV van elke video precies het verwachte aantal frames leest (anders kloppen de framenummers niet),
   en dat de pixels van alle frames precies dezelfde zijn als bij het vastleggen (data/tracks/video_pixels.sha256).
   Leest deze computer de video's anders uit, dan kan een nieuwe run andere gezichten en tracks geven: gebruik
   dan de vastgelegde uitkomsten en draai code/track_faces.py niet opnieuw;
4. dat de plaatjes van de labelapp (labeling/images/) en de foto's in pictures/ nog precies dezelfde zijn als bij
   het vastleggen: één controlegetal per map, zodat een plaatje opvalt dat ontbreekt of veranderd is (en in
   pictures/ ook een foto die erbij gezet is);
5. dat er geen kopieën als "bestand 2.jpg" in de map staan (die maakt een clouddienst zoals iCloud soms).

Gebruik (vanuit de map KTAI):
    .venv/bin/python code/check_setup.py               # controleren
    .venv/bin/python code/check_setup.py --vastleggen  # de huidige bestanden vastleggen in checksums.sha256

Bij een probleem eindigt het script met regels die met FOUT beginnen.
"""

import argparse
import hashlib
import json
import re
import sys
from importlib import metadata
from pathlib import Path

from frozen import CHECKSUMS, REPO, frozen, sha256

EXPECTED_FRAMES = {   # zoveel frames leest OpenCV van elke video (zie docs/stap1_gezichten_vinden_en_volgen.md)
    "Das Boot 1 [Ek2omNPSOYc] 28m10s-28m55s.mp4": 1125,
    "Das Boot 2a [10EqNLl5ZSM] 13m15s-13m41s.mp4": 647,
    "Das Boot 2b [10EqNLl5ZSM] 13m41s-14m15s.mp4": 853,
    "Das Boot 3 [kefBHWylmMk] 30m08s-31m04s.mp4": 1400,
    "Das Boot 4a [kefBHWylmMk] 45m35s-46m04s.mp4": 714,
    "Das Boot 4b [kefBHWylmMk] 46m04s-46m35s.mp4": 786,
    "Das Boot 5 [kefBHWylmMk] 32m05s-33m06s.mp4": 1525,
    "Das Boot 6 [ofY2rexjmc4] 3m51s-3m58s.mp4": 168,
    "Das Boot 7 [T-D6e3pjHKQ] 0m25s-1m00s.mp4": 839,
    "Das Boot 8a [dasgespenst] 0m00s-0m44s.mp4": 1096,
    "Das Boot 8b [dasgespenst] 0m44s-1m32s.mp4": 1194,
    "Das Boot 8c [dasgespenst] 1m32s-2m05s.mp4": 835,
}
# de bestanden die vastgelegd worden: invoer (video's, model) en de uitkomsten waar labels en controle bij horen
PIXELS = REPO / "data" / "tracks" / "video_pixels.sha256"
FROZEN_PATTERNS = ["movies/*.mp4", "models/*.tflite", "data/tracks/*.csv", "data/audit/*.csv",
                   "data/stills_index.csv", "labeling/items.json", "labeling/automatic_labels.csv"]
FOLDERS = ["labeling/images/", "pictures/"]   # één controlegetal voor alle plaatjes in de map samen


def requirements():
    pins = {}
    for line in (REPO / "requirements.txt").read_text(encoding="utf-8").splitlines():
        match = re.match(r"^([A-Za-z0-9_.-]+)==([^\s#]+)", line.strip())
        if match:
            pins[match.group(1)] = match.group(2)
    return pins


def folder_digest(folder):
    """Eén controlegetal over de namen en de inhoud van de plaatjes in een map. Voor labeling/images/ de plaatjes
    die items.json noemt; voor pictures/ alle .jpg, .jpeg en .png (dus ook een foto die erbij gezet is)."""
    if folder == "labeling/images/":
        data = json.loads((REPO / "labeling" / "items.json").read_text(encoding="utf-8"))
        names = {item["image"] for item in data["items"]} | {name for person in data["references"] for name in person["images"]}
        paths = [REPO / "labeling" / name for name in names]
    else:
        paths = [p for p in (REPO / folder).rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")]
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.relative_to(REPO).as_posix()):  # op tekst: overal dezelfde volgorde
        digest.update(f"{path.relative_to(REPO).as_posix()} {sha256(path) if path.exists() else 'ontbreekt'}\n".encode("utf-8"))
    return digest.hexdigest()


def video_pixels(name):
    """(aantal frames, controlegetal van de pixels van alle frames), frames op volgorde gelezen."""
    import cv2
    capture, count, digest = cv2.VideoCapture(str(REPO / "movies" / name)), 0, hashlib.sha256()
    if not capture.isOpened():
        return 0, ""
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        digest.update(frame.tobytes())
        count += 1
    capture.release()
    return count, digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Controleer of deze computer klaar is voor de scripts")
    parser.add_argument("--vastleggen", action="store_true", help="schrijf checksums.sha256 met de huidige bestanden")
    args = parser.parse_args()

    if args.vastleggen:
        PIXELS.write_text("".join(f"{video_pixels(name)[1]}  movies/{name}\n" for name in EXPECTED_FRAMES),
                          encoding="utf-8", newline="\n")   # ook op Windows dezelfde bytes
        paths = sorted({p for pattern in FROZEN_PATTERNS + ["data/tracks/video_pixels.sha256"] for p in REPO.glob(pattern)
                        if not p.name.endswith((".nieuw.csv", ".nieuw.json"))})
        lines = [f"{sha256(p)}  {p.relative_to(REPO).as_posix()}" for p in paths]
        lines += [f"{folder_digest(folder)}  {folder}" for folder in FOLDERS]
        CHECKSUMS.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        print(f"{len(lines)} bestanden en mappen vastgelegd in {CHECKSUMS.name}")
        return

    errors = []
    print(f"Python {sys.version.split()[0]}")
    if sys.version_info[:2] != (3, 12):
        errors.append("de scripts zijn gemaakt met Python 3.12; een andere versie kan andere uitkomsten geven")
    for package, wanted in requirements().items():
        try:
            found = metadata.version(package)
        except metadata.PackageNotFoundError:
            errors.append(f"pakket {package} ontbreekt (pip install -r requirements.txt)")
            continue
        print(f"{package} {found}")
        if found != wanted:
            errors.append(f"{package} is versie {found}, verwacht {wanted}")

    known = frozen()
    if not known:
        errors.append("checksums.sha256 ontbreekt")
    for relative, digest in known.items():
        path = REPO / relative
        if relative.endswith("/"):   # een hele map met plaatjes
            try:
                same = folder_digest(relative) == digest
            except (OSError, ValueError, KeyError):   # bijvoorbeeld als labeling/items.json ontbreekt of kapot is
                same = False
            if not same:
                errors.append(f"de plaatjes in {relative} zijn anders dan bij het vastleggen (een plaatje ontbreekt, "
                              "is veranderd of is erbij gekomen)")
            continue
        if not path.exists():
            errors.append(f"{relative} ontbreekt")
        elif sha256(path) != digest:
            errors.append(f"{relative} is anders dan het vastgelegde bestand")
    print(f"{len(known)} vastgelegde bestanden en mappen gecontroleerd")

    pixels = {}
    if PIXELS.exists():
        pixels = {path.strip(): digest for digest, path in
                  (line.split(maxsplit=1) for line in PIXELS.read_text(encoding="utf-8").splitlines() if line.strip())}
    for name, expected in EXPECTED_FRAMES.items():
        count, digest = video_pixels(name)
        print(f"{name}: {count} frames")
        if count == 0:
            errors.append(f"OpenCV kan {name} niet openen of lezen")
        elif count != expected:
            errors.append(f"OpenCV leest {count} frames van {name}, verwacht {expected}")
        elif pixels and pixels.get(f"movies/{name}") != digest:
            errors.append(f"deze computer leest de pixels van {name} anders uit dan bij het vastleggen. Gebruik de "
                          "vastgelegde uitkomsten en draai code/track_faces.py hier niet opnieuw")

    copies = [p for p in REPO.rglob("*") if re.search(r" \d+(\.[^/]*)?$", p.name)
              and ".venv" not in p.parts and "experiments" not in p.parts]
    for p in copies[:20]:
        errors.append(f"kopie van een clouddienst: {p.relative_to(REPO)}")

    if errors:
        for error in errors:
            print("FOUT:", error)
        sys.exit(1)
    print("Alles in orde.")


if __name__ == "__main__":
    main()
