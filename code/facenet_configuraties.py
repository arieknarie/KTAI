"""Welke configuratie van FaceNet herkent de vier personen het best? Algemeen en per filmpje.

Vergeleken worden alle combinaties van:
- model:      Facenet (128 getallen per gezicht) of Facenet512 (512 getallen)
- marge:      het kader precies zoals gevonden (0%), of 20% ruimer aan elke kant (meer van het hoofd erbij)
- voorbeelden: alleen de foto's, of de foto's + de stills in kostuum (zoals in code/basischeck.py)
- afstand:    cosinus, Euclidisch, of Euclidisch na normaliseren (euclidean_l2), de drie afstanden van deepface
- per persoon: de afstand tot het dichtstbijzijnde voorbeeld van die persoon, of tot het gemiddelde van zijn voorbeelden
- toewijzen:  elk kader los de dichtstbijzijnde persoon, of per beeld elke persoon hoogstens één keer (de kaders met
              de kleinste afstand eerst)
- drempel:    is de afstand kleiner dan de drempel, dan is het die persoon; anders iemand anders (200 drempels getest)

Score: per gezicht (per kader). Elk kader heeft volgens het nagekeken antwoordenblad een van de vier namen of geen
naam (figurant, geen gezicht). In een beeld dat bij het nakijken goed kreeg, is dat de keuze van de labelaar voor de
track van het kader (labels/labels.csv); in een beeld dat fout kreeg, krijgt elk verbeterd kader
(labels/correcties.csv) het kader van de computer dat er het meest mee overlapt (minstens 30% overlap, IoU), en de
andere kaders in dat beeld geen naam. Een verbeterd kader zonder kader van de computer eronder telt als gemist.
- goed (TP): FaceNet geeft het kader de juiste naam
- fout (FP): FaceNet geeft een naam aan een kader met een andere of geen naam (bijvoorbeeld een figurant)
- gemist (FN): een kader met een naam krijgt van FaceNet niet die naam, of er was geen kader
F1 is het harmonisch gemiddelde van precisie (TP / (TP + FP)) en recall (TP / (TP + FN)). De beste configuratie is die met de hoogste F1. Let op: de drempel is gekozen op dezelfde beelden waarop
gescoord wordt; de F1 van de beste configuratie is daardoor wat optimistisch.

De embeddings van alle kaders worden één keer gemaakt en bewaard in data/embeddings/ (gaat niet mee naar GitHub).

Uitvoer in results/configuraties/:
    alle_configuraties.csv     elke configuratie met de beste drempel, F1, precisie en recall
    beste_algemeen.csv/.png    de tien beste configuraties over alle filmpjes samen
    beste_per_filmpje.csv/.png per filmpje de beste configuratie, en de score van de algemeen beste daar
    f1_drempel.png             F1 tegen de drempel, per model en afstand (met de beste andere keuzes)
    per_filmpje.png            F1 per filmpje: algemeen beste configuratie tegen de beste voor dat filmpje
    tabel.png, tijdlijn.png    visualisatie 1 en 2 (zoals in de basischeck) met de algemeen beste configuratie
    verwarring.csv/.png        per gezicht wie het echt is tegen welke naam FaceNet geeft (algemeen beste configuratie)
De plaatjes komen ook in results/experimenten/facenet_configuraties/.

Gebruik (vanuit de map KTAI, met de pakketten uit requirements_herkenning.txt):
    .venv-herkenning/bin/python code/facenet_configuraties.py
"""

import itertools
import shutil

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from deepface import DeepFace

import basischeck
from basischeck import BATCH, PERSONS, REPO, fragments, small
from check_labels import items, judged
from fix_labels import corrected

OUT = REPO / "results" / "configuraties"
CACHE = REPO / "data" / "embeddings"
MODELS = ["Facenet", "Facenet512"]
MARGINS = [0.0, 0.2]
NAMES = list(PERSONS.values())


def crop(image: np.ndarray, x, y, w, h, margin: float) -> np.ndarray:
    x0, y0 = max(0, int(x - margin * w)), max(0, int(y - margin * h))
    x1, y1 = int(x + w + margin * w), int(y + h + margin * h)
    return small(image[y0:y1, x0:x1])


def represent(faces: list, model: str) -> np.ndarray:
    """De ruwe embeddings (niet genormaliseerd: de Euclidische afstand gebruikt ze zo)."""
    vectors = []
    for start in range(0, len(faces), BATCH):
        answer = DeepFace.represent(img_path=faces[start:start + BATCH], model_name=model, detector_backend="skip",
                                    enforce_detection=False, align=False)
        vectors += [(a[0] if isinstance(a, list) else a)["embedding"] for a in answer]
    return np.asarray(vectors, dtype=np.float32)


def box_embeddings(detections: pd.DataFrame) -> dict:
    """Per (model, marge) de embedding van elk kader uit detections_0.3.csv, in dezelfde volgorde."""
    CACHE.mkdir(parents=True, exist_ok=True)
    files = {(m, g): CACHE / f"kaders_{m}_marge{int(g * 100)}.npy" for m in MODELS for g in MARGINS}
    if all(f.exists() for f in files.values()):
        return {k: np.load(f) for k, f in files.items()}
    parts = {k: [] for k in files}
    for video, boxes in detections.groupby("video", sort=False):   # zelfde volgorde als de rijen (zie main)
        wanted = {f: g for f, g in boxes.groupby("frame")}
        capture, index, faces = cv2.VideoCapture(str(REPO / "movies" / video)), 0, {g: [] for g in MARGINS}
        while index <= max(wanted):                       # op volgorde lezen, nooit naar een beeld springen
            ok, image = capture.read()
            if not ok:
                raise SystemExit(f"{video}: beeld {index} kon niet gelezen worden")
            for b in (wanted[index].itertuples() if index in wanted else []):
                for g in MARGINS:
                    faces[g].append(crop(image, b.x, b.y, b.w, b.h, g))
            index += 1
        capture.release()
        for m, g in files:
            parts[(m, g)].append(represent(faces[g], m))
        print(f"  {video}: {len(boxes)} kaders")
    for k, f in files.items():
        np.save(f, np.concatenate(parts[k]))
    return {k: np.load(f) for k, f in files.items()}


def example_embeddings() -> dict:
    """Per (model, marge, voorbeelden) de namen en ruwe embeddings van de voorbeelden."""
    result = {}
    for kostuum in (False, True):
        rows = basischeck.example_rows(kostuum)
        for m, g in itertools.product(MODELS, MARGINS):
            faces = [crop(cv2.imread(str(REPO / r.source)), r.x, r.y, r.w, r.h, g) for r in rows.itertuples()]
            result[(m, g, kostuum)] = (rows["label"].map(PERSONS).to_numpy(), represent(faces, m))
    return result


def distances(boxes: np.ndarray, names: np.ndarray, refs: np.ndarray, metric: str, per_person: str) -> np.ndarray:
    """Afstand van elk kader tot elk van de vier personen (kaders x 4)."""
    unit = lambda v: v / np.linalg.norm(v, axis=1, keepdims=True)
    if metric != "euclidean":
        boxes, refs = unit(boxes), unit(refs)
    result = np.empty((len(boxes), len(NAMES)), dtype=np.float32)
    for k, name in enumerate(NAMES):
        own = refs[names == name]
        if per_person == "gemiddelde":
            own = own.mean(axis=0, keepdims=True)
            if metric != "euclidean":
                own = unit(own)
        if metric == "cosine":
            d = 1 - boxes @ own.T
        else:
            d = np.sqrt(np.maximum(0, (boxes ** 2).sum(1)[:, None] + (own ** 2).sum(1)[None] - 2 * boxes @ own.T))
        result[:, k] = d.min(axis=1)
    return result


def assigned(d: np.ndarray, frame_id: np.ndarray, assign: str) -> tuple:
    """Per kader de persoon die FaceNet kiest (0-3) en de afstand. Bij een drempel t krijgt een kader die persoon als
    de afstand kleiner is dan t. Dat klopt ook bij 'uniek': de kaders met de kleinste afstand gaan eerst, dus een
    drempel haalt alleen de laatste keuzes weg."""
    if assign == "los":
        k = d.argmin(axis=1)
        return k, d[np.arange(len(d)), k]
    person, dist = np.full(len(d), -1), np.full(len(d), np.inf, dtype=np.float32)
    boxes, people = np.unravel_index(np.argsort(d, axis=None), d.shape)
    order = np.lexsort((d[boxes, people], frame_id[boxes]))   # per beeld, kleinste afstand eerst
    used_box, used_person, current = set(), set(), -1
    for b, p in zip(boxes[order], people[order]):
        f = frame_id[b]
        if f != current:
            current, used_box, used_person = f, set(), set()
        if b in used_box or p in used_person:
            continue
        used_box.add(b)
        used_person.add(p)
        person[b], dist[b] = p, d[b, p]
    return person, dist


def sweep(person: np.ndarray, dist: np.ndarray, gt: np.ndarray, missed: int, thresholds: np.ndarray) -> np.ndarray:
    """F1, precisie en recall per kader, voor elke drempel (drempels x 3)."""
    right = person == gt
    result = []
    for t in thresholds:
        named = dist < t
        tp = int((named & right).sum())
        precision, recall = tp / max(1, int(named.sum())), tp / max(1, int((gt >= 0).sum()) + missed)
        result.append((2 * precision * recall / max(1e-9, precision + recall), precision, recall))
    return np.array(result)


def iou(a, b) -> float:
    w = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
    h = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    return w * h / (a[2] * a[3] + b[2] * b[3] - w * h) if w > 0 and h > 0 else 0.0


def box_truth(detections: pd.DataFrame, todo: list, frame_id: np.ndarray) -> tuple:
    """Per kader de juiste persoon (0-3, of -1 voor geen naam), en per beeld hoeveel verbeterde kaders geen kader van
    de computer hebben (gemist)."""
    verdict, fixes = judged(), corrected()
    label = pd.read_csv(REPO / "labels" / "labels.csv").set_index("face")["label"]
    gt = np.array([NAMES.index(PERSONS[l]) if l in PERSONS else -1 for l in
                   (label.get(f"{v}#track{t}") for v, t in zip(detections["video"], detections["track"]))])
    missed = np.zeros(len(todo), dtype=int)
    in_frame = pd.Series(np.arange(len(detections))).groupby(frame_id).apply(list).to_dict()
    for i, t in enumerate(todo):
        if verdict[t["key"]] != "fout":
            continue
        own = in_frame.get(i, [])
        gt[own] = -1
        for name, *box in fixes[t["key"]]:
            overlaps = [(iou(box, detections.loc[j, ["x", "y", "w", "h"]].tolist()), j) for j in own if gt[j] < 0]
            best = max(overlaps, default=(0, None))
            if best[0] >= 0.3:
                gt[best[1]] = NAMES.index(name)
            else:
                missed[i] += 1
    return gt, missed


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    detections = pd.read_csv(REPO / "data" / "tracks" / "detections_0.3.csv") \
        .sort_values(["video", "frame"], kind="stable").reset_index(drop=True)   # zo leest box_embeddings ze ook
    frames = pd.read_csv(REPO / "data" / "tracks" / "frames.csv")

    # het nagekeken antwoordenblad: per beeld welke van de vier erin staan (voor de tabel en de tijdlijn)
    verdict, fixes = judged(), corrected()
    todo = [t for t in items() if "#beeld" in t["key"]]
    truth = np.zeros((len(todo), len(NAMES)), dtype=bool)
    for i, t in enumerate(todo):
        for b in (fixes[t["key"]] if verdict[t["key"]] == "fout" else t["boxes"]):
            truth[i, NAMES.index(b[0])] = True
    row = {t["key"]: i for i, t in enumerate(todo)}
    frame_id = np.array([row[f"{v}#beeld{f}"] for v, f in zip(detections["video"], detections["frame"])])
    parts = fragments(frames).set_index("video")
    fragment = np.array([parts.loc[t["video"], "fragment"] for t in todo])
    groups = sorted(set(fragment), key=lambda g: int(g.split()[-1]))
    gt, missed = box_truth(detections, todo, frame_id)       # en per kader wie het is (voor de score)
    box_fragment = fragment[frame_id]

    print("embeddings van de kaders (de eerste keer duurt dit lang)")
    boxes = box_embeddings(detections)
    print("embeddings van de voorbeelden")
    refs = example_embeddings()

    rows, curves, kept = [], {}, {}
    for m, g, kostuum, metric, per_person, assign in itertools.product(
            MODELS, MARGINS, (False, True), ("cosine", "euclidean", "euclidean_l2"), ("dichtstbij", "gemiddelde"),
            ("los", "uniek")):
        names, ref = refs[(m, g, kostuum)]
        person, dist = assigned(distances(boxes[(m, g)], names, ref, metric, per_person), frame_id, assign)
        finite = dist[np.isfinite(dist)]
        thresholds = np.quantile(finite, np.linspace(0.005, 1, 200)) * 1.0001
        config = {"model": m, "marge": f"{int(g * 100)}%", "voorbeelden": "foto's + kostuum" if kostuum else "foto's",
                  "afstand": metric, "per_persoon": per_person, "toewijzen": assign}
        result = sweep(person, dist, gt, int(missed.sum()), thresholds)
        k = result[:, 0].argmax()
        rows.append({**config, "fragment": "alle", "drempel": round(float(thresholds[k]), 4),
                     "f1": result[k, 0], "precisie": result[k, 1], "recall": result[k, 2]})
        for group in groups:
            mask = box_fragment == group
            part = sweep(person[mask], dist[mask], gt[mask], int(missed[fragment == group].sum()), thresholds)
            j = part[:, 0].argmax()
            rows.append({**config, "fragment": group, "drempel": round(float(thresholds[j]), 4),
                         "f1": part[j, 0], "precisie": part[j, 1], "recall": part[j, 2],
                         "f1_bij_algemene_drempel": part[k, 0]})
        name = " | ".join(config.values())
        curves[name] = (config, thresholds, result[:, 0])
        kept[name] = (person, dist)
        print(f"  {name}: F1 {result[k, 0]:.3f} bij drempel {thresholds[k]:.3f}")

    table = pd.DataFrame(rows).round({"f1": 3, "precisie": 3, "recall": 3, "f1_bij_algemene_drempel": 3})
    table.to_csv(OUT / "alle_configuraties.csv", index=False, lineterminator="\n")
    keys = ["model", "marge", "voorbeelden", "afstand", "per_persoon", "toewijzen"]
    overall = table[table["fragment"] == "alle"].sort_values("f1", ascending=False)
    top = overall.drop(columns=["fragment", "f1_bij_algemene_drempel"]).head(10)
    top.to_csv(OUT / "beste_algemeen.csv", index=False, lineterminator="\n")
    winner = overall.iloc[0]
    per_video = []
    for group in groups:
        own = table[table["fragment"] == group].sort_values("f1", ascending=False).iloc[0]
        general = table[(table["fragment"] == group) & (table[keys] == winner[keys]).all(axis=1)].iloc[0]
        per_video.append({"filmpje": group, **{k: own[k] for k in keys}, "drempel": own["drempel"], "f1": own["f1"],
                          "f1_algemeen_beste": general["f1_bij_algemene_drempel"]})
    per_video = pd.DataFrame(per_video)
    per_video.to_csv(OUT / "beste_per_filmpje.csv", index=False, lineterminator="\n")
    print(top.to_string(index=False))
    print(per_video.to_string(index=False))

    figures(top, per_video, curves, winner, keys)
    person, dist = kept[" | ".join(str(winner[k]) for k in keys)]
    pred = np.zeros_like(truth)
    named = dist < winner["drempel"]
    pred[frame_id[named], person[named]] = True
    visualisations(pred, truth, todo, frames, winner)
    confusion(np.where(named, person, -1), gt, int(missed.sum()), winner)
    folder = REPO / "results" / "experimenten" / "facenet_configuraties"   # de plaatjes van dit experiment bij elkaar
    folder.mkdir(parents=True, exist_ok=True)
    for name in ("beste_algemeen", "beste_per_filmpje", "per_filmpje", "f1_drempel", "tabel", "tijdlijn", "verwarring"):
        shutil.copyfile(OUT / f"{name}.png", folder / f"{name}.png")
    print(f"klaar: {OUT.relative_to(REPO)}/")


def picture_table(data: pd.DataFrame, title: str, path) -> None:
    fig, ax = plt.subplots(figsize=(min(18, 1.6 * len(data.columns)), 0.45 * len(data) + 1))
    ax.axis("off")
    cells = ax.table(cellText=data.astype(str).values, colLabels=list(data.columns), loc="center", cellLoc="center")
    cells.auto_set_font_size(False)
    cells.set_fontsize(8)
    cells.auto_set_column_width(range(len(data.columns)))
    ax.set_title(title, fontsize=10, loc="left")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def figures(top: pd.DataFrame, per_video: pd.DataFrame, curves: dict, winner: pd.Series, keys: list) -> None:
    picture_table(top, "De tien beste configuraties van FaceNet (alle filmpjes samen, F1 per gezicht)",
                  OUT / "beste_algemeen.png")
    picture_table(per_video, "Per filmpje de beste configuratie, en de F1 van de algemeen beste configuratie daar",
                  OUT / "beste_per_filmpje.png")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
    for ax, model in zip(axes, MODELS):
        for metric, colour in zip(("cosine", "euclidean", "euclidean_l2"), ("#d1495b", "#00798c", "#edae49")):
            options = {n: c for n, c in curves.items() if c[0]["model"] == model and c[0]["afstand"] == metric}
            name = max(options, key=lambda n: options[n][2].max())
            config, thresholds, scores_ = options[name]
            ax.plot(thresholds, scores_, color=colour,
                    label=f"{metric} ({config['marge']}, {config['voorbeelden']}, {config['per_persoon']}, "
                          f"{config['toewijzen']})")
        ax.set_title(model, fontsize=10)
        ax.set_xlabel("drempel (afstand)")
        ax.legend(fontsize=7)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("F1")
    fig.suptitle("F1 tegen de drempel: per model en afstand de beste combinatie van de andere keuzes", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "f1_drempel.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.arange(len(per_video))
    ax.bar(x - 0.2, per_video["f1_algemeen_beste"], 0.4, color="#333333", label="algemeen beste configuratie")
    ax.bar(x + 0.2, per_video["f1"], 0.4, color="#d1495b", label="beste configuratie voor dat filmpje")
    ax.set_xticks(x, per_video["filmpje"])
    ax.set_ylabel("F1")
    ax.set_ylim(0, 1)
    ax.legend(fontsize=8)
    ax.set_title("F1 per filmpje (algemeen beste: " + ", ".join(str(winner[k]) for k in keys) + ")", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "per_filmpje.png", dpi=150)
    plt.close(fig)


def confusion(pred: np.ndarray, gt: np.ndarray, missed: int, winner: pd.Series) -> None:
    """Per gezicht: wie het echt is (rij) tegen welke naam FaceNet geeft (kolom), met de algemeen beste configuratie."""
    labels = NAMES + ["geen naam"]
    matrix = np.zeros((5, 5), dtype=int)
    np.add.at(matrix, (np.where(gt < 0, 4, gt), np.where(pred < 0, 4, pred)), 1)
    pd.DataFrame(matrix, index=[f"echt: {l}" for l in labels], columns=[f"FaceNet: {l}" for l in labels]) \
        .to_csv(OUT / "verwarring.csv", lineterminator="\n")
    share = matrix / matrix.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(8, 6.5))
    ax.imshow(share, cmap="Blues", vmin=0, vmax=1)
    for r, c in itertools.product(range(5), range(5)):
        ax.text(c, r, f"{matrix[r, c]}\n{100 * share[r, c]:.0f}%", ha="center", va="center", fontsize=9,
                color="white" if share[r, c] > 0.5 else "black")
    ax.set_xticks(range(5), labels, rotation=20)
    ax.set_yticks(range(5), [l if l != "geen naam" else "geen naam\n(figurant, geen gezicht)" for l in labels])
    ax.set_xlabel("naam die FaceNet geeft")
    ax.set_ylabel("wie het echt is (nagekeken antwoordenblad)")
    ax.set_title(f"Per gezicht: wie het is tegen wat FaceNet zegt (percentage per rij)\n{winner['model']}, marge "
                 f"{winner['marge']}, {winner['voorbeelden']}, {winner['afstand']}, {winner['per_persoon']}, "
                 f"{winner['toewijzen']}, drempel {winner['drempel']}. Plus {missed} verbeterde gezichten zonder kader "
                 f"(gemist).", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "verwarring.png", dpi=150)
    plt.close(fig)


def visualisations(pred: np.ndarray, truth: np.ndarray, todo: list, frames: pd.DataFrame, winner: pd.Series) -> None:
    """Visualisatie 1 en 2 van de basischeck, met de algemeen beste configuratie."""
    parts = fragments(frames).set_index("video")
    times = frames.set_index(["video", "frame"])["time_s"]
    def presence(matrix):
        rows = [{"fragment": parts.loc[t["video"], "fragment"], "persoon": NAMES[k],
                 "tijd_s": round(float(times[(t["video"], t["frame"])]) + parts.loc[t["video"], "offset"], 3)}
                for i, t in enumerate(todo) for k in np.flatnonzero(matrix[i])]
        return pd.DataFrame(rows)
    basischeck.OUT = OUT
    basischeck.TITLE = f"beste configuratie: {winner['model']}, marge {winner['marge']}, {winner['voorbeelden']}, " \
                       f"{winner['afstand']} < {winner['drempel']}"
    t, a = presence(truth), presence(pred)
    basischeck.table(t, a)
    basischeck.timeline(t, a)


if __name__ == "__main__":
    main()
