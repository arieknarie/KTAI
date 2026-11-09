# Basis: FaceNet zoals het standaard is ingesteld

> **De vraag.** Hoe goed herkent FaceNet de vier personen als we niets afstellen?
>
> **Het antwoord.** Slecht. Met alleen gewone foto's als voorbeeld krijgt bijna niemand een naam (score 0,074). Met de stills uit de film erbij krijgt bijna iedereen een naam, maar vaak de verkeerde (score 0,308).

![Hetzelfde gezicht twee keer: met alleen foto's krijgt het gezicht geen naam, met stills erbij wel](../fotos/zo_werkt_facenet.jpg)

*Zo werkt FaceNet. Dit is twee keer hetzelfde gezicht uit de film, en je leest elke rij van links naar rechts. Bovenaan krijgt FaceNet alleen gewone foto's als voorbeeld. Die lijken te weinig op dit gezicht, dus het gezicht krijgt geen naam. Onderaan zijn er ook stills uit de film, en krijgt het gezicht de juiste naam.*

Wat de woorden betekenen, staat in [de woordenlijst](../README.md#woordenlijst).

**In deze uitleg:**
[Waarom](#waarom-dit-experiment) ·
[Wat we gedaan hebben](#wat-we-gedaan-hebben) ·
[De instellingen](#de-instellingen) ·
[De twee meetmethodes](#de-twee-meetmethodes) ·
[Wat eruit kwam](#wat-eruit-kwam) ·
[Wat dit betekent](#wat-dit-betekent) ·
[De filmpjes](#de-filmpjes) ·
[Zelf draaien](#zo-draai-je-het-op-een-mac-en-op-windows)


## Waarom dit experiment

Met de standaardinstellingen zien we hoe goed FaceNet is zonder dat wij iets afstellen. Dat is ons vertrekpunt: alle andere experimenten vergelijken we hiermee.

We doen het met twee sets voorbeeldfoto's:

| Set voorbeelden | Wat erin zit | Aantal | De uitkomsten |
|---|---|---|---|
| **Foto's** | Gewone foto's van de acteurs, buiten de film | 23 gezichten | [`resultaten/fotos/`](resultaten/fotos/README.md) |
| **Foto's + stills** | Dezelfde foto's, en stills uit de film in kostuum | 73 gezichten | [`resultaten/fotos_en_kostuum/`](resultaten/fotos_en_kostuum/README.md) |

![De voorbeeldfoto's van de vier personen, in de set met foto's en stills](resultaten/fotos_en_kostuum/voorbeelden.jpg)

*Dit zijn alle voorbeelden in de set met foto's en stills, per persoon. Elk klein plaatje is precies wat FaceNet te zien krijgt. Let op hoe verschillend ze zijn: naast scherpe foto's staan er donkere en wazige stills. Beelden uit de filmpjes die we testen, gebruiken we nooit als voorbeeld.*


## Wat we gedaan hebben

Elke stap is een eigen script.

| Stap | Wat er gebeurt | Script |
|---|---|---|
| 1 | Van elke voorbeeldfoto maakt FaceNet een vector. | [`stap_1_voorbeelden.py`](stap_1_voorbeelden.py) |
| 2 | Van elk gezicht in de filmpjes maakt FaceNet een vector, en die wordt vergeleken met de voorbeelden. | [`stap_2_herkennen.py`](stap_2_herkennen.py) |
| 3 | Meten met methode 1: wie is er per beeld te zien? | [`stap_3_methode_1_per_beeld.py`](stap_3_methode_1_per_beeld.py) |
| 4 | Meten met methode 2: staat de naam op het juiste gezicht? | [`stap_4_methode_2_per_gezicht.py`](stap_4_methode_2_per_gezicht.py) |
| 5 | Een filmpje maken van alle fragmenten, met de namen van FaceNet. | [`stap_5_filmpje.py`](stap_5_filmpje.py) |
| 6 | De uitleg bij de uitkomsten schrijven, met de echte getallen. | [`stap_6_uitleg.py`](stap_6_uitleg.py) |

De gezichten in de filmpjes (de kaders) en de juiste antwoorden (de ground truth) komen uit [het labelen](../../labelen/README.md).


## De instellingen

Alle instellingen staan op één plek, in [`instellingen.py`](instellingen.py).

| Instelling | Waarde | Wat dat betekent |
|---|---|---|
| Model | Facenet | De standaardversie in deepface, de programmacode waarmee we FaceNet draaien. FaceNet maakt hiermee 128 getallen per gezicht. |
| Afstand | genormaliseerde Euclidische afstand | De maat voor hoe ver twee vectoren uit elkaar liggen. Deze afstand schrijft de opdracht voor. |
| Drempel | 0,80 | De grens die deepface voor deze afstand gebruikt. Is de afstand kleiner, dan krijgt het kader een naam. Anders is het *iemand anders*. |
| Extra ruimte om het kader | geen | FaceNet krijgt precies het kader van de detector te zien. |
| Vergelijken met | de meest gelijkende foto | Elke voorbeeldfoto is een los vergelijkingspunt. |
| Gezicht rechtzetten | nee | Het kader komt uit het labelen, dus deepface zoekt zelf geen gezicht meer. |


## De twee meetmethodes

We kijken op twee manieren hoe goed FaceNet is. De code staat in [`../gedeeld/meten.py`](../gedeeld/meten.py), en elk experiment gebruikt precies die code.

- **Methode 1: per beeld.** We weten wie er in elk beeld te zien is en we tellen. Ziet FaceNet deze persoon in dit beeld, en klopt dat? Waar in het beeld FaceNet de persoon ziet, maakt niet uit. Dit is de maat uit de opdracht.
- **Methode 2: per gezicht.** We weten ook waar elk gezicht staat. Een naam is alleen goed als het kader met die naam ook echt op het gezicht van die persoon ligt.

![Hetzelfde beeld met wat FaceNet zegt en wie er echt staat, en wat de twee methodes daarvan vinden](../fotos/twee_methodes.jpg)

*Zo verschillen de twee methodes op een echt beeld. FaceNet zet twee keer de naam Der Alte. Methode 1 rekent dat goed, want Der Alte staat in het beeld. Methode 2 ziet dat één van die namen op het gezicht van Werner staat.*

**Onze keuze: methode 2.** Methode 1 ziet een belangrijke fout niet: staat een persoon ergens in beeld, dan telt elke naam van die persoon als goed, ook op een figurant of op iets dat geen gezicht is. Methode 1 blijft nodig voor de tabel en de tijdlijn uit de opdracht, en daarom rapporteren we altijd beide.

**Zo werkt methode 2 precies.** Per beeld vergelijken we de kaders die van FaceNet een naam kregen met de gezichten in de ground truth.

| Uitkomst | Wanneer |
|---|---|
| **Goed** | Een gezicht uit de ground truth waarop een kader met de juiste naam ligt. Twee kaders op hetzelfde hoofd met de juiste naam tellen samen één keer. |
| **Naam op de verkeerde plek** | Een kader met een naam dat niet op het gezicht van die persoon ligt. |
| **Gemist** | Een gezicht uit de ground truth zonder de juiste naam: er is geen kader op die plek, of wel een kader maar geen naam of een andere naam. |

Twee kaders liggen op elkaar als ze minstens 30% overlappen. Overlap (*IoU*) is de oppervlakte die twee kaders gemeen hebben, gedeeld door de oppervlakte die ze samen bedekken.

**Waarom 30%.** Dat is dezelfde grens als bij het volgen van de gezichten in het labelen. Een kader in een verbeterd beeld staat soms iets naast het gezicht, dus een strengere grens zou goede namen afkeuren. De keuze maakt weinig uit, zoals de tabel laat zien (set met foto's + stills).

| Overlap minstens | 10% | 20% | **30%** | 40% | 50% | 70% |
|---|---|---|---|---|---|---|
| Score | 0,318 | 0,311 | **0,308** | 0,304 | 0,300 | 0,286 |

**De score.** Uit de tellingen volgen de *precisie* (als FaceNet een naam geeft, hoe vaak klopt die?), de *recall* (hoeveel van de echte gezichten krijgen de juiste naam?) en de *score* (F1, die twee samen, van 0 tot 1). In [dit plaatje](../README.md#zo-meten-we-hoe-goed-facenet-is) staat het uitgelegd met de echte aantallen.


## Wat eruit kwam

| Voorbeelden | Score per gezicht (methode 2) | Score per beeld (methode 1) | Gezichten met de juiste naam | Namen die kloppen |
|---|---|---|---|---|
| Foto's | **0,074** | 0,078 | 804 van de 20.990 (4%) | 93% |
| Foto's + stills | **0,308** | 0,636 | 8.355 van de 20.990 (40%) | 25% |

![Vier grafieken met de afstanden van goede en foute kaders, en de drempel](../fotos/drempel.png)

*Zo lees je dit plaatje: kijk naar de twee grafieken bovenaan, dat is de basis. Elke grafiek telt hoeveel kaders een bepaalde afstand hebben. Links van de stippellijn krijgt een kader een naam. Linksboven liggen bijna alle kaders rechts van de drempel: bijna niemand krijgt een naam. Rechtsboven liggen de meeste kaders links van de drempel, ook de oranje kaders waarbij de naam niet klopt.*

![De tijdlijn met foto's en stills: de ground truth en FaceNet](resultaten/fotos_en_kostuum/methode_1_tijdlijn.png)

*De tijdlijn met foto's + stills. Elke regel is een persoon, en de tijd loopt van links naar rechts. Zwart is wanneer de persoon echt in beeld is, rood wanneer FaceNet de persoon ziet. Kijk bijvoorbeeld naar Johann in Video 1 tot en met 7: daar is veel rood, terwijl Johann daar niet in beeld is.*

![Per kader: wie het echt is tegen de naam die FaceNet geeft, met foto's en stills](resultaten/fotos_en_kostuum/methode_2_verwarring.png)

*Zo lees je dit plaatje: elke rij is wie het echt is, elke kolom is de naam die FaceNet geeft. Bij een goed resultaat staan de hoge percentages op de schuine lijn. Hier zijn de getallen verdeeld over de hele tabel. In de onderste rij zie je dat figuranten en dingen die geen gezicht zijn, meestal toch een naam krijgen.*


## Wat dit betekent

- **Met alleen foto's herkent FaceNet bijna niemand.** Als FaceNet een naam geeft, klopt die bijna altijd (93%), maar van de 20.990 gezichten krijgen er maar 804 de juiste naam. De gewone foto's lijken te weinig op de donkere gezichten met baarden in de film.
- **Met de stills erbij geeft FaceNet veel vaker een naam.** Per beeld ziet dat er goed uit (score 0,636), maar per gezicht valt de score terug naar 0,308: drie van de vier namen staan op de verkeerde plek. Dat is precies waarom we methode 2 gebruiken.
- **Johann wordt veel te vaak gezien.** Met de stills erbij zegt FaceNet in 4.302 beelden Johann, terwijl Johann maar in 849 beelden staat. Wie er dan echt staat, staat bij [Wie wordt Johann](../wie_wordt_johann/README.md).
- **Eén foto kan heel veel invloed hebben.** Het bestand `gebruik_per_foto.csv` zegt welke voorbeeldfoto het meest op elk kader leek. In de set met stills was dat 10.016 keer het gezicht met het label Der Alte in `Fritz4.png`, en daarvan was 7.922 keer fout. Welke foto's het resultaat echt slechter maken, staat bij [Leave-one-out](../leave_one_out/README.md).


## De filmpjes

Een filmpje laat alle fragmenten achter elkaar zien, met een vierkantje om elk gezicht dat FaceNet als een van de vier personen herkent, en de naam erbij. Klik op GitHub op de link en daarna op *View raw* om een filmpje te downloaden.

- [Filmpje met alleen foto's](resultaten/fotos/filmpje.mp4)
- [Filmpje met foto's + stills](resultaten/fotos_en_kostuum/filmpje.mp4)


## Zo draai je het op een Mac en op Windows

Doe dit vanuit de map `experimenten`. Installeren hoeft één keer, zie [Installeren op Mac en Windows](../README.md#installeren-op-mac-en-windows).

Op een Mac:

```bash
.venv/bin/python basis/draai_alles.py
```

Op Windows:

```bat
.venv\Scripts\python basis\draai_alles.py
```

Dit draait alle stappen voor beide sets. Eén set kan ook, door er `--voorbeelden fotos` of `--voorbeelden fotos_en_kostuum` achter te zetten.

Een losse stap draai je zo:

```bash
.venv/bin/python basis/stap_2_herkennen.py --voorbeelden fotos
```

```bat
.venv\Scripts\python basis\stap_2_herkennen.py --voorbeelden fotos
```

Stap 2 duurt de eerste keer ongeveer een kwartier, omdat FaceNet dan alle 37.003 kaders bekijkt. De vectoren worden bewaard in `tussenbestanden/`, en daarna duurt stap 2 nog een minuut.
