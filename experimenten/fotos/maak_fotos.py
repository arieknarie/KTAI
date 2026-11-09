r"""De uitlegplaatjes in de README's. Alle getallen en beelden komen uit de echte uitkomsten van de experimenten.

Uitvoer in deze map (experimenten/fotos/):
    zo_werkt_facenet.jpg    hoe een gezicht een naam krijgt: hetzelfde gezicht met twee sets voorbeelden
    twee_methodes.jpg       het verschil tussen de twee meetmethodes op een echt beeld
    score_uitgelegd.png     wat precisie, recall en F1 betekenen, met de echte aantallen
    drempel.png             waarom afstellen zoveel uitmaakt: de afstanden en de drempel
    basis_tegen_tuned.gif   FaceNet standaard en FaceNet afgesteld naast elkaar, als bewegend plaatje
    marge_en_lichter.jpg    wat extra ruimte om het kader en lichter maken doen met een gezicht
    per_track.jpg           waarom per track beslissen helpt
    eerlijke_schatting.png  hoe de eerlijke schatting werkt
    schuivend_venster.png   hoe de herkenningsdichtheid wordt uitgerekend
    woorden/                de kleine plaatjes in de woordenlijst

Hiervoor is het programma ffmpeg nodig (zie experimenten/README.md).

Gebruik (vanuit de map experimenten, als de experimenten gedraaid hebben):
    Mac:     .venv/bin/python fotos/maak_fotos.py
    Windows: .venv\Scripts\python fotos\maak_fotos.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.colors import ListedColormap
from matplotlib.patches import FancyBboxPatch, Rectangle
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.facenet import cut, lighten, load_detections, unit, vector_path
from gedeeld.film import fragments
from gedeeld.herkennen import by_track, example_distances, person_distances
from gedeeld.meten import IOU, comma, hit_matrix, method_2_counts, overlap, right_and_wrong
from gedeeld.paden import EXPERIMENTEN, FRAMES, GROUND_TRUTH, MOVIES, NAMES, PICTURES
from gedeeld.voorbeelden import rows
from tuned.instellingen import example_path, winner

HERE = Path(__file__).resolve().parent
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3de"
BLUE, ORANGE, GREY = "#2a78d6", "#eb6834", "#8a8983"
RIGHT, WRONG = (51, 204, 102), (255, 77, 77)                     # groen en rood voor een naam die klopt of niet klopt
PERSON_COLOURS = {"Der Alte": "#ff4d4d", "Fritz Grade": "#4da6ff", "Johann": "#ffd11a", "Werner": "#33cc66"}

VIDEO_1 = "Das Boot 1 [Ek2omNPSOYc] 28m10s-28m55s.mp4"
VIDEO_5 = "Das Boot 5 [kefBHWylmMk] 32m05s-33m06s.mp4"
OVERVIEW_FRAME = 22                 # het beeld dat ook bovenaan labelen/README.md staat, met de track die Werner is
OVERVIEW_TRACK = 0
EXAMPLE_FRAME = 92                  # een gezicht dat met alleen foto's geen naam krijgt, en met stills erbij de juiste naam
EXAMPLE_TRACK = 1
GIF_START, GIF_FRAMES = 550, 125    # 5 seconden uit Video 5: daar is het verschil tussen standaard en afgesteld het grootst


def result(experiment: str, example_set: str) -> Path:
    return EXPERIMENTEN / experiment / "resultaten" / example_set


def frames_of(video: str, wanted) -> dict:
    """De gevraagde beelden uit een video, op volgorde gelezen: nooit naar een beeld springen."""
    wanted, found, capture = set(wanted), {}, cv2.VideoCapture(str(MOVIES / video))
    for index in range(max(wanted) + 1):
        ok, image = capture.read()
        if not ok:
            raise SystemExit(f"{video}: beeld {index} kon niet gelezen worden")
        if index in wanted:
            found[index] = image
    capture.release()
    return found


def rgb(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def number(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def bare(ax) -> None:
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def clean(ax, axis: str = "y") -> None:
    ax.tick_params(length=0, labelsize=9, colors=MUTED)
    ax.grid(axis=axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(font_manager.findfont(font_manager.FontProperties(family="DejaVu Sans", weight="bold" if bold else "normal")), size)


def tag(draw: ImageDraw.ImageDraw, box: tuple, text: str, colour: tuple, size: int = 13, width: int = 3) -> None:
    """Een kader met de naam erboven."""
    x, y, w, h = box
    draw.rectangle((x, y, x + w, y + h), outline=colour, width=width)
    if text:
        face = font(size, bold=True)
        top = y - size - 6 if y - size - 6 > 0 else y
        draw.rectangle((x, top, x + draw.textlength(text, font=face) + 8, top + size + 6), fill=colour)
        draw.text((x + 4, top + 2), text, fill=(15, 15, 15), font=face)


def save_jpg(image, path: Path, quality: int = 88) -> None:
    Image.fromarray(image).convert("RGB").save(path, quality=quality, optimize=True)


# ---------- hoe een gezicht een naam krijgt ----------

def how_facenet_works(data: dict, image: np.ndarray) -> None:
    b = data["example_box"]
    box = data["detections"].iloc[b]
    vector = unit(np.load(vector_path("Facenet", 0.0))[b:b + 1])
    face = rgb(cut(image, box.x, box.y, box.w, box.h))
    fig = plt.figure(figsize=(14.6, 8.2), facecolor="white")
    outer = fig.add_gridspec(2, 5, width_ratios=[3.25, 1.45, 1.45, 4.3, 2.0], hspace=0.5, wspace=0.13, left=0.012, right=0.992, top=0.79, bottom=0.035)
    fig.text(0.012, 0.965, "Hoe een gezicht een naam krijgt", fontsize=17, fontweight="bold", color=INK)
    fig.text(0.012, 0.925, "Twee keer hetzelfde gezicht uit Video 1. Alleen de voorbeelden waarmee FaceNet vergelijkt, verschillen. De drempel is allebei de keren 0,80.", fontsize=11.5, color=MUTED)
    titles = ["1. Het beeld met het kader", "2. Het gezicht", "3. De 128 getallen", "4. Afstand tot de voorbeelden van elke persoon", "5. De uitkomst"]
    labels = {"fotos": "Als voorbeeld alleen de gewone foto's", "fotos_en_kostuum": "Als voorbeeld de gewone foto's én de stills uit de film"}
    h, w = image.shape[:2]
    for row, example_set in enumerate(("fotos", "fotos_en_kostuum")):
        table = pd.read_csv(result("basis", example_set) / "voorbeelden.csv")
        refs = table[[f"v{i}" for i in range(128)]].to_numpy(dtype=np.float32)
        d = example_distances(vector, refs, "euclidean_l2")[0]
        nearest = {p: int(np.flatnonzero(table["persoon"] == p)[d[table["persoon"] == p].argmin()]) for p in NAMES}
        closest = min(NAMES, key=lambda p: d[nearest[p]])
        smallest = float(d[nearest[closest]])
        top, x = outer[row, 0].get_position(fig).y1, [outer[row, c].get_position(fig).x0 for c in range(5)]
        fig.text(x[0], top + 0.062, labels[example_set], fontsize=13.5, fontweight="bold", color=BLUE)
        for column, title in enumerate(titles):
            fig.text(x[column], top + 0.016, title, fontsize=11.5, fontweight="bold", color=INK)

        ax = fig.add_subplot(outer[row, 0])
        ax.imshow(cv2.resize(rgb(image), (960, round(960 * h / w)), interpolation=cv2.INTER_AREA), extent=(0, w, h, 0))
        ax.add_patch(Rectangle((box.x, box.y), box.w, box.h, fill=False, edgecolor=BLUE, linewidth=2.6))
        ax.set_anchor("N")
        bare(ax)

        ax = fig.add_subplot(outer[row, 1])
        ax.imshow(cv2.resize(face, (320, 320), interpolation=cv2.INTER_AREA))
        ax.set_anchor("N")
        bare(ax)

        ax = fig.add_subplot(outer[row, 2])
        limit = float(np.abs(vector).max())
        ax.imshow(vector[0].reshape(16, 8), cmap="RdBu_r", vmin=-limit, vmax=limit, aspect="auto")
        bare(ax)
        ax.text(0, -0.03, "   ".join(comma(float(v), 2) for v in vector[0][:3]) + "  …", transform=ax.transAxes, fontsize=8.5, color=MUTED, va="top")

        inner = outer[row, 3].subgridspec(4, 2, width_ratios=[1, 5.4], hspace=0.1, wspace=0.03)
        for i, person in enumerate(NAMES):
            r = table.iloc[nearest[person]]
            example = rgb(cut(cv2.imread(str(PICTURES / r["bestand"])), r["x"], r["y"], r["w"], r["h"]))
            ax = fig.add_subplot(inner[i, 0])
            ax.imshow(cv2.resize(example, (96, 96), interpolation=cv2.INTER_AREA))
            bare(ax)
            ax = fig.add_subplot(inner[i, 1])
            distance = float(d[nearest[person]])
            ax.barh(0, distance, height=0.5, color=BLUE if person == closest else "#c9c8c2")
            ax.text(1.74, 0, comma(distance, 2), va="center", ha="right", fontsize=11.5, fontweight="bold" if person == closest else "normal", color=INK)
            ax.text(0.012, 0.76, person, transform=ax.transAxes, fontsize=10, fontweight="bold", color=INK, va="center")
            ax.axvline(0.80, color=INK, linewidth=1.3, linestyle=(0, (4, 3)))
            ax.set_xlim(0, 1.76)
            ax.set_ylim(-0.4, 0.82)
            bare(ax)
            if i == 0:
                ax.text(0.80 / 1.76 + 0.01, 0.76, "drempel 0,80", transform=ax.transAxes, fontsize=9.5, color=INK, va="center")

        ax = fig.add_subplot(outer[row, 4])
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        named = smallest < 0.80
        ax.add_patch(FancyBboxPatch((0.03, 0.66), 0.94, 0.26, boxstyle="round,pad=0.01,rounding_size=0.05", facecolor=BLUE if named else "#c9c8c2", edgecolor="none"))
        ax.text(0.5, 0.79, closest if named else "iemand anders", ha="center", va="center", fontsize=15, fontweight="bold", color="white" if named else INK)
        ax.text(0.5, 0.58, f"De kleinste afstand is\n{comma(smallest, 2)}. Dat is {'kleiner' if named else 'groter'} dan\nde drempel, dus FaceNet\n{'geeft deze naam.' if named else 'geeft geen naam.'}", ha="center", va="top", fontsize=11, color=INK, linespacing=1.35)
    fig.savefig(HERE / "zo_werkt_facenet.jpg", dpi=105, pil_kwargs={"quality": 90})
    plt.close(fig)


# ---------- de twee meetmethodes ----------

def two_methods(data: dict) -> None:
    found = pd.read_csv(result("basis", "fotos_en_kostuum") / "voorspellingen.csv")
    truth = data["truth"]
    faces = {key: g for key, g in truth.groupby(["bestand", "beeld"])}
    named = found[found["facenet"].isin(NAMES)]
    best, score = None, -1
    for key, g in named.groupby(["bestand", "beeld"]):                  # een beeld waarin een persoon echt is, maar de naam óók op een ander gezicht staat
        if key not in faces or len(faces[key]) < 2 or not key[0].startswith(("Das Boot 1 ", "Das Boot 4", "Das Boot 3")):
            continue
        for b in g.itertuples():
            same = faces[key][faces[key]["persoon"] == b.facenet]
            if len(same) and overlap((b.x, b.y, b.w, b.h), tuple(same[["x", "y", "w", "h"]].iloc[0])) < IOU and b.w > score:
                best, score = (key, b.facenet), b.w
    (video, frame), person = best
    image = rgb(frames_of(video, [frame])[frame])
    h, w = image.shape[:2]
    small = cv2.resize(image, (1280, round(1280 * h / w)), interpolation=cv2.INTER_AREA)
    here = named[(named["bestand"] == video) & (named["beeld"] == frame)]
    gt = faces[(video, frame)]
    verdict = {}
    for b in here.itertuples():
        same = gt[gt["persoon"] == b.facenet]
        verdict[b.Index] = len(same) > 0 and overlap((b.x, b.y, b.w, b.h), tuple(same[["x", "y", "w", "h"]].iloc[0])) >= IOU
    other = next(p for p in gt["persoon"] if p != person)
    fig = plt.figure(figsize=(14, 5.55), facecolor="white")
    grid = fig.add_gridspec(2, 2, height_ratios=[3.95, 0.9], hspace=0.05, wspace=0.03, left=0.01, right=0.99, top=0.93, bottom=0.01)
    panels = ((grid[0, 0], [(r.facenet + (" ✓" if verdict[r.Index] else " ✗"), r.facenet, r.x, r.y, r.w, r.h) for r in here.itertuples()], "Wat FaceNet zegt"),
              (grid[0, 1], [(r.persoon, r.persoon, r.x, r.y, r.w, r.h) for r in gt.itertuples()], "Wie er echt staat (de ground truth)"))
    for cell, boxes, title in panels:
        ax = fig.add_subplot(cell)
        ax.imshow(small, extent=(0, w, h, 0))
        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)
        bare(ax)
        for text, name, x, y, bw, bh in boxes:
            ax.add_patch(Rectangle((x, y), bw, bh, fill=False, edgecolor=PERSON_COLOURS[name], linewidth=2.6))
            ax.text(x, y, text, fontsize=12, fontweight="bold", color="#111111", va="bottom", ha="left", bbox={"facecolor": PERSON_COLOURS[name], "edgecolor": "none", "pad": 1.5})
        ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color=INK)
    ax = fig.add_subplot(grid[1, :])
    ax.axis("off")
    ax.text(0, 0.72, "Methode 1 (per beeld):", fontsize=12, fontweight="bold", color=BLUE, va="center", transform=ax.transAxes)
    ax.text(0.19, 0.72, f"{person} staat in dit beeld en FaceNet noemt {person}. Dat telt als goed, ook al staat de naam ook op het verkeerde gezicht.", fontsize=12, color=INK, va="center", transform=ax.transAxes)
    ax.text(0, 0.24, "Methode 2 (per gezicht):", fontsize=12, fontweight="bold", color=ORANGE, va="center", transform=ax.transAxes)
    ax.text(0.19, 0.24, f"Het kader met ✓ is goed. Het kader met ✗ heet {person}, maar ligt op het gezicht van {other}. Dat is fout, en {other} is gemist.", fontsize=12, color=INK, va="center", transform=ax.transAxes)
    fig.savefig(HERE / "twee_methodes.jpg", dpi=105, pil_kwargs={"quality": 90})
    plt.close(fig)


# ---------- de score ----------

def explain_score() -> None:
    fig, axes = plt.subplots(2, 1, figsize=(13.4, 5.5), facecolor="white", sharex=True, gridspec_kw={"hspace": 0.36})
    cases = (("tuned", "FaceNet getuned, met foto's + stills"), ("basis", "FaceNet standaard, met foto's + stills"))
    tables = {e: pd.read_csv(result(e, "fotos_en_kostuum") / "methode_2_tabel.csv").set_index("acteur").loc["samen"] for e, _ in cases}
    longest = max(max(int(r["goed"]) + int(r["fout_benoemd"]), int(r["goed"]) + int(r["gemist"])) for r in tables.values())
    for ax, (experiment, title) in zip(axes, cases):
        r = tables[experiment]
        good, wrong, missed = int(r["goed"]), int(r["fout_benoemd"]), int(r["gemist"])
        for y, rest, rest_name, colour in ((0, missed, "gemist", GREY), (1, wrong, "fout", ORANGE)):
            ax.barh(y, good, height=0.62, color=BLUE, edgecolor="white", linewidth=2)
            ax.barh(y, rest, left=good, height=0.62, color=colour, edgecolor="white", linewidth=2)
            ax.text(good / 2, y, f"{number(good)} goed", ha="center", va="center", fontsize=11, fontweight="bold", color="white")
            if rest > 0.2 * longest:
                ax.text(good + rest / 2, y, f"{number(rest)} {rest_name}", ha="center", va="center", fontsize=11, fontweight="bold", color="white")
            else:
                ax.text(good + rest + longest * 0.012, y, f"{number(rest)} {rest_name}", ha="left", va="center", fontsize=11, fontweight="bold", color=INK)
        ax.set_yticks([0, 1], [f"Alle echte gezichten\n({number(good + missed)})", f"Alle namen die FaceNet gaf\n({number(good + wrong)})"], fontsize=10.5, color=INK)
        ax.invert_yaxis()
        ax.tick_params(length=0)
        ax.set_xticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color=INK)
        ax.text(1.02, 0.83, f"Recall {comma(r['recall'])}", transform=ax.transAxes, fontsize=11.5, fontweight="bold", color=INK, va="center")
        ax.text(1.02, 0.70, "deel van de gezichten met de juiste naam", transform=ax.transAxes, fontsize=8.8, color=MUTED, va="center")
        ax.text(1.02, 0.33, f"Precisie {comma(r['precisie'])}", transform=ax.transAxes, fontsize=11.5, fontweight="bold", color=INK, va="center")
        ax.text(1.02, 0.20, "deel van de namen dat klopt", transform=ax.transAxes, fontsize=8.8, color=MUTED, va="center")
        ax.text(1.62, 0.55, comma(r["f1"]), transform=ax.transAxes, fontsize=27, fontweight="bold", color=INK, va="center", ha="center")
        ax.text(1.62, 0.3, "score (F1)", transform=ax.transAxes, fontsize=10.5, color=MUTED, va="center", ha="center")
    axes[0].set_xlim(0, longest * 1.02)
    fig.subplots_adjust(left=0.17, right=0.63, top=0.93, bottom=0.03)
    fig.savefig(HERE / "score_uitgelegd.png", dpi=120)
    plt.close(fig)


# ---------- de drempel ----------

def threshold(data: dict) -> None:
    index = {n: i for i, n in enumerate(NAMES)}
    hit = data["hit"]
    panels = [("basis", "fotos", 0.80, "Standaard, alleen foto's", "bijna niemand krijgt een naam"),
              ("basis", "fotos_en_kostuum", 0.80, "Standaard, foto's + stills", "bijna iedereen krijgt een naam, ook als het fout is"),
              ("tuned", "fotos", winner("fotos")["drempel"], "Getuned, alleen foto's", "goed en fout liggen aan weerszijden van de drempel"),
              ("tuned", "fotos_en_kostuum", winner("fotos_en_kostuum")["drempel"], "Getuned, foto's + stills", "goed en fout liggen aan weerszijden van de drempel")]
    fig, axes = plt.subplots(2, 2, figsize=(12.6, 7.9), facecolor="white", sharex=True, gridspec_kw={"hspace": 0.42, "wspace": 0.12})
    bins = np.linspace(0, 1.6, 65)
    for ax, (experiment, example_set, limit, title, note) in zip(axes.flat, panels):
        found = pd.read_csv(result(experiment, example_set) / "voorspellingen.csv")
        distance = found["afstand"].to_numpy()
        person = found["dichtstbij"].map(index).to_numpy()
        ok = np.isfinite(distance)            # bij "elke persoon één keer per beeld" krijgt niet elk kader een persoon
        right = hit[np.arange(len(found)), person] >= 0
        ax.axvspan(0, limit, color="#f1f6fd", linewidth=0)
        ax.hist(distance[ok & ~right], bins=bins, color=ORANGE, alpha=0.75, label="de dichtstbijzijnde persoon klopt niet")
        ax.hist(distance[ok & right], bins=bins, color=BLUE, alpha=0.8, label="de dichtstbijzijnde persoon klopt")
        ax.axvline(limit, color=INK, linewidth=1.4, linestyle=(0, (4, 3)))
        ax.text(limit + 0.015, ax.get_ylim()[1] * 0.95, f"drempel {comma(limit, 2)}", fontsize=10.5, fontweight="bold", color=INK, va="top")
        ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color=INK, pad=40)
        share_right, share_wrong = 100 * (distance[ok & right] < limit).mean(), 100 * (distance[ok & ~right] < limit).mean()
        ax.text(0, 1.095, note, transform=ax.transAxes, fontsize=11, color=INK)
        ax.text(0, 1.025, f"Krijgt een naam: {share_right:.0f}% van de blauwe en {share_wrong:.0f}% van de oranje kaders", transform=ax.transAxes, fontsize=9.5, color=MUTED)
        ax.set_xlim(0, 1.6)
        clean(ax, "y")
    for ax in axes[1]:
        ax.set_xlabel("afstand tot de dichtstbijzijnde persoon (klein = lijkt erg op elkaar)", fontsize=10, color=MUTED)
    for ax in axes[:, 0]:
        ax.set_ylabel("aantal kaders", fontsize=10, color=MUTED)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles[::-1], labels[::-1], loc="upper left", ncol=2, frameon=False, fontsize=11, bbox_to_anchor=(0.06, 1.0))
    fig.subplots_adjust(left=0.07, right=0.985, top=0.85, bottom=0.075)
    fig.savefig(HERE / "drempel.png", dpi=115)
    plt.close(fig)


# ---------- FaceNet standaard en afgesteld naast elkaar ----------

def before_after_gif(data: dict) -> None:
    truth = data["truth"]
    truth = truth[truth["bestand"] == VIDEO_5]
    scores = {}
    panels = []
    for experiment, title in (("basis", "FaceNet standaard"), ("tuned", "FaceNet getuned")):
        found = pd.read_csv(result(experiment, "fotos_en_kostuum") / "voorspellingen.csv")
        panels.append((title, found[(found["bestand"] == VIDEO_5) & found["facenet"].isin(NAMES)]))
        scores[title] = pd.read_csv(result(experiment, "fotos_en_kostuum") / "methode_2_tabel.csv").set_index("acteur").loc["samen", "f1"]
    wanted = range(GIF_START, GIF_START + GIF_FRAMES, 2)
    images = frames_of(VIDEO_5, wanted)
    panel_w, panel_h, top, bottom = 480, 270, 36, 26
    with tempfile.TemporaryDirectory() as folder:
        for n, frame in enumerate(wanted):
            canvas = Image.new("RGB", (panel_w * 2 + 8, top + panel_h + bottom), "white")
            draw = ImageDraw.Draw(canvas)
            for k, (title, found) in enumerate(panels):
                left = k * (panel_w + 8)
                shown = Image.fromarray(rgb(cv2.resize(images[frame], (panel_w, panel_h), interpolation=cv2.INTER_AREA)))
                pen = ImageDraw.Draw(shown)
                scale = panel_w / images[frame].shape[1]
                faces = truth[truth["beeld"] == frame]
                for b in found[found["beeld"] == frame].itertuples():
                    same = faces[faces["persoon"] == b.facenet]
                    good = len(same) > 0 and overlap((b.x, b.y, b.w, b.h), tuple(same[["x", "y", "w", "h"]].iloc[0])) >= IOU
                    tag(pen, tuple(round(v * scale) for v in (b.x, b.y, b.w, b.h)), b.facenet, RIGHT if good else WRONG, size=12, width=2)
                canvas.paste(shown, (left, top))
                draw.text((left + 4, 8), f"{title}: score {comma(scores[title])}", fill=(11, 11, 11), font=font(17, bold=True))
            draw.text((4, top + panel_h + 5), "groen: de naam klopt     rood: de naam klopt niet     de score geldt voor alle filmpjes samen", fill=(82, 81, 78), font=font(13))
            canvas.save(Path(folder) / f"{n:03d}.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12.5", "-i", str(Path(folder) / "%03d.png"), "-vf",
                        "split[a][b];[a]palettegen=max_colors=160:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
                        "-loop", "0", str(HERE / "basis_tegen_tuned.gif")], check=True)


# ---------- wat de instellingen doen ----------

def margin_and_light(data: dict, video: str, frame: int) -> None:
    face = data["truth"][(data["truth"]["bestand"] == video) & (data["truth"]["beeld"] == frame) & (data["truth"]["persoon"] == "Werner")].iloc[0]
    image = frames_of(video, [frame])[frame]
    margins = [0.0, 0.1, 0.2, 0.3]
    fig, axes = plt.subplots(2, 4, figsize=(10.4, 5.5), facecolor="white", gridspec_kw={"hspace": 0.06, "wspace": 0.04})
    for j, margin in enumerate(margins):
        crop = cut(image, face.x, face.y, face.w, face.h, margin)
        for i, picture in enumerate((crop, lighten(crop))):
            ax = axes[i, j]
            ax.imshow(cv2.resize(rgb(picture), (300, 300), interpolation=cv2.INTER_AREA))
            bare(ax)
            if margin == 0.2 and i == 1:
                for spine in ax.spines.values():
                    spine.set_visible(True)
                    spine.set_color(BLUE)
                    spine.set_linewidth(4)
                ax.text(0.5, 0.05, "wat het beste werkt", transform=ax.transAxes, ha="center", fontsize=11, fontweight="bold", color="white", bbox={"facecolor": BLUE, "edgecolor": "none", "pad": 3})
        axes[0, j].set_title("geen extra ruimte" if margin == 0 else f"{margin:.0%} extra ruimte", fontsize=12, fontweight="bold", color=INK)
    axes[0, 0].set_ylabel("zoals in de film", fontsize=12, fontweight="bold", color=INK)
    axes[1, 0].set_ylabel("lichter gemaakt", fontsize=12, fontweight="bold", color=INK)
    fig.subplots_adjust(left=0.05, right=0.995, top=0.93, bottom=0.01)
    fig.savefig(HERE / "marge_en_lichter.jpg", dpi=105, pil_kwargs={"quality": 90})
    plt.close(fig)


def per_track_figure(data: dict) -> None:
    best = winner("fotos_en_kostuum")
    detections, hit = data["detections"], data["hit"]
    vectors = np.load(vector_path(best["model"], best["marge"], best["lichter"]))
    refs = np.load(example_path("fotos_en_kostuum", best["model"], best["marge"], best["lichter"]))
    names = rows("fotos_en_kostuum")["persoon"].to_numpy()
    d = person_distances(vectors, names, refs, best["afstand"], best["per_persoon"])
    track_id = detections.groupby(["video", "track"], sort=False).ngroup().to_numpy()
    together = by_track(d, track_id)
    nearest = d.argmin(axis=1)
    candidates = []
    for t in np.unique(track_id):                      # een lange track met een groot gezicht, die per kader wisselt en per track klopt
        i = np.flatnonzero(track_id == t)
        person = together[i[0]].argmin()
        if len(i) < 60 or detections["w"].iloc[i].median() < 400 or together[i[0], person] > best["drempel"] - 0.04 or (hit[i, person] >= 0).mean() < 0.95:
            continue
        named = d[i, nearest[i]] < best["drempel"]
        if len(set(nearest[i][named]) - {person}) >= 2:
            candidates.append((((nearest[i] == person) & named).mean(), t))
    t = min(candidates)[1]
    i = np.flatnonzero(track_id == t)
    person = int(together[i[0]].argmin())
    state = np.where(d[i, nearest[i]] >= best["drempel"], 0, np.where(nearest[i] == person, 2, 1))      # 0 geen naam, 1 verkeerde naam, 2 juiste naam
    video = detections["video"].iloc[i[0]]
    chosen = np.linspace(0, len(i) - 1, 8).round().astype(int)
    frames = detections["frame"].iloc[i].to_numpy()
    images = frames_of(video, frames[chosen])

    fig = plt.figure(figsize=(12.4, 3.75), facecolor="white")
    grid = fig.add_gridspec(3, 8, height_ratios=[3.2, 0.5, 0.5], hspace=0.5, wspace=0.05, left=0.09, right=0.995, top=0.985, bottom=0.105)
    for k, position in enumerate(chosen):
        b = detections.iloc[i[position]]
        ax = fig.add_subplot(grid[0, k])
        ax.imshow(cv2.resize(rgb(cut(images[b.frame], b.x, b.y, b.w, b.h)), (220, 220), interpolation=cv2.INTER_AREA))
        bare(ax)
        name = NAMES[nearest[i[position]]] if state[position] else "geen naam"
        ax.text(0.5, -0.04, name, transform=ax.transAxes, ha="center", va="top", fontsize=10.5, fontweight="bold", color={0: GREY, 1: ORANGE, 2: BLUE}[int(state[position])])
    colours = ListedColormap(["#c9c8c2", ORANGE, BLUE])
    ax = fig.add_subplot(grid[1, :])
    ax.imshow(state[None, :], cmap=colours, vmin=0, vmax=2, aspect="auto", interpolation="nearest")
    bare(ax)
    ax.text(-0.008, 0.5, "per kader", transform=ax.transAxes, ha="right", va="center", fontsize=11, fontweight="bold", color=INK)
    ax = fig.add_subplot(grid[2, :])
    ax.imshow(np.full((1, len(i)), 2), cmap=colours, vmin=0, vmax=2, aspect="auto", interpolation="nearest")
    bare(ax)
    ax.text(0.5, 0.5, f"{NAMES[person]}: de hele track één beslissing", transform=ax.transAxes, ha="center", va="center", fontsize=11, fontweight="bold", color="white")
    ax.text(-0.008, 0.5, "per track", transform=ax.transAxes, ha="right", va="center", fontsize=11, fontweight="bold", color=INK)
    fig.text(0.09, 0.022, f"{len(i)} beelden uit één track.   Blauw: de juiste naam.   Oranje: een verkeerde naam.   Grijs: geen naam.", fontsize=10.5, color=MUTED)
    fig.savefig(HERE / "per_track.jpg", dpi=110, pil_kwargs={"quality": 90})
    plt.close(fig)
    print(f"per_track: {video.split(' [')[0]}, track {detections['track'].iloc[i[0]]}, {len(i)} beelden, {NAMES[person]}")


def fair_estimate() -> None:
    table = pd.read_csv(result("tuned", "fotos_en_kostuum") / "eerlijke_schatting.csv")
    n = len(table)
    fig, ax = plt.subplots(figsize=(9.6, 3.7), facecolor="white")
    for row, r in enumerate(table.itertuples()):
        for column in range(n):
            test = column == row
            ax.add_patch(Rectangle((column + 0.04, row + 0.06), 0.92, 0.88, facecolor=ORANGE if test else "#dcdbd5", edgecolor="none"))
            ax.text(column + 0.5, row + 0.5, "meten" if test else "afstellen", ha="center", va="center", fontsize=8.5, fontweight="bold" if test else "normal", color="white" if test else MUTED)
        ax.text(n + 0.2, row + 0.5, comma(r.f1), va="center", fontsize=10.5, fontweight="bold", color=INK)
        ax.text(-0.15, row + 0.5, f"ronde {row + 1}", va="center", ha="right", fontsize=9.5, color=MUTED)
    for column, name in enumerate(table["filmpje"]):
        ax.text(column + 0.5, -0.25, name, ha="center", va="center", fontsize=9.5, color=INK)
    ax.text(n + 0.2, -0.25, "score", va="center", fontsize=9.5, color=INK)
    ax.set_xlim(-0.95, n + 1)
    ax.set_ylim(n, -0.6)
    ax.axis("off")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    fig.savefig(HERE / "eerlijke_schatting.png", dpi=125)
    plt.close(fig)


def sliding_window(data: dict) -> None:
    frames = pd.read_csv(FRAMES)
    frames = frames[frames["video"] == VIDEO_1].sort_values("frame")
    found = pd.read_csv(result("basis", "fotos_en_kostuum") / "voorspellingen.csv")
    good = right_and_wrong(found, method_2_counts(found, data["truth"])[2])[0]
    window, cells = 15, 47
    best = (-1, None, 0)                 # het stukje film waarin de juiste naam het vaakst aan- en uitgaat
    for person in NAMES:
        seen = set(good[(good["bestand"] == VIDEO_1) & (good["persoon"] == person)]["beeld"])
        candidate = np.array([f in seen for f in frames["frame"]], dtype=float)
        for first in range(0, len(candidate) - cells, 5):
            part = candidate[first:first + cells]
            changes = int(np.abs(np.diff(part)).sum()) if 0.35 <= part.mean() <= 0.65 else -1
            if changes > best[0]:
                best = (changes, person, first)
    _, person, start = best
    seen = set(good[(good["bestand"] == VIDEO_1) & (good["persoon"] == person)]["beeld"])
    signal = np.array([f in seen for f in frames["frame"]], dtype=float)
    density = np.convolve(signal, np.ones(window), "same") / np.convolve(np.ones(len(signal)), np.ones(window), "same")
    centre = 8                        # het beeld (geteld vanaf het begin van het plaatje) waarvoor het venster getekend wordt
    fig, ax = plt.subplots(figsize=(12, 3.5), facecolor="white")
    for k in range(cells):
        ax.add_patch(Rectangle((k + 0.05, 1.45), 0.9, 0.9, facecolor=INK if signal[start + k] else "white", edgecolor="#c9c8c2", linewidth=0.7))
        ax.add_patch(Rectangle((k + 0.05, 0), 0.9, 0.9, facecolor=plt.cm.Blues(float(density[start + k])), edgecolor="#c9c8c2", linewidth=0.7))
    left = centre - window // 2
    ax.add_patch(Rectangle((left, 1.33), window, 1.14, fill=False, edgecolor=ORANGE, linewidth=2.6))
    ax.add_patch(Rectangle((centre + 0.02, -0.04), 0.96, 0.98, fill=False, edgecolor=ORANGE, linewidth=2.6))
    ax.annotate("", xy=(centre + 0.5, 0.98), xytext=(centre + 0.5, 1.31), arrowprops={"arrowstyle": "-|>", "color": ORANGE, "linewidth": 2})
    part = signal[start + left:start + left + window]
    ax.text(left, 2.62, f"Venster van {window} beelden: in {int(part.sum())} van de {window} beelden staat de juiste naam op het gezicht. {int(part.sum())} / {window} = {comma(part.sum() / window, 2)}", ha="left", va="bottom", fontsize=11.5, fontweight="bold", color=ORANGE)
    ax.text(-0.3, 1.9, "De juiste naam\nop het gezicht\n(zwart = ja)", ha="right", va="center", fontsize=10, color=INK)
    ax.text(-0.3, 0.45, "Herkennings-\ndichtheid\n(donkerder = hoger)", ha="right", va="center", fontsize=10, color=INK)
    ax.set_xlim(-7.4, cells + 0.1)
    ax.set_ylim(-0.2, 3.02)
    ax.axis("off")
    fig.subplots_adjust(left=0.005, right=0.995, top=0.99, bottom=0.01)
    fig.savefig(HERE / "schuivend_venster.png", dpi=120)
    plt.close(fig)


# ---------- de kleine plaatjes in de woordenlijst ----------

def glossary(data: dict, image: np.ndarray) -> None:
    out = HERE / "woorden"
    out.mkdir(exist_ok=True)
    detections, truth = data["detections"], data["truth"]
    h, w = image.shape[:2]
    width, height, scale = 360, round(360 * h / w), 360 / w
    small = Image.fromarray(rgb(cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)))
    save_jpg(np.array(small), out / "beeld.jpg")

    boxes = small.copy()
    pen = ImageDraw.Draw(boxes)
    for b in detections[(detections["video"] == VIDEO_1) & (detections["frame"] == OVERVIEW_FRAME)].itertuples():
        tag(pen, tuple(round(v * scale) for v in (b.x, b.y, b.w, b.h)), "", (51, 204, 102), width=2)
    save_jpg(np.array(boxes), out / "kader.jpg")

    answer = small.copy()
    pen = ImageDraw.Draw(answer)
    for f in truth[(truth["bestand"] == VIDEO_1) & (truth["beeld"] == OVERVIEW_FRAME)].itertuples():
        tag(pen, tuple(round(v * scale) for v in (f.x, f.y, f.w, f.h)), f.persoon, tuple(int(PERSON_COLOURS[f.persoon][i:i + 2], 16) for i in (1, 3, 5)), size=10, width=2)
    save_jpg(np.array(answer), out / "ground_truth.jpg")

    track = detections[(detections["video"] == VIDEO_1) & (detections["track"] == OVERVIEW_TRACK)].sort_values("frame")
    chosen = track.iloc[np.linspace(0, len(track) - 1, 5).round().astype(int)]
    images = frames_of(VIDEO_1, chosen["frame"])
    tiles = [cv2.resize(rgb(cut(images[b.frame], b.x, b.y, b.w, b.h, 0.25)), (70, 70), interpolation=cv2.INTER_AREA) for b in chosen.itertuples()]
    strip = Image.new("RGB", (360, 92), "white")
    pen = ImageDraw.Draw(strip)
    for k, (tile, b) in enumerate(zip(tiles, chosen.itertuples())):
        strip.paste(Image.fromarray(tile), (k * 72 + 1, 0))
        pen.text((k * 72 + 3, 73), f"beeld {b.frame + 1}", fill=(82, 81, 78), font=font(11))
    save_jpg(np.array(strip), out / "track.jpg")

    table = rows("fotos_en_kostuum")
    werner = table[table["persoon"] == "Werner"]
    picks = (werner[werner["bestand"].str.contains("/personal/")].iloc[0], werner[werner["bestand"].str.contains("/inCharacter/")].iloc[6])
    sheet = Image.new("RGB", (360, 200), "white")
    pen = ImageDraw.Draw(sheet)
    for k, (r, label) in enumerate(zip(picks, ("foto (out-of-character)", "still (in-character)"))):
        face = rgb(cut(cv2.imread(str(PICTURES / r["bestand"])), r["x"], r["y"], r["w"], r["h"]))
        sheet.paste(Image.fromarray(cv2.resize(face, (176, 176), interpolation=cv2.INTER_AREA)), (k * 184, 0))
        pen.text((k * 184 + 2, 180), label, fill=(82, 81, 78), font=font(12))
    save_jpg(np.array(sheet), out / "foto_en_still.jpg")

    b = data["example_box"]
    vector = unit(np.load(vector_path("Facenet", 0.0))[b:b + 1])[0]
    fig, ax = plt.subplots(figsize=(3.6, 0.8), facecolor="white")
    limit = float(np.abs(vector).max())
    ax.imshow(vector[None, :], cmap="RdBu_r", vmin=-limit, vmax=limit, aspect="auto", interpolation="nearest")
    bare(ax)
    fig.subplots_adjust(left=0.005, right=0.995, top=0.98, bottom=0.04)
    fig.savefig(out / "vector.png", dpi=100)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(3.6, 1.05), facecolor="white")
    ax.add_patch(Rectangle((0, 0.3), 0.8, 0.28, facecolor=BLUE, edgecolor="none"))
    ax.add_patch(Rectangle((0.8, 0.3), 0.8, 0.28, facecolor="#c9c8c2", edgecolor="none"))
    ax.text(0.4, 0.44, "krijgt een naam", ha="center", va="center", fontsize=9.5, fontweight="bold", color="white")
    ax.text(1.2, 0.44, "iemand anders", ha="center", va="center", fontsize=9.5, fontweight="bold", color=INK)
    ax.plot([0.8, 0.8], [0.18, 0.72], color=INK, linewidth=1.8)
    ax.text(0.8, 0.80, "drempel 0,80", ha="center", va="bottom", fontsize=9.5, fontweight="bold", color=INK)
    ax.text(0, 0.1, "0 (lijkt erg op elkaar)", ha="left", va="center", fontsize=8.5, color=MUTED)
    ax.text(1.6, 0.1, "groot (lijkt niet)", ha="right", va="center", fontsize=8.5, color=MUTED)
    ax.set_xlim(-0.01, 1.61)
    ax.set_ylim(0, 1.05)
    ax.axis("off")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    fig.savefig(out / "drempel.png", dpi=100)
    plt.close(fig)


def main() -> None:
    detections = load_detections()
    truth = pd.read_csv(GROUND_TRUTH)
    example = detections.index[(detections["video"] == VIDEO_1) & (detections["frame"] == EXAMPLE_FRAME) & (detections["track"] == EXAMPLE_TRACK)][0]
    data = {"detections": detections, "truth": truth, "hit": hit_matrix(detections, truth), "example_box": int(example)}
    images = frames_of(VIDEO_1, [OVERVIEW_FRAME, EXAMPLE_FRAME])
    how_facenet_works(data, images[EXAMPLE_FRAME])
    two_methods(data)
    explain_score()
    threshold(data)
    before_after_gif(data)
    margin_and_light(data, "Das Boot 3 [kefBHWylmMk] 30m08s-31m04s.mp4", 511)
    per_track_figure(data)
    fair_estimate()
    sliding_window(data)
    glossary(data, images[OVERVIEW_FRAME])
    print("klaar")


if __name__ == "__main__":
    main()
