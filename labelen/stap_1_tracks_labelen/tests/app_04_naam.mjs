// Zonder naam van de labelaar wordt niets opgeslagen, en de pagina geeft geen foutmeldingen of beveiligingsmeldingen
// (bijvoorbeeld van de Content-Security-Policy, de regels die bepalen welke bestanden de pagina mag laden).
import { connect, check, sleep, rows } from "./lib.mjs";

const page = await connect();
const problems = [];
// Twee soorten meldingen tellen hier niet mee, omdat ze niet over de labelpagina zelf gaan:
// - een geweigerde of verbroken verbinding (net::ERR_CONNECTION_RESET of net::ERR_SOCKET_NOT_CONNECTED). Die komt
//   voor vlak nadat een eerdere test de demo-app opnieuw startte, of als de app het even te druk heeft en de browser
//   meer verbindingen tegelijk opent dan de app aanneemt. Dat laatste controleert test_server_start.py ("drukke
//   computer") zonder toeval; hier zou het de uitkomst laten afhangen van hoe druk de computer toevallig is;
// - /favicon.ico (het pictogram van het tabblad): dat vraagt Chrome zelf op, soms wel en soms niet. De app heeft geen
//   pictogram en levert alleen web/, images/ en items.json, dus dat verzoek geeft altijd 404 (niet gevonden).
// Alle andere meldingen tellen wel, ook een bestand dat de app niet levert (404) of een fout in de app (500).
const CONNECTION = /net::ERR_(CONNECTION_RESET|SOCKET_NOT_CONNECTED)\b/;
page.on("Log.entryAdded", ({ entry }) => {
  const address = (entry.url || "").replace(/^https?:\/\/[^/]+/, "");
  if (!["error", "warning"].includes(entry.level) || CONNECTION.test(entry.text) || address === "/favicon.ico") return;
  problems.push(`${entry.text}${address ? ` (${address})` : ""}`);
});
page.on("Runtime.exceptionThrown", ({ exceptionDetails }) => problems.push(exceptionDetails.exception?.description || exceptionDetails.text));
// Log.enable stuurt ook de meldingen van vóór deze test nog een keer; die tellen niet mee.
await page.send("Log.enable"); await sleep(200);
problems.length = 0;

await page.fresh({ name: "" });
check("zonder naam staat de cursor in het naamvak", await page.js(`document.activeElement.id === "labeler"`));
await page.js(`document.activeElement.blur(); true`);
await page.key("7"); await sleep(600);
check("zonder naam: melding 'Vul eerst ... je naam in'", (await page.text("error")).startsWith("Vul eerst"));
check("zonder naam wordt niets opgeslagen", rows().length === 0);
check("zonder naam wordt ook in de pagina niets als gekozen getoond", (await page.js(`Object.keys(state.labels).length`)) === 0);
await page.js(`(() => { const i = document.getElementById("labeler"); i.value = "Tester"; i.dispatchEvent(new Event("input")); i.blur(); return true; })()`);
check("na het invullen van een naam verdwijnt de melding", !(await page.visible("error")));
await page.ready();
await page.key("7"); await sleep(800); await page.saved();
const row = rows()[0];
check("met naam wordt opgeslagen, met die naam", row?.label === "unknown" && row?.how === "chosen" && row?.labeler === "Tester", JSON.stringify(row));
await page.show(await page.find(`i.kind === "track"`));
await page.js(`document.getElementById("brighter").click(); true`); await sleep(300);
check("geen fouten of beveiligingsmeldingen in de browser", problems.length === 0, JSON.stringify(problems).slice(0, 800));
await page.js(`document.getElementById("brighter").click(); true`);
page.close();
