# Zelf draaien

[← terug naar het overzicht](../README.md)

Dit document is voor wie de programma's van het project zelf opnieuw wil
draaien op de eigen computer. Voor het labelen is dit **niet** nodig: de
labelapp heeft alleen Python nodig, zie de
[handleiding voor de labelaar](../labeling/README.md).

Om het werk te bekijken hoef je de programma's ook niet te draaien. De
uitkomsten van stap 1 staan al in het project: de gevonden gezichten en de
tracks in `data/tracks/` (een track is één gezicht dat we door opeenvolgende
beelden volgen) en de controle van alle tracks in `data/audit/`. Ook alles wat
de labelapp voor stap 2 nodig heeft, staat er al, in `labeling/`. Van de
controle staat één deel niet op GitHub: de 352 vellen met uitsneden waarmee we
alle tracks met het oog gecontroleerd hebben (de map `data/audit/alle_tracks/`, samen ongeveer
100 MB). Die vellen maak je zelf opnieuw met `code/check_all_tracks.py` (zie
[De programma's](#de-programmas-in-deze-volgorde)). De labels van de labelaar
komen tijdens en na het labelen in de map `labels/`.


## Belangrijk: de uitkomsten liggen vast

De controle van alle tracks, de labels van de labelaar en de getallen in de
uitleg horen bij precies de bestanden die nu in `data/` en `labeling/` staan.
Draai je `code/track_faces.py` opnieuw op een andere computer of met andere
versies van de programma's, dan kan een heel klein verschil (bijvoorbeeld in
hoe een video wordt uitgelezen) al andere kaders en andere tracknummers geven.
Eén gezicht meer of minder in het eerste fragment geeft bijna alle tracks een
ander nummer. Dat is een probleem, want de controle zegt per tracknummer in
welke beelden een track op een ander gezicht of op iets anders staat, en op
die plekken knipt `track_faces.py` de track. Past de controle niet bij de
nieuwe tracks, dan knipt het programma niets en meldt het dat de controle
opnieuw moet.

Daarom zijn de belangrijke bestanden vastgelegd met een controlegetal (een
sha256: een lange code die verandert zodra er ook maar iets in het bestand
verandert). Die controlegetallen staan in het bestand `checksums.sha256`, in
20 regels: 18 voor bestanden (de drie video's, het model dat de gezichten
vindt, de uitkomsten van stap 1, de controle en de bestanden van de
labelapp) en 2 voor mappen met plaatjes (`labeling/images/` en `pictures/`,
met één controlegetal per map). De programma's gaan zo met de vastgelegde
bestanden om:

- `code/check_all_tracks.py`, `code/step1_images.py` en
  `code/make_label_items.py` controleren eerst of de gevonden gezichten in
  `data/tracks/` nog de vastgelegde bestanden zijn. Zo niet, dan stoppen ze
  met een duidelijke melding.
- Geeft `code/track_faces.py` of `code/make_label_items.py` een andere
  uitkomst dan vastgelegd, dan overschrijft het programma de vastgelegde
  bestanden niet. Het schrijft de nieuwe uitkomst ernaast, bijvoorbeeld als
  `detections_0.3.nieuw.csv`. `make_label_items.py` laat dan ook de plaatjes
  in `labeling/images/` staan zoals ze waren, want die horen bij de
  vastgelegde `labeling/items.json`. Alleen met de optie `--overschrijven`
  vervangt het programma de vastgelegde bestanden. Git (het programma dat de
  versies van het project bijhoudt) negeert zulke `.nieuw`-bestanden (de
  regel `*.nieuw.*` in `.gitignore` in de hoofdmap), zodat een nieuwe uitkomst
  niet per ongeluk op GitHub komt.
- `code/make_label_items.py` rekent eerst alles uit en schrijft helemaal
  niets als er op deze computer al keuzes van de labelapp zijn die niet meer
  zouden passen bij wat de labelapp dan toont. Zo gaat er geen labelwerk
  verloren.

De labelapp bewaart de keuzes in `labeling/labels.csv`, op de computer waarop
de app draait. Dat bestand gaat nooit mee naar GitHub (het staat in
`labeling/.gitignore`). De labelaar stuurt `labels.csv` tussendoor en aan het
eind naar Marc, en Marc zet het bestand in de map `labels/` (zie
[`labels/README.md`](../labels/README.md)). `make_label_items.py` kijkt alleen
naar `labeling/labels.csv`, niet naar de labels in `labels/`. Ook de labels in
`labels/` passen alleen bij de vastgelegde bestanden, want elke keuze hoort bij
een vast tracknummer.

Het bestand `data/tracks/run_info.json` is niet vastgelegd en wordt vervangen
elke keer dat `track_faces.py` draait. Daarin schrijft het programma alleen op
hoe die keer gedraaid is: de versies van de programma's, de instellingen en de
controlegetallen van de video's, het model en de uitkomsten.

Wil je bewust een nieuwe versie vastleggen, bedenk dan dat de controle van
alle tracks en het labelen daarna helemaal opnieuw moeten. De programma's
werken alleen met vastgelegde bestanden verder. Leg daarom na elke stap
hieronder de nieuwe bestanden vast met `code/check_setup.py --vastleggen`:

1. Draai `track_faces.py --overschrijven`. Past de oude controle niet bij de
   nieuwe tracks, dan knipt het programma nog niets.
2. Maak met `check_all_tracks.py` nieuwe vellen, controleer alle tracks
   opnieuw met het oog en zet de uitkomst in
   `data/audit/controle_alle_tracks.csv`. In de kolom `probleemframes` komen de
   beelden waarin een track op een ander gezicht of op iets anders staat.
3. Draai `track_faces.py --overschrijven` nog een keer. Nu knipt het programma
   de tracks op de plekken uit de nieuwe controle.
4. Draai `make_label_items.py --overschrijven`, en ook `--forceer` als er al
   keuzes in `labeling/labels.csv` staan die weg mogen.

Ook de plaatjes in `docs/` en de getallen in de uitleg moeten daarna opnieuw.
Met `--vastleggen` schrijft `check_setup.py` de controlegetallen op elke
computer op precies dezelfde manier weg, ook op Windows (Windows zet aan het
eind van elke regel normaal andere onzichtbare tekens dan een Mac). Zo blijven
de controlegetallen op alle computers kloppen.

Sla de vastgelegde CSV-bestanden nooit op vanuit Excel of een ander
rekenprogramma, ook niet als je niets veranderd hebt. Zo'n programma slaat het
bestand net iets anders op (bijvoorbeeld met een onzichtbaar teken aan het
begin, of met andere regeleinden). De getallen in het bestand zijn dan nog
hetzelfde, maar het controlegetal niet meer, en dan weigeren de programma's
verder te werken. Bekijken in Excel mag wel, zolang je het bestand daarna
zonder opslaan sluit.


## Installeren

Je hebt Python 3.12 nodig. Typ in een terminal (het venster waarin je
opdrachten typt: op een Mac het programma Terminal, op Windows de
Opdrachtprompt), in de map van het project (`KTAI`, of
`KTAI-facenet-stress-tests-v2` als je het project als ZIP-bestand van GitHub
gedownload hebt):

Op een Mac of Linux:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Op Windows:

```bash
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

Zo komt er een aparte map `.venv` met Python en de pakketten die de programma's
gebruiken. In `requirements.txt` staan de precieze versies waarmee wij gewerkt
hebben: MediaPipe 1.1.1 (vindt de gezichten), pandas 3.0.6 en NumPy 2.5.4
(rekenen met tabellen en getallen) en OpenCV 5.0.0.93 (leest de video's en
plaatjes; het pakket heet opencv-contrib-python).

Op Windows gebruik je in de commando's hieronder steeds `.venv\Scripts\python`
in plaats van `.venv/bin/python`.

Het model waarmee MediaPipe gezichten vindt, staat al in het project
(`models/blaze_face_full_range.tflite`). Ontbreekt het bestand, download het
dan zo:

```bash
curl -o models/blaze_face_full_range.tflite https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_full_range/float16/latest/blaze_face_full_range.tflite
```

Controleer daarna of het hetzelfde model is als het model waarmee wij gewerkt
hebben. De downloadlink wijst namelijk naar de nieuwste versie, en een andere
versie kan andere gezichten vinden:

```bash
shasum -a 256 models/blaze_face_full_range.tflite
```

Op Windows typ je daarvoor
`certutil -hashfile models\blaze_face_full_range.tflite SHA256`.

De uitkomst moet
`3698b18f063835bc609069ef052228fbe86d9c9a6dc8dcb7c7c2d69aed2b181b` zijn.

Controleer daarna of alles klopt:

```bash
.venv/bin/python code/check_setup.py
```

Dit programma kijkt in ongeveer een kwart minuut (op een oudere computer wat
langer) of de versies kloppen, of de video's, het model en de vastgelegde
uitkomsten dezelfde zijn als bij ons (via `checksums.sha256`), of OpenCV van
elke video precies het goede aantal beelden leest, en of OpenCV in elk beeld
precies dezelfde pixels ziet als bij ons. Dat laatste is belangrijk: leest
jouw computer de video's een heel klein beetje anders uit, dan kan
`code/track_faces.py` bij jou andere gezichten vinden. Gebruik in dat geval de vastgelegde uitkomsten en
draai `code/track_faces.py` niet opnieuw. Het programma kijkt ook of de
plaatjes van de labelapp (in `labeling/images/`) en de foto's in `pictures/`
nog dezelfde zijn als bij ons. Daarvoor staat in `checksums.sha256` één
controlegetal per map. Zo valt een plaatje op dat ontbreekt of veranderd is,
en in `pictures/` ook een foto die erbij gezet is. (In `labeling/images/` telt
alleen mee wat de labelapp laat zien; een extra plaatje daar doet niets.) Tot
slot kijkt het programma of er geen kopieën als `bestand 2.jpg` van een
clouddienst in de map staan. Staat er aan het eind *Alles in orde.*, dan is je
computer klaar.

Op Windows en Linux hebben we het installeren en de programma's niet
uitgeprobeerd; het zou daar wel moeten werken.


## De programma's, in deze volgorde

```bash
.venv/bin/python code/track_faces.py          # stap 1: gezichten zoeken, volgen en knippen (data/tracks/)
.venv/bin/python code/check_all_tracks.py     # de vellen voor de controle van alle tracks (data/audit/alle_tracks/)
.venv/bin/python code/detector_steekproef.py  # hoeveel duidelijke gezichten de detector vindt
.venv/bin/python code/step1_images.py         # de plaatjes in docs/
.venv/bin/python code/make_label_items.py     # stap 2: alles voor de labelapp (labeling/)
.venv/bin/python code/check_setup.py          # klopt alles nog met de vastgelegde bestanden?
```

- `track_faces.py` zoekt in elk beeld van de drie fragmenten de gezichten en
  maakt de tracks. Het zoeken doet MediaPipe (de detector): die zet een kader
  om elk gezicht dat hij vindt, met een score voor hoe zeker hij is. Een track
  begint bij een kader met een score van 0,3 of hoger. Een zwakker kader vanaf
  0,2 mag een track die al loopt alleen verlengen; zo'n kader heet een
  verlenging. Tot slot knipt het programma de tracks die volgens de controle
  van alle tracks deels op een ander gezicht of op iets anders staan; welke
  beelden dat zijn, leest het uit `data/audit/controle_alle_tracks.csv`. Hoe
  dat allemaal werkt, staat in [Stap 1](stap1_gezichten_vinden_en_volgen.md).
  Het zoeken is het langzame deel. Daarom bewaart het programma de gevonden
  gezichten in `data/tracks/raw/`, zodat een volgende keer alleen het volgen
  en knippen opnieuw gebeurt. Die map gaat niet mee naar GitHub; de eerste
  keer maakt het programma de map vanzelf aan.
- `check_all_tracks.py` maakt de vellen waarmee we alle tracks met het oog
  gecontroleerd hebben: van elke track van twee of meer kaders een strook
  lichter gemaakte uitsneden. De vellen komen in `data/audit/alle_tracks/`;
  welke track op welk vel staat, staat in `data/audit/alle_tracks_index.csv`.
  Op de vellen staan de tracknummers van vóór het knippen, net als in
  `controle_alle_tracks.csv`; in `data/tracks/detections_0.3.csv` staat dat
  nummer in de kolom `track_ongeknipt`. Gebruik ook bij de opties hieronder
  dat nummer. Met `--track <nummer> --van <frame> --tot <frame>` maakt het
  programma een strook met álle kaders van één track tussen twee beelden; zo
  hebben we elke track met een fout of een twijfel uit de eerste
  controleronde precies nagekeken. Met `--track <nummer> --stappen 36` komen
  er 36 gelijk verdeelde kaders op, andere dan op het gewone vel; zo zijn de
  plaatjes voor de tweede, onafhankelijke controle gemaakt. Met
  `--out <bestand>` kies je waar zo'n strook komt. Hoe de controle ging, staat
  in [Controle van het volgen](stap1_controle.md).
- `detector_steekproef.py` rekent uit hoeveel duidelijk zichtbare gezichten de
  detector vindt. Dat doet het op een steekproef van 120 beelden waarin we met
  het oog de gezichten hebben aangewezen (`data/audit/detector_steekproef.csv`
  en `data/audit/detector_steekproef_beelden.csv`). Het programma schrijft
  niets weg, maar zet de uitkomst op het scherm. Op de laatste regel moet
  staan dat de kaders vanaf 0,3 samen met de verlengingen 238 van de 278
  duidelijke gezichten vinden.
- `step1_images.py` maakt de plaatjes in de uitleg van stap 1 en van de
  controle.
- `make_label_items.py` zet alles klaar voor de labelapp: `labeling/items.json`
  (wat de app laat zien, ook de dunne grijze kaders om de andere gezichten die
  de detector in hetzelfde beeld vond), de beelden in `labeling/images/`,
  `labeling/automatic_labels.csv` en `data/stills_index.csv`.
- `check_setup.py` is dezelfde controle als bij [Installeren](#installeren).
  Draai het aan het eind nog een keer: staat er weer *Alles in orde.*, dan
  zijn alle vastgelegde bestanden nog hetzelfde.

Het programma `ffprobe` (uit FFmpeg) hebben we alleen gebruikt om de
eigenschappen van de fragmenten op te zoeken; de programma's hebben `ffprobe`
niet nodig.

Bij een eerdere manier van volgen (versie 4) hebben we niet alle tracks
gecontroleerd, maar alleen een steekproef. De bestanden van die steekproef
staan nu in `data/audit/eerdere_steekproef/`, samen met het programma
`audit_tracks.py` dat de plaatjes ervan maakte. Dat programma hoorde bij de
tracks van die eerdere versie, werkt niet meer met de huidige tracks en hoort
daarom niet meer bij de programma's in `code/`.


## Waar de data vandaan komt

De drie filmfragmenten komen van YouTube; het stukje tussen haakjes in de
bestandsnaam is het nummer van de video op YouTube:

| Fragment | YouTube |
|---|---|
| *Das Boot – die Auferstehung* | `Oqek9Ktuwy8` |
| *Mon Gars Filmmusik* | `LnFceG2lL3U` |
| *Go Back Johann* | `qa3jt_GXMts` |

Het bestand `movies/List_of_URLS` noemt ook drie fragmenten die we niet
gebruiken, en mist *Mon Gars Filmmusik*.


## Opgelet: de projectmap en clouddiensten

Zet de projectmap liever niet in een map die met iCloud, OneDrive of een
andere clouddienst gesynchroniseerd wordt, zoals Documenten op een Mac of
Windows. Een clouddienst maakt soms kopieën met namen als `000010 2.jpg`, ook
van de bestanden van git, en dat kan het project beschadigen. Zet het project
bijvoorbeeld in `~/Developer/KTAI` (Mac) of `C:\Users\<naam>\KTAI` (Windows).
Staat het project toch in zo'n map, verwijder dan nooit een hele map met
gemaakte bestanden om die opnieuw te maken; de programma's werken bestanden
daarom bij in plaats van eerst alles weg te gooien. `code/check_setup.py`
waarschuwt als er zulke kopieën in de map staan.
