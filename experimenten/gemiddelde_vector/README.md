# Eén gemiddelde vector per persoon

> **De vraag.** Werkt FaceNet beter als elke persoon één gemiddelde vector krijgt, in plaats van alle voorbeeldfoto's los?
>
> **Het antwoord.** Bij de standaarddrempel van 0,80 niet. De score per gezicht zakt van 0,308 naar 0,181 (foto's + stills). FaceNet geeft dan veel minder namen.

![Staafjes: de score per gezicht met alle voorbeelden los en met één gemiddelde vector](resultaten/vergelijking.png)

*Zo lees je dit plaatje: elk groepje is een set voorbeelden, en een hogere balk is beter. Blauw is de basis, waarbij alle voorbeelden los meedoen. Oranje is één gemiddelde vector per persoon. Oranje is steeds lager.*

Wat de woorden betekenen, staat in [de woordenlijst](../README.md#woordenlijst).


## Waarom dit experiment

In de [basis](../basis/README.md) is elke voorbeeldfoto een los vergelijkingspunt: een gezicht krijgt de naam van de foto die er het meest op lijkt. Zo kan één slechte foto veel fouten veroorzaken. Het idee is dat een gemiddelde daar minder last van heeft.


## Hoe we het gedaan hebben

1. We nemen per persoon alle voorbeeldfoto's en maken daarvan vectoren met lengte 1.
2. We nemen per persoon het gemiddelde van die vectoren, en brengen dat gemiddelde weer op lengte 1.
3. We vergelijken elk gezicht in de filmpjes alleen nog met die vier vectoren.
4. Verder is alles hetzelfde als bij de basis: hetzelfde model, dezelfde drempel van 0,80 en dezelfde twee meetmethodes.

Dat doen we voor drie sets voorbeelden. De uitkomsten staan per set in [`resultaten/`](resultaten/).


## Wat eruit kwam

| Voorbeelden | Score per gezicht: alle foto's los | Score per gezicht: gemiddelde | Score per beeld: alle foto's los | Score per beeld: gemiddelde |
|---|---|---|---|---|
| Foto's | 0,074 | 0,059 | 0,078 | 0,060 |
| Foto's + stills | 0,308 | 0,181 | 0,636 | 0,206 |
| Alleen stills | 0,300 | 0,114 | 0,628 | 0,211 |

![Per kader: wie het echt is tegen de naam van FaceNet, met één gemiddelde vector](resultaten/fotos_en_kostuum/methode_2_verwarring.png)

*Zo lees je dit plaatje: elke rij is wie het echt is, elke kolom is de naam die FaceNet geeft. Bij een goed resultaat staan de hoge percentages op de schuine lijn. Hier staan de meeste kaders in de laatste kolom: FaceNet geeft ze geen naam.*


## Wat dit betekent

- **Bij de drempel van 0,80 werkt een gemiddelde slechter.** Met foto's + stills klopt een naam nu vaak (precisie 0,818), maar krijgt maar één op de tien gezichten de juiste naam (recall 0,102).
- **Waarom dat zo is.** Een gemiddelde van heel verschillende foto's ligt ver van elk echt gezicht. De afstand komt daardoor vaak boven de drempel.
- **Met een eigen drempel is het gemiddelde wel goed.** In [tuned](../tuned/README.md) proberen we ook andere drempels, en daar wint het gemiddelde bij foto's + stills.


## Zo draai je het op een Mac en op Windows

Doe dit vanuit de map `experimenten`, nadat de [basis](../basis/README.md) gedraaid heeft. Installeren hoeft één keer, zie [Installeren op Mac en Windows](../README.md#installeren-op-mac-en-windows).

Op een Mac:

```bash
.venv/bin/python gemiddelde_vector/draai.py
```

Op Windows:

```bat
.venv\Scripts\python gemiddelde_vector\draai.py
```
