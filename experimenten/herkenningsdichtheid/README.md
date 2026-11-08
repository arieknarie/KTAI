# Herkenningsdichtheid op de tijdlijn

De tijdlijn van de basis laat voor elk beeld zien of FaceNet een persoon ziet: aan of uit. In een rommelig stuk film springt dat heen en weer, en dan is moeilijk te zien hoe zeker de herkenning is. Met een *convolutiefilter* rekenen we daarom de **herkenningsdichtheid** uit: het gemiddelde aantal herkenningen per tijdseenheid.

## Hoe we het gedaan hebben

Per persoon en per beeld is het signaal 1 als FaceNet die persoon in dat beeld ziet, en anders 0 (de basis, FaceNet standaard). Dat signaal halen we door een convolutie met een blokvormig venster: elk beeld krijgt het gemiddelde over het venster eromheen. Een dichtheid van 0,8 betekent dat FaceNet de persoon in 80% van de beelden in het venster ziet. We proberen vensters van 10, 15 en 20 beelden (ongeveer een halve tot een hele seconde).

## Wat eruit kwam

![Per filmpje en per persoon de herkenningsdichtheid als kleur, met de ground truth als zwarte lijn](resultaten/fotos_en_kostuum/dichtheid_venster_15.png)

*Foto's + stills, venster 15 beelden. Hoe donkerder de strook, hoe vaker FaceNet de persoon in het venster ziet. De zwarte lijn onder een strook laat zien wanneer de persoon volgens de ground truth echt in beeld is.*

| Voorbeelden | Persoon | Gemiddelde dichtheid FaceNet | Volgens de ground truth | Gemiddeld verschil |
|---|---|---|---|---|
| Foto's + stills | Der Alte | 0,551 | 0,745 | 0,372 |
| Foto's + stills | Fritz Grade | 0,531 | 0,476 | 0,195 |
| Foto's + stills | Johann | 0,385 | 0,076 | 0,418 |
| Foto's + stills | Werner | 0,356 | 0,581 | 0,342 |

**Wat dit betekent.** De dichtheid laat in één oogopslag zien waar FaceNet zeker is en waar de naam heen en weer springt. Bij Der Alte en Werner is de dichtheid lager dan zou moeten: FaceNet mist ze vaak. Bij Johann is de dichtheid veel hoger dan zou moeten: FaceNet ziet Johann op plekken waar hij er niet is (zie [Wie wordt als Johann herkend?](../wie_wordt_johann/README.md)). De grootte van het venster verandert de gemiddelde dichtheid vrijwel niet (de tabel met alle vensters staat in [`dichtheid_samenvatting.csv`](resultaten/dichtheid_samenvatting.csv)); een groter venster maakt de strook alleen rustiger.

De dichtheid per beeld staat in `dichtheid_venster_<n>.csv` in [`resultaten/`](resultaten/), per set.

## Zo draai je het op een Mac en op Windows

Doe dit vanuit de map `experimenten`, nadat de [basis](../basis/README.md) gedraaid heeft. Installeren hoeft één keer, zie [de uitleg over alle experimenten](../README.md#installeren-op-mac-en-windows).

Op een Mac:

```bash
.venv/bin/python herkenningsdichtheid/draai.py
```

Op Windows:

```bat
.venv\Scripts\python herkenningsdichtheid\draai.py
```
