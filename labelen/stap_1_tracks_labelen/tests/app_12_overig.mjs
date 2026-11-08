// Overig gedrag van de labelpagina: het laatste item, labels die buiten de pagina veranderd zijn, de meldingen als
// app.py een keuze niet aanneemt, een kapotte labels.csv bij het openen, oude keuzes uit de browser, een aangeklikte
// knop die geen focus houdt, de waarschuwing bij het sluiten van de pagina, en een tweede tabblad met de labelpagina
// (dan stopt het eerste tabblad).
import fs from "node:fs";
import path from "node:path";
import { connect, check, sleep, rows, rowOf, DEMO, CDP, url } from "./lib.mjs";

const page = await connect();
await page.fresh();

// ---- het laatste item: na de laatste keuze zegt de app hoeveel items nog niet af zijn
const last = await page.js("state.data.items.length - 1");
await page.show(last);
const kind = await page.js(`state.data.items[${last}].kind`);
const faces = await page.js(`state.data.items[${last}].faces.length`);
for (let k = 0; k < faces; k++) { await page.ready(); await page.js(`choose(state.activeFace, "unknown"); true`); await sleep(500); await page.saved(); }
if (kind !== "track") { await page.ready(); await page.js(`document.getElementById("next").click(); true`); await sleep(500); await page.saved(); }
await page.js("saving");
const open = await page.js(`fetch("/api/labels").then(r => r.json()).then(l => state.data.items.filter(i => !i.faces.every(f => l[f.face])).length)`);
const text = await page.text("instruction");
check("na het laatste item zegt de app hoeveel items nog niet af zijn", (await page.index()) === last &&
  text.startsWith("Dit was het laatste item") && text.includes(`Nog ${open} item(s)`), text);

// ---- een label dat buiten deze pagina is opgeslagen, verschijnt zodra de pagina weer in beeld komt
const outside = await page.js(`state.data.items.find((i, n) => n < ${last} && i.kind === "track" && !state.labels[i.faces[0].face]).faces[0].face`);
await fetch(url("/api/labels"), { method: "POST", headers: { "Content-Type": "application/json" },
  body: JSON.stringify([{ face: outside, label: "Johann", labeler: "Iemand anders" }]) });
await page.js(`window.dispatchEvent(new Event("focus")); true`);
check("een label dat elders is opgeslagen, verschijnt als de pagina weer in beeld komt",
  await page.until(`state.labels[${JSON.stringify(outside)}] === "Johann"`, 3000));

// ---- app.py neemt een keuze niet aan: de rode balk zegt wat er moet gebeuren
const track = await page.find(`i.kind === "track" && !state.labels[i.faces[0].face]`, 2);
await page.show(track);
await page.js(`unsaved.set("bestaat-niet#0", { face: "bestaat-niet#0", item: "bestaat-niet", label: "unknown", how: "chosen" }); save([])`);
check("onbekend gezicht: de rode balk zegt dat je de app opnieuw moet starten",
  (await page.visible("error")) && (await page.text("error")).includes("De app kent deze gezichten niet"), await page.text("error"));
await page.js(`unsaved.clear(); rememberUnsaved(); document.getElementById("error").classList.add("hidden"); true`);
await page.js(`document.getElementById("labeler").value = ""; save([labelRow(state.data.items[${track}], state.data.items[${track}].faces[0], "unknown")])`);
check("zonder naam neemt app.py niets aan: de rode balk vraagt om een naam",
  (await page.text("error")).includes("Vul bovenaan een naam in") && !rowOf(await page.js(`state.data.items[${track}].faces[0].face`)),
  await page.text("error"));
await page.js(`unsaved.clear(); rememberUnsaved(); document.getElementById("labeler").value = "Tester"; document.getElementById("error").classList.add("hidden"); true`);

// ---- oude keuzes uit de browser: een keuze die niet meer bestaat wordt weggelaten, een goede keuze wordt opgeslagen
const [good, gone] = await page.js(`(() => { const free = state.data.items.filter(i => i.kind === "track" && !state.labels[i.faces[0].face]);
  return [free[5], free[6]].map(i => labelRow(i, i.faces[0], "unknown")); })()`);
good.labeler = gone.labeler = "Tester";   // zoals save() in app.js een keuze in de browser bewaart
gone.label = "bestaat-niet";
await page.js(`localStorage.setItem("unsaved", ${JSON.stringify(JSON.stringify([good, gone]))}); true`);
await page.reload(); await sleep(800);
check("een keuze uit de browser die niet meer bestaat, wordt niet opgeslagen; een goede keuze wel",
  rowOf(good.face)?.label === "unknown" && !rowOf(gone.face), JSON.stringify([rowOf(good.face), rowOf(gone.face)]));

// ---- een kapotte labels.csv bij het openen van de pagina: een duidelijke melding in de rode balk
const file = path.join(DEMO, "labels.csv");
const saved = fs.readFileSync(file);
fs.writeFileSync(file, Buffer.from("face,label\r\nx,Jo\xebl\r\n", "latin1"));
await page.open(url(), { app: false });
await page.until(`!document.getElementById("error").classList.contains("hidden")`, 5000);
const error = await page.text("error");
check("kapotte labels.csv: de pagina zegt dat de gegevens niet geladen konden worden, en waarom",
  error.startsWith("De gegevens konden niet geladen worden") && error.includes("niet de goede kolommen"), error);
fs.writeFileSync(file, saved);
await page.open(url());

// ---- een aangeklikte knop houdt geen focus: Enter drukt die knop daarna niet nog een keer in
const pair = await page.find(`n > 0 && i.kind === "track" && state.data.items[n - 1].kind === "track" && !state.labels[state.data.items[n - 1].faces[0].face]`, 2);
await page.show(pair);
await page.click("#previous"); await page.ready();
const afterClick = await page.index();
await page.send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13, text: "\r" });
await page.send("Input.dispatchKeyEvent", { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13 });
await sleep(400);
check("een aangeklikte knop houdt geen focus (Enter drukt hem niet nog een keer in)",
  afterClick === pair - 1 && (await page.index()) === pair - 1 && (await page.js(`document.activeElement.id !== "previous"`)));

// ---- de pagina sluiten: alleen als er nog keuzes niet opgeslagen zijn, vraagt de browser of je de pagina wilt verlaten
// (nagebootst met een eigen beforeunload-gebeurtenis; app.js zegt dan "niet zomaar sluiten" met preventDefault)
const leave = () => page.js(`(() => { const e = new Event("beforeunload", { cancelable: true }); window.dispatchEvent(e);
  return e.defaultPrevented; })()`);
const quiet = await leave();
await page.js(`unsaved.set("test-niet-opgeslagen", { face: "test-niet-opgeslagen" }); true`);   // alleen in het geheugen
const warns = await leave();
await page.js(`unsaved.delete("test-niet-opgeslagen"); true`);
check("bij het sluiten waarschuwt de pagina alleen als er nog keuzes niet opgeslagen zijn", quiet === false && warns === true,
  `zonder: ${quiet}, met: ${warns}`);

// ---- een tweede tabblad met de labelpagina: dit tabblad stopt en bewaart niets meer
const tab = await (await fetch(`${CDP}/json/new?${url()}`, { method: "PUT" })).json();
const stopped = await page.until("stopped === true", 10000);
check("opnieuw geopend in een ander tabblad: dit tabblad stopt met een melding",
  stopped && (await page.text("error")).startsWith("Deze labelpagina is opnieuw geopend"), await page.text("error"));
const before = rows().length;
await page.js(`choose(state.activeFace, "unknown"); true`); await sleep(500);
check("een gestopt tabblad bewaart geen keuzes meer", rows().length === before);
await fetch(`${CDP}/json/close/${tab.id}`);
page.close();
