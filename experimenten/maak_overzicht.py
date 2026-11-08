r"""Het overzicht van alle experimenten: de F1 van elk experiment met beide meetmethodes naast elkaar.

Uitvoer: overzicht.csv en overzicht.png in deze map.

Gebruik (vanuit de map experimenten, als de experimenten gedraaid hebben):
    Mac:     .venv/bin/python maak_overzicht.py
    Windows: .venv\Scripts\python maak_overzicht.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
EXPERIMENTS = [("Basis, foto's", "basis/resultaten/fotos"),
               ("Basis, foto's + stills", "basis/resultaten/fotos_en_kostuum"),
               ("Alleen in-karakter stills", "alleen_in_karakter/resultaten"),
               ("Eén gemiddelde vector, foto's + stills", "gemiddelde_vector/resultaten/fotos_en_kostuum"),
               ("Tuned, foto's", "tuned/resultaten/fotos"),
               ("Tuned, foto's + stills", "tuned/resultaten/fotos_en_kostuum")]


def main() -> None:
    rows = []
    for name, folder in EXPERIMENTS:
        one = pd.read_csv(HERE / folder / "methode_1_tabel.csv").set_index("acteur").loc["samen"]
        two = pd.read_csv(HERE / folder / "methode_2_tabel.csv").set_index("acteur").loc["samen"]
        rows.append({"experiment": name, "methode_1_precisie": one["precisie"], "methode_1_recall": one["recall"], "methode_1_f1": one["f1"],
                     "methode_2_precisie": two["precisie"], "methode_2_recall": two["recall"], "methode_2_f1": two["f1"]})
    table = pd.DataFrame(rows)
    table.to_csv(HERE / "overzicht.csv", index=False, lineterminator="\n")

    y = np.arange(len(table))
    fig, ax = plt.subplots(figsize=(10, 4.4), facecolor="white")
    for shift, column, colour, label in ((-0.19, "methode_1_f1", "#2a78d6", "methode 1 (per beeld)"), (0.19, "methode_2_f1", "#eb6834", "methode 2 (per gezicht)")):
        ax.barh(y + shift, table[column], height=0.34, color=colour, label=label)
        for i, value in enumerate(table[column]):
            ax.text(value + 0.008, i + shift, f"{value:.3f}".replace(".", ","), va="center", fontsize=9, color="#0b0b0b")
    ax.set_yticks(y, table["experiment"], fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("F1 (0 is niets goed, 1 is alles goed)", fontsize=9.5, color="#52514e")
    ax.tick_params(length=0, labelsize=9, colors="#52514e")
    ax.tick_params(axis="y", colors="#0b0b0b")
    ax.grid(axis="x", color="#e4e3de", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    ax.set_title("Hoe goed is elk experiment?", loc="left", fontsize=12, fontweight="bold", color="#0b0b0b")
    fig.tight_layout()
    fig.savefig(HERE / "overzicht.png", dpi=140)
    plt.close(fig)
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
