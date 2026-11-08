// Toetsen en automatische figuranten: een ingedrukt gehouden toets of een toetscombinatie doet niets, de pijltjes
// bladeren alleen, een klik op een knopje of kader kiest het gezicht, na het laatste gezicht gaat de app terug naar het
// eerste open gezicht, Volgende markeert automatische figuranten als "auto" en overschrijft nooit een bestaand label,
// en een naam zonder letters telt niet.
import { connect, check, skip, sleep, rows, rowOf } from "./lib.mjs";

const page = await connect();
await page.fresh();

// ---- toetsen die niets mogen doen, bij een track
const track = await page.find(`i.kind === "track"`);
await page.show(track);
await page.key("5", { repeat: true }); await sleep(400);
check("ingedrukt gehouden toets (herhaling) doet niets", rows().length === 0 && (await page.index()) === track);
await page.key("5", { ctrlKey: true }); await page.key("5", { metaKey: true }); await sleep(400);
check("Ctrl/Cmd + cijfer doet niets", rows().length === 0 && (await page.index()) === track);
await page.key("5", { altKey: true }); await sleep(400);
check("Alt + cijfer doet niets", rows().length === 0 && (await page.index()) === track);
await page.key(" "); await sleep(400);
check("spatie doet niets", rows().length === 0 && (await page.index()) === track);

// ---- een foto of still met meer gezichten (bij voorkeur drie)
let still = await page.find(`i.kind !== "track" && i.faces.length === 3`);
if (still < 0) still = await page.find(`i.kind !== "track" && i.faces.length >= 2`);
if (still < 0) {
  skip("pijltjes, terug naar het eerste open gezicht en automatische figuranten", "items.json heeft geen foto of still met 2 of meer gezichten");
} else {
  const n = await page.js(`state.data.items[${still}].faces.length`);
  await page.show(still);
  await page.key("ArrowRight"); await page.ready();
  check("pijl rechts bladert alleen (geen figuranten)", rows().length === 0 && (await page.index()) === still + 1);
  await page.key("ArrowLeft"); await page.ready();
  // een klik op een knopje boven de keuzes of op een kader in het beeld kiest welk gezicht aan de beurt is
  await page.js(`document.querySelectorAll("#face-tabs button")[${n - 1}].click(); true`);
  const viaTab = await page.js("state.activeFace");
  await page.js(`document.querySelectorAll("#frame .box:not(.other)")[0].click(); true`);
  const viaBox = await page.js("state.activeFace");
  check("een klik op een knopje of op een kader kiest welk gezicht aan de beurt is", viaTab === n - 1 && viaBox === 0 && rows().length === 0,
    `knopje: gezicht ${viaTab}, kader: gezicht ${viaBox}`);
  await page.ready();
  await page.js(`state.activeFace = ${n - 1}; renderItem(); true`);
  await page.key("7"); await sleep(500); await page.saved();
  check("na het laatste gezicht gaat de app terug naar het eerste open gezicht", (await page.js("state.activeFace")) === 0);
  await page.ready(); await page.key("Enter"); await sleep(500);
  check("eerste Enter bij een still: alleen een waarschuwing", rows().filter(r => r.how === "auto").length === 0 && (await page.index()) === still);
  await page.ready(); await page.key("Enter"); await sleep(800); await page.saved();
  const autos = rows().filter(r => r.how === "auto").length, chosen = rows().filter(r => r.how === "chosen").length;
  check("Volgende: automatische figuranten gemarkeerd als auto", autos === n - 1 && chosen === 1, `auto ${autos}, chosen ${chosen}`);

  // een automatische figurant overschrijft nooit een label dat er al is
  const face = await page.js(`state.data.items[${still}].faces[${n - 1}].face`);
  await page.js(`fetch("/api/labels", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify([{ face: ${JSON.stringify(face)}, label: "other", how: "auto", labeler: "Tester" }]) }).then(r => r.json())`);
  check("automatische figurant overschrijft geen bestaand label", rowOf(face)?.label === "unknown", JSON.stringify(rowOf(face)));
}

// ---- een naam van alleen tekens of emoji
await page.js(`(() => { const i = document.getElementById("labeler"); i.value = "🙂🙂"; i.dispatchEvent(new Event("input")); return true; })()`);
await page.show(track);
const before = rows().length;
await page.key("6"); await sleep(500);
check("naam van alleen tekens/emoji telt niet als naam", rows().length === before && (await page.text("error")).startsWith("Vul eerst"));
page.close();
