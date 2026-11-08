# Werner met baard

In dit experiment kijken we wat er gebeurt als er meer stills van Werner **met baard** in de in-karakter set zitten. Er zijn alleen stills gebruikt; beelden uit de filmpjes mogen geen voorbeeld zijn.

## Hoe we het gedaan hebben

De in-karakter set heeft 12 stills van Werner. Daarvan hebben er 6 een baard en 5 geen baard. Op 1 still is dat niet te zien (te donker); die doet hier niet mee. De andere drie personen blijven hetzelfde.

![De stills van Werner: met baard, zonder baard, en niet te zien](resultaten/werner_stills.jpg)

We beginnen met de 5 stills zonder baard, en voegen daar 1 tot en met 6 stills met baard aan toe. Omdat het uitmaakt welke still je toevoegt, proberen we elke combinatie: 64 in totaal. FaceNet staat standaard (drempel 0,80), en we meten met methode 2 (per gezicht).

## Wat eruit kwam

![Grafiek: F1, precisie en recall van Werner bij steeds meer stills met baard](resultaten/werner_baard.png)

| Stills met baard | Werner: precisie | recall | **F1** (gemiddeld over de combinaties) | F1 laagste tot hoogste | Alle vier: F1 |
|---|---|---|---|---|---|
| 0 | 0,966 | 0,185 | **0,311** | 0,311 | 0,292 |
| 1 | 0,963 | 0,201 | **0,331** | 0,311 tot 0,431 | 0,295 |
| 2 | 0,960 | 0,217 | **0,351** | 0,311 tot 0,432 | 0,298 |
| 3 | 0,958 | 0,232 | **0,371** | 0,311 tot 0,432 | 0,302 |
| 4 | 0,956 | 0,248 | **0,391** | 0,311 tot 0,432 | 0,305 |
| 5 | 0,954 | 0,263 | **0,411** | 0,312 tot 0,432 | 0,309 |
| 6 | 0,953 | 0,279 | **0,431** | 0,431 | 0,312 |

**Wat dit betekent.** Met meer stills met baard vindt FaceNet Werner vaker (recall van 0,185 naar 0,279), terwijl een naam Werner bijna altijd blijft kloppen (precisie rond 0,95). De F1 van Werner stijgt van 0,311 naar 0,431.

De winst komt bijna helemaal van één still: `werner_and_fritz.png`. Met alleen die still erbij is de F1 van Werner al 0,431; de andere vijf stills veranderen er vrijwel niets aan. Het gaat dus niet om het aantal foto's met baard, maar om één foto die op de gezichten in de film lijkt. Alle combinaties staan in [`alle_combinaties.csv`](resultaten/alle_combinaties.csv).

## Zo draai je het op een Mac en op Windows

Doe dit vanuit de map `experimenten`, nadat de [basis](../basis/README.md) gedraaid heeft. Installeren hoeft één keer, zie [de uitleg over alle experimenten](../README.md#installeren-op-mac-en-windows).

Op een Mac:

```bash
.venv/bin/python werner_baard/draai.py
```

Op Windows:

```bat
.venv\Scripts\python werner_baard\draai.py
```
