# Basis (voorbeelden: foto's + stills in kostuum)

Dit is het basisexperiment: FaceNet staat zo standaard mogelijk ingesteld en vergelijkt elk gezicht in de filmpjes met de voorbeelden uit deze set. De uitleg van het experiment staat in [de README van de basis](../../README.md).

## De instellingen

| Instelling | Waarde |
|---|---|
| Model | Facenet |
| Extra ruimte om het kader | 0% |
| Afstand | genormaliseerde Euclidische afstand |
| Drempel | 0,80 |
| Per persoon | de afstand tot de meest gelijkende voorbeeldfoto |
| Toewijzen | elk kader los |
| Voorbeelden | foto's + stills in kostuum |

## Methode 1: per beeld

We weten wie er in elk beeld te zien is, en tellen per persoon in hoeveel beelden FaceNet die persoon ziet. *Goed* is een beeld waarin FaceNet de persoon terecht ziet, *fout* een beeld waarin FaceNet de persoon ten onrechte ziet, en *gemist* een beeld waarin de persoon wel staat maar FaceNet de persoon niet ziet. Waar in het beeld FaceNet de persoon ziet, maakt bij deze methode niet uit.

| Acteur | Ground truth (beelden) | FaceNet (beelden) | Foutmarge | Goed | Fout | Gemist | Precisie | Recall | F1 |
|---|---|---|---|---|---|---|---|---|---|
| Der Alte | 8.326 | 6.158 | 26,0% | 5.121 | 1.037 | 3.205 | 0,832 | 0,615 | 0,707 |
| Fritz Grade | 5.321 | 5.933 | 11,5% | 4.514 | 1.419 | 807 | 0,761 | 0,848 | 0,802 |
| Johann | 849 | 4.302 | 406,7% | 206 | 4.096 | 643 | 0,048 | 0,243 | 0,080 |
| Werner | 6.494 | 3.976 | 38,8% | 3.304 | 672 | 3.190 | 0,831 | 0,509 | 0,631 |
| **samen** | 20.990 | 20.369 | 3,0% | 13.145 | 7.224 | 7.845 | 0,645 | 0,626 | **0,636** |

![Tijdlijn: wanneer elke acteur te zien is, volgens de ground truth en volgens FaceNet](methode_1_tijdlijn.png)

## Methode 2: per gezicht

We weten ook waar elk gezicht staat. Een naam van FaceNet telt alleen als goed als het kader met die naam minstens 30% overlapt met het kader van die persoon in de ground truth. *Gemist* is verdeeld in: geen kader van de detector op die plek, wel een kader maar geen naam, of wel een kader maar een andere naam.

| Acteur | Gezichten | Goed | Fout benoemd | Gemist | waarvan geen kader | waarvan geen naam | waarvan andere naam | Precisie | Recall | F1 |
|---|---|---|---|---|---|---|---|---|---|---|
| Der Alte | 8.326 | 2.820 | 8.396 | 5.506 | 707 | 110 | 4.689 | 0,251 | 0,339 | 0,289 |
| Fritz Grade | 5.321 | 3.255 | 8.013 | 2.066 | 515 | 226 | 1.325 | 0,289 | 0,612 | 0,392 |
| Johann | 849 | 95 | 5.858 | 754 | 61 | 322 | 371 | 0,016 | 0,112 | 0,028 |
| Werner | 6.494 | 2.185 | 2.711 | 4.309 | 328 | 457 | 3.524 | 0,446 | 0,336 | 0,384 |
| **samen** | 20.990 | 8.355 | 24.978 | 12.635 | 1.611 | 1.115 | 9.909 | 0,251 | 0,398 | **0,308** |

![Per kader: wie het echt is tegen de naam die FaceNet geeft](methode_2_verwarring.png)

## Het filmpje

[`filmpje.mp4`](filmpje.mp4) is alle filmpjes achter elkaar, met een vierkantje om elk gezicht dat FaceNet als een van de vier personen herkent, en de naam erbij.

## De bestanden in deze map

| Bestand | Wat erin staat |
|---|---|
| `voorspellingen.csv` | Per kader wie FaceNet zegt dat het is (`facenet`), de dichtstbijzijnde persoon (`dichtstbij`), de afstand (`afstand`) en de voorbeeldfoto die de doorslag gaf (`foto`). |
| `gebruik_per_foto.csv` | Per voorbeeldfoto hoe vaak die foto de doorslag gaf, en hoe vaak dat goed of fout was. |
| `methode_1_tabel.csv`, `methode_1_tabel.png`, `methode_1_tijdlijn.png` | De uitkomst van methode 1. |
| `methode_2_tabel.csv`, `methode_2_tabel.png` | De uitkomst van methode 2. |
| `methode_2_verwarring.csv`, `methode_2_verwarring.png` | Per kader wie het echt is tegen de naam van FaceNet. |
| `methode_2_overlap.csv` | De uitkomst van methode 2 bij andere grenzen voor de overlap. |
| `filmpje.mp4` | Het filmpje. |

## Zo maak je dit opnieuw

Vanuit de map `experimenten` (installeren: zie [de uitleg over alle experimenten](../../../README.md#installeren-op-mac-en-windows)).

Op een Mac:

```bash
.venv/bin/python basis/draai_alles.py --voorbeelden fotos_en_kostuum
```

Op Windows:

```bat
.venv\Scripts\python basis\draai_alles.py --voorbeelden fotos_en_kostuum
```
