// Gedrag van de pagina: Enter in het naamvak, een naam van alleen cijfers, een dubbelklik telt één keer, de regel
// "Net gekozen", Enter slaat een open track niet over, de teller en de voortgangsknoppen, de grote foto van een
// acteur, de grootte van de uitvergroting en de groene balk als alles af is.
import fs from "node:fs";
import path from "node:path";
import { connect, check, sleep, rows, DEMO } from "./lib.mjs";

const page = await connect();
await page.fresh({ name: "" });

// een naam van alleen cijfers is geen naam; Enter in het naamvak beëindigt het typen
await page.js(`(() => { const i = document.getElementById("labeler"); i.focus(); i.value = "123"; i.dispatchEvent(new Event("input")); return true; })()`);
await page.key("Enter", {}, `document.getElementById("labeler")`); await sleep(200);
check("Enter in het naamvak beëindigt het typen", await page.js(`document.activeElement.id !== "labeler"`));
// twee tracks achter elkaar, met nog een item daarna
const track = await page.find(`i.kind === "track" && state.data.items[n + 1].kind === "track"`, 2);
await page.show(track);
await page.key("4"); await sleep(300);
check("naam van alleen cijfers telt niet", rows().length === 0);
await page.js(`(() => { const i = document.getElementById("labeler"); i.value = "Tester"; i.dispatchEvent(new Event("input")); i.blur(); return true; })()`);

// een dubbelklik op een keuzeknop: alleen de eerste klik telt
await page.show(track);
await page.js(`document.querySelector('#faces button[data-label="no_face"]').click(); document.querySelector('#faces button[data-label="no_face"]').click(); true`);
await sleep(700); await page.saved();
check("dubbelklik telt maar één keer", rows().length === 1 && (await page.index()) === track + 1, `${rows().length} rij(en)`);
check("na een keuze bij een track staat er wat er net gekozen is", (await page.text("last-choice")).includes("Geen gezicht"));

// Enter bij een track zonder keuze slaat die track niet over
await page.ready();
await page.key("Enter"); await sleep(300);
check("Enter bij een track zonder keuze slaat de track niet over", (await page.index()) === track + 1 &&
  (await page.text("instruction")).startsWith("Kies eerst"));
check("teller toont hoeveel er af is", (await page.text("item-counter")).includes("· 1 af"), await page.text("item-counter"));

// een voortgangsknop gaat naar het eerste item van dat onderdeel dat nog niet af is
const group = await page.js(`state.data.items[${track}].group`);
const expected = await page.js(`fetch("/api/labels").then(r => r.json()).then(labels =>
  state.data.items.findIndex(i => i.group === ${JSON.stringify(group)} && !i.faces.every(f => labels[f.face])))`);
await page.show(expected === 0 ? await page.js("state.data.items.length - 1") : 0);   // eerst ergens anders staan
await page.js(`[...document.querySelectorAll("#progress button")].find(b => b.title.startsWith(${JSON.stringify(group + ":")})).click(); true`);
await sleep(500);
const index = await page.index();
check("voortgangsknop gaat naar het eerste open item van dat onderdeel", index === expected, `item ${index}, verwacht ${expected}`);

// een foto van een acteur wordt groot zolang de muis erop staat
await page.js(`document.querySelector("#references img").dispatchEvent(new MouseEvent("mouseenter")); true`); await sleep(200);
check("foto van een acteur wordt groot bij aanwijzen", await page.visible("ref-big"));
await page.js(`document.querySelector("#references img").dispatchEvent(new MouseEvent("mouseleave")); true`); await sleep(100);
check("de grote foto verdwijnt als de muis weggaat", !(await page.visible("ref-big")));

// de uitvergroting rechts gebruikt de vrije ruimte (venster 1440 x 860)
const zoom = await page.js(`document.getElementById("zoom").clientWidth`);
check("uitvergroting gebruikt de vrije ruimte", zoom >= 150, `${zoom}px`);

// de groene balk: alles in de pagina als gekozen markeren (niet opgeslagen) en de voortgang opnieuw tekenen
await page.js(`state.data.items.forEach(it => it.faces.forEach(f => state.labels[f.face] = state.labels[f.face] || "unknown")); renderProgress(); true`);
const done = (await page.visible("done")) && (await page.text("done"));
const file = path.join(fs.realpathSync(DEMO), "labels.csv");
check("groene balk als alles af is, met de plek van labels.csv", typeof done === "string" && done.includes(file), done || "");
page.close();
