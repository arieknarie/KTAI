r"""Alle plaatjes in labelen/README.md, behalve de schermafbeeldingen van de programma's.

Maakt in deze map (de nummers zijn de stappen in de README):
    stap0_drempel.jpg                 hetzelfde beeld met de kaders bij detectiescore 0,5 en bij detectiescore 0,3
    stap0_beeldwissel.jpg             twee opeenvolgende beelden rond een beeldwissel, met de gemeten gelijkenis
    stap0_track.jpg                   zes beelden uit één track
    stap0_controle_wissel.jpg         24 uitsneden van track 437 (nummer van vóór het knippen), een track die van het
                                      ene gezicht naar een ander gezicht verspringt
    stap0_controle_geen_gezicht.jpg   24 uitsneden van track 84, een track die nooit op een gezicht staat
    overzicht.jpg                     één beeld door het hele proces, van het filmpje tot de ground truth
    stap2_fout_per_fragment.png       welk deel van de beelden per fragment fout was na stap 1
    stap3_voor_na.jpg                 drie beelden voor en na het verbeteren
    uitkomst_tijdlijn.png             wanneer elke persoon in beeld is, voor en na het nakijken en verbeteren
De getallen die de README gebruikt, schrijft het programma op het scherm.

Gebruik (vanuit de map labelen). Dit programma heeft naast de pakketten uit requirements.txt ook matplotlib nodig
(pip install matplotlib==3.11.2):
    Mac:     .venv/bin/python fotos/maak_fotos.py
    Windows: .venv\Scripts\python fotos\maak_fotos.py
"""

import sys
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.frozen import check_frozen
from gedeeld.items import corrected, items, judged
from gedeeld.paden import DETECTIONS, FRAMES, LABELS, MOVIES, TRACK_LIST, TRACKS

DOCS = Path(__file__).resolve().parent

GREEN, GREY, WHITE, BLACK = (0, 170, 0), (170, 170, 170), (255, 255, 255), (0, 0, 0)
FONT = cv2.FONT_HERSHEY_SIMPLEX


def read_frame(video: str, frame_index: int) -> np.ndarray:
    """Frame nummer `frame_index`, gevonden door de video vanaf het begin op volgorde te lezen,
    net als in track_faces.py. Direct naar een frame springen (CAP_PROP_POS_FRAMES) geeft in
    een van de eerdere fragmenten vanaf frame 4523 het frame ervoor."""
    capture = cv2.VideoCapture(str(MOVIES / video))
    for _ in range(frame_index + 1):
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError(f"frame {frame_index} van {video} niet gelezen")
    capture.release()
    return frame


def save_jpg(path: Path, image: np.ndarray, quality: int) -> None:
    """Een plaatje opslaan, ook als het pad letters als é bevat (cv2.imwrite kan dat op Windows niet)."""
    ok, data = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise SystemExit(f"{path}: plaatje kon niet gemaakt worden")
    path.write_bytes(data.tobytes())


def label(image: np.ndarray, text: str, x: int, y: int, color, scale: float = 0.45) -> None:
    """Tekst met een witte achtergrond, zodat de tekst op elk beeld leesbaar is."""
    (w, h), _ = cv2.getTextSize(text, FONT, scale, 1)
    cv2.rectangle(image, (x, y - h - 4), (x + w + 4, y + 2), WHITE, -1)
    cv2.putText(image, text, (x + 2, y - 2), FONT, scale, color, 1, cv2.LINE_AA)


def caption(image: np.ndarray, text: str) -> np.ndarray:
    """Witte balk met tekst boven een beeld."""
    bar = np.full((28, image.shape[1], 3), 255, np.uint8)
    cv2.putText(bar, text, (6, 19), FONT, 0.55, BLACK, 1, cv2.LINE_AA)
    return np.vstack([bar, image])


def threshold_image() -> None:
    """Het frame waarin het verschil tussen score 0,5 en score 0,3 het duidelijkst te zien is: zoveel mogelijk
    gezichten erbij door de lagere grens, terwijl er bij 0,5 ook al minstens twee gezichten zijn."""
    detections = pd.read_csv(TRACKS / "detections_0.3.csv")
    # alleen de gewone kaders (vanaf 0,3); de verlengingen (0,2 tot 0,3) horen niet bij deze vergelijking
    regular = detections[~detections["verlengd"]]
    counts = regular.groupby(["video", "frame"])["score"].agg(n03="size", n05=lambda s: int((s >= 0.5).sum()))
    counts = counts[counts["n05"] >= 2]
    counts["extra"] = counts["n03"] - counts["n05"]
    video, frame_index = counts.sort_values(["extra", "n05"], ascending=False).index[0]
    faces = regular[(regular["video"] == video) & (regular["frame"] == frame_index)]
    frame = read_frame(video, frame_index)
    scale = 860 / frame.shape[1]   # elk paneel 860 pixels breed, ook bij een video in hoge resolutie
    frame = cv2.resize(frame, (860, round(frame.shape[0] * scale)), interpolation=cv2.INTER_AREA)
    panels = []
    for threshold in (0.5, 0.3):
        panel = frame.copy()
        shown = faces[faces["score"] >= threshold]
        for face in shown.itertuples():
            x, y, w, h = (round(v * scale) for v in (face.x, face.y, face.w, face.h))
            cv2.rectangle(panel, (x, y), (x + w, y + h), GREEN, 2)
            label(panel, f"{face.score:.2f}", x, y, GREEN)
        panels.append(caption(panel, f"score minstens {str(threshold).replace('.', ',')}: {len(shown)} kaders"))
    gap = np.full((panels[0].shape[0], 10, 3), 255, np.uint8)
    save_jpg(DOCS / "stap0_drempel.jpg", np.hstack([panels[0], gap, panels[1]]), 90)


def track_image() -> None:
    """Zes frames uit de langste duidelijke track."""
    detections = pd.read_csv(TRACKS / "detections_0.3.csv")
    tracks = pd.read_csv(TRACKS / "tracks_0.3.csv")
    # de langste track die in elk frame duidelijk gedetecteerd is (score minstens 0,5), zodat het
    # voorbeeld goed te volgen is
    clear = detections.groupby("track")["score"].min()
    candidates = tracks[tracks["track"].map(clear).ge(0.5)]
    longest = candidates.sort_values(["faces", "track"], ascending=[False, True]).iloc[0]
    video = longest["video"]
    track_faces = detections[detections["track"] == longest["track"]]
    chosen = track_faces.iloc[np.linspace(0, len(track_faces) - 1, 6).round().astype(int)]
    panels = []
    for face in chosen.itertuples():
        frame = read_frame(video, face.frame)
        # andere tracks in hetzelfde frame grijs, de gekozen track groen
        others = detections[(detections["video"] == video) & (detections["frame"] == face.frame)
                            & (detections["track"] != face.track)]
        for other in others.itertuples():
            cv2.rectangle(frame, (other.x, other.y), (other.x + other.w, other.y + other.h), GREY, max(3, frame.shape[1] // 280))
        cv2.rectangle(frame, (face.x, face.y), (face.x + face.w, face.y + face.h), GREEN, max(4, frame.shape[1] // 200))
        label(frame, f"track {face.track}", face.x, face.y, GREEN, scale=max(0.9, frame.shape[1] / 900))
        small = cv2.resize(frame, (400, round(frame.shape[0] * 400 / frame.shape[1])), interpolation=cv2.INTER_AREA)
        minutes, seconds = divmod(face.time_s, 60)
        panels.append(caption(small, f"beeld {face.frame}  ({int(minutes)}:{seconds:04.1f})".replace(".", ",")))
    rows = [np.hstack(panels[i:i + 3]) for i in (0, 3)]
    save_jpg(DOCS / "stap0_track.jpg", np.vstack(rows), 90)
    print(f"track {longest['track']}: {longest['faces']} frames, {longest['start_s']} s tot {longest['end_s']} s")


def cut_image() -> None:
    """Twee opeenvolgende frames rond een gemarkeerde beeldwissel, met de gemeten gelijkenis: een beeldwissel
    waarbij de kleuren nauwelijks veranderen (gelijkenis minstens 0,9) maar de structuur het sterkst, zodat te
    zien is dat ook de structuur meetelt."""
    frames = pd.read_csv(TRACKS / "frames.csv")
    cuts = frames[frames["cut"]]
    same_colour = cuts[cuts["colour_similarity"] >= 0.9]
    row = (same_colour.sort_values(["structure_similarity", "frame"]) if len(same_colour)
           else cuts.sort_values(["colour_similarity", "frame"], ascending=[False, True])).iloc[0]
    video, frame_index = row["video"], int(row["frame"])
    panels = []
    for index, title in ((frame_index - 1, f"beeld {frame_index - 1}"),
                         (frame_index, f"beeld {frame_index}: kleuren {row['colour_similarity']:.2f}, ".replace(".", ",") + 
                                       f"licht-donkerpatroon {row['structure_similarity']:.2f}: beeldwissel".replace(".", ","))):
        image = read_frame(video, index)
        small = cv2.resize(image, (560, round(image.shape[0] * 560 / image.shape[1])), interpolation=cv2.INTER_AREA)
        panels.append(caption(small, title))
    gap = np.full((panels[0].shape[0], 10, 3), 255, np.uint8)
    save_jpg(DOCS / "stap0_beeldwissel.jpg", np.hstack([panels[0], gap, panels[1]]), 90)


def strip_image(track: int, filename: str) -> None:
    """24 uitsneden van één track, gelijk verdeeld van begin tot eind, met wat omgeving en lichter
    gemaakt, zoals bij de controle van de tracks (zie labelen/README.md)."""
    detections = pd.read_csv(TRACKS / "detections_0.3.csv")
    # de hele oorspronkelijke track, ook als die na de controle geknipt is (zie stap_0_voorbereiding/1_track_faces.py)
    faces = detections[detections["track_ongeknipt"] == track].sort_values("frame").reset_index(drop=True)
    chosen = faces.iloc[np.unique(np.linspace(0, len(faces) - 1, min(24, len(faces))).round().astype(int))]
    wanted = {face.frame: face for face in chosen.itertuples()}
    capture = cv2.VideoCapture(str(MOVIES / faces["video"].iloc[0]))
    tiles = []
    for index in range(max(wanted) + 1):  # op volgorde lezen, zie read_frame
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError(f"frame {index} niet gelezen")
        if index not in wanted:
            continue
        face = wanted[index]
        margin = int(0.6 * max(face.w, face.h))
        top, left = max(0, face.y - margin), max(0, face.x - margin)
        crop = frame[top:face.y + face.h + margin, left:face.x + face.w + margin].astype(np.float32)
        crop = np.clip(crop * (220 / max(20.0, float(np.percentile(crop, 97)))), 0, 255).astype(np.uint8)  # lichter
        thick = max(1, crop.shape[1] // 85)   # na het verkleinen tot 170 pixels nog goed te zien, ook bij 4K
        cv2.rectangle(crop, (face.x - left, face.y - top), (face.x - left + face.w, face.y - top + face.h), (0, 255, 0), thick)
        crop = cv2.resize(crop, (170, 170), interpolation=cv2.INTER_CUBIC)
        label(crop, f"frame {index}", 2, 16, BLACK, scale=0.45)
        tiles.append(crop)
    capture.release()
    while len(tiles) % 8:
        tiles.append(np.full_like(tiles[0], 255))
    rows = [np.hstack(tiles[i:i + 8]) for i in range(0, len(tiles), 8)]
    save_jpg(DOCS / filename, np.vstack(rows), 88)


COLOURS = {"Der Alte": "#ff4d4d", "Fritz Grade": "#4da6ff", "Johann": "#ffd11a", "Werner": "#33cc66"}   # zoals in stap 2 en 3
TEXT, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3de"
KEPT, ADDED, REMOVED = "#8a8983", "#eb6834", "#2a78d6"   # de tijdlijn: bleef hetzelfde, erbij gekomen, weggehaald
OVERVIEW = ("Das Boot 1 [Ek2omNPSOYc] 28m10s-28m55s.mp4", 22)
EXAMPLES = [("Das Boot 5 [kefBHWylmMk] 32m05s-33m06s.mp4", 853, "kader zonder gezicht weggehaald"),
            ("Das Boot 8b [dasgespenst] 0m44s-1m32s.mp4", 923, "kader bij een gemist gezicht gezet"),
            ("Das Boot 1 [Ek2omNPSOYc] 28m10s-28m55s.mp4", 1119, "kader erbij gezet en een kader verplaatst")]


def number(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def rgb(video: str, frame_index: int) -> np.ndarray:
    return cv2.cvtColor(read_frame(video, frame_index), cv2.COLOR_BGR2RGB)


def show(ax, image: np.ndarray, boxes: list, size: float = 8.5, line: float = 2.0) -> None:
    """Een beeld met de kaders van de vier personen, met de naam erboven (zoals in stap 2 en 3)."""
    h, w = image.shape[:2]
    small = cv2.resize(image, (1280, round(1280 * h / w)), interpolation=cv2.INTER_AREA)
    ax.imshow(small, extent=(0, w, h, 0))
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    for name, x, y, bw, bh in boxes:
        ax.add_patch(Rectangle((x, y), bw, bh, fill=False, edgecolor=COLOURS[name], linewidth=line))
        top = y / h < 0.06
        ax.text(x, y if not top else y + 0.05 * h, name, fontsize=size, fontweight="bold", color="#111111",
                va="bottom", ha="left", bbox={"facecolor": COLOURS[name], "edgecolor": "none", "pad": 1.5})


def overview(todo: dict, verdicts: dict, fixes: dict) -> None:
    """Eén beeld door het hele proces: wat er in elke stap met dat beeld gebeurt, en hoeveel het er in totaal zijn."""
    video, frame_index = OVERVIEW
    key = f"{video}#beeld{frame_index}"
    image = rgb(video, frame_index)
    detections = pd.read_csv(DETECTIONS)
    labels = pd.read_csv(LABELS)
    choice = labels.set_index("face")["label"]
    here = detections[(detections["video"] == video) & (detections["frame"] == frame_index)]
    tracks = labels[labels["item"].str.startswith("track:")]
    words = {"DerAlte": "Der Alte", "FritzGrade": "Fritz Grade", "Johann": "Johann", "Werner": "Werner",
             "other": "figurant", "no_face": "geen gezicht", "unknown": "weet niet"}

    fig = plt.figure(figsize=(15.8, 8.0), facecolor="white")
    grid = fig.add_gridspec(2, 3, left=0.012, right=0.988, top=0.945, bottom=0.075, wspace=0.05, hspace=0.3)
    axes = [fig.add_subplot(grid[r, c]) for r in range(2) for c in range(3)]

    def note(ax, title: str, text: str) -> None:
        ax.set_title(title, loc="left", fontsize=12.5, fontweight="bold", color=TEXT, pad=6)
        ax.text(0, -0.03, text, transform=ax.transAxes, fontsize=10, color=MUTED, va="top", linespacing=1.35)

    show(axes[0], image, [])
    note(axes[0], "Het filmpje", f"8 filmpjes (12 bestanden) met samen {number(len(pd.read_csv(FRAMES)))} beelden.\nDit is er één van.")

    show(axes[1], image, [])
    for b in here.itertuples():
        axes[1].add_patch(Rectangle((b.x, b.y), b.w, b.h, fill=False, edgecolor="#39e639", linewidth=2))
    note(axes[1], "Stap 0: gezichten vinden en volgen",
         f"De computer vond {number(len(detections))} kaders\nen plakte die aan elkaar tot {number(tracks.shape[0])} tracks.")

    show(axes[2], image, [])
    for b in here.itertuples():
        word = words[choice[f"{b.video}#track{b.track}"]]
        persons = word in COLOURS
        axes[2].add_patch(Rectangle((b.x, b.y), b.w, b.h, fill=False, edgecolor=COLOURS.get(word, "#d8d8d8"),
                                    linewidth=2, linestyle="-" if persons else (0, (3, 2))))
        right_edge = b.x > 0.85 * image.shape[1]
        axes[2].text(b.x + b.w if right_edge else b.x, b.y, word, fontsize=8.5, fontweight="bold", color="#111111", va="bottom",
                     ha="right" if right_edge else "left", bbox={"facecolor": COLOURS.get(word, "#d8d8d8"), "edgecolor": "none", "pad": 1.5})
    note(axes[2], "Stap 1: per track labelen", f"Elke track krijgt één keuze: {number(len(tracks))} keuzes,\nplus {len(labels) - len(tracks)} gezichten op foto's en stills.")

    show(axes[3], image, todo[key]["boxes"])
    axes[3].text(0.5, 0.965, "Let op: Der Alte stond in het vorige beeld wel, nu niet", transform=axes[3].transAxes, ha="center", va="top",
                 fontsize=10.5, fontweight="bold", color="white", bbox={"facecolor": "#d1495b", "edgecolor": "none", "pad": 4})
    count = Counter(verdicts.values())
    note(axes[3], "Stap 2: per beeld nakijken", f"De nakijker vond dit beeld fout.\nIn totaal {number(count['goed'])} keer goed en {number(count['fout'])} keer fout.")

    show(axes[4], image, fixes[key])
    note(axes[4], "Stap 3: foute beelden verbeteren", f"Het ontbrekende kader staat erbij.\nAlle {number(count['fout'])} foute beelden zijn verbeterd.")

    ax = axes[5]
    ax.axis("off")
    ax.set_title("De uitkomst: de ground truth", loc="left", fontsize=12.5, fontweight="bold", color=TEXT, pad=6)
    rows = [[str(frame_index), name, str(x), str(y), str(w), str(h)] for name, x, y, w, h in sorted(fixes[key])]
    table = ax.table(cellText=rows, colLabels=["beeld", "persoon", "x", "y", "w", "h"], cellLoc="left", bbox=(0, 0.5, 1, 0.5),
                     colWidths=[0.14, 0.3, 0.14, 0.14, 0.14, 0.14])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    for (row, _), cell in table.get_celld().items():
        cell.set_edgecolor(GRID)
        cell.set_linewidth(1)
        if row == 0:
            cell.set_text_props(fontweight="bold", color=TEXT)
            cell.set_facecolor("#f4f3ef")
    ax.text(0, 0.4, "Voor elk beeld staat vast wie er te zien is en waar.\nMet deze lijst kijken we later na of\n"
            "FaceNet de juiste persoon aanwijst.", transform=ax.transAxes, fontsize=11, color=TEXT, va="top", linespacing=1.5)
    total = sum(len(fixes[k] if verdicts[k] == "fout" else t["boxes"]) for k, t in todo.items() if "video" in t)
    ax.text(0, -0.03, f"{number(total)} rijen: per beeld één rij\nvoor elke persoon in dat beeld.", transform=ax.transAxes, fontsize=10, color=MUTED, va="top", linespacing=1.35)
    axes[4].apply_aspect()
    position = axes[4].get_position()
    ax.set_position([ax.get_position().x0, position.y0, ax.get_position().width, position.height])

    fig.savefig(DOCS / "overzicht.jpg", dpi=115, pil_kwargs={"quality": 90})
    plt.close(fig)


def wrong_per_fragment(todo: dict, verdicts: dict) -> None:
    """Welk deel van de beelden per fragment fout was na stap 1."""
    counts = defaultdict(Counter)
    for key, t in todo.items():
        if "video" in t:
            counts["Video " + t["video"].split(" [")[0].split()[-1].rstrip("abc")][verdicts[key]] += 1
    names = sorted(counts, key=lambda g: int(g.split()[-1]))
    wrong = np.array([counts[g]["fout"] for g in names])
    total = np.array([counts[g]["fout"] + counts[g]["goed"] for g in names])
    share = 100 * wrong / total
    fig, ax = plt.subplots(figsize=(9.2, 3.7), facecolor="white")
    ax.barh(names, share, height=0.55, color="#2a78d6")
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    for i, g in enumerate(names):
        ax.text(share[i] + 1, i, f"{share[i]:.1f}%".replace(".", ",") + f"   ({number(int(wrong[i]))} van {number(int(total[i]))} beelden)",
                va="center", fontsize=9.5, color=TEXT)
    ax.set_xlabel("deel van de beelden dat bij het nakijken fout bleek (%)", fontsize=9.5, color=MUTED)
    ax.tick_params(axis="both", length=0, labelsize=9.5, colors=MUTED)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for name, spine in ax.spines.items():
        spine.set_visible(False)
    ax.set_title("Hoeveel beelden fout waren na stap 1, per filmpje", loc="left", fontsize=12, fontweight="bold", color=TEXT, pad=10)
    fig.tight_layout()
    fig.savefig(DOCS / "stap2_fout_per_fragment.png", dpi=140)
    plt.close(fig)


def before_after(todo: dict, fixes: dict) -> None:
    """Drie beelden naast elkaar voor en na stap 3."""
    fig = plt.figure(figsize=(12.2, 3.72 * len(EXAMPLES) + 0.2), facecolor="white")
    grid = fig.add_gridspec(len(EXAMPLES), 2, left=0.012, right=0.988, top=0.955, bottom=0.012, wspace=0.03, hspace=0.2)
    for row, (video, frame_index, text) in enumerate(EXAMPLES):
        key = f"{video}#beeld{frame_index}"
        image = rgb(video, frame_index)
        left, right = fig.add_subplot(grid[row, 0]), fig.add_subplot(grid[row, 1])
        show(left, image, todo[key]["boxes"], size=10, line=2.4)
        show(right, image, fixes[key], size=10, line=2.4)
        where = f"{video.split(' [')[0]}, beeld {frame_index + 1}"
        left.set_title(f"Voor stap 3 ({where})", loc="left", fontsize=11, fontweight="bold", color=TEXT, pad=5)
        right.set_title(f"Na stap 3: {text}", loc="left", fontsize=11, fontweight="bold", color=TEXT, pad=5)
    fig.savefig(DOCS / "stap3_voor_na.jpg", dpi=125, pil_kwargs={"quality": 90})
    plt.close(fig)


def pieces(times: list, step: float) -> list:
    """Opeenvolgende beelden samen als één stuk: (begin, lengte)."""
    if not times:
        return []
    times = np.sort(np.asarray(times))
    breaks = np.where(np.diff(times) > 1.5 * step)[0]
    starts, ends = np.r_[times[0], times[breaks + 1]], np.r_[times[breaks], times[-1]]
    return [(float(s), float(e - s + step)) for s, e in zip(starts, ends)]


def timeline(todo: dict, verdicts: dict, fixes: dict) -> None:
    """Wanneer elke persoon in beeld is: wat na stap 1 al klopte, en wat stap 2 en 3 erbij deden of weghaalden."""
    frames = pd.read_csv(FRAMES)
    start, offset, step = {}, {}, {}
    for video, f in frames.groupby("video", sort=True):
        group = "Video " + video.split(" [")[0].split()[-1].rstrip("abc")
        step[video] = float(np.median(np.diff(f["time_s"])))
        offset[video] = (group, start.get(group, 0.0))
        start[group] = start.get(group, 0.0) + len(f) * step[video]
    times = frames.set_index(["video", "frame"])["time_s"]
    states = defaultdict(lambda: {"kept": [], "added": [], "removed": []})
    before, after = defaultdict(list), defaultdict(list)
    steps = {}
    for key, t in todo.items():
        if "video" not in t:
            continue
        group, shift = offset[t["video"]]
        steps[group] = step[t["video"]]
        moment = float(times[(t["video"], t["frame"])]) + shift
        old = {b[0] for b in t["boxes"]}
        new = {b[0] for b in (fixes[key] if verdicts[key] == "fout" else t["boxes"])}
        for person in old:
            before[(group, person)].append(moment)
        for person in new:
            after[(group, person)].append(moment)
        for person in old & new:
            states[(group, person)]["kept"].append(moment)
        for person in new - old:
            states[(group, person)]["added"].append(moment)
        for person in old - new:
            states[(group, person)]["removed"].append(moment)

    people = list(COLOURS)
    groups = sorted({g for g, _ in states}, key=lambda g: int(g.split()[-1]))
    count_before = {p: sum(len(pieces(v, steps[g])) for (g, q), v in before.items() if q == p) for p in people}
    count_after = {p: sum(len(pieces(v, steps[g])) for (g, q), v in after.items() if q == p) for p in people}
    frames_before = {p: sum(len(v) for (g, q), v in before.items() if q == p) for p in people}
    frames_after = {p: sum(len(v) for (g, q), v in after.items() if q == p) for p in people}

    fig, axes = plt.subplots(len(groups), 1, figsize=(12.4, 1.32 * len(groups) + 1.0), squeeze=False, facecolor="white")
    for ax, group in zip(axes[:, 0], groups):
        for y, person in enumerate(people):
            for state, colour in (("kept", KEPT), ("added", ADDED), ("removed", REMOVED)):
                ax.broken_barh(pieces(states[(group, person)][state], steps[group]), (y - 0.3, 0.6), color=colour, linewidth=0)
        ax.set_yticks(range(len(people)), people, fontsize=8.5, color=MUTED)
        ax.set_ylim(len(people) - 0.45, -0.55)
        ax.set_xlim(0, start[group])
        ax.set_title(group, loc="left", fontsize=10, fontweight="bold", color=TEXT, pad=3)
        ax.tick_params(axis="both", length=0, labelsize=8.5, colors=MUTED)
        ax.grid(axis="x", color=GRID, linewidth=0.7)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_visible(False)
    axes[-1, 0].set_xlabel("tijd in het filmpje (seconden)", fontsize=9.5, color=MUTED)
    handles = [Rectangle((0, 0), 1, 1, color=c) for c in (KEPT, ADDED, REMOVED)]
    fig.legend(handles, ["klopte al na stap 1", "erbij gekomen door stap 2 en 3", "weggehaald door stap 2 en 3"], loc="upper left", ncol=3,
               fontsize=10, frameon=False, bbox_to_anchor=(0.005, 0.968), labelcolor=TEXT)
    old, new = sum(count_before.values()), sum(count_after.values())
    fig.suptitle(f"Nakijken en verbeteren vulde de gaten: {old} losse stukken werden er {new}", x=0.012, ha="left", y=0.992, fontsize=12.5, fontweight="bold", color=TEXT)
    fig.tight_layout(rect=(0, 0, 1, 0.945))
    fig.savefig(DOCS / "uitkomst_tijdlijn.png", dpi=125)
    plt.close(fig)
    for person in people:
        print(f"{person}: {number(frames_before[person])} -> {number(frames_after[person])} beelden, "
              f"{count_before[person]} -> {count_after[person]} losse stukken")
    print(f"samen {old} -> {new} losse stukken")


def main() -> None:
    check_frozen(DETECTIONS, TRACK_LIST, FRAMES)
    threshold_image()
    cut_image()
    track_image()
    strip_image(437, "stap0_controle_wissel.jpg")
    strip_image(84, "stap0_controle_geen_gezicht.jpg")
    todo = {t["key"]: t for t in items()}
    verdicts, fixes = judged(), corrected()
    overview(todo, verdicts, fixes)
    wrong_per_fragment(todo, verdicts)
    before_after(todo, fixes)
    timeline(todo, verdicts, fixes)
    print(f"plaatjes in {DOCS.name}/")


if __name__ == "__main__":
    main()
