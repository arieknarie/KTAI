# Spreiding: hoe ver liggen de voorbeeldfoto's uit elkaar?

> **De vraag.** Hoe verschillend zijn de foto's van één persoon voor FaceNet, en hoe dicht liggen de foto's van verschillende personen bij elkaar? En kiest FaceNet bij een onherkenbaar kader de persoon met de grootste spreiding?
>
> **Het antwoord.** Bij de stills liggen de foto's van één persoon ver uit elkaar (1,34 tot 1,49), en de foto's van verschillende personen juist heel dicht bij elkaar (0,24 tot 0,36). Dat verklaart veel fouten. Het idee over de spreiding klopt maar in één van de drie sets.

![Drie tabellen als kleurvlakken: de grootste afstand binnen een persoon en de kleinste afstand tussen twee personen, per set](resultaten/afstanden.png)

*Zo lees je dit plaatje: er zijn drie sets voorbeelden. In de vakjes op de schuine lijn staat de grootste afstand tussen twee foto's van dezelfde persoon: de spreiding. In de andere vakjes staat de kleinste afstand tussen twee foto's van verschillende personen. Hoe groter de afstand, hoe minder de foto's voor FaceNet op elkaar lijken. Kijk naar de middelste tabel: de lichte vakjes (0,24 tot 0,36) liggen ver onder de drempel van 0,80.*

Wat de woorden betekenen, staat in [de woordenlijst](../README.md#woordenlijst).


## Waarom dit experiment

FaceNet geeft een naam als de afstand tot een voorbeeld klein genoeg is. Dat werkt alleen als foto's van verschillende personen ver genoeg uit elkaar liggen. Daarom kijken we naar de voorbeeldfoto's zelf.


## Hoe we het gedaan hebben

1. We gebruiken FaceNet standaard en de genormaliseerde Euclidische afstand.
2. We rekenen de afstand uit tussen alle voorbeelden in een set.
3. Per persoon zoeken we de grootste afstand binnen die persoon: de *spreiding*.
4. Per paar personen zoeken we de kleinste afstand tussen die twee.
5. We doen dat voor drie sets: de gewone foto's (out-of-character), de stills (in-character) en de totale set.


## Wat eruit kwam

**De spreiding is groter bij de stills.** Bij de gewone foto's is de grootste afstand 0,96 tot 1,19, bij de stills 1,34 tot 1,49. De stills zijn dan ook donker, wazig of van opzij genomen.

**Verschillende personen liggen bij de stills heel dicht bij elkaar.**

| Set | Kleinste afstand tussen twee personen | Ten opzichte van de drempel van 0,80 |
|---|---|---|
| Gewone foto's | 1,00 tot 1,42 | ruim erboven |
| Stills | 0,24 tot 0,36 | ver eronder |

Een gezicht in de film dat op zo'n still lijkt, kan dus zomaar de verkeerde naam krijgen.

![De twee verste foto's van elke persoon en de twee dichtste foto's van elk paar personen](resultaten/verste_en_dichtste_fotos.jpg)

*Zo lees je dit plaatje: boven elk paar foto's staat wat het paar laat zien. Bij* grootste afstand *staan de twee foto's van dezelfde persoon die het minst op elkaar lijken. Bij* kleinste afstand *staan twee foto's van verschillende personen die voor FaceNet het meest op elkaar lijken. Dat laatste zijn steeds donkere of wazige beelden.*

Dezelfde donkere en wazige foto's, zoals `Fritz4.png`, `Fritz1.jpg`, `johann3.png` en `johann_and_fritz.png`, komen terug bij [Leave-one-out](../leave_one_out/README.md) en [Wie wordt Johann](../wie_wordt_johann/README.md).


## Kiest FaceNet bij een onherkenbaar kader de persoon met de grootste spreiding?

Het idee is: de persoon met de grootste spreiding heeft voorbeelden in alle richtingen, en ligt dus vaak het dichtst bij een onherkenbaar kader. Om dat te testen, tellen we bij alle kaders die op geen van de vier gezichten liggen (figuranten en dingen die geen gezicht zijn) welke persoon het dichtstbij is.

| Set | Grootste spreiding | Vaakst dichtstbij | Klopt het idee? |
|---|---|---|---|
| Gewone foto's | Fritz Grade (1,19) | Werner (81,2%) | nee |
| Stills | Der Alte (1,49) | Der Alte (38,8%) | ja |
| Totale set | Fritz Grade (1,50) | Der Alte (38,9%) | nee |

Het idee is dus niet algemeen waar. Wie er bij een onherkenbaar kader wint, lijkt vooral af te hangen van welke donkere en wazige foto's er in de set zitten.

Alle getallen staan in [`spreiding.csv`](resultaten/spreiding.csv), [`kleinste_afstand.csv`](resultaten/kleinste_afstand.csv) en [`onherkenbaar.csv`](resultaten/onherkenbaar.csv).


## Zo draai je het op een Mac en op Windows

Doe dit vanuit de map `experimenten`, nadat de [basis](../basis/README.md) gedraaid heeft. Installeren hoeft één keer, zie [Installeren op Mac en Windows](../README.md#installeren-op-mac-en-windows).

Op een Mac:

```bash
.venv/bin/python spreiding/draai.py
```

Op Windows:

```bat
.venv\Scripts\python spreiding\draai.py
```
