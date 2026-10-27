# Tests van de labelapp

## Waar deze map voor is

De labelapp in de map `labeling/` is het programma waarmee de labelaar bij elk gevonden gezicht kiest wie het is. De
labelapp bestaat uit twee delen: een kleine webserver (`labeling/app.py`) die de keuzes in `labeling/labels.csv`
bewaart, en een labelpagina in de browser (`labeling/web/index.html`, `app.js` en `style.css`).

De tests in deze map controleren automatisch of de labelapp nog doet wat hij moet doen. Een test doet wat een
labelaar zou doen (een keuze maken, op Volgende klikken, de app sluiten en weer starten, het venster kleiner maken) en
kijkt daarna of de labelapp het goede antwoord geeft. Zo merk je het meteen als een verandering in de labelapp iets
anders kapotmaakt, zonder dat iemand alles met de hand hoeft na te lopen.

Draai de tests na elke verandering in `labeling/`, en ook nadat `labeling/items.json` opnieuw gemaakt is (bijvoorbeeld
voor nieuwe video's). De tests zoeken de items die ze nodig hebben zelf op in `items.json` (bijvoorbeeld "een still met
drie of meer gezichten" of "een track met een groot gezicht"), dus de tests werken met elke `items.json`.

## In het kort

Open Terminal in de hoofdmap van het project en typ:

```bash
bash tests/run_tests.sh
```

Na ongeveer drie minuten staat onderaan `TOTAAL: ... tests, 0 mislukt` als alles goed is.

## Wat je nodig hebt

Deze drie programma's moeten op de computer staan. Tussen haakjes staat hoe je in Terminal ziet of het programma er
is en welke versie het heeft.

- **Python 3**, versie 3.8 of nieuwer (`python3 --version`). De labelapp zelf is in Python geschreven, en de tests van
  de webserver ook. Op een Mac vraagt de computer bij de eerste keer `python3` soms om de "command line developer
  tools" te installeren; klik dan op Installeer.
- **Node**, versie 22 of nieuwer (`node --version`), te downloaden van [nodejs.org](https://nodejs.org) (kies de
  versie "LTS"). Node draait de tests van de labelpagina.
- **Google Chrome**, de gewone browser, te downloaden van [google.com/chrome](https://www.google.com/chrome/). De tests
  starten een eigen Chrome zonder venster, met een eigen profiel (zie "Woorden" onderaan). Een Chrome die je zelf open
  hebt, merkt daar niets van.

Het script `run_tests.sh` draait op een Mac en op Linux. Er hoeft verder niets geïnstalleerd te worden.

## Alle tests draaien

1. Open Terminal (op de Mac: Programma's > Hulpprogramma's > Terminal).
2. Ga naar de hoofdmap van het project, de map waarin `labeling/` en `tests/` staan. Typ daarvoor `cd ` (met een
   spatie erachter), sleep de projectmap vanuit de Finder in het Terminal-venster en druk op Enter.
3. Typ `bash tests/run_tests.sh` en druk op Enter.

Alle tests samen duren ongeveer drie minuten. Laat het Terminal-venster zolang open. Je eigen labelapp mag gewoon
blijven draaien, en je kunt intussen ander werk doen. Start de tests niet twee keer tegelijk.

## De uitkomst lezen

Na elk testbestand verschijnt één regel met het aantal geslaagde en mislukte controles, en aan het eind het totaal:

```
app_01_basis.mjs: 14 geslaagd, 0 mislukt
app_02_herstart.mjs: 6 geslaagd, 0 mislukt
...
test_server_start.py (Python 3.12): 19 geslaagd, 0 mislukt

TOTAAL: 310 tests, 0 mislukt
```

- **Geslaagd**: de labelapp deed bij die controle wat hij moet doen.
- **Mislukt**: de labelapp deed iets anders dan verwacht. Die controle staat dan boven de regel van het testbestand,
  met `FAIL` ervoor en tussen haakjes wat de test zag. Een voorbeeld:
  `FAIL  1366x657 track: alles past zonder scrollen  ({"panelOverflow":12, ...})` betekent dat de labelaar bij een
  venster van 1366 bij 657 pixels in het blok rechts 12 pixels zou moeten scrollen.
- **Overgeslagen**: een regel met `OVERGESLAGEN` betekent dat `items.json` geen item heeft waarmee die controle kan
  (bijvoorbeeld geen still met meer gezichten). Een overgeslagen controle telt niet mee als geslaagd en niet als mislukt.

Voor wie het script vanuit een ander programma start: het script stopt met exitcode 0 als alles geslaagd is en met
exitcode 1 als er iets mislukt is.

## Als er iets mislukt

1. Lees de regel met `FAIL`: de naam van de controle zegt wat er niet goed ging.
2. Draai alleen dat testbestand nog een keer, door de naam erachter te zetten (zonder `.mjs` of `.py` mag ook):

   ```bash
   bash tests/run_tests.sh layout_02_balken
   ```

   Meer testbestanden tegelijk kan ook: `bash tests/run_tests.sh app_01_basis layout_02_balken`.
3. Mislukt de controle weer, dan is er waarschijnlijk echt iets mis in de labelapp. Stuur de regels met `FAIL` naar wie
   de labelapp onderhoudt. Verander de test niet om hem te laten slagen; de test laat juist zien wat de labelaar zou
   merken.
4. Stopt het script meteen met `FOUT:`, dan ontbreekt er iets (Python, Node, Chrome of een bestand in `labeling/`). De
   melding zegt wat er ontbreekt.

## De echte labels blijven onaangeroerd

`run_tests.sh` werkt nooit in `labeling/` zelf. Het script maakt eerst een tijdelijke map met een kopie van
`labeling/app.py`, `items.json`, `automatic_labels.csv`, `web/` en `images/`. Het bestand `labels.csv` (de keuzes van de
labelaar) en de map `backups/` gaan nooit mee. Alle tests werken met die kopie (de "demo-app"). Daarna doet het script dit:

1. Het start de demo-app zonder browservenster. De labelapp kiest zelf een vrije poort tussen 8765 en 8784 en schrijft
   die in `.labelapp.port` in de map van de kopie. Draait je eigen labelapp ook, dan krijgt de demo-app gewoon een
   andere poort.
2. Het start een eigen Chrome zonder venster, met een eigen profiel en een eigen poort voor de besturing.
3. Het draait de testbestanden in een vaste volgorde. Elk testbestand begint met een schone start: geen `labels.csv`
   en een lege opslag in de browser (met alleen de naam van de labelaar, en de aantekening dat de uitleg al gezien is).
4. Aan het eind stopt het alleen de programma's die het zelf gestart heeft (op procesnummer; andere programma's, ook
   een andere labelapp of je eigen Chrome, worden nooit gestopt) en gooit het de tijdelijke map weg. Dat gebeurt ook
   als je het script halverwege stopt met Ctrl+C.

## Wat de tests controleren

| Testbestand | Wat er gecontroleerd wordt |
|---|---|
| `app_01_basis.mjs` | De pagina laadt; een keuze met de muis of met een toets komt meteen in `labels.csv`, met de goede kolommen en de naam van de labelaar; Volgende waarschuwt eerst en maakt daarna de gezichten zonder keuze figurant; bij een track gaat de app na een keuze vanzelf door; ← gaat terug; de knop "Naar eerste item dat nog niet af is". |
| `app_02_herstart.mjs` | De app opnieuw starten: de labels blijven bewaard, er komt een reservekopie in `backups/`, de pagina gaat verder bij het laatst bekeken item; Beeld lichter staat standaard aan en de toets L zet het uit en aan; als de app niet draait, geeft een keuze een rode waarschuwing. |
| `app_03_storing.mjs` | Keuzes die gemaakt zijn terwijl het venster van de app dicht was, komen later alsnog in `labels.csv` (bij de volgende keuze, of na het opnieuw openen van de pagina). |
| `app_04_naam.mjs` | Zonder naam van de labelaar wordt niets opgeslagen; de pagina geeft geen foutmeldingen of beveiligingsmeldingen (bijvoorbeeld een bestand dat niet geladen mag worden). |
| `app_05_snel.mjs` | Tien snelle wijzigingen voor hetzelfde gezicht: de laatste keuze staat in `labels.csv`. |
| `app_06_toetsen.mjs` | Een ingedrukt gehouden toets, Ctrl, Cmd of Alt met een cijfer en de spatie doen niets; de pijltjes bladeren alleen; een klik op een knopje of een kader kiest welk gezicht aan de beurt is; na het laatste gezicht gaat de app terug naar het eerste open gezicht; automatische figuranten staan als `auto` in `labels.csv` en overschrijven nooit een bestaand label; een naam zonder letters telt niet. |
| `app_07_gedrag.mjs` | Enter in het naamvak; een naam van alleen cijfers; een dubbelklik telt één keer; de regel "Net gekozen"; Enter slaat een track zonder keuze niet over; de teller en de voortgangsknoppen bovenaan; de grote foto van een acteur; de grootte van de uitvergroting; de groene balk als alles af is. |
| `app_08_volgende.mjs` | De knop Volgende werkt bij een track net als Enter (gaat niet door zonder keuze), → slaat wel over; bij een still waarschuwt Volgende eerst, en opnieuw na een keuze tussendoor; de groene balk zegt dat je `labels.csv` naar Marc stuurt. |
| `app_09_lichter.mjs` | Beeld lichter meet steeds het gezicht dat in beeld is, ook als het beeld kleiner is opgeslagen dan de video (bij 4K-video's); cijfers via de toets zelf (AZERTY-toetsenbord, numeriek blok); oude keuzes voor een ander kader worden niet opgeslagen; de pagina komt niet ongezien uit de cache; een `labels.csv` in een andere tekenset geeft de bekende uitleg; de keuze voor Beeld lichter blijft bewaard. |
| `app_10_uitleg.mjs` | De uitleg (rondleiding) opent de eerste keer vanzelf, elke stap staat bij acht venstermaten helemaal in beeld, toetsen bladeren alleen door de uitleg, de browser onthoudt dat de uitleg gezien is, de uitleg stopt het tekenen, en zonder naam staat na het sluiten de cursor in het naamvak. |
| `app_11_tekenen.mjs` | De grijze kaders bij een track; een gemist gezicht tekenen met de muis (bij een track en bij een still), kiezen wie het is, weghalen (knop Weghalen, Delete of Backspace), en terugzien na herladen; de controles in `app.py` op getekende kaders. |
| `app_12_overig.mjs` | Het laatste item; labels die buiten de pagina veranderd zijn; de meldingen als `app.py` een keuze niet aanneemt; een kapotte `labels.csv` bij het openen; een aangeklikte knop houdt geen focus; de waarschuwing bij het sluiten van de pagina met keuzes die nog niet opgeslagen zijn; een tweede tabblad met de labelpagina stopt het eerste tabblad. |
| `layout_01_past.mjs` | Alles past op één scherm zonder scrollen, bij zeven venstermaten (van 1920 × 950 tot 1024 × 580 pixels) en zeven soorten items, ook met getekende gezichten. |
| `layout_02_balken.mjs` | Hetzelfde met de rode balk (keuzes niet opgeslagen), de gele waarschuwing rechts, getekende gezichten en de groene balk, bij dezelfde zeven venstermaten. |
| `test_server_security.py` | De webserver levert alleen de bestanden die de labelpagina nodig heeft (ook niet via omwegen als `../`), beantwoordt alleen het eigen adres, laat alleen de eigen labelpagina opslaan, weigert kapotte of te grote verzoeken netjes, overschrijft een kapotte `labels.csv` nooit, neemt bestand, frame en kader altijd uit `items.json`, schoont de naam op en stuurt de juiste soort bestand en beveiligingsregels mee. |
| `test_server_start.py` | Twee starts tegelijk geven één app; de keuze van de poort en `.labelapp.port`; op een drukke computer neemt de app toch alle verbindingen van de browser aan; een label dat niet meer bij `items.json` past (ook een getekend gezicht); een BOM, een vergrendelde of een kapotte `labels.csv`; de reservekopieën; het opschonen van de naam. Deze test draait met twee Python-versies als die er zijn (bijvoorbeeld `python3` en die in `.venv/`), omdat een labelaar een andere Python kan hebben. |

De bestanden `app_*.mjs` en `layout_*.mjs` besturen de labelpagina in Chrome. De gedeelde hulpmiddelen daarvoor staan
in `lib.mjs`. De bestanden `test_server_*.py` praten rechtstreeks met de webserver en gebruiken alleen standaard-Python.

## Instellen

Vindt het script Python, Node of Chrome niet, of wil je een andere versie gebruiken, zet dan het pad in een
omgevingsvariabele (een instelling die je vóór de opdracht typt):

```bash
PYTHON=python3.12 CHROME="/pad/naar/chrome" NODE=/pad/naar/node bash tests/run_tests.sh
```

Zonder `CHROME` zoekt het script eerst naar `/Applications/Google Chrome.app` (Mac) en daarna naar `google-chrome` of
`chromium` (Linux). De tijdelijke map komt in de gewone map voor tijdelijke bestanden van de computer; met `TMPDIR=...`
ervoor kies je een andere map.

## Een test toevoegen

Een nieuwe browsertest is een nieuw bestand `app_<nummer>_<onderwerp>.mjs` naar het voorbeeld van een bestaand
testbestand. Begin met `const page = await connect(); await page.fresh();` (een schone start), zoek de items op met
`page.find(...)` op hun soort en eigenschappen (nooit een vast itemnummer, tracknummer of videonaam), en schrijf elke
controle met `check("wat er gecontroleerd wordt", uitkomst, details)`. Wacht na een keuze met `await page.saved()` tot
de keuze in `labels.csv` staat, voordat de test `labels.csv` leest. Zet de naam van het nieuwe bestand daarna in de
lijst in `run_tests.sh`. Een test die de opslag van de browser leegmaakt, zet ook `uitleg-gezien` op `1`
(`page.fresh()` doet dat al), anders opent de uitleg en zit die in de weg.

## Woorden

- **Track**: een stukje video waarin de computer één gezicht een tijdje gevolgd heeft. De labelaar ziet daar één beeld
  van en kiest één keer.
- **Still**: een losse foto uit de film, vaak met meer gezichten.
- **Chrome zonder venster** (in het Engels "headless"): een gewone Chrome die geen venster op het scherm toont. De tests
  besturen die Chrome via het DevTools-protocol, de manier waarop ook de ontwikkelhulpmiddelen van Chrome met een
  pagina praten.
- **Poort**: een nummer waarop een programma op deze computer bereikbaar is, zoals `127.0.0.1:8765`.
- **Procesnummer**: het nummer dat de computer aan elk draaiend programma geeft. Het script onthoudt de nummers van de
  programma's die het zelf startte, en stopt alleen die.
- **BOM**: een onzichtbaar teken dat bijvoorbeeld Excel vooraan in een CSV-bestand zet.
