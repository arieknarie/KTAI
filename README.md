# Gezichten herkennen in Das Boot

Dit project hoort bij de opdracht *Face Recognizer* van het vak Key Topics in
Artificial Intelligence aan de Open Universiteit. Wat de opdracht precies
vraagt, en bij welke stap van ons project elk deel van de opdracht hoort, staat
in [De opdracht](docs/opdracht.md). Wie de opdracht nog niet kent, leest dat
document het best als eerste.


## Wat we willen maken

We willen een computerprogramma maken dat naar een stukje film kijkt en bij
elk beeld zegt welke bekende personen erin te zien zijn. We gebruiken daarvoor
acht fragmenten uit de film *Das Boot*, en vier personen uit die film: Der
Alte, Fritz Grade, Johann en Werner.

Als het programma werkt, willen we laten zien hoe vaak elk van de vier personen
in beeld is en op welke momenten. Daarnaast willen we uitzoeken wanneer het
programma zich vergist: bijvoorbeeld als het beeld donker is, als iemand klein
in beeld staat, of als iemand van opzij gefilmd wordt.


## Hoe zo'n programma werkt

Een programma dat gezichten herkent, doet dat in twee stappen.

Eerst zoekt het programma in een beeld waar gezichten staan. Het programma
zet dan een rechthoek om elk gezicht dat het vindt (in de documenten heet zo'n
rechthoek een *kader*). Op dat moment weet het programma nog niet wíé het is,
alleen dát daar een gezicht staat. Voor dit zoeken gebruiken we een bestaand
programma van Google, de MediaPipe Face Detector, omdat de opdracht dat
aanraadt. Bij elk kader geeft MediaPipe ook een getal tussen 0 en 1, de
*score*: hoe zeker MediaPipe ervan is dat in het kader echt een gezicht staat.

Daarna bepaalt het programma wie het gezicht is. Daarvoor maakt een ander
bestaand programma van elk gezicht een lange rij getallen, een soort
vingerafdruk van het gezicht. Twee
foto's van dezelfde persoon geven vingerafdrukken die erg op elkaar lijken;
twee verschillende personen geven vingerafdrukken die meer van elkaar
verschillen. Van elk van de vier personen maken we vooraf vingerafdrukken van
gewone foto's van de acteur die de persoon speelt. Van die foto's weten we
zeker dat die acteur erop staat. Een gezicht in de film krijgt de naam van de
persoon waarvan de vingerafdruk het meest lijkt, maar alleen als de gelijkenis
groot genoeg is. Is de gelijkenis met alle vier te klein, dan is het iemand
anders.


## Waarom we eerst zelf vastleggen wie er in beeld is

Als het programma zegt "hier staat Werner", moeten we kunnen controleren of
dat klopt. Daarvoor moeten we van tevoren zelf weten wie er werkelijk in
beeld is. Je kunt het vergelijken met het nakijken van een toets: daarvoor heb
je een antwoordenblad nodig. Ons antwoordenblad wordt een tabel waarin bij elk
gezicht dat het programma in de fragmenten vindt, staat wie dat werkelijk is
(hieronder staat een voorbeeld). Zonder antwoordenblad kunnen we niet zeggen
hoe goed het programma is, en kunnen we ook niet onderzoeken in welke
situaties het programma zich vergist.

Dat antwoordenblad maken is het meeste werk van het hele project. De acht
fragmenten zijn samen ongeveer zeven en een halve minuut lang. Een video
bestaat uit losse beelden die snel na elkaar getoond worden (bij deze
fragmenten 24 of 25 beelden per seconde), en de acht fragmenten bestaan samen
uit 11.182 beelden. In al die beelden samen zet MediaPipe 37.003 kaders. Vaak
staat zo'n kader echt om een gezicht, maar ook vaak om een oor, een hand of een
pet. Niemand kan 37.003 keer met de hand aangeven wie dat is.

Daarom laten we de computer elk gezicht eerst volgen van beeld tot beeld. Als
iemand vijf seconden in beeld is, staat diezelfde persoon in ruim honderd
beelden achter elkaar. De computer ziet dat er in elk volgend beeld een kader
op bijna dezelfde plek staat, gaat ervan uit dat dat hetzelfde gezicht is, en
voegt al die kaders samen tot één stukje. In de documenten noemen we zo'n
stukje een **track**: één gezicht dat gevolgd wordt over een reeks beelden na
elkaar. Daarna legt een mens per track vast wie het is, met een eigen
programma: de *labelapp*. Dat vastleggen heet *labelen*, en de persoon die
labelt noemen we de *labelaar*. De labelaar ziet van elke track één beeld en
kiest maar één keer wie dat is. Die keuze geldt dan voor de hele track. Zo
blijven er 1.387 tracks over in plaats van 37.003 losse kaders.

Een track begint alleen bij een kader met een score van minstens 0,3. Een
track die al loopt, mag ook doorgaan met een kader waarover MediaPipe meer
twijfelt, met een score vanaf 0,2. Zo'n extra kader noemen we een
*verlenging*; van de 37.003 kaders zijn er 5.211 een verlenging. Door de
verlengingen breekt een track minder vaak af als MediaPipe even twijfelt.
Daardoor zijn er minder tracks om te labelen, en komen er meer gezichten op
het antwoordenblad.

### Hoe het antwoordenblad eruitziet

Na het labelen maken we van twee bestanden één tabel. In
`data/tracks/detections_0.3.csv` staat elk kader, ook de verlengingen: in welk
fragment, in welk beeld, waar het kader staat en bij welke track het kader
hoort. In `labels/labels.csv` staat per track de keuze van de labelaar, plus
de gezichten die de labelaar zelf getekend heeft (zie de laatste rij
hieronder). Elk kader krijgt de keuze van zijn track. De tabel die zo
ontstaat, is het antwoordenblad. Een verzonnen voorbeeld (deze getallen en
namen komen niet uit de echte fragmenten):

| Fragment | Beeld | Kader om het gezicht | Track | Wie |
|---|---|---|---|---|
| Fragment 1 | 4700 | x 300, y 90, 80 × 80 | 3301 | Werner |
| Fragment 1 | 4701 | x 302, y 91, 80 × 80 | 3301 | Werner |
| Fragment 1 | 4701 | x 40, y 120, 40 × 40 | 3302 | Figurant |
| Fragment 1 | 4701 | x 500, y 100, 50 × 50 (getekend) | geen | Johann |

Bij het kader staat waar de linkerbovenhoek ligt (x pixels vanaf links, y
pixels vanaf boven) en hoe breed en hoog het kader is. In de kolom *Wie* staat
een van de vier personen, *Figurant* (iemand anders), *Geen gezicht* (in het
kader staat bijvoorbeeld een lamp) of *Weet niet*. De laatste rij is een
gezicht dat MediaPipe gemist had, en waar de labelaar in de labelapp zelf een
kader omheen tekende. Zo'n getekend gezicht hoort niet bij een track en staat
daarom maar in één beeld op het antwoordenblad.

De labelapp bewaart de keuzes van de labelaar eerst in het bestand
`labeling/labels.csv` op de computer van de labelaar. De labelaar stuurt dat
bestand per mail naar Marc uit ons team, aan het eind van het labelen en ook
tussendoor. Marc zet het bestand in de map `labels/` op GitHub, de website
waar ons project staat.

In stap 4 laten we het programma bij elk gevonden gezicht zeggen wie het is.
In stap 5 zetten we dat antwoord per rij naast de kolom *Wie*. Zo zien we bij
elke rij of het programma gelijk heeft, en hoeveel procent van alle rijen goed
is. Ook tellen we hoe vaak iedereen in beeld is, één keer volgens het
antwoordenblad en één keer volgens het programma, en vergelijken we die twee.
In stap 6 kijken we bij welke rijen het programma zich vergist, bijvoorbeeld
bij donkere, kleine of van opzij gefilmde gezichten.

Het antwoordenblad heeft één belangrijke beperking: een gezicht waar MediaPipe
in stap 1 geen kader omheen zette, staat er meestal niet op. We hebben elk van
de 11.182 beelden bekeken. Daarbij zagen we samen 37.659 keer een gezicht, en
10.867 keer had dat gezicht geen kader (een gezicht dat in 50 beelden na elkaar
gemist wordt, telt 50 keer). Van de gemiste gezichten die we daarna nog eens
scherp bekeken hebben, klopte ongeveer 3 van de 4. Het gaat om kleine gezichten
op de achtergrond, maar ook om grote gezichten die donker, onscherp of half van
opzij in beeld zijn (zie
[Controle van het volgen](docs/stap1_controle.md#de-controle-van-elk-beeld)).
Ziet de labelaar in de labelapp een gezicht van een van de vier personen
zonder kader, dan tekent de labelaar er zelf een kader omheen. Dat kan alleen
in de beelden die de labelapp laat zien: van elke track één beeld. Een gezicht
zonder kader van iemand anders (een figurant) tekent de labelaar niet: dat zou
in drukke scènes uren kosten, en voor het antwoordenblad gaat het om de vier
personen.


## Waar we nu staan

| Stap | Wat er gebeurt | Stand | Uitleg |
|---|---|---|---|
| 1 | De computer zoekt in alle beelden de gezichten en volgt elk gezicht van beeld tot beeld. | klaar | [Stap 1: gezichten vinden en volgen](docs/stap1_gezichten_vinden_en_volgen.md) |
| 1b | We hebben elk kader van elke track van twee of meer kaders bekeken (810 tracks, 36.506 kaders): blijft het kader van begin tot eind op hetzelfde gezicht (of op hetzelfde ding, zoals een oor)? In 44 tracks schoof het kader naar iemand of iets anders. Die tracks zijn op die plekken geknipt, en elk stuk is een eigen track geworden. Bij 2 tracks was niet te zeggen of het kader op hetzelfde bleef. Daarnaast hebben we elk van de 11.182 beelden bekeken, om te tellen hoeveel gezichten de detector mist. | klaar | [Controle van het volgen](docs/stap1_controle.md) |
| 2 | Een mens geeft bij elke track aan wie het is. Zo ontstaat het antwoordenblad. | de labelapp is klaar; het labelen zelf is nog niet begonnen (wat er eerst nog moet gebeuren, staat onder de tabel) | [Stap 2: labelen](docs/stap2_labelen.md), en de [handleiding voor de labelaar](labeling/README.md) |
| 3 | Vingerafdrukken maken van de foto's van de vier acteurs. | nog niet begonnen | |
| 4 | In elk beeld van de fragmenten de gezichten herkennen. | nog niet begonnen | |
| 5 | Tellen hoe vaak iedereen in beeld is, een tijdlijn maken, en alles vergelijken met het antwoordenblad. | nog niet begonnen | |
| 6 | Uitzoeken wanneer het herkennen wel en niet werkt, en wat helpt. We kijken naar hoe groot het gezicht in beeld is, van welke kant het gefilmd is, waar we de grens leggen voor een gelijkenis die groot genoeg is, lage beeldkwaliteit, veranderd uiterlijk (baard, vuil) en slecht licht. | nog niet begonnen | |

Deze versie van het project staat op GitHub onder een eigen naam (een
*branch*): `facenet-stress-tests-v2`. Daar haalt de labelaar het project op
(zie de handleiding voor de labelaar). Op Windows is de labelapp nog niet
uitgeprobeerd. Als iemand uit
het team de labelapp uitprobeert, blijven die proefkeuzes op de eigen computer
(in `labeling/labels.csv`) en gaan ze niet mee naar GitHub. De labelaar begint
dus vanzelf met een lege lijst.

Hoe je alle stappen zelf opnieuw kunt draaien, staat in
[Zelf draaien](docs/zelf_draaien.md).


## Wat er in deze map staat

- `pictures/personal/` bevat 23 gewone foto's van de vier acteurs, in een map
  per persoon. Van deze foto's weten we zeker welke acteur erop staat. Op twee
  foto's staan ook andere mensen; daar wijst de labelaar in stap 2 aan welk
  gezicht van wie is. Deze foto's worden straks de voorbeelden waarmee het
  programma vergelijkt.
- `pictures/inCharacter/` bevat 35 losse beelden uit de film (*stills*). Twee
  stills staan er twee keer in, elke keer in een andere map en onder een andere
  bestandsnaam; het zijn dus 33 verschillende stills. Ook de stills staan in
  mappen met de naam van een persoon, maar die indeling is nooit gecontroleerd.
  Misschien gebruiken we de stills later als extra voorbeelden, naast de
  gewone foto's. Dan moeten we zeker weten wie erop staat, en daarom worden de
  stills in stap 2 opnieuw gelabeld.
- `movies/` bevat de acht filmfragmenten, in 4K waar de bron dat heeft. GitHub
  neemt geen bestanden groter dan 100 MB aan; daarom staan drie fragmenten in
  delen (bijvoorbeeld `Das Boot 2a` en `Das Boot 2b`), samen 12 bestanden. Waar
  elk fragment vandaan komt, staat in `movies/List_of_URLS`.
- `code/` bevat de programma's van dit project: voor stap 1, voor de controle
  van stap 1 en voor het klaarzetten van stap 2. Welk programma wat doet,
  staat in [Zelf draaien](docs/zelf_draaien.md).
- `data/` bevat wat die programma's gevonden hebben:
  - `data/tracks/` bevat alle kaders en alle tracks.
  - `data/audit/` bevat de controles van stap 1: het oordeel over elke track
    (`controle_alle_tracks.csv`) en de controle van elk beeld
    (`controle_alle_beelden.csv` en `controle_alle_beelden_vondsten.csv`). De
    plaatjes waarop we alles bekeken hebben, gaan niet mee naar GitHub, omdat
    het programma `code/check_all_tracks.py` ze opnieuw kan maken (zie
    [Controle van het volgen](docs/stap1_controle.md#zelf-nakijken)).
- `labeling/` bevat de labelapp: het programma waarmee een mens de gezichten
  labelt, met een eigen handleiding.
- `tests/` bevat de automatische tests van de labelapp (310 controles), met
  uitleg in [tests/README.md](tests/README.md).
- `labels/` is de map waarin Marc het bestand `labels.csv` van de labelaar op
  GitHub zet. Hoe dat werkt, staat in [labels/README.md](labels/README.md).
- `docs/` bevat de uitleg per stap en de plaatjes daarbij.
- `models/` bevat het bestand dat MediaPipe nodig heeft om gezichten te
  vinden. In de andere documenten heet dat bestand het *model*.
- `papers/` bevat de literatuur.
