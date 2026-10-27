// De basis van de labelpagina: de pagina laadt, een keuze met de muis of met een toets komt meteen in labels.csv,
// Volgende maakt gezichten zonder keuze figurant, en bij een track gaat de app na een keuze vanzelf door.
import { connect, check, skip, rows, csvHeader, sleep } from "./lib.mjs";

const page = await connect();
await page.fresh({ name: "Partner" });

// ---- 1. het eerste scherm
const counter = await page.text("item-counter");
check("app laadt en toont item 1", /^Item 1 van \d+/.test(counter), counter);
check("naam staat ingevuld", (await page.js(`document.getElementById("labeler").value`)) === "Partner");

// ---- 2. een foto of still met minstens drie gezichten: kiezen met de muis en met een toets
const still = await page.find(`i.kind !== "track" && i.faces.length >= 3`);
if (still < 0) {
  skip("keuzes en Volgende bij een still met meer gezichten", "items.json heeft geen foto of still met 3 of meer gezichten");
} else {
  await page.show(still);
  await page.js(`document.querySelector('#faces button[data-face="0"][data-label="unknown"]').click(); true`); await sleep(500); await page.saved();
  check("klik slaat op in labels.csv", rows().length === 1, `${rows().length} rij(en)`);
  const active = await page.js("state.activeFace");
  check("na een keuze gaat de selectie naar het volgende gezicht", active === 1, `actief gezicht ${active}`);
  await page.ready();
  await page.key("7"); await sleep(500); await page.saved();
  check("sneltoets 7 (Weet niet) slaat op", rows().length === 2, `${rows().length} rij(en)`);
  const header = csvHeader().join(",");
  check("labels.csv heeft de juiste kolommen", header === "face,item,label,how,labeler,time,source,frame,x,y,w,h", header);
  check("naam van de labelaar wordt opgeslagen", rows()[0]?.labeler === "Partner", JSON.stringify(rows()[0]));

  // ---- 3. Volgende: eerst een waarschuwing, de tweede keer worden de overige gezichten figurant
  const faces = await page.js(`state.data.items[${still}].faces.map(f => f.face)`);
  await page.ready();
  await page.js(`document.getElementById("next").click(); true`); await sleep(500);
  check("eerste keer Volgende: waarschuwing hoeveel gezichten figurant worden", (await page.text("instruction")).startsWith("Nog"));
  await page.ready();
  await page.js(`document.getElementById("next").click(); true`); await sleep(800); await page.saved();
  const labels = await page.js(`fetch("/api/labels").then(r => r.json())`);
  const others = faces.filter(f => labels[f]?.label === "other").length;
  check("Volgende maakt de overige gezichten figurant", others === faces.length - 2, `${others} van ${faces.length - 2}`);
  check("Volgende gaat naar het volgende item", (await page.index()) === still + 1);
}

// ---- 4. een track met een groot gezicht: een keuze met een toets gaat vanzelf door naar het volgende item
const track = await page.js(`(() => { let best = -1; state.data.items.forEach((i, n) => {
  if (i.kind === "track" && n < state.data.items.length - 1 && (best < 0 || i.faces[0].box[2] > state.data.items[best].faces[0].box[2])) best = n; });
  return best; })()`);
await page.show(track);
await page.key("7"); await sleep(700);
check("bij een track gaat een keuze vanzelf door naar het volgende item", (await page.index()) === track + 1);
await page.key("ArrowLeft"); await page.ready();
check("pijl links gaat terug", (await page.index()) === track);
await page.js(`document.querySelector('#faces button[data-label="no_face"]').click(); true`); await sleep(700); await page.saved();
const trackFace = await page.js(`state.data.items[${track}].faces[0].face`);
check("een keuze wijzigen vervangt het oude label", (await page.js(`fetch("/api/labels").then(r => r.json())`))[trackFace]?.label === "no_face");

// ---- 5. de knop 'Naar eerste item dat nog niet af is'
const expected = await page.firstOpenOnServer();
await page.js(`document.getElementById("first-open").click(); true`); await sleep(500);
const firstOpen = await page.index();
check("'Naar eerste item dat nog niet af is' werkt", firstOpen === expected, `item ${firstOpen}, verwacht ${expected}`);
page.close();
