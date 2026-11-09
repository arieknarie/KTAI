r"""Eén gemiddelde vector per persoon: alle voorbeelden van een persoon samengevoegd tot één vector.

Verder is alles hetzelfde als bij de basis: hetzelfde model, dezelfde drempel en dezelfde meting. De vector van een persoon is het
gemiddelde van de genormaliseerde vectoren van zijn voorbeelden, daarna weer op lengte 1 gebracht.
Uitvoer in resultaten/<set>/: voorspellingen.csv en de uitkomsten van beide meetmethodes; in resultaten/ vergelijking.csv.

Met --model tuned staan alle andere instellingen op de beste instellingen voor die set, en krijgen "alle foto's los" en "één gemiddelde vector" elk hun
eigen beste drempel, op dezelfde manier als bij het afstellen. De uitvoer staat dan in resultaten_tuned/.

Gebruik (vanuit de map experimenten, na basis/draai_alles.py en alleen_in_karakter/draai.py; voor --model tuned na tuned/draai_alles.py
en alleen_in_karakter/draai.py --model tuned):
    Mac:     .venv/bin/python gemiddelde_vector/draai.py
             .venv/bin/python gemiddelde_vector/draai.py --model tuned
    Windows: .venv\Scripts\python gemiddelde_vector\draai.py
             .venv\Scripts\python gemiddelde_vector\draai.py --model tuned
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.facenet import box_vectors, load_detections
from gedeeld.getuned import Tuned, model_choice
from gedeeld.herkennen import example_distances, person_distances, predictions
from gedeeld.meten import fast_counts, fast_setup, grouped_bars, method_2, rates
from gedeeld.paden import EXAMPLE_SETS, EXPERIMENTEN, NAMES

HERE = Path(__file__).resolve().parent
DREMPEL = 0.80
SOURCES = {"fotos": EXPERIMENTEN / "basis" / "resultaten" / "fotos",
           "fotos_en_kostuum": EXPERIMENTEN / "basis" / "resultaten" / "fotos_en_kostuum",
           "alleen_kostuum": EXPERIMENTEN / "alleen_in_karakter" / "resultaten"}


def best_threshold(person, distance, setup) -> float:
    """De drempel met de hoogste F1 volgens methode 2, op dezelfde manier als bij het afstellen."""
    finite = distance[np.isfinite(distance)]
    faces = int(setup["faces_per_person"].sum())
    thresholds = np.quantile(finite, np.linspace(0.005, 1, 200)) * 1.0001
    def exact(t):
        good, wrong, missed = fast_counts(person, distance, setup["hit"], faces, t)
        return 2 * good / max(1, 2 * good + wrong + missed)
    return float(max(thresholds, key=exact))


def tuned_run() -> None:
    detections = load_detections()
    setup = fast_setup(detections)
    faces = int(setup["faces_per_person"].sum())
    output = HERE / "resultaten_tuned"
    rows = []
    for example_set in SOURCES:
        out = output / example_set
        out.mkdir(parents=True, exist_ok=True)
        tuned = Tuned(example_set, detections)
        row = {"voorbeelden": EXAMPLE_SETS[example_set].removeprefix("voorbeelden: "), "keuze_van_het_getunde_model": tuned.settings["per_persoon"]}
        for how, name in (("dichtstbij", "alle_vectoren"), ("gemiddelde", "gemiddelde")):
            matrix, person, distance = tuned.decide(tuned.person_matrix(per_person=how))
            threshold = best_threshold(person, distance, setup)
            two = rates(*fast_counts(person, distance, setup["hit"], faces, threshold))
            row |= {f"drempel_{name}": round(threshold, 4), f"methode_2_f1_{name}": two[2], f"methode_2_precisie_{name}": two[0], f"methode_2_recall_{name}": two[1]}
            if how == "gemiddelde":
                found = tuned.found(matrix, person, distance, threshold)
                found.to_csv(out / "voorspellingen.csv", index=False, lineterminator="\n")
                title = f"getuned, één gemiddelde vector per persoon, {EXAMPLE_SETS[example_set]}"
                method_2(found, out, title)
        rows.append(row)
    table = pd.DataFrame(rows)
    table.to_csv(output / "vergelijking.csv", index=False, lineterminator="\n")
    grouped_bars(table["voorbeelden"].tolist(), table["methode_2_f1_alle_vectoren"].tolist(), table["methode_2_f1_gemiddelde"].tolist(),
                 ("alle voorbeelden los", "één gemiddelde vector per persoon"), "Getuned: score per gezicht, elk met de eigen beste drempel", output / "vergelijking.png")
    print(table.to_string(index=False))


def main() -> None:
    if model_choice() == "tuned":
        tuned_run()
        return
    detections = load_detections()
    boxes = box_vectors(detections, [("Facenet", 0.0)])[("Facenet", 0.0)]
    rows = []
    for example_set, source in SOURCES.items():
        out = HERE / "resultaten" / example_set
        out.mkdir(parents=True, exist_ok=True)
        examples = pd.read_csv(source / "voorbeelden.csv")
        names, photos = examples["persoon"].to_numpy(), examples["bestand"].to_numpy()
        refs = examples[[f"v{i}" for i in range(128)]].to_numpy(dtype=np.float32)
        d = person_distances(boxes, names, refs, "euclidean_l2", "gemiddelde")
        person = d.argmin(axis=1)
        each = example_distances(boxes, refs, "euclidean_l2")
        chosen = np.array(NAMES, dtype=object)[person]
        index = np.where(names[None, :] == chosen[:, None], each, np.inf).argmin(axis=1)
        found = predictions(detections, chosen, d[np.arange(len(d)), person], DREMPEL, photos[index])
        found.to_csv(out / "voorspellingen.csv", index=False, lineterminator="\n")
        title = f"één gemiddelde vector per persoon, {EXAMPLE_SETS[example_set]}"
        two = method_2(found, out, title).set_index("acteur").loc["samen"]
        base_two = pd.read_csv(source / "methode_2_tabel.csv").set_index("acteur").loc["samen"]
        rows.append({"voorbeelden": EXAMPLE_SETS[example_set].removeprefix("voorbeelden: "),
                     "methode_2_f1_alle_vectoren": base_two["f1"], "methode_2_f1_gemiddelde": two["f1"],
                     "methode_2_precisie_gemiddelde": two["precisie"], "methode_2_recall_gemiddelde": two["recall"]})
    table = pd.DataFrame(rows)
    table.to_csv(HERE / "resultaten" / "vergelijking.csv", index=False, lineterminator="\n")
    grouped_bars(table["voorbeelden"].tolist(), table["methode_2_f1_alle_vectoren"].tolist(), table["methode_2_f1_gemiddelde"].tolist(),
                 ("alle voorbeelden los (de basis)", "één gemiddelde vector per persoon"), "Score per gezicht, bij dezelfde drempel van 0,80", HERE / "resultaten" / "vergelijking.png")
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
