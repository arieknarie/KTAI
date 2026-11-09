# De experimenten: hoe goed herkent FaceNet de vier personen?

In deze map testen we **FaceNet**, een programma dat gezichten herkent, op fragmenten uit de film *Das Boot*. We zoeken vier personen: Der Alte, Fritz Grade, Johann en Werner. De juiste antwoorden komen uit [het labelen](../labelen/README.md).

> **Het antwoord in het kort.** FaceNet zonder afstellen is slecht: met gewone foto's als voorbeeld krijgt bijna niemand een naam (score 0,074), en met stills uit de film krijgt bijna iedereen een naam, vaak de verkeerde (score 0,308). Goed afgesteld haalt FaceNet een score van 0,874. De winst komt vooral van de juiste drempel, het lichter maken van donkere gezichten, vergelijken met het gemiddelde van de foto's en per track beslissen.

![Staafjes: de score van elk experiment, met beide meetmethodes](overzicht.png)

*Zo lees je dit plaatje: elke regel is een experiment, en een langere balk is beter. Blauw is de score per beeld, oranje de score per gezicht. Oranje is de strengste maat, en daarmee beoordelen we FaceNet. Dezelfde getallen staan in [`overzicht.csv`](overzicht.csv).*

**In deze uitleg:**
[Zo werkt FaceNet](#zo-werkt-facenet) ·
[Zo meten we](#zo-meten-we-hoe-goed-facenet-is) ·
[Waarom afstellen zoveel uitmaakt](#waarom-afstellen-zoveel-uitmaakt) ·
[Alle experimenten](#alle-experimenten) ·
[Woordenlijst](#woordenlijst) ·
[Installeren](#installeren-op-mac-en-windows) ·
[Draaien](#zo-draai-je-de-experimenten) ·
[Wat er in deze map staat](#wat-er-in-deze-map-staat)


## Zo werkt FaceNet

FaceNet kent geen namen. FaceNet maakt van een gezicht een rij van 128 getallen, een *vector*. Twee foto's van dezelfde persoon geven rijen die op elkaar lijken. Daarom geven we FaceNet voorbeeldfoto's van de vier personen, en vergelijken we elk gezicht in de film daarmee.

Zo krijgt een gezicht een naam:

1. De detector uit het labelen heeft al een *kader* om elk gezicht gezet.
2. FaceNet maakt van het gezicht in het kader een vector.
3. We meten de afstand tot de vectoren van alle voorbeeldfoto's. Een kleine afstand betekent dat de gezichten voor FaceNet op elkaar lijken.
4. De persoon met het dichtstbijzijnde voorbeeld is de kandidaat.
5. Is die afstand kleiner dan de *drempel*, dan krijgt het kader die naam. Is de afstand groter, dan is het *iemand anders*.

![Hetzelfde gezicht twee keer: met alleen foto's krijgt het gezicht geen naam, met stills erbij wel](fotos/zo_werkt_facenet.jpg)

*Zo lees je dit plaatje: dit is twee keer hetzelfde gezicht, en je leest elke rij van links naar rechts. Bij stap 4 staat per persoon de foto die het meest op het gezicht lijkt, met de afstand ernaast. Bovenaan zijn er alleen gewone foto's. Daarvan lijkt er geen genoeg op dit gezicht: de kleinste afstand is 1,01 en dat is meer dan de drempel. Onderaan zijn er ook stills uit de film. De kleinste afstand is dan 0,65, en het gezicht krijgt de juiste naam.*


## Zo meten we hoe goed FaceNet is

De ground truth zegt per beeld wie er te zien is en waar. Daarmee kijken we FaceNet op twee manieren na. Elk experiment gebruikt allebei de manieren, met precies dezelfde code ([`gedeeld/meten.py`](gedeeld/meten.py)).

| | Methode 1: per beeld | Methode 2: per gezicht |
|---|---|---|
| **De vraag** | Ziet FaceNet deze persoon in dit beeld? | Staat de naam op het gezicht van deze persoon? |
| **Wat als goed telt** | De persoon staat in het beeld, en FaceNet noemt die naam ergens in het beeld. | Het kader met de naam overlapt minstens 30% met het gezicht van die persoon. |
| **Het nadeel** | Een naam op het verkeerde gezicht telt ook als goed. | Een kader dat iets naast het gezicht staat, kan fout rekenen. Daarom is de grens maar 30%. |
| **Waarvoor we het gebruiken** | De tabel en de tijdlijn uit de opdracht. | Het beoordelen van FaceNet. **Dit is onze keuze.** |

![Hetzelfde beeld met wat FaceNet zegt en wie er echt staat, en wat de twee methodes daarvan vinden](fotos/twee_methodes.jpg)

*Zo verschillen de twee methodes op een echt beeld. FaceNet zet twee keer de naam Der Alte. Methode 1 is tevreden, want Der Alte staat in het beeld. Methode 2 ziet dat één van die namen op het gezicht van Werner staat.*

Beide methodes geven drie getallen, allemaal van 0 tot 1:

- **Precisie:** als FaceNet een naam geeft, hoe vaak klopt die naam dan?
- **Recall:** van alle echte gezichten, hoeveel krijgen de juiste naam?
- **De score (F1):** precisie en recall samen in één cijfer. De score is alleen hoog als ze allebei hoog zijn.

![De echte aantallen achter de score, voor FaceNet afgesteld en FaceNet standaard](fotos/score_uitgelegd.png)

*Zo lees je dit plaatje: blauw is goed, grijs is gemist en oranje is fout. Afgesteld krijgen de meeste gezichten de juiste naam, en zijn er bijna geen foute namen. Standaard zijn er drie keer zoveel foute namen als goede namen. Daardoor is de precisie laag, en de score dus ook.*


## Waarom afstellen zoveel uitmaakt

Een kader krijgt alleen een naam als de afstand kleiner is dan de drempel. Goed en fout moeten dus aan verschillende kanten van de drempel liggen. Het plaatje laat zien of dat zo is.

![Vier grafieken met de afstanden van goede en foute kaders, en de drempel](fotos/drempel.png)

*Zo lees je dit plaatje: elke grafiek telt hoeveel kaders een bepaalde afstand hebben. Blauw zijn kaders waarbij de dichtstbijzijnde persoon klopt, oranje zijn kaders waarbij die niet klopt. Links van de stippellijn krijgt een kader een naam.*

- **Standaard, alleen foto's (linksboven).** Bijna alle afstanden zijn groter dan 0,80. De gewone foto's lijken te weinig op de donkere gezichten in de film, dus bijna niemand krijgt een naam.
- **Standaard, foto's + stills (rechtsboven).** De meeste afstanden zijn kleiner dan 0,80, ook als de persoon niet klopt. De oranje kaders liggen zelfs het verst naar links. De donkere en wazige stills lijken voor FaceNet op bijna alles, dus bijna iedereen krijgt een naam.
- **Afgesteld (onder).** Blauw ligt links en oranje ligt rechts van de drempel. Alleen dan kan één drempel goed en fout uit elkaar halen. Daarom gaat de score zo omhoog.


## Alle experimenten

Lees ze het best in deze volgorde. Elke naam is een link naar de volledige uitleg.

| Experiment | De vraag | Het antwoord |
|---|---|---|
| [**Basis**](basis/README.md) | Hoe goed is FaceNet zonder afstellen? | Slecht. Score 0,074 met foto's, 0,308 met foto's + stills. |
| [**Tuned**](tuned/README.md) | Hoe goed is FaceNet met de best mogelijke instellingen? | Goed. Score 0,808 met foto's, 0,874 met foto's + stills. Als de instellingen op andere filmpjes gekozen zijn: 0,766 en 0,834. |
| [**Alleen in karakter**](alleen_in_karakter/README.md) | Hoe belangrijk zijn de gewone foto's als de stills er al zijn? | Bijna niet. Zonder de gewone foto's zakt de score alleen van 0,308 naar 0,300. |
| [**Eén gemiddelde vector**](gemiddelde_vector/README.md) | Werkt één gemiddelde per persoon beter dan alle foto's los? | Bij de standaarddrempel niet. De score zakt van 0,308 naar 0,181. |
| [**Spreiding**](spreiding/README.md) | Hoe ver liggen de voorbeelden uit elkaar? Kiest FaceNet bij een onherkenbaar kader de persoon met de grootste spreiding? | Stills van verschillende personen liggen heel dicht bij elkaar (0,24). Het idee over de spreiding klopt in één van de drie sets. |
| [**Wie wordt Johann**](wie_wordt_johann/README.md) | Wie wordt als Johann herkend waar Johann er niet is? | Vooral figuranten en dingen die geen gezicht zijn (41%), en Der Alte (39%). 86% komt door één foto. |
| [**Werner met baard**](werner_baard/README.md) | Wat doen meer stills van Werner met baard? | De score van Werner gaat van 0,311 naar 0,431, bijna helemaal door één still. |
| [**Leave-one-out**](leave_one_out/README.md) | Welke voorbeeldfoto's maken het resultaat slechter? | Vooral `johann3.png`. Zonder die foto is de score 0,049 hoger. |
| [**Moving average**](moving_average/README.md) | Wat doet een filter met een ondergrens van 0,2 en een bovengrens van 0,7? | Het helpt een beetje: de score per beeld gaat van 0,636 naar 0,664. |
| [**Herkenningsdichtheid**](herkenningsdichtheid/README.md) | Hoe vaak herkent FaceNet iemand per tijdseenheid? | Een tijdlijn die laat zien waar FaceNet zeker is en waar de naam heen en weer springt. |

Welke foto's wij voor elke herkenning gebruikten, staat per experiment in `voorspellingen.csv` (kolom `foto`) en in `gebruik_per_foto.csv`. De filmpjes met de namen van FaceNet staan bij [de basis](basis/README.md#de-filmpjes), [tuned](tuned/README.md#de-filmpjes) en [alleen in karakter](alleen_in_karakter/README.md).


## Woordenlijst

| Woord | Zo ziet het eruit | Wat het betekent |
|---|---|---|
| **Beeld** (*frame*) | ![Eén beeld uit de film](fotos/woorden/beeld.jpg) | Een film is een reeks losse beelden die snel na elkaar komen, meestal 25 per seconde. |
| **Kader** | ![Hetzelfde beeld met groene kaders om de gezichten](fotos/woorden/kader.jpg) | De rechthoek die de computer om een gezicht zet. Een kader kan ook op iets staan dat geen gezicht is. |
| **Track** | ![Vijf keer hetzelfde gezicht uit opeenvolgende stukken film](fotos/woorden/track.jpg) | Hetzelfde gezicht, gevolgd over beelden na elkaar. Een track is dus een reeks kaders. |
| **Ground truth** | ![Hetzelfde beeld met de namen van de personen](fotos/woorden/ground_truth.jpg) | De lijst die met de hand gemaakt en gecontroleerd is: per beeld wie van de vier personen er te zien is en waar. Daarmee kijken we FaceNet na. Het bestand heet [`ground_truth.csv`](../labelen/output/stap_3_fouten_verbeteren/ground_truth.csv). |
| **Foto en still** | ![Een gewone foto en een still van dezelfde persoon](fotos/woorden/foto_en_still.jpg) | De voorbeelden voor FaceNet. Een *foto* is een gewone foto van de acteur, buiten de film (*out-of-character*). Een *still* is een beeld uit de film, in kostuum (*in-character*). |
| **Vector** | ![Een strook met 128 kleuren: de getallen van één gezicht](fotos/woorden/vector.png) | De rij van 128 getallen die FaceNet van een gezicht maakt. |
| **Afstand en drempel** | ![Een lijn: links van de drempel krijgt een kader een naam, rechts niet](fotos/woorden/drempel.png) | De *afstand* zegt hoe verschillend twee vectoren zijn: klein is lijkt op elkaar. De *drempel* is de grens: is de afstand kleiner, dan krijgt het kader een naam. De afstand die de opdracht voorschrijft, heet de *genormaliseerde Euclidische afstand*. |
| **Score (F1), precisie, recall** | | Zie [Zo meten we hoe goed FaceNet is](#zo-meten-we-hoe-goed-facenet-is). |


## Installeren op Mac en Windows

Dit hoef je maar één keer te doen.

**1. Open een terminal in de map `experimenten`.** Een terminal is het venster waarin je opdrachten typt.

- **Mac:** open het programma Terminal, typ `cd ` (met een spatie erachter), sleep de map `experimenten` naar het venster en druk op Enter.
- **Windows:** open de map `experimenten` in de Verkenner, klik bovenin op de balk met de naam van de map, typ `cmd` en druk op Enter.

**2. Installeer Python 3.12** vanaf <https://www.python.org/downloads/>. Zet op Windows in het eerste scherm een vinkje bij *Add python.exe to PATH*.

**3. Installeer de pakketten:** deepface (FaceNet), TensorFlow, pandas, NumPy, OpenCV en matplotlib.

Op een Mac:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Op Windows:

```bat
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

**4. Installeer ffmpeg.** Dat programma is nodig voor de filmpjes. Open daarna een nieuw terminalvenster.

Op een Mac:

```bash
brew install ffmpeg
```

Op Windows:

```bat
winget install Gyan.FFmpeg
```

De eerste keer haalt deepface de gewichten van FaceNet op, ongeveer 90 MB per model. Op Windows hebben we de programma's niet zelf uitgeprobeerd.


## Zo draai je de experimenten

Alle uitkomsten staan al in de mappen. Opnieuw draaien hoeft alleen als je iets verandert. Doe het vanuit de map `experimenten`, in deze volgorde.

Op een Mac typ je `.venv/bin/python`, gevolgd door het script uit de tabel:

```bash
.venv/bin/python basis/draai_alles.py
```

Op Windows typ je `.venv\Scripts\python`, gevolgd door het script, met `\` in plaats van `/`:

```bat
.venv\Scripts\python basis\draai_alles.py
```

| Experiment | Script | Hoe lang het duurt |
|---|---|---|
| Basis | `basis/draai_alles.py` | de eerste keer een kwartier |
| Alleen in karakter | `alleen_in_karakter/draai.py` | enkele minuten |
| Eén gemiddelde vector | `gemiddelde_vector/draai.py` | een halve minuut |
| Spreiding | `spreiding/draai.py` | een halve minuut |
| Wie wordt Johann | `wie_wordt_johann/draai.py` | een halve minuut |
| Werner met baard | `werner_baard/draai.py` | een halve minuut |
| Leave-one-out | `leave_one_out/draai.py` | een halve minuut |
| Moving average | `moving_average/draai.py` | een halve minuut |
| Herkenningsdichtheid | `herkenningsdichtheid/draai.py` | een halve minuut |
| Tuned | `tuned/draai_alles.py` | de eerste keer een uur |
| Het overzicht bovenaan | `maak_overzicht.py` | een paar seconden |
| De uitlegplaatjes | `fotos/maak_fotos.py` | een halve minuut |

De vectoren van alle gezichten worden één keer uitgerekend en bewaard in de map `tussenbestanden/`. Die map gaat niet mee naar GitHub.


## Wat er in deze map staat

| Map of bestand | Wat het is |
|---|---|
| `basis/`, `tuned/`, `alleen_in_karakter/`, `gemiddelde_vector/`, `spreiding/`, `wie_wordt_johann/`, `werner_baard/`, `leave_one_out/`, `moving_average/`, `herkenningsdichtheid/` | De experimenten, elk met de code, een map `resultaten` en een eigen uitleg. |
| `gedeeld/` | De code die alle experimenten gebruiken: waar de bestanden staan, FaceNet aanroepen, de voorbeelden, de twee meetmethodes en het filmpje. |
| `fotos/` | De uitlegplaatjes in deze README's, en `maak_fotos.py` die ze maakt. |
| `maak_overzicht.py`, `overzicht.csv`, `overzicht.png` | Het overzicht bovenaan deze uitleg. |
| `requirements.txt` | De pakketten met de versies waarmee gewerkt is. |
| `LIJSTJE.md` | De checklist van wat er gedaan is. |
