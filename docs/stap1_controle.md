# Controle van het volgen

[← terug naar het overzicht](../README.md)

In stap 1 zoekt een programma, de detector, in elk beeld van de drie
filmfragmenten naar gezichten, en zet om elk gevonden gezicht een kader.
Daarna voegt de computer de kaders samen tot tracks. Een track is een reeks
kaders waarin hetzelfde gezicht gevolgd wordt over beelden na elkaar (zie
[Stap 1](stap1_gezichten_vinden_en_volgen.md)). In stap 2 geeft een mens, de
labelaar, bij elke track aan wie het is. De labelaar ziet van elke track maar
één beeld, en die ene keuze geldt voor alle kaders van de track. Zo ontstaat
het antwoordenblad: de tabel waarin straks bij elk kader staat wie het is, en
waarmee we het herkenningsprogramma nakijken (zie het voorbeeld in
[het overzicht](../README.md#hoe-het-antwoordenblad-eruitziet)).

Als het kader van een track halverwege overspringt naar een ander gezicht, of
naar bijvoorbeeld een lamp, krijgt een deel van de kaders dus de verkeerde naam
op het antwoordenblad. Daarom hebben we elke track bekeken waarin dat kan
gebeuren. In dit document
staat hoe we dat gedaan hebben, wat eruit kwam, hoe we de fouten verbeterd
hebben en wat nog onzeker is. Deze controle hoort bij de manier van volgen die
we nu gebruiken (versie 5 in [Stap 1](stap1_gezichten_vinden_en_volgen.md)).
Een eerdere versie hebben we alleen met een steekproef gecontroleerd; dat staat
kort onder [De eerdere steekproef](#de-eerdere-steekproef).


## Hoe we gecontroleerd hebben

Vóór de controle waren er 2.736 tracks. Daarvan bestaan er 908 uit maar één
kader. In een track van één kader kan het kader nergens naartoe springen, dus
die tracks zijn niet bekeken (zie [Korte tracks](#korte-tracks)). De andere
1.828 tracks zijn allemaal bekeken.

**De vellen.** Het programma
[`code/check_all_tracks.py`](../code/check_all_tracks.py) maakt van elke track
een strook uitsneden. Een uitsnede is een klein vierkant stukje beeld rond het
kader, met het kader erin getekend en het beeldnummer eronder. Donkere
uitsneden maakt het programma lichter, zodat ook donkere scènes te beoordelen
zijn. Van een track van hoogstens 16 kaders komen alle kaders op de strook. Van
een langere track komen er 16 kaders op, gelijk verdeeld van begin tot eind,
plus de kaders rond de vier plekken waar het kader het meest verspringt, want
daar gaat het volgen het eerst mis. De stroken staan onder elkaar op 352
plaatjes, de vellen.

**De vraag bij elke track.** Blijft het kader van begin tot eind op dezelfde
persoon of op hetzelfde ding? Een hoofd dat draait, wegkijkt, deels bedekt is
of wazig wordt, is nog steeds dezelfde persoon, dus dat is goed. Een track die
van begin tot eind op dezelfde lamp staat, is ook goed. Zo'n track is geen
gezicht, maar de labelaar kiest daar *Geen gezicht*, en dat klopt dan voor alle
kaders van de track. Er is alleen gekeken óf het kader op hetzelfde blijft,
nooit wie iemand is.

De controle ging in drie rondes:

1. **Eerste ronde: alle vellen.** Elke track kreeg een oordeel: goed, fout of
   niet te zeggen. De uitkomst: 1.653 goed, 126 fout en 49 niet te zeggen.
2. **Elke vondst nagekeken.** De 175 tracks met fout of niet te zeggen zijn
   opnieuw bekeken, nu met een strook van álle kaders rond de plek waar het
   misging. Bij een foute track is daarbij precies vastgelegd in welke beelden
   het kader op iets anders staat. De uitkomst: 123 tracks echt fout, 26 toch
   goed, en bij 26 tracks blijft het niet te zeggen, omdat het beeld te donker
   of te onduidelijk is.
3. **Een tweede blik.** Om te zien of de eerste ronde fouten gemist heeft, zijn
   185 tracks nog een keer bekeken, los van het eerdere oordeel en met een
   nieuwe strook: 36 kaders gelijk verdeeld over de track, of alle kaders als
   de track korter is. Dat waren alle 125 tracks van 100 kaders of meer (zulke
   tracks duren minstens drie à vier seconden) en 60 willekeurig gekozen
   tracks van 5 tot 99 kaders. Tien keer verschilde het nieuwe oordeel van het
   eerdere. Die tien tracks zijn daarna nog een keer bekeken, weer met stroken
   van alle kaders, en dat oordeel besliste. Daaruit bleek dat de eerste ronde
   bij de 125 lange tracks één fout gemist had (track 1583, het eerste
   voorbeeld hieronder), en bij de 60 andere tracks geen. Ook bleek één track
   (track 104) toch goed, terwijl die na de tweede ronde fout heette. Welke 185
   tracks een tweede blik kregen, met de oordelen van elke ronde, staat in
   `data/audit/controle_tweede_blik.csv`.

Alle oordelen staan in `data/audit/controle_alle_tracks.csv`. Per track staan
daar het fragment, het eerste en het laatste beeld, het aantal kaders (kolom
`frames`), het oordeel (`goed`, `fout` of `niet_te_zeggen`), bij een foute
track de beelden waarin het kader op iets anders staat (`probleemframes`), en
een korte toelichting (`opmerking`). De tracknummers in dat bestand zijn de
nummers van vóór het knippen dat [verderop](#wat-we-met-de-fouten-gedaan-hebben)
staat.


## Wat eruit kwam

De tabel hieronder geeft de eindoordelen, verdeeld naar de lengte van de
track. De lengte tellen we in kaders: in hoeveel beelden de track een kader
heeft. Het gaat om de tracks van vóór het knippen. Daarom staan hier 125
tracks van 100 kaders of meer, en in
[Stap 1](stap1_gezichten_vinden_en_volgen.md#wat-eruit-kwam) (na het knippen)
122.

| Lengte van de track | Bekeken | Goed | Fout | Niet te zeggen |
|---|---|---|---|---|
| 2 tot 4 kaders | 637 | 620 | 7 | 10 |
| 5 tot 24 kaders | 732 | 660 | 64 | 8 |
| 25 tot 99 kaders | 334 | 283 | 45 | 6 |
| 100 kaders of meer | 125 | 116 | 7 | 2 |
| samen | 1.828 | 1.679 | 123 | 26 |

De fouten zitten vooral in tracks van 5 tot 99 kaders: daar was ongeveer 1 op
de 10 tracks fout.

In de 123 foute tracks staan samen 973 kaders op een andere persoon of op iets
anders. Dat is 1,8% van alle 54.599 kaders. (Die 54.599 kaders bestaan uit
43.414 gewone kaders en 11.185 verlengingen. De detector geeft elk kader een score:
hoe zeker de detector is dat er een gezicht staat. Een gewoon kader heeft een
score van 0,3 of hoger. Een verlenging is een kader met een score van 0,2 tot
0,3; zo'n kader mag alleen een track laten doorgaan die al loopt. Zie
[Stap 1](stap1_gezichten_vinden_en_volgen.md).) Zonder verbetering zouden die
973 kaders op het antwoordenblad de naam van de rest van hun track krijgen, en
dus meestal een verkeerde naam.

### Twee voorbeelden

**Een track die naar een ander gezicht overspringt.** Track 1583 is de fout die
de eerste ronde gemist had en die pas bij de tweede blik gevonden is.

![24 uitsneden van track 1583](stap1_controle_wissel.jpg)

*De 24 uitsneden van track 1583, van links naar rechts en van boven naar
beneden; het getal is het beeldnummer. In de bovenste rij staat het groene
kader op een gezicht dat van opzij te zien is. Rond beeld 1500 schuift het
kader naar een gezicht ernaast: in beeld 1503 staat het kader al op dat andere
gezicht, en is het eerste gezicht nog links in de uitsnede te zien. Daarna
blijft het kader op het andere gezicht, dat naar de camera kijkt. Na het
knippen zijn het twee tracks: beeld 1450 tot en met 1500 houdt nummer 1583, en
beeld 1501 tot en met 1604 is nu track 2859.*

**Een track die nooit een gezicht is.** De detector ziet soms een voorwerp voor
een gezicht aan en volgt dat voorwerp dan netjes. Het kader van track 263 staat
in alle 83 beelden op dezelfde meter; 72 van die 83 kaders zijn verlengingen.
Zo'n track is goed: de labelaar kiest *Geen gezicht*, en dat klopt dan voor
alle kaders.

![24 uitsneden van track 263](stap1_controle_geen_gezicht.jpg)

*24 van de 83 uitsneden van track 263, gelijk verdeeld van beeld 3041 tot en
met 3127. Het kader blijft steeds op dezelfde meter.*


## Wat we met de fouten gedaan hebben

Het programma [`code/track_faces.py`](../code/track_faces.py) knipt de 123
foute tracks op de plekken die in de kolom `probleemframes` staan. Elk stuk
wordt een eigen track. Zo krijgt het stuk op een andere persoon straks een
eigen naam van de labelaar, en een stuk op een lamp het label *Geen gezicht*.

Er is op 161 plekken geknipt. Dat gaf 160 nieuwe tracks: in één track lag
tussen twee knippen geen enkel kader, omdat het gezicht daar even niet gevonden
was. De nieuwe tracks hebben de nummers 2736 tot en met 2896 gekregen (nummer
2886 is daardoor niet gebruikt). Omdat de nieuwe nummers achter de bestaande
nummers komen, houden alle andere tracks hun nummer. In de bestanden in
`data/tracks/` staat in de kolom `track_ongeknipt` het nummer van vóór het
knippen. Na het knippen zijn er 2.896 tracks. Daarvan zijn er 937 maar één
kader lang (vóór het knippen 908), omdat 29 losgeknipte stukken uit één kader
bestaan.


## Wat nog onzeker is

**De 26 tracks die niet te zeggen waren.** Die tracks zijn niet geknipt. Samen
hebben ze 579 kaders. Het beeld is daar te donker of te onduidelijk, dus de
labelaar kiest daar waarschijnlijk *Weet niet* (zie [Stap 2](stap2_labelen.md)).

**Fouten die geen enkele ronde gezien heeft.** Die kunnen er nog zijn. Bij de
tweede blik kwam in de 125 lange tracks één gemiste fout boven (die is nu
verbeterd), en in de 60 andere tracks geen. De meeste tracks van 2 tot 99
kaders zijn alleen in de eerste ronde bekeken. Dat er weinig fouten over zijn,
is daarom waarschijnlijk, maar hoeveel precies, weten we niet. Een
foutpercentage noemen we bewust niet, omdat dat nauwkeuriger zou lijken dan
het is.

**Wat deze controle niet meet.** Deze controle gaat alleen over het volgen.
Vergissingen van de labelaar komen er nog bij; die meten we met een tweede
labelaar (zie [Stap 2](stap2_labelen.md#wat-er-na-het-labelen-gebeurt)). En een
gezicht dat de detector helemaal niet gevonden heeft, zit in geen enkele track
(zie [Stap 1](stap1_gezichten_vinden_en_volgen.md) en
[Stap 2](stap2_labelen.md)).


## Korte tracks

Tracks van één kader zijn niet bekeken, omdat het kader daarin niet kan
overspringen. Tracks van 2 tot 4 kaders zijn wel bekeken: van de 637 waren er 7
fout (zie de tabel hierboven).

Een andere vraag is of korte tracks wel echte gezichten zijn. Dat hebben we
alleen bij de eerdere versie van het volgen gemeten (zie
[De eerdere steekproef](#de-eerdere-steekproef)). Van 150 willekeurige tracks
van 1 tot 4 beelden was toen ongeveer 4 op de 10 een gezicht (ook half, wazig,
donker of van opzij), ongeveer 3 op de 10 geen gezicht, en bij de rest was het
niet te zeggen. Bij versie 5 hebben we dat niet opnieuw geteld. Weglaten zou
echte gezichten uit het antwoordenblad halen, en een korte track labelen kost
weinig werk. **Daarom worden alle tracks gelabeld, ook die van één kader.**


## Zelf nakijken

Daarvoor moet het project eerst geïnstalleerd zijn (zie
[Zelf draaien](zelf_draaien.md#installeren)). Alle opdrachten hieronder geef je
vanuit de map `KTAI`.

Deze opdracht maakt alle 352 vellen opnieuw, in `data/audit/alle_tracks/`:

```bash
.venv/bin/python code/check_all_tracks.py
```

De vellen staan niet op GitHub; deze opdracht maakt ze. Welke track op welk vel
staat, en welke beelden van die track getoond zijn, staat in
`data/audit/alle_tracks_index.csv`. Op de vellen is een gewoon kader groen. Een
verlenging is oranje en heeft een `v` achter het beeldnummer.

Om één vondst precies na te kijken, maakt deze opdracht een strook met alle
kaders van één track tussen twee beelden (hier track 1583, van beeld 1450 tot
en met 1510):

```bash
.venv/bin/python code/check_all_tracks.py --track 1583 --van 1450 --tot 1510
```

En zo maak je een strook zoals bij de tweede blik, met 36 kaders gelijk
verdeeld over de hele track:

```bash
.venv/bin/python code/check_all_tracks.py --track 1583 --stappen 36 --out data/audit/alle_tracks/track_1583_tweede_blik.jpg
```

Gebruik altijd het tracknummer uit `controle_alle_tracks.csv`, dus het nummer
van vóór het knippen (kolom `track_ongeknipt` in `data/tracks/`).


## De eerdere steekproef

Vóór versie 5 volgde de computer de gezichten op een iets andere manier
(versie 4, met 3.191 tracks). Die tracks hebben we niet allemaal bekeken, maar
een steekproef: 215 tracks, plus 150 heel korte tracks. Daaruit leerden we twee
dingen. Een track springt vooral over naar een ander gezicht in drukke scènes,
waar veel gezichten dicht bij elkaar staan. En een kader kan aan het begin of
het eind van een track op iets anders staan, zoals een lamp of een
achterhoofd. De gevonden fouten zijn toen geknipt (14 knippen in 12 tracks).
Voor de tracks die niet of maar kort bekeken waren, schatten we dat ongeveer
220 van de toen 43.414 kaders (0,5%) nog een verkeerde naam zouden krijgen.

Bij die versie hebben we ook zes andere manieren van volgen geprobeerd, zoals
een strengere eis voor overlap en het voorspellen van de beweging. Geen
daarvan gaf minder fouten zonder veel goede tracks onnodig in stukken te
knippen. En bij die controle bleek dat een programma dat direct naar een
beeldnummer springt, soms het verkeerde beeld krijgt. Sindsdien lezen alle
programma's de fragmenten van het begin af, op volgorde (zie
[Stap 1](stap1_gezichten_vinden_en_volgen.md#elk-beeld-op-volgorde)).

Bij versie 5 horen andere tracks met andere nummers. Daarom paste de
steekproef niet meer, en zijn daarna alle tracks opnieuw gecontroleerd. De
plaatjes, de oordelen en het oude programma van de steekproef staan in
`data/audit/eerdere_steekproef/` (met een korte uitleg in `README.md`). De
tracknummers daar horen bij versie 4.
