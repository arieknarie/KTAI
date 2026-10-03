# FaceNet stress tests – *Das Boot*

Code for the experiments in the paper (`../paper/main.tex`); the overall plan
is in `../PLAN.md`. It answers the three sub-questions of the paper with one
stress test each:

| Stress test | Question | Degradation (whole still) | Mitigation |
|---|---|---|---|
| 1 – Low resolution | Do small, blurry faces lower FaceNet's accuracy, and does interpolation help? | Still shrunk to 1/2 … 1/16 | Bicubic / Lanczos interpolation instead of nearest neighbour |
| 2 – Changing faces | Do sweat, dirt and beards lower recognition, and do extra reference photos help? | Film stills instead of normal photos | Extra in-character reference faces |
| 3 – Poor lighting | Does submarine lighting hurt recognition, and does CLAHE help? | Darkness and red alarm light (severity 0 … 0.9) | CLAHE pre-processing |

## How it works

The system gets every in-character still **as a whole**, as in practice:
with extras in the background, small faces and dark corners.

1. **Detection:** RetinaFace finds and aligns every face in the still.
2. **Embedding:** FaceNet maps each face (160 × 160 px) to a 128-dimensional
   vector of length 1.
3. **Identification:** each face gets the name of the reference face
   (*gallery*) at the smallest Euclidean distance, or **"unknown"** when that
   distance is 0.80 or more (open set: extras should become "unknown").
4. **Leave-one-out:** a still is never compared with reference faces from the
   same still or copies of them (identical files are skipped, near-identical
   face crops are grouped with a perceptual hash).
5. **Scoring:** the detected faces are matched, by box overlap, with the
   labelled faces in `data/labels.csv`. Every face gets one outcome:

| Face | Outcome | Meaning |
|---|---|---|
| Der Alte, Fritz, Johann, Werner | `correct` | recognised as the right person |
| | `wrong` | recognised as another of the four |
| | `rejected` | found, but "unknown" |
| | `missed` | not found by the face detector |
| Extra (`other`) | `rejected` | correctly "unknown" |
| | `false_identity` | wrongly named as one of the four |

Degradations are applied to the whole still **before** detection, so
detection, alignment and feature extraction all suffer from them.

The data in `../pictures` is used as follows:

- `pictures/personal/<name>/`: the actors **outside** their role, i.e. the
  baseline appearance. Always part of the gallery.
- `pictures/inCharacter/<name>/`: film stills. These are the test stills, and
  in Stress Test 2 their labelled faces are also extra references.
- `movies/`: optional, for describing real footage (face size, brightness).

## Files

| File | Purpose |
|---|---|
| `config.py` | All settings (paths, model, threshold, scales, severities, …) |
| `face_model.py` | Face detection and FaceNet embeddings (wraps `deepface`) |
| `image_ops.py` | Degradations (low resolution, low light) and mitigations (interpolation, CLAHE) |
| `labels.py` | Reading/writing `data/labels.csv` |
| `prepare_faces.py` | **Step 1** – detect all faces, write the crops and `data/labels.csv` |
| `label_quiz.py` | **Step 2** – label the remaining faces with a quiz in the browser |
| `run_stress_tests.py` | **Step 3** – run all experiments, write `results/` |
| `describe_dataset.py` | **Step 4** – statistics of the data set (face size, brightness) |
| `plots.py` | Figures for the paper |
| `intermediate.py` | Images of the intermediate results (see below) |

## Installation

Python 3.11 or 3.12 is required (TensorFlow does not support newer versions yet).

```bash
cd experiments
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The first run downloads the FaceNet and RetinaFace weights
(± 200 MB) to `~/.deepface/`.

## Running

```bash
python prepare_faces.py                     # step 1 (add --movies to include the clips)
python label_quiz.py                        # step 2, then: python label_quiz.py --apply answers.txt
python run_stress_tests.py                  # step 3 (± 30 min; --max-stills 3 for a quick test)
python describe_dataset.py                  # step 4
```

### Labels

Every face found in a still needs a label (`DerAlte`, `FritzGrade`,
`Johann`, `Werner`, or `other` for an extra), because the scoring is done per
face. The `label_source` column records where a label comes from:

| `label_source` | Meaning |
|---|---|
| `filename` | Automatic: the file name names one person and exactly one face was found |
| `claude` | Set by visual inspection of the detection images; please check |
| `quiz` | Answered in the label quiz |
| `manual` | Typed into `labels.csv` by hand |

A face with an empty label ("weet niet" in the quiz) is left out of the
scoring. Running `prepare_faces.py` again keeps all labels.

The "largest face" in a picture is **not** used as a label: in `johann7.jpg`
the largest face is an extra in the foreground.

## Results

`run_stress_tests.py` writes to `results/`:

| File | Content |
|---|---|
| `per_face.csv` | Every face under every condition: prediction, distance, closest reference, outcome |
| `summary.csv` | Scores per experiment, mitigation and level |
| `summary_by_identity.csv` | The same, per person |
| `figures/stress_test_*.pdf/png` | Figures for the paper |

Scores in `summary.csv`:

| Column | Meaning |
|---|---|
| `recognised` | Share of the named faces recognised correctly (the main score) |
| `wrong`, `rejected`, `missed` | Share of the named faces with that outcome |
| `closest_correct` | Share of the named faces whose closest reference is the right person, ignoring the threshold |
| `extras_named` | Share of the extras that were wrongly given one of the four names |
| `precision` | Of all names the system gave, the share that was correct |

### Intermediate results

Every processing step is also saved as an image in `results/intermediate/`
(not in git; the scripts re-create it), so the results can be checked by eye:

| Folder / file | What you see |
|---|---|
| `detections/` | Every picture with a numbered box per detected face; `f0`, `f1`, … match the end of the `face_id` in `labels.csv` |
| `label_quiz.html` | The label quiz |
| `gallery_overview.jpg`, `gallery_overview_clahe.jpg` | All reference faces exactly as FaceNet receives them (160 × 160), without and with CLAHE |
| `stress_test_1_resolution/` | Per still: every scale × upscaling method side by side |
| `stress_test_2_appearance/` | Per still: both galleries side by side |
| `stress_test_3_lighting/` | Per still: every lighting severity, without and with CLAHE |

The boxes on the stress-test sheets show the name the system gave and the
distance: green = right person, red = wrong name, grey = "unknown",
orange = a named person the detector missed. While `run_stress_tests.py`
runs, the scores of every condition are also printed in the terminal.
