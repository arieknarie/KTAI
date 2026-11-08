# Wie wordt als Johann herkend?

In de basis met stills zegt FaceNet veel te vaak Johann: in 4.302 beelden, terwijl Johann maar in 849 beelden staat. In dit experiment kijken we wie er echt staat als FaceNet ten onrechte Johann zegt.

## Hoe we het gedaan hebben

We nemen alle kaders waaraan FaceNet (standaard, drempel 0,80) de naam Johann geeft, terwijl het kader niet op het gezicht van Johann ligt. In de ground truth staat voor elk van die kaders wie het echt is: een van de andere drie personen, of geen van de vier (een figurant of iets dat geen gezicht is). Dat tellen we per filmpje, voor de sets met stills, en we kijken welke voorbeeldfoto de doorslag gaf. Met alleen de gewone foto's zegt FaceNet nergens ten onrechte Johann.

![Per filmpje: hoeveel kaders ten onrechte Johann heten, en wie het echt is](resultaten/wie_wordt_johann.png)

## Wat eruit kwam

In de filmpjes waarin Johann helemaal niet voorkomt (Video 1 tot en met 7), noemt FaceNet 4.522 kaders ten onrechte Johann (met foto's + stills):

| Wie het echt is | Aantal kaders | Deel |
|---|---|---|
| Geen van de vier (figurant, of geen gezicht) | 1.835 | 40,6% |
| Der Alte | 1.777 | 39,3% |
| Fritz Grade | 633 | 14,0% |
| Werner | 277 | 6,1% |

Der Alte wordt dus het vaakst voor Johann aangezien, en verder vooral figuranten en dingen die geen gezicht zijn. Over alle filmpjes samen zijn het 5.858 kaders.

**De oorzaak is vooral één foto.** Van die 5.858 kaders gaf `johann3.png` 5.054 keer de doorslag (86%).

![De voorbeeldfoto's die het vaakst de doorslag gaven bij een onterechte Johann](resultaten/johann_fotos.jpg)

*De voorbeeldfoto's die het vaakst de doorslag gaven, met hoe vaak.*

Wat er gebeurt als die foto wordt weggelaten, staat in [leave-one-out](../leave_one_out/README.md): dan wordt de F1 per gezicht 0,049 hoger. Alle getallen staan in [`johann_per_filmpje.csv`](resultaten/johann_per_filmpje.csv) en [`johann_per_foto.csv`](resultaten/johann_per_foto.csv).

## Zo draai je het op een Mac en op Windows

Doe dit vanuit de map `experimenten`, nadat de [basis](../basis/README.md) gedraaid heeft. Installeren hoeft één keer, zie [de uitleg over alle experimenten](../README.md#installeren-op-mac-en-windows).

Op een Mac:

```bash
.venv/bin/python wie_wordt_johann/draai.py
```

Op Windows:

```bat
.venv\Scripts\python wie_wordt_johann\draai.py
```
