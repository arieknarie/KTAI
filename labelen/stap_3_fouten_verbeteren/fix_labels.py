r"""Stap 3: de foute beelden verbeteren. Elk beeld dat in stap 2 fout kreeg, wordt hier goed gezet.

Invoer:  de oordelen uit stap 2 (output/stap_2_beelden_nakijken/controle_labels.csv), de labels uit stap 1, de kaders
         uit stap 0 en de filmpjes.
Uitvoer: output/stap_3_fouten_verbeteren/correcties.csv, met per verbeterd beeld de kaders van de vier personen.

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
- Enter (of de knop Opslaan): opslaan en naar het volgende foute beeld. Backspace: terug naar het vorige foute beeld;
  de verbeteringen van dat beeld en van alle beelden erna worden dan gewist, zodat je vanaf daar opnieuw verbetert.
In correcties.csv komt per opgeslagen beeld, per persoon in het beeld, één rij met het kader (in pixels van het
originele beeld); een beeld zonder een van de vier krijgt één rij zonder persoon. Bij een tweede keer opslaan telt de
laatste keer; een rij met persoon "-" wist de verbetering van dat beeld. Wie stopt en later weer start, gaat verder
bij het eerste foute beeld dat nog niet verbeterd is.

Gebruik (vanuit de map labelen):
    Mac:     .venv/bin/python stap_3_fouten_verbeteren/fix_labels.py
    Windows: .venv\Scripts\python stap_3_fouten_verbeteren\fix_labels.py
Met --uitvoer <map> komen de verbeteringen in een andere map, bijvoorbeeld om het programma te proberen zonder de echte
uitkomst te veranderen. Het opent vanzelf in de browser, op http://localhost:8030 (of het eerstvolgende vrije adres). Stoppen: Ctrl+C in het
terminalvenster.
Daarna maakt make_ground_truth.py (in deze map) uit alle stappen samen de ground truth.
"""

import argparse
import csv
import datetime
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.beelden import Images
from gedeeld.items import corrected, items, judged
from gedeeld.paden import CORRECTIONS, DETECTIONS, LABELS
from gedeeld.webserver import run

PORT = 8030
PAGE = Path(__file__).with_name("pagina.html").read_bytes()


def detected(todo: list) -> dict:
    """Per item alle kaders die de computer vond (of die de labelaar zag), los van de keuze: om op te klikken."""
    index = {t["key"]: i for i, t in enumerate(todo)}
    found = {}
    for b in pd.read_csv(DETECTIONS).itertuples():
        found.setdefault(index[f"{b.video}#beeld{b.frame}"], []).append([b.x, b.y, b.w, b.h])
    labels = pd.read_csv(LABELS)
    for b in labels[~labels["item"].str.startswith("track:")].itertuples():
        if b.item in index:
            found.setdefault(index[b.item], []).append([b.x, b.y, b.w, b.h])
    return found


def erase(out: Path, keys: list) -> None:
    now = datetime.datetime.now().isoformat(timespec="seconds")
    with open(out, "a", newline="", encoding="utf-8") as f:
        csv.writer(f, lineterminator="\n").writerows([[key, "-", "", "", "", "", now] for key in keys])


def save(out: Path, item: str, boxes: list) -> None:
    new, now = not out.exists(), datetime.datetime.now().isoformat(timespec="seconds")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        if new:
            writer.writerow(["item", "persoon", "x", "y", "w", "h", "tijd"])
        for name, x, y, w, h in boxes or [["", "", "", "", ""]]:
            writer.writerow([item, name, x, y, w, h, now])


def main() -> None:
    parser = argparse.ArgumentParser(description="Stap 3: de foute beelden verbeteren")
    parser.add_argument("--uitvoer", type=Path, help="map voor correcties.csv, in plaats van de echte uitkomst")
    args = parser.parse_args()
    out = args.uitvoer / CORRECTIONS.name if args.uitvoer else CORRECTIONS

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
                self.send(PAGE, "text/html; charset=utf-8")
            elif self.path == "/items":
                body = (f'{{"items": {listing}, "verdict": {json.dumps(judged())}, '
                        f'"fixes": {json.dumps(corrected(out))}, "found": {found}}}')
                self.send(body.encode(), "application/json")
            elif self.path.startswith("/image/") and self.path[7:].isdigit() and int(self.path[7:]) < len(todo):
                self.send(images.get(int(self.path[7:])), "image/jpeg")
            else:
                self.send(b"niet gevonden", "text/plain", 404)

        def do_POST(self) -> None:
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if self.path == "/wissen":
                with write:
                    erase(out, [str(key) for key in data["items"]])
                return self.send(b"ok", "text/plain")
            if self.path != "/correctie":
                return self.send(b"onbekend", "text/plain", 400)
            boxes = [[str(b[0])] + [int(v) for v in b[1:5]] for b in data["boxes"]]
            with write:
                save(out, str(data["item"]), boxes)
            self.send(b"ok", "text/plain")

        def log_message(self, *args) -> None:
            pass

    run(Handler, PORT, "Stap 3: de foute beelden verbeteren")


if __name__ == "__main__":
    main()
