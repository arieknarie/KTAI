// De uitleg (rondleiding): die opent de eerste keer vanzelf, elke stap staat helemaal in beeld bij alle venstermaten
// (de zeven maten van de layouttests en 1440 x 860, de maat waarmee de andere tests werken), toetsen bladeren alleen
// door de uitleg, de browser onthoudt dat de uitleg gezien is, de uitleg stopt het tekenen, en zonder naam staat na
// het sluiten de cursor in het naamvak.
// Deze test leegt de opslag van de browser zonder "uitleg gezien" te zetten: de uitleg moet juist vanzelf openen.
import { connect, check, sleep, rows } from "./lib.mjs";

const SIZES = [[1440, 860], [1920, 950], [1536, 730], [1440, 780], [1366, 657], [1280, 650], [1100, 600], [1024, 580]];
const page = await connect();
await page.fresh({ tourSeen: false });

const steps = await page.js("TOUR.length");
const open = () => page.visible("tour");
check("de uitleg opent de eerste keer vanzelf", await open());
check("de uitleg begint bij stap 1", (await page.text("tour-count")) === `Uitleg 1 van ${steps}`, await page.text("tour-count"));
check("bij stap 1 kan je niet terug", await page.js(`document.getElementById("tour-back").disabled`));

// tijdens de uitleg doen de toetsen van de app niets: een cijfer kiest niets en Enter bladert alleen door de uitleg
const before = rows().length, index = await page.index();
await page.key("7", { code: "Digit7" }); await sleep(300);
check("tijdens de uitleg kiest een cijfertoets niets", rows().length === before);
await page.key("t"); await sleep(200);
check("tijdens de uitleg zet T het tekenen niet aan", (await page.js("state.drawing")) === false && (await open()));
await page.key("Enter"); await sleep(200);
check("tijdens de uitleg gaat Enter naar de volgende stap van de uitleg", (await page.js("tourStep")) === 1 && (await page.index()) === index);
await page.key("ArrowLeft"); await sleep(200);
check("pijl links gaat een stap terug in de uitleg", (await page.js("tourStep")) === 0);
check("zolang de uitleg de eerste keer openstaat, is die nog niet als gezien bewaard",
  (await page.js(`localStorage.getItem("uitleg-gezien")`)) === null);

// elke stap bij elke venstermaat: de uitleg staat helemaal in beeld, het oplichtende kader valt niet buiten beeld,
// en de pagina scrolt niet. De eerste keer is dat de uitleg die vanzelf opende; daarna opent de test de uitleg zelf.
// De uitleg gaat steeds dicht doordat de test na de laatste stap nog een keer op → drukt (zoals een labelaar).
for (const [w, h] of SIZES) {
  await page.size(w, h);
  await page.js(`if (tourStep < 0) openTour(); else tourGo(0); true`); await sleep(200);
  const bad = [];
  for (let step = 0; step < steps; step++) {
    const r = await page.js(`(() => { const b = document.getElementById("tour-bubble").getBoundingClientRect();
      const s = document.getElementById("tour-spot"), sr = s.getBoundingClientRect();
      return { step: tourStep, inside: b.left >= 0 && b.top >= 0 && b.right <= innerWidth && b.bottom <= innerHeight,
               spot: s.classList.contains("hidden") || (sr.width > 0 && sr.right <= innerWidth + 8 && sr.bottom <= innerHeight + 8),
               scroll: Math.max(document.documentElement.scrollHeight - innerHeight, document.documentElement.scrollWidth - innerWidth),
               last: document.getElementById("tour-next").textContent }; })()`);
    if (!r.inside || !r.spot || r.scroll > 0 || r.step !== step || (step === steps - 1 && r.last !== "Begin met labelen")) bad.push(step + 1);
    await page.key("ArrowRight"); await sleep(120);
  }
  check(`uitleg bij ${w}x${h}: elke stap helemaal in beeld, niets scrolt`, bad.length === 0, bad.length ? `stappen ${bad}` : "");
  check(`uitleg bij ${w}x${h}: na de laatste stap dicht`, !(await open()));
}
await page.size(1440, 860);
check("na de uitleg onthoudt de browser dat die gezien is", (await page.js(`localStorage.getItem("uitleg-gezien")`)) === "1");
await page.reload();
check("de tweede keer opent de uitleg niet vanzelf", !(await open()));
await page.js(`document.getElementById("tour-open").click(); true`); await sleep(200);
check("de knop Uitleg opent de uitleg", await open());
await page.key("Escape"); await sleep(200);
check("Esc sluit de uitleg", !(await open()));
await page.js(`document.getElementById("tour-open").click(); true`); await sleep(200);
await page.js(`document.getElementById("tour-skip").click(); true`); await sleep(200);
check("de knop 'Uitleg sluiten' sluit de uitleg", !(await open()));

// de uitleg openen terwijl tekenen aanstaat: het tekenen stopt (anders zou een klik in de uitleg een kader tekenen)
await page.key("t"); await sleep(200);
const drawingBefore = await page.js("state.drawing");
await page.js(`document.getElementById("tour-open").click(); true`); await sleep(200);
check("de uitleg openen stopt het tekenen van een gemist gezicht", drawingBefore === true && (await page.js("state.drawing")) === false && (await open()));
await page.key("Escape"); await sleep(200);

// zonder naam: na het sluiten van de uitleg staat de cursor in het naamvak, zodat de labelaar meteen zijn naam typt
await page.js(`(() => { const i = document.getElementById("labeler"); i.value = ""; i.dispatchEvent(new Event("input")); i.blur(); return true; })()`);
await page.js(`document.getElementById("tour-open").click(); true`); await sleep(200);
await page.js(`document.getElementById("tour-skip").click(); true`); await sleep(200);
check("zonder naam staat na het sluiten van de uitleg de cursor in het naamvak", await page.js(`document.activeElement.id === "labeler"`));
page.close();
