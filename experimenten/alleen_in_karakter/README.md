# Alleen de in-karakter foto's

De basis gebruikt de gewone foto's van de acteurs (*out-of-character*) en de stills in kostuum (*in-character*). In dit experiment gebruiken we **alleen de stills**. Dat beantwoordt twee vragen: hoe ziet de tijdlijn eruit
als FaceNet alleen in-karakter foto's als voorbeeld heeft, en hoe belangrijk zijn de out-of-character foto's nog als de in-karakter foto's er al zijn (een *ablation*: een onderdeel weglaten om te zien wat dat onderdeel doet)?

## Hoe we het gedaan hebben

We draaien precies dezelfde stappen als de [basis](../basis/README.md) (FaceNet standaard, drempel 0,80), maar met alleen de 50 gezichten op de stills als voorbeeld. Beide meetmethodes en het filmpje staan in [`resultaten/`](resultaten/), en de uitleg met alle getallen in [`resultaten/README.md`](resultaten/README.md). Zoals altijd doen de drie stills die (bijna) een beeld uit een filmpje zijn niet mee.

![De voorbeelden: alleen de stills in kostuum](resultaten/voorbeelden.jpg)

## Wat eruit kwam

![De tijdlijn met alleen de in-karakter foto's: de ground truth en FaceNet](resultaten/methode_1_tijdlijn.png)

| Voorbeelden | Aantal | Methode 1: F1 | Methode 2: F1 |
|---|---|---|---|
| Alleen foto's (out-of-character) | 23 | 0,078 | 0,074 |
| Alleen stills (in-character) | 50 | 0,628 | 0,300 |
| Foto's + stills (totale set) | 73 | 0,636 | 0,308 |

![Staafjes: de F1 van de drie sets voorbeelden, met beide meetmethodes](resultaten/vergelijking.png)

**Wat dit betekent.** Vrijwel alle winst komt van de stills. Laat je de out-of-character foto's weg, dan zakt de F1 maar 0,008 (van 0,308 naar 0,300 met methode 2, en van 0,636 naar 0,628 met methode 1). De gewone foto's voegen dus bijna niets toe zodra de stills er zijn. Andersom niet: met alleen de gewone foto's
herkent FaceNet bijna niemand.

Het filmpje staat in [`resultaten/filmpje.mp4`](resultaten/filmpje.mp4).

## Zo draai je het op een Mac en op Windows

Doe dit vanuit de map `experimenten`, nadat de [basis](../basis/README.md) gedraaid heeft. Installeren hoeft één keer, zie [de uitleg over alle experimenten](../README.md#installeren-op-mac-en-windows).

Op een Mac:

```bash
.venv/bin/python alleen_in_karakter/draai.py
```

Op Windows:

```bat
.venv\Scripts\python alleen_in_karakter\draai.py
```
