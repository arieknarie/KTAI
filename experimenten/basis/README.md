# Basis: FaceNet zoals het standaard is ingesteld

In dit experiment staat FaceNet zo standaard mogelijk ingesteld. FaceNet is het herkenningsprogramma dat we testen: het maakt van een
gezicht een rij getallen (een *vector*), en twee foto's van dezelfde persoon geven vectoren die dicht bij elkaar liggen. Met de standaardinstellingen
zien we hoe goed FaceNet is zonder dat we iets afstellen. Daar vergelijken we de andere experimenten mee.

Het experiment is gedaan met twee sets voorbeeldfoto's: alleen de gewone foto's van de acteurs, en de foto's samen met de stills in kostuum (beelden uit de
film). De uitkomsten staan in [`resultaten/`](resultaten/), per set in een eigen map, met een eigen uitleg en een filmpje:

- [Alleen foto's](resultaten/fotos/README.md)
- [Foto's + stills in kostuum](resultaten/fotos_en_kostuum/README.md)


## Wat we doen, in het kort

| Stap | Wat er gebeurt | Code |
|---|---|---|
| 1 | Van elke voorbeeldfoto maakt FaceNet een vector. | [`stap_1_voorbeelden.py`](stap_1_voorbeelden.py) |
| 2 | Van elk gezicht in de filmpjes maakt FaceNet een vector, en die wordt vergeleken met de voorbeelden. | [`stap_2_herkennen.py`](stap_2_herkennen.py) |
| 3 | Meten met methode 1: per beeld, wie is er te zien? | [`stap_3_methode_1_per_beeld.py`](stap_3_methode_1_per_beeld.py) |
| 4 | Meten met methode 2: per gezicht, op de plek waar het gezicht staat. | [`stap_4_methode_2_per_gezicht.py`](stap_4_methode_2_per_gezicht.py) |
| 5 | Een filmpje van alle fragmenten achter elkaar, met de namen die FaceNet geeft. | [`stap_5_filmpje.py`](stap_5_filmpje.py) |
| 6 | De uitleg bij de uitkomsten, met de echte getallen. | [`stap_6_uitleg.py`](stap_6_uitleg.py) |

De gezichten (de kaders) en de juiste antwoorden (de ground truth) komen uit het labelen, zie [`labelen/README.md`](../../labelen/README.md).

![De voorbeeldfoto's van de vier personen, in de set met foto's en stills](resultaten/fotos_en_kostuum/voorbeelden.jpg)

*De voorbeelden in de set met foto's en stills. Elk klein plaatje is precies wat FaceNet van een voorbeeld te zien krijgt.*


## De standaardinstellingen

De instellingen staan op één plek, in [`instellingen.py`](instellingen.py).

| Instelling | Waarde | Waarom |
|---|---|---|
| Model | Facenet | De standaardversie in deepface, de programmacode waarmee we FaceNet draaien: 128 getallen per gezicht. |
| Afstand | genormaliseerde Euclidische afstand | Deze afstand schrijft de opdracht voor. Beide vectoren krijgen eerst lengte 1, daarna meten we hoe ver ze uit elkaar liggen. |
| Drempel | 0,80 | De grens die deepface voor FaceNet met deze afstand gebruikt. Is de afstand tot het dichtstbijzijnde voorbeeld kleiner, dan krijgt het kader die naam. Anders is het *iemand anders*. |
| Kader | precies het kader van de detector | Geen extra ruimte om het gezicht. |
| Per persoon | de meest gelijkende voorbeeldfoto | Elke voorbeeldfoto is een los vergelijkingspunt. |
| Gezicht rechtzetten | nee | Het kader komt uit het labelen; deepface zoekt zelf geen gezicht meer. |


## De twee meetmethodes

We kijken op twee manieren hoe goed FaceNet is. De code van beide methodes staat in [`../gedeeld/meten.py`](../gedeeld/meten.py), en elk experiment gebruikt precies die code.

**Methode 1: per beeld.** We weten wie er in elk beeld te zien is, en we tellen. Per beeld en per persoon is de vraag: ziet FaceNet deze persoon in dit beeld, en klopt dat? Waar in
het beeld FaceNet de persoon ziet, maakt niet uit. Dit is de maat van de opdracht: de tabel met de foutmarge en de tijdlijn.

**Methode 2: per gezicht.** We weten ook waar elk gezicht staat, en we matchen daarop. Een naam van FaceNet is alleen goed als het kader met die naam ook echt op het gezicht van die persoon
ligt.

![Hetzelfde beeld: wat FaceNet zegt en wat de ground truth zegt](fotos/twee_methodes.jpg)

*In dit beeld staat Der Alte, en FaceNet noemt ook Der Alte. Methode 1 rekent dat goed, ook al zet FaceNet die naam daarnaast op iemand anders. Methode 2 ziet dat dat tweede kader fout is, en dat de
andere persoon niet herkend is.*

**Onze keuze: methode 2.** We beoordelen het model met methode 2, omdat methode 1 een belangrijke fout niet ziet: staat de persoon ergens in beeld, dan telt elke naam als goed, ook als die op een figurant
of op iets dat geen gezicht is staat. Methode 1 blijft nodig voor de tabel en de tijdlijn van de opdracht, en we rapporteren dus altijd beide.

**Zo werkt methode 2 precies.** Per beeld vergelijken we de kaders die van FaceNet een naam kregen met de gezichten in de ground truth:

- Twee kaders liggen *op elkaar* als ze minstens 30% overlappen. Overlap (*IoU*) is de oppervlakte die twee kaders gemeen hebben, gedeeld door de oppervlakte die ze samen bedekken.
- **Goed**: een gezicht uit de ground truth waarop een kader met de juiste naam ligt.
- **Fout benoemd**: een kader met een naam dat niet op het gezicht van die persoon ligt.
- **Gemist**: een gezicht uit de ground truth zonder de juiste naam. We splitsen dat op in: geen kader van de detector op die plek, wel een kader maar geen naam, of wel een kader maar een andere naam.
- Twee kaders op hetzelfde hoofd met de juiste naam tellen samen één keer goed, en niet als fout.

Uit die tellingen volgen *precisie* (hoe vaak klopt een naam die FaceNet geeft), *recall* (hoeveel van de echte gezichten vindt FaceNet) en *F1* (die twee samen, van 0 tot 1).

**Waarom 30% overlap.** De grens van 30% is dezelfde als bij het volgen van de gezichten in het labelen. Het kader van een verbeterd beeld staat soms iets naast het gezicht, dus een strengere grens zou goede namen ten onrechte
afkeuren. In de tabel hieronder is te zien dat de keuze weinig uitmaakt: de uitkomst van de set met foto's en stills verandert nauwelijks tussen 10% en 50% (`methode_2_overlap.csv`).

| Overlap minstens | 10% | 20% | **30%** | 40% | 50% | 70% |
|---|---|---|---|---|---|---|
| F1 (foto's + stills) | 0,318 | 0,311 | **0,308** | 0,304 | 0,300 | 0,286 |


## De uitkomsten

| Voorbeelden | Methode 1: precisie | recall | **F1** | Methode 2: precisie | recall | **F1** |
|---|---|---|---|---|---|---|
| Alleen foto's | 0,986 | 0,041 | **0,078** | 0,929 | 0,038 | **0,074** |
| Foto's + stills in kostuum | 0,645 | 0,626 | **0,636** | 0,251 | 0,398 | **0,308** |

![De tijdlijn met foto's en stills: de ground truth en FaceNet](resultaten/fotos_en_kostuum/methode_1_tijdlijn.png)

**Wat dit betekent.**

- **Met alleen foto's herkent FaceNet bijna niemand.** Met de drempel van 0,80 is FaceNet heel voorzichtig: als FaceNet een naam geeft, klopt die bijna altijd, maar van de 20.990 gezichten vindt FaceNet er maar 804. De gewone foto's
  lijken te weinig op de donkere gezichten met baarden in de film.
- **Met de stills erbij geeft FaceNet veel vaker een naam.** Volgens methode 1 ziet dat er goed uit (F1 0,636), maar volgens methode 2 valt de score terug naar 0,308: veel namen staan op het verkeerde gezicht. Dat is de reden om methode 2 te gebruiken.
- **Johann wordt veel te vaak gezien.** Met de stills erbij zegt FaceNet in 4.302 beelden Johann, terwijl Johann maar in 849 beelden staat. Wie er dan echt staat, staat in [`../wie_wordt_johann/`](../wie_wordt_johann/README.md).
- **Eén slechte foto kan veel schade doen.** Het bestand `gebruik_per_foto.csv` zegt welke voorbeeldfoto bij elk kader de doorslag gaf. In de set met stills gaf het gezicht met het label Der Alte in `Fritz4.png` 10.016 keer de doorslag, en daarvan was 7.922 keer fout. Welke foto's het resultaat
  slechter maken, staat in [`../leave_one_out/`](../leave_one_out/README.md).

![Per kader: wie het echt is tegen de naam die FaceNet geeft, met foto's en stills](resultaten/fotos_en_kostuum/methode_2_verwarring.png)


## De filmpjes

- [Alleen foto's](resultaten/fotos/filmpje.mp4)
- [Foto's + stills in kostuum](resultaten/fotos_en_kostuum/filmpje.mp4)

In een filmpje staat een vierkantje om elk gezicht dat FaceNet als een van de vier personen herkent, met de naam erbij.


## Zo draai je het op een Mac en op Windows

Doe dit vanuit de map `experimenten`. Installeren hoeft één keer, zie [de uitleg over alle experimenten](../README.md#installeren-op-mac-en-windows). Voor de filmpjes is ook het programma ffmpeg nodig (Mac: `brew install ffmpeg`, Windows: `winget install Gyan.FFmpeg`).

Op een Mac:

```bash
.venv/bin/python basis/draai_alles.py
```

Op Windows:

```bat
.venv\Scripts\python basis\draai_alles.py
```

Dit draait alle stappen voor beide sets. Eén set kan ook, door er `--voorbeelden fotos` of `--voorbeelden fotos_en_kostuum` achter te zetten. Een losse stap draait zo (op Windows met `.venv\Scripts\python` en `\`):

```bash
.venv/bin/python basis/stap_2_herkennen.py --voorbeelden fotos
```

Stap 2 duurt de eerste keer ongeveer een kwartier, omdat FaceNet dan alle 37.003 gezichten bekijkt. De vectoren worden bewaard in `tussenbestanden/` (gaat niet mee naar GitHub), en daarna duurt het nog een minuut.
