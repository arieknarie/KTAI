r"""Alleen de in-karakter foto's: de tijdlijnen en de ablation zonder de out-of-character foto's.

Dit experiment draait de stappen van de basis met alleen de stills in kostuum als voorbeelden, en zet daarna de drie sets naast
elkaar: alleen foto's (out-of-character), alleen stills (in-character) en allebei. Gemeten wordt per gezicht (methode 2).
Uitvoer in resultaten/: alles van de basis voor deze set (met de tijdlijn), en vergelijking.csv.

Met --model tuned draaien de stappen van tuned voor deze set, en staat de uitvoer in resultaten_tuned/. In vergelijking.csv staat dan ook de score
met precies de instellingen van de set met foto's + stills: dan verandert alleen de lijst met voorbeelden.

Gebruik (vanuit de map experimenten, na basis/draai_alles.py; voor --model tuned na tuned/draai_alles.py):
    Mac:     .venv/bin/python alleen_in_karakter/draai.py
             .venv/bin/python alleen_in_karakter/draai.py --model tuned
    Windows: .venv\Scripts\python alleen_in_karakter\draai.py
             .venv\Scripts\python alleen_in_karakter\draai.py --model tuned
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd

EXPERIMENTEN = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(EXPERIMENTEN))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.facenet import load_detections
from gedeeld.getuned import OUTPUT, Tuned, model_choice, results_of
from gedeeld.meten import bars, fast_counts, fast_setup, rates
from gedeeld.voorbeelden import rows as example_rows

SETS = (("alleen foto's (out-of-character)", "fotos"), ("alleen stills (in-character)", "alleen_kostuum"), ("foto's + stills (totale set)", "fotos_en_kostuum"))
LABELS = ["alleen foto's\n(out-of-character)", "alleen stills\n(in-character)", "foto's + stills\n(totale set)"]


def main() -> None:
    model = model_choice()
    out = HERE / OUTPUT[model]
    if not (out / "filmpje.mp4").exists():
        subprocess.run([sys.executable, str(EXPERIMENTEN / ("tuned" if model == "tuned" else "basis") / "draai_alles.py"), "--voorbeelden", "alleen_kostuum"], check=True)
    if model == "tuned":
        detections = load_detections()
        setup = fast_setup(detections)
        faces = int(setup["faces_per_person"].sum())
    table = []
    for name, example_set in SETS:
        two = pd.read_csv(results_of(model, example_set) / "methode_2_tabel.csv").set_index("acteur").loc["samen"]
        row = {"voorbeelden": name, "voorbeelden_aantal": len(example_rows(example_set)), "methode_2_precisie": two["precisie"], "methode_2_recall": two["recall"], "methode_2_f1": two["f1"]}
        if model == "tuned":
            fixed = Tuned(example_set, detections, settings_of="fotos_en_kostuum")      # alleen de lijst met voorbeelden verandert
            person, distance = fixed.decide(fixed.person_matrix())[1:]
            row["methode_2_f1_instellingen_fotos_en_stills"] = rates(*fast_counts(person, distance, setup["hit"], faces, fixed.threshold))[2]
        table.append(row)
    table = pd.DataFrame(table)
    table.to_csv(out / "vergelijking.csv", index=False, lineterminator="\n")
    bars(LABELS, table["methode_2_f1"].tolist(), ("Getuned: w" if model == "tuned" else "W") + "at de out-of-character foto's toevoegen", out / "vergelijking.png")
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
