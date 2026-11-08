# Het labelen: wie staat er in elk beeld?

In deze map staat alles over het labelen van de filmpjes uit *Das Boot*: de code,
de uitkomsten en deze uitleg.

Ons project test hoe goed het herkenningsprogramma FaceNet vier personen uit de
film herkent: Der Alte, Fritz Grade, Johann en Werner. Om te kunnen nakijken of
FaceNet de juiste persoon aanwijst, moeten we eerst zelf zeker weten wie er in
elk beeld van de filmpjes staat. Dat overzicht heet de **ground truth**: het
antwoordenblad waarmee we FaceNet nakijken. Labelen is het werk waarmee we dat
antwoordenblad gemaakt hebben.

**Het labelen is klaar.** De ground truth staat in
[`output/stap_3_fouten_verbeteren/ground_truth.csv`](output/stap_3_fouten_verbeteren/ground_truth.csv).
Wie de ground truth alleen wil gebruiken, hoeft dus niets te draaien. Wie wil
weten hoe de ground truth gemaakt is, of een stap zelf wil doen, leest hieronder
verder.

![Eén beeld door het hele proces: het filmpje, de gevonden kaders, de labels per track, het nakijken, het verbeteren en de ground truth](fotos/overzicht.jpg)

*Zo gaat één beeld (Das Boot 1, beeld 23) door het hele proces. De computer vond
vijf kaders. Bij het labelen kreeg elk kader de keuze van zijn track. Bij het
nakijken bleek dat er een persoon ontbrak. Bij het verbeteren kwam dat kader
erbij. Daarna staat in de ground truth precies wie er in dit beeld te zien is en
waar. De getallen onder elk plaatje gaan over alle filmpjes samen.*


## Inhoud

- [De belangrijkste woorden](#de-belangrijkste-woorden)
- [Het labelen in het kort](#het-labelen-in-het-kort)
- [Wat er in deze map staat](#wat-er-in-deze-map-staat)
- [Installeren op Mac en Windows](#installeren-op-mac-en-windows)
- [Stap 0: de gezichten vinden en volgen](#stap-0-de-gezichten-vinden-en-volgen)
- [Stap 1: per track labelen](#stap-1-per-track-labelen)
- [Stap 2: per beeld nakijken](#stap-2-per-beeld-nakijken)
- [Stap 3: de foute beelden verbeteren](#stap-3-de-foute-beelden-verbeteren)
- [De uitkomst: de ground truth](#de-uitkomst-de-ground-truth)
- [Alles opnieuw doen, en waar je op moet letten](#alles-opnieuw-doen-en-waar-je-op-moet-letten)


## De belangrijkste woorden

| Woord | Wat het betekent |
|---|---|
| **Beeld** (in de code *frame*) | Een video is een reeks losse beelden die snel na elkaar getoond worden, meestal 25 per seconde. |
| **Detector** | Het programma dat in een beeld gezichten zoekt. Wij gebruiken de MediaPipe Face Detector. |
| **Kader** | De rechthoek die de detector om een gezicht zet. Een kader heeft een plek (x, y: de linkerbovenhoek) en een maat (w: breedte, h: hoogte), in pixels van het originele beeld. |
| **Score** | Een getal van 0 tot 1 dat zegt hoe zeker de detector ervan is dat er een gezicht in het kader staat. |
| **Track** | Hetzelfde gezicht, gevolgd over beelden na elkaar. Een track bestaat dus uit een reeks kaders. |
| **Beeldwissel** | De plek waar de film ineens naar een ander shot springt. |
| **Label** | De keuze die een mens maakt: wie staat er in dit kader? |
| **Item** | Alles wat in de programma's één beurt krijgt, bijvoorbeeld één track of één beeld. |
| **Ground truth** | Het antwoordenblad: per beeld wie van de vier personen er te zien is, en waar. |


## Het labelen in het kort

Bij elk gezicht in elk beeld met de hand aangeven wie het is, zou 37.003 keer
kiezen betekenen. Daarom laten we de computer eerst de gezichten vinden en volgen,
zodat een mens alleen per track hoeft te kiezen. Dat gaat snel, maar een track
laat maar één beeld zien, en de computer mist ook gezichten. Toen we daarna de
tijdlijn tekenden (wanneer is elke persoon in beeld?), zaten daar veel gaten in.
Daarom is daarna elk beeld nagekeken, en is elk fout beeld met de hand verbeterd.

| Stap | Wat er gebeurt | Code | Uitkomst |
|---|---|---|---|
| **0. Voorbereiding** | De computer zoekt de gezichten, volgt ze en zet alles klaar om te labelen. Alle tracks zijn gecontroleerd. | [`stap_0_voorbereiding/`](stap_0_voorbereiding/) | 37.003 kaders in 1.387 tracks |
| **1. Per track labelen** | Een mens kiest per track en per gezicht op een foto of still wie het is. | [`stap_1_tracks_labelen/`](stap_1_tracks_labelen/) | 1.482 keuzes |
| **2. Per beeld nakijken** | Een mens bekijkt elk beeld met de namen erbij en zegt goed of fout. | [`stap_2_beelden_nakijken/`](stap_2_beelden_nakijken/) | 9.516 keer goed, 1.701 keer fout |
| **3. Foute beelden verbeteren** | Een mens zet in elk fout beeld de kaders van de vier personen goed. Daarna worden alle stappen samengevoegd. | [`stap_3_fouten_verbeteren/`](stap_3_fouten_verbeteren/) | De ground truth: 20.990 rijen |

De uitkomst van elke stap is de invoer van de volgende stap. Elke stap heeft een
eigen map met code en een eigen map in [`output/`](output/).


## Wat er in deze map staat

De filmpjes staan één map hoger, in [`../filmpjes/`](../filmpjes/). Alle andere
bestanden van het labelen staan in deze map:

```
labelen/
├── README.md                       deze uitleg
├── requirements.txt                de pakketten die stap 0, 2 en 3 nodig hebben
├── checksums.sha256                controlegetallen van de vastgelegde bestanden
├── invoer/
│   ├── model/                      het model van de detector
│   └── pictures/                   de foto's van de acteurs en de stills uit de film
├── gedeeld/                        code die meer stappen gebruiken (paden, kaders, beelden, webserver)
├── stap_0_voorbereiding/
│   ├── 0_check_setup.py            controleert of de computer en de bestanden in orde zijn
│   ├── 1_track_faces.py            zoekt en volgt de gezichten
│   ├── 2_check_all_tracks.py       maakt de plaatjes waarmee alle tracks gecontroleerd zijn
│   └── 3_make_label_items.py       zet alles klaar voor de labelapp
├── stap_1_tracks_labelen/
│   ├── START_MAC.command           hiermee start je de labelapp op een Mac
│   ├── START_WINDOWS.bat           hiermee start je de labelapp op Windows
│   ├── app.py, web/                de labelapp
│   ├── items.json, images/         alles wat de labelapp laat zien
│   └── tests/                      de automatische tests van de labelapp
├── stap_2_beelden_nakijken/
│   ├── check_labels.py             het programma om elk beeld na te kijken
│   └── pagina.html                 de pagina in de browser
├── stap_3_fouten_verbeteren/
│   ├── fix_labels.py               het programma om foute beelden te verbeteren
│   ├── pagina.html                 de pagina in de browser
│   └── make_ground_truth.py        voegt alle stappen samen tot de ground truth
├── output/
│   ├── stap_0_voorbereiding/       de kaders, de tracks en de controle daarvan
│   ├── stap_1_tracks_labelen/      labels.csv
│   ├── stap_2_beelden_nakijken/    controle_labels.csv
│   └── stap_3_fouten_verbeteren/   correcties.csv en de ground truth
└── fotos/                          de plaatjes in deze uitleg
```

### De filmpjes

We gebruiken acht fragmenten uit *Das Boot*. GitHub neemt geen bestanden groter
dan 100 MB aan; daarom zijn fragment 2, 4 en 8 in delen geknipt, zonder de beelden
opnieuw te coderen. Samen zijn het 12 bestanden. In de programma's en grafieken
heten de fragmenten Video 1 tot en met Video 8. De beelden staan precies zo in de
bestanden als in de bron, zonder geluid.

| Fragment | Bestanden in `filmpjes/` | Lengte | Beelden | Grootte van een beeld | Bron |
|---|---|---|---|---|---|
| Video 1 | Das Boot 1 | 0:45 | 1.125 | 3840 × 2160 | [YouTube](https://www.youtube.com/watch?v=Ek2omNPSOYc), 28:10 tot 28:55 |
| Video 2 | Das Boot 2a, 2b | 1:00 | 647 + 853 | 3840 × 2160 | [YouTube](https://www.youtube.com/watch?v=10EqNLl5ZSM), 13:15 tot 14:15 |
| Video 3 | Das Boot 3 | 0:56 | 1.400 | 3840 × 2160 | [YouTube](https://www.youtube.com/watch?v=kefBHWylmMk), 30:08 tot 31:04 |
| Video 4 | Das Boot 4a, 4b | 1:00 | 714 + 786 | 3840 × 2160 | [YouTube](https://www.youtube.com/watch?v=kefBHWylmMk), 45:35 tot 46:35 |
| Video 5 | Das Boot 5 | 1:01 | 1.525 | 3840 × 2160 | [YouTube](https://www.youtube.com/watch?v=kefBHWylmMk), 32:05 tot 33:06 |
| Video 6 | Das Boot 6 | 0:07 | 168 | 1920 × 1080 | [YouTube](https://www.youtube.com/watch?v=ofY2rexjmc4), 3:51 tot 3:58 |
| Video 7 | Das Boot 7 | 0:35 | 839 | 1920 × 1080 | [YouTube](https://www.youtube.com/watch?v=T-D6e3pjHKQ), 0:25 tot 1:00 |
| Video 8 | Das Boot 8a, 8b, 8c | 2:05 | 1.096 + 1.194 + 835 | 3840 × 2160 | aangeleverd bestand |
| **samen** | 12 bestanden | ongeveer 7,5 minuut | **11.182** | | |

De filmpjes hebben 25 beelden per seconde, behalve Video 6 en 7 (23,98).


## Installeren op Mac en Windows

Dit hoef je maar één keer te doen. Wie alleen de uitkomsten wil gebruiken, hoeft
niets te installeren. **Alleen labelen (stap 1)** kan zonder deze pakketten: daarvoor
is alleen Python nodig, zie [Stap 1](#stap-1-per-track-labelen).

**1. Python.** Stap 0, 2 en 3 zijn gemaakt met Python 3.12. Download Python 3.12 van
<https://www.python.org/downloads/> en installeer het. Op Windows zet je in het
eerste scherm een vinkje bij *Add python.exe to PATH*.

**2. Het project op je computer zetten.** Download de branch `final-version` als
[ZIP-bestand](https://github.com/arieknarie/KTAI/archive/refs/heads/final-version.zip)
(ongeveer 800 MB) en pak het uit, of gebruik git:

```bash
git clone -b final-version https://github.com/arieknarie/KTAI.git
```

Zet de map niet in iCloud, OneDrive of een andere clouddienst, en op Windows in een
map zonder letters als é in het pad (zie
[Waar je op moet letten](#waar-je-op-moet-letten)).

**3. Een terminal openen in de map `labelen`.** Een terminal is het venster waarin
je opdrachten typt. Alle opdrachten in deze uitleg geef je vanuit de map `labelen`.

- **Mac:** open het programma Terminal, typ `cd ` (met een spatie erachter), sleep
  de map `labelen` naar het venster en druk op Enter.
- **Windows:** open de map `labelen` in de Verkenner, klik bovenin op de balk met de
  naam van de map, typ `cmd` en druk op Enter.

**4. De pakketten installeren.** Dit maakt een aparte map `.venv` met Python en de
pakketten: MediaPipe (vindt de gezichten), pandas en NumPy (rekenen met tabellen) en
OpenCV (leest de video's).

Op een Mac:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Op Windows:

```bat
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

**5. Controleren of alles klopt.** Dit programma kijkt of de versies kloppen, of alle
bestanden nog dezelfde zijn als bij ons, en of deze computer de filmpjes op precies
dezelfde manier uitleest. Staat er aan het eind *Alles in orde.*, dan is de computer
klaar.

| Mac | Windows |
|---|---|
| `.venv/bin/python stap_0_voorbereiding/0_check_setup.py` | `.venv\Scripts\python stap_0_voorbereiding\0_check_setup.py` |

Op Windows hebben we het installeren en de programma's niet uitgeprobeerd; het zou
daar wel moeten werken. De opdrachten zijn op Windows steeds hetzelfde, met
`.venv\Scripts\python` in plaats van `.venv/bin/python` en `\` in plaats van `/`.


## Stap 0: de gezichten vinden en volgen

**Waarom deze stap.** Een mens kan niet 37.003 keer kiezen. Daarom zoekt de computer
de gezichten en plakt de computer de kaders van hetzelfde gezicht aan elkaar tot
tracks. Dan hoeft een mens per track maar één keer te kiezen. De uitkomsten van deze
stap liggen vast, dus deze stap hoef je niet opnieuw te doen.

### Hoe het werkte

**Gezichten zoeken.** De MediaPipe Face Detector (de versie *full range*, die ook
gezichten verder weg vindt) bekijkt elk beeld van elk filmpje. Standaard telt de
detector alleen kaders met een score van minstens 0,5. In de donkere, drukke scènes
van deze film mist de detector dan veel gezichten die een mens wel ziet. Daarom
bewaren we alles vanaf een score van 0,3. Een kader dat geen gezicht blijkt, is geen
probleem: bij het labelen wordt dat *Geen gezicht*. Een gezicht zonder kader is wel
een probleem, want dat komt niet vanzelf op het antwoordenblad.

![Hetzelfde beeld met de grens 0,5 en de grens 0,3](fotos/stap0_drempel.jpg)

*Hetzelfde beeld twee keer. Links de kaders met een score van minstens 0,5 (vier
kaders), rechts de kaders met een score van minstens 0,3 (dertien kaders).*

**Gezichten volgen.** De computer gaat de beelden op volgorde langs en past bij elk
beeld zes regels toe:

1. **Let op beeldwissels.** Lijkt een beeld te weinig op het vorige beeld (kleur lager
   dan 0,9 of licht-donkerpatroon lager dan 0,7), dan stoppen alle tracks.
2. **Het kader moet bijna op dezelfde plek staan.** Het nieuwe kader en het laatste
   kader van de track moeten minstens 30% overlappen.
3. **De omgeving moet nog hetzelfde zijn.** Een ruim gebied rond het kader moet nog
   lijken op hetzelfde gebied in het vorige beeld (gelijkenis minstens 0,6).
4. **Een gezicht mag even weg zijn.** Is er geen passend kader, dan wacht de computer
   hoogstens 12 beelden (een halve seconde), maar nooit over een beeldwissel heen.
5. **Een zwak kader mag een track alleen verlengen.** Een kader met een score van 0,2
   tot 0,3 mag een track die al loopt laten doorlopen, maar begint nooit een track.
6. **Een kader met een score vanaf 0,3 dat nergens bij past, begint een nieuwe track.**

Een fout in het antwoordenblad is erger dan extra werk. Daarom zijn de regels streng
waar twee personen door elkaar kunnen raken (regel 1 tot en met 3), en ruim waar
alleen extra werk dreigt (regel 4 en 5).

![Twee beelden na elkaar met een beeldwissel ertussen](fotos/stap0_beeldwissel.jpg)

*Een beeldwissel in Das Boot 5. De kleuren lijken nog op elkaar (0,95), maar het
licht-donkerpatroon zakt naar -0,19. De computer laat hier alle tracks stoppen.*

![Zes beelden uit één track](fotos/stap0_track.jpg)

*Zes beelden uit één track in Das Boot 4b. Het groene kader blijft op hetzelfde
gezicht, ook als het gezicht beweegt. De grijze kaders zijn andere tracks.*

**Alle tracks controleren.** Omdat een track maar één label krijgt, mag het kader niet
halverwege naar een ander gezicht springen. Daarom is elke track van twee of meer
kaders kader voor kader bekeken: 810 tracks met samen 36.506 kaders. In 44 tracks
stond het kader voor een deel op iets anders (285 kaders, 0,8% van alle kaders). Die
tracks zijn op die plekken geknipt, zodat elk stuk een eigen label krijgt. Daardoor
werden het 1.387 tracks.

![Alle uitsneden van een track die naar een ander gezicht overspringt](fotos/stap0_controle_wissel.jpg)

*Een track die overspringt: tot en met beeld 818 staat het groene kader op het gezicht
vooraan, in beeld 819 springt het kader naar het gezicht erachter. Na het knippen zijn
het twee tracks.*

Ook elk van de 11.182 beelden is bekeken om te tellen hoe vaak de detector een gezicht
mist. Bij die eerste blik hadden 10.867 gezichten geen kader (een gezicht dat in 50
beelden gemist wordt, telt 50 keer), en stonden 4.691 kaders niet op een gezicht.
Daarom was de detector alleen niet genoeg, en zijn stap 2 en 3 later nodig gebleken.

**Klaarzetten om te labelen.** Van elke track kiest het programma één beeld om te
laten zien: het beeld waarin het kader groot is en de detector het zekerst is (score
maal breedte van het kader). Dat beeld en de andere kaders in hetzelfde beeld komen in
`items.json` en `images/`, in de map van de labelapp.

### Zo doe je het

Dit is alleen nodig als je de uitkomsten zelf opnieuw wilt maken. De opdrachten staan
in de volgorde waarin ze horen.

| Wat | Mac | Windows |
|---|---|---|
| Gezichten zoeken en volgen (duurt ongeveer een uur) | `.venv/bin/python stap_0_voorbereiding/1_track_faces.py` | `.venv\Scripts\python stap_0_voorbereiding\1_track_faces.py` |
| Plaatjes om de tracks te controleren (met `--beelden` erachter ook van elk beeld; samen ongeveer 1,5 GB) | `.venv/bin/python stap_0_voorbereiding/2_check_all_tracks.py` | `.venv\Scripts\python stap_0_voorbereiding\2_check_all_tracks.py` |
| Alles klaarzetten voor de labelapp | `.venv/bin/python stap_0_voorbereiding/3_make_label_items.py` | `.venv\Scripts\python stap_0_voorbereiding\3_make_label_items.py` |

Geeft een programma een andere uitkomst dan de vastgelegde bestanden, dan overschrijft
het programma die bestanden niet, maar schrijft het de nieuwe uitkomst ernaast, als
`<naam>.nieuw.<ext>`. Waarom dat zo is, staat bij
[Waar je op moet letten](#waar-je-op-moet-letten).

### Wat eruit kwam

De bestanden staan in
[`output/stap_0_voorbereiding/`](output/stap_0_voorbereiding/).

| Bestand | Wat erin staat |
|---|---|
| `tracks/detections_0.3.csv` | Elk van de 37.003 kaders: bestand (`video`), `frame`, `time_s`, kader (`x`, `y`, `w`, `h`), `score`, of het een verlenging is (`verlengd`), `track`, en de track van vóór het knippen (`track_ongeknipt`). |
| `tracks/tracks_0.3.csv` | Elke track van de 1.387: eerste en laatste beeld, tijd, aantal kaders. |
| `tracks/frames.csv` | Elk van de 11.182 beelden: tijd, hoeveel het beeld op het vorige lijkt, en of het een beeldwissel is (`cut`). |
| `tracks/detections_0.5.csv`, `tracks/tracks_0.5.csv` | Dezelfde lijsten met alleen kaders vanaf score 0,5, om later te kunnen vergelijken. |
| `tracks/run_info.json` | Waarmee de uitkomsten gemaakt zijn: versies, instellingen en controlegetallen. |
| `controle/controle_alle_tracks.csv` | Het oordeel over elke gecontroleerde track, met de beelden waar de track fout gaat. |
| `controle/controle_alle_beelden.csv`, `controle/controle_alle_beelden_vondsten.csv` | De controle van elk beeld: gezichten zonder kader en kaders zonder gezicht. |
| `stills_index.csv` | Welk bestand bij welke still hoort. In de labelapp heet een still alleen `still_01` enzovoort. |
| `automatic_labels.csv` | De 21 foto's van de acteurs met één gezicht. Die krijgen hun label vanzelf: de foto staat in een map met de naam van de persoon. |


## Stap 1: per track labelen

**Waarom deze stap.** Het antwoordenblad moet onafhankelijk zijn van het programma dat
we testen. Daarom kiest een mens, zonder hulp of suggesties van een computer. De
persoon die labelt noemen we de *labelaar*.

### Hoe het werkte

De labelaar kreeg 1.422 items te zien: 1.387 tracks, 33 stills (losse foto's uit de
film) en 2 foto's van de acteurs waarop meer mensen staan. Samen zijn dat 1.482
gezichten. Van een track ziet de labelaar één beeld, met een geel kader om het gezicht.
De keuze geldt voor de hele track. De labelaar kiest uit zeven knoppen:

| Knop | Toets | Wanneer |
|---|---|---|
| Der Alte, Fritz Grade, Johann, Werner | 1, 2, 3, 4 | Het kader staat om het gezicht van deze persoon, en de labelaar weet het zeker. |
| Figurant | 5 | Een gezicht dat niet een van de vier personen is. |
| Geen gezicht | 6 | Zeker geen gezicht, bijvoorbeeld een lamp, een hand of een oor. |
| Weet niet | 7 | De labelaar twijfelt. Een gok die fout is, zou FaceNet later onterecht fout rekenen. |

De labelapp draait op de eigen computer en werkt in de browser. Er gaat niets via
internet, en elke keuze wordt meteen bewaard.

![Het scherm van de labelapp, met nummers bij de onderdelen](fotos/stap1_scherm.jpg)

*Het scherm van de labelapp bij een still. (1) de naam van de labelaar, (2) de voortgang
per deel, (3) foto's van de vier personen om mee te vergelijken, (4) het beeld met de
kaders, (5) het gezicht dat aan de beurt is, groot, (6) Beeld lichter, (7) de nummers van
de gezichten, (8) de knoppen om te kiezen, (9) een gemist gezicht zelf tekenen, (10)
vorige en volgende, (11) naar het eerste item dat nog niet af is, (12) de korte uitleg.*

![Een track in de labelapp: één geel kader, de andere gevonden kaders dun en gestippeld](fotos/stap1_track.jpg)

*Een track in de labelapp. Er is één geel kader: daarvoor geldt de keuze. De dunne
stippelkaders zijn andere gevonden kaders; die komen elk in een eigen track aan de beurt.*

Een paar keuzes in de app, en waarom:

- **Geen namen in beeld.** Bestandsnamen kunnen een naam bevatten en de labelaar sturen.
  Daarom heet een still in de app *Still 1 van 33*, en een filmpje *Video 1*.
- **Alles past op één scherm.** De labelaar hoeft nooit te scrollen.
- **Beeld lichter.** Veel scènes zijn erg donker. Deze stand maakt donkere gezichten
  lichter, zodat de labelaar ze kan herkennen.
- **Geen vergissingen door snel drukken.** Een ingedrukte toets en een dubbelklik tellen
  één keer, en de app laat pas kiezen als het nieuwe beeld er even staat.
- **Elke keuze is meteen veilig.** De app schrijft eerst een tijdelijk bestand en maakt
  reservekopieën. Lukt bewaren even niet, dan toont de app een rode balk.

### Zo doe je het

De labelapp heeft alleen Python nodig (versie 3.8 of nieuwer), geen extra pakketten.
De echte labels staan al in `output/`. Start je de app, dan begint de app met een lege
lijst in een eigen bestand: de echte uitkomst verandert daar niet door.

**De app starten.**

- **Mac:** dubbelklik in de map `stap_1_tracks_labelen` op `START_MAC.command`. Zegt de
  Mac de eerste keer dat het bestand niet geopend kan worden, klik dan op **Gereed**, ga
  naar **Systeeminstellingen > Privacy en beveiliging**, en klik onderaan bij de melding
  over `START_MAC.command` op **Open toch**. Werkt dubbelklikken niet, typ dan in de
  terminal `python3 stap_1_tracks_labelen/app.py`.
- **Windows:** dubbelklik in de map `stap_1_tracks_labelen` op `START_WINDOWS.bat`. Zegt
  Windows *Windows heeft uw pc beveiligd*, klik dan op **Meer informatie** en **Toch
  uitvoeren**. Werkt dubbelklikken niet, typ dan in de terminal
  `py stap_1_tracks_labelen\app.py`.

Er opent een venster met tekst, en daarna de labelpagina in de browser. Laat dat venster
open zolang je labelt: het venster ís de app. De eerste keer start een korte rondleiding
langs alles op het scherm.

| Toets | Wat de toets doet |
|---|---|
| **1** t/m **7** | Kiezen (zie de tabel met knoppen hierboven) |
| **Enter** | Volgende |
| **←** / **→** | Vorige of volgende bekijken, zonder iets te kiezen |
| **T** | Een gemist gezicht van een van de vier personen zelf tekenen |
| **Delete** | Een getekend kader weghalen |
| **L** | Beeld lichter aan of uit |

**Stoppen en verdergaan.** Sluit het tabblad en het venster van de app. Start je de app
later opnieuw uit dezelfde map, dan ga je verder waar je gebleven was.

**Als alles af is.** De keuzes staan in `labels.csv` in de map van de app. Dat bestand
hoort daarna in `output/stap_1_tracks_labelen/`:

| Mac | Windows |
|---|---|
| `cp stap_1_tracks_labelen/labels.csv output/stap_1_tracks_labelen/labels.csv` | `copy stap_1_tracks_labelen\labels.csv output\stap_1_tracks_labelen\labels.csv` |

Omgekeerd kun je de echte keuzes in de app bekijken door dat bestand naar de map van de
app te kopiëren.

**De tests.** De app heeft 310 automatische tests: kiezen met muis en toetsen, verdergaan
na een herstart, reservekopieën, beveiliging en het scherm op zeven groottes. Daarvoor zijn
Python, Node 22 of nieuwer en Google Chrome nodig. Vanuit de map `labelen` op een Mac:
`bash stap_1_tracks_labelen/tests/run_tests.sh`. Alle tests slagen ook in deze nieuwe
indeling.

### Wat eruit kwam

Alle 1.482 gezichten hebben een keuze, in
[`output/stap_1_tracks_labelen/labels.csv`](output/stap_1_tracks_labelen/labels.csv).
Elke rij is één gezicht of één track. Dit zijn de eerste twee tracks (de kolommen
`labeler`, `time` en `source` zijn hier weggelaten):

| face | item | label | how | frame | x | y | w | h |
|---|---|---|---|---|---|---|---|---|
| Das Boot 1 […].mp4#track0 | track:Das Boot 1 […].mp4#0 | Werner | chosen | 538 | 2505 | 831 | 411 | 411 |
| Das Boot 1 […].mp4#track1 | track:Das Boot 1 […].mp4#1 | DerAlte | chosen | 101 | 896 | 459 | 655 | 655 |

Het `frame` en het kader zijn van het beeld dat de labelaar te zien kreeg. In de kolom
`how` staat `chosen`: de labelaar koos dit zelf. Getekende gezichten zijn er niet.

| Keuze | Tracks | Alle gezichten (ook op foto's en stills) |
|---|---|---|
| Der Alte | 147 | 166 |
| Fritz Grade | 114 | 129 |
| Johann | 27 | 35 |
| Werner | 61 | 76 |
| Figurant | 328 | 355 |
| Geen gezicht | 708 | 719 |
| Weet niet | 2 | 2 |
| **samen** | **1.387** | **1.482** |

Meer dan de helft van de tracks is geen gezicht. Dat is precies waarvoor de knop *Geen
gezicht* bestaat: de detector ziet in deze 4K-beelden vaak een oor, een hand of een pet
voor een gezicht aan, en volgt dat ding dan netjes van beeld tot beeld.


## Stap 2: per beeld nakijken

**Waarom deze stap.** Na stap 1 weten we per track wie het is. Toen we daaruit de tijdlijn
tekenden, zaten er veel gaten in de lijn van een persoon: bij dezelfde persoon stonden
ineens beelden zonder naam. Dat komt doordat de detector een gezicht soms mist, en de
labelaar van een track maar één beeld ziet. Daarom is elk beeld daarna nog een keer met
het oog bekeken.

### Hoe het werkte

Het programma laat achter elkaar alle 11.182 beelden zien, ook de beelden zonder kader,
en daarna de 35 gelabelde foto's en stills. Bij elk beeld is er maar één vraag: **kloppen
de namen in dit beeld?** Pijltje links is goed, pijltje rechts is fout.

![Het programma van stap 2: een beeld met de namen van de personen](fotos/stap2_scherm.jpg)

*Het programma van stap 2. Bovenaan staat welk beeld het is en hoeveel er gedaan zijn.*

Vier dingen maken het nakijken snel en betrouwbaar:

- **Alleen de vier personen.** Figuranten en kaders met *Geen gezicht* staan er niet bij,
  want voor het project gaat het om de vier personen.
- **Eén kader per persoon.** Staat dezelfde persoon meer dan één keer in een beeld, dan
  maakt het programma er één groot kader van. De detector zet soms twee kaders op één hoofd.
- **Een waarschuwing bij een gat.** Stond een persoon in het vorige beeld van het filmpje
  wel en in dit beeld niet, dan staat er bovenin een rode waarschuwing. Dat gebeurde bij
  248 beelden, en 190 daarvan (ongeveer drie van de vier) bleken inderdaad fout.
- **Niet per ongeluk te snel.** Een toets telt pas als het beeld er helemaal staat, en een
  ingedrukte toets telt één keer. Zo krijgt geen beeld een oordeel dat niet gezien is.

![De rode waarschuwing bovenin: een persoon uit het vorige beeld is weg](fotos/stap2_waarschuwing.jpg)

*Hetzelfde filmpje even later. Eén persoon stond in het vorige beeld wel en heeft hier geen
kader meer. De waarschuwing staat in de balk bovenin.*

De beelden worden altijd op volgorde uit de video gelezen. Direct naar een beeldnummer
springen is niet betrouwbaar: OpenCV geeft dan soms het beeld ervoor, en dan staat een
kader op het verkeerde beeld.

### Zo doe je het

Start het programma vanuit de map `labelen`:

| Mac | Windows |
|---|---|
| `.venv/bin/python stap_2_beelden_nakijken/check_labels.py` | `.venv\Scripts\python stap_2_beelden_nakijken\check_labels.py` |

De pagina opent vanzelf in de browser. Stoppen doe je met Ctrl+C in de terminal.

| Toets | Wat de toets doet |
|---|---|
| **←** | Goed: de namen in dit beeld kloppen |
| **→** | Fout: er klopt iets niet (een naam ontbreekt, staat fout of staat op de verkeerde plek) |
| **Backspace** | Eén beeld terug. Bij een nieuw oordeel over een beeld telt het laatste oordeel. |

Elk oordeel komt meteen in het bestand. Stop je en start je later opnieuw, dan ga je verder
bij het eerste beeld zonder oordeel; de video wordt dan eerst tot daar gelezen, dus dat
eerste beeld kan even duren.

Alle beelden hebben al een oordeel. Wil je het programma alleen proberen, zet er dan
`--uitvoer proef` achter. De oordelen komen dan in de map `proef`, en de echte uitkomst
verandert niet.

### Wat eruit kwam

Van de 11.217 beelden, foto's en stills kregen er **9.516 goed (84,8%)** en **1.701 fout
(15,2%)**, in
[`output/stap_2_beelden_nakijken/controle_labels.csv`](output/stap_2_beelden_nakijken/controle_labels.csv).
Elke rij is één oordeel. Is een beeld vaker beoordeeld, dan telt de laatste rij van dat beeld.

| item | oordeel | tijd |
|---|---|---|
| Das Boot 1 […].mp4#beeld0 | goed | 2026-11-04T16:54:58 |
| Das Boot 1 […].mp4#beeld1 | goed | 2026-11-04T16:54:58 |

![Staafdiagram: het deel van de beelden dat fout was, per filmpje](fotos/stap2_fout_per_fragment.png)

Het verschil per filmpje is groot. In Video 3 en 4 klopte vrijwel alles al na stap 1. In
Video 6 was twee derde fout: dat filmpje is kort (168 beelden), en in de
[tijdlijn](#wat-nakijken-en-verbeteren-heeft-opgeleverd) is te zien dat één persoon daar
lang ontbrak.


## Stap 3: de foute beelden verbeteren

**Waarom deze stap.** Stap 2 zegt welke beelden fout zijn, maar niet wat er wel moet staan.
In deze stap worden de kaders van de vier personen in elk fout beeld goed gezet.

### Hoe het werkte

Het programma laat alleen de 1.701 foute beelden zien, één voor één.

![Het programma van stap 3 met nummers bij de onderdelen](fotos/stap3_scherm.jpg)

*Het programma van stap 3. (1) Rechts groot het foute beeld met de kaders van de vier
personen. (2) Linksboven het laatste goede beeld ervoor. (3) Een knop per persoon: de knop
is gekleurd als die persoon in het beeld staat. (4) Opslaan en naar het volgende foute
beeld. (5) Hoeveel beelden er al verbeterd zijn.*

- **Het laatste goede beeld als voorbeeld.** Linksboven staat altijd het laatste goede
  beeld uit hetzelfde filmpje: een beeld dat in stap 2 goed kreeg, of een beeld dat hier al
  verbeterd is. Zo is altijd te zien wie er net nog in beeld was.
- **Een kader erbij zetten.** Zet de knop van een persoon aan en klik op het gezicht. Vond
  de computer op die plek een kader, dan wordt dat kader gebruikt. Vond de computer daar niets,
  dan komt er een kader zo groot als het kader van die persoon in het laatste goede beeld.
- **Een kader weghalen.** Klik op een knop die aan staat: het kader van die persoon gaat weg.
  Om een kader te verplaatsen, zet je de knop uit en weer aan en klik je op de goede plek.
- **Doorwerken zonder alles opnieuw te doen.** Na een beeld dat net verbeterd is, staan in
  het volgende foute beeld dezelfde kaders al op dezelfde plek. Volgt het foute beeld op een
  beeld dat goed kreeg, dan komt wie ontbreekt erbij op dezelfde plek. In een reeks foute
  beelden na elkaar hoef je zo meestal alleen te controleren en op Enter te drukken.
- **Terug is echt terug.** Met Backspace ga je een fout beeld terug, en worden de verbeteringen
  van dat beeld en alle beelden erna gewist. Zo sluit het overnemen van de kaders weer aan.

### Zo doe je het

Start het programma vanuit de map `labelen`:

| Mac | Windows |
|---|---|
| `.venv/bin/python stap_3_fouten_verbeteren/fix_labels.py` | `.venv\Scripts\python stap_3_fouten_verbeteren\fix_labels.py` |

| Handeling | Wat er gebeurt |
|---|---|
| Knop aan zetten, dan klikken op een gezicht | Om dat gezicht komt een kader met die naam |
| Klikken op een knop die aan staat | Het kader van die persoon gaat weg |
| **Enter** (of de groene knop) | Opslaan en naar het volgende foute beeld |
| **Backspace** | Terug naar het vorige foute beeld; dat beeld en alles erna wordt gewist |

Stop je en start je later opnieuw, dan ga je verder bij het eerste foute beeld dat nog niet
verbeterd is. Alle foute beelden zijn al verbeterd. Wil je het programma alleen proberen, zet
er dan `--uitvoer proef` achter.

Als alle beelden verbeterd zijn, maakt dit programma de ground truth:

| Mac | Windows |
|---|---|
| `.venv/bin/python stap_3_fouten_verbeteren/make_ground_truth.py` | `.venv\Scripts\python stap_3_fouten_verbeteren\make_ground_truth.py` |

### Wat eruit kwam

Alle 1.701 foute beelden zijn verbeterd, in
[`output/stap_3_fouten_verbeteren/correcties.csv`](output/stap_3_fouten_verbeteren/correcties.csv).
Per opgeslagen beeld staat daar per persoon één rij met het kader. Een rij zonder persoon
betekent dat er geen van de vier in het beeld staat. Is een beeld opnieuw opgeslagen, dan telt
de laatste keer, en een rij met persoon `-` betekent dat een verbetering gewist is.

![Drie voorbeelden van een beeld voor en na het verbeteren](fotos/stap3_voor_na.jpg)

*Drie beelden voor en na het verbeteren. De namen zijn de keuzes uit de stappen 1 en 3.*

In de 1.699 foute beelden uit de filmpjes veranderde dit:

| Wat er veranderde | Aantal kaders |
|---|---|
| Een persoon erbij | 1.673 |
| Een kader verplaatst naar een andere plek | 306 |
| Een persoon weggehaald | 155 |
| Bleef ongeveer hetzelfde | 1.913 |

Het grootste deel gaat dus om een persoon die wel in beeld is maar nog geen kader had. Van de
3.892 kaders in de verbeterde beelden hadden er 1.607 (41%) geen kader van de detector op die
plek. Dat zijn de gezichten die de detector gemist heeft, en die zonder deze stap niet op het
antwoordenblad hadden gestaan.


## De uitkomst: de ground truth

Het programma `make_ground_truth.py` voegt alles samen. Per beeld geldt:

- **Kreeg het beeld in stap 2 goed?** Dan tellen de kaders uit stap 1, zoals stap 2 ze liet
  zien (één kader per persoon).
- **Kreeg het beeld in stap 2 fout?** Dan tellen de verbeterde kaders uit stap 3.

De uitkomst staat in
[`output/stap_3_fouten_verbeteren/ground_truth.csv`](output/stap_3_fouten_verbeteren/ground_truth.csv),
met per beeld één rij voor elke persoon in dat beeld: 20.990 rijen. Dit zijn de rijen van het
beeld bovenaan deze uitleg:

| fragment | bestand | beeld | tijd_s | persoon | x | y | w | h | herkomst |
|---|---|---|---|---|---|---|---|---|---|
| Video 1 | Das Boot 1 […].mp4 | 22 | 0.88 | Der Alte | 1104 | 780 | 435 | 435 | stap_3 |
| Video 1 | Das Boot 1 […].mp4 | 22 | 0.88 | Fritz Grade | 1724 | 834 | 317 | 317 | stap_3 |
| Video 1 | Das Boot 1 […].mp4 | 22 | 0.88 | Werner | 2643 | 830 | 396 | 396 | stap_3 |

- `beeld` telt vanaf 0. Op het scherm van de programma's telt een beeld vanaf 1 (dit is daar
  *beeld 23*).
- `tijd_s` is het aantal seconden vanaf het begin van het fragment, ook bij een fragment in delen.
- `herkomst` zegt of de rij uit stap 1 komt (17.098 rijen) of uit stap 3 (3.892 rijen).
- Een beeld zonder een van de vier personen heeft geen rij. Alle beelden staan in
  `output/stap_0_voorbereiding/tracks/frames.csv`; in 9.849 van de 11.182 beelden staat minstens
  één van de vier.

Hetzelfde voor de gelabelde foto's en stills staat in
[`ground_truth_fotos_en_stills.csv`](output/stap_3_fouten_verbeteren/ground_truth_fotos_en_stills.csv).
Twee van die stills waren in stap 2 fout (`still_09` en `still_31`) en zijn dus verbeterd.

### Wat nakijken en verbeteren heeft opgeleverd

| Persoon | Beelden na stap 1 | Beelden na stap 3 | Erbij | Losse stukken na stap 1 | Losse stukken na stap 3 |
|---|---|---|---|---|---|
| Der Alte | 7.671 | 8.326 | +655 (+8,5%) | 102 | 40 |
| Fritz Grade | 4.779 | 5.321 | +542 (+11,3%) | 92 | 36 |
| Johann | 775 | 849 | +74 (+9,5%) | 19 | 10 |
| Werner | 6.247 | 6.494 | +247 (+4,0%) | 59 | 27 |
| **samen** | **19.472** | **20.990** | **+1.518 (+7,8%)** | **272** | **113** |

Een *los stuk* is een aaneengesloten stuk film waarin een persoon in beeld is. Hoe minder losse
stukken, hoe minder gaten in de lijn van die persoon. In de tijdlijn hieronder is dat te zien.

![Tijdlijn per filmpje en per persoon: wat al klopte, wat erbij kwam en wat werd weggehaald](fotos/uitkomst_tijdlijn.png)

*Per filmpje en per persoon wanneer die persoon in beeld is. Grijs klopte al na stap 1. Oranje
is erbij gekomen en blauw is weggehaald door stap 2 en 3.*

Dit betekent dat de ground truth nu veel beter laat zien wanneer iemand in beeld is. Dat is
precies wat het project moet meten: hoe vaak en wanneer elke persoon te zien is.

### Hoe we weten dat dit klopt

- **De bestanden zijn nog precies dezelfde.** `0_check_setup.py` controleert de 12 videobestanden,
  de pixels van alle beelden, de foto's en de vastgelegde uitkomsten. De uitkomst is *Alles in orde.*
- **De code doet in deze indeling nog hetzelfde.** Stap 0 is in deze indeling opnieuw gedraaid en gaf
  precies dezelfde tracks en dezelfde bestanden voor de labelapp als de vastgelegde versie.
- **De labelapp is getest.** Alle 310 automatische tests slagen.
- **De ground truth is los nageteld.** Een apart programma kwam op dezelfde aantallen per persoon uit.

### Wat er niet in zit

- **Alleen de vier personen zijn nagekeken.** Figuranten zijn in stap 2 en 3 niet nagekeken en
  staan niet in de ground truth. Hun labels staan alleen in `labels.csv`.
- **De plek van een verbeterd kader is minder precies dan de naam.** In stap 3 kan een kader op
  dezelfde plek blijven staan als in het vorige beeld. Een persoon staat dus in het juiste beeld,
  maar het kader kan iets naast het gezicht staan, zeker bij de 1.607 kaders zonder kader van de
  detector. Voor *wie is er in beeld* maakt dat niets uit; bij een test per gezicht moet je met
  overlap werken.
- **Elk beeld is door één persoon nagekeken.** Er is geen tweede persoon die dezelfde beelden
  beoordeeld heeft, dus we weten niet hoe vaak twee mensen het oneens zouden zijn.


## Alles opnieuw doen, en waar je op moet letten

De volledige volgorde, vanuit de map `labelen`:

| Stap | Mac | Windows |
|---|---|---|
| Controleren | `.venv/bin/python stap_0_voorbereiding/0_check_setup.py` | `.venv\Scripts\python stap_0_voorbereiding\0_check_setup.py` |
| 0. Zoeken en volgen | `.venv/bin/python stap_0_voorbereiding/1_track_faces.py` | `.venv\Scripts\python stap_0_voorbereiding\1_track_faces.py` |
| 0. Tracks controleren | `.venv/bin/python stap_0_voorbereiding/2_check_all_tracks.py` | `.venv\Scripts\python stap_0_voorbereiding\2_check_all_tracks.py` |
| 0. Klaarzetten | `.venv/bin/python stap_0_voorbereiding/3_make_label_items.py` | `.venv\Scripts\python stap_0_voorbereiding\3_make_label_items.py` |
| 1. Labelen | dubbelklik `stap_1_tracks_labelen/START_MAC.command` | dubbelklik `stap_1_tracks_labelen\START_WINDOWS.bat` |
| 2. Nakijken | `.venv/bin/python stap_2_beelden_nakijken/check_labels.py` | `.venv\Scripts\python stap_2_beelden_nakijken\check_labels.py` |
| 3. Verbeteren | `.venv/bin/python stap_3_fouten_verbeteren/fix_labels.py` | `.venv\Scripts\python stap_3_fouten_verbeteren\fix_labels.py` |
| 3. Ground truth | `.venv/bin/python stap_3_fouten_verbeteren/make_ground_truth.py` | `.venv\Scripts\python stap_3_fouten_verbeteren\make_ground_truth.py` |

### Waar je op moet letten

- **De uitkomsten liggen vast.** De labels horen bij precies deze kaders en tracknummers. Een
  andere computer of een andere versie van een pakket kan andere kaders en dus andere tracknummers
  geven, en dan passen de labels niet meer. Daarom staan de controlegetallen van de belangrijke
  bestanden in `checksums.sha256`, en overschrijven de programma's die bestanden niet.
  Wil je bewust een nieuwe versie, dan moeten de controle, het labelen en het nakijken helemaal
  opnieuw.
- **Sla de CSV-bestanden niet op in Excel.** Bekijken mag, maar Excel slaat een bestand net anders
  op, en dan klopt het controlegetal niet meer.
- **Geen iCloud of OneDrive.** Een clouddienst maakt soms kopieën met namen als `000010 2.jpg`, en
  dat kan het project beschadigen. `0_check_setup.py` waarschuwt daarvoor.
- **Op Windows: een pad zonder letters als é.** OpenCV kan op Windows soms geen bestanden lezen
  als er zulke letters in het pad staan.

| Wat je ziet | Wat je doet |
|---|---|
| `FOUT:` aan het eind van `0_check_setup.py` | Lees de regel: die zegt welk bestand of welke versie niet klopt. Gebruik dan de vastgelegde uitkomsten en draai stap 0 niet opnieuw. |
| De pagina van stap 2 of 3 opent niet vanzelf | Typ het adres over dat in de terminal staat, bijvoorbeeld `http://localhost:8020`. |
| Het eerste beeld na een herstart laadt lang | Dat klopt: de video wordt op volgorde gelezen tot het beeld waar je gebleven was. |
| `python3.12` of `py -3.12` wordt niet gevonden | Python 3.12 is nog niet geïnstalleerd, zie [Installeren](#installeren-op-mac-en-windows). |
| Een rode balk in de labelapp | De tekst in de balk zegt wat er aan de hand is. Meestal is het venster van de app gesloten: start de app opnieuw. |

De plaatjes in deze uitleg maakt [`fotos/maak_fotos.py`](fotos/maak_fotos.py) (daarvoor is ook
matplotlib nodig). De schermafbeeldingen zijn gemaakt van de echte programma's.
