r"""Extra: helpt het nog om slechte voorbeeldfoto's weg te laten? Stap voor stap wordt de foto weggelaten die de score het meest verbetert.

Dit is te gunstig gemeten, want de foto's worden gekozen op dezelfde beelden als waarop gemeten wordt. De winst is toch maar klein, en daarom laat Periskop geen foto's weg.
Uitvoer: resultaten/foto_weglaten.csv.

Gebruik (vanuit de map experimenten, na stap 2):
    Mac:     .venv/bin/python top_model/extra_foto_weglaten.py
    Windows: .venv\Scripts\python top_model\extra_foto_weglaten.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.herkennen import assigned, person_distances
from gedeeld.voorbeelden import rows
from instellingen import EXAMPLE_SET, OUT, THRESHOLDS, winner
from model import Data, f1, sweep, view_paths


def main() -> None:
    best = winner()
    data = Data(EXAMPLE_SET)
    table = rows(EXAMPLE_SET)
    views = [tuple(v) for v in best["blikken"]]
    boxes = {v: np.load(view_paths(EXAMPLE_SET, v)[0]) for v in views}
    refs = {v: np.load(view_paths(EXAMPLE_SET, v)[1]) for v in views}

    def score(active: list) -> float:
        matrix = np.mean([person_distances(boxes[v], data.names[active], refs[v][active], "euclidean_l2", "gemiddelde") for v in views], axis=0)
        matrix = data.best_part(matrix, best["deel_van_de_track"])
        person, distance = assigned(matrix, data.frame_id, "uniek")
        ordered = np.sort(matrix, axis=1)
        keep = (ordered[:, 1] - ordered[:, 0] >= best["verschil_met_tweede"]) & (data.score >= best["zekerheid_detector"])
        person, distance = np.where(keep, person, -1), np.where(keep, distance, np.inf)
        person, distance, hit, part = data.with_filled(person, distance) if best["gaten_vullen"] else (person, distance, data.hit, data.box_part)
        thresholds = np.quantile(distance[np.isfinite(distance)], np.linspace(0.005, 1, THRESHOLDS)) * 1.0001
        good, wrong = sweep(data, person, distance, hit, part, thresholds)
        return float(f1(good.sum(0), wrong.sum(0), data.faces.sum()).max())

    active = list(range(len(table)))
    current = score(active)
    steps = [{"stap": 0, "weggelaten": "niets", "voorbeelden_over": len(active), "score": round(current, 4)}]
    while True:
        tries = [(score([j for j in active if j != i]), i) for i in active if len({data.names[j] for j in active if j != i}) == 4]
        value, drop = max(tries)
        if value <= current or len(steps) > 8:
            break
        active.remove(drop)
        current = value
        steps.append({"stap": len(steps), "weggelaten": f"{data.names[drop]}: {table['bestand'][drop].split('/')[-1]}", "voorbeelden_over": len(active), "score": round(current, 4)})
    pd.DataFrame(steps).to_csv(OUT / "foto_weglaten.csv", index=False, lineterminator="\n")
    print(pd.DataFrame(steps).to_string(index=False))


if __name__ == "__main__":
    main()
