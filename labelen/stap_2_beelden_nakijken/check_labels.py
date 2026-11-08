r"""Stap 2: elk beeld nakijken. Zeg per beeld of de labels uit stap 1 kloppen.

Invoer:  de labels uit stap 1 (output/stap_1_tracks_labelen/labels.csv), de kaders uit stap 0 en de filmpjes.
Uitvoer: output/stap_2_beelden_nakijken/controle_labels.csv, met per beeld goed of fout.

Het programma laat achter elkaar zien:
1. elk beeld van elk fragment in filmpjes/ (alle 11.182, ook de beelden zonder kader);
2. elke foto en elke still die in stap 1 gelabeld is.
Alleen de vier personen krijgen een kader: om elk gezicht dat in stap 1 als een van de vier is aangewezen, met de naam
erbij. Staat een persoon meer dan één keer in hetzelfde beeld (bijvoorbeeld twee kaders op één hoofd), dan worden die
kaders samen één groot kader. Was een persoon in het vorige beeld van het fragment wel te zien en in dit beeld niet,
dan staat er bovenin een waarschuwing.

Toetsen: pijltje links = goed, pijltje rechts = fout, Backspace = een beeld terug.
Elk oordeel komt meteen in controle_labels.csv. Geef je een beeld twee keer een oordeel, dan telt het laatste.
Wie stopt en later weer start, gaat verder bij het eerste beeld zonder oordeel.

Gebruik (vanuit de map labelen):
    Mac:     .venv/bin/python stap_2_beelden_nakijken/check_labels.py
    Windows: .venv\Scripts\python stap_2_beelden_nakijken\check_labels.py
Met --uitvoer <map> komen de oordelen in een andere map, bijvoorbeeld om het programma te proberen zonder de echte
uitkomst te veranderen. De controle opent vanzelf in de browser, op http://localhost:8020 (of het eerstvolgende
vrije adres). Stoppen: Ctrl+C in het terminalvenster.
"""

import argparse
import csv
import datetime
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # zodat de map gedeeld/ gevonden wordt

from gedeeld.beelden import Images
from gedeeld.items import items, judged
from gedeeld.paden import VERDICTS
from gedeeld.webserver import run

PORT = 8020
PAGE = Path(__file__).with_name("pagina.html").read_bytes()


def save(out: Path, item: str, verdict: str) -> None:
    new = not out.exists()
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        if new:
            writer.writerow(["item", "oordeel", "tijd"])
        writer.writerow([item, verdict, datetime.datetime.now().isoformat(timespec="seconds")])


def main() -> None:
    parser = argparse.ArgumentParser(description="Stap 2: elk beeld nakijken")
    parser.add_argument("--uitvoer", type=Path, help="map voor controle_labels.csv, in plaats van de echte uitkomst")
    args = parser.parse_args()
    out = args.uitvoer / VERDICTS.name if args.uitvoer else VERDICTS

    todo = items()
    images = Images(todo)
    listing = json.dumps([{k: t[k] for k in ("key", "title", "w", "h", "boxes", "gone")} for t in todo],
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
                self.send(PAGE, "text/html; charset=utf-8")
            elif self.path == "/items":
                body = b'{"items": ' + listing + b', "done": ' + json.dumps(judged(out)).encode() + b"}"
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
                save(out, str(data["item"]), data["oordeel"])
            self.send(b"ok", "text/plain")

        def log_message(self, *args) -> None:
            pass

    run(Handler, PORT, f"Stap 2: {len(todo)} beelden, foto's en stills nakijken")


if __name__ == "__main__":
    main()
