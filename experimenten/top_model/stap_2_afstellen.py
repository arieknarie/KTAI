r"""Stap 2: afstellen. Alle combinaties van de bouwstenen van Periskop worden geprobeerd; de beste volgens de score per gezicht wint.

Uitvoer in resultaten/:
    alle_instellingen.csv        elke combinatie met de beste drempel en de score
    beste_instelling.json        de winnende combinatie
    eerlijke_schatting.csv       de score als de combinatie en de drempel gekozen worden op de andere filmpjes
    wat_elke_stap_toevoegt.csv/.png  hoe de score stijgt bij elke bouwsteen, vanaf het getunde model
    per_filmpje.csv/.png         de score per filmpje, naast het getunde model
    andere_sets.csv              hoe goed Periskop is met alleen de foto's of alleen de stills

Gebruik (vanuit de map experimenten, na stap 1):
    Mac:     .venv/bin/python top_model/stap_2_afstellen.py
    Windows: .venv\Scripts\python top_model\stap_2_afstellen.py
"""

import itertools
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.meten import grouped_bars, rates
from instellingen import BEST_PART, EXAMPLE_SET, GAPS, MARGINS, MIRROR, ONE, OTHER_SETS, OUT, SCORES, THRESHOLDS, TWO_CROPS, TWO_MODELS, VIEWS
from model import Data, f1, sweep


def evaluate(data: Data, settings: dict) -> dict:
    """De score per drempel en per filmpje voor één combinatie."""
    _, person, distance = data.decide(settings)
    person, distance, hit, box_part = data.with_filled(person, distance) if settings["gaten_vullen"] else (person, distance, data.hit, data.box_part)
    finite = distance[np.isfinite(distance)]
    thresholds = np.quantile(finite, np.linspace(0.005, 1, THRESHOLDS)) * 1.0001
    good, wrong = sweep(data, person, distance, hit, box_part, thresholds)
    score = f1(good.sum(0), wrong.sum(0), data.faces.sum())
    k = int(score.argmax())
    return {"settings": settings, "thresholds": thresholds, "good": good, "wrong": wrong, "best": k, "f1": float(score[k])}


def search(data: Data) -> list:
    results = []
    for (name, views), part, margin, minimum, gaps in itertools.product(VIEWS.items(), BEST_PART, MARGINS, SCORES, GAPS):
        results.append(evaluate(data, {"naam_blikken": name, "blikken": views, "deel_van_de_track": part, "verschil_met_tweede": margin, "zekerheid_detector": minimum, "gaten_vullen": gaps}))
        results[-1]["naam"] = name
    return results


def honest(data: Data, results: list) -> tuple:
    """Voor elk filmpje de beste combinatie en drempel op de andere zeven filmpjes, gemeten op dat ene filmpje."""
    rows, parts = [], len(data.groups)
    for part, group in enumerate(data.groups):
        others = [i for i in range(parts) if i != part]
        chosen = max(results, key=lambda r: f1(r["good"][others].sum(0), r["wrong"][others].sum(0), data.faces[others].sum()).max())
        t = int(f1(chosen["good"][others].sum(0), chosen["wrong"][others].sum(0), data.faces[others].sum()).argmax())
        g, w = int(chosen["good"][part, t]), int(chosen["wrong"][part, t])
        s = chosen["settings"]
        rows.append({"filmpje": group, "blikken": s["naam_blikken"], "deel_van_de_track": s["deel_van_de_track"], "verschil_met_tweede": s["verschil_met_tweede"],
                     "zekerheid_detector": s["zekerheid_detector"], "gaten_vullen": s["gaten_vullen"], "drempel": round(float(chosen["thresholds"][t]), 4),
                     "gezichten": int(data.faces[part]), "goed": g, "fout_benoemd": w, "gemist": int(data.faces[part]) - g, **dict(zip(("precisie", "recall", "f1"), rates(g, w, int(data.faces[part]) - g)))})
    table = pd.DataFrame(rows)
    g, w = int(table["goed"].sum()), int(table["fout_benoemd"].sum())
    return table, rates(g, w, int(data.faces.sum()) - g)[2]


def steps_figure(rows: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.6, 0.62 * len(rows) + 1.1), facecolor="white")
    y = np.arange(len(rows))
    ax.barh(y, rows["score"], height=0.62, color=["#8a8983"] + ["#eb6834"] * (len(rows) - 1))
    for i, value in enumerate(rows["score"]):
        ax.text(value + 0.003, i, f"{value:.3f}".replace(".", ","), va="center", fontsize=10.5, color="#0b0b0b")
    ax.set_yticks(y, rows["stap"], fontsize=10.5, color="#0b0b0b")
    ax.invert_yaxis()
    ax.set_xlim(0.8, 0.96)
    ax.set_xlabel("score per gezicht (let op: de as begint bij 0,8)", fontsize=9.5, color="#52514e")
    ax.tick_params(length=0, labelsize=9, colors="#52514e")
    ax.tick_params(axis="y", colors="#0b0b0b")
    ax.grid(axis="x", color="#e4e3de", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title("Wat elke bouwsteen toevoegt", loc="left", fontsize=12, fontweight="bold", color="#0b0b0b")
    fig.tight_layout()
    fig.savefig(OUT / "wat_elke_stap_toevoegt.png", dpi=130)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = Data(EXAMPLE_SET)
    results = search(data)
    table = []
    for r in results:
        k, s = r["best"], r["settings"]
        g, w = int(r["good"].sum(0)[k]), int(r["wrong"].sum(0)[k])
        table.append({"blikken": s["naam_blikken"], "deel_van_de_track": s["deel_van_de_track"], "verschil_met_tweede": s["verschil_met_tweede"], "zekerheid_detector": s["zekerheid_detector"],
                      "gaten_vullen": s["gaten_vullen"], "drempel": round(float(r["thresholds"][k]), 4), "goed": g, "fout_benoemd": w, "gemist": int(data.faces.sum()) - g,
                      **dict(zip(("precisie", "recall", "f1"), rates(g, w, int(data.faces.sum()) - g))), "f1_precies": r["f1"]})
    overview = pd.DataFrame(table).sort_values("f1_precies", ascending=False, kind="stable")
    overview.drop(columns="f1_precies").to_csv(OUT / "alle_instellingen.csv", index=False, lineterminator="\n")

    top = max(results, key=lambda r: r["f1"])
    k = top["best"]
    fair, fair_score = honest(data, results)
    fair.to_csv(OUT / "eerlijke_schatting.csv", index=False, lineterminator="\n")
    best = {**top["settings"], "drempel": float(top["thresholds"][k]), "f1": round(top["f1"], 3), "f1_eerlijke_schatting": fair_score}
    (OUT / "beste_instelling.json").write_text(json.dumps(best, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    # hoe de score stijgt, vanaf het getunde model
    settings = {"naam_blikken": "het getunde model", "blikken": ONE, "deel_van_de_track": 1.0, "verschil_met_tweede": 0.0, "zekerheid_detector": 0.0, "gaten_vullen": False}
    steps = [("Het getunde model", {})]
    if best["deel_van_de_track"] < 1:
        steps.append((f"+ alleen de beste {best['deel_van_de_track']:.0%} van de beelden van een track", {"deel_van_de_track": best["deel_van_de_track"]}))
    if best["blikken"] != ONE:
        steps.append(("+ twee modellen samen", {"blikken": TWO_MODELS}))
    if best["blikken"] in (TWO_CROPS, MIRROR):
        steps.append(("+ twee uitsneden van elk gezicht", {"blikken": TWO_CROPS}))
    if best["blikken"] == MIRROR:
        steps.append(("+ ook het spiegelbeeld", {"blikken": MIRROR}))
    if best["verschil_met_tweede"] > 0:
        steps.append(("+ duidelijk verschil met de tweede persoon", {"verschil_met_tweede": best["verschil_met_tweede"]}))
    if best["zekerheid_detector"] > 0:
        steps.append(("+ alleen tracks waar de detector zeker van is", {"zekerheid_detector": best["zekerheid_detector"]}))
    if best["gaten_vullen"]:
        steps.append(("+ gaten in een track vullen", {"gaten_vullen": True}))
    rows = []
    for name, change in steps:
        settings = {**settings, **change}
        rows.append({"stap": name, "score": round(evaluate(data, settings)["f1"], 3)})
    rows = pd.DataFrame(rows)
    rows.to_csv(OUT / "wat_elke_stap_toevoegt.csv", index=False, lineterminator="\n")
    steps_figure(rows)

    # per filmpje, naast het getunde model
    base = evaluate(data, {"naam_blikken": "het getunde model", "blikken": ONE, "deel_van_de_track": 1.0, "verschil_met_tweede": 0.0, "zekerheid_detector": 0.0, "gaten_vullen": False})
    per = []
    for part, group in enumerate(data.groups):
        for name, r in (("getuned", base), ("periskop", top)):
            g, w = int(r["good"][part, r["best"]]), int(r["wrong"][part, r["best"]])
            per.append({"filmpje": group, "model": name, "f1": rates(g, w, int(data.faces[part]) - g)[2]})
    per = pd.DataFrame(per).pivot(index="filmpje", columns="model", values="f1").reindex(data.groups).reset_index()
    per.to_csv(OUT / "per_filmpje.csv", index=False, lineterminator="\n")
    grouped_bars(per["filmpje"].tolist(), per["getuned"].tolist(), per["periskop"].tolist(), ("het getunde model", "Periskop"), "De score per filmpje", OUT / "per_filmpje.png")

    # hoe goed Periskop is met de andere sets voorbeelden
    other = []
    for example_set in OTHER_SETS:
        d = Data(example_set)
        res = search(d)
        t = max(res, key=lambda r: r["f1"])
        other.append({"voorbeelden": example_set, "f1": round(t["f1"], 3), "f1_eerlijke_schatting": honest(d, res)[1], "blikken": t["naam"], "deel_van_de_track": t["settings"]["deel_van_de_track"]})
    pd.DataFrame(other).to_csv(OUT / "andere_sets.csv", index=False, lineterminator="\n")
    print(json.dumps(best, ensure_ascii=False))
    print(overview.groupby("blikken")["f1"].max().to_string())
    print(overview.groupby("zekerheid_detector")["f1"].max().to_string())
    print(rows.to_string(index=False))
    print(fair[["filmpje", "blikken", "deel_van_de_track", "drempel", "f1"]].to_string(index=False))
    print(per.to_string(index=False))
    print(pd.DataFrame(other).to_string(index=False))


if __name__ == "__main__":
    main()
