"""Hoeveel duidelijk zichtbare gezichten vindt de detector? Rekent dat uit op de steekproef in data/audit/.

De steekproef: 120 beelden, 40 per fragment, gelijk verdeeld over elk fragment
(data/audit/detector_steekproef_beelden.csv). In die beelden is met het oog bepaald welke gezichten er
staan (data/audit/detector_steekproef.csv): "duidelijk" (een gezicht dat je goed ziet), "moeilijk" (wel
een gezicht, maar erg donker, klein of wazig) en "duidelijk, zonder kader" (een duidelijk gezicht waar
bij geen enkele geteste instelling van de detector een kader omheen stond; daarvan is de plek niet
vastgelegd).

Een gezicht telt als gevonden als er in dat beeld een kader is dat minstens 30% overlapt met het
gezicht (dezelfde maat als bij het volgen). Het programma rekent dat uit voor de kaders vanaf 0,5, de
kaders vanaf 0,3, en de kaders vanaf 0,3 samen met de verlengingen (kaders van 0,2 tot 0,3 die een track
verlengen), en apart voor grote gezichten (minstens 6% van de breedte van het beeld) en kleine.

Gebruik (vanuit de map KTAI):
    .venv/bin/python code/detector_steekproef.py
"""

from pathlib import Path

import cv2
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
SAMPLE = REPO / "data" / "audit" / "detector_steekproef.csv"
DETECTIONS = REPO / "data" / "tracks" / "detections_0.3.csv"
BIG = 0.06   # een groot gezicht is minstens zo breed als 6% van het beeld


def overlap(a, b) -> float:
    """Intersection over union van twee kaders (x, y, breedte, hoogte)."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    iw = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    ih = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = iw * ih
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def main() -> None:
    sample = pd.read_csv(SAMPLE)
    detections = pd.read_csv(DETECTIONS)
    width = {video: cv2.VideoCapture(str(REPO / "movies" / video)).get(cv2.CAP_PROP_FRAME_WIDTH)
             for video in sample["video"].unique()}
    clear = sample[sample["gezicht"].str.startswith("duidelijk")].copy()
    located = clear["gezicht"] == "duidelijk"
    clear["groot"] = located & (clear["w"] / clear["video"].map(width) >= BIG)
    variants = {
        "kaders vanaf 0,5": detections[(detections["score"] >= 0.5) & ~detections["verlengd"]],
        "kaders vanaf 0,3": detections[~detections["verlengd"]],
        "kaders vanaf 0,3 plus verlengingen": detections,
    }
    print(f"{len(clear)} duidelijke gezichten in {sample.groupby(['video', 'frame']).ngroups} beelden met gezichten "
          f"({int((~located).sum())} zonder plek, want nooit een kader), waarvan {int(clear['groot'].sum())} groot")
    for name, boxes in variants.items():
        by_frame = {key: group for key, group in boxes.groupby(["video", "frame"])}

        def found(row) -> bool:
            if row.gezicht != "duidelijk":
                return False
            group = by_frame.get((row.video, row.frame))
            return group is not None and any(
                overlap((row.x, row.y, row.w, row.h), (b.x, b.y, b.w, b.h)) >= 0.3 for b in group.itertuples())

        hit = pd.Series([found(row) for row in clear.itertuples()], index=clear.index)
        big, small = clear["groot"], located & ~clear["groot"]
        print(f"  {name}: {int(hit.sum())} van {len(clear)} ({hit.mean():.0%}); groot {int(hit[big].sum())} van "
              f"{int(big.sum())} ({hit[big].mean():.0%}); klein {int(hit[small].sum())} van {int(small.sum())}")


if __name__ == "__main__":
    main()
