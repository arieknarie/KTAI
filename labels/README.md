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
