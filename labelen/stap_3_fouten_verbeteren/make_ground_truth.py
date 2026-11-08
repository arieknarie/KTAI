r"""Het eindresultaat van het labelen: de ground truth, uit de uitkomsten van alle stappen samen.

Per item (een beeld, foto of still) telt wat er bij het nakijken gezien is:
- kreeg het item in stap 2 "goed": de kaders van de vier personen uit stap 1 (zoals stap 2 ze liet zien: één kader per
  persoon per beeld);
- kreeg het item in stap 2 "fout": de verbeterde kaders uit stap 3.

Uitvoer in output/stap_3_fouten_verbeteren/:
    ground_truth.csv                  per beeld van de filmpjes en per persoon in dat beeld één rij: fragment (Video 1
                                      tot en met 8), bestand, beeld (telt vanaf 0), tijd_s (seconden vanaf het begin
                                      van het fragment), persoon, het kader (x, y, w, h, in pixels van het originele
                                      beeld) en herkomst (stap_1 of stap_3)
    ground_truth_fotos_en_stills.csv  hetzelfde voor de gelabelde foto's en stills: item, persoon, x, y, w, h, herkomst
Een beeld zonder een van de vier personen heeft geen rij. Alle beelden staan in
output/stap_0_voorbereiding/tracks/frames.csv.

Gebruik (vanuit de map labelen):
    Mac:     .venv/bin/python stap_3_fouten_verbeteren/make_ground_truth.py
    Windows: .venv\Scripts\python stap_3_fouten_verbeteren\make_ground_truth.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.items import corrected, items, judged
from gedeeld.paden import FRAMES, GROUND_TRUTH, GROUND_TRUTH_PHOTOS


def fragments(frames: pd.DataFrame) -> dict:
    """Per bestand het fragment (Video 1 tot en met 8) en na hoeveel seconden van het fragment het bestand begint
    (fragment 2, 4 en 8 staan in delen)."""
    result, start = {}, {}
    for video, f in frames.groupby("video", sort=True):
        group = "Video " + video.split(" [")[0].split()[-1].rstrip("abc")
        result[video] = (group, start.get(group, 0.0))
        start[group] = start.get(group, 0.0) + len(f) * float(np.median(np.diff(f["time_s"])))
    return result


def main() -> None:
    verdicts, fixes = judged(), corrected()
    frames = pd.read_csv(FRAMES)
    parts, times = fragments(frames), frames.set_index(["video", "frame"])["time_s"]
    films, photos = [], []
    for item in items():
        verdict = verdicts.get(item["key"])
        if verdict is None or (verdict == "fout" and item["key"] not in fixes):
            raise SystemExit(f"{item['key']} is nog niet klaar: draai eerst stap 2 en stap 3 helemaal af.")
        boxes, origin = (fixes[item["key"]], "stap_3") if verdict == "fout" else (item["boxes"], "stap_1")
        for name, x, y, w, h in boxes:
            box = {"persoon": name, "x": int(x), "y": int(y), "w": int(w), "h": int(h), "herkomst": origin}
            if "video" in item:
                group, offset = parts[item["video"]]
                films.append({"fragment": group, "bestand": item["video"], "beeld": item["frame"],
                              "tijd_s": round(float(times[(item["video"], item["frame"])]) + offset, 3), **box})
            else:
                photos.append({"item": item["key"], **box})
    GROUND_TRUTH.parent.mkdir(parents=True, exist_ok=True)
    films = pd.DataFrame(films)
    films.to_csv(GROUND_TRUTH, index=False, lineterminator="\n")
    pd.DataFrame(photos).to_csv(GROUND_TRUTH_PHOTOS, index=False, lineterminator="\n")
    print(f"{len(films)} rijen in {GROUND_TRUTH.name}, {len(photos)} rijen in {GROUND_TRUTH_PHOTOS.name}")
    print(films["persoon"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()
