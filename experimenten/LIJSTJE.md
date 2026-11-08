# Het lijstje

Dit is alles waar aan gewerkt wordt. Een vinkje betekent: klaar en op GitHub.

![Eén beeld door het hele proces, van het filmpje tot de ground truth](../labelen/fotos/overzicht.jpg)

## Klaar

- [x] Branch `final-version` met `filmpjes/` en `labelen/` (code per stap, `output/`, uitleg met foto's, Mac en Windows)

## Experimenten

- [x] `basis/`: FaceNet standaard, met foto's en met foto's + kostuum: code in stappen, map `resultaten`, beide meetmethodes (per beeld en per gezicht) met een keuze voor de tweede, een filmpje en md's
- [x] `tuned/`: hetzelfde met de best mogelijke instellingen, ook voor beide sets foto's
- [x] Rapporteren welke foto precies gebruikt is voor elke identificatie
- [x] Moving average filter op de detectie (onder 0,2 geen detectie, boven 0,7 wel)
- [x] Spreiding binnen een karakter en kleinste afstand tussen karakters, voor out-of-character, in-character en de totale set, met figuren
- [x] Testen of FaceNet bij een onherkenbaar beeld kiest voor het karakter met de grootste spreiding
- [x] Tijdlijnen op basis van alleen de in-karakter foto's, en dus ook: wat gebeurt er zonder de out-of-character foto's
- [x] Leave-one-out: welke foto's maken het resultaat slechter
- [x] Convolutiefilter: herkenningsdichtheid op de tijdlijn (venster van 10 tot 20 beelden)
- [x] Wie wordt als Johann herkend op plekken waar Johann er niet is
- [x] De vectoren per persoon samenvoegen tot één gemiddelde vector
- [x] Werner met baard: wat gebeurt er als meer stills van Werner met baard in de in-karakter set zitten (alleen stills, geen beelden uit de filmpjes)
- [x] `README.md` over alle experimenten, en hoe je ze draait op Mac en Windows
