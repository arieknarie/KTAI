# De uitkomsten van tuned: foto's

Dit zijn de uitkomsten van FaceNet met de best gevonden instellingen. Als voorbeelden krijgt FaceNet hier: foto's. Waarom we dit doen en hoe we hebben afgesteld, staat in [de uitleg van tuned](../../README.md).

> **In het kort.** De score per gezicht is **0,808**. De score is een cijfer van 0 tot 1: bij 1 vindt FaceNet alle gezichten en klopt elke naam.
>
> - Van de 20.990 gezichten krijgen er 15.064 de juiste naam (72%).
> - FaceNet zette 16.296 namen in de filmpjes, en daarvan klopten er 15.064 (92%).
> - Het best herkend: Werner (score 0,868). Het slechtst herkend: Johann (score 0,535).

**Het filmpje:** [`filmpje.mp4`](filmpje.mp4) laat alle fragmenten achter elkaar zien, met een vierkantje om elk gezicht dat FaceNet als een van de vier personen herkent. Klik op GitHub op de link en daarna op *View raw* om het filmpje te downloaden.

Wat de woorden betekenen, staat in [de woordenlijst](../../../README.md#woordenlijst). Hoe we meten, staat bij [Zo meten we hoe goed FaceNet is](../../../README.md#zo-meten-we-hoe-goed-facenet-is).


## De instellingen

Dit zijn de instellingen waarmee deze uitkomsten gemaakt zijn.

| Instelling | Waarde |
|---|---|
| Model | Facenet |
| Extra ruimte om het kader | 20% |
| Donkere gezichten lichter maken | ja |
| Afstand | genormaliseerde Euclidische afstand |
| Per persoon | de afstand tot de meest gelijkende voorbeeldfoto |
| Toewijzen | per beeld elke persoon hoogstens één keer |
| Beslissen | per track |
| Drempel | 1,0684 |

![Alle voorbeeldfoto's in deze set, per persoon](voorbeelden.jpg)

*De voorbeelden in deze set. Elk klein plaatje is precies wat FaceNet van een voorbeeld te zien krijgt.*


## Methode 2: per gezicht

Dit is de maat waarmee we FaceNet beoordelen. We weten waar elk gezicht staat. Een naam telt alleen als goed als het kader met die naam minstens 30% overlapt met het gezicht van die persoon.

**De score per persoon.** Precisie zegt hoe vaak een naam klopt. Recall zegt hoeveel van de echte gezichten de juiste naam krijgen. De score (F1) is die twee samen.

| Persoon | Score (F1) | Precisie | Recall |
|---|---|---|---|
| Der Alte | 0,832 | 0,985 | 0,721 |
| Fritz Grade | 0,707 | 0,984 | 0,552 |
| Johann | 0,535 | 0,969 | 0,370 |
| Werner | 0,868 | 0,843 | 0,895 |
| **alle vier samen** | **0,808** | **0,924** | **0,718** |

**De aantallen.** *Goed* is een gezicht met de juiste naam. *Naam op de verkeerde plek* is een kader met een naam dat niet op het gezicht van die persoon ligt. *Gemist* is een gezicht zonder de juiste naam.

| Persoon | Gezichten | Goed | Naam op de verkeerde plek | Gemist |
|---|---|---|---|---|
| Der Alte | 8.326 | 6.003 | 93 | 2.323 |
| Fritz Grade | 5.321 | 2.936 | 48 | 2.385 |
| Johann | 849 | 314 | 10 | 535 |
| Werner | 6.494 | 5.811 | 1.081 | 683 |
| **alle vier samen** | **20.990** | **15.064** | **1.232** | **5.926** |

**Waarom een gezicht gemist wordt.** Soms heeft de detector op die plek geen kader gevonden. Soms is er wel een kader, maar geeft FaceNet geen naam of een andere naam.

| Persoon | Geen kader | Wel kader, geen naam | Wel kader, andere naam |
|---|---|---|---|
| Der Alte | 707 | 1.595 | 21 |
| Fritz Grade | 515 | 1.783 | 87 |
| Johann | 61 | 466 | 8 |
| Werner | 328 | 317 | 38 |
| **alle vier samen** | **1.611** | **4.161** | **154** |

![Per kader: wie het echt is tegen de naam die FaceNet geeft](methode_2_verwarring.png)

*Zo lees je dit plaatje: elke rij is wie het echt is, elke kolom is de naam die FaceNet geeft. Bij een goed resultaat staan de hoge percentages op de schuine lijn van linksboven naar rechtsonder. De onderste rij zijn kaders die op geen van de vier personen liggen: figuranten en dingen die geen gezicht zijn. Daar hoort alles in de laatste kolom te staan.*

**Een eerlijke schatting.** De instellingen zijn gekozen op dezelfde beelden als waarop we meten. Daardoor is de score hierboven wat te gunstig. Bij de eerlijke schatting kiezen we de instellingen steeds op zeven filmpjes en meten we op het achtste. Dan is de score **0,766** (zie `eerlijke_schatting.csv`). Alle geprobeerde instellingen staan in `alle_instellingen.csv`, en per filmpje de beste instelling in `beste_per_filmpje.csv`.

![De hoogste score per keuze bij het afstellen](afstellen_per_instelling.png)

*Zo lees je dit plaatje: elk blok is één instelling. De balken laten zien hoe hoog de score kan worden met elke keuze. De blauwe balk is de keuze van de winnaar.*


## Methode 1: per beeld

Deze maat staat in de opdracht. We weten wie er in elk beeld te zien is, en tellen per persoon in hoeveel beelden FaceNet die persoon ziet. Waar in het beeld FaceNet de persoon ziet, maakt niet uit.

| Persoon | Score (F1) | Precisie | Recall |
|---|---|---|---|
| Der Alte | 0,837 | 0,990 | 0,725 |
| Fritz Grade | 0,709 | 0,987 | 0,554 |
| Johann | 0,535 | 0,969 | 0,370 |
| Werner | 0,920 | 0,894 | 0,948 |
| **alle vier samen** | **0,829** | **0,948** | **0,736** |

**De aantallen.** De *foutmarge* zegt hoeveel procent het aantal beelden van FaceNet afwijkt van het echte aantal beelden. *Goed* is een beeld waarin FaceNet de persoon terecht ziet, *fout* een beeld waarin FaceNet de persoon ten onrechte ziet, en *gemist* een beeld waarin de persoon wel staat maar FaceNet de persoon niet ziet.

| Persoon | Echt in beeld | FaceNet ziet | Foutmarge | Goed | Fout | Gemist |
|---|---|---|---|---|---|---|
| Der Alte | 8.326 | 6.096 | 26,8% | 6.037 | 59 | 2.289 |
| Fritz Grade | 5.321 | 2.984 | 43,9% | 2.946 | 38 | 2.375 |
| Johann | 849 | 324 | 61,8% | 314 | 10 | 535 |
| Werner | 6.494 | 6.892 | 6,1% | 6.159 | 733 | 335 |
| **alle vier samen** | **20.990** | **16.296** | **22,4%** | **15.456** | **840** | **5.534** |

![Tijdlijn: wanneer elke persoon te zien is, volgens de ground truth en volgens FaceNet](methode_1_tijdlijn.png)

*Zo lees je dit plaatje: elke regel is een persoon, en van links naar rechts loopt de tijd in het filmpje. Zwart is wanneer de persoon echt in beeld is, rood is wanneer FaceNet de persoon ziet. Lopen zwart en rood gelijk, dan klopt het. Rood zonder zwart betekent dat FaceNet de persoon ten onrechte ziet, en zwart zonder rood dat FaceNet de persoon mist.*


## De bestanden in deze map

| Bestand | Wat erin staat |
|---|---|
| `voorspellingen.csv` | Elk kader op een regel: wie FaceNet zegt dat het is (`facenet`), de persoon die het dichtstbij is (`dichtstbij`), de afstand (`afstand`) en de voorbeeldfoto die het meest op het kader lijkt (`foto`). |
| `gebruik_per_foto.csv` | Per voorbeeldfoto hoe vaak die foto het meest op een kader leek, en hoe vaak de naam dan goed of fout was. |
| `voorbeelden.jpg` | De voorbeelden in deze set. |
| `methode_1_tabel.csv`, `methode_1_tabel.png`, `methode_1_tijdlijn.png` | De uitkomst van methode 1. |
| `methode_2_tabel.csv`, `methode_2_tabel.png` | De uitkomst van methode 2. |
| `methode_2_verwarring.csv`, `methode_2_verwarring.png` | Per kader wie het echt is tegen de naam van FaceNet. |
| `methode_2_overlap.csv` | De uitkomst van methode 2 als de grens voor de overlap anders is. |
| `filmpje.mp4` | Het filmpje met de namen van FaceNet. |


## Zo maak je dit opnieuw

Doe dit vanuit de map `experimenten`. Installeren hoeft één keer, zie [Installeren op Mac en Windows](../../../README.md#installeren-op-mac-en-windows).

Op een Mac:

```bash
.venv/bin/python tuned/draai_alles.py --voorbeelden fotos
```

Op Windows:

```bat
.venv\Scripts\python tuned\draai_alles.py --voorbeelden fotos
```
