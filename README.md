# KTAI – FaceNet en Das Boot

Foto's, filmfragmenten, code en paper voor het vak Key Topics in Artificial
Intelligence van de Open Universiteit.

We onderzoeken hoe goed FaceNet vier bemanningsleden uit de film *Das Boot*
(1981) herkent, en wat er met die herkenning gebeurt bij lage resolutie, bij
gezichten die tijdens de film veranderen (baard, vuil, vermoeidheid) en bij
het donkere, rode licht in de onderzeeër.

Onderzoeksvraag: hoe beïnvloeden lage resolutie, veranderende gezichten en
slechte belichting in *Das Boot* de prestaties van het
FaceNet-herkenningsalgoritme?


## Mappen

```
KTAI/
├── README.md
├── PLAN.md                   onderzoeksplan en status
├── RESULTATEN.md             resultaten met grafieken en voorbeelden
├── pictures/
│   ├── personal/<naam>/      23 foto's van de acteurs buiten hun rol
│   └── inCharacter/<naam>/   35 stills uit de film (2 daarvan dubbel)
├── movies/                   3 filmfragmenten (samen ongeveer 10 minuten)
├── papers/                   gebruikte literatuur
├── paper/                    de paper in LaTeX (ICML-opmaak)
└── experiments/              code, labels en resultaten
    ├── *.py
    ├── data/labels.csv
    └── results/
```

De vier personen:

| Naam in de code | Personage | Rol |
|---|---|---|
| `DerAlte` | Der Alte | kapitein |
| `FritzGrade` | Fritz Grade | hoofdwerktuigkundige |
| `Johann` | Johann | machinist |
| `Werner` | Werner | oorlogscorrespondent |

De map onder `pictures/` geeft aan bij wie een foto hoort. De bestandsnaam van
een still geeft aan wie erop staat, bijvoorbeeld `alte_and_werner2.png` voor
Der Alte en Werner.


## Werking

De herkenning gaat in vier stappen.

1. RetinaFace zoekt alle gezichten in het beeld, zet er een kader omheen en
   draait elk gezicht recht (ogen horizontaal).
2. FaceNet zet elk gezicht (160 × 160 pixels) om in een embedding: een vector
   van 128 getallen. FaceNet is vooraf getraind op een grote verzameling
   gezichten, zodat foto's van dezelfde persoon vectoren opleveren die dicht bij
   elkaar liggen. Wij trainen zelf niets.
3. De vector wordt vergeleken met die van de referentiefoto's (de galerij). Het
   gezicht krijgt de naam van de referentie met de kleinste Euclidische afstand.
4. Is die kleinste afstand 0,80 of groter, dan wordt het gezicht "onbekend".
   Dat is nodig omdat er op de stills ook figuranten staan.

De afstand ligt tussen 0 (identiek) en 2. De drempel van 0,80 is de
standaardwaarde van deepface voor dit FaceNet-model. We hebben hem niet zelf
afgesteld, omdat dat met zo weinig beelden de resultaten zou flatteren.

Voorbeeld met `alte_and_fritz.png`, waarop Der Alte, Fritz en een figurant
staan, herkend met de galerij van foto's van de acteurs plus gezichten uit de
film:

| Gezicht | Uitkomst systeem | Afstand | Beoordeling |
|---|---|---|---|
| Der Alte | Der Alte | 0,76 | goed |
| Fritz | onbekend | 0,83 | afgewezen, net boven de drempel |
| figurant | onbekend | 0,93 | terecht afgewezen |


## Stresstests

Elke stresstest hoort bij een deelvraag van de paper. De bewerking wordt steeds
op de hele still toegepast, vóór de detectie. Het systeem moet de gezichten dus
ook in het bewerkte beeld zelf vinden. Per test vergelijken we een situatie
zonder en met een mitigatie.

**1. Lage resolutie.** De still wordt verkleind tot 1/2, 1/4, 1/8 en 1/16 van
de oorspronkelijke breedte en hoogte en daarna weer vergroot tot het
oorspronkelijke formaat. Zo bootsen we gezichten na die ver van de camera
staan. Het vergroten gebeurt op drie manieren: nearest neighbour (pixels
worden herhaald, geen interpolatie; dit is de basislijn), bicubic en Lanczos
(interpolatie).

**2. Veranderende gezichten.** De originele stills worden herkend met twee
galerijen: één met alleen de foto's van de acteurs buiten hun rol, en één
waarin ook gezichten uit de film zelf zitten (met baard, vuil en pet).

**3. Slechte belichting.** De still wordt donkerder gemaakt in vier stappen
(ernst 0,25, 0,5, 0,75 en 0,9): minder licht, een gamma groter dan 1 zodat
schaduwen het eerst verdwijnen, en beeldruis. In de variant rood alarmlicht
wordt het beeld daarnaast gemengd met een rood gekleurde grijswaardenversie,
naar verhouding van de ernst (bij 0,25 voor een kwart, bij 0,9 voor 90%), zodat
de kleur steeds meer verdwijnt en vooral rood overblijft. Als mitigatie gebruiken we CLAHE
(Contrast Limited Adaptive Histogram Equalization), dat het contrast per klein
deel van het beeld verhoogt. CLAHE wordt toegepast op het helderheidskanaal,
op de hele still en op de hele referentiefoto's, zodat beide precies dezelfde
bewerking krijgen.

Bij dezelfde ernst is rood alarmlicht donkerder dan gewone duisternis, omdat
puur rood licht minder helder is. Daarom wordt per conditie ook de gemiddelde
helderheid van de stills bijgehouden (`frame_brightness`), zodat beide
varianten bij gelijke helderheid vergeleken kunnen worden.


## Evaluatie

Het systeem krijgt steeds de complete still, inclusief figuranten,
achtergrondgezichten en donkere hoeken. Het moet zelf de juiste gezichten
vinden en figuranten afwijzen.

### Labels

Om de uitkomsten te kunnen beoordelen heeft elk gezicht uit de foto's en
stills een label in [`experiments/data/labels.csv`](experiments/data/labels.csv):
een van de vier namen, of `other` voor een figurant. Bij het herkennen van een
still gebruikt het systeem de labels van die still niet; die dienen alleen om
achteraf te scoren. Wel bepalen de labels welke gezichten als referentie in de
galerij komen en onder welke naam.

| `label_source` | Herkomst | Aantal |
|---|---|---|
| `filename` | automatisch: de bestandsnaam noemt één persoon en er is precies één gezicht gevonden | 28 |
| `visual` | visueel gecontroleerd op de detectiebeelden | 38 |
| `quiz` | ingevuld in de labelquiz | 68 |

Drie gezichten uit de stills hebben geen label en tellen niet mee: twee die in
de quiz als "weet niet" zijn gemarkeerd, en het rechtergezicht in
`derAlte1.jpeg`. Die still zet een beeld uit de film naast een recent portret
van de acteur; dat portret is geen gezicht uit de film. Er blijven 52 gezichten
van de vier over, verdeeld over 33 stills. De 1700 gezichten uit de
filmfragmenten (`source` is `movie`, toegevoegd met `prepare_faces.py --movies`)
hebben ook geen label; ze worden alleen gebruikt voor de statistieken van
stap 4.

Het grootste gezicht in een foto wordt niet automatisch als de genoemde persoon
gelabeld. In `johann7.jpg` is het grootste gezicht namelijk een figurant op de
voorgrond; Johann staat kleiner in het midden.

### Leave-one-out

Een still wordt nooit vergeleken met referentiegezichten uit dezelfde still,
anders zou een gezicht met zichzelf worden vergeleken. Twee stills stonden
dubbel in de map (in verschillende personenmappen); de tweede kopie wordt
overgeslagen. Ook een still die op een ander formaat nog eens is opgeslagen,
zou worden overgeslagen: dat wordt gecontroleerd met een perceptuele hash van
de hele foto. In de huidige data komt dat niet voor.

De referentiegezichten worden op dezelfde manier uit hun foto geknipt als de
gezichten in een still: de hele foto wordt bewerkt (bijvoorbeeld met CLAHE),
de gezichten worden opnieuw gedetecteerd en via de overlap van de kaders aan
de labels gekoppeld.

### Scoring

Na de herkenning wordt elk gevonden gezicht gekoppeld aan een gelabeld gezicht
op basis van de overlap van de kaders (intersection over union van minstens
0,3). Elk gezicht krijgt dan één uitkomst:

| Label | Uitkomst | Betekenis |
|---|---|---|
| een van de vier | `correct` | juiste naam |
| | `wrong` | verward met een van de andere drie |
| | `rejected` | gevonden, maar "onbekend" genoemd |
| | `missed` | niet gevonden door de detector |
| figurant | `rejected` | terecht "onbekend" genoemd |
| | `false_identity` | ten onrechte een van de vier namen gegeven |

De belangrijkste maat is `recognised`: het aandeel van de gezichten van de vier
dat de juiste naam kreeg.


## Resultaten

De volledige resultaten, met grafieken en voorbeelden, staan in
[RESULTATEN.md](RESULTATEN.md). De belangrijkste uitkomsten op de 52 gezichten
van de vier in 33 stills:

| Situatie | Herkend | Figuranten met een foute naam |
|---|---|---|
| originele stills, alleen acteursfoto's als referentie | 15% | 0 van 56 |
| originele stills, acteursfoto's + filmgezichten | 62% | 45 van 56 |
| still verkleind tot 1/4 (gezichten ± 40 px), bicubic | 29% | 47 van 53 |
| duisternis, ernst 0,75 | 19% | 31 van 31 |
| duisternis, ernst 0,75, met CLAHE | 23% | 3 van 35 |

- Veranderende gezichten hebben het grootste effect. Met alleen de normale
  acteursfoto's wijst het systeem meestal wel de juiste persoon aan, maar is de
  afstand te groot. Referenties uit de film helpen, maar een paar donkere of
  onscherpe referenties zorgen voor veel foute namen.
- Lage resolutie en weinig licht verlagen de herkenning sterk. Interpolatie
  houdt kleine gezichten vindbaar, maar verbetert de herkenning nauwelijks.
- CLAHE verandert het aantal herkende gezichten weinig, maar voorkomt een groot
  deel van de foute namen.


## Installatie

Nodig: Python 3.12 (de vastgezette numpy-versie vereist minimaal 3.12; nieuwere
versies zijn niet getest),
ongeveer 2 GB schijfruimte voor de pakketten en 200 MB voor de modelgewichten.
De gewichten worden bij de eerste run automatisch gedownload naar
`~/.deepface/`.

```bash
cd experiments
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```


## Gebruik

Alle commando's worden uitgevoerd vanuit `experiments/`, met de virtuele
omgeving actief.

| Stap | Commando | Wat het doet | Duur |
|---|---|---|---|
| 1 | `python prepare_faces.py` | gezichten zoeken in alle foto's en stills, `data/labels.csv` aanmaken | ± 2 min |
| 2 | `python label_quiz.py` | labelquiz in de browser voor gezichten zonder label | – |
| 2b | `python label_quiz.py --apply antwoorden.txt` | quiz-antwoorden in `labels.csv` zetten | seconden |
| 3 | `python run_stress_tests.py` | alle stresstests draaien, resultaten naar `results/` | ± 20 min |
| 4 | `python describe_dataset.py` | statistieken over gezichtsgrootte en helderheid | seconden |

Opmerkingen:

- `labels.csv` staat al in de repository, inclusief alle labels. Na het
  installeren kan direct stap 3 worden gedraaid. Stap 1 en 2 zijn alleen nodig
  als er foto's bijkomen of als je de labelquiz wilt gebruiken. Bij een nieuwe
  run van stap 1 blijven bestaande labels behouden: ze worden via de overlap
  van de kaders aan dezelfde gezichten gekoppeld.
- De versies in `requirements.txt` liggen vast, zodat de detector op elke
  computer dezelfde kaders vindt.
- `prepare_faces.py --movies` zoekt ook gezichten in de filmfragmenten (één beeld
  per seconde). Die worden alleen gebruikt voor de statistieken van stap 4.
- `run_stress_tests.py --max-stills 3` doet een korte proefrun op 3 stills (± 4 min).
  Let op: de proefrun schrijft naar dezelfde bestanden als de volledige run en
  overschrijft dus de CSV-bestanden en grafieken in `results/`. Zet ze daarna
  terug met `git checkout -- results/` of draai de volledige run opnieuw.
- `python plots.py` tekent de grafieken opnieuw uit de CSV-bestanden, zonder het
  experiment opnieuw te draaien.
- Alle instellingen (drempel, schalen, ernstniveaus, CLAHE-parameters) staan in
  [`experiments/config.py`](experiments/config.py).


## Code

Alle code staat in [`experiments/`](experiments/). Het commentaar in de code
is Engelstalig.

`config.py` bevat alle instellingen: mappen, de vier namen, het model (FaceNet,
128 dimensies), de detector (RetinaFace), de drempel (0,80) en de niveaus van
de stresstests.

`face_model.py` is een dunne laag rond de bibliotheek deepface. `detect_faces`
zoekt alle gezichten in een beeld en geeft per gezicht de uitsnede, het kader
(x, y, breedte, hoogte) en de detectiescore; detecties met een score onder 0,90
worden genegeerd. `embed` berekent de embedding van een gezicht van 160 × 160
pixels en normaliseert die naar lengte 1.

`image_ops.py` bevat de beeldbewerkingen. `to_model_input` maakt van een
uitsnede een vierkant van 160 × 160 pixels; er komt een zwarte rand omheen in
plaats van uitrekken. `reduce_resolution` (stresstest 1) verkleint en vergroot
een still. `simulate_low_light` (stresstest 3) maakt een still donker of rood.
`apply_clahe` past CLAHE toe op het L-kanaal in LAB-kleurruimte.
`difference_hash` berekent de perceptuele hash voor het opsporen van foto's
die dubbel zijn opgeslagen. `match_boxes` koppelt twee lijsten kaders op basis
van hun overlap.

`labels.py` leest en schrijft `data/labels.csv` en controleert of er alleen
geldige namen in staan. Het haalt uit een bestandsnaam welke personen er
genoemd worden, en zorgt dat bestaande labels behouden blijven als stap 1
opnieuw draait. Die labels worden binnen dezelfde foto via de overlap van de
kaders aan de nieuwe detecties gekoppeld, niet via het volgnummer, zodat een
label nooit naar een ander gezicht kan verspringen.

`prepare_faces.py` (stap 1) loopt alle foto's en stills langs, slaat dubbele
foto's over, zoekt de gezichten, bewaart elke uitsnede in `data/faces/` en
schrijft per gezicht een regel in `labels.csv`. Waar dat eenduidig kan, wordt
het label automatisch ingevuld. Daarnaast worden detectiebeelden gemaakt: elke
foto met genummerde kaders (`f0`, `f1`, ...), zodat te zien is welk nummer bij
welk gezicht hoort.

`label_quiz.py` (stap 2) maakt een webpagina waarop per still de genummerde
gezichten staan, met per gezicht de keuze Der Alte, Fritz, Johann, Werner,
Figurant of Weet niet. Bovenaan staat een balk met referentiefoto's van de
vier. De antwoorden worden met `--apply` in `labels.csv` gezet.

`run_stress_tests.py` (stap 3) voert het experiment uit:

1. bouwt twee galerijen: alleen foto's van de acteurs, en foto's van de acteurs
   plus gezichten uit de film (met een CLAHE-versie voor stresstest 3);
2. bewerkt per still en per conditie het beeld, zoekt de gezichten, berekent de
   embeddings en zoekt per gezicht de dichtstbijzijnde referentie, waarbij
   referenties uit dezelfde still worden overgeslagen;
3. koppelt de gevonden gezichten aan de labels en bepaalt per gezicht de
   uitkomst;
4. schrijft de uitkomsten en samenvattingen naar `results/`, maakt de grafieken
   en de overzichtsvellen, en print per conditie de score.

Beelden die in meerdere condities identiek zijn, zoals de onbewerkte still,
worden maar één keer geanalyseerd.

`intermediate.py` maakt de tussenresultaten als afbeeldingen: per still een
overzichtsvel met alle condities naast elkaar en op elk gezicht een gekleurd
kader met de gegeven naam en de afstand.

| Kleur | Betekenis |
|---|---|
| groen | juiste naam |
| rood | verkeerde naam (verwisseld, of een figurant die een naam kreeg) |
| grijs | onbekend |
| oranje | een van de vier, maar niet gevonden door de detector |

`plots.py` maakt de grafieken voor de paper, als PDF en PNG, in de afmetingen
van het ICML-formaat en met kleuren die ook bij kleurenblindheid te
onderscheiden zijn. Het script kan ook los worden gedraaid om de grafieken
opnieuw te tekenen uit de CSV-bestanden.

`describe_dataset.py` (stap 4) berekent per bron (foto's, stills en eventueel
filmbeelden) hoeveel gezichten er zijn en hoe groot en helder ze zijn. Dit is
bedoeld voor de sectie Datasets van de paper.


## Uitvoer

Alle uitvoer staat in [`experiments/results/`](experiments/results/).

| Bestand | Inhoud |
|---|---|
| `summary.csv` | scores per stresstest, mitigatie en niveau |
| `summary_by_identity.csv` | dezelfde scores per persoon; `precision` is hier het aandeel juiste gevallen van alle keren dat die naam werd gegeven |
| `per_face.csv` | elk gezicht in elke conditie: gegeven naam, afstand, dichtstbijzijnde referentie en uitkomst |
| `figures/` | grafieken voor de paper: één per stresstest, de verdeling van de afstanden (`distances`), herkenning tegen helderheid (`lighting_brightness`) en, uit stap 4, gezichtsgrootte en helderheid per bron (`dataset_faces`) |
| `examples/` | met de hand gekozen kopieën van tussenresultaten die in RESULTATEN.md staan: vier overzichtsvellen, twee detectiebeelden (een still en een filmbeeld) en twee referentiegezichten; de scripts werken deze map niet bij |
| `dataset_summary.csv`, `dataset_per_identity.csv` | statistieken van stap 4 |

Kolommen in `summary.csv`:

| Kolom | Betekenis |
|---|---|
| `experiment` | `appearance` (stresstest 2), `resolution` (1) of `lighting` (3) |
| `variant` | bewerking van de still: `clean`, `downscaled`, `dark` of `red_alarm` |
| `mitigation` | galerij, vergrotingsmethode, of wel/geen CLAHE |
| `level` | schaal (0,5 is half zo groot) of ernst (0 tot 0,9) |
| `named_faces` | aantal meegetelde gezichten van de vier |
| `recognised` | aandeel van die gezichten met de juiste naam |
| `wrong`, `rejected`, `missed` | aandeel verwisseld, "onbekend" genoemd of niet gevonden |
| `closest_correct` | aandeel waarbij de dichtstbijzijnde referentie de juiste persoon was, zonder rekening te houden met de drempel |
| `extras_found` | aantal gevonden figuranten |
| `extras_named` | aandeel figuranten dat ten onrechte een naam kreeg |
| `precision` | aandeel juiste namen van alle namen die het systeem gaf |
| `frame_brightness` | gemiddelde helderheid van de stills zoals het systeem ze zag (0 tot 255) |

Als `closest_correct` hoog is en `recognised` laag, wijst het systeem wel de
juiste persoon aan maar ligt de afstand boven de drempel van 0,80.

Alle tussenresultaten (detectiebeelden en overzichtsvellen, enkele honderden
afbeeldingen) komen in `experiments/results/intermediate/`. Die map staat niet
in git omdat de scripts hem opnieuw aanmaken; een paar voorbeelden staan in
`results/examples/`.


## Beperkingen

- De dataset is klein: 33 unieke stills met 52 gezichten van de vier. Eén
  gezicht verschuift een percentage al met ongeveer 2 procentpunt, dus het
  aantal moet steeds vermeld worden.
- De labels zijn deels visueel en via de quiz ingevuld. Fouten in de labels
  werken door in de scores.
- Verkleining, duisternis en rood licht zijn gesimuleerd en dus een benadering
  van echte filmbeelden.
- De drempel van 0,80 is niet afgesteld op deze data. Zonder aparte testset
  zou afstellen de resultaten te gunstig maken.
- Een deel van de foto's van de acteurs is jaren na de film gemaakt, wat ook
  een verschil in uiterlijk geeft.
- Eén onscherpe, donkere referentie van Fritz trekt bij zware degradatie veel
  gezichten naar zich toe (zie Resultaten). Deze referentie is niet verwijderd,
  omdat dat de resultaten mooier zou maken dan ze zijn.


## Bronnen en software

- deepface, voor detectie en herkenning: <https://github.com/serengil/deepface>
- F. Schroff, D. Kalenichenko en J. Philbin, *FaceNet: A Unified Embedding for
  Face Recognition and Clustering*, CVPR 2015. Het gebruikte 128-dimensionale
  model is de opensourceversie die deepface meelevert.
- RetinaFace als gezichtsdetector, via deepface.
- K. Zuiderveld, *Contrast Limited Adaptive Histogram Equalization*, Graphics
  Gems IV, 1994. Implementatie uit OpenCV.
- Overige literatuur: [`paper/references.bib`](paper/references.bib) en de map
  `papers/`.
