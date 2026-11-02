"""Controle van de labels: loop elk beeld na en zeg per beeld of de labels kloppen.

Het programma laat achter elkaar zien:
1. elk beeld van elk fragment in movies/ (alle 11.182, ook de beelden zonder kader);
2. elke foto en elke still die de labelaar gelabeld heeft (labels/labels.csv).
Om elk gezicht staat het kader met de keuze van de labelaar uit labels/labels.csv. Bij een beeld uit een fragment is
dat de keuze voor de track van het kader (data/tracks/detections_0.3.csv). Staat een van de vier personen meer dan
één keer in hetzelfde beeld (bijvoorbeeld twee kaders op één hoofd), dan worden die kaders samen één groot kader. Bij
figurant, geen gezicht en weet niet gebeurt dat alleen met kaders die over elkaar liggen.

Toetsen: pijltje links = goed, pijltje rechts = fout, Backspace = een beeld terug.
Elk oordeel komt meteen in labels/controle_labels.csv. Geef je een beeld twee keer een oordeel, dan telt het laatste.
Wie stopt en later weer start, gaat verder bij het eerste beeld zonder oordeel.

De beelden worden altijd op volgorde uit de video gelezen (OpenCV springt soms een beeld verkeerd bij het zoeken naar
een beeldnummer). Verder gaan na een herstart, of ver terug gaan, duurt daarom even.

Gebruik (vanuit de map KTAI):
    .venv/bin/python code/check_labels.py
De controle opent in de browser op http://localhost:8020. Stoppen: Ctrl+C in het terminalvenster.
"""

import csv
import datetime
import json
import threading
import webbrowser
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "labels" / "controle_labels.csv"
PORT = 8020
WIDTH = 1920     # zo breed (in pixels) gaat een beeld hoogstens naar de browser
CACHE = 400      # zoveel beelden blijven klaarliggen, zodat een paar beelden terug meteen kan
AHEAD = 25       # zoveel beelden leest het programma alvast vooruit
NAMES = {"DerAlte": "Der Alte", "FritzGrade": "Fritz Grade", "Johann": "Johann", "Werner": "Werner",
         "other": "figurant", "no_face": "geen gezicht", "unknown": "weet niet"}


PERSONS = ("Der Alte", "Fritz Grade", "Johann", "Werner")


def together(a: list, b: list) -> bool:
    """Worden twee kaders (naam, x, y, w, h) één kader: dezelfde persoon, of dezelfde andere keuze en over elkaar?"""
    if a[0] != b[0]:
        return False
    w = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    h = min(a[2] + a[4], b[2] + b[4]) - max(a[2], b[2])
    return a[0] in PERSONS or (w > 0 and h > 0)


def merge(boxes: list) -> list:
    """Kaders die samen één kader worden (zie together) worden één kader om allemaal heen."""
    boxes = [list(b) for b in boxes]
    i = 0
    while i < len(boxes):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if together(a, b):
                x0, y0 = min(a[1], b[1]), min(a[2], b[2])
                x1, y1 = max(a[1] + a[3], b[1] + b[3]), max(a[2] + a[4], b[2] + b[4])
                boxes[i] = [a[0], x0, y0, x1 - x0, y1 - y0]
                del boxes[j]
                i = -1                                   # opnieuw beginnen: het grote kader kan weer andere raken
                break
        i += 1
    return boxes


def items() -> list:
    """Alles wat nagelopen wordt, op volgorde: elk beeld van elk fragment, daarna de foto's en stills."""
    labels = pd.read_csv(REPO / "labels" / "labels.csv")
    choice = labels.set_index("face")["label"]
    detections = pd.read_csv(REPO / "data" / "tracks" / "detections_0.3.csv")
    frames = pd.read_csv(REPO / "data" / "tracks" / "frames.csv")
    boxes = {}
    for b in detections.itertuples():
        name = NAMES.get(choice.get(f"{b.video}#track{b.track}"), "geen label")
        boxes.setdefault((b.video, int(b.frame)), []).append((name, b.x, b.y, b.w, b.h))
    for b in labels[labels["how"] == "getekend"].itertuples():      # gezichten die de labelaar zelf tekende
        boxes.setdefault((b.source, int(b.frame)), []).append((NAMES.get(b.label, b.label), b.x, b.y, b.w, b.h))
    result = []
    for video, f in frames.groupby("video", sort=True):
        capture = cv2.VideoCapture(str(REPO / "movies" / video))
        w, h = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        capture.release()
        for frame in sorted(f["frame"]):
            result.append({"key": f"{video}#beeld{frame}", "video": video, "frame": int(frame),
                           "title": f"{video.split(' [')[0]}, beeld {frame + 1} van {len(f)}", "w": w, "h": h,
                           "boxes": merge(boxes.get((video, int(frame)), []))})
    stills = pd.read_csv(REPO / "data" / "stills_index.csv").set_index("still")["bestand"]
    rest = labels[~labels["item"].str.startswith("track:") & (labels["how"] != "getekend")]
    kinds = rest["item"].drop_duplicates().str.split(":").str[0]
    number = {"photo": 0, "still": 0}
    for item, g in rest.groupby("item", sort=False):
        kind, source = item.split(":", 1)
        number[kind] += 1
        path = REPO / (source if kind == "photo" else stills[source])
        h, w = cv2.imread(str(path)).shape[:2]
        result.append({"key": item, "path": str(path), "w": w, "h": h,
                       "title": f"{'foto' if kind == 'photo' else 'still'} {number[kind]} van {(kinds == kind).sum()}",
                       "boxes": merge([(NAMES.get(b.label, b.label), b.x, b.y, b.w, b.h) for b in g.itertuples()])})
    return result


def jpg(image) -> bytes:
    if image.shape[1] > WIDTH:
        image = cv2.resize(image, (WIDTH, round(image.shape[0] * WIDTH / image.shape[1])), interpolation=cv2.INTER_AREA)
    return cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()


class Images:
    """Geeft het plaatje van elk item. Beelden uit een video worden op volgorde gelezen; de laatste CACHE plaatjes
    blijven klaarliggen."""

    def __init__(self, todo: list):
        self.todo, self.lock, self.cache = todo, threading.Lock(), OrderedDict()
        self.video, self.capture, self.next = None, None, 0
        self.want, self.wake = 0, threading.Event()
        threading.Thread(target=self.read_ahead, daemon=True).start()

    def get(self, i: int) -> bytes:
        item = self.todo[i]
        with self.lock:
            if i not in self.cache:
                if "path" in item:
                    self.keep(i, cv2.imread(item["path"]))
                else:
                    self.read_until(i)
            self.cache.move_to_end(i)
            return self.cache[i]

    def read_until(self, i: int) -> None:
        video, frame = self.todo[i]["video"], self.todo[i]["frame"]
        if video != self.video or frame < self.next:
            if self.capture is not None:
                self.capture.release()
            self.video, self.capture, self.next = video, cv2.VideoCapture(str(REPO / "movies" / video)), 0
        while self.next <= frame:
            ok, image = self.capture.read()
            if not ok:
                raise RuntimeError(f"{video}: beeld {self.next} kon niet gelezen worden")
            if self.next > frame - CACHE:
                self.keep(i - (frame - self.next), image)       # zelfde video: item i hoort bij beeld frame
            self.next += 1

    def keep(self, i: int, image) -> None:
        self.cache[i] = jpg(image)
        while len(self.cache) > CACHE:
            self.cache.popitem(last=False)

    def read_ahead(self) -> None:
        while True:
            self.wake.wait()
            self.wake.clear()
            try:
                for i in range(self.want, min(self.want + AHEAD, len(self.todo))):
                    self.get(i)
            except RuntimeError as error:                     # de browser krijgt de fout bij het beeld zelf
                print(error)

    def show(self, i: int) -> bytes:
        self.want = i + 1
        self.wake.set()
        return self.get(i)


def judged() -> dict:
    """Het laatste oordeel per item uit labels/controle_labels.csv."""
    if not OUT.exists():
        return {}
    with open(OUT, newline="", encoding="utf-8") as f:
        return {row["item"]: row["oordeel"] for row in csv.DictReader(f)}


def save(item: str, verdict: str) -> None:
    new = not OUT.exists()
    with open(OUT, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        if new:
            writer.writerow(["item", "oordeel", "tijd"])
        writer.writerow([item, verdict, datetime.datetime.now().isoformat(timespec="seconds")])


PAGE = """<!doctype html>
<html lang="nl"><head><meta charset="utf-8"><title>Controle labels</title>
<style>
  html, body { margin: 0; height: 100%; overflow: hidden; background: #111; color: #eee; font: 15px system-ui, sans-serif; }
  #bar { height: 44px; display: flex; align-items: center; gap: 24px; padding: 0 16px; box-sizing: border-box; }
  #title { font-weight: 600; }
  #before { color: #ffd11a; }
  #hint { margin-left: auto; color: #aaa; }
  #stage { position: relative; margin: 0 auto; }
  #stage.loading { opacity: 0.3; }
  #stage img { display: block; width: 100%; height: 100%; }
  .box { position: absolute; border: 3px solid; box-sizing: border-box; }
  .box span { position: absolute; left: -3px; bottom: 100%; padding: 1px 6px; font-weight: 600; white-space: nowrap; color: #111; }
  .box.top span { bottom: auto; top: 0; }
</style></head><body>
<div id="bar"><span id="title">laden…</span><span id="count"></span><span id="before"></span>
<span id="hint">← goed &nbsp;&nbsp; → fout &nbsp;&nbsp; Backspace terug</span></div>
<div id="stage" class="loading"><img id="img" alt=""></div>
<script>
const COLOURS = { "Der Alte": "#ff4d4d", "Fritz Grade": "#4da6ff", "Johann": "#ffd11a", "Werner": "#33cc66",
                  "figurant": "#bbbbbb", "geen gezicht": "#ff66ff", "weet niet": "#ff9933" };
const $ = id => document.getElementById(id);
let items = [], done = {}, i = 0, ready = false;

function fit() {
  if (i >= items.length) return;
  const t = items[i], s = Math.min(innerWidth / t.w, (innerHeight - 44) / t.h);
  $("stage").style.width = t.w * s + "px";
  $("stage").style.height = t.h * s + "px";
}

function count() {
  const v = Object.values(done);
  $("count").textContent = `gedaan ${v.length} van ${items.length}, fout ${v.filter(o => o === "fout").length}`;
}

function show() {
  ready = false;
  count();
  document.querySelectorAll(".box").forEach(b => b.remove());
  if (i >= items.length) {
    $("title").textContent = "Klaar: alles is nagelopen (Backspace = terug)";
    $("stage").style.display = "none";
    $("before").textContent = "";
    return;
  }
  const t = items[i];
  $("stage").style.display = "";
  $("stage").className = "loading";
  $("title").textContent = t.title + " (laden…)";
  $("before").textContent = done[t.key] ? "eerder: " + done[t.key] : "";
  fit();
  $("img").onload = () => {
    for (const [name, x, y, w, h] of t.boxes) {
      const b = document.createElement("div"), c = COLOURS[name] || "#ffffff";
      b.className = "box" + (y / t.h < 0.04 ? " top" : "");
      Object.assign(b.style, { left: 100 * x / t.w + "%", top: 100 * y / t.h + "%",
                               width: 100 * w / t.w + "%", height: 100 * h / t.h + "%", borderColor: c });
      const s = document.createElement("span");
      s.textContent = name;
      s.style.background = c;
      b.appendChild(s);
      $("stage").appendChild(b);
    }
    $("stage").className = "";
    $("title").textContent = t.title;
    ready = true;
  };
  $("img").onerror = () => { $("title").textContent = t.title + ": het beeld kon niet geladen worden"; };
  $("img").src = "/image/" + i;
}

addEventListener("keydown", e => {
  if (e.key === "Backspace") {
    e.preventDefault();
    if (i > 0) { i--; show(); }
    return;
  }
  if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
  e.preventDefault();
  if (e.repeat || !ready) return;
  const t = items[i], verdict = e.key === "ArrowLeft" ? "goed" : "fout";
  fetch("/oordeel", { method: "POST", body: JSON.stringify({ item: t.key, oordeel: verdict }) })
    .then(r => { if (!r.ok) throw new Error(); })
    .catch(() => alert("Het oordeel over " + t.title + " is NIET opgeslagen. Draait het programma nog?"));
  done[t.key] = verdict;
  i++;
  show();
});
addEventListener("resize", fit);

fetch("/items").then(r => r.json()).then(d => {
  items = d.items;
  done = d.done;
  i = items.findIndex(t => !(t.key in done));
  if (i < 0) i = items.length;
  show();
});
</script></body></html>
"""


def main() -> None:
    todo = items()
    images = Images(todo)
    listing = json.dumps([{k: t[k] for k in ("key", "title", "w", "h", "boxes")} for t in todo],
                         default=int).encode()
    write = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def send(self, body: bytes, kind: str, status: int = 200) -> None:
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path == "/":
                self.send(PAGE.encode(), "text/html; charset=utf-8")
            elif self.path == "/items":
                body = b'{"items": ' + listing + b', "done": ' + json.dumps(judged()).encode() + b"}"
                self.send(body, "application/json")
            elif self.path.startswith("/image/") and self.path[7:].isdigit() and int(self.path[7:]) < len(todo):
                self.send(images.show(int(self.path[7:])), "image/jpeg")
            else:
                self.send(b"niet gevonden", "text/plain", 404)

        def do_POST(self) -> None:
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if self.path != "/oordeel" or data.get("oordeel") not in ("goed", "fout"):
                return self.send(b"onbekend", "text/plain", 400)
            with write:
                save(str(data["item"]), data["oordeel"])
            self.send(b"ok", "text/plain")

        def log_message(self, *args) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Controle van de labels: {len(todo)} beelden, foto's en stills. Open http://localhost:{PORT}")
    print("Stoppen: Ctrl+C")
    webbrowser.open(f"http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
