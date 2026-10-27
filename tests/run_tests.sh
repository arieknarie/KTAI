#!/bin/bash
# Draait alle tests van de labelapp (de map labeling/) en zegt per testbestand hoeveel controles geslaagd en mislukt zijn.
#
# Gebruik, vanuit de hoofdmap van het project:   bash tests/run_tests.sh
# Alleen een paar testbestanden draaien kan ook:  bash tests/run_tests.sh app_01_basis layout_02_balken
#
# Wat dit script doet:
# 1. Het maakt een tijdelijke map met een verse kopie van labeling/: app.py, items.json, automatic_labels.csv, web/ en
#    images/. labels.csv en backups/ gaan nooit mee, zodat de echte labels nooit geraakt worden.
# 2. Het start die kopie van de app (zonder browservenster) en een eigen Chrome zonder venster (headless), met een eigen
#    profiel en een eigen poort. Een Chrome of een labelapp die je zelf open hebt, merkt daar niets van.
# 3. Het draait de testbestanden in een vaste volgorde en telt de regels PASS (geslaagd) en FAIL (mislukt).
# 4. Het stopt daarna alleen de programma's die het zelf gestart heeft (op procesnummer) en gooit de tijdelijke map weg.
#
# Instellen kan met omgevingsvariabelen: PYTHON (standaard python3), NODE (standaard node) en CHROME (het pad naar
# Google Chrome of Chromium, als het script Chrome niet zelf vindt).
# Het script stopt met exitcode 1 als er iets mislukt is, en met 0 als alles geslaagd is.

set -u
export PYTHONDONTWRITEBYTECODE=1   # geen __pycache__-mappen

TESTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO="$(dirname "$TESTS")"
SOURCE="$REPO/labeling"
PY="${PYTHON:-python3}"
NODE_BIN="${NODE:-node}"

stop_here() { echo "FOUT: $1" >&2; exit 1; }

# ---------- controleren wat nodig is ----------

command -v "$PY" >/dev/null 2>&1 || stop_here "Python 3 niet gevonden (zie tests/README.md, 'Wat je nodig hebt')."
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null || stop_here "Python 3.8 of nieuwer is nodig."
command -v "$NODE_BIN" >/dev/null 2>&1 || stop_here "Node niet gevonden (zie tests/README.md, 'Wat je nodig hebt')."
"$NODE_BIN" -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)' || stop_here "Node 22 of nieuwer is nodig."
find_chrome() {
  if [ -n "${CHROME:-}" ]; then echo "$CHROME"; return; fi
  local mac="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  if [ -x "$mac" ]; then echo "$mac"; return; fi
  local name
  for name in google-chrome google-chrome-stable chromium chromium-browser; do
    if command -v "$name" >/dev/null 2>&1; then command -v "$name"; return; fi
  done
}
CHROME_BIN="$(find_chrome)"
[ -n "$CHROME_BIN" ] && [ -x "$CHROME_BIN" ] || stop_here "Google Chrome niet gevonden. Zet het pad in CHROME (zie tests/README.md)."
[ -f "$SOURCE/app.py" ] && [ -f "$SOURCE/items.json" ] || stop_here "labeling/app.py of labeling/items.json ontbreekt."

# ---------- de tijdelijke map en het opruimen ----------

WORK="$(mktemp -d "${TMPDIR:-/tmp}/labelapp_tests.XXXXXX")" || stop_here "kan geen tijdelijke map maken"
WORK="$(cd "$WORK" && pwd -P)"
DEMO="$WORK/labeling"
CHROME_PID=""

is_our_app() {   # draait het proces met dit nummer nog, en is het een labelapp (app.py)?
  [ -n "$1" ] && kill -0 "$1" 2>/dev/null && ps -p "$1" -o command= 2>/dev/null | grep -q "app.py"
}
stop_app() {     # stopt alleen de demo-app waarvan het procesnummer in app.pid staat
  local pid
  pid="$(cat "$WORK/app.pid" 2>/dev/null)"
  if is_our_app "$pid"; then
    kill "$pid" 2>/dev/null
    for _ in $(seq 50); do kill -0 "$pid" 2>/dev/null || break; sleep 0.1; done
  fi
}
cleanup() {
  stop_app
  if [ -n "$CHROME_PID" ] && kill -0 "$CHROME_PID" 2>/dev/null; then
    kill "$CHROME_PID" 2>/dev/null
    wait "$CHROME_PID" 2>/dev/null
  fi
  sleep 0.5
  rm -rf "$WORK"
}
trap cleanup EXIT
trap 'exit 130' INT TERM

# ---------- de kopie van labeling/ en de demo-app ----------

echo "Kopie van labeling/ maken (zonder labels.csv en backups/) ..."
mkdir -p "$DEMO"
cp "$SOURCE/app.py" "$SOURCE/items.json" "$DEMO/"
[ -f "$SOURCE/automatic_labels.csv" ] && cp "$SOURCE/automatic_labels.csv" "$DEMO/"
cp -R "$SOURCE/web" "$DEMO/web"
cp -R "$SOURCE/images" "$DEMO/images"

wait_for_app() {   # wacht tot de app uit $DEMO antwoordt (hoogstens 15 seconden)
  "$PY" - "$DEMO" <<'EOF'
import json, os, sys, time, urllib.request
folder = os.path.realpath(sys.argv[1])
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
for attempt in range(150):
    try:
        port = int(open(os.path.join(folder, ".labelapp.port")).read().strip())
        info = json.loads(opener.open(f"http://127.0.0.1:{port}/api/ping", timeout=1).read().decode("utf-8"))
        if os.path.realpath(info["folder"]) == folder:
            sys.exit(0)
    except Exception:
        pass
    time.sleep(0.1)
sys.exit(1)
EOF
}
start_app() {
  (cd "$DEMO" && LABELAPP_NO_BROWSER=1 exec "$PY" -u app.py >> "$WORK/app.log" 2>&1) &
  echo $! > "$WORK/app.pid"
  wait_for_app || { cat "$WORK/app.log" >&2; stop_here "de demo-app startte niet"; }
}
ensure_app() {     # een test kan de app stoppen en weer starten; antwoordt hij niet meer, dan wordt hij opnieuw gestart
  if is_our_app "$(cat "$WORK/app.pid" 2>/dev/null)" && wait_for_app; then return; fi
  stop_app
  start_app
}
start_app

# ---------- de eigen Chrome ----------

CDP_PORT="$("$PY" -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')"
"$CHROME_BIN" --headless=new --disable-gpu --no-first-run --no-default-browser-check --disable-extensions \
  --no-proxy-server --remote-debugging-port="$CDP_PORT" --user-data-dir="$WORK/chrome-profiel" \
  --window-size=1440,860 about:blank > "$WORK/chrome.log" 2>&1 &
CHROME_PID=$!
CDP="http://127.0.0.1:$CDP_PORT"
"$PY" - "$CDP" <<'EOF' || { cat "$WORK/chrome.log" >&2; stop_here "Chrome startte niet"; }
import sys, time, urllib.request
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
for attempt in range(150):
    try:
        opener.open(sys.argv[1] + "/json/version", timeout=1).read()
        sys.exit(0)
    except Exception:
        time.sleep(0.1)
sys.exit(1)
EOF

# ---------- de tests ----------

TOTAL=0; FAILED=0; SKIPPED=0
run() {   # run <naam> <commando ...>: draait één testbestand en telt de uitkomst
  local name="$1"; shift
  local out code pass fail skip
  out="$("$@" 2>&1)"; code=$?
  pass=$(grep -c "^PASS" <<<"$out"); fail=$(grep -c "^FAIL" <<<"$out"); skip=$(grep -c "^OVERGESLAGEN" <<<"$out")
  grep -E "^(FAIL|OVERGESLAGEN)" <<<"$out" | sed 's/^/    /'
  if [ "$code" -ne 0 ]; then   # het testbestand stopte met een fout: de rest van dat bestand is niet gedraaid
    echo "    FAIL  $name stopte met een fout:"
    { grep -E "Error|fout" <<<"$out" | head -2; grep -v -E "^(PASS|FAIL|OVERGESLAGEN)" <<<"$out" | grep -v -E "Error|fout" | tail -3; } | sed 's/^/      /'
    fail=$((fail + 1))
  fi
  TOTAL=$((TOTAL + pass + fail)); FAILED=$((FAILED + fail)); SKIPPED=$((SKIPPED + skip))
  if [ "$skip" -gt 0 ]; then echo "$name: $pass geslaagd, $fail mislukt, $skip overgeslagen"
  else echo "$name: $pass geslaagd, $fail mislukt"; fi
}

# alleen de testbestanden die als argument genoemd zijn (zonder argumenten: allemaal)
wanted() { [ ${#ONLY[@]} -eq 0 ] || [[ " ${ONLY[*]} " == *" $1 "* ]]; }
ONLY=()
for name in "$@"; do ONLY+=("$(basename "${name%.*}")"); done

echo "De tests draaien (dit duurt een paar minuten) ..."
for test in app_01_basis app_02_herstart app_03_storing app_04_naam app_05_snel app_06_toetsen app_07_gedrag \
            app_08_volgende app_09_lichter app_10_uitleg app_11_tekenen app_12_overig layout_01_past layout_02_balken; do
  wanted "$test" || continue
  ensure_app
  run "$test.mjs" "$NODE_BIN" "$TESTS/$test.mjs" "$CDP" "$DEMO" "$WORK" "$PY"
done
if wanted test_server_security; then
  ensure_app
  run "test_server_security.py" "$PY" "$TESTS/test_server_security.py" "$DEMO" "$PY"
fi

# De starttest draait met twee Python-versies als die er zijn: de Python van hierboven en een andere versie
# (bijvoorbeeld die in .venv/ van het project), want de labelaar kan een andere Python hebben.
VERSIONS=" "; COUNT=0
for candidate in "$PY" "$REPO/.venv/bin/python" /usr/bin/python3 python3.8 python3.9 python3.10 python3.11 python3.12 python3.13 python3.14; do
  wanted test_server_start || break
  [ "$COUNT" -ge 2 ] && break
  path="$(command -v "$candidate" 2>/dev/null)" || continue
  version="$("$path" -c 'import sys; print("%d.%d" % sys.version_info[:2]) if sys.version_info >= (3, 8) else sys.exit(1)' 2>/dev/null)" || continue
  case "$VERSIONS" in *" $version "*) continue ;; esac
  VERSIONS="$VERSIONS$version "; COUNT=$((COUNT + 1))
  START="$WORK/start_$COUNT"
  mkdir -p "$START"
  cp "$SOURCE/app.py" "$SOURCE/items.json" "$START/"
  run "test_server_start.py (Python $version)" "$path" "$TESTS/test_server_start.py" "$START"
done

echo
[ "$SKIPPED" -gt 0 ] && echo "OVERGESLAGEN: $SKIPPED (items.json heeft voor die controles geen geschikt item)"
echo "TOTAAL: $TOTAL tests, $FAILED mislukt"
[ "$FAILED" -eq 0 ]
