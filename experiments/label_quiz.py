"""Label the remaining faces with a quiz in the browser.

Usage:
    python label_quiz.py                      # make the quiz and open it in the browser
    python label_quiz.py --apply answers.txt  # write the answers to data/labels.csv

The quiz shows every picture that still has unlabelled faces, with the
numbered boxes from results/intermediate/detections/. For each face, pick one
of the four people, "Figurant" (an extra) or "Weet niet". At the end the page
shows the answers as text (copy it, or download it as a file); pass that text
to --apply. "Weet niet" leaves the label empty, so that face is not used.

A bar at the top, which stays visible while scrolling, shows clear reference
faces of the four people (REFERENCE_FACES): film stills from the start and
later in the film (they change, e.g. beards) and a photo of the actor.
"""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

import config
import labels

QUIZ_HTML = config.INTERMEDIATE_DIR / "label_quiz.html"
CHOICES = [*config.IDENTITIES, config.OTHER_LABEL]

# Clear reference faces per person for the bar at the top of the quiz, picked
# by hand from the labelled faces: film stills from the start of the film
# (clean-shaven) and later on (beard, dirt), and one photo of the actor from
# that period. (An automatic choice picked a recent portrait of the actor of
# Der Alte, which does not help when looking at film stills.)
REFERENCE_FACES = {
    "DerAlte": {
        "film": ["inCharacter/Werner/alte_and_werner_and_fritz_jpg_f0",
                 "inCharacter/DerAlte/derAlte1_jpeg_f1",
                 "inCharacter/DerAlte/alte_and_fritz_png_f1"],
        "actor": ["personal/DerAlte/derAlte2_jpg_f0"],
    },
    "FritzGrade": {
        "film": ["inCharacter/Werner/alte_and_werner_and_fritz_jpg_f1",
                 "inCharacter/FritzGrade/Fritz2_png_f0",
                 "inCharacter/DerAlte/alte_and_fritz_png_f0"],
        "actor": ["personal/FritzGrade/fritz1_png_f0"],
    },
    "Johann": {
        "film": ["inCharacter/Johann/alte_and_johann_jpg_f1",
                 "inCharacter/Johann/johann4_jpg_f0",
                 "inCharacter/Johann/johann5_jpg_f0"],
        "actor": ["personal/Johann/Johann1_jpg_f0"],
    },
    "Werner": {
        "film": ["inCharacter/Werner/werner1_jpg_f0",
                 "inCharacter/Werner/alte_and_werner3_jpg_f1",
                 "inCharacter/FritzGrade/alte_and_fritz_and_werner_png_f2"],
        "actor": ["personal/Werner/werner1_jpg_f0"],
    },
}


def reference_faces() -> list[dict]:
    """Crop paths (relative to the quiz page) of the faces in REFERENCE_FACES.

    Faces that no longer exist or no longer carry the expected label (e.g.
    after re-running prepare_faces.py) are left out with a warning.
    """
    faces = labels.load_labels().set_index("face_id")
    references = []
    for identity, groups in REFERENCE_FACES.items():
        reference = {"label": identity}
        for kind, face_ids in groups.items():
            reference[kind] = []
            for face_id in face_ids:
                if face_id not in faces.index or faces.at[face_id, "label"] != identity:
                    print(f"  warning: reference face {face_id} is missing or not labelled {identity}")
                    continue
                reference[kind].append("../../" + faces.at[face_id, "crop_path"])
        references.append(reference)
    return references


def quiz_data() -> list[dict]:
    """One entry per picture that still has at least one unlabelled face."""
    faces = labels.load_labels()
    faces = faces[faces["source"] != "movie"]  # movie frames: see README
    faces = faces.assign(picture=faces["face_id"].str.rsplit("_f", n=1).str[0])
    pictures = []
    for picture, group in faces.groupby("picture", sort=False):
        if (group["label"] != "").all():
            continue
        named = labels.identities_in_filename(Path(group["source_path"].iloc[0]))
        pictures.append({
            "picture": picture,
            "image": f"detections/{picture}.jpg",  # relative to the HTML file
            "named": sorted(named),
            "faces": [
                {"face_id": row.face_id,
                 "number": row.face_id.rsplit("_", 1)[-1],
                 "crop": "../../" + row.crop_path,
                 "label": row.label}
                for row in group.itertuples()
            ],
        })
    return pictures


def write_quiz() -> None:
    pictures = quiz_data()
    if not pictures:
        print("All faces are labelled; nothing to ask.")
        return
    html = (HTML_TEMPLATE.replace("__DATA__", json.dumps(pictures))
            .replace("__CHOICES__", json.dumps(CHOICES))
            .replace("__REFERENCES__", json.dumps(reference_faces())))
    QUIZ_HTML.parent.mkdir(parents=True, exist_ok=True)
    QUIZ_HTML.write_text(html, encoding="utf-8")
    open_faces = sum(face["label"] == "" for picture in pictures for face in picture["faces"])
    print(f"Quiz with {len(pictures)} pictures / {open_faces} faces: {QUIZ_HTML}")
    webbrowser.open(QUIZ_HTML.as_uri())


def apply_answers(text: str) -> None:
    """Write lines "face_id=label" to labels.csv (label_source "quiz")."""
    faces = labels.load_labels()
    applied = 0
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        face_id, label = (part.strip() for part in line.rsplit("=", 1))
        if label not in CHOICES:
            raise SystemExit(f"invalid label {label!r} in line: {line}")
        mask = faces["face_id"] == face_id
        if mask.sum() != 1:
            raise SystemExit(f"unknown face_id: {face_id}")
        faces.loc[mask, ["label", "label_source"]] = [label, "quiz"]
        applied += 1
    labels.save_labels(faces)
    print(f"Applied {applied} answers; {(faces['label'] == '').sum()} face(s) still without a label.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", metavar="FILE", help="answers file from the quiz ('-' reads from stdin)")
    args = parser.parse_args()
    if args.apply:
        text = sys.stdin.read() if args.apply == "-" else Path(args.apply).read_text(encoding="utf-8")
        apply_answers(text)
    else:
        write_quiz()


# The page is self-contained; images are loaded from the results/intermediate
# and data/faces folders through relative paths.
HTML_TEMPLATE = """<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gezichten labelen</title>
<style>
  :root { --bg: #fcfcfb; --ink: #0b0b0b; --ink-2: #52514e; --line: #d9d8d3; --accent: #2a78d6; --error: #c62828; }
  @media (prefers-color-scheme: dark) {
    :root { --bg: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7; --line: #3a3a38; --accent: #3987e5; --error: #ef6c6c; }
  }
  body { margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.5 system-ui, sans-serif; }
  main { max-width: 900px; margin: 0 auto; padding: 16px; }
  .meta { color: var(--ink-2); font-size: 14px; }
  .scene { width: 100%; border-radius: 8px; border: 1px solid var(--line); }
  .face { display: flex; gap: 12px; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--line); flex-wrap: wrap; }
  .face img { width: 72px; height: 72px; object-fit: contain; background: #000; border-radius: 6px; }
  .face .num { font-weight: 600; width: 34px; }
  .choices { display: flex; gap: 6px; flex-wrap: wrap; }
  button { font: inherit; font-size: 14px; padding: 6px 10px; border-radius: 6px; border: 1px solid var(--line);
           background: transparent; color: var(--ink); cursor: pointer; }
  button.on { background: var(--accent); border-color: var(--accent); color: #fff; }
  .nav { display: flex; gap: 8px; margin: 16px 0; align-items: center; flex-wrap: wrap; }
  .error { color: var(--error); font-size: 14px; }
  textarea { width: 100%; height: 260px; font: 13px ui-monospace, monospace; background: transparent; color: var(--ink); }
  .refs { position: sticky; top: 0; z-index: 1; background: var(--bg); border-bottom: 1px solid var(--line);
          padding: 8px 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); gap: 8px; }
  .ref b { display: block; font-size: 14px; font-weight: 600; }
  .ref img { width: 76px; height: 76px; object-fit: cover; border-radius: 6px; margin-right: 3px; }
  .ref img.actor { outline: 2px solid var(--line); }
  .ref-toggle { font-size: 13px; margin-left: 8px; }
</style>
</head>
<body>
<main>
  <h1 style="font-size: 22px; font-weight: 500;">Wie is wie?</h1>
  <p class="meta">Kies per genummerd gezicht wie het is. Figurant = iemand anders dan de vier.
     Weet niet = het gezicht wordt niet gebruikt. Je antwoorden blijven bewaard als je de pagina herlaadt.
     De balk hieronder blijft staan: per persoon een paar filmbeelden en (met rand) een foto van de acteur.
     <button class="ref-toggle" id="toggle-refs">Referenties verbergen</button></p>
  <div class="refs" id="refs"></div>
  <div id="quiz"></div>
</main>
<script>
const PICTURES = __DATA__;
const CHOICES = __CHOICES__;
const REFERENCES = __REFERENCES__;
const NAMES = { DerAlte: "Der Alte", FritzGrade: "Fritz", Johann: "Johann", Werner: "Werner", other: "Figurant", unknown: "Weet niet" };
const STORE = "label-quiz-answers";
let answers = {};
try { answers = JSON.parse(localStorage.getItem(STORE) || "{}"); } catch (e) { answers = {}; }
let step = 0;

function save() { try { localStorage.setItem(STORE, JSON.stringify(answers)); } catch (e) {} }

function renderReferences() {
  const bar = document.getElementById("refs");
  bar.innerHTML = REFERENCES.map(r =>
    `<div class="ref"><b>${NAMES[r.label]}</b>` +
    r.film.map(src => `<a href="${src}" target="_blank"><img src="${src}" alt="${NAMES[r.label]} in de film" title="in de film"></a>`).join("") +
    r.actor.map(src => `<a href="${src}" target="_blank"><img class="actor" src="${src}" alt="acteur van ${NAMES[r.label]}" title="de acteur"></a>`).join("") +
    `</div>`).join("");
  const toggle = document.getElementById("toggle-refs");
  toggle.onclick = () => {
    const hidden = bar.style.display === "none";
    bar.style.display = hidden ? "" : "none";
    toggle.textContent = hidden ? "Referenties verbergen" : "Referenties tonen";
  };
}
function openFaces(p) { return p.faces.filter(f => f.label === ""); }

function render() {
  const root = document.getElementById("quiz");
  if (step >= PICTURES.length) return renderResult(root);
  const p = PICTURES[step];
  const named = p.named.length ? p.named.map(n => NAMES[n]).join(", ") : "niemand";
  let html = `<p class="meta">Vraag ${step + 1} van ${PICTURES.length} &middot; ${p.picture}<br>
              Volgens de bestandsnaam staat hierop: <b>${named}</b></p>
              <img class="scene" src="${p.image}" alt="${p.picture}">`;
  for (const f of p.faces) {
    if (f.label !== "") {
      html += `<div class="face"><img src="${f.crop}" alt=""><span class="num">${f.number}</span>
               <span class="meta">al gelabeld: ${NAMES[f.label] || f.label}</span></div>`;
      continue;
    }
    html += `<div class="face"><img src="${f.crop}" alt=""><span class="num">${f.number}</span><div class="choices">`;
    for (const c of [...CHOICES, "unknown"]) {
      const on = answers[f.face_id] === c ? " on" : "";
      html += `<button class="${on}" data-face="${f.face_id}" data-choice="${c}">${NAMES[c]}</button>`;
    }
    html += `</div></div>`;
  }
  html += `<div class="nav">
             <button id="prev" ${step === 0 ? "disabled" : ""}>Vorige</button>
             <button id="rest">Rest = figurant</button>
             <button id="next">${step === PICTURES.length - 1 ? "Klaar" : "Volgende"}</button>
             <span id="err" class="error"></span></div>`;
  root.innerHTML = html;
  root.querySelectorAll("button[data-face]").forEach(b => b.onclick = () => {
    answers[b.dataset.face] = b.dataset.choice; save(); render();
  });
  document.getElementById("prev").onclick = () => { step -= 1; render(); };
  document.getElementById("rest").onclick = () => {
    openFaces(p).forEach(f => { if (!answers[f.face_id]) answers[f.face_id] = "other"; }); save(); render();
  };
  document.getElementById("next").onclick = () => {
    const missing = openFaces(p).filter(f => !answers[f.face_id]).map(f => f.number);
    if (missing.length) { document.getElementById("err").textContent = "Nog kiezen voor: " + missing.join(", "); return; }
    step += 1; render(); window.scrollTo(0, 0);
  };
}

function renderResult(root) {
  const lines = ["# label-quiz answers (face_id=label)"];
  for (const p of PICTURES) for (const f of openFaces(p)) {
    const a = answers[f.face_id];
    if (a && a !== "unknown") lines.push(`${f.face_id}=${a}`);
  }
  const text = lines.join("\\n") + "\\n";
  root.innerHTML = `<p>Klaar! Download de antwoorden (of kopieer ze naar een tekstbestand)
     en gebruik <code>python label_quiz.py --apply bestand.txt</code>.</p>
     <textarea id="out" readonly></textarea>
     <div class="nav"><button id="copy">Kopieer</button><a id="dl" download="label_quiz_answers.txt">Download</a>
     <button id="back">Terug</button><span id="msg" class="meta"></span></div>`;
  document.getElementById("out").value = text;
  document.getElementById("dl").href = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
  document.getElementById("back").onclick = () => { step = PICTURES.length - 1; render(); };
  document.getElementById("copy").onclick = async () => {
    const out = document.getElementById("out");
    try { await navigator.clipboard.writeText(text); }
    catch (e) { out.select(); document.execCommand("copy"); }
    document.getElementById("msg").textContent = "Gekopieerd.";
  };
}
renderReferences();
render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
