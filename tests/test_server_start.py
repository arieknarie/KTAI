"""Starten en stoppen van de labelapp (labeling/app.py), en het lezen en schrijven van labels.csv.

Deze test start de app zelf, in een eigen kopie van app.py en items.json (run_tests.sh maakt die kopie), en
controleert:
- twee starts tegelijk (bijvoorbeeld door twee keer te klikken): er blijft één app draaien, en de tweede start opent
  alleen de pagina van de app die al draait (daarvoor houdt de app het bestand .labelapp.lock vast);
- de app kiest de eerste vrije poort, schrijft die in .labelapp.port en haalt dat bestand weg bij het stoppen;
- op een drukke computer, als de app even niet aan de beurt is, neemt de app toch alle verbindingen van de browser aan;
- labels.csv: een label dat niet meer bij items.json past wordt niet gebruikt (ook een getekend gezicht), een BOM
  (van Excel) maakt niets uit, een vergrendelde of kapotte labels.csv geeft een duidelijke melding, en de
  reservekopieën in backups/;
- het opschonen van de naam van de labelaar.

Gebruik (run_tests.sh doet dit): python3 test_server_start.py <lege map met een kopie van app.py en items.json>
De app draait met dezelfde Python als deze test; run_tests.sh draait de test daarom met twee Python-versies.
Alleen standaard-Python. Elke controle schrijft "PASS  <naam>", "FAIL  <naam>  (details)" of "OVERGESLAGEN  <naam>".
"""
import csv
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

DIR = os.path.realpath(sys.argv[1])
ENV = {**os.environ, "LABELAPP_NO_BROWSER": "1"}
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # rechtstreeks naar 127.0.0.1, nooit via een proxy
PORTS = range(8765, 8785)   # dezelfde poorten als in app.py
started = []                # alle apps die deze test startte; aan het eind worden ze zeker gestopt
logs = 0


def check(name, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok or detail == "" else f"  ({detail})"))


def start():
    """Start de app in DIR (zonder browservenster). Geeft het proces en het bestand waarin de app schrijft."""
    global logs
    logs += 1
    log = os.path.join(DIR, f"start_{logs}.log")
    with open(log, "w") as out:
        process = subprocess.Popen([sys.executable, "-u", "app.py"], cwd=DIR, env=ENV, stdout=out, stderr=subprocess.STDOUT)
    started.append(process)
    return process, log


def read(log):
    with open(log, encoding="utf-8", errors="replace") as f:
        return f.read()


def stop(process):
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(10)
    except subprocess.TimeoutExpired:
        process.kill()


def ping(port):
    """De map van de labelapp op deze poort, of None."""
    try:
        with OPENER.open(f"http://127.0.0.1:{port}/api/ping", timeout=1) as response:
            return json.loads(response.read().decode("utf-8")).get("folder")
    except Exception:
        return None


def wait_running():
    """Wacht tot de app uit DIR antwoordt; geeft de poort."""
    for attempt in range(150):
        try:
            with open(os.path.join(DIR, ".labelapp.port")) as f:
                port = int(f.read().strip())
            if ping(port) and os.path.realpath(ping(port)) == DIR:
                return port
        except (OSError, ValueError):
            pass
        time.sleep(0.1)
    raise RuntimeError("de app startte niet")


def get(port, path):
    with OPENER.open(f"http://127.0.0.1:{port}{path}", timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def post(port, rows):
    request = urllib.request.Request(f"http://127.0.0.1:{port}/api/labels", data=json.dumps(rows).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
    try:
        with OPENER.open(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return json.loads(error.read().decode("utf-8"))


LABELS = os.path.join(DIR, "labels.csv")
with open(os.path.join(DIR, "items.json"), encoding="utf-8") as f:
    items = json.load(f)["items"]
# twee gezichten van twee verschillende items (de eerste twee items met een gezicht; welke maakt voor deze test niet uit)
first, second = [i for i in items if i["faces"]][:2]
f0, f1 = first["faces"][0], second["faces"][0]
# een getekend gezicht (een kader dat de labelaar zelf tekende) bij het eerste item, binnen het beeld
DRAWN = {"face": first["id"] + "#getekend-1", "label": "Johann", "labeler": "T", "how": "getekend",
         "x": 1, "y": 1, "w": min(10, first["width"] - 1), "h": min(10, first["height"] - 1)}

try:
    # ---- 1. twee starts op hetzelfde moment: precies één app blijft draaien
    a, log_a = start()
    b, log_b = start()
    for attempt in range(150):
        if (a.poll() is None) != (b.poll() is None):
            break
        time.sleep(0.1)
    running = [p for p in (a, b) if p.poll() is None]
    check("twee starts tegelijk: één server blijft draaien", len(running) == 1, f"{len(running)} draaien")
    second = read(log_b if running == [a] else log_a)
    check("de tweede start opent de draaiende app", "draait al" in second, second.strip().splitlines()[-1:] if second else "")
    server = running[0] if running else a
    port = wait_running()

    # ---- 2. labels.csv zoals de app die schrijft
    post(port, [{"face": f0["face"], "label": "unknown", "labeler": "T"}, {"face": f1["face"], "label": "no_face", "labeler": "T"},
                DRAWN])
    with open(LABELS, "rb") as f:
        raw = f.read()
    check("labels.csv heeft overal dezelfde regeleinden (geen \\r\\n, ook niet op Windows)", b"\r\n" not in raw and raw.count(b"\n") == 4)
    check("een getekend gezicht wordt bewaard en weer aan de pagina gegeven",
          get(port, "/api/labels").get(DRAWN["face"], {}).get("label") == "Johann")
    if os.name != "nt":
        mode = os.stat(LABELS).st_mode & 0o777
        check("labels.csv heeft gewone bestandsrechten (rw-r--r--)", mode == 0o644, oct(mode))

    # ---- 3. een label waarvan het kader niet meer klopt met items.json wordt niet gebruikt, net als een getekend gezicht
    # waarvan het bestand niet meer klopt (bijvoorbeeld na een nieuwe items.json); een BOM maakt niets uit
    with open(LABELS, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        if row["face"] == f1["face"]:
            row["x"] = str(int(row["x"]) + 5)
        if row["face"] == DRAWN["face"]:
            row["source"] = "een ander bestand.mp4"
    with open(LABELS, "w", newline="", encoding="utf-8-sig") as f:   # zoals Excel het opslaat: met een BOM vooraan
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    labels = get(port, "/api/labels")
    check("label met een ander kader dan in items.json wordt niet gebruikt", f1["face"] not in labels and f0["face"] in labels)
    check("getekend gezicht met een ander bestand dan in items.json wordt niet gebruikt", DRAWN["face"] not in labels)
    check("labels.csv met BOM wordt gewoon gelezen", labels.get(f0["face"], {}).get("label") == "unknown")

    # ---- 4. stoppen: .labelapp.port is daarna weg
    stop(server)
    time.sleep(0.3)
    check("na stoppen is .labelapp.port weg", not os.path.exists(os.path.join(DIR, ".labelapp.port")))

    # ---- 5. de functies van app.py zelf, in dit programma geladen
    sys.path.insert(0, DIR)
    os.chdir(DIR)
    import app

    # een vergrendelde labels.csv (nagebootst: vervangen lukt niet) geeft een duidelijke melding en laat labels.csv heel
    real_replace, real_sleep = os.replace, app.time.sleep

    def locked(*args, **kwargs):
        raise PermissionError("vergrendeld")

    os.replace, app.time.sleep = locked, (lambda seconds: None)
    with open(LABELS, encoding="utf-8-sig") as f:
        before = f.read()
    try:
        app.save_rows([{"face": f0["face"], "label": "other", "labeler": "T"}])
        message = ""
    except PermissionError as error:
        message = str(error)
    finally:
        os.replace, app.time.sleep = real_replace, real_sleep
    check("vergrendelde labels.csv: duidelijke melding", "Excel" in message, message[:80])
    with open(LABELS, encoding="utf-8-sig") as f:
        same = f.read() == before
    check("vergrendelde labels.csv: bestand onveranderd, geen tijdelijke bestanden", same and not [n for n in os.listdir(DIR) if n.endswith(".tmp")])

    # reservekopieën: met een kopie bij elke opslag blijven er hoogstens KEEP_BACKUPS bewaard
    for old in os.listdir(app.BACKUP_DIR) if os.path.isdir(app.BACKUP_DIR) else []:
        os.remove(os.path.join(app.BACKUP_DIR, old))
    app.BACKUP_EVERY, app.KEEP_BACKUPS = 0, 3
    for label in ["unknown", "no_face", "other", "unknown", "no_face"]:
        app.save_rows([{"face": f0["face"], "label": label, "labeler": "T"}])
        time.sleep(1.05)   # de naam van een reservekopie bevat de tijd in seconden
    backups = sorted(os.listdir(app.BACKUP_DIR))
    check("reservekopieën: de oudste worden weggegooid, de nieuwste blijven", len(backups) == 3, backups)
    app.BACKUP_EVERY = 15 * 60
    app.save_rows([{"face": f0["face"], "label": "other", "labeler": "T"}])
    check("reservekopieën: binnen het kwartier geen extra kopie", len(os.listdir(app.BACKUP_DIR)) == 3)

    # de naam van de labelaar: alleen letters, cijfers, spatie, punt en streepjes, met minstens één letter
    cases = [("Jan", "Jan"), ("  Jan de Vries  ", "Jan de Vries"), ("123", ""), ("=SUM(A1)", "SUMA1"), ("..-_Piet", "Piet"),
             ("José", "José"), ("x" * 50, "x" * 40), ("🙂🙂", ""), ("", ""), (None, "")]
    wrong = [(name, app.clean_name(name), want) for name, want in cases if app.clean_name(name) != want]
    check("de naam van de labelaar wordt opgeschoond", not wrong, wrong)

    # ---- 6. een bezette poort: de app kiest de volgende vrije poort en schrijft die in .labelapp.port.
    # Bij de start meldt de app ook de label(s) in labels.csv die niet meer bij items.json passen (hier: f1 en het
    # getekende gezicht, zie 3).
    blocker, blocked = socket.socket(), None
    for candidate in PORTS:   # de eerste poort die nu vrij is, tijdelijk bezet houden
        try:
            blocker.bind(("127.0.0.1", candidate))
            blocker.listen(1)
            blocked = candidate
            break
        except OSError:
            continue
    if blocked is None:
        check("bezette poort: de app kiest een andere vrije poort", False, "geen vrije poort tussen 8765 en 8784")
    else:
        server, log = start()
        port = wait_running()
        check("bezette poort: de app kiest een andere vrije poort en schrijft die in .labelapp.port",
              port != blocked and port in PORTS and ping(port) is not None, f"bezet {blocked}, gekozen {port}")
        startup = read(log)
        check("bij de start meldt de app labels die niet meer bij items.json passen", "Let op: 2 label(s)" in startup, startup[:200])
        others = [p for p in PORTS if p < port and p != blocked and ping(p) and os.path.realpath(ping(p)) != DIR]
        if others:
            check("bij de start meldt de app een labelapp uit een andere map", "labelapp uit een andere map" in startup, startup[:300])
        else:
            print("OVERGESLAGEN  melding over een labelapp uit een andere map  (er draait geen andere labelapp op een lagere poort)")
        stop(server)
        blocker.close()

    # ---- 7. een drukke computer: de app is even niet aan de beurt (nagebootst door de app twee seconden stil te zetten),
    # terwijl de browser verbindingen opent. Chrome opent tot zes verbindingen tegelijk naar één adres (en soms meer);
    # de test opent er acht tegelijk. Geen enkele verbinding mag dan geweigerd worden: een geweigerde verbinding is in de
    # browser een foto of beeld dat niet laadt, of een keuze die (voorlopig) niet opgeslagen wordt.
    if not hasattr(signal, "SIGSTOP"):
        print("OVERGESLAGEN  drukke computer: de app neemt alle verbindingen aan  (de app stilzetten kan hier niet)")
    else:
        server, log = start()
        port = wait_running()
        answers = []

        def ask():
            connection = socket.socket()
            connection.settimeout(20)
            try:
                connection.connect(("127.0.0.1", port))
                connection.sendall(f"GET /api/ping HTTP/1.0\r\nHost: 127.0.0.1:{port}\r\n\r\n".encode())
                data = b""
                while True:
                    chunk = connection.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                answers.append(data.split(b"\r\n", 1)[0])
            except OSError as error:
                answers.append(type(error).__name__.encode())
            finally:
                connection.close()

        os.kill(server.pid, signal.SIGSTOP)
        try:
            clients = [threading.Thread(target=ask) for _ in range(8)]
            for client in clients:
                client.start()
            time.sleep(2)
        finally:
            os.kill(server.pid, signal.SIGCONT)
        for client in clients:
            client.join(30)
        good = sum(1 for answer in answers if answer.startswith(b"HTTP/") and b" 200 " in answer + b" ")
        check("drukke computer: de app neemt 8 verbindingen tegelijk aan (geen enkele geweigerd)", good == 8,
              f"{good} van 8 aangenomen: {sorted(set(a.decode(errors='replace') for a in answers))}")
        stop(server)

    # ---- 8. een kapotte labels.csv (andere kolommen) bij de start: een duidelijke melding, en de app start niet
    with open(LABELS, "w", encoding="utf-8") as f:
        f.write("a,b\n1,2\n")
    broken, log = start()
    try:
        broken.wait(15)
    except subprocess.TimeoutExpired:
        pass
    check("kapotte labels.csv bij de start: duidelijke melding en geen server", broken.poll() is not None
          and "niet de goede kolommen" in read(log) and not os.path.exists(os.path.join(DIR, ".labelapp.port")), read(log)[:200])
finally:
    for process in started:
        stop(process)
