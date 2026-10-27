"""Labelapp: toont de gezichten die gelabeld moeten worden en slaat elk label meteen op.

Starten: dubbelklik op START_MAC.command (Mac) of START_WINDOWS.bat (Windows),
of typ in een terminal in deze map: python3 app.py (Mac) / py app.py (Windows).

Dit programma gebruikt alleen standaard-Python (versie 3.8 of nieuwer); er
hoeft niets extra geïnstalleerd te worden.

Wat het programma doet:
- Het start een kleine webserver op de computer van de labelaar zelf (de
  computer waarop dit programma gestart wordt) en opent de labelpagina in de
  browser van die computer. De webserver is alleen vanaf die computer
  bereikbaar; er gaat niets via internet.
- Per map draait er altijd maar één labelapp. Wordt de app uit deze map nog
  een keer gestart (bijvoorbeeld door twee keer te klikken), dan opent de
  tweede start alleen de pagina van de app die al draait. Daarvoor houdt de
  app het bestand .labelapp.lock vast zolang de app draait; in .labelapp.port
  staat op welk adres de app draait.
- Bij elke start (als er al labels zijn), en daarna bij het eerste label na
  elk kwartier, wordt een reservekopie van labels.csv gemaakt in backups/.
- Elke keuze op de labelpagina wordt direct opgeslagen in labels.csv, in deze
  map op de computer van de labelaar. Na het labelen stuurt de labelaar
  labels.csv naar Marc (zie README.md, stap 6).

Kolommen van labels.csv:
    face            gezicht-id (uit items.json)
    item            het item (foto, still of track) waar het gezicht bij hoort
    label           DerAlte, FritzGrade, Johann, Werner, other (figurant), no_face (geen gezicht)
                    of unknown (weet niet)
    how             chosen: de labelaar koos dit zelf;
                    auto: figurant gemaakt bij Volgende, omdat de labelaar voor dit gezicht
                    niets gekozen had;
                    getekend: een gezicht dat de computer gemist had en waar de labelaar zelf
                    een kader omheen tekende (gezicht-id: <item>#getekend-<nummer>)
    labeler         naam van de labelaar
    time            tijdstip van opslaan
    source, frame, x, y, w, h   bestand, framenummer (bij video) en kader van het gezicht

Beveiliging en zekerheid:
- De webserver luistert alleen op 127.0.0.1 (de computer zelf).
- Opslaan kan alleen vanaf de eigen labelpagina: een andere website die in
  dezelfde browser openstaat, kan niets wegschrijven of uitlezen.
- Alleen gezichten die in items.json staan en de keuzes uit items.json worden
  opgeslagen. Bestand, frame en kader van elk gezicht komen uit items.json,
  niet uit de browser. Bij een getekend gezicht komen bestand en frame uit het
  item in items.json, en moet het kader binnen het beeld van dat item liggen. Een automatische figurant overschrijft nooit een label
  dat er al is. De naam van de labelaar wordt beperkt tot letters, cijfers,
  spaties, punten en streepjes (zodat een spreadsheet de naam nooit als formule
  leest); zonder naam wordt niets opgeslagen.
- labels.csv wordt eerst als tijdelijk bestand geschreven en pas daarna in één
  keer vervangen, zodat labels.csv nooit half geschreven kan zijn.
- Alleen de bestanden die de labelpagina nodig heeft (web/, images/,
  items.json) worden geleverd; de rest van deze map niet.
"""

import csv
import datetime
import errno
import json
import os
import posixpath
import re
import shutil
import signal
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ITEMS_FILE = HERE / "items.json"
LABELS_FILE = HERE / "labels.csv"
BACKUP_DIR = HERE / "backups"
LOCK_FILE = HERE / ".labelapp.lock"
PORT_FILE = HERE / ".labelapp.port"
KEEP_BACKUPS = 40           # zoveel reservekopieën worden bewaard
BACKUP_EVERY = 15 * 60      # tijdens het labelen: een reservekopie per zoveel seconden
PORTS = range(8765, 8785)   # poorten die geprobeerd worden, op volgorde
MAX_REQUEST = 2_000_000     # maximale grootte van één opslagverzoek (bytes)
MAX_NAME = 40               # maximale lengte van de naam van de labelaar
COLUMNS = ["face", "item", "label", "how", "labeler", "time", "source", "frame", "x", "y", "w", "h"]
PLACE = ["source", "frame", "x", "y", "w", "h"]   # waar het gezicht staat; moet kloppen met items.json

lock = threading.Lock()     # zorgt dat twee opslagacties nooit tegelijk schrijven
last_backup = 0.0           # tijdstip van de laatste reservekopie


def load_items():
    """Alle gezichten uit items.json ({gezicht-id: vaste gegevens}), de items ({item-id: bestand, frame en maat
    van het beeld}, voor getekende gezichten) en de toegestane keuzes."""
    data = json.loads(ITEMS_FILE.read_text(encoding="utf-8"))
    faces, items = {}, {}
    for item in data["items"]:
        for face in item["faces"]:
            x, y, w, h = face["box"]
            faces[face["face"]] = {"face": face["face"], "item": item["id"], "source": face["source"],
                                   "frame": face.get("frame", ""), "x": x, "y": y, "w": w, "h": h}
        first = item["faces"][0]
        items[item["id"]] = {"source": first["source"], "frame": first.get("frame", ""),
                             "width": item["width"], "height": item["height"]}
    return faces, items, {choice["key"] for choice in data["choices"]}


FACES, ITEMS, CHOICES = load_items()
DRAWN = "#getekend-"    # een getekend gezicht heet <item-id>#getekend-<nummer>
MIN_DRAWN = 4           # kleinste breedte en hoogte (pixels) van een getekend kader


def clean_name(name):
    """Naam van de labelaar: alleen letters, cijfers, spatie, punt, streepje en liggend streepje,
    niet beginnend met een leesteken, en met minstens één letter (anders leeg).
    (labeling/web/app.js doet hetzelfde.)"""
    name = re.sub(r"[^\w .-]", "", str(name or ""))
    name = name.lstrip(" .-_")[:MAX_NAME].strip()
    return name if re.search(r"[^\W\d_]", name) else ""


def drawn_face(row):
    """De vaste gegevens van een getekend gezicht (zoals FACES), of None als de rij geen geldig getekend
    gezicht is: het item bestaat niet, of het kader ligt niet helemaal binnen het beeld."""
    item_id, mark, number = str(row.get("face", "")).rpartition(DRAWN)
    item = ITEMS.get(item_id)
    if not mark or item is None or not number.isdigit() or len(number) > 20:
        return None
    try:
        x, y, w, h = (int(row.get(key)) for key in ("x", "y", "w", "h"))
    except (TypeError, ValueError):
        return None
    if x < 0 or y < 0 or w < MIN_DRAWN or h < MIN_DRAWN or x + w > item["width"] or y + h > item["height"]:
        return None
    return {"face": row["face"], "item": item_id, "source": item["source"], "frame": item["frame"],
            "x": x, "y": y, "w": w, "h": h}


def matches_items(row):
    """Hoort een opgeslagen label bij hetzelfde gezicht als in de huidige items.json? Een getekend gezicht hoort
    erbij als het item nog bestaat met hetzelfde bestand en frame, en het kader binnen het beeld ligt."""
    face = FACES.get(row.get("face")) or (drawn_face(row) if row.get("how") == "getekend" else None)
    return face is not None and all(str(row.get(key, "")) == str(face[key]) for key in PLACE)


def read_labels():
    """Alle opgeslagen labels: {gezicht-id: rij}."""
    if not LABELS_FILE.exists():
        return {}
    broken = ValueError("labels.csv heeft niet de goede kolommen. Is het bestand in een ander programma "
                        "veranderd? Zet een reservekopie uit backups/ terug (zie README.md).")
    try:
        with LABELS_FILE.open(newline="", encoding="utf-8-sig") as f:  # -sig: ook als een ander programma een BOM schreef
            reader = csv.DictReader(f)
            if "face" not in (reader.fieldnames or []) or "label" not in reader.fieldnames:
                raise broken
            return {row["face"]: row for row in reader}
    except (UnicodeDecodeError, csv.Error):  # in een andere tekenset opgeslagen (bijvoorbeeld door Excel) of beschadigd
        raise broken from None


def write_labels(labels):
    """Schrijf alle labels naar labels.csv: eerst naar een eigen tijdelijk bestand, dat daarna in één
    keer labels.csv vervangt. Is labels.csv even vergrendeld (op Windows bijvoorbeeld door Excel of
    een virusscanner), dan wordt het een paar seconden opnieuw geprobeerd."""
    handle, temporary = tempfile.mkstemp(dir=HERE, prefix="labels_", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")  # zelfde regeleinden op Mac en Windows
            writer.writeheader()
            for row in labels.values():
                writer.writerow({column: row.get(column, "") for column in COLUMNS})
            f.flush()
            os.fsync(f.fileno())  # echt op schijf, ook bij een stroomstoring direct daarna
        os.chmod(temporary, 0o644)  # gewone rechten, zoals elk ander bestand in de map
        for attempt in range(20):
            try:
                os.replace(temporary, LABELS_FILE)
                return
            except PermissionError:
                time.sleep(0.25)
        raise PermissionError("labels.csv is geopend in een ander programma (bijvoorbeeld Excel). Sluit dat "
                              "programma en kies daarna opnieuw iets.")
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)


def make_backup():
    """Reservekopie van labels.csv in backups/, met datum en tijd in de naam."""
    global last_backup
    last_backup = time.time()
    if not LABELS_FILE.exists():
        return
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    shutil.copy2(LABELS_FILE, BACKUP_DIR / f"labels_{stamp}.csv")
    backups = sorted(BACKUP_DIR.glob("labels_*.csv"))
    for old in backups[:-KEEP_BACKUPS]:
        old.unlink()


def save_rows(rows):
    """Verwerk de keuzes uit één opslagverzoek. Geeft (aantal verwerkt, overgeslagen keuzes met reden).

    - Onbekend gezicht of onbekende keuze: overgeslagen (dan is items.json veranderd terwijl de app
      draaide; de pagina vraagt dan om de app opnieuw te starten).
    - Lege naam: overgeslagen.
    - Automatische figurant (how = auto) bij een gezicht dat al een label heeft: niets veranderd.
    """
    now = datetime.datetime.now().isoformat(timespec="seconds")
    done, skipped = 0, []
    with lock:
        labels = read_labels()
        for row in rows:
            face, label, name = row.get("face"), row.get("label"), clean_name(row.get("labeler"))
            fixed = FACES.get(face) or drawn_face(row)   # een gezicht uit items.json, of een getekend gezicht
            drawn = face not in FACES
            if fixed is None or (label and label not in CHOICES) or (drawn and label == "no_face"):
                skipped.append({"face": str(face)[:80], "reason": "onbekend"})
            elif label and not name:
                skipped.append({"face": face, "reason": "naam"})
            elif label:
                how = "getekend" if drawn else "auto" if row.get("how") == "auto" else "chosen"
                if how == "auto" and face in labels and matches_items(labels[face]):
                    done += 1  # er is al een label; een automatische figurant verandert dat niet
                    continue
                # alles behalve de keuze en de naam komt uit items.json (bij een getekend gezicht ook het kader,
                # dat binnen het beeld moet liggen)
                labels[face] = dict(fixed, label=label, how=how, labeler=name, time=now)
                done += 1
            else:
                labels.pop(face, None)  # keuze gewist
                done += 1
        write_labels(labels)
        if time.time() - last_backup >= BACKUP_EVERY:
            try:
                make_backup()
            except OSError as error:  # een mislukte reservekopie maakt het opslaan niet ongedaan
                print("Let op: de reservekopie is mislukt:", error)
    return done, skipped


class Handler(SimpleHTTPRequestHandler):
    """Levert de labelpagina en verwerkt het opslaan van labels."""

    # vaste bestandstypen; op Windows kan het register anders bijvoorbeeld .js als tekst opgeven,
    # en dan voert de browser het script niet uit
    extensions_map = {
        ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8",
        ".jpg": "image/jpeg", ".png": "image/png", "": "application/octet-stream",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HERE), **kwargs)

    def log_message(self, format, *args):
        pass  # geen meldingen per opgevraagd plaatje in het venster

    def end_headers(self):
        # de pagina mag niet in een andere website getoond worden en laadt alleen eigen bestanden
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; form-action 'none'")
        # de browser vraagt de pagina en items.json elke keer na, zodat een nieuwe versie meteen gebruikt wordt
        # (een onveranderd bestand kost dan alleen een kort antwoord "niet veranderd")
        if getattr(self, "path", "").startswith(("/web/", "/items.json")):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def own_address(self):
        """Is de app aangesproken via haar eigen adres (127.0.0.1 of localhost met de eigen poort)?"""
        port = self.server.server_address[1]
        return self.headers.get("Host", "") in (f"127.0.0.1:{port}", f"localhost:{port}")

    def own_page(self):
        """Komt een opslagverzoek van de eigen labelpagina? Een browser stuurt bij elk
        opslagverzoek mee van welke pagina het komt (Origin)."""
        port = self.server.server_address[1]
        origin = self.headers.get("Origin")
        return origin is None or origin in (f"http://127.0.0.1:{port}", f"http://localhost:{port}")

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # het pad zoals de webserver het leest: %-codes vertaald en ".." weggewerkt
        raw = urllib.parse.unquote(self.path.split("?", 1)[0].split("#", 1)[0])
        path = posixpath.normpath(raw) + ("/" if raw.endswith("/") and raw != "/" else "")
        if not self.own_address():
            self.send_error(403)
            return
        if path in ("/", "/web"):
            # doorsturen naar /web/, zodat de pagina haar opmaak en script op de goede plek vindt
            self.send_response(302)
            self.send_header("Location", "/web/")
            self.end_headers()
            return
        if path == "/api/ping":  # zodat een tweede start ziet dat deze app al draait, en de pagina weet waar labels.csv staat
            self.send_json({"app": "labelapp", "folder": str(HERE), "labels": str(LABELS_FILE)})
            return
        if path == "/api/labels":
            try:
                with lock:
                    labels = read_labels()
            except ValueError as error:
                self.send_json({"error": str(error)}, 500)
                return
            # alleen labels die bij hetzelfde gezicht horen als in de huidige items.json
            self.send_json({face: row for face, row in labels.items() if matches_items(row)})
            return
        if not (path == "/items.json" or path.startswith(("/web/", "/images/"))) or \
                (path.endswith("/") and path != "/web/"):
            self.send_error(404)  # andere bestanden en mappenoverzichten worden niet geleverd
            return
        super().do_GET()

    def do_HEAD(self):
        self.send_error(405)

    def do_POST(self):
        if self.path != "/api/labels":
            self.send_json({"error": "onbekend adres"}, 404)
            return
        if not (self.own_address() and self.own_page()):
            self.send_json({"error": "alleen de eigen labelpagina mag opslaan"}, 403)
            return
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            self.send_json({"error": "verkeerd soort verzoek"}, 415)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if not 0 < length <= MAX_REQUEST:
                raise ValueError("opslagverzoek is leeg of te groot")
            rows = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
                raise ValueError("verwacht een lijst met keuzes")
        except ValueError as error:  # ook voor kapotte JSON
            self.send_json({"error": str(error)}, 400)
            return
        try:
            done, skipped = save_rows(rows)
            self.send_json({"saved": done, "skipped": skipped})
        except Exception as error:  # bijvoorbeeld labels.csv vergrendeld door een ander programma
            self.send_json({"error": str(error)}, 500)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    # Een browser vraagt veel plaatjes tegelijk op. Standaard wachten er hoogstens 5 verbindingen op hun beurt; op
    # een drukke computer weigert de app dan soms een plaatje of een keuze.
    request_queue_size = 64
    # Op Windows zou een tweede programma met deze instelling dezelfde poort kunnen krijgen. (Twee labelapps
    # uit dezelfde map kunnen niet tegelijk draaien: daarvoor zorgt .labelapp.lock.)
    allow_reuse_address = os.name != "nt"

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (ConnectionError, TimeoutError)):
            return  # de browser brak een verzoek af (bijvoorbeeld bij herladen): geen melding nodig
        super().handle_error(request, client_address)


class AlreadyRunning(Exception):
    pass


def take_lock():
    """Houd .labelapp.lock vast zolang de app draait. Geeft het open bestand (of None als vergrendelen in
    deze map niet kan); AlreadyRunning als een andere labelapp uit deze map het bestand al vasthoudt."""
    try:
        handle = open(LOCK_FILE, "a+")
    except PermissionError:
        print("De map labeling is alleen-lezen. Pak het ZIP-bestand uit naar een gewone map (zie README.md, stap 2).")
        raise SystemExit(1)
    try:
        if os.name == "nt":
            import msvcrt
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return handle
    except OSError as error:
        handle.close()
        if isinstance(error, BlockingIOError) or error.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
            raise AlreadyRunning()
        # bijvoorbeeld een netwerkmap die geen vergrendeling kent
        print("Let op: deze map kan niet vergrendeld worden. Start de app hier maar één keer tegelijk.")
        return None


def ping(port):
    """Map van de labelapp op deze poort, of None (zonder proxy, alleen deze computer)."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f"http://127.0.0.1:{port}/api/ping", timeout=1) as response:
            info = json.loads(response.read().decode("utf-8"))
        return info.get("folder") if info.get("app") == "labelapp" else None
    except Exception:
        return None


def open_running_app():
    """Een labelapp uit deze map draait al: open de pagina van die app."""
    for attempt in range(20):  # die app kan net aan het starten zijn
        try:
            port = int(PORT_FILE.read_text().strip())
            if ping(port) == str(HERE):
                address = f"http://127.0.0.1:{port}/"
                print("De labelapp uit deze map draait al, in een ander venster.")
                print(f"De labelpagina wordt geopend: {address}")
                print("Dit venster mag je sluiten.")
                if not os.environ.get("LABELAPP_NO_BROWSER"):
                    webbrowser.open(address)
                return
        except (OSError, ValueError):
            pass
        time.sleep(0.5)
    print("De labelapp uit deze map lijkt al te draaien, maar is niet bereikbaar.")
    print("Sluit alle vensters van de labelapp en start de app opnieuw.")


def main():
    if sys.version_info < (3, 8):
        print("Deze app heeft Python 3.8 of nieuwer nodig. Zie README.md, stap 1.")
        return
    print("De labelapp start ...")
    try:
        lock_handle = take_lock()
    except AlreadyRunning:
        open_running_app()
        return

    try:
        stale = sum(1 for row in read_labels().values() if not matches_items(row))
    except ValueError as error:
        print(error)
        return
    if stale:
        print(f"Let op: {stale} label(s) in labels.csv horen bij gezichten die niet (meer) in items.json staan. "
              "Die labels blijven in labels.csv staan, maar de app gebruikt ze niet.")
    make_backup()

    server = None
    for port in PORTS:
        try:
            server = Server(("127.0.0.1", port), Handler)
            break
        except OSError:
            other = ping(port)  # poort al in gebruik: door een labelapp uit een andere map?
            if other:
                print("Let op: er draait ook een labelapp uit een andere map:", other)
                print("Gebruik alleen de pagina van dit venster; de labels komen dan in deze map.\n")
    if server is None:
        print("Geen vrije poort gevonden. Sluit andere vensters van de labelapp en probeer opnieuw.")
        return
    port = server.server_address[1]
    PORT_FILE.write_text(str(port))
    address = f"http://127.0.0.1:{port}/"
    print("De labelapp draait.")
    print(f"Open deze pagina in je browser als die niet vanzelf opent: {address}")
    print("Labels worden opgeslagen in:", LABELS_FILE)
    print("Stoppen: sluit dit venster (of druk op Ctrl+C).")
    if not os.environ.get("LABELAPP_NO_BROWSER"):  # alleen bij het testen van de app uitgezet
        threading.Timer(1.0, lambda: webbrowser.open(address)).start()
    for name in ("SIGTERM", "SIGHUP"):  # ook bij het sluiten van het venster netjes stoppen (Mac)
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), lambda *args: sys.exit(0))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        try:
            PORT_FILE.unlink()
        except OSError:
            pass
        if lock_handle:
            lock_handle.close()
        print("De labelapp is gestopt.")


if __name__ == "__main__":
    main()
