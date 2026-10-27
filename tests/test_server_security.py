"""Beveiliging en robuustheid van de webserver van de labelapp (labeling/app.py), getest tegen de draaiende demo-app.

De webserver van de labelapp draait op de computer van de labelaar en mag alleen de eigen labelpagina bedienen.
Deze test stuurt de server allerlei verzoeken, ook verzoeken die een andere website of een kwaadwillend programma zou
kunnen sturen, en controleert het antwoord:
- alleen de bestanden die de labelpagina nodig heeft (web/, images/, items.json) worden geleverd, ook niet via
  omwegen in het adres zoals "../" of "%2e%2e";
- alleen verzoeken aan het eigen adres (127.0.0.1 of localhost met de eigen poort) worden beantwoord, en alleen de
  eigen labelpagina mag opslaan;
- kapotte, te grote of verkeerde opslagverzoeken krijgen een nette foutmelding;
- bestand, frame, kader en item van een gezicht komen altijd uit items.json, en de naam van de labelaar wordt
  opgeschoond (zodat een spreadsheet die nooit als formule leest);
- de server stuurt de juiste soort bestand (Content-Type) en de beveiligingsregels voor de browser mee.

Gebruik (run_tests.sh doet dit): python3 test_server_security.py <map van de demo-app> <python voor een tweede start>
Alleen standaard-Python. Elke controle schrijft "PASS  <naam>" of "FAIL  <naam>  (details)".
"""
import csv
import http.client
import json
import os
import subprocess
import sys
import time
import urllib.parse

DEMO, PYTHON = sys.argv[1], sys.argv[2]
with open(os.path.join(DEMO, ".labelapp.port")) as f:   # de app kiest zelf een vrije poort en schrijft die hier
    PORT = int(f.read().strip())
OWN = f"http://127.0.0.1:{PORT}"


def check(name, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok or detail == "" else f"  ({detail})"))


def req(method, path, body=None, headers=None):
    """Eén verzoek rechtstreeks aan de demo-app (zonder proxy). Geeft (status, headers, inhoud)."""
    connection = http.client.HTTPConnection("127.0.0.1", PORT, timeout=10)
    all_headers = {"Host": f"127.0.0.1:{PORT}"}
    all_headers.update(headers or {})
    connection.request(method, path, body=body, headers=all_headers)
    response = connection.getresponse()
    data = response.read()
    connection.close()
    return response.status, response.headers, data


def post(rows, **headers):
    """Een opslagverzoek zoals de labelpagina het stuurt (tenzij `headers` iets anders zegt)."""
    all_headers = {"Content-Type": "application/json", "Origin": OWN}
    all_headers.update(headers)
    return req("POST", "/api/labels", json.dumps(rows).encode(), all_headers)


def stored():
    with open(os.path.join(DEMO, "labels.csv"), newline="", encoding="utf-8") as f:
        return {row["face"]: row for row in csv.DictReader(f)}


with open(os.path.join(DEMO, "items.json"), encoding="utf-8") as f:
    items = json.load(f)
# een gezicht om mee te testen: het eerste gezicht van de eerste track (of van het eerste item als er geen track is),
# en het beeld van dat item (en de map waarin dat beeld staat). Een adres mag geen spaties bevatten; die worden,
# net als in de browser, als %20 geschreven.
item = next((i for i in items["items"] if i["kind"] == "track"), next(iter(items["items"])))
face = item["faces"][0]
image = "/" + urllib.parse.quote(item["image"])
folder = image.rsplit("/", 1)[0] + "/"
# in de naam van een controle: een vaste omschrijving in plaats van het adres, dat bij elke items.json anders is
SHOWN = {image: "<beeld van een item>", folder: "<map met beelden van items>/"}

# ---- welke adressen geleverd worden en welke niet
for path, want in [("/web/", 200), ("/items.json", 200), ("/web/app.js", 200), (image, 200),
                   ("/app.py", 404), ("/labels.csv", 404), ("/backups/", 404), ("/images/", 404), ("/web/../app.py", 404),
                   ("/web/%2e%2e/app.py", 404), ("/web/..%2fapp.py", 404), ("//app.py", 404), ("/web//../app.py", 404),
                   ("/web/./index.html", 200), ("/web/index.html?x=1", 200), ("/images/../labels.csv", 404), ("/README.md", 404),
                   (folder, 404), ("/.labelapp.port", 404), ("/automatic_labels.csv", 404)]:
    status, _, _ = req("GET", path)
    check(f"GET {SHOWN.get(path, path)} -> {want}", status == want, status)
for path in ["/", "/web"]:
    status, headers, _ = req("GET", path)
    check(f"GET {path} stuurt door naar /web/", status == 302 and headers.get("Location") == "/web/", (status, headers.get("Location")))
status, _, _ = req("HEAD", "/web/")
check("HEAD wordt niet ondersteund (405)", status == 405, status)

# ---- alleen het eigen adres en de eigen labelpagina
status, _, _ = req("GET", "/api/labels", headers={"Host": "evil.example:8765"})
check("ander adres (DNS-rebinding) wordt geweigerd", status == 403, status)
status, _, _ = req("GET", "/api/ping", headers={"Host": f"localhost:{PORT}"})
check("het adres localhost met de eigen poort werkt ook", status == 200, status)
status, _, _ = post([{"face": face["face"], "label": "unknown", "labeler": "Test"}], Origin="http://evil.example")
check("opslaan vanaf een andere website wordt geweigerd", status == 403, status)
status, _, _ = post([{"face": face["face"], "label": "unknown", "labeler": "Test"}], Host="evil.example")
check("opslaan via een ander adres wordt geweigerd", status == 403, status)
status, _, _ = post([{"face": face["face"], "label": "unknown", "labeler": "Test"}], Origin=f"http://localhost:{PORT}")
check("opslaan vanaf de eigen pagina op localhost mag", status == 200, status)
status, _, _ = req("POST", "/api/labels", json.dumps([{"face": face["face"], "label": "unknown"}]).encode(),
                   {"Content-Type": "text/plain", "Origin": OWN})
check("opslaan als 'text/plain' (zonder voorcontrole door de browser) wordt geweigerd", status == 415, status)
status, _, _ = req("POST", "/api/andere", b"[]", {"Content-Type": "application/json", "Origin": OWN})
check("opslaan op een ander adres dan /api/labels geeft 404", status == 404, status)

# ---- kapotte, lege, te grote en verkeerde opslagverzoeken
status, _, data = req("POST", "/api/labels", b"{kapot", {"Content-Type": "application/json"})
check("kapotte JSON geeft een nette fout", status == 400 and "error" in json.loads(data), data[:80])
status, _, data = req("POST", "/api/labels", b"[]", {"Content-Type": "application/json", "Content-Length": "2000001"})
check("te groot verzoek wordt geweigerd", status == 400, data[:80])
status, _, data = req("POST", "/api/labels", b"", {"Content-Type": "application/json", "Content-Length": "0"})
check("leeg verzoek wordt geweigerd", status == 400, data[:80])
status, _, data = post({"face": face["face"], "label": "unknown"})
check("een verzoek zonder lijst wordt geweigerd", status == 400, data[:80])
status, _, data = post([face["face"]])
check("een lijst met iets anders dan keuzes wordt geweigerd", status == 400, data[:80])
status, _, data = req("POST", "/api/labels", b'[{"face": "\xff"}]', {"Content-Type": "application/json", "Origin": OWN})
check("een opslagverzoek dat geen UTF-8 is, geeft een nette fout", status == 400 and "error" in json.loads(data), data[:80])
status, _, data = post([{"face": "bestaat/niet#0", "label": "unknown", "labeler": "Test"}, {"face": face["face"], "label": "hacker", "labeler": "Test"}])
answer = json.loads(data)
check("onbekend gezicht en onbekende keuze worden overgeslagen", status == 200 and answer["saved"] == 0 and len(answer["skipped"]) == 2, data[:120])
status, _, data = post([{"face": face["face"], "label": "unknown", "labeler": "!!!"}])
answer = json.loads(data)
check("zonder naam (met letters) wordt niets opgeslagen", answer.get("saved") == 0 and answer.get("skipped", [{}])[0].get("reason") == "naam", data[:120])

# ---- wat er in labels.csv komt
status, _, data = post([{"face": face["face"], "label": "no_face", "labeler": '=HYPERLINK("http://x")', "x": 9999,
                         "source": "nep.mp4", "item": "nep", "how": "getekend"}])
row = stored()[face["face"]]
check("naam wordt opgeschoond (geen formule)", row["labeler"] == "HYPERLINKhttpx", row["labeler"])
check("kader, bestand en item komen uit items.json", row["x"] == str(face["box"][0]) and row["source"] == face["source"]
      and row["item"] == item["id"], (row["x"], row["source"], row["item"]))
check("een gezicht uit items.json kan niet als getekend gezicht opgeslagen worden", row["how"] == "chosen", row["how"])
status, _, data = post([{"face": face["face"], "label": ""}])
check("lege keuze wist het label", status == 200 and face["face"] not in stored())

# ---- een kapotte labels.csv (bijvoorbeeld in een ander programma veranderd): opslaan geeft een duidelijke melding en
# overschrijft labels.csv niet, zodat de labelaar een reservekopie kan terugzetten zonder dat er iets kwijt is
LABELS = os.path.join(DEMO, "labels.csv")
with open(LABELS, "rb") as f:
    keep = f.read()
broken = b"a,b\n1,2\n"   # andere kolommen dan face, label, ...
with open(LABELS, "wb") as f:
    f.write(broken)
status, _, data = post([{"face": face["face"], "label": "unknown", "labeler": "Test"}])
with open(LABELS, "rb") as f:
    after = f.read()
check("opslaan bij een kapotte labels.csv: duidelijke melding, en labels.csv blijft zoals het was",
      status == 500 and "niet de goede kolommen" in json.loads(data).get("error", "") and after == broken, (status, data[:100]))
with open(LABELS, "wb") as f:
    f.write(keep)

# ---- de soort bestand en de beveiligingsregels voor de browser
for path, want in [("/web/", "text/html; charset=utf-8"), ("/web/app.js", "text/javascript; charset=utf-8"),
                   ("/web/style.css", "text/css; charset=utf-8"), ("/items.json", "application/json; charset=utf-8"),
                   (image, "image/jpeg" if image.endswith(".jpg") else "image/png"), ("/api/labels", "application/json; charset=utf-8")]:
    _, headers, _ = req("GET", path)
    check(f"GET {SHOWN.get(path, path)} heeft Content-Type {want}", headers.get("Content-Type") == want, headers.get("Content-Type"))
for path in ["/web/", "/api/labels"]:
    _, headers, _ = req("GET", path)
    policy = headers.get("Content-Security-Policy", "")
    check(f"GET {path}: de browser mag de pagina niet in een andere website tonen en laadt alleen eigen bestanden",
          headers.get("X-Content-Type-Options") == "nosniff" and headers.get("X-Frame-Options") == "DENY"
          and "default-src 'self'" in policy and "frame-ancestors 'none'" in policy, dict(headers))
_, headers, _ = req("GET", "/api/labels")
check("de labels worden nooit uit de cache van de browser gehaald (no-store)", headers.get("Cache-Control") == "no-store", headers.get("Cache-Control"))

# ---- ping en een tweede start
status, _, data = req("GET", "/api/ping")
info = json.loads(data)
check("ping geeft de map van de app", os.path.realpath(info.get("folder", "")) == os.path.realpath(DEMO), info)
start = time.time()
out = subprocess.run([PYTHON, "app.py"], cwd=DEMO, capture_output=True, text=True, timeout=30,
                     env={**os.environ, "LABELAPP_NO_BROWSER": "1"}).stdout
check("tweede start opent de draaiende app in plaats van een tweede server", "draait al" in out and time.time() - start < 10,
      out.strip().splitlines()[:2])
