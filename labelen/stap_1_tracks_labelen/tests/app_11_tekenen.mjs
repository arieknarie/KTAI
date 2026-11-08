// Grijze kaders en getekende gezichten. Bij een track staan de andere gezichten die de computer in hetzelfde beeld vond
// als dunne grijze kaders. Mist de computer een gezicht, dan tekent de labelaar er zelf een kader omheen (met echte
// muisbewegingen), kiest wie het is, of haalt het kader weer weg; bij een track en bij een still. app.py controleert
// elk getekend kader.
import { connect, check, skip, sleep, rows } from "./lib.mjs";

const page = await connect();
await page.fresh();

// ---- bij een track: de andere gevonden gezichten dun en grijs, niet aan te klikken, met een uitleg erbij
const withOthers = await page.find(`i.kind === "track" && (i.others || []).length >= 2`);
if (withOthers < 0) {
  skip("grijze kaders bij een track", "items.json heeft geen track met andere gezichten in hetzelfde beeld");
} else {
  await page.show(withOthers);
  check("bij een track staan de andere gevonden gezichten als grijze kaders", await page.js(`(() => {
    const item = state.data.items[state.index], boxes = document.querySelectorAll("#frame .box.other");
    return boxes.length === item.others.length && [...boxes].every(b => getComputedStyle(b).pointerEvents === "none"); })()`));
  check("bij een track met grijze kaders legt de uitleg rechts die kaders uit", (await page.text("instruction")).includes("Grijze stippelkaders"));
}

// ---- een gemist gezicht tekenen bij een track
const track = await page.find(`i.kind === "track"`, 2);
await page.show(track);
const frame = () => page.js(`(() => { const r = document.getElementById("frame").getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()`);
const [fx, fy] = await frame();
const faceCount = () => page.js(`facesOf(state.data.items[state.index]).length`);

// zonder naam kan je niet tekenen
await page.js(`(() => { const i = document.getElementById("labeler"); i.value = ""; i.dispatchEvent(new Event("input")); return true; })()`);
await page.key("t"); await sleep(200);
check("zonder naam kan je niet tekenen", !(await page.js("state.drawing")) && (await page.text("error")).startsWith("Vul eerst"));
await page.js(`(() => { const i = document.getElementById("labeler"); i.value = "Tester"; i.dispatchEvent(new Event("input")); i.blur(); return true; })()`);

await page.key("t"); await sleep(200);
check("T zet tekenen aan", await page.js(`state.drawing && document.getElementById("frame").classList.contains("drawing")`));
const before = rows().length;
await page.key("7"); await sleep(300);
check("tijdens het tekenen kiest een cijfertoets niets", rows().length === before);
await page.key("Escape"); await sleep(200);
check("Esc stopt het tekenen", !(await page.js("state.drawing")));
await page.key("t"); await sleep(150);
await page.drag(fx + 20, fy + 20, fx + 20, fy + 20); await sleep(300);
check("een klik zonder te slepen maakt geen getekend gezicht", (await faceCount()) === 1);
await page.key("T"); await sleep(150);
check("T zet tekenen ook weer uit", !(await page.js("state.drawing")));

await page.key("t"); await sleep(150);
await page.drag(fx + 10, fy + 10, fx + 90, fy + 100); await sleep(400);
const drawn = await page.js(`(() => { const item = state.data.items[state.index], f = facesOf(item)[state.activeFace];
  return { drawn: !!f.drawn, box: f.box, n: facesOf(item).length, drawing: state.drawing,
           noFace: !!document.querySelector('#faces button[data-label="no_face"]'),
           tabs: [...document.querySelectorAll("#face-tabs button")].map(b => b.textContent),
           title: document.querySelector("#faces .title").textContent, instruction: document.getElementById("instruction").textContent }; })()`);
check("na het slepen staat er een getekend gezicht, en dat is aan de beurt", drawn.drawn && drawn.n === 2 && !drawn.drawing, JSON.stringify(drawn.box));
check("bij een getekend gezicht is er geen knop Geen gezicht", !drawn.noFace);
check("de knopjes heten 'track' (het gele kader) en '+1' (het getekende gezicht)", JSON.stringify(drawn.tabs) === JSON.stringify(["track", "+1"]), JSON.stringify(drawn.tabs));
check("een getekend gezicht zonder keuze: de titel en de uitleg rechts zeggen dat het getekend is",
  drawn.title.startsWith("Getekend gezicht 1") && drawn.instruction.startsWith("Kies wie het getekende gezicht is"), `${drawn.title} | ${drawn.instruction}`);
await page.ready();
await page.key("4", { code: "Digit4" }); await sleep(700); await page.saved();
const saved = rows().filter(r => r.face.includes("#getekend-"));
check("de keuze voor het getekende gezicht wordt bewaard (how = getekend)", saved.length === 1 && saved[0].label === "Werner" && saved[0].how === "getekend", JSON.stringify(saved));
check("na een getekend gezicht gaat de app niet door, en het gele kader is weer aan de beurt",
  (await page.index()) === track && (await page.js("state.activeFace")) === 0);

// een tweede kader zonder keuze: Volgende waarschuwt, Delete haalt het weg zonder iets te bewaren
await page.key("t"); await sleep(150);
await page.drag(fx + 120, fy + 20, fx + 170, fy + 80); await sleep(400);
await page.ready();
await page.key("Enter"); await sleep(300);
check("Volgende met een getekend kader zonder keuze waarschuwt", (await page.text("instruction")).startsWith("Kies eerst wie het getekende"));
// De pagina haalt de labels opnieuw op bij app.py (dat gebeurt als het venster weer in beeld komt). Het merkteken in
// state.labels verdwijnt zodra dat gebeurd is; het getekende kader zonder keuze moet dan blijven staan.
await page.js(`state.labels["merkteken-test"] = "x"; window.dispatchEvent(new Event("focus")); true`);
const refreshed = await page.until(`!("merkteken-test" in state.labels)`, 5000);
check("een getekend kader zonder keuze blijft staan als de pagina de labels opnieuw ophaalt",
  refreshed && (await faceCount()) === 3 && (await page.js("facesOf(state.data.items[state.index])[state.activeFace].drawn === true")));
const n1 = rows().length;
await page.key("Delete"); await sleep(400);
check("Delete haalt een getekend kader zonder keuze weg", (await faceCount()) === 2 && rows().length === n1);
await page.key("t"); await sleep(150);
await page.drag(fx + 120, fy + 20, fx + 170, fy + 80); await sleep(400);
await page.key("Backspace"); await sleep(400);
check("Backspace haalt een getekend kader ook weg", (await faceCount()) === 2 && rows().length === n1);

// een getekend kader zonder keuze bestaat alleen op de pagina: bij een ander item vervalt het
await page.key("t"); await sleep(150);
await page.drag(fx + 120, fy + 20, fx + 170, fy + 80); await sleep(400);
await page.key("ArrowRight"); await page.ready();
await page.key("ArrowLeft"); await page.ready();
check("een getekend kader zonder keuze vervalt bij een ander item", (await faceCount()) === 2 && rows().length === n1);

// na herladen staat het bewaarde getekende gezicht er weer
await page.reload();
await page.show(track);
check("na herladen staat het getekende gezicht er weer, met de keuze",
  await page.js(`(() => { const f = facesOf(state.data.items[state.index])[1]; return !!f && f.drawn && state.labels[f.face] === "Werner"; })()`));
// een bewaard getekend gezicht weghalen: ook weg uit labels.csv
await page.js(`selectFace(1); true`); await page.ready();
await page.js(`document.getElementById("remove").click(); true`); await sleep(700); await page.saved();
check("Weghalen haalt een bewaard getekend gezicht ook uit labels.csv", !rows().some(r => r.face.includes("#getekend-")) && (await faceCount()) === 1);

// ---- de controles in app.py: een getekend kader moet binnen het beeld liggen, mag niet te klein zijn (minstens 4 bij 4
// pixels), kan geen Geen gezicht zijn, moet bij een bestaand item horen; bestand en frame komen altijd uit items.json
const item = await page.js(`(() => { const i = state.data.items[${track}]; return { id: i.id, w: i.width, h: i.height, source: i.faces[0].source, frame: i.faces[0].frame ?? "" }; })()`);
const post = rowsToSend => page.js(`fetch("/api/labels", { method: "POST", headers: { "Content-Type": "application/json" },
  body: JSON.stringify(${JSON.stringify(rowsToSend)}) }).then(r => r.json())`);
const base = { item: item.id, label: "Johann", how: "getekend", labeler: "Tester", source: item.source, frame: item.frame };
const result = await post([
  { ...base, face: item.id + "#getekend-1", x: item.w - 10, y: 5, w: 30, h: 30 },                    // buiten het beeld
  { ...base, face: item.id + "#getekend-2", x: 5, y: 5, w: 30, h: 30, label: "no_face" },            // Geen gezicht kan niet
  { ...base, face: "bestaat-niet#getekend-3", x: 5, y: 5, w: 30, h: 30 },                            // onbekend item
  { ...base, face: item.id + "#getekend-5", x: 5, y: 5, w: 3, h: 30 },                               // te klein
  { ...base, face: item.id + "#getekend-4", x: 5, y: 5, w: 30, h: 30, source: "iets anders", frame: 1 },   // goed
]);
check("app.py weigert een getekend kader buiten het beeld, te klein, met Geen gezicht of bij een onbekend item",
  (result.skipped || []).length === 4 && result.saved === 1, JSON.stringify(result));
const stored = rows().find(r => r.face === item.id + "#getekend-4");
check("app.py neemt bestand en frame van een getekend gezicht uit items.json",
  !!stored && stored.source === item.source && stored.frame === String(item.frame) && [stored.x, stored.y, stored.w, stored.h].join() === "5,5,30,30",
  JSON.stringify(stored));
await post([{ ...base, face: item.id + "#getekend-4", x: 5, y: 5, w: 30, h: 30, label: "" }]);

// ---- een gemist gezicht tekenen bij een foto of still: het getekende gezicht telt door na de gezichten van de computer,
// en na de keuze is het eerste gezicht van de computer zonder keuze weer aan de beurt
const still = await page.find(`i.kind !== "track" && i.faces.length >= 2`);
if (still < 0) {
  skip("een gemist gezicht tekenen bij een still", "items.json heeft geen foto of still met 2 of meer gezichten");
} else {
  await page.show(still);
  const [sx, sy] = await frame();
  await page.key("t"); await sleep(150);
  await page.drag(sx + 10, sy + 10, sx + 70, sy + 80); await sleep(400);
  const info = await page.js(`(() => { const item = state.data.items[state.index];
    return { n: facesOf(item).length, computer: item.faces.length, active: state.activeFace, id: item.id,
             tab: [...document.querySelectorAll("#face-tabs button")].at(-1)?.textContent,
             title: document.querySelector("#faces .title").textContent }; })()`);
  check("bij een still telt een getekend gezicht door na de gezichten van de computer",
    info.n === info.computer + 1 && info.active === info.computer && info.tab === String(info.computer + 1) &&
    info.title.startsWith(`Gezicht ${info.computer + 1} (getekend)`), JSON.stringify(info));
  await page.ready();
  await page.key("3", { code: "Digit3" }); await sleep(500); await page.saved();
  const own = rows().filter(r => r.item === info.id && r.face.includes("#getekend-"));
  check("na een getekend gezicht bij een still is het eerste gezicht zonder keuze weer aan de beurt",
    (await page.index()) === still && (await page.js("state.activeFace")) === 0 && own.length === 1 && own[0].label === "Johann",
    JSON.stringify(own));
  // opruimen: het getekende gezicht weer weghalen
  await page.js(`selectFace(facesOf(state.data.items[state.index]).length - 1); true`); await page.ready();
  await page.js(`document.getElementById("remove").click(); true`); await sleep(500); await page.saved();
}
page.close();
