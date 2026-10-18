// Labelpagina. De gegevens komen uit items.json (gemaakt door code/make_label_items.py);
// elk label wordt via app.py direct opgeslagen in labels.csv.

const state = {
  data: null,        // inhoud van items.json
  labels: {},        // gezicht-id -> label, zoals opgeslagen in labels.csv
  index: 0,          // nummer van het item dat nu getoond wordt
  activeFace: 0,     // nummer van het gezicht dat nu gekozen wordt
  labelsFile: "",    // waar labels.csv staat (voor de melding als alles af is)
  drawn: {},         // item-id -> gezichten die de labelaar zelf getekend heeft (die had de computer gemist)
  drawing: false,    // staat "Gezicht tekenen" aan?
};

const $ = id => document.getElementById(id);
const esc = text => String(text).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const APP_WINDOW = "het venster van de app (op Windows zwart, op de Mac het venster van Terminal)";
// Toont de afbeelding `image` het bestand `path` (uit items.json)? img.src is een volledig, gecodeerd adres.
const shows = (image, path) => !!image.getAttribute("src") &&
  decodeURIComponent(new URL(image.src, location.href).pathname).endsWith("/" + path);

// Uitleg bij de keuzeknoppen (zichtbaar als je de muis op een knop houdt).
const CHOICE_HELP = {
  other: "Een gezicht dat je goed genoeg ziet, en het is niet een van de vier personen.",
  no_face: "Alleen als je zeker weet dat er geen gezicht in het kader staat: bijvoorbeeld een lamp, een hand, een achterhoofd of kleding.",
  unknown: "Wel een gezicht, maar je kunt niet zeggen wie (te donker, te wazig, te klein, te ver weggedraaid). " +
           "Ook als je twijfelt wie het is, of twijfelt of het wel een gezicht is.",
};
const choiceHelp = c => CHOICE_HELP[c.key] || `Alleen als je zeker weet dat dit ${c.name} is. Twijfel je? Kies 7 Weet niet.`;

// ---------- opslaan ----------

// Keuzes die (nog) niet opgeslagen konden worden, bijvoorbeeld omdat het venster van de app
// dicht was. Ze worden bij de volgende geslaagde opslag alsnog meegestuurd.
const unsaved = new Map();
function rememberUnsaved() {
  if (stopped) return;
  try { localStorage.setItem("unsaved", JSON.stringify([...unsaved.values()])); } catch (e) { /* niet nodig */ }
}

// Opslagverzoeken gaan één voor één, in de volgorde van de keuzes. Zo kan een oudere keuze een
// nieuwere keuze voor hetzelfde gezicht nooit overschrijven.
let saving = Promise.resolve();
function save(rows) {
  if (stopped) return saving;
  const labeler = $("labeler").value.trim();
  rows.forEach(row => { row.labeler = labeler; unsaved.set(row.face, row); });
  rememberUnsaved();
  saving = saving.then(sendUnsaved);
  return saving;
}

async function sendUnsaved() {
  const sending = [...unsaved.values()];
  if (!sending.length || stopped) return;
  $("save-status").textContent = "Opslaan…";
  $("save-status").className = "status";
  try {
    const response = await fetch("/api/labels", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(sending),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || response.statusText);
    // overgeslagen keuzes blijven bewaard en worden later opnieuw verstuurd
    const skipped = new Set((result.skipped || []).map(s => s.face));
    sending.forEach(row => { if (!skipped.has(row.face) && unsaved.get(row.face) === row) unsaved.delete(row.face); });
    rememberUnsaved();
    if (skipped.size) throw new Error((result.skipped || []).some(s => s.reason === "naam")
      ? "Vul bovenaan een naam in, met letters."
      : `De app kent deze gezichten niet. Sluit ${APP_WINDOW} en start de app opnieuw.`);
    $("save-status").textContent = "Opgeslagen ✓";
    $("save-status").className = "status saved";
    $("error").classList.add("hidden");
  } catch (error) {
    // TypeError: de app was niet bereikbaar. Anders: de app antwoordde met een melding.
    const unreachable = error instanceof TypeError;
    $("error").textContent = `Let op: ${unsaved.size} keuze(s) NIET opgeslagen. ` + (unreachable
      ? `De app reageert niet: ${APP_WINDOW} is dicht of vastgelopen. Start de app opnieuw (zie de handleiding, stap 3). ` +
        "De keuzes die nog niet opgeslagen zijn, worden daarna alsnog opgeslagen."
      : error.message + " Zodra je daarna weer iets kiest, worden de keuzes die nog niet opgeslagen zijn, alsnog opgeslagen.");
    $("error").classList.remove("hidden");
    $("save-status").textContent = "";
  }
}

// Zonder naam wordt niets opgeslagen: bij elk label moet te zien zijn wie het gekozen heeft.
// De naam wordt net zo opgeschoond als in app.py (letters, cijfers, spatie, punt en streepjes),
// en moet minstens één letter bevatten.
const cleanName = name => name.replace(/[^\p{L}\p{N}_ .-]/gu, "").replace(/^[ ._-]+/, "").slice(0, 40).trim();
const nameOk = () => /\p{L}/u.test(cleanName($("labeler").value));
function haveName() {
  if (nameOk()) return true;
  $("error").textContent = "Vul eerst bovenaan bij \"Jouw naam\" je naam in (met letters) en druk op Enter. Daarna kun je kiezen.";
  $("error").classList.remove("hidden");
  $("labeler").focus();
  return false;
}

// how: "chosen" als de labelaar zelf kiest, "auto" als een gezicht zonder keuze figurant wordt bij Volgende
function labelRow(item, face, label, how = "chosen") {
  return { face: face.face, item: item.id, label: label, how: how, source: face.source, frame: face.frame ?? "",
           x: face.box[0], y: face.box[1], w: face.box[2], h: face.box[3] };
}

// ---------- één labelpagina tegelijk ----------

// Wordt de labelpagina opnieuw geopend (bijvoorbeeld na een nieuwe start van de app), dan stopt deze
// oudere pagina. Haar niet-opgeslagen keuzes staan in de browser en worden door de nieuwe pagina opgeslagen.
const pageId = String(Date.now()) + "-" + Math.random();
let stopped = false;
window.addEventListener("storage", event => {
  if (event.key !== "active-page" || !event.newValue || event.newValue === pageId) return;
  stopped = true;
  unsaved.clear();
  $("error").textContent = "Deze labelpagina is opnieuw geopend in een ander tabblad of venster. Werk daar verder; " +
                           "dit tabblad kun je sluiten.";
  $("error").classList.remove("hidden");
});

// ---------- tekenen ----------

const choiceName = key => (state.data.choices.find(c => c.key === key) || {}).name || key;
const choiceKey = key => (state.data.choices.find(c => c.key === key) || {}).shortcut || "";
const isDone = item => item.faces.every(face => state.labels[face.face]);   // getekende gezichten tellen niet mee
// alle gezichten van een item: eerst die van de computer, daarna de getekende
const facesOf = item => item.faces.concat(state.drawn[item.id] || []);
const pct = (value, total) => (100 * value / total).toFixed(3) + "%";

function renderProgress() {
  const groups = [];
  let doneTotal = 0;
  state.data.items.forEach((item, index) => {
    let group = groups.find(g => g.name === item.group);
    if (!group) { group = { name: item.group, total: 0, done: 0, first: index, open: undefined }; groups.push(group); }
    group.total++;
    if (isDone(item)) { group.done++; doneTotal++; }
    else if (group.open === undefined) group.open = index;
  });
  const current = state.data.items[state.index].group;
  const short = name => name.replace(" uit de film", "").replace(" van de acteurs", "");
  $("progress").innerHTML = groups.map(g =>
    `<button data-go="${g.open ?? g.first}" class="${g.name === current ? "current" : ""}"` +
    ` title="${esc(g.name)}: naar het eerste item dat nog niet af is">${esc(short(g.name))}: ${g.done} van ${g.total}` +
    `<span class="bar"><span style="width:${pct(g.done, g.total)}"></span></span></button>`).join("");
  $("progress").querySelectorAll("button").forEach(b => b.onclick = () => show(Number(b.dataset.go)));

  const total = state.data.items.length;
  $("item-counter").textContent = `Item ${state.index + 1} van ${total} · ${doneTotal} af`;
  if (doneTotal === total) {
    $("done").textContent = `Klaar! Alle ${total} items zijn gelabeld. Je labels staan in het bestand: ${state.labelsFile}. ` +
      "Stuur dat bestand naar Marc (zie de handleiding, stap 6). Daarna mag je de browser en het venster van de app sluiten.";
    $("done").classList.remove("hidden");
  } else {
    $("done").classList.add("hidden");
  }
}

function renderReferences() {
  $("references").innerHTML = state.data.references.map(person =>
    `<div class="person"><b>${esc(person.name)}</b>` +
    person.images.map(src => `<img src="../${esc(src)}" alt="${esc(person.name)}">`).join("") + `</div>`).join("");
  // een foto groot tonen zolang de muis erop staat
  $("references").querySelectorAll("img").forEach(img => {
    img.onmouseenter = () => {
      const r = img.getBoundingClientRect(), big = $("ref-big");
      big.src = img.src;
      big.classList.remove("hidden");
      big.style.left = Math.min(r.right + 8, innerWidth - 150) + "px";
      big.style.top = Math.max(4, Math.min(r.top, innerHeight - 170)) + "px";
    };
    img.onmouseleave = () => $("ref-big").classList.add("hidden");
  });
}

// Een waarschuwing in de uitleg rechts (geel), waarna de uitvergroting opnieuw past.
function warn(html) {
  $("instruction").innerHTML = html;
  $("instruction").classList.add("warn");
  fitZoom();
  renderZoom();
}

// Het nummer en de naam van een gezicht in een item. Getekende gezichten tellen door na de gezichten van
// de computer; bij een track heet het gezicht van de computer "geel kader".
function faceNumber(item, i) {
  if (item.kind !== "track") return String(i + 1);
  return i === 0 ? "track" : `+${i}`;
}
function faceTitle(item, i) {
  const face = facesOf(item)[i];
  if (face.drawn) return item.kind === "track" ? `Getekend gezicht ${i}` : `Gezicht ${i + 1} (getekend)`;
  return item.kind === "track" ? "Gezicht in het gele kader" : `Gezicht ${i + 1} van ${item.faces.length}`;
}

function instruction(item) {
  if (state.drawing) {
    return "Sleep met de muis een kader om het gezicht dat de computer gemist heeft. <b>Esc</b> = stoppen met tekenen.";
  }
  const face = facesOf(item)[state.activeFace];
  if (face && face.drawn && !state.labels[face.face]) {
    return "Kies wie het getekende gezicht is. Verkeerd getekend? Klik op <b>Weghalen</b> (of druk op Delete).";
  }
  if (item.kind === "track") {
    return "Wie is het gezicht in het <b>gele kader</b>? Na je keuze ga je vanzelf door. Twijfel je wie het is, " +
           "of of het wel een gezicht is? Kies <b>7 Weet niet</b>." +
           ((item.others || []).length ? ` <span class="others-note">Grijze stippelkaders zijn andere gezichten die de ` +
                                         "computer ook vond; die komen later apart aan de beurt.</span>" : "");
  }
  return "Kies voor elk genummerd gezicht wie het is. Gezichten zonder keuze worden <b>figurant</b> als je op Volgende klikt.";
}

// Het item waarvoor de waarschuwing van Volgende in beeld staat (-1: geen). Zodra het beeld opnieuw
// getekend wordt, bijvoorbeeld na een keuze, is de waarschuwing weg en waarschuwt Volgende opnieuw.
let warned = -1;

function renderItem() {
  const item = state.data.items[state.index];
  $("item-title").textContent = item.title;
  $("instruction").innerHTML = instruction(item);
  $("instruction").classList.remove("warn");
  warned = -1;

  // het beeld met de kaders, zo groot als op het scherm past (ook kleine video-frames worden vergroot)
  if (!shows($("image"), item.image)) $("image").src = "../" + item.image;
  const frame = $("frame");
  fitFrame();
  frame.querySelectorAll(".box").forEach(box => box.remove());
  frame.classList.toggle("drawing", state.drawing);
  // bij een track: de gezichten die de computer in dit beeld ook vond (die komen in een eigen track aan de beurt)
  (item.others || []).forEach(([x, y, w, h]) => {
    const box = document.createElement("div");
    box.className = "box other";
    box.title = "Dit gezicht heeft de computer ook gevonden; het komt in een eigen track aan de beurt.";
    box.style.left = pct(x, item.width); box.style.top = pct(y, item.height);
    box.style.width = pct(w, item.width); box.style.height = pct(h, item.height);
    frame.appendChild(box);
  });
  const faces = facesOf(item);
  faces.forEach((face, i) => {
    const [x, y, w, h] = face.box;
    const box = document.createElement("div");
    const label = state.labels[face.face];
    box.className = "box" + (face.drawn ? " drawn" : "") + (label ? " done" : "") + (i === state.activeFace ? " active" : "");
    box.style.left = pct(x, item.width); box.style.top = pct(y, item.height);
    box.style.width = pct(w, item.width); box.style.height = pct(h, item.height);
    const number = item.kind === "track" && !face.drawn ? "" : `${faceNumber(item, i)} `;
    box.innerHTML = `<span>${number}${label ? esc(choiceName(label)) : ""}</span>`;
    box.onclick = () => selectFace(i);
    frame.appendChild(box);
  });

  // bij meer gezichten: een knopje per gezicht om te wisselen (groen = gekozen, geel = nu aan de beurt)
  $("face-tabs").innerHTML = faces.length < 2 ? "" : faces.map((face, i) => {
    const label = state.labels[face.face];
    return `<button data-face="${i}" class="${label ? "done" : ""} ${i === state.activeFace ? "active" : ""}"` +
           ` title="${esc(faceTitle(item, i))}${label ? ": " + esc(choiceName(label)) : " (nog niets gekozen)"}">` +
           `${faceNumber(item, i)}${label ? " ✓" : ""}</button>`;
  }).join("");
  $("face-tabs").querySelectorAll("button").forEach(b => b.onclick = () => selectFace(Number(b.dataset.face)));

  // de keuzeknoppen voor het gezicht dat nu aan de beurt is (bij een getekend gezicht zonder "Geen gezicht":
  // een verkeerd getekend kader haal je weg)
  const i = state.activeFace, face = faces[i], label = state.labels[face.face];
  const title = faceTitle(item, i);
  $("faces").innerHTML = `<div class="face"><div class="title">${esc(title)}${label ? ": " + esc(choiceName(label)) : ""}` +
    (face.drawn ? ` <button class="remove" id="remove" title="Dit getekende kader weghalen (toets Delete)">Weghalen</button>` : "") +
    `</div><div class="choices">` + state.data.choices.filter(c => !(face.drawn && c.key === "no_face")).map(c =>
      `<button data-face="${i}" data-label="${c.key}" class="${label === c.key ? "chosen" : ""}" title="${esc(choiceHelp(c))}">` +
      `<kbd>${esc(c.shortcut)}</kbd>${esc(c.name)}</button>`).join("") + `</div></div>`;
  $("faces").querySelectorAll(".choices button").forEach(b => b.onclick = () => choose(Number(b.dataset.face), b.dataset.label));
  if (face.drawn) $("remove").onclick = removeDrawn;
  $("draw").classList.toggle("on", state.drawing);

  renderProgress();
  fitZoom();
  renderZoom();
  updateBrightness();
}

// Het beeld zo groot maken als in het beeldvak past, zonder dat er iets buiten het scherm valt.
function fitFrame() {
  if (!state.data) return;
  const item = state.data.items[state.index], stage = $("stage");
  const width = Math.min(stage.clientWidth, stage.clientHeight * item.width / item.height);
  $("frame").style.width = Math.max(50, Math.floor(width)) + "px";
}

// De uitvergroting zo groot maken als in het rechterblok past: eerst klein, dan meten hoeveel ruimte
// er onder de knoppen over is, en die ruimte aan de uitvergroting geven. De pagina scrolt nooit.
function fitZoom() {
  const panel = $("panel"), zoom = $("zoom");
  zoom.style.width = zoom.style.height = "";   // de kleinste maat uit style.css
  const css = getComputedStyle(panel);
  const inner = panel.clientWidth - parseFloat(css.paddingLeft) - parseFloat(css.paddingRight);
  const top = panel.getBoundingClientRect().top;
  const bottom = Math.max(...[...panel.children].map(child => child.getBoundingClientRect().bottom));
  const free = panel.clientHeight - parseFloat(css.paddingBottom) - (bottom - top) - 2;
  const size = Math.floor(Math.min(inner, zoom.offsetWidth + Math.max(0, free), 260));
  zoom.style.width = zoom.style.height = size + "px";
}

// Het gezicht dat nu aan de beurt is, uitvergroot (gezichten in de video's zijn vaak klein).
function renderZoom() {
  const item = state.data.items[state.index], zoom = $("zoom");
  const [x, y, w, h] = facesOf(item)[state.activeFace].box;
  const side = Math.max(w, h) * 1.6, scale = zoom.clientWidth / side;
  zoom.style.backgroundImage = `url('../${item.image}')`;
  zoom.style.backgroundSize = `${item.width * scale}px ${item.height * scale}px`;
  zoom.style.backgroundPosition = `${-(x + w / 2 - side / 2) * scale}px ${-(y + h / 2 - side / 2) * scale}px`;
}

new ResizeObserver(fitFrame).observe($("stage"));   // ook als het venster of een balk de ruimte verandert
new ResizeObserver(() => { if (state.data) { fitZoom(); renderZoom(); } }).observe($("panel"));

// ---------- kiezen en bladeren ----------

// Een keuze of Volgende telt pas als het beeld geladen is en minstens 0,3 seconde te zien was. Zo kiest een
// dubbelklik of twee snelle toetsaanslagen nooit voor een gezicht dat nog niet in beeld was.
const WAIT_MS = 300;
let readyAt = 0;
const ready = () => $("image").complete && performance.now() >= readyAt;
const notYet = () => { readyAt = Math.max(readyAt, performance.now() + WAIT_MS); };

function selectFace(i) {
  state.activeFace = i;
  notYet();
  renderItem();
}

function choose(faceIndex, label) {
  if (stopped || !ready() || !haveName() || state.drawing) return;
  const item = state.data.items[state.index];
  const face = facesOf(item)[faceIndex];
  if (face.drawn && label === "no_face") return;   // een verkeerd getekend kader haal je weg
  state.labels[face.face] = label;
  save([labelRow(item, face, label, face.drawn ? "getekend" : "chosen")]);
  if (face.drawn) {
    // na een getekend gezicht: terug naar het eerste gezicht van de computer zonder keuze (bij een track het gele kader)
    const open = item.faces.findIndex(f => !state.labels[f.face]);
    state.activeFace = open >= 0 ? open : faceIndex;
    notYet();
    renderItem();
    return;
  }
  if (item.kind === "track") {
    // de regel "Net gekozen" staat alleen bij het item direct na de keuze; ← brengt je dan terug naar die keuze
    const from = state.index;
    move(state.index + 1);
    $("last-choice").textContent = state.index !== from
      ? `Net gekozen: ${choiceKey(label)} ${choiceName(label)}. Fout? Druk op ← en kies opnieuw.` : "";
    return;
  }
  // naar het volgende gezicht zonder keuze: eerst verder, daarna weer vooraan beginnen
  const order = item.faces.map((f, i) => (faceIndex + 1 + i) % item.faces.length);
  const open = order.find(i => !state.labels[item.faces[i].face]);
  state.activeFace = open !== undefined ? open : faceIndex;
  notYet();
  renderItem();
}

// Volgende (knop of Enter). Bij een track zonder keuze gaat de app niet door: na een keuze gaat de app
// al vanzelf door, en Volgende slaat dus nooit ongemerkt een track over (overslaan kan met →).
// Bij een foto of still met gezichten zonder keuze zegt de app eerst hoeveel dat er zijn; pas bij de
// tweede keer Volgende, terwijl die waarschuwing nog in beeld staat, worden die gezichten figurant.
function next() {
  if (stopped || !ready()) return;
  const item = state.data.items[state.index];
  if (state.drawing) stopDrawing();
  const unchosen = facesOf(item).findIndex(f => f.drawn && !state.labels[f.face]);
  if (unchosen >= 0) {
    state.activeFace = unchosen;
    renderItem();
    warn("Kies eerst wie het getekende gezicht is, of klik op <b>Weghalen</b>.");
    return;
  }
  if (item.kind === "track" && !isDone(item)) {
    warn("Kies eerst wie het is (<b>1</b> t/m <b>7</b>). Wil je deze track overslaan, druk dan op <b>→</b>.");
    return;
  }
  if (item.kind !== "track") {
    const open = item.faces.filter(f => !state.labels[f.face]);
    if (open.length) {
      if (!haveName()) return;
      if (warned !== state.index) {
        warned = state.index;
        warn(`Nog <b>${open.length}</b> gezicht(en) zonder keuze (wit gestippeld). Klik nog een keer op Volgende ` +
             "(of druk op Enter): die gezichten worden dan <b>figurant</b>.");
        notYet();
        return;
      }
      save(open.map(f => { state.labels[f.face] = "other"; return labelRow(item, f, "other", "auto"); }));
    }
  }
  move(state.index + 1);
}

// Naar een ander item. Bij het laatste item zegt de app of er nog items open staan.
function move(index) {
  if (index >= state.data.items.length) {
    const open = state.data.items.filter(item => !isDone(item)).length;
    renderItem();
    if (open) warn(`Dit was het laatste item. Nog <b>${open}</b> item(s) zijn niet af: klik op ` +
                   "<b>Naar eerste item dat nog niet af is</b>.");
    return;
  }
  show(index);
}

function show(index) {
  $("last-choice").textContent = "";
  state.drawing = false;
  if (state.data.items[state.index]) dropUnchosenDrawn(state.data.items[state.index]);
  state.index = Math.max(0, Math.min(index, state.data.items.length - 1));
  const item = state.data.items[state.index];
  const open = item.faces.findIndex(f => !state.labels[f.face]);
  state.activeFace = open >= 0 ? open : 0;
  notYet();
  try { localStorage.setItem("label-index", String(state.index)); } catch (e) { /* niet nodig */ }
  renderItem();
  // het volgende beeld alvast laden, zodat het er meteen staat
  const after = state.data.items[state.index + 1];
  if (after) new Image().src = "../" + after.image;
}

// ---------- een gemist gezicht tekenen ----------
// Mist de computer een gezicht van een van de vier personen, dan tekent de labelaar er zelf een kader omheen.
// Zo'n gezicht heet <item-id>#getekend-<nummer> en wordt pas bewaard als de labelaar kiest wie het is.

const MIN_DRAWN = 6;   // kleinste breedte en hoogte (pixels van het beeld) van een getekend kader
let sketch = null;     // het kader dat nu getekend wordt: {x, y, el} (x en y in pixels op het scherm)

function toggleDrawing() { if (state.drawing) stopDrawing(); else startDrawing(); }
function startDrawing() {
  if (stopped || !haveName()) return;
  state.drawing = true;
  renderItem();
}
function stopDrawing() {
  state.drawing = false;
  if (sketch) { sketch.el.remove(); sketch = null; }
  renderItem();
}

// het kader tussen het punt waar de muis begon en waar de muis nu is, binnen het beeld
function sketchBox(event) {
  const r = $("frame").getBoundingClientRect();
  const cx = Math.min(Math.max(event.clientX - r.left, 0), r.width), cy = Math.min(Math.max(event.clientY - r.top, 0), r.height);
  return [Math.min(sketch.x, cx), Math.min(sketch.y, cy), Math.abs(cx - sketch.x), Math.abs(cy - sketch.y)];
}
$("frame").addEventListener("pointerdown", event => {
  if (!state.drawing || event.button !== 0) return;
  event.preventDefault();
  const r = $("frame").getBoundingClientRect();
  const el = document.createElement("div");
  el.className = "sketch";
  $("frame").appendChild(el);
  sketch = { x: event.clientX - r.left, y: event.clientY - r.top, el };
  $("frame").setPointerCapture(event.pointerId);
});
$("frame").addEventListener("pointermove", event => {
  if (!sketch) return;
  const [x, y, w, h] = sketchBox(event);
  Object.assign(sketch.el.style, { left: x + "px", top: y + "px", width: w + "px", height: h + "px" });
});
$("frame").addEventListener("pointerup", event => {
  if (!sketch) return;
  const item = state.data.items[state.index], scale = item.width / $("frame").getBoundingClientRect().width;
  const [sx, sy, sw, sh] = sketchBox(event).map(v => v * scale);
  sketch.el.remove();
  sketch = null;
  const x = Math.max(0, Math.round(sx)), y = Math.max(0, Math.round(sy));
  const w = Math.min(Math.round(sw), item.width - x), h = Math.min(Math.round(sh), item.height - y);
  if (w < MIN_DRAWN || h < MIN_DRAWN) return;   // te klein: waarschijnlijk alleen een klik
  const first = item.faces[0];
  const face = { face: `${item.id}#getekend-${Date.now()}`, box: [x, y, w, h], source: first.source,
                 frame: first.frame ?? "", drawn: true };
  (state.drawn[item.id] = state.drawn[item.id] || []).push(face);
  state.drawing = false;
  state.activeFace = facesOf(item).length - 1;
  notYet();
  renderItem();
});
$("frame").addEventListener("pointercancel", () => { if (sketch) { sketch.el.remove(); sketch = null; } });

// Het getekende kader dat nu aan de beurt is weghalen (ook uit labels.csv als er al een keuze voor was).
function removeDrawn() {
  const item = state.data.items[state.index], face = facesOf(item)[state.activeFace];
  if (stopped || !face || !face.drawn) return;
  if (state.labels[face.face]) {
    if (!haveName()) return;
    delete state.labels[face.face];
    save([labelRow(item, face, "", "getekend")]);
  }
  state.drawn[item.id] = (state.drawn[item.id] || []).filter(f => f !== face);
  const open = item.faces.findIndex(f => !state.labels[f.face]);
  state.activeFace = open >= 0 ? open : 0;
  renderItem();
}

// Getekende kaders waarvoor nog niets gekozen is, bestaan alleen op deze pagina; bij een ander item vervallen ze.
function dropUnchosenDrawn(item) {
  if (state.drawn[item.id]) state.drawn[item.id] = state.drawn[item.id].filter(f => state.labels[f.face]);
}

// Een getekend gezicht uit een opgeslagen rij, of null als de rij niet bij een item van deze items.json past.
function drawnFaceOf(row) {
  const item = state.data.items.find(i => i.id === row.item);
  if (!item || row.how !== "getekend" || !String(row.face).startsWith(item.id + "#getekend-")) return null;
  const [x, y, w, h] = [row.x, row.y, row.w, row.h].map(Number);
  if (!(x >= 0 && y >= 0 && w >= 4 && h >= 4 && x + w <= item.width && y + h <= item.height)) return null;
  return { face: row.face, box: [x, y, w, h], source: item.faces[0].source, frame: item.faces[0].frame ?? "", drawn: true };
}

// Zet de opgeslagen labels (uit app.py) en de keuzes die nog niet opgeslagen zijn op de pagina, samen met de
// getekende gezichten. Getekende kaders zonder keuze die alleen op deze pagina bestaan, blijven staan.
function applyStored(stored) {
  const pending = Object.entries(state.drawn).map(([id, faces]) => [id, faces.filter(f => !state.labels[f.face])]);
  state.labels = {};
  state.drawn = {};
  const addDrawn = row => {
    const face = drawnFaceOf(row);
    if (!face) return;
    const list = state.drawn[row.item] = state.drawn[row.item] || [];
    if (!list.some(f => f.face === face.face)) list.push(face);
  };
  Object.entries(stored).forEach(([face, row]) => { state.labels[face] = row.label; if (row.how === "getekend") addDrawn(row); });
  unsaved.forEach(row => {
    if (row.label) { state.labels[row.face] = row.label; if (row.how === "getekend") addDrawn(row); return; }
    delete state.labels[row.face];
    if (state.drawn[row.item]) state.drawn[row.item] = state.drawn[row.item].filter(f => f.face !== row.face);
  });
  pending.forEach(([id, faces]) => faces.forEach(f => {
    const list = state.drawn[id] = state.drawn[id] || [];
    if (!list.some(g => g.face === f.face)) list.push(f);
  }));
  Object.values(state.drawn).forEach(list => list.sort((a, b) => (a.face < b.face ? -1 : 1)));
  const item = state.data.items[state.index];
  if (item && state.activeFace >= facesOf(item).length) state.activeFace = 0;
}

function firstOpen() {
  const index = state.data.items.findIndex(item => !isDone(item));
  if (index >= 0) show(index); else renderProgress();   // alles af: de groene balk zegt wat je nu doet
}

document.addEventListener("keydown", event => {
  if (tourStep >= 0) {   // de uitleg staat open: alleen bladeren door de uitleg
    if (event.key === "Escape") closeTour();
    else if (event.key === "ArrowRight" || event.key === "Enter") tourGo(tourStep + 1);
    else if (event.key === "ArrowLeft") tourGo(tourStep - 1);
    if (event.key !== "Tab") event.preventDefault();
    return;
  }
  if (event.target.id === "labeler" || !state.data) return;  // tijdens het typen van je naam
  // Een ingedrukt gehouden toets telt maar één keer, en toetscombinaties (Ctrl, Cmd, Alt) doen niets.
  if (event.repeat || event.ctrlKey || event.metaKey || event.altKey) return;
  // Ook de cijfertoets zelf telt: op een AZERTY-toetsenbord geeft de cijferrij zonder Shift andere tekens, en op het
  // numerieke blok zonder NumLock geeft bijvoorbeeld 4 een pijltje.
  const digit = (/^(?:Digit|Numpad)([0-9])$/.exec(event.code || "") || [])[1];
  const choice = state.data.choices.find(c => c.shortcut === event.key || c.shortcut === digit);
  if (event.key === "Escape" && state.drawing) { stopDrawing(); event.preventDefault(); }
  else if (event.key === "t" || event.key === "T") { toggleDrawing(); event.preventDefault(); }
  else if ((event.key === "Delete" || event.key === "Backspace") && facesOf(state.data.items[state.index])[state.activeFace].drawn) {
    removeDrawn(); event.preventDefault();
  }
  else if (choice) { choose(state.activeFace, choice.key); event.preventDefault(); }
  else if (event.key === "Enter") { event.preventDefault(); next(); }
  else if (event.key === "ArrowRight") { show(state.index + 1); event.preventDefault(); }    // alleen bladeren
  else if (event.key === "ArrowLeft") { show(state.index - 1); event.preventDefault(); }
  else if (event.key === " ") { event.preventDefault(); }  // spatie doet niets (ook niet op een knop)
  else if (event.key === "l" || event.key === "L") { $("brighter").checked = !$("brighter").checked; setBrighter(); }
});

// Een aangeklikte knop houdt geen focus, zodat Enter of spatie hem niet nog een keer indrukt.
document.addEventListener("click", event => {
  const button = event.target.closest("button, input[type=checkbox]");
  if (button) button.blur();
});

// Haal de opgeslagen labels opnieuw op als de pagina weer in beeld komt. Keuzes die nog niet
// opgeslagen zijn, gaan voor.
async function refreshLabels() {
  if (!state.data || stopped || document.visibilityState !== "visible") return;
  try {
    const response = await fetch("/api/labels", { cache: "no-store" });
    if (!response.ok) return;   // de labels die al op het scherm staan, blijven staan
    applyStored(await response.json());
    renderItem();
  } catch (e) { /* de app draait even niet; bij de volgende keuze verschijnt de rode balk */ }
}
document.addEventListener("visibilitychange", refreshLabels);
window.addEventListener("focus", refreshLabels);

// Waarschuwing bij het sluiten van de pagina als er nog keuzes niet opgeslagen zijn.
window.addEventListener("beforeunload", event => {
  if (unsaved.size && !stopped) { event.preventDefault(); event.returnValue = ""; }
});

// "Beeld lichter": hoe donkerder het gezicht in het kader, hoe sterker het beeld wordt opgelicht (factor 1 tot 5),
// zodat het gezicht ongeveer even licht wordt als een normaal belicht gezicht. Een goed belicht gezicht blijft zoals het is.
// Er wordt altijd gemeten voor het item en het gezicht die nu op het scherm staan: staat het beeld van dit item er nog
// niet, dan meet de load-listener hieronder zodra het beeld er is.
function updateBrightness() {
  if (!$("brighter").checked || !state.data) return;
  const image = $("image"), item = state.data.items[state.index];
  if (!(image.complete && image.naturalWidth && shows(image, item.image))) return;
  const [x, y, w, h] = facesOf(item)[state.activeFace].box;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 32;
  const context = canvas.getContext("2d");
  context.drawImage(image, x, y, w, h, 0, 0, 32, 32);
  const pixels = context.getImageData(0, 0, 32, 32).data;
  let sum = 0;
  for (let i = 0; i < pixels.length; i += 4) sum += 0.299 * pixels[i] + 0.587 * pixels[i + 1] + 0.114 * pixels[i + 2];
  const mean = sum / (pixels.length / 4);
  const factor = Math.min(5, Math.max(1, 120 / Math.max(mean, 8)));
  document.documentElement.style.setProperty("--bright", factor.toFixed(2));
}
$("image").addEventListener("load", () => updateBrightness());

function setBrighter() {
  document.body.classList.toggle("bright", $("brighter").checked);
  updateBrightness();
  try { localStorage.setItem("brighter", $("brighter").checked ? "1" : "0"); } catch (e) { /* niet nodig */ }
}

// ---------- korte uitleg (rondleiding) ----------
// De eerste keer opent de uitleg vanzelf; daarna kan de labelaar hem openen met de knop Uitleg bovenaan.
// Elke stap laat één deel van het scherm zien; de rest van het scherm wordt donker.

const TOUR = [
  { title: "Welkom", text: "In deze app geef je bij gezichten uit de film <i>Das Boot</i> aan wie het is. Deze uitleg " +
    "duurt ongeveer een minuut. Je kunt hem later altijd weer openen met de knop <b>Uitleg</b> bovenaan." },
  { target: "#labeler", title: "Jouw naam", text: "Vul hier eerst je naam in en druk op Enter. Bij elke keuze bewaart " +
    "de app wie die keuze gemaakt heeft; zonder naam bewaart de app niets." },
  { target: ".refs", title: "De vier personen", text: "Hier staan foto's van de vier acteurs, om mee te vergelijken. " +
    "Houd de muis op een foto om die foto groter te zien." },
  { target: "#frame", title: "Het beeld", text: "Hier staat het beeld. De computer heeft om alles wat op een gezicht " +
    "lijkt een kader gezet. Het <b>gele kader</b> is het gezicht waarvoor je nu kiest. Een kader betekent niet altijd " +
    "dat er echt een gezicht staat: soms staat er een lamp of een hand in." },
  { target: "#zoom", title: "Uitvergroting", text: "Hier zie je het gezicht in het gele kader nog een keer groot. " +
    "Gezichten in de video's zijn vaak klein; hier zie je ze beter." },
  { target: "#faces", title: "Kiezen", text: "Kies hier wie het is, met de muis of met de toetsen 1 t/m 7. " +
    "Kies <b>1 t/m 4</b> alleen als je zeker weet wie het is. <b>5 Figurant</b>: een gezicht dat je goed ziet, maar " +
    "het is niet een van de vier. <b>6 Geen gezicht</b>: alleen als er zeker geen gezicht in het kader staat. " +
    "<b>7 Weet niet</b>: als je twijfelt." },
  { target: ".item-head", title: "Stukjes video", text: "De meeste items zijn een stukje video: één gezicht dat de " +
    "computer een tijdje gevolgd heeft. Je ziet daar één beeld van, en je keuze geldt voor het hele stukje. Na je " +
    "keuze gaat de app vanzelf door. Vergist? Druk op <b>←</b> en kies opnieuw." },
  { target: ".nav", title: "Foto's en stills", text: "Op een foto of een still (een losse foto uit de film) staan soms " +
    "meer gezichten, elk met een nummer. Kies dan voor elk gezicht en klik daarna op <b>Volgende</b>. Een gezicht " +
    "waarvoor je niets koos, wordt dan figurant." },
  { target: "#draw", title: "Een gemist gezicht", text: "Bij een stukje video staan andere gezichten die de computer ook " +
    "vond met een dun grijs kader; die komen in een eigen stukje aan de beurt. Zie je een gezicht van een van de vier " +
    "personen zonder enig kader? " +
    "Klik dan op <b>Gemist gezicht tekenen</b> (of druk op <b>T</b>), sleep met de muis een kader om het gezicht en " +
    "kies wie het is. Een verkeerd getekend kader haal je weg met <b>Weghalen</b>. Andere gezichten zonder kader hoef " +
    "je niet te tekenen." },
  { target: ".brighter", title: "Beeld lichter", text: "Veel beelden uit de film zijn erg donker. <b>Beeld lichter</b> " +
    "staat daarom aan. Met de toets <b>L</b> zet je het uit en weer aan." },
  { target: "#progress", title: "Hoe ver je bent", text: "Hier zie je per deel hoe ver je bent. Elke keuze wordt " +
    "meteen bewaard: je kunt altijd stoppen en later verdergaan waar je gebleven was." },
  { title: "Klaar om te beginnen", text: "Stuur het bestand <b>labels.csv</b> aan het eind, en ook tussendoor, naar " +
    "Marc (zie de handleiding, stap 6). Twijfel je ergens over? Kies dan <b>7 Weet niet</b>. Veel succes!" },
];
let tourStep = -1;   // -1: de uitleg staat niet open

function openTour() {
  if (state.drawing) stopDrawing();
  tourStep = 0;
  $("tour").classList.remove("hidden");
  renderTour();
}
function closeTour() {
  tourStep = -1;
  $("tour").classList.add("hidden");
  try { localStorage.setItem("uitleg-gezien", "1"); } catch (e) { /* niet nodig */ }
  if (state.data && !nameOk()) $("labeler").focus();
}
function tourGo(step) {
  if (step < 0) return;
  if (step >= TOUR.length) { closeTour(); return; }
  tourStep = step;
  renderTour();
}
function renderTour() {
  const step = TOUR[tourStep], target = step.target && document.querySelector(step.target);
  const visible = target && target.getClientRects().length && target.getBoundingClientRect().width > 0;
  $("tour-count").textContent = `Uitleg ${tourStep + 1} van ${TOUR.length}`;
  $("tour-title").textContent = step.title;
  $("tour-text").innerHTML = step.text;
  $("tour-back").disabled = tourStep === 0;
  $("tour-next").textContent = tourStep === TOUR.length - 1 ? "Begin met labelen" : "Volgende →";
  const spot = $("tour-spot"), bubble = $("tour-bubble"), gap = 12, pad = 6;
  $("tour").classList.toggle("dim", !visible);
  spot.classList.toggle("hidden", !visible);
  document.querySelectorAll(".tour-shade").forEach(shade => shade.classList.toggle("hidden", !visible));
  // de uitleg naast het deel van het scherm waar die over gaat, altijd helemaal in beeld
  const bw = bubble.offsetWidth, bh = bubble.offsetHeight, W = innerWidth, H = innerHeight;
  let left = (W - bw) / 2, top = (H - bh) / 2;
  if (visible) {
    const r = target.getBoundingClientRect();
    const L = Math.max(0, r.left - pad), T = Math.max(0, r.top - pad);
    const R = Math.min(innerWidth, r.right + pad), B = Math.min(innerHeight, r.bottom + pad);
    Object.assign(spot.style, { left: L + "px", top: T + "px", width: R - L + "px", height: B - T + "px" });
    // vier donkere vlakken rond het deel van het scherm waar de uitleg over gaat
    const [above, below, left_, right_] = document.querySelectorAll(".tour-shade");
    Object.assign(above.style, { left: "0", top: "0", width: "100vw", height: T + "px" });
    Object.assign(below.style, { left: "0", top: B + "px", width: "100vw", height: Math.max(0, innerHeight - B) + "px" });
    Object.assign(left_.style, { left: "0", top: T + "px", width: L + "px", height: B - T + "px" });
    Object.assign(right_.style, { left: R + "px", top: T + "px", width: Math.max(0, innerWidth - R) + "px", height: B - T + "px" });
    const places = [[r.right + gap, r.top], [r.left - gap - bw, r.top], [r.left, r.bottom + gap], [r.left, r.top - gap - bh]];
    const fits = ([x, y]) => x >= 8 && x + bw <= W - 8 && y + Math.min(bh, 40) <= H - 8;
    const place = places.find(fits);
    if (place) [left, top] = place;
  }
  bubble.style.left = Math.max(8, Math.min(left, W - bw - 8)) + "px";
  bubble.style.top = Math.max(8, Math.min(top, H - bh - 8)) + "px";
  $("tour-next").focus();
}
$("tour-open").onclick = openTour;
$("tour-next").onclick = () => tourGo(tourStep + 1);
$("tour-back").onclick = () => tourGo(tourStep - 1);
$("tour-skip").onclick = closeTour;
window.addEventListener("resize", () => { if (tourStep >= 0) renderTour(); });

// ---------- starten ----------

async function start() {
  let stored = {};
  try {
    state.data = await (await fetch("../items.json", { cache: "no-store" })).json();
    const response = await fetch("/api/labels", { cache: "no-store" });
    stored = await response.json();
    if (!response.ok) throw new Error(stored.error || response.statusText);
    state.labelsFile = (await (await fetch("/api/ping", { cache: "no-store" })).json()).labels || "labels.csv";
  } catch (error) {
    $("error").textContent = "De gegevens konden niet geladen worden. Start de app met START_MAC.command of " +
                             "START_WINDOWS.bat (zie de handleiding). (" + error.message + ")";
    $("error").classList.remove("hidden");
    return;
  }
  try { $("labeler").value = localStorage.getItem("labeler") || ""; } catch (e) { /* niet nodig */ }
  $("labeler").oninput = () => {
    try { localStorage.setItem("labeler", $("labeler").value.trim()); } catch (e) { /* niet nodig */ }
    if ($("error").textContent.startsWith("Vul eerst") && nameOk()) $("error").classList.add("hidden");
  };
  // Enter of Esc in het naamvak: klaar met de naam (daarna werken de sneltoetsen weer)
  $("labeler").onkeydown = event => {
    if (event.key === "Enter" || event.key === "Escape") { event.preventDefault(); $("labeler").blur(); }
  };
  $("previous").onclick = () => show(state.index - 1);
  $("next").onclick = next;
  $("first-open").onclick = firstOpen;
  $("draw").onclick = toggleDrawing;
  $("brighter").onchange = setBrighter;
  try { $("brighter").checked = localStorage.getItem("brighter") !== "0"; } catch (e) { $("brighter").checked = true; }
  setBrighter();
  renderReferences();
  // keuzes die bij een vorige keer niet opgeslagen konden worden: nu alsnog opslaan
  try {
    const faces = new Map(state.data.items.flatMap(item => item.faces.map(face => [face.face, face])));
    for (const row of JSON.parse(localStorage.getItem("unsaved") || "[]")) {
      // hoort bij een oudere versie van items.json: het gezicht bestaat niet meer, of hetzelfde id staat nu bij
      // een ander beeld of kader (dezelfde controle als voor labels.csv in app.py)
      const face = faces.get(row.face) || drawnFaceOf(row);
      if (!face || String(row.source) !== String(face.source) || String(row.frame ?? "") !== String(face.frame ?? "") ||
          [row.x, row.y, row.w, row.h].join() !== face.box.join()) continue;
      if (row.label && !state.data.choices.some(c => c.key === row.label)) continue;   // een keuze die niet meer bestaat
      unsaved.set(row.face, row);
    }
  } catch (e) { /* niet nodig */ }
  applyStored(stored);
  try { localStorage.setItem("active-page", pageId); } catch (e) { /* niet nodig */ }  // een oudere pagina stopt nu
  if (unsaved.size) await save([]);
  let saved = null;
  try { saved = localStorage.getItem("label-index"); } catch (e) { /* niet nodig */ }
  if (saved !== null) show(Number(saved)); else firstOpen();
  if (!nameOk()) $("labeler").focus();
  let seen = true;
  try { seen = localStorage.getItem("uitleg-gezien") === "1"; } catch (e) { /* zonder opslag in de browser: geen uitleg */ }
  if (!seen) openTour();
}

start();
