#!/bin/bash
# Start de labelapp op een Mac. Dubbelklik op dit bestand (zie README.md).
cd "$(dirname "$0")" || exit 1
# Op een Mac zonder Python bestaat /usr/bin/python3 alleen als verwijzing naar de ontwikkelaarstools van Apple.
# Daarom wordt eerst gekeken of er echt een Python 3.8 of nieuwer is.
if command -v python3 >/dev/null 2>&1 && \
   { [ "$(command -v python3)" != /usr/bin/python3 ] || xcode-select -p >/dev/null 2>&1; } && \
   python3 -c 'import sys; sys.exit(sys.version_info < (3, 8))' >/dev/null 2>&1; then
    python3 app.py
else
    echo "Python 3.8 of nieuwer is niet gevonden op deze computer."
    echo "Installeer Python eerst; zie README.md, stap 1."
fi
echo
read -r -p "Druk op Enter om dit venster te sluiten."
