r"""Alleen de in-karakter foto's: de tijdlijnen en de ablation zonder de out-of-character foto's.

Dit experiment draait de stappen van de basis met alleen de stills in kostuum als voorbeelden, en zet daarna de drie sets naast
elkaar: alleen foto's (out-of-character), alleen stills (in-character) en allebei.
Uitvoer in resultaten/: alles van de basis voor deze set (met de tijdlijn), en vergelijking.csv.

Gebruik (vanuit de map experimenten, na basis/draai_alles.py):
    Mac:     .venv/bin/python alleen_in_karakter/draai.py
    Windows: .venv\Scripts\python alleen_in_karakter\draai.py
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd

EXPERIMENTEN = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(EXPERIMENTEN))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.meten import grouped_bars


def main() -> None:
    if not (HERE / "resultaten" / "filmpje.mp4").exists():
        subprocess.run([sys.executable, str(EXPERIMENTEN / "basis" / "draai_alles.py"), "--voorbeelden", "alleen_kostuum"], check=True)
    rows = []
    for name, folder in (("alleen foto's (out-of-character)", EXPERIMENTEN / "basis" / "resultaten" / "fotos"),
                         ("alleen stills (in-character)", HERE / "resultaten"),
                         ("foto's + stills (totale set)", EXPERIMENTEN / "basis" / "resultaten" / "fotos_en_kostuum")):
        one = pd.read_csv(folder / "methode_1_tabel.csv").set_index("acteur").loc["samen"]
        two = pd.read_csv(folder / "methode_2_tabel.csv").set_index("acteur").loc["samen"]
        rows.append({"voorbeelden": name, "voorbeelden_aantal": len(pd.read_csv(folder / "voorbeelden.csv")),
                     "methode_1_precisie": one["precisie"], "methode_1_recall": one["recall"], "methode_1_f1": one["f1"],
                     "methode_2_precisie": two["precisie"], "methode_2_recall": two["recall"], "methode_2_f1": two["f1"]})
    table = pd.DataFrame(rows)
    table.to_csv(HERE / "resultaten" / "vergelijking.csv", index=False, lineterminator="\n")
    grouped_bars(["alleen foto's\n(out-of-character)", "alleen stills\n(in-character)", "foto's + stills\n(totale set)"], table["methode_1_f1"].tolist(), table["methode_2_f1"].tolist(),
                 ("methode 1 (per beeld)", "methode 2 (per gezicht)"), "Wat de out-of-character foto's toevoegen", HERE / "resultaten" / "vergelijking.png")
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
