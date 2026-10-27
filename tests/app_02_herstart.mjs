// De app opnieuw starten en een app die niet meer draait: de labels blijven bewaard, bij de start maakt de app een
// reservekopie, de pagina gaat verder bij het laatst bekeken item, Beeld lichter werkt met de toets L, en als het
// venster van de app dicht is, verschijnt bij een keuze een rode waarschuwing.
import fs from "node:fs";
import path from "node:path";
import { connect, check, sleep, DEMO, stopApp, startApp, url } from "./lib.mjs";

const page = await connect();
await page.fresh();
const countLabels = () => page.js(`fetch("/api/labels").then(r => r.json()).then(x => Object.keys(x).length)`);

// twee keuzes bij twee tracks, zodat er labels zijn die bewaard moeten blijven
const track = await page.find(`i.kind === "track" && state.data.items[n + 1].kind === "track"`, 3);
await page.show(track);
await page.key("7"); await sleep(600); await page.saved(); await page.ready();
await page.key("7"); await sleep(600); await page.saved();
const before = await countLabels();
const at = await page.index();   // het item dat nu in beeld is; de pagina onthoudt dat in de browser

// ---- 1. de app opnieuw starten
fs.rmSync(path.join(DEMO, "backups"), { recursive: true, force: true });
await stopApp();
await startApp();
await page.open(url());
const after = await countLabels();
check("labels blijven bewaard na herstart", after === before && before > 0, `${before} -> ${after}`);
const backups = fs.existsSync(path.join(DEMO, "backups")) ? fs.readdirSync(path.join(DEMO, "backups")) : [];
check("bij de start is een reservekopie gemaakt", backups.length === 1, backups.join(", "));
const index = await page.index();
check("de app gaat verder bij het laatst bekeken item", index === at, `item ${index}, verwacht ${at}`);

// ---- 2. Beeld lichter bij een track met een groot gezicht
const big = await page.js(`(() => { let best = -1; state.data.items.forEach((i, n) => {
  if (i.kind === "track" && n < state.data.items.length - 1 && (best < 0 || i.faces[0].box[2] > state.data.items[best].faces[0].box[2])) best = n; });
  return best; })()`);
await page.show(big);
const bright = () => page.js(`document.body.classList.contains("bright") && document.getElementById("brighter").checked`);
const brightBefore = await bright();
check("beeld lichter staat standaard aan", brightBefore === true);
await page.key("l"); await sleep(300);
const off = await bright();
await page.key("L"); await sleep(300);
check("sneltoets L zet beeld lichter uit en aan", off === false && (await bright()) === true);

// ---- 3. het venster van de app is dicht: een keuze geeft de rode waarschuwing
await stopApp();
await page.js(`document.querySelector('#faces button[data-label="unknown"]').click(); true`); await sleep(1500);
const banner = (await page.visible("error")) && (await page.text("error"));
check("rode waarschuwing als de app niet meer draait", typeof banner === "string" && banner.includes("NIET opgeslagen"), banner || "");
await startApp();   // voor de volgende tests
page.close();
