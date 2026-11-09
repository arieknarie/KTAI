r"""Leave-one-out: welke voorbeeldfoto's maken het resultaat slechter?

Per voorbeeldfoto wordt gekeken wat er met het resultaat gebeurt als die ene foto er niet in zit. Wordt de F1 hoger zonder de foto, dan maakt die
foto het resultaat slechter. FaceNet staat standaard (drempel 0,80), en de vectoren veranderen niet: alleen de lijst met voorbeelden verandert.

Daarna wordt stap voor stap steeds de foto weggelaten die de F1 het meest verbetert, tot weglaten niet meer helpt. Let op: dat zegt wat er bij deze
filmpjes had kunnen gebeuren; de foto's zijn op dezelfde beelden uitgekozen als waarop gemeten wordt.

Met --model tuned staat FaceNet op de beste instellingen voor die set, en blijft de drempel gelijk.

Uitvoer in resultaten/<set>/ (met --model tuned in resultaten_tuned/<set>/): leave_one_out.csv, weglaten_stap_voor_stap.csv, leave_one_out.png
en slechtste_fotos.jpg.

Gebruik (vanuit de map experimenten, na basis/draai_alles.py en alleen_in_karakter/draai.py; voor --model tuned na tuned/draai_alles.py
en alleen_in_karakter/draai.py --model tuned):
    Mac:     .venv/bin/python leave_one_out/draai.py
             .venv/bin/python leave_one_out/draai.py --model tuned
    Windows: .venv\Scripts\python leave_one_out\draai.py
             .venv\Scripts\python leave_one_out\draai.py --model tuned
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
from gedeeld.getuned import OUTPUT, Tuned, model_choice, results_of
from gedeeld.herkennen import example_distances
from gedeeld.meten import fast_counts, fast_setup, rates
from gedeeld.paden import NAMES, PICTURES

HERE = Path(__file__).resolve().parent
DREMPEL = 0.80
SETS = ["fotos", "fotos_en_kostuum", "alleen_kostuum"]


def score(decide, active, setup, threshold) -> float:
    person, best = decide(active)
    return rates(*fast_counts(person, best, setup["hit"], int(setup["faces_per_person"].sum()), threshold))[2]


def main() -> None:
    model = model_choice()
    detections = load_detections()
    setup = fast_setup(detections)
    boxes = None if model == "tuned" else box_vectors(detections, [("Facenet", 0.0)])[("Facenet", 0.0)]
    for example_set in SETS:
        out = HERE / OUTPUT[model] / example_set
        out.mkdir(parents=True, exist_ok=True)
        if model == "tuned":
            tuned = Tuned(example_set, detections)
            examples, names, threshold = tuned.table, tuned.names, tuned.threshold

            def decide(active: list, tuned=tuned) -> tuple:
                return tuned.decide(tuned.person_matrix(active))[1:]
        else:
            examples = pd.read_csv(results_of(model, example_set) / "voorbeelden.csv")
            names, threshold = examples["persoon"].to_numpy(), DREMPEL
            refs = examples[[f"v{i}" for i in range(128)]].to_numpy(dtype=np.float32)
            person_of = np.array([NAMES.index(n) for n in names])
            distance = example_distances(boxes, refs, "euclidean_l2")

            def decide(active: list, distance=distance, person_of=person_of) -> tuple:
                part = distance[:, active]
                nearest = part.argmin(axis=1)
                return person_of[np.array(active)][nearest], part[np.arange(len(part)), nearest]
        everything = list(range(len(names)))
        base_two = score(decide, everything, setup, threshold)

        rows = []
        for i in everything:
            two = score(decide, [j for j in everything if j != i], setup, threshold)
            rows.append({"persoon": names[i], "bestand": examples["bestand"][i], "x": int(examples["x"][i]), "y": int(examples["y"][i]), "w": int(examples["w"][i]), "h": int(examples["h"][i]),
                         "methode_2_f1_met": base_two, "methode_2_f1_zonder": two, "methode_2_verschil": round(two - base_two, 4)})
        table = pd.DataFrame(rows).sort_values("methode_2_verschil", ascending=False, kind="stable").reset_index(drop=True)
        table.to_csv(out / "leave_one_out.csv", index=False, lineterminator="\n")

        active, path = everything.copy(), [{"stap": 0, "weggelaten": "niets", "voorbeelden_over": len(everything), "methode_2_f1": base_two}]
        current = base_two
        while len(active) > 4:
            tries = []
            for i in active:
                left = [j for j in active if j != i]
                if len({names[j] for j in left}) == 4:      # elke persoon houdt minstens één voorbeeld
                    tries.append((score(decide, left, setup, threshold), i))
            best_score, drop = max(tries)
            if best_score <= current:
                break
            active.remove(drop)
            current = best_score
            path.append({"stap": len(path), "weggelaten": f"{names[drop]}: {examples['bestand'][drop].split('/')[-1]}", "voorbeelden_over": len(active),
                         "methode_2_f1": best_score})
        pd.DataFrame(path).to_csv(out / "weglaten_stap_voor_stap.csv", index=False, lineterminator="\n")

        changed = table[table["methode_2_verschil"] != 0]
        print(example_set, "F1 met alles:", base_two); print(table.head(6)[["persoon", "bestand", "methode_2_verschil"]].to_string(index=False)); print(pd.DataFrame(path).tail(4).to_string(index=False))
        if changed.empty:                                   # dan heeft geen enkele foto invloed en valt er niets te tekenen
            continue
        fig, ax = plt.subplots(figsize=(9.4, 0.3 * len(changed) + 1.5), facecolor="white")
        y = np.arange(len(changed))
        values = changed["methode_2_verschil"].to_numpy()
        ax.barh(y, values, height=0.65, color=np.where(values > 0, "#d1495b", "#8a8983"))
        ax.set_yticks(y, [f"{p}: {b.split('/')[-1]}" for p, b in zip(changed["persoon"], changed["bestand"])], fontsize=8.5)
        ax.invert_yaxis()
        ax.axvline(0, color="#52514e", linewidth=1)
        ax.set_xlabel("verandering van de score (F1 per gezicht) als deze foto wordt weggelaten", fontsize=9.5, color="#52514e")
        ax.tick_params(length=0, labelsize=8, colors="#52514e")
        ax.tick_params(axis="y", colors="#0b0b0b")
        ax.grid(axis="x", color="#e4e3de", linewidth=0.8)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_visible(False)
        fig.suptitle(f"Wat gebeurt er als je één foto weglaat? Rood: de score wordt hoger. Grijs: de score wordt lager.", x=0.012, ha="left", fontsize=11, fontweight="bold", color="#0b0b0b")
        fig.tight_layout(rect=(0, 0, 1, 1 - 0.3 / fig.get_figheight()))
        fig.savefig(out / "leave_one_out.png", dpi=130)
        plt.close(fig)

        tiles = []
        for r in table[table["methode_2_verschil"] > 0].head(7).itertuples():
            face = cut(cv2.imread(str(PICTURES / r.bestand)), r.x, r.y, r.w, r.h)
            face = cv2.resize(face, (150, 150), interpolation=cv2.INTER_AREA)
            bar = np.full((44, 150, 3), 255, np.uint8)
            cv2.putText(bar, r.persoon, (3, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(bar, f"score {r.methode_2_verschil:+.3f}".replace(".", ","), (3, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
            tiles.append(np.vstack([bar, face]))
        if tiles:
            cv2.imwrite(str(out / "slechtste_fotos.jpg"), np.hstack(tiles), [cv2.IMWRITE_JPEG_QUALITY, 88])


if __name__ == "__main__":
    main()
