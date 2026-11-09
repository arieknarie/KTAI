# Leave-one-out: welke voorbeeldfoto's maken het resultaat slechter?

> **De vraag.** Zitten er voorbeeldfoto's tussen die FaceNet juist slechter maken?
>
> **Het antwoord.** Ja. Zonder de ene foto `johann3.png` gaat de score per gezicht van 0,308 naar 0,357. Laat je steeds de schadelijkste foto weg, dan is de score met acht foto's minder 0,426. Die acht foto's zijn gekozen op dezelfde beelden als waarop we meten, dus die laatste score is te gunstig.

![Per voorbeeld: hoeveel de score verandert als het voorbeeld wordt weggelaten](resultaten/fotos_en_kostuum/leave_one_out.png)

*Zo lees je dit plaatje: elke regel is één voorbeeld, in de set met foto's + stills. Een rode balk naar rechts betekent dat de score hoger wordt zonder dat voorbeeld: die foto is dus schadelijk. Een blauwe balk naar links betekent dat de score lager wordt: die foto helpt. Voorbeelden die niets veranderen, staan er niet bij.*

Wat de woorden betekenen, staat in [de woordenlijst](../README.md#woordenlijst).


## Waarom dit experiment

Niet elke voorbeeldfoto helpt. Een donkere of wazige foto kan ervoor zorgen dat veel gezichten de verkeerde naam krijgen. Met *leave-one-out* (één weglaten) vinden we die foto's.


## Hoe we het gedaan hebben

1. FaceNet staat standaard, met een drempel van 0,80.
2. We laten één voorbeeld weg en meten opnieuw, met beide meetmethodes. De vectoren veranderen niet, alleen de lijst met voorbeelden verandert.
3. Dat doen we voor elk voorbeeld, en voor de drie sets voorbeelden.
4. Daarna laten we stap voor stap steeds de foto weg die de score het meest verbetert, tot weglaten niet meer helpt.


## Wat eruit kwam

Van de 73 voorbeelden in de set met foto's + stills maken er 5 het resultaat slechter, 22 maken het beter en 46 veranderen niets.

Dit zijn de 5 foto's waarbij het resultaat beter wordt zonder die foto:

| Foto | Label van dit gezicht | Score per gezicht zonder de foto | Score per beeld zonder de foto |
|---|---|---|---|
| `johann3.png` | Johann | **+0,049** | +0,085 |
| `alte_and_werner_and_fritz.jpg` | Fritz Grade | +0,014 | +0,006 |
| `Fritz1.jpg` | Werner | +0,012 | -0,029 |
| `Fritz5.png` | Fritz Grade | +0,001 | -0,002 |
| `johann2.png` | Johann | +0,001 | +0,003 |

![De voorbeeldfoto's waarbij het resultaat beter wordt zonder die foto](resultaten/fotos_en_kostuum/slechtste_fotos.jpg)

*Deze foto's maken het resultaat slechter. Boven elke foto staat het label en hoeveel de score stijgt zonder die foto. Bijna allemaal zijn ze donker, wazig of half in beeld.*

Dit gebeurt er als je steeds de schadelijkste foto weglaat:

| Stap | Weggelaten | Voorbeelden over | Score per gezicht |
|---|---|---|---|
| 0 | niets | 73 | 0,308 |
| 1 | Johann: `johann3.png` | 72 | 0,357 |
| 2 | Werner: `Fritz1.jpg` | 71 | 0,388 |
| 3 | Fritz Grade: `alte_and_werner_and_fritz.jpg` | 70 | 0,404 |
| 4 | Fritz Grade: `Fritz5.png` | 69 | 0,407 |
| 5 | Johann: `johann2.png` | 68 | 0,412 |
| 6 | Fritz Grade: `derAlte2.jpg` | 67 | 0,414 |
| 7 | Johann: `werner_and_johann.jpg` | 66 | 0,421 |
| 8 | Johann: `johann_and_fritz.png` | 65 | 0,426 |


## Wat dit betekent

- **Eén foto doet het meeste kwaad.** Zonder `johann3.png` stijgt de score van 0,308 naar 0,357.
- **Een foto die vaak gekozen wordt, is niet altijd schadelijk.** Het gezicht met het label Der Alte in `Fritz4.png` leek 10.016 keer het meest op een kader. Zonder die foto wordt het resultaat toch slechter (score -0,020), omdat die kaders dan naar een andere persoon gaan.
- **Met alleen de gewone foto's maakt geen enkele foto het resultaat slechter.** 11 foto's helpen en 12 veranderen niets ([`resultaten/fotos/`](resultaten/fotos/)). FaceNet geeft met die foto's dan ook bijna geen namen.

De bestanden per set staan in [`resultaten/`](resultaten/): `leave_one_out.csv` (elke foto), `weglaten_stap_voor_stap.csv`, `leave_one_out.png` en `slechtste_fotos.jpg`.


## Zo draai je het op een Mac en op Windows

Doe dit vanuit de map `experimenten`, nadat de [basis](../basis/README.md) en [alleen in karakter](../alleen_in_karakter/README.md) gedraaid hebben. Installeren hoeft één keer, zie [Installeren op Mac en Windows](../README.md#installeren-op-mac-en-windows).

Op een Mac:

```bash
.venv/bin/python leave_one_out/draai.py
```

Op Windows:

```bat
.venv\Scripts\python leave_one_out\draai.py
```
