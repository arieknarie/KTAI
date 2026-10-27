// De knop Volgende: bij een track zonder keuze gaat de app niet door (net als Enter), de toets → slaat wel over;
// bij een still waarschuwt Volgende eerst, opnieuw na een keuze tussendoor, en pas de tweede keer met de
// waarschuwing in beeld worden de gezichten zonder keuze figurant. De groene balk zegt dat labels.csv naar Marc gaat.
import { connect, check, skip, sleep, rows } from "./lib.mjs";

const page = await connect();
await page.fresh();
const nextButton = async () => { await page.ready(); await page.js(`document.getElementById("next").click(); true`); await sleep(400); };
const warnShown = () => page.js(`document.getElementById("instruction").classList.contains("warn")`);

// ---- de knop Volgende bij een track zonder keuze: waarschuwt en blijft staan, ook bij een tweede klik
const track = await page.find(`i.kind === "track"`, 2);
await page.show(track);
await nextButton();
check("knop Volgende bij een track zonder keuze gaat niet door", (await page.index()) === track && (await page.text("instruction")).startsWith("Kies eerst"));
await nextButton();
check("ook een tweede klik op Volgende slaat de track niet over", (await page.index()) === track && rows().length === 0);
await page.key("ArrowRight"); await page.ready();
check("→ slaat de track wel over, zonder iets te bewaren", (await page.index()) === track + 1 && rows().length === 0);
// een track die af is: Volgende gaat door
await page.key("ArrowLeft"); await page.ready();
await page.key("7"); await sleep(700); await page.saved();
await page.key("ArrowLeft"); await page.ready();
await nextButton();
check("knop Volgende bij een track die af is, gaat door", (await page.index()) === track + 1);

// ---- een still met meer gezichten: waarschuwen, één keuze, opnieuw waarschuwen, daarna de rest figurant
let still = await page.find(`i.kind !== "track" && i.faces.length >= 3`);
if (still < 0) still = await page.find(`i.kind !== "track" && i.faces.length >= 2`);
if (still < 0) {
  skip("Volgende bij een still", "items.json heeft geen foto of still met 2 of meer gezichten");
} else {
  await page.show(still);
  const before = rows().length;
  await nextButton();
  check("still: eerste Volgende waarschuwt", (await warnShown()) && (await page.index()) === still);
  await page.ready(); await page.key("7"); await sleep(600); await page.saved();
  check("still: na een keuze is de waarschuwing weg", !(await warnShown()));
  await nextButton();
  const faces = await page.js(`state.data.items[${still}].faces.length`);
  check("still: na een keuze waarschuwt Volgende opnieuw", (await warnShown()) && (await page.index()) === still &&
    rows().length === before + 1 && (await page.text("instruction")).startsWith(`Nog ${faces - 1} gezicht`), await page.text("instruction"));
  await nextButton(); await sleep(300); await page.saved();
  const auto = rows().filter(r => r.label === "other" && r.how === "auto").length;
  check("still: tweede Volgende met de waarschuwing in beeld maakt de rest figurant", (await page.index()) === still + 1 && auto === faces - 1, `${auto} automatisch`);
}

// ---- de groene balk (alles in de pagina als gekozen markeren, zonder op te slaan)
await page.js(`state.data.items.forEach(it => it.faces.forEach(f => state.labels[f.face] = state.labels[f.face] || "unknown")); renderProgress(); true`);
check("groene balk zegt dat je het bestand naar Marc stuurt", (await page.text("done")).includes("naar Marc"));
page.close();
