# Moving average: een filter dat losse flitsen weghaalt

> **De vraag.** Wordt het resultaat beter met een filter dat losse flitsen in de herkenning weghaalt?
>
> **Het antwoord.** Een beetje. Op de herkenning gaat de score per beeld van 0,636 naar 0,664. Op de score van de detector gaat de score per gezicht van 0,308 naar 0,345.

![Het filter op een echt stukje film: de ruwe herkenning, het lopend gemiddelde, de twee grenzen en de uitkomst](resultaten/uitleg_filter.png)

*Zo lees je dit plaatje: dit is Der Alte in Video 1, met een venster van 15 beelden. Grijs zijn de beelden waarin FaceNet Der Alte ziet. Blauw is het lopend gemiddelde daarvan. Oranje bovenaan is de uitkomst van het filter. Het filter gaat pas aan als de blauwe lijn boven 0,7 komt, en pas uit als de lijn onder 0,2 zakt. Daartussen blijft het zoals het was.*

Wat de woorden betekenen, staat in [de woordenlijst](../README.md#woordenlijst).


## Waarom dit experiment

Een herkenning springt van beeld tot beeld aan en uit. Iemand die vijf seconden in beeld is, wordt dan in losse stukjes herkend. Een *moving average* (lopend gemiddelde) middelt over een aantal beelden, en haalt zulke sprongen eruit.


## Hoe het filter werkt

1. **Het signaal.** Per beeld is er een getal, bijvoorbeeld 1 als FaceNet de persoon ziet en 0 als FaceNet de persoon niet ziet.
2. **Het lopend gemiddelde.** Elk beeld krijgt het gemiddelde van de beelden eromheen, evenveel ervoor als erna. Dat stuk heet het *venster*.
3. **De twee grenzen.** Onder 0,2 is er geen detectie, boven 0,7 wel. Daartussen blijft het zoals het was.

Doordat er twee verschillende grenzen zijn, flikkert de uitkomst niet aan en uit als het gemiddelde rond één grens schommelt.


## Hoe we het gedaan hebben

"Detectie" kan twee dingen betekenen, dus we hebben het filter op twee plekken geprobeerd. FaceNet staat standaard (drempel 0,80), en we proberen vensters van 5 tot 41 beelden.

| | A. Op de score van de detector | B. Op de herkenning |
|---|---|---|
| **Waarop** | Per track | Per persoon |
| **Het signaal** | De score van het kader in elk beeld (0 als er even geen kader is) | 1 als FaceNet de persoon in dat beeld ziet, anders 0 |
| **Wat het filter doet** | Kaders in beelden waar het filter uit staat, tellen niet meer mee | Het filter zegt per beeld of de persoon in beeld is. Het venster loopt nooit over een beeldwissel heen |


## Wat eruit kwam

![Grafiek: de score bij verschillende vensters, voor beide manieren](resultaten/fotos_en_kostuum/filter_vensters.png)

*Zo lees je dit plaatje: van links naar rechts wordt het venster groter. Helemaal links staat de score zonder filter. Blauw (B) stijgt een klein beetje. Oranje (A, score per beeld) daalt. Groen (A, score per gezicht) stijgt eerst een beetje en zakt daarna.*

| Venster (beelden) | geen | 5 | 9 | 15 | 25 | 41 |
|---|---|---|---|---|---|---|
| A: kaders over | 37.003 | 21.460 | 20.471 | 19.702 | 18.828 | 18.203 |
| A: score per beeld | 0,636 | 0,579 | 0,565 | 0,557 | 0,535 | 0,526 |
| A: score per gezicht | 0,308 | **0,345** | 0,332 | 0,328 | 0,318 | 0,304 |
| B: score per beeld | 0,636 | 0,650 | 0,653 | 0,655 | 0,656 | **0,664** |

Dit is met foto's + stills in kostuum. Met alleen de gewone foto's verandert er bijna niets, omdat FaceNet dan toch bijna geen namen geeft ([`resultaten/fotos/`](resultaten/fotos/)).

![De tijdlijn na het filter op de herkenning, venster 15 beelden](resultaten/fotos_en_kostuum/filter_B_tijdlijn.png)

*De tijdlijn na het filter op de herkenning (venster 15 beelden). Zwart is wanneer de persoon echt in beeld is, rood is FaceNet na het filter. De rode stukken zijn nu langer en rustiger.*


## Wat dit betekent

- **Op de score van de detector (A) gooit het filter veel kaders weg.** Met een bovengrens van 0,7 blijft bij een venster van 5 beelden maar 58% van de kaders over. Daardoor verdwijnen er kaders zonder gezicht, en wordt de score per gezicht iets beter. Per beeld wordt de score juist slechter, omdat er ook echte gezichten verdwijnen.
- **Op de herkenning (B) wordt de tijdlijn rustiger.** De precisie stijgt en de recall blijft bijna gelijk, dus de score per beeld wordt iets beter.
- **Het filter lost het echte probleem niet op.** Het veel grotere verschil zit in het afstellen, zie [tuned](../tuned/README.md).

De getallen staan per set in [`resultaten/`](resultaten/): `filter_A_detector.csv` en `filter_B_herkenning.csv`.


## Zo draai je het op een Mac en op Windows

Doe dit vanuit de map `experimenten`, nadat de [basis](../basis/README.md) gedraaid heeft. Installeren hoeft één keer, zie [Installeren op Mac en Windows](../README.md#installeren-op-mac-en-windows).

Op een Mac:

```bash
.venv/bin/python moving_average/draai.py
```

Op Windows:

```bat
.venv\Scripts\python moving_average\draai.py
```
