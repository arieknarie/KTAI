# experiments

Code, labels en resultaten van het onderzoek. De uitleg over de werking, de
stresstests, de evaluatie en de code staat in de [hoofd-README](../README.md);
de resultaten staan in [RESULTATEN.md](../RESULTATEN.md).

## Gebruik

```bash
cd experiments
python3.12 -m venv .venv            # Python 3.12 (numpy 2.5.3 vereist minimaal 3.12)
source .venv/bin/activate
pip install -r requirements.txt

python run_stress_tests.py           # ± 20 min; --max-stills 3 voor een proefrun van ± 4 min (overschrijft de CSV's en grafieken in results/)
python describe_dataset.py           # statistieken over de data
```

De labels staan al in `data/labels.csv`, dus je kunt direct beginnen met
`run_stress_tests.py`. Alleen als er foto's bijkomen:

```bash
python prepare_faces.py              # gezichten zoeken; bestaande labels blijven bewaard
python label_quiz.py                 # nieuwe gezichten labelen in de browser
python label_quiz.py --apply antwoorden.txt
```

## Bestanden

| Bestand | Wat het doet |
|---|---|
| `config.py` | alle instellingen: mappen, model, drempel, niveaus van de stresstests |
| `face_model.py` | gezichten vinden (RetinaFace) en embeddings berekenen (FaceNet), via deepface |
| `image_ops.py` | beeldbewerking: verkleinen/vergroten, donker/rood maken, CLAHE, perceptuele hash (dubbele foto's), overlap van kaders |
| `labels.py` | lezen/schrijven/controleren van `data/labels.csv` |
| `prepare_faces.py` | stap 1: alle gezichten zoeken, uitknippen en in `labels.csv` zetten |
| `label_quiz.py` | stap 2: labelquiz in de browser, en verwerken van de antwoorden |
| `run_stress_tests.py` | stap 3: het experiment (alle drie de stresstests) |
| `intermediate.py` | tussenresultaten als plaatjes (detecties, galerij, overzichtsvellen) |
| `plots.py` | grafieken voor de paper (`python plots.py` tekent ze opnieuw uit de CSV's) |
| `describe_dataset.py` | stap 4: grootte en helderheid van de gezichten per bron |
| `requirements.txt` | de benodigde Python-pakketten, met vaste versies |

## Mappen

| Map | Inhoud | In git? |
|---|---|---|
| `data/labels.csv` | één regel per gevonden gezicht, met het label (wie is het) | ja |
| `data/faces/` | de uitgeknipte gezichten (voor de labelquiz) | nee, wordt door stap 1 gemaakt |
| `results/*.csv` | de uitkomsten en samenvattingen | ja |
| `results/figures/` | grafieken (PDF voor LaTeX, PNG) | ja |
| `results/examples/` | met de hand gekozen voorbeeldbeelden voor RESULTATEN.md (overzichtsvellen, detectiebeelden, twee referentiegezichten); niet door de scripts bijgewerkt | ja |
| `results/intermediate/` | alle tussenresultaten (honderden plaatjes) en de labelquiz | nee, wordt door de scripts gemaakt |
| `.venv/` | de Python-omgeving | nee |

## labels.csv

| Kolom | Betekenis |
|---|---|
| `face_id` | unieke naam van het gezicht, bijv. `inCharacter/Johann/johann7_jpg_f2` (= gezicht nr. 2 in `johann7.jpg`) |
| `crop_path` | het uitgeknipte gezicht |
| `source` | `personal` (foto van de acteur buiten zijn rol), `inCharacter` (still) of `movie` (filmbeeld) |
| `source_path` | het originele bestand |
| `frame_time_s` | tijdstip in het filmfragment, in seconden (leeg bij foto's en stills) |
| `x`, `y`, `w`, `h` | het kader van het gezicht in het originele beeld, in pixels |
| `confidence` | hoe zeker de detector was |
| `brightness` | gemiddelde helderheid van het gezicht (0 = zwart, 255 = wit) |
| `label` | `DerAlte`, `FritzGrade`, `Johann`, `Werner`, `other` (figurant) of leeg (niet gebruikt) |
| `label_source` | `filename` (automatisch), `visual` (visueel gecontroleerd), `quiz` of `manual` |

Een label met de hand aanpassen mag gewoon in dit bestand; zet `label_source`
dan op `manual`, want labels met `filename` worden bij een nieuwe run van stap 1
opnieuw uit de bestandsnaam berekend. Gebruik daarbij de detectiebeelden in
`results/intermediate/detections/` (die maakt stap 1; ze staan niet in git): het
nummer `f0`, `f1`, … op het plaatje is het einde van de `face_id`.
