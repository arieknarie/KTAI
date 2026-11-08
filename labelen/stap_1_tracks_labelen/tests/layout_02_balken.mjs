// Past alles op één scherm, ook met de balken en meldingen erbij? Dezelfde controle als layout_01_past.mjs, maar nu
// met de rode balk (de lange melding "keuzes NIET opgeslagen"), de gele waarschuwing rechts, getekende gezichten en
// de groene balk "Klaar!". Ook dan mag de labelaar nooit hoeven scrollen, bij alle zeven venstermaten.
import { connect, check, sleep } from "./lib.mjs";

const SIZES = [[1920, 950], [1536, 730], [1440, 780], [1366, 657], [1280, 650], [1100, 600], [1024, 580]];
const page = await connect();
await page.fresh();

const most = await page.js(`(() => { let b = -1; state.data.items.forEach((i, n) => {
  if (i.kind !== "track" && (b < 0 || i.faces.length > state.data.items[b].faces.length)) b = n; }); return Math.max(0, b); })()`);
const track = Math.max(0, await page.find(`i.kind === "track" && (i.others || []).length > 0`));

// De rode balk met de echte melding van app.js als de app niet reageert: één opslagverzoek laten mislukken door de
// verbinding in de pagina even te laten weigeren (de app zelf blijft draaien).
await page.show(track);
await page.js(`(async () => { const real = window.fetch; window.fetch = () => Promise.reject(new TypeError("Failed to fetch"));
  try { const item = state.data.items[state.index]; await save([labelRow(item, item.faces[0], "unknown")]); } finally { window.fetch = real; }
  return true; })()`);
const message = await page.text("error");
check("de rode balk staat er, met de melding dat keuzes niet opgeslagen zijn", (await page.visible("error")) && message.includes("NIET opgeslagen"), message);

// drie getekende gezichten bij een item (alleen op de pagina); `chosen`: met een keuze erbij (dan geen waarschuwing daarover)
const withDrawn = (index, chosen) => page.js(`(() => { const item = state.data.items[${index}]; state.drawn[item.id] = [];
  for (let k = 0; k < 3; k++) { const face = item.id + "#getekend-" + (1000 + k);
    state.drawn[item.id].push({ face, box: [10 + 30 * k, 10, 20, 20], source: item.faces[0].source, frame: item.faces[0].frame ?? "", drawn: true });
    if (${chosen}) state.labels[face] = "Werner"; }
  state.activeFace = facesOf(item).length - 1; renderItem(); return true; })()`);
const clearDrawn = () => page.js(`(() => { Object.values(state.drawn).flat().forEach(f => delete state.labels[f.face]); state.drawn = {};
  state.activeFace = 0; renderItem(); return true; })()`);
// Volgende indrukken zonder dat er iets bewaard wordt: dan toont de app de gele waarschuwing
const warnByNext = async () => { await page.ready(); await page.js(`next(); true`); await sleep(200); };

const cases = [
  ["still met de meeste gezichten + rode balk", most, async () => {}],
  ["track + rode balk", track, async () => {}],
  ["still + getekende gezichten + gele waarschuwing + rode balk", most, async () => { await withDrawn(most, true); await warnByNext(); }],
  ["track + getekende gezichten + gele waarschuwing + rode en groene balk", track, async () => {
    await withDrawn(track, false); await warnByNext();
    await page.js(`window.__labels = { ...state.labels }; state.data.items.forEach(it => it.faces.forEach(f => state.labels[f.face] = state.labels[f.face] || "unknown"));
      renderProgress(); true`);
  }],
];

for (const [w, h] of SIZES) {
  await page.size(w, h);
  for (const [name, index, extra] of cases) {
    await page.show(index); await sleep(300);
    await extra(); await sleep(300);
    const r = await page.js(`(() => {
      const d = document.documentElement, p = document.querySelector(".panel"), refs = document.querySelector(".refs");
      const s = document.getElementById("stage").getBoundingClientRect(), f = document.getElementById("frame").getBoundingClientRect();
      return { page: d.scrollHeight - innerHeight, pageX: d.scrollWidth - innerWidth, panel: p.scrollHeight - p.clientHeight,
               refs: refs.scrollHeight - refs.clientHeight, frame: Math.round(f.bottom - s.bottom), frameX: Math.round(f.right - s.right),
               red: !document.getElementById("error").classList.contains("hidden"),
               green: !document.getElementById("done").classList.contains("hidden"),
               warn: document.getElementById("instruction").classList.contains("warn"),
               zoom: document.getElementById("zoom").offsetWidth }; })()`);
    const bars = r.red && (!name.includes("gele") || r.warn) && (!name.includes("groene") || r.green);
    const ok = bars && r.page <= 0 && r.pageX <= 0 && r.panel <= 0 && r.refs <= 0 && r.frame <= 1 && r.frameX <= 1;
    check(`${w}x${h} ${name}: alles past zonder scrollen`, ok, JSON.stringify(r));
    await clearDrawn();
    await page.js(`if (window.__labels) { state.labels = window.__labels; delete window.__labels; renderProgress(); } true`);
  }
}
await page.size(1440, 860);
await page.js(`unsaved.clear(); rememberUnsaved(); true`);
page.close();
