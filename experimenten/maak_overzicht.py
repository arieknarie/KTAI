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
               ("Alleen stills, standaard", "alleen_in_karakter/resultaten"),
               ("Eén gemiddelde vector, standaard", "gemiddelde_vector/resultaten/fotos_en_kostuum"),
               ("Tuned, foto's", "tuned/resultaten/fotos"),
               ("Tuned, foto's + stills", "tuned/resultaten/fotos_en_kostuum"),
               ("Alleen stills, tuned", "alleen_in_karakter/resultaten_tuned"),
               ("Eén gemiddelde vector, tuned", "gemiddelde_vector/resultaten_tuned/fotos_en_kostuum"),
               ("Top model: Periskop", "top_model/resultaten")]


def main() -> None:
    rows = []
    for name, folder in EXPERIMENTS:
        two = pd.read_csv(HERE / folder / "methode_2_tabel.csv").set_index("acteur").loc["samen"]
        row = {"experiment": name, "methode_2_precisie": two["precisie"], "methode_2_recall": two["recall"], "methode_2_f1": two["f1"]}
        if (HERE / folder / "methode_1_tabel.csv").exists():          # methode 1 staat alleen bij de basis
            one = pd.read_csv(HERE / folder / "methode_1_tabel.csv").set_index("acteur").loc["samen"]
            row |= {"methode_1_precisie": one["precisie"], "methode_1_recall": one["recall"], "methode_1_f1": one["f1"]}
        rows.append(row)
    table = pd.DataFrame(rows)
    table.to_csv(HERE / "overzicht.csv", index=False, lineterminator="\n")

    fig, ax = plt.subplots(figsize=(10, 6.1), facecolor="white")
    for i, r in table.iterrows():
        both = pd.notna(r["methode_1_f1"])
        if both:
            ax.barh(i - 0.19, r["methode_1_f1"], height=0.34, color="#2a78d6", label="methode 1 (per beeld, alleen bij de basis)" if i == 0 else None)
            ax.text(r["methode_1_f1"] + 0.008, i - 0.19, f"{r['methode_1_f1']:.3f}".replace(".", ","), va="center", fontsize=9, color="#0b0b0b")
        y = i + 0.19 if both else i
        ax.barh(y, r["methode_2_f1"], height=0.34 if both else 0.5, color="#eb6834", label="methode 2 (per gezicht)" if i == 0 else None)
        ax.text(r["methode_2_f1"] + 0.008, y, f"{r['methode_2_f1']:.3f}".replace(".", ","), va="center", fontsize=9, color="#0b0b0b")
    ax.set_yticks(np.arange(len(table)), table["experiment"], fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("score (F1): 0 is niets goed, 1 is alles goed", fontsize=9.5, color="#52514e")
    ax.tick_params(length=0, labelsize=9, colors="#52514e")
    ax.tick_params(axis="y", colors="#0b0b0b")
    ax.grid(axis="x", color="#e4e3de", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(frameon=False, fontsize=9.5, ncol=2, loc="lower left", bbox_to_anchor=(-0.01, 1.0))
    ax.set_title("Hoe goed is elk experiment?", loc="left", fontsize=12, fontweight="bold", color="#0b0b0b", pad=30)
    fig.tight_layout()
    fig.savefig(HERE / "overzicht.png", dpi=140)
    plt.close(fig)
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
