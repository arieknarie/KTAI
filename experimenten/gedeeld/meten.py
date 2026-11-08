"""De twee meetmethodes. Elk experiment meet op precies dezelfde manier, met deze code.

Methode 1 (per beeld): we weten wie er in elk beeld te zien is, en tellen. Per beeld en per persoon: staat deze persoon
volgens FaceNet in dit beeld, en klopt dat? Waar FaceNet de persoon ziet, maakt niet uit.

Methode 2 (per gezicht): we weten ook waar elk gezicht staat, en matchen daarop. Een naam van FaceNet is alleen goed als
het kader dat die naam kreeg ook echt op het gezicht van die persoon ligt: minstens IOU overlap met het kader in de
ground truth. IOU (intersection over union) is de oppervlakte die twee kaders gemeen hebben, gedeeld door de oppervlakte
die ze samen bedekken.
- goed: een gezicht uit de ground truth waarop FaceNet de juiste naam zette
- fout benoemd: een kader met een naam dat niet op het gezicht van die persoon ligt (een figurant, geen gezicht, of een
  van de andere drie)
- gemist: een gezicht uit de ground truth zonder de juiste naam, verdeeld in: geen kader van de detector op die plek,
  wel een kader maar geen naam ("iemand anders"), of wel een kader maar een andere naam
Twee kaders op hetzelfde hoofd met de juiste naam tellen samen één keer goed, en niet als fout.
"""

from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from gedeeld.film import fragments
from gedeeld.paden import FRAMES, GROUND_TRUTH, NAMES, OTHER

IOU = 0.3      # de keuze voor methode 2: minstens 30% overlap (zie experimenten/basis/README.md)
COLUMNS = ["fragment", "bestand", "beeld", "tijd_s"]
NOBODY = "geen van de vier"


def rates(tp: int, fp: int, fn: int) -> tuple:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return round(precision, 3), round(recall, 3), round(f1, 3)


def comma(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def overlap(a, b) -> float:
    """IoU van twee kaders (x, y, w, h)."""
    w = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
    h = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    return w * h / (a[2] * a[3] + b[2] * b[3] - w * h) if w > 0 and h > 0 else 0.0


# ---------- methode 1: per beeld ----------

def presence(found: pd.DataFrame) -> pd.DataFrame:
    """Welke persoon volgens FaceNet in welk beeld te zien is (elke combinatie één keer)."""
    seen = found[found["facenet"].isin(NAMES)]
    return seen[COLUMNS + ["facenet"]].drop_duplicates(["bestand", "beeld", "facenet"]).rename(columns={"facenet": "persoon"})


def method_1_table(truth: pd.DataFrame, ai: pd.DataFrame) -> pd.DataFrame:
    rows, totals = [], [0, 0, 0, 0, 0]
    for person in NAMES:
        gt = set(map(tuple, truth.loc[truth["persoon"] == person, ["bestand", "beeld"]].to_numpy()))
        pred = set(map(tuple, ai.loc[ai["persoon"] == person, ["bestand", "beeld"]].to_numpy()))
        tp, fp, fn = len(gt & pred), len(pred - gt), len(gt - pred)
        rows.append({"acteur": person, "ground_truth": len(gt), "ai_voorspelling": len(pred),
                     "foutmarge_procent": round(100 * abs(len(pred) - len(gt)) / len(gt), 1) if gt else None,
                     "goed": tp, "fout": fp, "gemist": fn, **dict(zip(("precisie", "recall", "f1"), rates(tp, fp, fn)))})
        totals = [totals[0] + len(gt), totals[1] + len(pred), totals[2] + tp, totals[3] + fp, totals[4] + fn]
    rows.append({"acteur": "samen", "ground_truth": totals[0], "ai_voorspelling": totals[1],
                 "foutmarge_procent": round(100 * abs(totals[1] - totals[0]) / totals[0], 1),
                 "goed": totals[2], "fout": totals[3], "gemist": totals[4],
                 **dict(zip(("precisie", "recall", "f1"), rates(*totals[2:])))})
    return pd.DataFrame(rows)


def segments(times: np.ndarray, step: float) -> list:
    """Opeenvolgende beelden samen als één stuk (begin, lengte), voor de tijdlijn."""
    if len(times) == 0:
        return []
    times = np.sort(times)
    breaks = np.where(np.diff(times) > 1.5 * step)[0]
    starts, ends = np.r_[times[0], times[breaks + 1]], np.r_[times[breaks], times[-1]]
    return [(s, e - s + step) for s, e in zip(starts, ends)]


def timeline(truth: pd.DataFrame, ai: pd.DataFrame, path, title: str, ai_label: str = "AI-voorspelling (FaceNet)") -> None:
    """Visualisatie 2 van de opdracht: de tijd (x) tegen de personen (y), per fragment."""
    lengths = fragments(pd.read_csv(FRAMES)).groupby("fragment")["lengte"].first().to_dict()
    groups = sorted(lengths, key=lambda g: int(g.split()[-1]))
    fig, axes = plt.subplots(len(groups), 1, figsize=(12, 1.6 * len(groups) + 0.5), squeeze=False)
    for ax, group in zip(axes[:, 0], groups):
        for y, person in enumerate(NAMES):
            for data, shift, colour in ((truth, 0.18, "#333333"), (ai, -0.18, "#d1495b")):
                t = data[(data["fragment"] == group) & (data["persoon"] == person)]["tijd_s"].to_numpy()
                ax.broken_barh(segments(t, 0.04), (y + shift - 0.15, 0.3), color=colour)
        ax.set_yticks(range(len(NAMES)), NAMES, fontsize=8)
        ax.set_ylim(-0.6, len(NAMES) - 0.4)
        ax.set_xlim(0, lengths[group])
        ax.invert_yaxis()
        ax.set_title(group, fontsize=9, loc="left")
        ax.tick_params(axis="x", labelsize=8)
    axes[-1, 0].set_xlabel("tijd in het fragment (seconden)")
    fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color="#333333"), plt.Rectangle((0, 0), 1, 1, color="#d1495b")],
               labels=["ground truth (labelen)", ai_label], loc="upper right", ncol=2, fontsize=8)
    fig.suptitle(f"Wanneer elke acteur te zien is ({title})", x=0.01, ha="left", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(path, dpi=130)
    plt.close(fig)


def picture_table(data: pd.DataFrame, labels: list, title: str, path) -> None:
    fig, ax = plt.subplots(figsize=(1.45 * len(labels) + 1, 0.42 * len(data) + 1.1))
    ax.axis("off")
    cells = ax.table(cellText=data.astype(str).values, colLabels=labels, loc="center", cellLoc="center")
    cells.auto_set_font_size(False)
    cells.set_fontsize(8.5)
    cells.scale(1, 1.5)
    ax.set_title(title, fontsize=10, loc="left")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def method_1(found: pd.DataFrame, out, title: str) -> pd.DataFrame:
    """Methode 1. Schrijft methode_1_tabel.csv/.png (visualisatie 1 van de opdracht) en methode_1_tijdlijn.png."""
    truth = pd.read_csv(GROUND_TRUTH)[COLUMNS + ["persoon"]]
    ai = presence(found)
    table = method_1_table(truth, ai)
    table.to_csv(out / "methode_1_tabel.csv", index=False, lineterminator="\n")
    shown = table.copy()
    for column in ("precisie", "recall", "f1"):
        shown[column] = shown[column].map(comma)
    shown["foutmarge_procent"] = shown["foutmarge_procent"].map(lambda v: "-" if pd.isna(v) else comma(v, 1) + "%")
    picture_table(shown, ["Acteur", "Ground truth (beelden)", "AI-voorspelling (beelden)", "Foutmarge", "Goed", "Fout", "Gemist",
                          "Precisie", "Recall", "F1"], f"Methode 1, per beeld ({title})", out / "methode_1_tabel.png")
    timeline(truth, ai, out / "methode_1_tijdlijn.png", title)
    return table


# ---------- methode 2: per gezicht ----------

def _by_frame(table: pd.DataFrame) -> dict:
    result = defaultdict(list)
    for r in table.itertuples():
        result[(r.bestand, r.beeld)].append(r)
    return result


def method_2_counts(found: pd.DataFrame, truth: pd.DataFrame, minimum: float = IOU) -> tuple:
    """Per persoon de tellingen van methode 2, de verwarring (wie het echt is tegen de naam van FaceNet, per kader) en per
    kader of de naam goed is."""
    boxes, faces = _by_frame(found), _by_frame(truth)
    counts = {p: {"gezichten": 0, "goed": 0, "fout_benoemd": 0, "gemist": 0, "geen_kader": 0, "geen_naam": 0, "andere_naam": 0} for p in NAMES}
    labels = NAMES + [NOBODY]
    names = NAMES + [OTHER]
    confusion = np.zeros((5, 5), dtype=int)
    right = np.zeros(len(found), dtype=bool)
    position = {r.Index: i for i, r in enumerate(found.itertuples())}
    for frame in set(boxes) | set(faces):
        here, wanted = boxes.get(frame, []), faces.get(frame, [])
        for b in here:
            over = [(overlap((b.x, b.y, b.w, b.h), (f.x, f.y, f.w, f.h)), f.persoon) for f in wanted]
            over = [o for o in over if o[0] >= minimum]
            real = max(over)[1] if over else NOBODY
            confusion[labels.index(real), names.index(b.facenet)] += 1
            if b.facenet in NAMES:
                if any(person == b.facenet for _, person in over):
                    right[position[b.Index]] = True
                else:
                    counts[b.facenet]["fout_benoemd"] += 1
        for f in wanted:
            c = counts[f.persoon]
            c["gezichten"] += 1
            over = [b for b in here if overlap((b.x, b.y, b.w, b.h), (f.x, f.y, f.w, f.h)) >= minimum]
            if any(b.facenet == f.persoon for b in over):
                c["goed"] += 1
            else:
                c["gemist"] += 1
                c["geen_kader" if not over else "geen_naam" if all(b.facenet == OTHER for b in over) else "andere_naam"] += 1
    return counts, confusion, right


def method_2_table(counts: dict) -> pd.DataFrame:
    rows = []
    total = {k: sum(c[k] for c in counts.values()) for k in next(iter(counts.values()))}
    for person, c in {**counts, "samen": total}.items():
        rows.append({"acteur": person, **c, **dict(zip(("precisie", "recall", "f1"), rates(c["goed"], c["fout_benoemd"], c["gemist"])))})
    return pd.DataFrame(rows)


def method_2(found: pd.DataFrame, out, title: str) -> pd.DataFrame:
    """Methode 2. Schrijft methode_2_tabel.csv/.png, methode_2_verwarring.csv/.png, methode_2_overlap.csv (de uitkomst bij
    andere grenzen voor de overlap) en gebruik_per_foto.csv (welke voorbeeldfoto de doorslag gaf, en hoe vaak dat klopte)."""
    truth = pd.read_csv(GROUND_TRUTH)
    counts, confusion, right = method_2_counts(found, truth)
    table = method_2_table(counts)
    table.to_csv(out / "methode_2_tabel.csv", index=False, lineterminator="\n")
    shown = table[["acteur", "gezichten", "goed", "fout_benoemd", "gemist", "precisie", "recall", "f1"]].copy()
    for column in ("precisie", "recall", "f1"):
        shown[column] = shown[column].map(comma)
    picture_table(shown, ["Acteur", "Gezichten", "Goed", "Fout benoemd", "Gemist", "Precisie", "Recall", "F1"],
                  f"Methode 2, per gezicht ({title})", out / "methode_2_tabel.png")

    rows, columns = NAMES + [NOBODY], NAMES + [OTHER]
    pd.DataFrame(confusion, index=[f"echt: {r}" for r in rows], columns=[f"FaceNet: {c}" for c in columns]).to_csv(out / "methode_2_verwarring.csv", lineterminator="\n")
    totals = confusion.sum(axis=1, keepdims=True)
    share = np.divide(confusion, totals, out=np.zeros(confusion.shape), where=totals > 0)
    fig, ax = plt.subplots(figsize=(8, 6.2))
    ax.imshow(share, cmap="Blues", vmin=0, vmax=1)
    for r in range(5):
        for c in range(5):
            ax.text(c, r, f"{confusion[r, c]}\n{100 * share[r, c]:.0f}%", ha="center", va="center", fontsize=9,
                    color="white" if share[r, c] > 0.5 else "black")
    ax.set_xticks(range(5), columns, rotation=20)
    ax.set_yticks(range(5), [r if r != NOBODY else "geen van de vier\n(figurant, geen gezicht)" for r in rows])
    ax.set_xlabel("naam die FaceNet geeft")
    ax.set_ylabel("wie het echt is (ground truth)")
    ax.set_title(f"Per kader: wie het is tegen wat FaceNet zegt (percentage per rij)\n{title}", fontsize=9.5)
    fig.tight_layout()
    fig.savefig(out / "methode_2_verwarring.png", dpi=150)
    plt.close(fig)

    curve = []
    for minimum in (0.1, 0.2, 0.3, 0.4, 0.5, 0.7):
        c = method_2_counts(found, truth, minimum)[0]
        t = {k: sum(v[k] for v in c.values()) for k in ("goed", "fout_benoemd", "gemist")}
        curve.append({"overlap": minimum, **t, **dict(zip(("precisie", "recall", "f1"), rates(t["goed"], t["fout_benoemd"], t["gemist"])))})
    pd.DataFrame(curve).to_csv(out / "methode_2_overlap.csv", index=False, lineterminator="\n")

    named = found.assign(goed=right, gebruikt=found["facenet"].isin(NAMES))
    use = named[named["gebruikt"]].groupby(["dichtstbij", "foto"]).agg(keer_gebruikt=("goed", "size"), waarvan_goed=("goed", "sum")).reset_index()
    use = use.rename(columns={"dichtstbij": "persoon"}).sort_values(["persoon", "keer_gebruikt"], ascending=[True, False])
    use["waarvan_fout"] = use["keer_gebruikt"] - use["waarvan_goed"]
    use.to_csv(out / "gebruik_per_foto.csv", index=False, lineterminator="\n")
    return table


# ---------- methode 2 snel, voor het afstellen en voor leave-one-out ----------

def hit_matrix(detections: pd.DataFrame, truth: pd.DataFrame, minimum: float = IOU) -> np.ndarray:
    """hit[kader, persoon]: het rijnummer van het gezicht van die persoon in de ground truth waar dit kader op ligt, of -1."""
    faces = defaultdict(list)
    for i, f in enumerate(truth.itertuples()):
        faces[(f.bestand, f.beeld)].append((NAMES.index(f.persoon), i, (f.x, f.y, f.w, f.h)))
    hit = np.full((len(detections), len(NAMES)), -1, dtype=np.int32)
    for b, row in enumerate(detections.itertuples()):
        for person, i, box in faces.get((row.video, row.frame), []):
            if overlap((row.x, row.y, row.w, row.h), box) >= minimum:
                hit[b, person] = i
    return hit


def fast_counts(person: np.ndarray, distance: np.ndarray, hit: np.ndarray, faces: int, threshold: float) -> tuple:
    """Goed en fout benoemd van methode 2 bij één drempel: hetzelfde als method_2_counts, maar veel sneller."""
    named = (person >= 0) & (distance < threshold)
    g = hit[np.flatnonzero(named), person[named]]
    return len(np.unique(g[g >= 0])), int((g < 0).sum()), faces - len(np.unique(g[g >= 0]))


def fast_per_person(person: np.ndarray, distance: np.ndarray, hit: np.ndarray, faces_per_person: np.ndarray, threshold: float) -> np.ndarray:
    """Goed, fout benoemd en gemist van methode 2 per persoon (4 x 3), bij één drempel."""
    result = np.zeros((len(NAMES), 3), dtype=int)
    for p in range(len(NAMES)):
        named = (person == p) & (distance < threshold)
        g = hit[named, p]
        good = len(np.unique(g[g >= 0]))
        result[p] = good, int((g < 0).sum()), faces_per_person[p] - good
    return result


def fast_method_1(person: np.ndarray, distance: np.ndarray, frame_id: np.ndarray, truth_frames: np.ndarray, threshold: float) -> tuple:
    """Goed, fout en gemist van methode 1 over alle personen, bij één drempel. `truth_frames` is beelden x 4 (ja of nee)."""
    predicted = np.zeros_like(truth_frames)
    named = (person >= 0) & (distance < threshold)
    predicted[frame_id[named], person[named]] = True
    good = int((predicted & truth_frames).sum())
    return good, int((predicted & ~truth_frames).sum()), int((~predicted & truth_frames).sum())


def fast_setup(detections: pd.DataFrame) -> dict:
    """Alles wat de snelle metingen nodig hebben: de ground truth als getallen."""
    truth = pd.read_csv(GROUND_TRUTH)
    frame_id = detections.groupby(["video", "frame"], sort=False).ngroup().to_numpy()
    index = {(v, f): i for (v, f), i in zip(zip(detections["video"], detections["frame"]), frame_id)}
    frames = len(set(frame_id))
    extra = {}
    for key in set(zip(truth["bestand"], truth["beeld"])) - set(index):       # gezichten in beelden zonder enig kader
        extra[key] = frames + len(extra)
    index.update(extra)
    truth_frames = np.zeros((frames + len(extra), len(NAMES)), dtype=bool)
    truth_frames[[index[k] for k in zip(truth["bestand"], truth["beeld"])], truth["persoon"].map(NAMES.index).to_numpy()] = True
    faces_per_person = truth["persoon"].map(NAMES.index).value_counts().reindex(range(len(NAMES)), fill_value=0).to_numpy()
    return {"hit": hit_matrix(detections, truth), "frame_id": frame_id, "truth_frames": truth_frames, "faces_per_person": faces_per_person}


def grouped_bars(labels: list, first: list, second: list, names: tuple, title: str, path) -> None:
    """Twee staafjes per groep, met de waarde erboven."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8.4, 3.9), facecolor="white")
    for shift, values, name, colour in ((-0.19, first, names[0], "#2a78d6"), (0.19, second, names[1], "#eb6834")):
        ax.bar(x + shift, values, width=0.34, color=colour, label=name)
        for i, value in enumerate(values):
            ax.text(i + shift, value + 0.015, f"{value:.3f}".replace(".", ","), ha="center", fontsize=9, color="#0b0b0b")
    ax.set_xticks(x, labels, fontsize=9.5)
    ax.set_ylim(0, 1)
    ax.set_ylabel("F1", fontsize=9.5, color="#52514e")
    ax.tick_params(length=0, labelsize=9, colors="#52514e")
    ax.grid(axis="y", color="#e4e3de", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    ax.set_title(title, loc="left", fontsize=11, fontweight="bold", color="#0b0b0b")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
