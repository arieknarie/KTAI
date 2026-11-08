# Spreiding: hoe ver liggen de voorbeeldfoto's uit elkaar?

FaceNet maakt van elke foto een vector, en de afstand tussen twee vectoren zegt hoe verschillend twee gezichten zijn voor FaceNet. In dit experiment kijken we naar de voorbeeldfoto's zelf, voor de out-of-character set, de in-character set en de totale set:

- de **maximale afstand** tussen twee foto's van dezelfde persoon (de spreiding);
- de **minimale afstand** tussen twee foto's van verschillende personen;
- of FaceNet bij een onherkenbaar kader kiest voor de persoon met de grootste spreiding.

## Hoe we het gedaan hebben

We gebruiken FaceNet standaard en de genormaliseerde Euclidische afstand. We rekenen de afstand uit tussen alle voorbeelden in een set, en zoeken per persoon de grootste afstand en per paar personen de kleinste afstand. Daarna tellen we bij alle kaders die op geen van de vier gezichten liggen (figuranten, en dingen die geen gezicht zijn) welke persoon het dichtstbij is. Die kaders zijn voor FaceNet immers niet te herkennen.

![Drie tabellen als kleurvlakken: de grootste afstand binnen een persoon en de kleinste afstand tussen twee personen, per set](resultaten/afstanden.png)

![De twee verste foto's van elke persoon en de twee dichtste foto's van elk paar personen](resultaten/verste_en_dichtste_fotos.jpg)

*De totale set: de twee foto's met de grootste afstand binnen een persoon, en de twee foto's met de kleinste afstand tussen twee personen.*

## Wat eruit kwam

**De spreiding is veel groter bij de stills.** In de out-of-character set is de maximale afstand 0,96 tot 1,19, in de in-character set 1,34 tot 1,49. Dat is logisch: de stills zijn donker, wazig of van opzij.

**Verschillende personen liggen bij de stills heel dicht bij elkaar.** In de out-of-character set is de kleinste afstand tussen twee personen 1,00 tot 1,42, ruim boven de drempel van 0,80. In de in-character set is dat 0,24 tot 0,36, ver onder de drempel. Dat betekent dat een kader dat op zo'n still lijkt, zomaar de verkeerde naam krijgt. De dichtste paren zijn steeds de donkere en wazige gezichten, zoals `Fritz4.png`, `Fritz1.jpg`, `johann3.png` en `johann_and_fritz.png`. Dat zijn ook de foto's die in [leave-one-out](../leave_one_out/README.md) en bij [de Johann-fouten](../wie_wordt_johann/README.md) terugkomen.

**Kiest FaceNet bij een onherkenbaar kader de persoon met de grootste spreiding?** Dat klopt in één van de drie sets.

| Set | Grootste spreiding | Vaakst dichtstbij bij een onherkenbaar kader |
|---|---|---|
| Out-of-character | Fritz Grade (1,19) | Werner (81,2%); Fritz Grade 14,8% |
| In-character | Der Alte (1,49) | Der Alte (38,8%) |
| Totale set | Fritz Grade (1,50) | Der Alte (38,9%); Fritz Grade 34,7% |

Het idee is dus niet algemeen waar. Wie er bij een onherkenbaar kader wint, lijkt vooral af te hangen van welke donkere, wazige foto's er in de set zitten, en niet van de spreiding zelf.

Alle getallen staan in [`spreiding.csv`](resultaten/spreiding.csv), [`kleinste_afstand.csv`](resultaten/kleinste_afstand.csv) en [`onherkenbaar.csv`](resultaten/onherkenbaar.csv).

## Zo draai je het op een Mac en op Windows

Doe dit vanuit de map `experimenten`, nadat de [basis](../basis/README.md) gedraaid heeft. Installeren hoeft één keer, zie [de uitleg over alle experimenten](../README.md#installeren-op-mac-en-windows).

Op een Mac:

```bash
.venv/bin/python spreiding/draai.py
```

Op Windows:

```bat
.venv\Scripts\python spreiding\draai.py
```
