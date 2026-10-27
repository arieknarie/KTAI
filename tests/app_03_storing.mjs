// Keuzes die gemaakt zijn terwijl het venster van de app dicht was (een "storing"), komen later alsnog in labels.csv:
// bij de volgende keuze, of bij het opnieuw openen van de pagina.
import { connect, check, sleep, rowOf, stopApp, startApp, url, port } from "./lib.mjs";

const page = await connect();
await page.fresh();

// vijf tracks achter elkaar: bij een track gaat de app na elke keuze vanzelf naar het volgende item
const first = await page.find(`[0, 1, 2, 3, 4].every(k => state.data.items[n + k].kind === "track")`, 5);
await page.show(first);
const faces = await page.js(`[0, 1, 2, 3].map(k => state.data.items[${first} + k].faces[0].face)`);
const choose = async label => { await page.ready(); await page.js(`choose(state.activeFace, "${label}"); true`); await page.saved(); await sleep(600); };

// Scenario 1: venster dicht, twee keuzes, venster weer open, derde keuze
await stopApp();
await choose("unknown");
await choose("unknown");
check("waarschuwing toont 2 niet-opgeslagen keuzes", (await page.text("error")).includes("2 keuze(s)"), await page.text("error"));
await startApp();
await choose("unknown");
await sleep(600);
const saved = [0, 1, 2].map(k => rowOf(faces[k])?.label);
check("scenario 1: alle 3 keuzes staan in labels.csv", saved.every(label => label === "unknown"), JSON.stringify(saved));
check("scenario 1: rode waarschuwing is weer weg", !(await page.visible("error")));

// Scenario 2: venster dicht, keuze, pagina herladen terwijl de app niet draait, app gestart, pagina opnieuw geopend
const portBefore = port();
await stopApp();
await choose("no_face");
await page.reload({ app: false });   // de app draait niet: de browser toont alleen een foutpagina
await startApp();
await page.open(url());
await page.saved(); await sleep(800);
// Wat de pagina toont, voor de details als een controle mislukt. Zegt de rode balk dat de app niet reageert terwijl de
// app wel draait, dan weigerde de app een verbinding van de browser (zie "drukke computer" in test_server_start.py).
const seen = async () => JSON.stringify({ poort: `${portBefore} -> ${port()}`, rodeBalk: (await page.visible("error")) ? await page.text("error") : "",
  appDraait: await fetch(url("/api/ping")).then(r => r.ok).catch(() => false), inDeBrowser: await page.js(`localStorage.getItem("unsaved")`) });
check("scenario 2: keuze van tijdens de storing staat na herladen in labels.csv", rowOf(faces[3])?.label === "no_face",
  `${rowOf(faces[3])?.label || "ontbreekt"} ${await seen()}`);
check("scenario 2: niets blijft als niet-opgeslagen achter", (await page.js(`localStorage.getItem("unsaved")`)) === "[]", await seen());
page.close();
