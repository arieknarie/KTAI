r"""Leave-one-out: welke voorbeeldfoto's maken het resultaat slechter?

Per voorbeeldfoto wordt gekeken wat er met het resultaat gebeurt als die ene foto er niet in zit. Wordt de F1 hoger zonder de foto, dan maakt die
foto het resultaat slechter. FaceNet staat standaard (drempel 0,80), en de vectoren veranderen niet: alleen de lijst met voorbeelden verandert.

Daarna wordt stap voor stap steeds de foto weggelaten die de F1 het meest verbetert, tot weglaten niet meer helpt. Let op: dat zegt wat er bij deze
filmpjes had kunnen gebeuren; de foto's zijn op dezelfde beelden uitgekozen als waarop gemeten wordt.

Uitvoer in resultaten/<set>/: leave_one_out.csv, weglaten_stap_voor_stap.csv, leave_one_out.png en slechtste_fotos.jpg.

Gebruik (vanuit de map experimenten, na basis/draai_alles.py en alleen_in_karakter/draai.py):
    Mac:     .venv/bin/python leave_one_out/draai.py
    Windows: .venv\Scripts\python leave_one_out\draai.py
"""

import sys
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.facenet import box_vectors, cut, load_detections
from gedeeld.herkennen import example_distances
from gedeeld.meten import fast_counts, fast_method_1, fast_setup, rates
from gedeeld.paden import EXPERIMENTEN, NAMES, PICTURES

HERE = Path(__file__).resolve().parent
DREMPEL = 0.80
SETS = {"fotos": EXPERIMENTEN / "basis" / "resultaten" / "fotos",
        "fotos_en_kostuum": EXPERIMENTEN / "basis" / "resultaten" / "fotos_en_kostuum",
        "alleen_kostuum": EXPERIMENTEN / "alleen_in_karakter" / "resultaten"}


def score(distance, person_of, active, setup) -> tuple:
    part = distance[:, active]
    nearest = part.argmin(axis=1)
    person, best = person_of[np.array(active)][nearest], part[np.arange(len(part)), nearest]
    two = rates(*fast_counts(person, best, setup["hit"], int(setup["faces_per_person"].sum()), DREMPEL))[2]
    one = rates(*fast_method_1(person, best, setup["frame_id"], setup["truth_frames"], DREMPEL))[2]
    return two, one


def main() -> None:
    detections = load_detections()
    boxes = box_vectors(detections, [("Facenet", 0.0)])[("Facenet", 0.0)]
    setup = fast_setup(detections)
    for example_set, source in SETS.items():
        out = HERE / "resultaten" / example_set
        out.mkdir(parents=True, exist_ok=True)
        examples = pd.read_csv(source / "voorbeelden.csv")
        names = examples["persoon"].to_numpy()
        refs = examples[[f"v{i}" for i in range(128)]].to_numpy(dtype=np.float32)
        person_of = np.array([NAMES.index(n) for n in names])
        distance = example_distances(boxes, refs, "euclidean_l2")
        everything = list(range(len(names)))
        base_two, base_one = score(distance, person_of, everything, setup)

        rows = []
        for i in everything:
            two, one = score(distance, person_of, [j for j in everything if j != i], setup)
            rows.append({"persoon": names[i], "bestand": examples["bestand"][i], "x": int(examples["x"][i]), "y": int(examples["y"][i]), "w": int(examples["w"][i]), "h": int(examples["h"][i]),
                         "methode_2_f1_met": base_two, "methode_2_f1_zonder": two, "methode_2_verschil": round(two - base_two, 4),
                         "methode_1_f1_met": base_one, "methode_1_f1_zonder": one, "methode_1_verschil": round(one - base_one, 4)})
        table = pd.DataFrame(rows).sort_values("methode_2_verschil", ascending=False, kind="stable").reset_index(drop=True)
        table.to_csv(out / "leave_one_out.csv", index=False, lineterminator="\n")

        active, path = everything.copy(), [{"stap": 0, "weggelaten": "niets", "voorbeelden_over": len(everything), "methode_2_f1": base_two, "methode_1_f1": base_one}]
        current = base_two
        while len(active) > 4:
            tries = []
            for i in active:
                left = [j for j in active if j != i]
                if len({names[j] for j in left}) == 4:      # elke persoon houdt minstens één voorbeeld
                    tries.append((score(distance, person_of, left, setup)[0], i))
            best_score, drop = max(tries)
            if best_score <= current:
                break
            active.remove(drop)
            current = best_score
            path.append({"stap": len(path), "weggelaten": f"{names[drop]}: {examples['bestand'][drop].split('/')[-1]}", "voorbeelden_over": len(active),
                         "methode_2_f1": best_score, "methode_1_f1": score(distance, person_of, active, setup)[1]})
        pd.DataFrame(path).to_csv(out / "weglaten_stap_voor_stap.csv", index=False, lineterminator="\n")

        changed = table[table["methode_2_verschil"] != 0]
        print(example_set, "F1 met alles:", base_two); print(table.head(6)[["persoon", "bestand", "methode_2_verschil", "methode_1_verschil"]].to_string(index=False)); print(pd.DataFrame(path).tail(4).to_string(index=False))
        if changed.empty:                                   # dan heeft geen enkele foto invloed en valt er niets te tekenen
            continue
        fig, ax = plt.subplots(figsize=(9.4, 0.3 * len(changed) + 1.5), facecolor="white")
        y = np.arange(len(changed))
        values = changed["methode_2_verschil"].to_numpy()
        ax.barh(y, values, height=0.65, color=np.where(values > 0, "#d1495b", "#2a78d6"))
        ax.set_yticks(y, [f"{p}: {b.removeprefix('pictures/')}" for p, b in zip(changed["persoon"], changed["bestand"])], fontsize=7.5)
        ax.invert_yaxis()
        ax.axvline(0, color="#52514e", linewidth=1)
        ax.set_xlabel("verandering van de F1 (methode 2) als deze foto wordt weggelaten; rood is beter zonder de foto", fontsize=9, color="#52514e")
        ax.tick_params(length=0, labelsize=8, colors="#52514e")
        ax.tick_params(axis="y", colors="#0b0b0b")
        ax.grid(axis="x", color="#e4e3de", linewidth=0.8)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_title(f"Leave-one-out, de {len(changed)} van de {len(table)} voorbeelden met effect (F1 met alles: {base_two:.3f})".replace(".", ","), loc="left", fontsize=10.5, fontweight="bold", color="#0b0b0b")
        fig.tight_layout()
        fig.savefig(out / "leave_one_out.png", dpi=130)
        plt.close(fig)

        tiles = []
        for r in table[table["methode_2_verschil"] > 0].head(7).itertuples():
            face = cut(cv2.imread(str(PICTURES / r.bestand)), r.x, r.y, r.w, r.h)
            face = cv2.resize(face, (150, 150), interpolation=cv2.INTER_AREA)
            bar = np.full((44, 150, 3), 255, np.uint8)
            cv2.putText(bar, r.persoon, (3, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(bar, f"F1 {r.methode_2_verschil:+.4f}", (3, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
            tiles.append(np.vstack([bar, face]))
        if tiles:
            cv2.imwrite(str(out / "slechtste_fotos.jpg"), np.hstack(tiles), [cv2.IMWRITE_JPEG_QUALITY, 88])


if __name__ == "__main__":
    main()
