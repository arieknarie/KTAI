# Labels

In deze map komt het bestand `labels.csv` met de keuzes van de labelaar. De
labelaar is de persoon die in de labelapp bij elk gevonden gezicht aangeeft
wie het is (zie [Stap 2: labelen](../docs/stap2_labelen.md)). Uit dit bestand
maken we na het labelen het antwoordenblad: de tabel waarmee we straks
nakijken of het herkenningsprogramma de juiste naam geeft.


## Hoe het bestand in deze map komt

De labelapp bewaart elke keuze meteen in `labeling/labels.csv`, op de computer
waarop de app draait. Dat bestand gaat niet mee naar GitHub (het staat in
`labeling/.gitignore`). Zo kan iedereen in het team de app uitproberen zonder
dat die proefkeuzes in het project terechtkomen.

De labelaar stuurt `labels.csv` per mail naar Marc, aan het eind van het
labelen en ook tussendoor (zie stap 6 van de
[handleiding voor de labelaar](../labeling/README.md#stap-6-je-keuzes-naar-marc-sturen)).
Marc zet het bestand in deze map en zet het met `git add labels/labels.csv`,
`git commit` en `git push` op GitHub. Een nieuwere versie vervangt de oudere;
git bewaart elke versie.


## Wat er in het bestand staat

Elke rij hoort bij één gezicht en zegt wie dat gezicht is volgens de
labelaar. Bij een track (een stukje film waarin de computer hetzelfde gezicht
van beeld tot beeld volgt) is dat één rij voor de hele track. Bij een foto of
een still (een los beeld uit de film) met meer gezichten is het één rij per
gezicht. De keuzes bij de foto's en stills komen niet op het antwoordenblad;
die gebruiken we om zeker te weten wie er op die foto's en stills staat.

Soms heeft de computer een gezicht van een van de vier personen helemaal
gemist. Dan tekent de labelaar zelf een rechthoek om dat gezicht. Zo'n
getekend gezicht krijgt ook een rij, met in de kolom `how` het woord
`getekend`. Wat er in elke kolom staat, staat bovenaan in
[`labeling/app.py`](../labeling/app.py).


## Van de keuzes naar het antwoordenblad

Het antwoordenblad maken we uit twee bestanden. In
`data/tracks/detections_0.3.csv` staat elk gezicht dat de computer in de
fragmenten vond, met de track waar dat gezicht bij hoort. Daar horen ook de
gezichten bij waarvan de computer minder zeker was, maar waarmee een track
langer doorloopt (zie [Stap 1](../docs/stap1_gezichten_vinden_en_volgen.md)).
In `labels.csv` staat per track de keuze van de labelaar. Elk gevonden gezicht
krijgt de keuze van zijn track. Elk getekend gezicht wordt één extra rij op het
antwoordenblad, voor dat ene beeld. Een voorbeeld van het antwoordenblad staat
in [het overzicht](../README.md#hoe-het-antwoordenblad-eruitziet).


## De labels nakijken

Met `code/check_labels.py` kijken we na of de labels kloppen. Het programma
laat elk beeld van elk fragment zien (alle 11.182, ook de beelden zonder
kader), en daarna elke gelabelde foto en still. Alleen de vier personen
krijgen een kader: om elk gezicht dat de labelaar als een van de vier
aanwees, met de naam erbij. Staat een persoon meer dan één keer in hetzelfde
beeld, dan worden die kaders samen één groot kader. Was een persoon in het
vorige beeld wel te zien en in dit beeld niet, dan staat er bovenin een rode
waarschuwing.

Per beeld druk je op pijltje links als de labels goed zijn en op pijltje
rechts als er iets fout is. Met Backspace ga je een beeld terug. Elk oordeel
komt meteen in `labels/controle_labels.csv`. Wie stopt en later weer start,
gaat verder bij het eerste beeld zonder oordeel. Starten (vanuit de map KTAI):
`.venv/bin/python code/check_labels.py`. De controle opent dan in de browser.


## De foute beelden verbeteren

Met `code/fix_labels.py` verbeteren we elk beeld dat bij het nakijken fout
kreeg. Rechts staat groot het foute beeld, linksboven het laatste goede beeld
ervoor (of het laatste beeld dat al verbeterd is), en daaronder een knop per
persoon. Een knop staat aan als die persoon al in het beeld staat. Zet je een
knop aan en klik je op een gezicht, dan komt om dat gezicht een kader met die
naam. Zet je een knop uit, dan gaat het kader weg. Enter slaat op en gaat naar
het volgende foute beeld. Alles komt in `labels/correcties.csv`. Starten
(vanuit de map KTAI): `.venv/bin/python code/fix_labels.py`.
