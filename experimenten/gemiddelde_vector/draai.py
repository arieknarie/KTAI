r"""Eén gemiddelde vector per persoon: alle voorbeelden van een persoon samengevoegd tot één vector.

Verder is alles hetzelfde als bij de basis: hetzelfde model, dezelfde drempel en dezelfde meting. De vector van een persoon is het
gemiddelde van de genormaliseerde vectoren van zijn voorbeelden, daarna weer op lengte 1 gebracht.
Uitvoer in resultaten/<set>/: voorspellingen.csv en de uitkomsten van beide meetmethodes; in resultaten/ vergelijking.csv.

Gebruik (vanuit de map experimenten, na basis/draai_alles.py en alleen_in_karakter/draai.py):
    Mac:     .venv/bin/python gemiddelde_vector/draai.py
    Windows: .venv\Scripts\python gemiddelde_vector\draai.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.facenet import box_vectors, load_detections
from gedeeld.herkennen import example_distances, person_distances, predictions
from gedeeld.meten import grouped_bars, method_1, method_2
from gedeeld.paden import EXAMPLE_SETS, EXPERIMENTEN, NAMES

HERE = Path(__file__).resolve().parent
DREMPEL = 0.80
SOURCES = {"fotos": EXPERIMENTEN / "basis" / "resultaten" / "fotos",
           "fotos_en_kostuum": EXPERIMENTEN / "basis" / "resultaten" / "fotos_en_kostuum",
           "alleen_kostuum": EXPERIMENTEN / "alleen_in_karakter" / "resultaten"}


def main() -> None:
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
        one, two = method_1(found, out, title).set_index("acteur").loc["samen"], method_2(found, out, title).set_index("acteur").loc["samen"]
        base_one = pd.read_csv(source / "methode_1_tabel.csv").set_index("acteur").loc["samen"]
        base_two = pd.read_csv(source / "methode_2_tabel.csv").set_index("acteur").loc["samen"]
        rows.append({"voorbeelden": EXAMPLE_SETS[example_set].removeprefix("voorbeelden: "),
                     "methode_1_f1_alle_vectoren": base_one["f1"], "methode_1_f1_gemiddelde": one["f1"],
                     "methode_2_f1_alle_vectoren": base_two["f1"], "methode_2_f1_gemiddelde": two["f1"],
                     "methode_2_precisie_gemiddelde": two["precisie"], "methode_2_recall_gemiddelde": two["recall"]})
    table = pd.DataFrame(rows)
    table.to_csv(HERE / "resultaten" / "vergelijking.csv", index=False, lineterminator="\n")
    grouped_bars(table["voorbeelden"].tolist(), table["methode_2_f1_alle_vectoren"].tolist(), table["methode_2_f1_gemiddelde"].tolist(),
                 ("alle voorbeelden los (de basis)", "één gemiddelde vector per persoon"), "F1 per gezicht (methode 2), bij dezelfde drempel van 0,80", HERE / "resultaten" / "vergelijking.png")
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
