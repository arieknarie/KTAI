// Past alles op één scherm, zonder scrollen? De labelaar mag nooit hoeven scrollen: niet de pagina, niet het blok met
// de knoppen rechts en niet het blok met de foto's van de acteurs links, en het beeld valt nergens buiten zijn vak.
// Gecontroleerd bij zeven venstermaten (van een groot scherm tot een kleine laptop) en zeven soorten items,
// waaronder items met getekende gezichten (die geven extra knopjes en de knop Weghalen).
import { connect, check, sleep } from "./lib.mjs";

const SIZES = [[1920, 950], [1536, 730], [1440, 780], [1366, 657], [1280, 650], [1100, 600], [1024, 580]];
const page = await connect();
await page.fresh();

// de items, gezocht op hun soort en eigenschappen (zo werkt de test met elke items.json)
const pick = await page.js(`(() => {
  const it = state.data.items, best = (score, keep = () => true) => {
    let b = -1; it.forEach((i, n) => { if (keep(i) && (b < 0 || score(i) > score(it[b]))) b = n; }); return Math.max(0, b); };
  const first = test => { const n = it.findIndex(test); return n; };
  const still3 = first(i => i.kind !== "track" && i.faces.length === 3);
  const track = first(i => i.kind === "track" && (i.others || []).length > 0);
  return {
    "foto": Math.max(0, first(i => i.kind === "photo")),
    "still-meeste-gezichten": best(i => i.faces.length, i => i.kind !== "track"),
    "still-3-gezichten": still3 >= 0 ? still3 : best(i => -Math.abs(i.faces.length - 3), i => i.kind !== "track"),
    "hoogste-beeld": best(i => i.height / i.width),
    "track": track >= 0 ? track : Math.max(0, first(i => i.kind === "track")) }; })()`);
const cases = [...Object.entries(pick), ["still+getekend", pick["still-meeste-gezichten"]], ["track+getekend", pick.track]];

// drie getekende gezichten bij een item (alleen op de pagina, niet opgeslagen); het laatste is aan de beurt
const withDrawn = (index, n) => page.js(`(() => { const item = state.data.items[${index}]; state.drawn[item.id] = [];
  for (let k = 0; k < ${n}; k++) state.drawn[item.id].push({ face: item.id + "#getekend-" + (1000 + k), box: [10 + 30 * k, 10, 20, 20],
    source: item.faces[0].source, frame: item.faces[0].frame ?? "", drawn: true });
  state.activeFace = facesOf(item).length - 1; renderItem(); return true; })()`);

for (const [w, h] of SIZES) {
  await page.size(w, h);
  for (const [name, index] of cases) {
    await page.show(index); await sleep(300);
    if (name.endsWith("+getekend")) { await withDrawn(index, 3); await sleep(300); }
    const r = await page.js(`(() => {
      const d = document.documentElement, panel = document.querySelector(".panel"), refs = document.querySelector(".refs");
      const stage = document.getElementById("stage").getBoundingClientRect(), frame = document.getElementById("frame").getBoundingClientRect();
      const hint = document.querySelector(".hint").getBoundingClientRect();
      return { pageScroll: d.scrollHeight - innerHeight, pageScrollX: d.scrollWidth - innerWidth,
               panelOverflow: panel.scrollHeight - panel.clientHeight, refsOverflow: refs.scrollHeight - refs.clientHeight,
               frameOut: Math.round(frame.bottom - stage.bottom), frameWidthOut: Math.round(frame.right - stage.right),
               hintBottom: Math.round(hint.bottom - innerHeight), frameW: Math.round(frame.width), frameH: Math.round(frame.height),
               zoom: document.getElementById("zoom").offsetWidth }; })()`);
    const ok = r.pageScroll <= 0 && r.pageScrollX <= 0 && r.panelOverflow <= 0 && r.refsOverflow <= 0 &&
               r.frameOut <= 1 && r.frameWidthOut <= 1 && r.hintBottom <= 0;
    check(`${w}x${h} ${name}: alles past zonder scrollen`, ok, JSON.stringify(r));
    if (name.endsWith("+getekend")) await page.js(`state.drawn = {}; state.activeFace = 0; renderItem(); true`);
  }
}
await page.size(1440, 860);
page.close();
