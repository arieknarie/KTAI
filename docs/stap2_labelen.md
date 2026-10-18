# Stap 2: labelen

[← terug naar het overzicht](../README.md)

In deze stap legt een mens vast wie elk gezicht is dat de computer in stap 1
gevonden heeft. Zo ontstaat het antwoordenblad: een tabel waarin bij elk
gevonden gezicht staat wie het werkelijk is. Met die tabel controleren we
later of het herkenningsprogramma gelijk heeft. Een voorbeeld van die tabel
staat bij punt 6 van [Wat er na het labelen gebeurt](#wat-er-na-het-labelen-gebeurt).
Dit document legt uit wat er gelabeld wordt, welke keuzes we daarbij gemaakt
hebben en waarom, hoe het programma voor het labelen werkt, en wat er na het
labelen met de labels gebeurt. Het programma voor het labelen is klaar; het
labelen zelf is nog niet begonnen.

De persoon die labelt (de *labelaar*) gebruikt een klein programma in de
browser: de labelapp. De labelapp staat in de map [`labeling/`](../labeling/),
met een eigen handleiding voor de labelaar:
[`labeling/README.md`](../labeling/README.md). Het programma
[`code/make_label_items.py`](../code/make_label_items.py) zet alles klaar wat
de labelapp laat zien.


## Waarom een mens labelt

Het antwoordenblad moet onafhankelijk zijn van het herkenningsprogramma dat we
willen testen. Als een computerprogramma het antwoordenblad zou invullen, en
dat programma vergist zich op dezelfde plekken als het programma dat we testen,
dan zouden die vergissingen nooit opvallen. Daarom doet een mens het, zonder
hulp of suggesties van een computer: de labelapp laat alleen het beeld en de
kaders zien, en zegt bij de stills en de video's nooit wie iemand zou kunnen
zijn. Alleen bij de twee foto's van de acteurs staat de naam van de map erbij,
omdat die mappen wel gecontroleerd zijn.


## Wat er gelabeld wordt

De labelaar ziet drie soorten beelden. Elk beeld noemen we een *item*.

**Twee foto's van de acteurs.** Van de 23 gewone foto's van de vier acteurs
staan er op 21 maar één gezicht. Bij die foto's weten we al wie het is: de
foto's staan in een map met de naam van de persoon. Die 21 foto's krijgen hun
label dus automatisch (ze staan in `labeling/automatic_labels.csv`). Op twee
foto's (`werner4.jpg` en `werner5.jpg`) staan meer mensen. Daar moet de
labelaar aanwijzen wie wie is: 5 gezichten in totaal.

**33 stills.** Een still is een losse foto uit de film. In de map
`pictures/inCharacter/` staan 35 bestanden, maar twee stills staan er twee keer
in: dezelfde foto staat dan in twee verschillende mappen, onder een andere
bestandsnaam. Zo blijven er 33 verschillende stills over, met samen 90
gezichten. De stills staan in mappen met een naam, maar die indeling is
nooit gecontroleerd en kan fout zijn. Daarom krijgt de labelaar die namen niet
te zien (zie hieronder).

**2.896 tracks uit de video's.** Een track is één gezicht dat de computer in
stap 1 heeft gevolgd over een reeks beelden na elkaar. Van elke track ziet de
labelaar één beeld, met een geel kader om het gezicht, en de keuze geldt voor
de hele track.

Samen zijn dat 2.931 items met 2.991 gezichten. Bij de vorige manier van
volgen waren het 3.240 items. Sinds de nieuwe manier van volgen in
[stap 1](stap1_gezichten_vinden_en_volgen.md) (versie 5) mag een track
doorlopen op een kader waarvan de detector (het programma dat in stap 1 de
gezichten zocht) minder zeker is: een *verlenging*. Doordat een track nu
doorloopt, valt een gezicht minder vaak uiteen in losse tracks, en heeft de
labelaar 309 items minder te doen.

Bij elk gezicht kiest de labelaar een van zeven knoppen: een van de vier
personen (Der Alte, Fritz Grade, Johann of Werner), *Figurant* (iemand
anders), *Geen gezicht* (in het kader staat iets dat geen gezicht is) of
*Weet niet* (er staat een gezicht, maar de labelaar kan niet zeggen wie het
is). Ziet de labelaar een gezicht van een van de vier personen zonder kader,
dan tekent de labelaar er zelf een kader omheen (zie hieronder).


## Keuzes die we gemaakt hebben, en waarom

**De labelaar gokt niet.** Twijfelt de labelaar, dan kiest de labelaar *Weet
niet*. Een gok die fout is, komt op het antwoordenblad en zou een goede
herkenning straks fout rekenen. Hetzelfde geldt als de labelaar twijfelt of er
wel een gezicht in het kader staat: dan is het *Weet niet*, en *Geen gezicht*
alleen als de labelaar het zeker weet. Zo weten we later hoe vaak de detector
zich zeker vergist heeft: de
kaders met *Geen gezicht* zijn zeker geen gezicht. Hoe vaak de detector zich
misschien vergist heeft, weten we niet precies, want *Weet niet* bevat ook
gezichten die de labelaar wel zag maar niet kon herkennen, bijvoorbeeld omdat
ze te donker of te klein zijn. Het aantal kaders met *Geen gezicht* is dus het
minimum, en *Geen gezicht* en *Weet niet* samen het maximum.

**Geen namen in beeld.** Bij de stills ziet de labelaar geen mapnaam en geen
bestandsnaam, alleen *Still 1 van 33* enzovoort, en de stills staan in een
volgorde die niets met de mappen te maken heeft. Ook in de bestanden van de
labelapp heet een still alleen `still_01`, `still_02` enzovoort. Welk bestand
bij welke still hoort, staat niet in de map `labeling/`, maar in
`data/stills_index.csv`. Om dezelfde reden heten de video's op het scherm van
de labelapp *Video 1*, *Video 2* en *Video 3*: de titel van een van de
fragmenten bevat een naam, en die naam zou de labelaar kunnen sturen. Video 1
is het fragment *die Auferstehung*, Video 2 is *Mon Gars Filmmusik* en Video 3
is *Go Back Johann*. Dit gaat over wat de labelaar op het scherm ziet. De
labelaar downloadt wel het hele
project, dus de namen staan ook op de computer van de labelaar: in
`data/stills_index.csv`, in de mappen van `pictures/inCharacter/` en in de
mapnamen in `labeling/images/frames/`. De handleiding vraagt de labelaar om
die tijdens het labelen niet te openen.

**Welk beeld van een track.** Van een track ziet de labelaar het beeld waarin
het kader groot is en de detector het zekerst is. Dat is het beeld waarin de
score (het getal voor hoe zeker de detector is) maal de breedte van het kader
het hoogst is. We hebben ook andere regels geprobeerd, bijvoorbeeld het
scherpste beeld kiezen. Op 40 willekeurige tracks (van de vorige manier van
volgen) hebben we de beelden van de verschillende regels naast elkaar bekeken
zonder te weten welke regel welk beeld had gekozen. Geen enkele andere regel
gaf duidelijk vaker een beter beeld, en de regels met scherpte kozen in de
gecontroleerde tracks vaker een beeld waarin het kader juist níét op het
goede gezicht stond.
Daarom blijft de huidige regel.

**Automatisch figurant, maar niet ongemerkt.** Op een still met acht gezichten
zijn de meeste mensen figuranten. Om de labelaar niet acht keer *Figurant* te
laten klikken, kunnen de gezichten waarvoor de labelaar niets kiest vanzelf
*Figurant* worden. Klikt de labelaar op Volgende (of drukt de labelaar op
Enter), dan zegt de app eerst in een geel vak hoeveel gezichten nog geen keuze
hebben. Pas bij de tweede keer Volgende worden die gezichten *Figurant*. Kiest
de labelaar tussendoor toch nog iets voor een van die gezichten, dan
waarschuwt de app bij de volgende klik eerst opnieuw. Zo slaat niemand per
ongeluk gezichten over. In het bestand met de labels staat bij zo'n
automatische figurant `auto` in de kolom `how` (bij een zelf gekozen label
`chosen`), zodat we later altijd kunnen zien welke figuranten automatisch
zijn.

**Ook de heel korte tracks.** 937 tracks zijn maar één beeld lang. In zo'n
korte track kan een echt gezicht staan, maar ook een lamp of een hand. In een
steekproef bij de vorige manier van volgen was ongeveer 4 van de 10 korte
tracks (van 1 tot 4 beelden) een echt gezicht (zie
[Controle van het volgen](stap1_controle.md#korte-tracks)). Daarom worden alle
tracks gelabeld, ook de kortste.

**Gemiste gezichten tekenen, maar alleen van de vier personen.** De detector
mist ook gezichten (zie het eind van dit document). Een gezicht zonder kader
komt niet op het antwoordenblad. Daarom kan de labelaar in de labelapp zelf
een kader tekenen om een gezicht dat de computer helemaal gemist heeft. Dat
vragen we alleen bij de vier personen, niet bij figuranten. Alle gemiste
figuranten tekenen zou in drukke scènes uren kosten, en elke labelaar zou dat
anders doen. Voor het antwoordenblad gaat het vooral om de vier personen: die
moet het herkenningsprogramma vinden, en van hen tellen we hoe vaak ze in
beeld zijn.

**Drie stills komen uit de fragmenten.** Bij het klaarzetten vergelijkt het
programma elke still met alle beelden van de drie fragmenten. Drie stills
blijken (bijna) hetzelfde beeld te zijn als een beeld uit een fragment. Dat
staat in `data/stills_index.csv` (kolommen `uit_video` en `uit_frame`). Dat is
belangrijk als we de stills later als extra voorbeeldfoto's willen gebruiken,
naast de gewone foto's van de acteurs: een still die bijna hetzelfde is als een
beeld uit een fragment, maakt de test op dat fragment te makkelijk. Zo'n still
mag dus geen voorbeeld zijn bij het herkennen in datzelfde fragment. Een vierde
still, `still_14`, is geen beeld uit een fragment, maar wel een andere foto van
hetzelfde moment als in het fragment *Mon Gars Filmmusik* (Video 2 in de
labelapp), in het shot van beeld 731 tot en met 1432: dezelfde drie mensen, in
dezelfde kleding en in dezelfde opstelling als rond beeld 800. Het programma
voor het klaarzetten ziet dat niet, omdat het alleen hele, verkleinde beelden
vergelijkt. Ook `still_14` mag dus geen voorbeeld zijn bij het herkennen in dat
fragment.


## Hoe de labelapp werkt

De labelapp is een klein programma (`labeling/app.py`) dat alleen Python nodig
heeft: de gratis programmeertaal waarin de app geschreven is. Extra onderdelen
voor Python zijn niet nodig, en er hoeft verder niets geïnstalleerd te
worden: alle beelden staan al klaar in `labeling/images/` (2.134 plaatjes,
78 MB).

Als de labelaar de app start, start de app een kleine webserver: het deel van
de app dat de labelpagina aan de browser geeft en de keuzes bewaart. Die
webserver is alleen op de eigen computer bereikbaar. Daarna opent de app de
labelpagina in de browser. Er gaat niets via internet.

**Alles past op één scherm.** De labelpagina is zo gemaakt dat de labelaar
nooit hoeft te scrollen: links de foto's van de vier acteurs om mee te
vergelijken (op een smal scherm boven het beeld), in het midden het beeld (zo
groot als past), rechts de knoppen en een uitvergroting van het gezicht dat
aan de beurt is. Dat is getest op zeven schermgroottes, van een kleine laptop
(1024 × 580 pixels) tot een groot scherm (1920 × 950).

**Een korte uitleg in de app.** De eerste keer dat de labelpagina opent, start
vanzelf een rondleiding van twaalf kleine stappen langs alles wat op het
scherm staat. Later opent de knop *Uitleg* bovenaan die rondleiding opnieuw.
Zo hoeft de labelaar niet alles uit de handleiding te onthouden.

**Andere gevonden kaders in grijs.** Bij een track geldt de keuze alleen voor
het gezicht in het gele kader. Vaak heeft de computer in hetzelfde beeld nog
andere kaders gevonden: bij 2.735 van de 2.896 tracks. Die andere kaders staan
er als dun grijs stippelkader bij. Ze komen elk in een eigen track aan de
beurt. Het grijze kader laat de labelaar zien dat de computer daar wel iets
gevonden heeft, zodat de labelaar dat gezicht niet als gemist gaat tekenen.

**Een gemist gezicht tekenen.** Staat er een gezicht van een van de vier
personen in beeld zonder enig kader (ook geen grijs kader), dan klikt de
labelaar op *+ Gemist gezicht tekenen* (of drukt op T), sleept met de muis een
kader om het gezicht en kiest wie het is. *Geen gezicht* kan daar niet: een
verkeerd getekend kader haalt de labelaar weg met *Weghalen* (of de toets
Delete). In `labels.csv` staat bij zo'n gezicht `getekend` in de kolom `how`.
Waarom alleen de vier personen, staat hierboven bij de keuzes.

**Elke keuze wordt meteen bewaard**, in het bestand `labeling/labels.csv`. De
app schrijft eerst een tijdelijk bestand en vervangt daarna in één keer het
oude bestand, zodat `labels.csv` nooit half geschreven kan zijn, ook niet als
de stroom uitvalt. Bij het starten (als er al keuzes zijn) en daarna elk
kwartier waarin er gelabeld wordt, maakt de app een reservekopie in
`labeling/backups/`; de laatste 40 blijven bewaard. Lukt bewaren even niet
(bijvoorbeeld omdat het venster van de app per ongeluk gesloten is), dan toont
de pagina een rode balk en onthoudt de browser de keuzes tot de app weer
draait. De labelaar stuurt `labels.csv` per mail naar Marc, aan het eind en
ook tussendoor (zie punt 3 van
[Wat er na het labelen gebeurt](#wat-er-na-het-labelen-gebeurt)).

**Vergissingen worden zo veel mogelijk voorkomen.** Een toets die ingedrukt
blijft, telt maar één keer. Een dubbelklik of twee snelle toetsaanslagen
tellen ook maar één keer: de app laat pas kiezen als een nieuw beeld er een
fractie van een seconde staat. Bij een track gaat de app pas verder als er
gekozen is; een track overslaan kan alleen met de pijltjestoets →. Na een
keuze bij een track staat boven het volgende beeld wat er net gekozen is,
zodat een verkeerde toets opvalt. Die regel staat alleen bij het item direct
na de keuze; bladert de labelaar verder, dan verdwijnt hij. Een "Beeld
lichter"-stand maakt donkere gezichten vanzelf lichter; de app meet daarvoor
hoe donker het kader is van het gezicht dat op dat moment aan de beurt is. Bij
ongeveer een derde van de tracks (965 van de 2.896) is het gezicht in het
getoonde beeld namelijk erg donker: gemiddeld minder dan 40 op een schaal van
0 (zwart) tot 255 (wit). Van alle kaders in de drie fragmenten is zelfs ruim
de helft (57%) zo donker.

**Veiligheid.** Alleen de eigen labelpagina kan labels bewaren of opvragen;
een andere website die in dezelfde browser openstaat, kan dat niet. De app
bewaart alleen keuzes voor gezichten die in de lijst van de labelapp staan, en
alleen een van de zeven keuzes. Een getekend gezicht bewaart de app alleen als
het kader binnen het beeld ligt; bij welk bestand en beeldnummer het getekende
gezicht hoort, neemt de app uit die lijst, niet uit de browser. Er draait per
map altijd maar één app tegelijk, zodat er nooit twee programma's tegelijk in
`labels.csv` schrijven.

**Getest.** De labelapp is getest in Chrome, met Python 3.12 en (voor de
webserver) ook Python 3.9, met 194 automatische tests, die allemaal slagen.
Die tests staan niet in het project, dus een teamlid kan ze niet zelf opnieuw
draaien. De tests controleerden: kiezen met muis en toetsen (de cijfers 1 tot
7 ook op het aparte cijferblok en op een Frans of Belgisch toetsenbord),
"Beeld lichter", de automatische figuranten, een gemist gezicht tekenen en
weghalen, de korte uitleg, terugbladeren en wijzigen, dubbelklikken,
verdergaan na een herstart, de reservekopieën, de rode balk en het alsnog
bewaren na een storing, de verplichte naam, twee keer tegelijk starten, een
`labels.csv` die in Excel openstaat of door een ander programma is opgeslagen,
de beveiliging, en het scherm op zeven groottes. **Op Windows is de app nog
niet getest.**


## Wat er na het labelen gebeurt

Dit is het plan voor het labelen zelf en voor wat daarna met de labels
gebeurt. Geen van deze stappen is al gedaan.

1. **Delen.** De nieuwe versie van het project komt op GitHub, op de branch
   `facenet-stress-tests-v2` (een branch is een aparte versie van het project
   op GitHub). De labelaar downloadt het project daarvandaan. Zolang die
   branch niet op GitHub staat, werken de links in de handleiding nog niet.
   Het bestand waarin de labelapp de keuzes bewaart, `labeling/labels.csv`,
   gaat nooit mee naar GitHub: het staat in `labeling/.gitignore`, de lijst
   met bestanden die git overslaat (git is het programma dat de versies van
   het project bijhoudt en naar GitHub stuurt). Proefkeuzes van iemand uit
   het team blijven dus op diens eigen computer, en de labelaar begint
   vanzelf met een lege lijst.
2. **Labelen.** De labelaar volgt de handleiding en labelt alle items. Na de
   eerste sessie (de foto's, de stills en de eerste tracks van Video 1) labelt
   iemand uit het team dezelfde items in een eigen kopie van de map
   `labeling/`, en vergelijkt pas daarna met de keuzes van de labelaar; zo
   merken we vroeg of de labelaar een regel uit de handleiding anders leest
   dan bedoeld. De items van deze proefronde tellen niet mee bij de tweede
   labelaar (punt 5).
3. **Terugsturen.** De labelaar stuurt `labels.csv` per mail naar Marc, aan
   het eind en ook tussendoor (zie stap 6 van de
   [handleiding](../labeling/README.md#stap-6-je-keuzes-naar-marc-sturen)).
   Marc zet het bestand in de map `labels/` van het project en zet het met
   `git add labels/labels.csv`, `git commit` en `git push` op GitHub. Wie in
   het team de labels wil hebben, haalt ze daarna op met `git pull` op de
   branch `facenet-stress-tests-v2`; de keuzes van de labelaar staan dan in
   `labels/labels.csv`. Open het bestand daarbij niet in Excel om het op te
   slaan: Excel kan het bestand veranderen. Wie de keuzes van de labelaar in
   de labelapp wil bekijken, kopieert `labels/labels.csv` naar
   `labeling/labels.csv` op de eigen computer (geef een eigen proefbestand met
   die naam eerst een andere naam); die kopie blijft op de eigen computer.
4. **Labels nakijken.** We kijken of elk gezicht gelabeld is, hoe vaak elke
   keuze voorkomt, hoe vaak *Weet niet* gekozen is, hoeveel figuranten
   automatisch zijn en hoeveel gezichten de labelaar zelf getekend heeft. We
   gebruiken ook drie controles die geen extra labelwerk kosten. Twee kaders liggen daarbij
   *over elkaar* als ze in hetzelfde beeld minstens 30% overlappen: het stuk
   dat de twee kaders gemeen hebben, is minstens 30% van de oppervlakte die ze
   samen bedekken. Dat is dezelfde maat als bij het volgen in
   [stap 1](stap1_gezichten_vinden_en_volgen.md#de-regels).
   (a) Twee tracks die in hetzelfde beeld voorkomen en waarvan de kaders in dat
   beeld niet over elkaar liggen, kunnen niet allebei dezelfde van de vier
   personen zijn; twee figuranten in één beeld kan wel. (b) Als de detector
   hetzelfde gezicht twee keer vond (twee kaders van verschillende tracks over
   elkaar), moeten beide tracks hetzelfde label hebben, of is een van beide
   *Geen gezicht*. Twee kaders over elkaar komen 964 keer voor, bij 379 paren
   van tracks. (c) De stills `still_21`, `still_23` en `still_30` zijn beelden
   uit de fragmenten (zie *Drie stills komen uit de fragmenten* hierboven).
   Hun negen gezichten heeft de computer dus ook in de fragmenten gevonden, in
   tracks. Elk van die negen gezichten hoort hetzelfde label te krijgen als de
   track met hetzelfde gezicht. Welke track dat is, zoeken we na het labelen
   op door de kaders van de still op het beeld uit het fragment te leggen.
5. **Een tweede labelaar.** Een tweede persoon labelt een deel van de items
   opnieuw, in een eigen kopie van de map. De labelapp laat nu altijd alle
   items zien; voor de tweede labelaar maken we dus nog een aparte lijst met
   alleen dat deel. De labelapp van de tweede labelaar laat de keuzes van de
   eerste labelaar niet zien, want die staan alleen in de map `labels/`. Dat
   deel kiezen we zo dat het iets zegt over de meeste gezichten: ongeveer 100
   tracks, waarbij lange tracks (met veel gezichten) meer kans hebben om
   gekozen te worden, plus 30 korte tracks en 10 stills, zonder de items uit
   de proefronde (punt 2). We loten dat deel met een vast startgetal voor de
   computer, zodat de loting later precies te herhalen is. Hoe vaak de twee
   labelaars hetzelfde kiezen (en Cohen's kappa, een maat voor overeenstemming
   waarbij toevallige overeenstemming eruit gehaald is), laat zien hoe
   betrouwbaar het antwoordenblad is. Apart tellen we hoe vaak de twee
   labelaars twee verschillende zekere keuzes maakten (een van de vier
   personen, *Figurant* of *Geen gezicht*): alleen zo'n verschil maakt het
   antwoordenblad fout, een verschil met *Weet niet* niet. Kiezen de twee
   labelaars bij een gezicht iets anders, dan wordt dat gezicht *Weet niet*.
   De tweede labelaar zet het eigen bestand in de map `labels/` onder een
   eigen naam, zodat het bestand van de eerste labelaar niet overschreven
   wordt.
6. **Het antwoordenblad per beeld maken.** Na het labelen maken we één tabel:
   het antwoordenblad. Daarvoor combineren we twee bestanden:
   `data/tracks/detections_0.3.csv`, met elk kader dat de detector gevonden
   heeft (fragment, beeldnummer, kader en tracknummer), ook de *verlengingen*
   (de zwakkere kaders waarmee een track sinds versie 5 mag doorlopen), en
   `labels/labels.csv`, met de keuzes van de labelaar (één keuze per track,
   plus de getekende gezichten). Elk kader krijgt de keuze van zijn track. Een
   getekend gezicht in het beeld van een track wordt één extra rij, alleen voor
   dat ene beeld; die rij hoort bij geen enkele track (de laatste rij
   hieronder). Een verzonnen voorbeeld (deze getallen en namen komen niet uit
   de echte fragmenten; het is hetzelfde voorbeeld als in
   [het overzicht](../README.md#hoe-het-antwoordenblad-eruitziet)):

   | Fragment | Beeld | Kader om het gezicht | Track | Wie |
   |---|---|---|---|---|
   | Fragment 1 | 4700 | x 300, y 90, 80 × 80 | 3301 | Werner |
   | Fragment 1 | 4701 | x 302, y 91, 80 × 80 | 3301 | Werner |
   | Fragment 1 | 4701 | x 40, y 120, 40 × 40 | 3302 | Figurant |
   | Fragment 1 | 4701 | x 500, y 100, 50 × 50 (getekend) | geen | Johann |

   Het kader zegt waar het gezicht in het beeld staat: x en y zijn de
   linkerbovenhoek, daarna volgen breedte × hoogte, in pixels. In stap 4 van
   het project zet het herkenningsprogramma bij elke rij wie het programma
   denkt dat het is. In stap 5 vergelijken we die gok per rij met de kolom
   *Wie*. Zo zien we hoeveel procent het programma goed heeft. Ook tellen we
   in stap 5 hoe vaak en wanneer elke persoon in beeld is: één keer met deze
   tabel en één keer met wat het herkenningsprogramma zegt. In stap 6 kijken
   we wanneer het programma zich vergist, bijvoorbeeld bij donkere, kleine of
   van opzij gefilmde gezichten.

   We koppelen een keuze aan een gezicht via het fragment, het beeldnummer en
   het kader, niet alleen via het nummer van de track. Als we later de
   detector anders instellen (bijvoorbeeld bij de test met lage
   beeldkwaliteit), kloppen de tracknummers namelijk niet meer. Dan koppelen
   we elk nieuw kader aan het gelabelde kader dat er in hetzelfde beeld het
   meest mee overlapt (minstens de helft). Gezichten met *Geen gezicht* tellen
   niet als gezicht; gezichten met *Weet niet* houden we apart. *Weet niet*
   zal vooral vallen bij donkere, kleine en weggedraaide gezichten, en juist
   die gezichten onderzoeken we in stap 6. Daarom melden we in stap 5 en 6 bij
   elke groep gezichten (donker of licht, klein of groot, recht of van opzij)
   ook welk deel van die groep een ander label dan *Weet niet* heeft. Hoe lang
   iemand in beeld is, tellen we alleen met de zekere labels; dat is dus een
   ondergrens, en daarnaast melden we hoeveel gezichten in dezelfde scènes
   *Weet niet* zijn.

   De getekende gezichten tellen we ook apart. Zo zien we hoe vaak de
   detector juist een van de vier personen mist. Dat getal gaat alleen over
   de beelden die de labelaar te zien krijgt, één per track; in de andere
   beelden van de fragmenten tekent niemand gemiste gezichten.

   Eén keuze per track werkt alleen als het kader de hele track op hetzelfde
   gezicht (of hetzelfde ding, zoals een lamp) blijft. Bij de
   [controle van het volgen](stap1_controle.md) is dat voor elke track van twee
   of meer beelden nagekeken. Waar een track halverwege op een andere persoon
   of op iets anders terechtkwam, is dat stuk losgeknipt tot een eigen track
   (161 knippen in 123 tracks), dus die stukken krijgen hun eigen label. Bij 26
   tracks was dat niet te zeggen, omdat het beeld te donker of te onduidelijk
   was; daar kiest de labelaar waarschijnlijk *Weet niet*. Een fout die bij de
   controle niet opviel, kan nog in een track zitten.
7. **Afspraken voor tellen en tijdlijn.** Voor stap 5 van het project (hoe vaak
   en wanneer iemand in beeld is) leggen we vooraf vast wat "in beeld" betekent.
   Een persoon is in een beeld te zien als daar een gezicht met die persoon is
   gevonden, of als dat beeld valt binnen een track van die persoon waarin het
   gezicht heel even niet gevonden werd. Dat komt vaak voor: in de 2.896
   tracks ontbreekt het gezicht 1.976 keer heel even (hooguit 12 beelden,
   ongeveer een halve seconde), samen in 5.351 beelden. De track gaat na zo'n
   gat verder op hetzelfde gezicht, dus de persoon is er in die korte tijd
   waarschijnlijk nog. We rapporteren beide: alleen de gevonden gezichten, en
   met die korte gaten opgevuld.

Een beperking die we in het verslag moeten noemen: op het antwoordenblad staan
alleen de gezichten die de detector gevonden heeft, plus de gezichten van de
vier personen die de labelaar zelf tekent in het ene beeld per track. Een
figurant die de detector mist, en een van de vier personen die de detector
mist in een beeld dat de labelaar niet te zien krijgt, staan er niet op. In een
steekproef van 120 beelden uit de fragmenten vond de detector (met de
verlengingen van versie 5) 238 van de 278 duidelijk zichtbare gezichten,
ongeveer 86%; vooral kleine gezichten op de achtergrond ontbreken (zie [Stap 1](stap1_gezichten_vinden_en_volgen.md#hoeveel-gezichten-mist-de-detector)).
