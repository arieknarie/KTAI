# De uitkomsten van het getunde model: foto's + stills

Dit zijn de uitkomsten van FaceNet met de best gevonden instellingen voor deze voorbeelden. FaceNet krijgt hier als voorbeelden de gewone foto's en de stills uit de film. Waarom we dit doen en hoe we de instellingen gezocht hebben, staat in [de uitleg van tuned](../../README.md).

> **In het kort.** De score per gezicht is **0,874**. De score is een cijfer van 0 tot 1: bij 1 krijgt elk gezicht van de vier personen de juiste naam, en klopt elke naam die FaceNet geeft.
>
> - Van de 20.990 gezichten krijgen er 16.949 de juiste naam (81%).
> - FaceNet zette 17.807 namen in de filmpjes, en daarvan klopten er 16.949 (95%).
> - Het best herkend: Werner (score 0,919). Het slechtst herkend: Johann (score 0,374).

**Het filmpje:** [`filmpje.mp4`](filmpje.mp4) laat alle fragmenten achter elkaar zien, met een vierkantje om elk gezicht dat FaceNet als een van de vier personen herkent. Klik op GitHub op de link en daarna op *View raw* om het filmpje te downloaden.

Wat de woorden betekenen, staat in [de woordenlijst](../../../README.md#woordenlijst). Hoe we meten, staat bij [Zo meten we hoe goed FaceNet is](../../../README.md#zo-meten-we-hoe-goed-facenet-is).


## De instellingen

Dit zijn de instellingen waarmee deze uitkomsten gemaakt zijn.

| Instelling | Waarde |
|---|---|
| Model | Facenet512 |
| Extra ruimte om het kader | 20% |
| Lichter maken | ja |
| Afstand | genormaliseerde Euclidische afstand |
| Vergelijken met | het gemiddelde van de foto's van elke persoon |
| Naam in een beeld | elk één keer |
| Beslissen | per track |
| Drempel | 1,1076 |

![Alle voorbeeldfoto's in deze set, per persoon](voorbeelden.jpg)

*De voorbeelden in deze set. Elk klein plaatje is precies wat FaceNet van een voorbeeld te zien krijgt.*


## De score per gezicht

Dit is de maat waarmee we FaceNet beoordelen. We weten waar elk gezicht staat. Een naam telt alleen als goed als het kader met die naam minstens 30% overlapt met het gezicht van die persoon.

**De score per persoon.** Precisie zegt hoe vaak een naam klopt. Recall zegt hoeveel van de echte gezichten de juiste naam krijgen. De score (F1) is die twee samen.

| Persoon | Score (F1) | Precisie | Recall |
|---|---|---|---|
| Der Alte | 0,898 | 0,967 | 0,839 |
| Fritz Grade | 0,839 | 0,922 | 0,769 |
| Johann | 0,374 | 0,650 | 0,263 |
| Werner | 0,919 | 0,974 | 0,870 |
| **alle vier samen** | **0,874** | **0,952** | **0,807** |

**De aantallen.** *Goed* is een gezicht met de juiste naam. *Naam op de verkeerde plek* is een kader met een naam dat niet op het gezicht van die persoon ligt. *Gemist* is een gezicht zonder de juiste naam.

| Persoon | Gezichten | Goed | Naam op de verkeerde plek | Gemist |
|---|---|---|---|---|
| Der Alte | 8.326 | 6.984 | 242 | 1.342 |
| Fritz Grade | 5.321 | 4.093 | 346 | 1.228 |
| Johann | 849 | 223 | 120 | 626 |
| Werner | 6.494 | 5.649 | 150 | 845 |
| **alle vier samen** | **20.990** | **16.949** | **858** | **4.041** |

**Waarom een gezicht gemist wordt.** Soms heeft de detector op die plek geen kader gevonden. Soms is er wel een kader, maar geeft FaceNet geen naam of een andere naam.

| Persoon | Geen kader | Wel kader, geen naam | Wel kader, andere naam |
|---|---|---|---|
| Der Alte | 707 | 599 | 36 |
| Fritz Grade | 515 | 694 | 19 |
| Johann | 61 | 483 | 82 |
| Werner | 328 | 473 | 44 |
| **alle vier samen** | **1.611** | **2.249** | **181** |

De score kan hier niet 1 worden. FaceNet bekijkt alleen kaders, dus de 1.611 gezichten zonder kader krijgen nooit een naam. Zelfs als elke naam klopt, blijft de score onder 0,96.

![Per kader: wie het echt is tegen de naam die FaceNet geeft](methode_2_verwarring.png)

*Zo lees je dit plaatje: elke rij is wie het echt is, elke kolom is de naam die FaceNet geeft. Bij een goed resultaat staan de hoge percentages op de schuine lijn van linksboven naar rechtsonder. De onderste rij zijn kaders die op geen van de vier personen liggen: figuranten en dingen die geen gezicht zijn. Daar hoort alles in de laatste kolom te staan. Dit plaatje telt kaders, de tabellen hierboven tellen gezichten. Daarom zijn de getallen niet precies gelijk.*

![Tijdlijn per gezicht: wanneer elke persoon echt in beeld is, en wanneer FaceNet de naam goed of op een verkeerde plek zet](methode_2_tijdlijn.png)

*Zo lees je dit plaatje: elke regel is een persoon, en van links naar rechts loopt de tijd in het filmpje. Zwart is wanneer de persoon echt in beeld is. Groen is wanneer FaceNet de juiste naam op het gezicht van die persoon zet. Rood is wanneer FaceNet die naam op een verkeerde plek zet. Hoe meer groen gelijk loopt met zwart en hoe minder rood er is, hoe beter.*

**Een eerlijke schatting.** De instellingen zijn gekozen op dezelfde beelden als waarop we meten. Daardoor is de score hierboven iets te gunstig. Bij de eerlijke schatting kiezen we de instellingen steeds op zeven filmpjes en meten we op het achtste. Dan is de score **0,834** (zie `eerlijke_schatting.csv`). Alle geprobeerde instellingen staan in `alle_instellingen.csv`, en per filmpje de beste instelling in `beste_per_filmpje.csv`.

![De hoogste score per keuze bij het afstellen](afstellen_per_instelling.png)

*Zo lees je dit plaatje: elk blok is één instelling. De balken laten zien hoe hoog de score kan worden met elke keuze. De oranje balk is de keuze van de winnaar.*


## De bestanden in deze map

| Bestand | Wat erin staat |
|---|---|
| `voorspellingen.csv` | Elk kader op een regel: wie FaceNet zegt dat het is (`facenet`), de persoon die het dichtstbij is (`dichtstbij`), de afstand (`afstand`) en de voorbeeldfoto die het meest op het kader lijkt (`foto`). |
| `gebruik_per_foto.csv` | Per voorbeeldfoto hoe vaak die foto het meest op een kader leek, en hoe vaak de naam dan goed of fout was. |
| `voorbeelden.jpg` | De voorbeelden in deze set. |
| `methode_2_tabel.csv`, `methode_2_tabel.png`, `methode_2_tijdlijn.png` | De uitkomst per gezicht. |
| `methode_2_verwarring.csv`, `methode_2_verwarring.png` | Per kader wie het echt is tegen de naam van FaceNet. |
| `methode_2_overlap.csv` | De uitkomst van methode 2 als de grens voor de overlap anders is. |
| `filmpje.mp4` | Het filmpje met de namen van FaceNet. |


## Zo maak je dit opnieuw

Doe dit vanuit de map `experimenten`. Installeren hoeft één keer, zie [Installeren op Mac en Windows](../../../README.md#installeren-op-mac-en-windows).

Op een Mac:

```bash
.venv/bin/python tuned/draai_alles.py --voorbeelden fotos_en_kostuum
```

Op Windows:

```bat
.venv\Scripts\python tuned\draai_alles.py --voorbeelden fotos_en_kostuum
```
