"""Verbeteren van de labels: elk beeld dat bij de controle (code/check_labels.py) fout kreeg, opnieuw goed zetten.

Per fout beeld staat rechts groot het foute beeld, met de kaders van de vier personen. Linksboven staat het laatste
goede beeld ervoor uit hetzelfde fragment (een beeld dat goed kreeg, of een beeld dat hier al verbeterd is). Daaronder
staan vier knoppen, één per persoon; de knop staat aan als die persoon al in het beeld staat.
- Knop aan zetten en dan op een gezicht in het grote beeld klikken: om dat gezicht komt een kader met die naam. Het
  kader is het kader dat de computer daar vond; vond de computer daar niets, dan een kader zo groot als het kader van
  die persoon in het laatste goede beeld.
- Knop uit zetten: het kader van die persoon gaat weg.
- Is het laatste goede beeld een beeld dat hier verbeterd is, dan staan de kaders van dat beeld er precies zo op
  (dezelfde personen op dezelfde plek). Anders: stond een persoon in het laatste goede beeld en ontbreekt die in het
  foute beeld, dan staat zijn kader er al op dezelfde plek (op het kader dat de computer daar vond, als dat er is).
- Enter (of de knop Opslaan): opslaan en naar het volgende foute beeld. Backspace: terug naar het vorige foute beeld.
Elk opgeslagen beeld komt in labels/correcties.csv: per persoon in het beeld één rij met het kader (in pixels van het
originele beeld); een beeld zonder een van de vier krijgt één rij zonder persoon. Bij een tweede keer opslaan telt de
laatste keer. Wie stopt en later weer start, gaat verder bij het eerste foute beeld dat nog niet verbeterd is.

Gebruik (vanuit de map KTAI):
    .venv/bin/python code/fix_labels.py
Het opent in de browser op http://localhost:8030. Stoppen: Ctrl+C in het terminalvenster.
"""

import csv
import datetime
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pandas as pd

from check_labels import REPO, Images, items, judged

OUT = REPO / "labels" / "correcties.csv"
PORT = 8030


def detected(todo: list) -> dict:
    """Per item alle kaders die de computer vond (of die de labelaar zag), los van de keuze: om op te klikken."""
    index = {t["key"]: i for i, t in enumerate(todo)}
    found = {}
    for b in pd.read_csv(REPO / "data" / "tracks" / "detections_0.3.csv").itertuples():
        found.setdefault(index[f"{b.video}#beeld{b.frame}"], []).append([b.x, b.y, b.w, b.h])
    labels = pd.read_csv(REPO / "labels" / "labels.csv")
    for b in labels[~labels["item"].str.startswith("track:")].itertuples():
        if b.item in index:
            found.setdefault(index[b.item], []).append([b.x, b.y, b.w, b.h])
    return found


def corrected() -> dict:
    """De laatste correctie per item: {item: [[persoon, x, y, w, h], ...]}."""
    if not OUT.exists():
        return {}
    rows = {}
    with open(OUT, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            last = rows.setdefault(r["item"], {"tijd": r["tijd"], "boxes": []})
            if r["tijd"] != last["tijd"]:                    # een nieuwere keer opslaan vervangt de oudere
                last["tijd"], last["boxes"] = r["tijd"], []
            if r["persoon"]:
                last["boxes"].append([r["persoon"], int(r["x"]), int(r["y"]), int(r["w"]), int(r["h"])])
    return {item: r["boxes"] for item, r in rows.items()}


def save(item: str, boxes: list) -> None:
    new, now = not OUT.exists(), datetime.datetime.now().isoformat(timespec="seconds")
    with open(OUT, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        if new:
            writer.writerow(["item", "persoon", "x", "y", "w", "h", "tijd"])
        for name, x, y, w, h in boxes or [["", "", "", "", ""]]:
            writer.writerow([item, name, x, y, w, h, now])


PAGE = """<!doctype html>
<html lang="nl"><head><meta charset="utf-8"><title>Labels verbeteren</title>
<style>
  html, body { margin: 0; height: 100%; overflow: hidden; background: #111; color: #eee; font: 15px system-ui, sans-serif; }
  #bar { height: 40px; display: flex; align-items: center; gap: 24px; padding: 0 16px; }
  #bar b { white-space: nowrap; }
  #main { display: flex; gap: 12px; padding: 0 12px; height: calc(100% - 40px); }
  #left { width: 28%; display: flex; flex-direction: column; gap: 10px; }
  #left .note { color: #aaa; }
  .stage { position: relative; }
  .stage img { display: block; width: 100%; height: 100%; }
  .stage.loading { opacity: 0.3; }
  #big { cursor: crosshair; }
  .box { position: absolute; border: 3px solid; box-sizing: border-box; pointer-events: none; }
  .box span { position: absolute; left: -3px; bottom: 100%; padding: 1px 6px; font-weight: 600; white-space: nowrap; color: #111; }
  .box.top span { bottom: auto; top: 0; }
  #buttons { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  button { font: 600 16px system-ui, sans-serif; padding: 12px; border-radius: 6px; border: 3px solid #555; background: #222; color: #eee; cursor: pointer; }
  button.on { color: #111; }
  button.active { outline: 4px solid #fff; }
  #save { grid-column: span 2; background: #2a6; border-color: #2a6; color: #fff; }
</style></head><body>
<div id="bar"><b id="title">laden…</b><span id="count"></span>
<span style="margin-left:auto;color:#aaa">knop aan + klik op gezicht = kader &nbsp; Enter = opslaan &nbsp; Backspace = vorige</span></div>
<div id="main">
  <div id="left">
    <div class="note" id="goodtitle"></div>
    <div class="stage" id="good"><img alt=""></div>
    <div id="buttons"></div>
  </div>
  <div class="stage" id="big"><img alt=""></div>
</div>
<script>
const PERSONS = ["Der Alte", "Fritz Grade", "Johann", "Werner"];
const COLOURS = { "Der Alte": "#ff4d4d", "Fritz Grade": "#4da6ff", "Johann": "#ffd11a", "Werner": "#33cc66" };
const $ = id => document.getElementById(id);
let items, verdict, fixes, found, wrong, n = 0, boxes = [], active = null, good = -1, ready = false;

function draw(stage, t, list) {
  stage.querySelectorAll(".box").forEach(b => b.remove());
  for (const [name, x, y, w, h] of list) {
    const b = document.createElement("div"), s = document.createElement("span");
    b.className = "box" + (y / t.h < 0.04 ? " top" : "");
    Object.assign(b.style, { left: 100 * x / t.w + "%", top: 100 * y / t.h + "%", width: 100 * w / t.w + "%",
                             height: 100 * h / t.h + "%", borderColor: COLOURS[name] });
    s.textContent = name;
    s.style.background = COLOURS[name];
    b.appendChild(s);
    stage.appendChild(b);
  }
}

function size(stage, t, width, height) {
  const s = Math.min(width / t.w, height / t.h);
  stage.style.width = t.w * s + "px";
  stage.style.height = t.h * s + "px";
}

function load(stage, i, list, then) {
  const t = items[i], img = stage.querySelector("img");
  stage.className = "stage loading";
  stage.querySelectorAll(".box").forEach(b => b.remove());
  img.onload = () => { stage.className = "stage"; draw(stage, t, list); then && then(); };
  img.src = "/image/" + i;
}

function buttons() {
  $("buttons").innerHTML = "";
  for (const name of PERSONS) {
    const b = document.createElement("button"), on = boxes.some(x => x[0] === name);
    b.textContent = name;
    b.className = (on ? "on" : "") + (active === name ? " active" : "");
    b.style.borderColor = COLOURS[name];
    if (on || active === name) b.style.background = COLOURS[name];
    b.onclick = () => {
      if (active === name) active = null;
      else if (on) boxes = boxes.filter(x => x[0] !== name);
      else active = name;
      buttons();
      draw($("big"), items[wrong[n]], boxes);
    };
    $("buttons").appendChild(b);
  }
  const s = document.createElement("button");
  s.id = "save";
  s.textContent = "Opslaan en volgende (Enter)";
  s.onclick = save;
  $("buttons").appendChild(s);
}

function lastGood(i) {
  const video = items[i].key.split("#beeld")[0];
  for (let k = i - 1; k >= 0 && items[k].key.startsWith(video + "#beeld") && items[i].key.includes("#beeld"); k--)
    if (verdict[items[k].key] === "goed" || items[k].key in fixes) return k;
  return -1;
}

function overlap(a, b) {
  const w = Math.min(a[0] + a[2], b[0] + b[2]) - Math.max(a[0], b[0]), h = Math.min(a[1] + a[3], b[1] + b[3]) - Math.max(a[1], b[1]);
  return w > 0 && h > 0 ? w * h / (a[2] * a[3] + b[2] * b[3] - w * h) : 0;
}

function carry(i, before) {
  // Wie in het laatste goede beeld stond en hier ontbreekt, komt op dezelfde plek: op het kader dat de computer daar
  // vond, of anders precies waar het in het goede beeld stond.
  for (const [name, ...box] of before) {
    if (boxes.some(b => b[0] === name)) continue;
    const best = (found[i] || []).map(f => [overlap(f, box), f]).sort((a, b) => b[0] - a[0])[0];
    boxes.push([name, ...(best && best[0] > 0.3 ? best[1] : box)]);
  }
}

function show() {
  ready = false;
  $("count").textContent = `fout beeld ${Math.min(n + 1, wrong.length)} van ${wrong.length}, verbeterd ${wrong.filter(i => items[i].key in fixes).length}`;
  if (n >= wrong.length) { $("title").textContent = "Klaar: alle foute beelden zijn verbeterd (Backspace = terug)"; $("main").style.display = "none"; return; }
  $("main").style.display = "";
  const i = wrong[n], t = items[i];
  boxes = JSON.parse(JSON.stringify(fixes[t.key] || t.boxes));
  active = null;
  good = lastGood(i);
  if (!(t.key in fixes) && good >= 0) {
    if (items[good].key in fixes) boxes = JSON.parse(JSON.stringify(fixes[items[good].key]));   // net verbeterd: precies overnemen
    else carry(i, items[good].boxes);
  }
  $("title").textContent = t.title + (t.key in fixes ? " (al verbeterd)" : "");
  const leftW = $("left").clientWidth;
  size($("big"), t, innerWidth - leftW - 36, innerHeight - 52);
  buttons();
  const big = () => load($("big"), i, boxes, () => { ready = true; });
  if (good >= 0) {
    const g = items[good];
    $("goodtitle").textContent = "laatste goede: " + g.title + (g.key in fixes ? " (verbeterd)" : "");
    $("good").style.display = "";
    size($("good"), g, leftW, innerHeight * 0.45);
    load($("good"), good, fixes[g.key] || g.boxes, big);    // eerst het eerdere beeld: de video wordt op volgorde gelezen
  } else {
    $("goodtitle").textContent = "geen goed beeld ervoor";
    $("good").style.display = "none";
    big();
  }
}

$("big").onclick = e => {
  if (!ready || !active) return;
  const t = items[wrong[n]], r = $("big").getBoundingClientRect();
  const x = (e.clientX - r.left) / r.width * t.w, y = (e.clientY - r.top) / r.height * t.h;
  const hits = (found[wrong[n]] || []).filter(([bx, by, bw, bh]) => x >= bx && x <= bx + bw && y >= by && y <= by + bh)
                                       .sort((a, b) => a[2] * a[3] - b[2] * b[3]);
  let box = hits[0];
  if (!box) {
    const before = good >= 0 ? (fixes[items[good].key] || items[good].boxes).find(b => b[0] === active) : null;
    const w = before ? before[3] : Math.round(t.h / 8), h = before ? before[4] : w;
    box = [Math.round(x - w / 2), Math.round(y - h / 2), w, h];
  }
  boxes = boxes.filter(b => b[0] !== active).concat([[active, ...box]]);
  active = null;
  buttons();
  draw($("big"), t, boxes);
};

function save() {
  if (!ready) return;
  const t = items[wrong[n]];
  fetch("/correctie", { method: "POST", body: JSON.stringify({ item: t.key, boxes }) })
    .then(r => { if (!r.ok) throw new Error(); })
    .catch(() => alert("De correctie van " + t.title + " is NIET opgeslagen. Draait het programma nog?"));
  fixes[t.key] = boxes;
  n++;
  show();
}

addEventListener("keydown", e => {
  if (e.key === "Enter") { e.preventDefault(); if (!e.repeat) save(); }
  if (e.key === "Backspace") { e.preventDefault(); if (n > 0) { n--; show(); } }
});
addEventListener("resize", () => n < wrong.length && show());

fetch("/items").then(r => r.json()).then(d => {
  ({ items, verdict, fixes, found } = d);
  wrong = items.map((t, i) => i).filter(i => verdict[items[i].key] === "fout");
  n = wrong.findIndex(i => !(items[i].key in fixes));
  if (n < 0) n = wrong.length;
  show();
});
</script></body></html>
"""


def main() -> None:
    todo = items()
    images = Images(todo)
    listing = json.dumps([{k: t[k] for k in ("key", "title", "w", "h", "boxes")} for t in todo], default=int)
    found = json.dumps(detected(todo), default=int)
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
                body = (f'{{"items": {listing}, "verdict": {json.dumps(judged())}, '
                        f'"fixes": {json.dumps(corrected())}, "found": {found}}}')
                self.send(body.encode(), "application/json")
            elif self.path.startswith("/image/") and self.path[7:].isdigit() and int(self.path[7:]) < len(todo):
                self.send(images.get(int(self.path[7:])), "image/jpeg")
            else:
                self.send(b"niet gevonden", "text/plain", 404)

        def do_POST(self) -> None:
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if self.path != "/correctie":
                return self.send(b"onbekend", "text/plain", 400)
            boxes = [[str(b[0])] + [int(v) for v in b[1:5]] for b in data["boxes"]]
            with write:
                save(str(data["item"]), boxes)
            self.send(b"ok", "text/plain")

        def log_message(self, *args) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Labels verbeteren: open http://localhost:{PORT}  (stoppen: Ctrl+C)")
    webbrowser.open(f"http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
