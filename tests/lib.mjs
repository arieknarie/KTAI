// Gedeelde hulpmiddelen voor de browsertests van de labelapp (de bestanden app_*.mjs en layout_*.mjs).
//
// Een browsertest bestuurt de labelpagina in een Chrome zonder venster (headless) via het DevTools-protocol: de test
// voert stukjes JavaScript uit in de pagina, drukt (nagemaakte) toetsen in en leest daarna wat de pagina toont en
// wat de app in labels.csv heeft gezet.
//
// run_tests.sh start elk testbestand met vier argumenten:
//   1. het adres van de DevTools-poort van de Chrome die run_tests.sh zelf startte, bijvoorbeeld http://127.0.0.1:53124
//   2. de map met de tijdelijke kopie van labeling/ waarin de demo-app draait (de echte labels.csv blijft onaangeroerd)
//   3. de werkmap van deze testronde; daarin staat app.pid, het procesnummer van de demo-app
//   4. het Python-programma waarmee de demo-app draait (nodig als een test de app stopt en weer start)
//
// Elke controle schrijft één regel: "PASS  <wat er gecontroleerd is>" of "FAIL  <wat er gecontroleerd is>  (details)".
// Kan een controle niet, omdat items.json geen geschikt item heeft, dan schrijft de test "OVERGESLAGEN  <naam>  (reden)".

import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";

export const [, , CDP, DEMO, WORK, PYTHON] = process.argv;
if (!PYTHON) {
  console.log("FAIL  dit testbestand hoort gestart te worden door run_tests.sh (zie tests/README.md)");
  process.exit(1);
}

export const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

// Een testbestand dat vastloopt, stopt na vier minuten met een melding; run_tests.sh telt dat als mislukt.
setTimeout(() => {
  console.log("FAIL  het testbestand duurde langer dan 4 minuten en is gestopt");
  process.exit(1);
}, 240_000).unref();

export function check(name, ok, detail = "") {
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}${!ok && detail !== "" ? `  (${detail})` : ""}`);
  return !!ok;
}

export function skip(name, reason) {
  console.log(`OVERGESLAGEN  ${name}  (${reason})`);
}

// ---------- de demo-app ----------

const PIDFILE = path.join(WORK, "app.pid");
const PORTFILE = path.join(DEMO, ".labelapp.port");

// De poort van de demo-app staat in .labelapp.port in de map van de app (de app kiest zelf een vrije poort).
export const port = () => Number(fs.readFileSync(PORTFILE, "utf8").trim());
export const url = (address = "/web/") => `http://127.0.0.1:${port()}${address}`;

const alive = pid => { try { process.kill(pid, 0); return true; } catch { return false; } };

// Stopt de demo-app: alleen het proces waarvan het nummer in app.pid staat (nooit een andere labelapp).
export async function stopApp() {
  const pid = Number(fs.readFileSync(PIDFILE, "utf8").trim());
  if (pid && alive(pid)) process.kill(pid, "SIGTERM");
  // de app haalt .labelapp.port weg als hij stopt
  for (let n = 0; n < 100 && fs.existsSync(PORTFILE); n++) await sleep(100);
  await sleep(300);
}

// Start de demo-app opnieuw (zonder browservenster), zet het nieuwe procesnummer in app.pid en wacht tot de app antwoordt.
export async function startApp() {
  const log = fs.openSync(path.join(WORK, "app.log"), "a");
  const child = spawn(PYTHON, ["-u", "app.py"], {
    cwd: DEMO, env: { ...process.env, LABELAPP_NO_BROWSER: "1" }, detached: true, stdio: ["ignore", log, log],
  });
  fs.writeFileSync(PIDFILE, String(child.pid));
  child.unref();
  fs.closeSync(log);
  const folder = fs.realpathSync(DEMO);
  for (let n = 0; n < 150; n++) {
    try {
      const info = await (await fetch(url("/api/ping"))).json();
      if (fs.realpathSync(info.folder) === folder) return;
    } catch { /* de app is nog aan het starten */ }
    await sleep(100);
  }
  throw new Error("de demo-app startte niet opnieuw (zie app.log in de werkmap)");
}

// ---------- labels.csv van de demo-app ----------

// Eenvoudige CSV-lezer die ook komma's en aanhalingstekens binnen een veld goed leest.
function parseCsv(text) {
  const lines = [];
  let row = [], field = "", quoted = false;
  text = text.replace(/^﻿/, "");
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') quoted = false;
      else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(field); lines.push(row); row = []; field = "";
    } else field += c;
  }
  if (field !== "" || row.length) { row.push(field); lines.push(row); }
  return lines;
}

const LABELS = () => path.join(DEMO, "labels.csv");

// De kolomnamen van labels.csv (leeg als er nog geen labels.csv is).
export function csvHeader() {
  return fs.existsSync(LABELS()) ? (parseCsv(fs.readFileSync(LABELS(), "utf8"))[0] || []) : [];
}

// Alle rijen van labels.csv als {face, item, label, how, labeler, time, source, frame, x, y, w, h}.
export function rows() {
  if (!fs.existsSync(LABELS())) return [];
  const [header, ...lines] = parseCsv(fs.readFileSync(LABELS(), "utf8"));
  return lines.filter(line => line.length > 1).map(line => Object.fromEntries(header.map((h, i) => [h, line[i] ?? ""])));
}

// De rij van één gezicht uit labels.csv, of undefined.
export const rowOf = face => rows().find(r => r.face === face);

export const removeLabels = () => fs.rmSync(LABELS(), { force: true });

// ---------- de browser ----------

// Maakt verbinding met het tabblad van de Chrome van run_tests.sh. Alle testbestanden gebruiken hetzelfde tabblad.
export async function connect() {
  const targets = await (await fetch(CDP + "/json")).json();
  const target = targets.find(t => t.type === "page");
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
  let nextId = 0;
  const pending = new Map(), listeners = [];
  ws.onmessage = message => {
    const msg = JSON.parse(message.data);
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
    if (msg.method) listeners.forEach(([method, fn]) => { if (method === msg.method) fn(msg.params); });
  };
  const send = (method, params = {}) => new Promise(resolve => {
    const id = ++nextId;
    pending.set(id, resolve);
    ws.send(JSON.stringify({ id, method, params }));
  });
  // Valt de verbinding met Chrome onverwacht weg (bijvoorbeeld als het tabblad vastloopt), dan stopt de test meteen met
  // een duidelijke melding, in plaats van stil te blijven wachten op een antwoord dat nooit komt.
  let closing = false;
  ws.onclose = () => {
    if (closing) return;
    console.log("FAIL  de verbinding met Chrome is onverwacht verbroken (is het tabblad van Chrome vastgelopen?)");
    process.exit(1);
  };
  const page = { send, on: (method, fn) => listeners.push([method, fn]), close: () => { closing = true; ws.close(); } };

  // JavaScript uitvoeren in de pagina; geeft de uitkomst terug. Een fout in de pagina stopt de test met een melding.
  page.js = async expression => {
    const answer = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
    if (answer.error) throw new Error(`DevTools: ${answer.error.message}`);
    const details = answer.result.exceptionDetails;
    if (details) throw new Error(`fout in de pagina bij "${expression.slice(0, 80)}": ${details.exception?.description || details.text}`);
    return answer.result.result.value;
  };

  // Wacht tot een uitdrukking in de pagina waar is (hoogstens `ms` milliseconden); geeft true of false.
  page.until = async (expression, ms = 10000) => {
    const end = Date.now() + ms;
    while (Date.now() < end) {
      try { if (await page.js(expression)) return true; } catch { /* de pagina laadt nog */ }
      await sleep(100);
    }
    return false;
  };

  // De vensterbreedte en -hoogte van de pagina (zoals een browservenster van die maat).
  page.size = (width, height) => send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });

  const loaded = `!window.__oudePagina && document.readyState === "complete"`;
  const appReady = `typeof state !== "undefined" && !!state.data && document.getElementById("item-counter").textContent !== ""`;
  // Een adres openen en wachten tot de pagina geladen is (bij de labelpagina: tot de items er staan).
  page.open = async (address, { app = address.includes("/web/") } = {}) => {
    await page.js("window.__oudePagina = true").catch(() => {});
    await send("Page.navigate", { url: address });
    if (!(await page.until(loaded, 15000)) || (app && !(await page.until(appReady, 15000)))) {
      throw new Error(`de pagina ${address} laadde niet`);
    }
    if (app) await page.ready();
  };
  page.reload = async ({ app = true } = {}) => {
    await page.js("window.__oudePagina = true").catch(() => {});
    await send("Page.reload");
    if (!(await page.until(loaded, 15000)) || (app && !(await page.until(appReady, 15000)))) throw new Error("herladen lukte niet");
    if (app) await page.ready();
  };

  // Een schone start: geen labels.csv, niets meer in de opslag van de browser, alleen de naam van de labelaar.
  // De uitleg (rondleiding) staat dan als "al gezien" (uitleg-gezien = 1), behalve als de test de uitleg zelf test.
  page.fresh = async ({ name = "Tester", tourSeen = true } = {}) => {
    await page.open(url("/items.json"), { app: false });   // zelfde adres als de app, maar zonder de app
    await page.js(`localStorage.clear();` + (tourSeen ? ` localStorage.setItem("uitleg-gezien", "1");` : "") +
                  (name ? ` localStorage.setItem("labeler", ${JSON.stringify(name)});` : "") + " true");
    removeLabels();
    await page.open(url());
  };

  // Wacht tot de app een keuze aanneemt: het beeld is geladen en was minstens 0,3 seconde te zien (zie ready() in app.js).
  page.ready = () => page.until("ready()", 5000);

  // Wacht tot de opslagverzoeken van de pagina klaar zijn (zie save() in app.js); daarna staat elke keuze in labels.csv.
  // Zo hangt een controle van labels.csv niet af van hoe snel de computer is.
  page.saved = () => page.js("saving.then(() => true)").catch(() => false);

  // Naar een item gaan (zoals bladeren) en wachten tot het beeld er staat.
  page.show = async index => { await page.js(`show(${index}); true`); await page.ready(); };

  // Een toets indrukken (een nagemaakte toetsaanslag op de pagina). `extra`: bijvoorbeeld { code: "Digit1" } of { ctrlKey: true }.
  page.key = (key, extra = {}, target = "document") =>
    page.js(`${target}.dispatchEvent(new KeyboardEvent("keydown", ${JSON.stringify({ key, bubbles: true, cancelable: true, ...extra })})); true`);

  // Echte muisbewegingen (zoals een mens die sleept), in pixels van het venster.
  page.mouse = (type, x, y) => send("Input.dispatchMouseEvent", { type, x, y, button: "left", buttons: type === "mouseReleased" ? 0 : 1, clickCount: 1 });
  page.drag = async (x1, y1, x2, y2) => {
    await page.mouse("mousePressed", x1, y1);
    for (let k = 1; k <= 5; k++) await page.mouse("mouseMoved", x1 + (x2 - x1) * k / 5, y1 + (y2 - y1) * k / 5);
    await page.mouse("mouseReleased", x2, y2);
  };
  page.click = async selector => {
    const [x, y] = await page.js(`(() => { const r = document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect();
      return [r.left + r.width / 2, r.top + r.height / 2]; })()`);
    await page.mouse("mousePressed", x, y);
    await page.mouse("mouseReleased", x, y);
  };

  // Het eerste item dat voldoet aan `condition` (een uitdrukking met i = het item en n = zijn nummer), waarbij er na
  // dat item nog `after` items komen (zodat de app na een keuze kan doorgaan). -1 als er geen is.
  page.find = (condition, after = 1) =>
    page.js(`state.data.items.findIndex((i, n) => n < state.data.items.length - ${after} && (${condition}))`);

  // Het nummer van het eerste item dat nog niet af is, uitgerekend uit de labels die de app (app.py) bewaard heeft.
  page.firstOpenOnServer = () => page.js(`fetch("/api/labels", { cache: "no-store" }).then(r => r.json())
    .then(labels => state.data.items.findIndex(i => !i.faces.every(f => labels[f.face])))`);

  page.text = id => page.js(`document.getElementById(${JSON.stringify(id)}).textContent`);
  page.visible = id => page.js(`!document.getElementById(${JSON.stringify(id)}).classList.contains("hidden")`);
  page.index = () => page.js("state.index");

  await send("Page.enable");
  await send("Runtime.enable");
  // een venster "Pagina verlaten?" (als er nog keuzes niet opgeslagen zijn) wordt meteen bevestigd
  page.on("Page.javascriptDialogOpening", () => send("Page.handleJavaScriptDialog", { accept: true }));
  await page.size(1440, 860);
  return page;
}
