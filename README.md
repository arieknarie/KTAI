# FaceNet getest op *Das Boot*

Dit is ons project voor de cursus *Key Topics in Artificial Intelligence* van de Open Universiteit. We testen hoe goed het programma **FaceNet** vier personen herkent in fragmenten uit de film *Das Boot*: Der Alte, Fritz Grade, Johann en Werner.

> **Het antwoord in het kort.** Met de standaardinstellingen herkent FaceNet de personen slecht: de score is 0,074 met gewone foto's als voorbeeld, en 0,308 met foto's en stills uit de film. Goed afgesteld wordt de score 0,808 met foto's en 0,874 met foto's en stills.
>
> De score is een cijfer van 0 tot 1. Bij 1 vindt FaceNet alle gezichten en klopt elke naam.

![Hetzelfde stukje film twee keer: links FaceNet standaard met veel rode namen, rechts FaceNet afgesteld met alleen groene namen](experimenten/fotos/basis_tegen_tuned.gif)

*Hetzelfde stukje film, links met FaceNet standaard en rechts met FaceNet afgesteld. Groen betekent dat de naam klopt, rood dat de naam niet klopt. Van de vier personen staan in dit stukje alleen Der Alte en Werner in beeld. De andere gezichten zijn figuranten, en die horen geen naam te krijgen.*


## Zo zit het project in elkaar

Het project bestaat uit drie delen, en elk deel bouwt voort op het vorige.

| Deel | Wat er gebeurt | Waar |
|---|---|---|
| **1. De filmpjes** | Acht fragmenten uit *Das Boot*, samen 11.182 beelden. | [`filmpjes/`](filmpjes/) |
| **2. Het labelen** | Met de hand is vastgelegd wie er in elk beeld staat en waar. Die lijst heet de *ground truth*. Daarmee kijken we FaceNet na. | [`labelen/`](labelen/README.md) |
| **3. De experimenten** | FaceNet wordt getest: eerst standaard, dan zo goed mogelijk afgesteld, en daarna met acht andere proeven. | [`experimenten/`](experimenten/README.md) |

![Eén beeld door het hele labelproces: het filmpje, de gevonden kaders, de labels per track, het nakijken, het verbeteren en de ground truth](labelen/fotos/overzicht.jpg)

*Zo is de ground truth gemaakt. Eén beeld gaat door alle stappen: van het filmpje naar de lijst waarin staat wie er in dit beeld te zien is en waar.*


## Waar begin ik met lezen?

| Je wilt weten | Lees dan |
|---|---|
| wat er uit alle experimenten gekomen is | [Alle experimenten](experimenten/README.md#alle-experimenten) |
| hoe FaceNet aan een gezicht een naam geeft | [Zo werkt FaceNet](experimenten/README.md#zo-werkt-facenet) |
| hoe we meten of FaceNet goed is | [Zo meten we hoe goed FaceNet is](experimenten/README.md#zo-meten-we-hoe-goed-facenet-is) |
| waarom afstellen zoveel uitmaakt | [Waarom afstellen zoveel uitmaakt](experimenten/README.md#waarom-afstellen-zoveel-uitmaakt) |
| wat een woord betekent | [De woordenlijst met plaatjes](experimenten/README.md#woordenlijst) |
| hoe FaceNet het doet zonder afstellen | [Basis](experimenten/basis/README.md) |
| hoe FaceNet het doet na het afstellen | [Tuned](experimenten/tuned/README.md) |
| hoe de juiste antwoorden gemaakt zijn | [Het labelen](labelen/README.md) |


## Zelf draaien op Mac en Windows

Alle uitkomsten staan al in de mappen. Opnieuw draaien hoeft alleen als je iets wilt veranderen.

Zet eerst het project op je computer. Dat is ongeveer 1 GB. Zet de map niet in iCloud, OneDrive of een andere clouddienst.

Op een Mac en op Windows gaat dat hetzelfde:

```bash
git clone -b final-version https://github.com/arieknarie/KTAI.git
```

Daarna kies je wat je wilt draaien. Per deel staat precies beschreven wat je op een Mac en op Windows moet doen:

- [Het labelen installeren en draaien](labelen/README.md#installeren-op-mac-en-windows)
- [De experimenten installeren en draaien](experimenten/README.md#installeren-op-mac-en-windows)

Op Windows hebben we de programma's niet zelf uitgeprobeerd. De opdrachten zijn daar beschreven zoals ze zouden moeten werken.
