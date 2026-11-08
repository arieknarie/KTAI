// Beeld lichter meet steeds het gezicht dat in beeld is (ook als het beeld kleiner is opgeslagen dan de video),
// "Net gekozen" verdwijnt na het bladeren, cijfers werken op een AZERTY-toetsenbord en op het numerieke blok,
// achtergebleven keuzes voor een ander kader worden niet opgeslagen, de pagina komt niet ongezien uit de cache,
// en een labels.csv in een andere tekenset geeft de bekende uitleg.
import fs from "node:fs";
import path from "node:path";
import { connect, check, sleep, rows, DEMO, url } from "./lib.mjs";

const page = await connect();
await page.fresh();

// De factor van Beeld lichter zoals app.js die zou moeten uitrekenen voor het item en het gezicht in beeld:
// het gemiddelde licht van het gezicht in het kader (het kader in pixels van de video, omgerekend naar het opgeslagen
// beeld), en daaruit een factor van 1 tot 5.
const expected = () => page.js(`(() => { const item = state.data.items[state.index], img = document.getElementById("image");
  if (!(img.complete && img.naturalWidth && shows(img, item.image))) return "laden";
  const [x, y, w, h] = facesOf(item)[state.activeFace].box, scale = img.naturalWidth / item.width;
  const c = document.createElement("canvas"); c.width = c.height = 32;
  const g = c.getContext("2d"); g.drawImage(img, x * scale, y * scale, w * scale, h * scale, 0, 0, 32, 32);
  const p = g.getImageData(0, 0, 32, 32).data;
  let s = 0; for (let i = 0; i < p.length; i += 4) s += 0.299 * p[i] + 0.587 * p[i + 1] + 0.114 * p[i + 2];
  return Math.min(5, Math.max(1, 120 / Math.max(s / (p.length / 4), 8))).toFixed(2); })()`);
const actual = () => page.js(`document.documentElement.style.getPropertyValue("--bright")`);
const smaller = () => page.js(`document.getElementById("image").naturalWidth !== state.data.items[state.index].width`);

// ---- Beeld lichter: na elke keuze hoort de factor bij het gezicht dat dan in beeld is (30 keuzes achter elkaar)
const start = await page.find(`i.kind === "track"`, 40);
await page.show(start);
let wrong = 0, measured = 0, small = 0;
// Na elke keuze: wachten tot het beeld van het volgende item er staat, en daarna nog even, zodat de load-listener van
// app.js zeker gedraaid heeft (anders zou de test de factor meten voordat app.js die kon uitrekenen).
const loaded = `(() => { const img = document.getElementById("image");
  return img.complete && img.naturalWidth > 0 && shows(img, state.data.items[state.index].image); })()`;
for (let n = 0; n < 30; n++) {
  await page.key("7");
  await page.until(loaded, 5000); await sleep(450);
  const e = await expected(), a = await actual();
  if (e === "laden") continue;
  measured++;
  if (e !== a) wrong++;
  if (await smaller()) small++;
}
check("Beeld lichter meet steeds het gezicht dat in beeld is", measured >= 20 && wrong === 0,
  `${wrong} fout van ${measured} (waarvan ${small} met een kleiner opgeslagen beeld)`);

// ---- Beeld lichter rekent het kader om als het opgeslagen beeld kleiner is dan de video (bijvoorbeeld bij 4K):
// doe alsof de video twee keer zo groot was (maat en kaders van het item x 2); de factor moet dan hetzelfde blijven.
// Gekozen wordt een item waarbij het verkeerde stuk van het beeld (kader x 2, niet omgerekend) een andere factor geeft.
const scaled = await page.js(`(async () => {
  const items = state.data.items, img = document.getElementById("image");
  const factorAt = (x, y, w, h) => { const c = document.createElement("canvas"); c.width = c.height = 32;
    const g = c.getContext("2d"); g.drawImage(img, x, y, w, h, 0, 0, 32, 32); const p = g.getImageData(0, 0, 32, 32).data;
    let s = 0; for (let i = 0; i < p.length; i += 4) s += 0.299 * p[i] + 0.587 * p[i + 1] + 0.114 * p[i + 2];
    return Math.min(5, Math.max(1, 120 / Math.max(s / (p.length / 4), 8))).toFixed(2); };
  for (let n = 0; n < items.length - 1; n++) {
    const item = items[n];
    if (item.kind !== "track") continue;
    show(n);
    await new Promise(r => { if (img.complete && img.naturalWidth && shows(img, item.image)) r(); else img.addEventListener("load", r, { once: true }); });
    const k = img.naturalWidth / item.width, [x, y, w, h] = item.faces[0].box;
    if ((2 * x + 2 * w) * k > img.naturalWidth || (2 * y + 2 * h) * k > img.naturalHeight) continue;
    updateBrightness();
    const real = document.documentElement.style.getPropertyValue("--bright");
    if (factorAt(2 * x * k, 2 * y * k, 2 * w * k, 2 * h * k) === real) continue;   // zou het verschil niet laten zien
    const keep = { width: item.width, height: item.height, box: item.faces[0].box };
    item.width *= 2; item.height *= 2; item.faces[0].box = item.faces[0].box.map(v => v * 2);
    updateBrightness();
    const twice = document.documentElement.style.getPropertyValue("--bright");
    item.width = keep.width; item.height = keep.height; item.faces[0].box = keep.box;
    updateBrightness();
    return { item: n, real, twice };
  }
  return null; })()`);
check("Beeld lichter rekent het kader om naar de maat van het opgeslagen beeld", !!scaled && scaled.real === scaled.twice, JSON.stringify(scaled));

// ---- "Net gekozen" staat alleen bij het item direct na de keuze
// (voorbij de 30 items van hierboven, zodat er nog niets gekozen is)
const track = await page.find(`i.kind === "track" && state.data.items[n + 1].kind === "track" && n > ${start + 35}`, 3);
await page.show(track);
await page.key("7"); await sleep(600);
check("na een keuze staat er wat je net gekozen hebt", (await page.text("last-choice")).startsWith("Net gekozen"));
await page.key("ArrowRight"); await page.ready();
check("na verder bladeren is 'Net gekozen' weg", (await page.text("last-choice")) === "");

// ---- cijfers via de toets zelf: AZERTY '&' op de toets 1, en 4 op het numerieke blok zonder NumLock (dan 'ArrowLeft')
const digits = await page.find(`i.kind === "track" && state.data.items[n + 1].kind === "track" && n > ${track + 3}`, 3);
await page.show(digits);
let before = rows().length;
await page.key("&", { code: "Digit1" }); await sleep(600); await page.saved();
check("AZERTY: de cijferrij zonder Shift kiest ook", rows().length === before + 1 && rows().at(-1).label === "DerAlte", JSON.stringify(rows().at(-1)));
await page.ready();
before = rows().length;
const at = await page.index();
await page.key("ArrowLeft", { code: "Numpad4" }); await sleep(600); await page.saved();
check("numeriek blok zonder NumLock: 4 kiest Werner in plaats van terug te bladeren",
  rows().length === before + 1 && rows().at(-1).label === "Werner" && (await page.index()) === at + 1, JSON.stringify(rows().at(-1)));

// ---- een achtergebleven keuze (in de browser) voor hetzelfde gezicht-id maar een ander kader wordt niet opgeslagen
const other = await page.js(`(() => { const labels = new Set(${JSON.stringify(rows().map(r => r.face))});
  const item = state.data.items.find(i => i.kind === "track" && !labels.has(i.faces[0].face));
  const f = item.faces[0]; return { face: f.face, item: item.id, source: f.source, frame: f.frame ?? "", box: f.box }; })()`);
const stale = { face: other.face, item: other.item, label: "Johann", how: "chosen", source: other.source,
                frame: other.frame === "" ? 1 : Number(other.frame) + 1, x: other.box[0] + 1, y: other.box[1], w: other.box[2], h: other.box[3] };
await page.js(`localStorage.setItem("unsaved", ${JSON.stringify(JSON.stringify([stale]))}); true`);
before = rows().length;
await page.reload(); await sleep(500);
check("een achtergebleven keuze voor een ander kader wordt niet opgeslagen", rows().length === before && !rows().some(r => r.face === other.face));

// ---- de pagina en items.json komen nooit ongezien uit de cache van de browser
const head = await fetch(url("/web/app.js"));
const items = await fetch(url("/items.json"));
check("de pagina wordt niet ongezien uit de cache gehaald", head.headers.get("cache-control") === "no-cache" && items.headers.get("cache-control") === "no-cache");

// ---- labels.csv in een andere tekenset (bijvoorbeeld opgeslagen door Excel): de bekende uitleg in plaats van een Python-fout
const file = path.join(DEMO, "labels.csv");
const saved = fs.readFileSync(file);
fs.writeFileSync(file, Buffer.from("face,label\r\nx,Jo\xebl\r\n", "latin1"));
const response = await fetch(url("/api/labels"));
const body = await response.text();
check("labels.csv in een andere tekenset geeft de bekende uitleg", response.status === 500 && body.includes("niet de goede kolommen"), `${response.status} ${body.slice(0, 80)}`);
fs.writeFileSync(file, saved);

// ---- de keuze voor Beeld lichter blijft bewaard na herladen
await page.key("l"); await sleep(200);
await page.reload();
const offAfterReload = await page.js(`!document.getElementById("brighter").checked && !document.body.classList.contains("bright")`);
await page.key("l"); await sleep(200);
await page.reload();
check("Beeld lichter uit of aan blijft bewaard na herladen", offAfterReload && (await page.js(`document.getElementById("brighter").checked`)));
page.close();
