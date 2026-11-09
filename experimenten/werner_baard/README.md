# Werner met baard

> **De vraag.** Wat gebeurt er als er meer stills van Werner **met baard** in de voorbeelden zitten?
>
> **Het antwoord.** FaceNet vindt Werner vaker: de score van Werner gaat van 0,311 naar 0,431. Die winst komt bijna helemaal van één still: `werner_and_fritz.png`.

![Grafiek: score, precisie en recall van Werner bij steeds meer stills met baard](resultaten/werner_baard.png)

*Zo lees je dit plaatje: van links naar rechts komen er steeds meer stills van Werner met baard bij. Blauw is de score van Werner, en die loopt op. Oranje is de precisie: die blijft hoog, dus de naam Werner blijft kloppen. Groen is de recall: die stijgt, dus FaceNet vindt Werner vaker. Het lichtblauwe vlak laat zien hoe ver de score uiteenloopt tussen de verschillende combinaties.*

Wat de woorden betekenen, staat in [de woordenlijst](../README.md#woordenlijst).


## Waarom dit experiment

Op een deel van de stills heeft Werner een baard, en op een deel niet. We willen weten of FaceNet Werner beter vindt als er meer voorbeelden met baard zijn. We gebruiken alleen stills. Beelden uit de filmpjes die we testen, mogen geen voorbeeld zijn.


## Hoe we het gedaan hebben

De stills van Werner, ingedeeld op baard:

![De stills van Werner: met baard, zonder baard, en niet te zien](resultaten/werner_stills.jpg)

*De 12 stills van Werner in de in-karakter set. Op 6 stills heeft Werner een baard, op 5 niet. Op 1 still is dat niet te zien, want die is te donker. Die still doet hier niet mee.*

1. We beginnen met de 5 stills zonder baard.
2. We voegen daar 1 tot en met 6 stills met baard aan toe.
3. Omdat het uitmaakt welke still je toevoegt, proberen we elke combinatie: 64 in totaal.
4. De andere drie personen blijven hetzelfde.
5. FaceNet staat standaard (drempel 0,80), en we meten met methode 2 (per gezicht).


## Wat eruit kwam

De getallen zijn het gemiddelde van alle combinaties met dat aantal stills.

| Stills met baard | Precisie van Werner | Recall van Werner | **Score van Werner** | Score van alle vier |
|---|---|---|---|---|
| 0 | 0,966 | 0,185 | **0,311** | 0,292 |
| 1 | 0,963 | 0,201 | **0,331** | 0,295 |
| 2 | 0,960 | 0,217 | **0,351** | 0,298 |
| 3 | 0,958 | 0,232 | **0,371** | 0,302 |
| 4 | 0,956 | 0,248 | **0,391** | 0,305 |
| 5 | 0,954 | 0,263 | **0,411** | 0,309 |
| 6 | 0,953 | 0,279 | **0,431** | 0,312 |


## Wat dit betekent

- **Met meer stills met baard vindt FaceNet Werner vaker.** De recall gaat van 0,185 naar 0,279.
- **De naam Werner blijft kloppen.** De precisie blijft rond 0,95.
- **Het gaat om één foto, niet om het aantal.** Met alleen de still `werner_and_fritz.png` erbij is de score van Werner al 0,431. De andere vijf stills veranderen daar vrijwel niets aan. Die ene foto lijkt op de gezichten in de film.

Alle combinaties staan in [`alle_combinaties.csv`](resultaten/alle_combinaties.csv).


## Zo draai je het op een Mac en op Windows

Doe dit vanuit de map `experimenten`, nadat de [basis](../basis/README.md) gedraaid heeft. Installeren hoeft één keer, zie [Installeren op Mac en Windows](../README.md#installeren-op-mac-en-windows).

Op een Mac:

```bash
.venv/bin/python werner_baard/draai.py
```

Op Windows:

```bat
.venv\Scripts\python werner_baard\draai.py
```
