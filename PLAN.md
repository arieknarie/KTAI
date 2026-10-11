# Plan – FaceNet onder stress: een casestudy op basis van *Das Boot*

Werkplan voor het onderzoek en de paper (Key Topics in Artificial Intelligence,
Open Universiteit). Branch: `facenet-stress-tests`.

---

## 1. Doel en onderzoeksvragen

**Hoofdvraag:** Hoe beïnvloeden lage resolutie, veranderende gezichten en slechte
belichting in *Das Boot* de prestaties van het FaceNet-herkenningsalgoritme?

| # | Deelvraag | Stresstest | Mitigatie |
|---|---|---|---|
| 1 | Hoe beïnvloedt lage beeldresolutie de nauwkeurigheid, en helpt pixel-interpolatie? | Lage resolutie | Interpolatie (bicubic/Lanczos) i.p.v. nearest neighbour |
| 2 | In hoeverre verlagen door stress en vermoeidheid veranderde gezichten de herkenning, en helpen extra referentiefoto's? | Veranderende gezichten | Extra in-character referentiefoto's |
| 3 | Hoe beïnvloedt de slechte belichting in de onderzeeër de feature-extractie, en verbetert CLAHE het lokale contrast en de nauwkeurigheid? | Duisternis / rood alarmlicht | CLAHE-voorbewerking |

## 2. Data (in deze repository)

| Map | Inhoud | Rol |
|---|---|---|
| `pictures/personal/<naam>/` | 23 foto's van de vier acteurs **buiten** hun rol | Referentiegalerij (normale uitgangssituatie) |
| `pictures/inCharacter/<naam>/` | 35 filmstills, waarvan 2 exacte dubbelingen (dus 33 unieke) | Testscènes; deels ook extra referenties (uitgebreide galerij, gebruikt in alle drie de stresstests) |
| `movies/` | 3 filmclips (± 10 minuten in totaal) | Beschrijving van echt filmmateriaal (gezichtsgrootte, helderheid) |
| `papers/` | Gebruikte literatuur | – |

De vier personen: **Der Alte**, **Fritz Grade**, **Johann** en **Werner**.
Wie er op een still staat, volgt uit de bestandsnaam
(`alte_and_werner2.png` → Der Alte en Werner).

## 3. Methode

### 3.1 Herkenningspipeline

1. **Detectie en uitlijning:** RetinaFace vindt alle gezichten in het beeld en
   lijnt ze uit (ogen horizontaal).
2. **Embedding:** FaceNet zet elk gezicht (160 × 160 px) om in een
   128-dimensionale vector met lengte 1.
3. **Vergelijking:** de Euclidische afstand tot alle referentiegezichten wordt
   berekend en de dichtstbijzijnde referentie bepaalt de naam.
4. **Open set:** is die afstand gelijk aan of groter dan de drempel (0,80, de standaardwaarde
   van deepface voor FaceNet), dan wordt het gezicht **"onbekend"**. Dat is
   nodig, omdat er op de stills ook figuranten staan.

### 3.2 Evaluatie per scène, gescoord per gezicht

Het systeem krijgt steeds een **complete still**, met figuranten,
achtergrondgezichten, kleine en donkere gezichten. De stills worden vooraf niet
opgeschoond: precies die moeilijkheden worden onderzocht. Wel negeert de
detector gezichten met een detectiescore onder 0,90. Een gezicht dat in de
originele still zo wegvalt, krijgt geen label en telt niet mee.

Om te kunnen scoren heeft elk gevonden gezicht een **label**: een van de
vier personen, of `other` (figurant). Het systeem ziet die labels niet; ze zijn
alleen de grondwaarheid. Gedetecteerde gezichten worden via de overlap van de
kaders aan de labels gekoppeld, ook in gedegradeerde beelden.

| Gezicht | Uitkomst | Betekenis |
|---|---|---|
| Een van de vier | goed | juiste persoon herkend |
| | fout | verward met een van de andere drie |
| | afgewezen | wel gevonden, maar "onbekend" |
| | gemist | de detector vindt het gezicht niet |
| Figurant | terecht afgewezen | "onbekend" |
| | onterecht benoemd | krijgt een van de vier namen |

Hoofdmaat: **herkend** = aandeel van de gezichten van de vier dat goed is.
Daarnaast: gemist, figuranten onterecht benoemd, precisie en `closest_correct`
(de dichtstbijzijnde referentie klopt, los van de drempel).

**Labelen:** automatisch alleen als de bestandsnaam één persoon noemt en er precies
één gezicht is gevonden. De rest is gelabeld door visuele inspectie
(`label_source = visual`) en via de labelquiz (`label_quiz.py`, `label_source = quiz`).
"Weet niet" in de quiz betekent dat het gezicht niet wordt gescoord.

### 3.3 Referentiegalerij

- **Basis:** de gezichten van de acteurs op hun persoonlijke foto's (gelabeld).
- **Uitgebreid:** basis + de gelabelde in-character gezichten. Stresstest 2 vergelijkt deze galerij met de basisgalerij; stresstest 1 en 3 gebruiken altijd de uitgebreide galerij (bij CLAHE krijgen ook de referentiefoto's die bewerking).
- **Leave-one-out:** een still wordt nooit vergeleken met referenties uit
  dezelfde still. Dubbele stills (exact hetzelfde bestand, of dezelfde still op
  een ander formaat, herkend via een perceptuele hash van de hele foto) worden
  overgeslagen.
- **Zelfde bewerking:** referenties worden op dezelfde manier uit hun foto
  geknipt als de gezichten in een still (hele foto bewerken, bijv. CLAHE, dan
  detecteren en via de kaders aan de labels koppelen).

### 3.4 De drie stresstests

De degradatie wordt op **het hele frame** toegepast, vóór de detectie. Zo
lijden detectie, uitlijning én feature-extractie eronder, zoals beschreven door
Cheng & Zhu.

| Stresstest | Degradatie (niveaus) | Mitigatie |
|---|---|---|
| 1 – Resolutie | Still verkleind tot 1/2, 1/4, 1/8 en 1/16 van de originele grootte | Terugschalen naar de originele grootte met nearest neighbour (geen interpolatie), bicubic of Lanczos |
| 2 – Uiterlijk | Originele stills | Galerij met alleen persoonlijke foto's vs. galerij met extra in-character referenties |
| 3 – Belichting | "Duisternis" en "rood alarmlicht", ernst 0 / 0,25 / 0,5 / 0,75 / 0,9 | Zonder vs. met CLAHE (op het L-kanaal van LAB) |

Duisternis wordt gesimuleerd met minder belichting, een gamma > 1 (schaduwen
verdwijnen eerst) en sensorruis. Bij rood alarmlicht gaat bovendien de
kleurinformatie verloren en blijft alleen rood over.

### 3.5 Tussenresultaten (zichtbaar gemaakt)

Elke stap wordt als afbeelding opgeslagen in `experiments/results/intermediate/`:

- `detections/` – alle stills en foto's met genummerde kaders per gevonden gezicht.
- `label_quiz.html` – de labelquiz.
- `gallery_overview*.jpg` – alle referentiegezichten zoals FaceNet ze ziet,
  zonder en met CLAHE.
- `stress_test_*/` – per still een overzichtsvel met alle condities naast
  elkaar. Elk gezicht krijgt een kader met de voorspelde naam en de afstand:
  groen = juiste persoon, rood = foute naam, grijs = onbekend, oranje = gemist
  door de detector.

Tijdens het draaien worden de resultaten per conditie ook direct in de
terminal getoond.

## 4. Van resultaat naar paper

| Paper-sectie | Wat er komt te staan | Bron |
|---|---|---|
| Methods | Pipeline (3.1), evaluatie (3.2), galerij (3.3), stresstests (3.4); een pipeline-figuur | Dit plan, `README.md` (Werking, Stresstests, Evaluatie) |
| Datasets | Aantallen stills/gezichten per persoon, gezichtsgrootte en helderheid van foto's vs. stills vs. filmclips | `describe_dataset.py` → `dataset_summary.csv`, `dataset_per_identity.csv`, `dataset_faces.pdf` |
| Implementation details | deepface, RetinaFace, FaceNet-128, drempel 0,80, CLAHE-parameters, niveaus | `experiments/config.py` |
| Results | Eén figuur per stresstest plus een tabel | `results/figures/stress_test_*.pdf`, `results/summary*.csv` |
| Discussion | Beperkingen (zie §7) en voorbeelden uit de tussenresultaten | `results/intermediate/` |

## 5. Werkwijze en status

| Stap | Wat | Status |
|---|---|---|
| 1 | Repository gekloond, branch `facenet-stress-tests` | ✅ |
| 2 | Paper-skelet (`paper/main.tex`) + `references.bib` met opgezochte bronnen (`cheng2024` nog niet bevestigd, zie stap 8 en §7) | ✅ (ICML-stijlbestanden moet het team zelf toevoegen) |
| 3 | Pipeline: detectie, embeddings, degradaties, CLAHE, tussenresultaten | ✅ |
| 4 | Evaluatie per scène, gescoord per gezicht (figuranten horen erbij) | ✅ proefrun op 3 stills geslaagd |
| 5 | Gezichten labelen: 28 automatisch, 38 visueel, 68 via de quiz, 3 zonder label | ✅ |
| 6 | Codereview (5 reviewers + controle), gevonden fouten hersteld | ✅ |
| 6a | Volledige run (± 20 min), tussenresultaten gecontroleerd, [RESULTATEN.md](RESULTATEN.md) | ✅ |
| 6b | Team: labels met `label_source = visual` steekproefsgewijs controleren | ⏳ team |
| 7 | Team: Methods, Results en Discussion schrijven met de figuren en tabellen | ⏳ team |
| 8 | Team: placeholders vervangen (abstract, figuren, studentnummer), bron `cheng2024` controleren | ⏳ team |

## 6. Bevindingen (volledige run, 33 stills, 52 gezichten)

Uitgebreid in [RESULTATEN.md](RESULTATEN.md). Kort:

- **De drempel is de bottleneck bij veranderde gezichten:** met alleen
  acteursfoto's wijst de dichtstbijzijnde referentie in 79% van de gevallen de
  juiste persoon aan, maar wordt maar 15% herkend: de afstand ligt meestal boven
  0,80 (mediaan 0,97). Met filmgezichten erbij wordt 62% herkend (stresstest 2).
- **Zekere foute namen:** met filmgezichten krijgen 45 van de 56 figuranten een
  naam. 25 daarvan via één onscherp, donker achtergrondgezicht van Fritz
  (`alte_and_fritz2.png`, f1) en 10 via een donker gezicht van Johann. Bij zware
  degradatie (1/8–1/16, veel donker of rood licht) krijgen gezichten massaal die
  twee namen, met een heel kleine afstand. Een extra referentiefoto van lage
  kwaliteit kan de herkenning dus **schaden**. Dat is een discussiepunt voor
  stresstest 2 en staat op gespannen voet met Luévano et al.: volgens `main.tex`
  geeft juist een diverse database met referentiebeelden van lage kwaliteit,
  samen met eenvoudige interpolatie, de stabielste herkenning (die bewering moet
  nog in het artikel worden nagelezen, zie §7). De referentie blijft bewust in de
  galerij: weglaten zou de resultaten mooier maken dan ze zijn.
- **Resolutie:** herkenning daalt van 62% naar ± 30% bij gezichten van ± 40 px.
  Interpolatie houdt kleine gezichten vindbaar (bij 1/16 mist nearest neighbour
  96%, bicubic 25%), maar herkent ze nauwelijks beter.
- **Belichting:** herkenning daalt met de helderheid; bij gelijke helderheid is
  rood licht niet slechter dan duisternis. CLAHE verandert de herkenning weinig,
  maar voorkomt een groot deel van de foute namen (bijv. figuranten met een naam
  bij donker 0,5: 40/42 → 7/46).

## 7. Beperkingen en risico's

- **Kleine dataset:** 33 unieke stills met 52 gezichten van de vier, dus de
  percentages hebben een grote onzekerheid. Noem altijd *n*. (Het rechtergezicht
  in `derAlte1.jpeg` is een recent portret van de acteur en telt niet mee.)
- **Labels deels door visuele inspectie:** de grondwaarheid is zo goed als de
  labels. Labels met `label_source = visual` moet het team controleren.
- **Gesimuleerde degradaties** benaderen het echte filmmateriaal, maar zijn het
  niet. De statistieken van de filmclips (stap 4 in de README,
  `describe_dataset.py`) laten zien hoe klein en donker de echte gezichten zijn.
- **Drempel niet getuned:** 0,80 is de standaardwaarde van deepface. Afstemmen op
  deze data zou zonder aparte validatieset tot overfitting leiden.
- **Leeftijdsverschil:** de persoonlijke foto's zijn deels jaren na de film
  gemaakt. Dat is ook een "veranderend gezicht".
- **Literatuur controleren:**
  - `cheng2024`: geen review uit 2024 gevonden. Tijdelijk staat Cheng, Zhu & Gong
    (ACCV 2018) in de bib.
  - Luévano et al. (2026): de abstract bevestigt dat eenvoudige interpolatie beter
    werkt dan zware super-resolutie, maar de bewering over "a diverse database of
    low-quality reference images" moet in de paper zelf worden nagelezen.
  - Abdalah & Alkazaz: nagaan of "cross-appearance samples are strictly needed"
    letterlijk zo in het artikel staat.
