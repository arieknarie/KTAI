# De uitkomsten van de basis: foto's + stills in kostuum

Dit zijn de uitkomsten van FaceNet met de standaardinstellingen. Als voorbeelden krijgt FaceNet hier: foto's + stills in kostuum. Waarom we dit doen en hoe het werkt, staat in [de uitleg van de basis](../../README.md).

> **In het kort.** De score per gezicht is **0,308**. De score is een cijfer van 0 tot 1: bij 1 vindt FaceNet alle gezichten en klopt elke naam.
>
> - Van de 20.990 gezichten krijgen er 8.355 de juiste naam (40%).
> - FaceNet zette 33.333 namen in de filmpjes, en daarvan klopten er 8.355 (25%).
> - Het best herkend: Fritz Grade (score 0,392). Het slechtst herkend: Johann (score 0,028).

**Het filmpje:** [`filmpje.mp4`](filmpje.mp4) laat alle fragmenten achter elkaar zien, met een vierkantje om elk gezicht dat FaceNet als een van de vier personen herkent. Klik op GitHub op de link en daarna op *View raw* om het filmpje te downloaden.

Wat de woorden betekenen, staat in [de woordenlijst](../../../README.md#woordenlijst). Hoe we meten, staat bij [Zo meten we hoe goed FaceNet is](../../../README.md#zo-meten-we-hoe-goed-facenet-is).


## De instellingen

Dit zijn de instellingen waarmee deze uitkomsten gemaakt zijn.

| Instelling | Waarde |
|---|---|
| Model | Facenet |
| Extra ruimte om het kader | 0% |
| Afstand | genormaliseerde Euclidische afstand |
| Drempel | 0,80 |
| Per persoon | de afstand tot de meest gelijkende voorbeeldfoto |
| Toewijzen | elk kader los |
| Voorbeelden | foto's + stills in kostuum |

![Alle voorbeeldfoto's in deze set, per persoon](voorbeelden.jpg)

*De voorbeelden in deze set. Elk klein plaatje is precies wat FaceNet van een voorbeeld te zien krijgt.*


## Methode 2: per gezicht

Dit is de maat waarmee we FaceNet beoordelen. We weten waar elk gezicht staat. Een naam telt alleen als goed als het kader met die naam minstens 30% overlapt met het gezicht van die persoon.

**De score per persoon.** Precisie zegt hoe vaak een naam klopt. Recall zegt hoeveel van de echte gezichten de juiste naam krijgen. De score (F1) is die twee samen.

| Persoon | Score (F1) | Precisie | Recall |
|---|---|---|---|
| Der Alte | 0,289 | 0,251 | 0,339 |
| Fritz Grade | 0,392 | 0,289 | 0,612 |
| Johann | 0,028 | 0,016 | 0,112 |
| Werner | 0,384 | 0,446 | 0,336 |
| **alle vier samen** | **0,308** | **0,251** | **0,398** |

**De aantallen.** *Goed* is een gezicht met de juiste naam. *Naam op de verkeerde plek* is een kader met een naam dat niet op het gezicht van die persoon ligt. *Gemist* is een gezicht zonder de juiste naam.

| Persoon | Gezichten | Goed | Naam op de verkeerde plek | Gemist |
|---|---|---|---|---|
| Der Alte | 8.326 | 2.820 | 8.396 | 5.506 |
| Fritz Grade | 5.321 | 3.255 | 8.013 | 2.066 |
| Johann | 849 | 95 | 5.858 | 754 |
| Werner | 6.494 | 2.185 | 2.711 | 4.309 |
| **alle vier samen** | **20.990** | **8.355** | **24.978** | **12.635** |

**Waarom een gezicht gemist wordt.** Soms heeft de detector op die plek geen kader gevonden. Soms is er wel een kader, maar geeft FaceNet geen naam of een andere naam.

| Persoon | Geen kader | Wel kader, geen naam | Wel kader, andere naam |
|---|---|---|---|
| Der Alte | 707 | 110 | 4.689 |
| Fritz Grade | 515 | 226 | 1.325 |
| Johann | 61 | 322 | 371 |
| Werner | 328 | 457 | 3.524 |
| **alle vier samen** | **1.611** | **1.115** | **9.909** |

![Per kader: wie het echt is tegen de naam die FaceNet geeft](methode_2_verwarring.png)

*Zo lees je dit plaatje: elke rij is wie het echt is, elke kolom is de naam die FaceNet geeft. Bij een goed resultaat staan de hoge percentages op de schuine lijn van linksboven naar rechtsonder. De onderste rij zijn kaders die op geen van de vier personen liggen: figuranten en dingen die geen gezicht zijn. Daar hoort alles in de laatste kolom te staan.*


## Methode 1: per beeld

Deze maat staat in de opdracht. We weten wie er in elk beeld te zien is, en tellen per persoon in hoeveel beelden FaceNet die persoon ziet. Waar in het beeld FaceNet de persoon ziet, maakt niet uit.

| Persoon | Score (F1) | Precisie | Recall |
|---|---|---|---|
| Der Alte | 0,707 | 0,832 | 0,615 |
| Fritz Grade | 0,802 | 0,761 | 0,848 |
| Johann | 0,080 | 0,048 | 0,243 |
| Werner | 0,631 | 0,831 | 0,509 |
| **alle vier samen** | **0,636** | **0,645** | **0,626** |

**De aantallen.** De *foutmarge* zegt hoeveel procent het aantal beelden van FaceNet afwijkt van het echte aantal beelden. *Goed* is een beeld waarin FaceNet de persoon terecht ziet, *fout* een beeld waarin FaceNet de persoon ten onrechte ziet, en *gemist* een beeld waarin de persoon wel staat maar FaceNet de persoon niet ziet.

| Persoon | Echt in beeld | FaceNet ziet | Foutmarge | Goed | Fout | Gemist |
|---|---|---|---|---|---|---|
| Der Alte | 8.326 | 6.158 | 26,0% | 5.121 | 1.037 | 3.205 |
| Fritz Grade | 5.321 | 5.933 | 11,5% | 4.514 | 1.419 | 807 |
| Johann | 849 | 4.302 | 406,7% | 206 | 4.096 | 643 |
| Werner | 6.494 | 3.976 | 38,8% | 3.304 | 672 | 3.190 |
| **alle vier samen** | **20.990** | **20.369** | **3,0%** | **13.145** | **7.224** | **7.845** |

![Tijdlijn: wanneer elke persoon te zien is, volgens de ground truth en volgens FaceNet](methode_1_tijdlijn.png)

*Zo lees je dit plaatje: elke regel is een persoon, en van links naar rechts loopt de tijd in het filmpje. Zwart is wanneer de persoon echt in beeld is, rood is wanneer FaceNet de persoon ziet. Lopen zwart en rood gelijk, dan klopt het. Rood zonder zwart betekent dat FaceNet de persoon ten onrechte ziet, en zwart zonder rood dat FaceNet de persoon mist.*


## De bestanden in deze map

| Bestand | Wat erin staat |
|---|---|
| `voorspellingen.csv` | Elk kader op een regel: wie FaceNet zegt dat het is (`facenet`), de persoon die het dichtstbij is (`dichtstbij`), de afstand (`afstand`) en de voorbeeldfoto die het meest op het kader lijkt (`foto`). |
| `gebruik_per_foto.csv` | Per voorbeeldfoto hoe vaak die foto het meest op een kader leek, en hoe vaak de naam dan goed of fout was. |
| `voorbeelden.csv`, `voorbeelden.jpg` | De voorbeelden in deze set. |
| `methode_1_tabel.csv`, `methode_1_tabel.png`, `methode_1_tijdlijn.png` | De uitkomst van methode 1. |
| `methode_2_tabel.csv`, `methode_2_tabel.png` | De uitkomst van methode 2. |
| `methode_2_verwarring.csv`, `methode_2_verwarring.png` | Per kader wie het echt is tegen de naam van FaceNet. |
| `methode_2_overlap.csv` | De uitkomst van methode 2 als de grens voor de overlap anders is. |
| `filmpje.mp4` | Het filmpje met de namen van FaceNet. |


## Zo maak je dit opnieuw

Doe dit vanuit de map `experimenten`. Installeren hoeft één keer, zie [Installeren op Mac en Windows](../../../README.md#installeren-op-mac-en-windows).

Op een Mac:

```bash
.venv/bin/python basis/draai_alles.py --voorbeelden fotos_en_kostuum
```

Op Windows:

```bat
.venv\Scripts\python basis\draai_alles.py --voorbeelden fotos_en_kostuum
```
