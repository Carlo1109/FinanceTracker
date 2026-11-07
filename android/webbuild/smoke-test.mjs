/**
 * Prova del bundle web PRIMA di creare l'APK.
 *
 *   node smoke-test.mjs [cartella-bundle] [cartella-screenshot]
 *
 * Apre l'app in Chromium (telefono simulato) con internet BLOCCATO:
 *  - l'app deve avviarsi solo con i file locali (prova dell'offline);
 *  - ogni pagina deve aprirsi senza errori Python;
 *  - un movimento salvato deve esserci ancora dopo il riavvio (persistenza);
 *  - (con FT_TEST_FOLDER=1) cartella dei dati: i dati vanno nella cartella
 *    e tornano da lì dopo una "reinstallazione".
 * Salva uno screenshot per pagina. Esce con codice 1 se qualcosa non va.
 */

import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium, devices } from "playwright";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(process.argv[2] || path.join(HERE, "..", "app", "src", "main", "assets", "web"));
const SHOTS = path.resolve(process.argv[3] || path.join(HERE, "smoke-screenshots"));
const BOOT_TIMEOUT = 300_000;

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".wasm": "application/wasm",
  ".whl": "application/zip",
  ".zip": "application/zip",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
  ".py": "text/plain; charset=utf-8",
  ".toml": "text/plain; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
};

// Stesse regole del server interno dell'app Android (MainActivity.java).
function serve(req, res) {
  let rel = decodeURIComponent(new URL(req.url, "http://x").pathname).replace(/^\/+/, "");
  if (rel === "" || rel.includes("..")) rel = "index.html";
  let file = path.join(ROOT, rel);
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    if (path.extname(rel) === "") file = path.join(ROOT, "index.html");
    else {
      res.writeHead(404).end();
      return;
    }
  }
  res.writeHead(200, {
    "Content-Type": MIME[path.extname(file)] || "application/octet-stream",
    "Access-Control-Allow-Origin": "*",
  });
  fs.createReadStream(file).pipe(res);
}

const server = http.createServer(serve);
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const BASE = `http://127.0.0.1:${server.address().port}`;
fs.mkdirSync(SHOTS, { recursive: true });

const failures = [];
const external = new Set();
const browser = await chromium.launch();
const context = await browser.newContext({ ...devices["Pixel 7"] });

// Niente internet: tutto ciò che non è il server locale viene bloccato.
await context.route("**/*", (route) => {
  const url = route.request().url();
  if (url.startsWith(BASE) || url.startsWith("data:") || url.startsWith("blob:")) {
    return route.continue();
  }
  external.add(new URL(url).host);
  return route.abort();
});

const page = await context.newPage();
page.on("console", (msg) => {
  if (msg.type() === "error") console.log("  [console]", msg.text().slice(0, 400));
});
page.on("pageerror", (err) => console.log("  [pageerror]", err.message));

async function waitForApp(label) {
  const started = Date.now();
  await page.waitForSelector(".ft-mtop", { timeout: BOOT_TIMEOUT });
  await page.waitForTimeout(2500);
  console.log(`  ${label}: pronta in ${((Date.now() - started) / 1000).toFixed(1)}s`);
}

async function checkNoErrors(label) {
  const errors = await page.$$eval('[data-testid="stException"]', (nodes) =>
    nodes.map((n) => n.innerText.slice(0, 1500)),
  );
  if (errors.length) failures.push(`${label}: eccezione Python\n${errors.join("\n---\n")}`);
}

async function shot(name) {
  await page.screenshot({ path: path.join(SHOTS, `${name}.png`) });
}

async function runPython(code) {
  return page.evaluate((c) => window.__ftStlite.runPython(c), code);
}

try {
  console.log("Avvio (offline)...");
  const t0 = Date.now();
  await page.goto(BASE + "/");
  await waitForApp("Dashboard");
  console.log(`  avvio completo in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  await checkNoErrors("Dashboard");
  await shot("01-dashboard");

  const tabs = [
    ["Movimenti", "02-movimenti"],
    ["Nuovo", "03-nuovo-movimento"],
    ["Importa", "04-importa"],
    ["Opzioni", "05-impostazioni"],
    ["Home", "06-dashboard-di-nuovo"],
  ];
  for (const [label, name] of tabs) {
    const t = Date.now();
    await page.locator(".st-key-ft_mobile_tabbar a", { hasText: label }).first().click();
    await page.waitForTimeout(800);
    await page.waitForFunction(
      () => !document.querySelector('[data-stale="true"]'),
      null,
      { timeout: 60_000 },
    );
    console.log(`  ${label}: ${((Date.now() - t) / 1000).toFixed(1)}s`);
    await page.waitForTimeout(1200);
    await checkNoErrors(label);
    await shot(name);
  }

  // Persistenza: salva un movimento, fai girare lo script (sincronizza
  // IndexedDB), riavvia la pagina e verifica che il movimento ci sia ancora.
  console.log("Persistenza dati...");
  await runPython(`
import sys, datetime
if "/home/pyodide" not in sys.path: sys.path.insert(0, "/home/pyodide")
from src.services.movement_service import add_manual_movement
add_manual_movement(datetime.date(2026, 1, 15), "SMOKE TEST", 9.99, "Altro", "Uscita", "Fineco")
`);
  await page.locator(".st-key-ft_mobile_tabbar a", { hasText: "Movimenti" }).first().click();
  await page.waitForTimeout(6000);

  await page.reload();
  await waitForApp("Riavvio");
  const count = await runPython(`
import sys
if "/home/pyodide" not in sys.path: sys.path.insert(0, "/home/pyodide")
from src.services.movement_service import load_movements
df = load_movements()
int((df["descrizione"] == "SMOKE TEST").sum()) if len(df) else 0
`);
  if (Number(count) < 1) failures.push("Persistenza: il movimento salvato è sparito dopo il riavvio");
  else console.log("  ok: dati ancora presenti dopo il riavvio");
} catch (error) {
  failures.push(`Errore durante la prova: ${error.stack || error}`);
  await shot("99-errore").catch(() => {});
}

// ---------------------------------------------------------------------------
// Cartella dei dati (app Android): ponte nativo simulato, Python vero.
//  1. primo avvio: scelta della cartella, poi un movimento viene salvato lì;
//  2. "reinstallazione" (memoria interna vuota): i dati tornano dalla cartella.
// ---------------------------------------------------------------------------

function fakeNativeBridge({ configured, folder }) {
  const store = folder || {};
  let state = { configured, prompted: configured };
  let clock = 1;
  window.__ftFakeFolder = store;
  window.FTAndroid = {
    storageState: () => JSON.stringify({ ...state, label: state.configured ? "Telefono › Documents/FinanceTracker" : "" }),
    pickFolder: () => setTimeout(() => {
      state = { configured: true, prompted: true };
      window.__ftFolderPicked({ ok: true, label: "Telefono › Documents/FinanceTracker", hasData: !!store["finance_tracker.db"] });
    }, 50),
    skipFolderPrompt: () => { state.prompted = true; },
    folderRead: (n) => JSON.stringify(store[n]
      ? { ok: true, data: store[n].data, size: store[n].size, modified: store[n].modified }
      : { ok: true, missing: true }),
    folderInfo: (n) => JSON.stringify(store[n]
      ? { ok: true, exists: true, size: store[n].size, modified: store[n].modified }
      : { ok: true, exists: false }),
    folderWrite: (n, data) => {
      store[n] = { data, size: atob(data).length, modified: ++clock };
      return JSON.stringify({ ok: true, size: store[n].size, modified: store[n].modified });
    },
    lockState: () => JSON.stringify({ available: false, enabled: false }),
    setLockEnabled: () => {},
    saveFile: () => {},
    toast: () => {},
    appReady: () => {},
  };
}

async function folderPage(options) {
  const ctx = await browser.newContext({ ...devices["Pixel 7"] });
  await ctx.route("**/*", (route) => {
    const url = route.request().url();
    return url.startsWith(BASE) || url.startsWith("data:") || url.startsWith("blob:")
      ? route.continue()
      : route.abort();
  });
  await ctx.addInitScript(fakeNativeBridge, options);
  const folderPg = await ctx.newPage();
  folderPg.on("pageerror", (err) => console.log("  [pageerror]", err.message));
  return { ctx, folderPg };
}

// Cartella dei dati: per ora spenta nell'app (vedi FOLDER_STORAGE_ENABLED in android/web/native.js).
if (process.env.FT_TEST_FOLDER === "1" && !failures.length) {
  try {
    console.log("Cartella dei dati: primo avvio...");
    const first = await folderPage({ configured: false, folder: {} });
    await first.folderPg.goto(BASE + "/");
    await first.folderPg.locator("#ft-setup-pick").click({ timeout: 30_000 });
    await first.folderPg.waitForSelector(".ft-mtop", { timeout: BOOT_TIMEOUT });
    await first.folderPg.evaluate((c) => window.__ftStlite.runPython(c), `
import sys, datetime
if "/home/pyodide" not in sys.path: sys.path.insert(0, "/home/pyodide")
from src.services.movement_service import add_manual_movement
add_manual_movement(datetime.date(2026, 2, 2), "CARTELLA TEST", 4.5, "Altro", "Uscita", "Fineco")
`);
    await first.folderPg.waitForFunction(() => {
      const db = window.__ftFakeFolder["finance_tracker.db"];
      return db && atob(db.data).includes("CARTELLA TEST");
    }, null, { timeout: 30_000 });
    console.log("  ok: il movimento è stato salvato nella cartella");

    await first.folderPg.locator(".st-key-ft_mobile_tabbar a", { hasText: "Opzioni" }).first().click();
    await first.folderPg.getByRole("tab", { name: "Dati" }).click();
    await first.folderPg.waitForTimeout(1500);
    const widget = await first.folderPg.locator('[data-ft-widget="storage"]').innerText();
    if (!widget.includes("Documents/FinanceTracker")) failures.push(`Opzioni → Dati non mostra la cartella: ${widget}`);
    await first.folderPg.screenshot({ path: path.join(SHOTS, "07-cartella-dati.png") });

    const savedFolder = await first.folderPg.evaluate(() => window.__ftFakeFolder);
    await first.ctx.close();

    console.log("Cartella dei dati: reinstallazione (memoria interna vuota)...");
    const second = await folderPage({ configured: true, folder: savedFolder });
    await second.folderPg.goto(BASE + "/");
    await second.folderPg.waitForSelector(".ft-mtop", { timeout: BOOT_TIMEOUT });
    const restored = await second.folderPg.evaluate((c) => window.__ftStlite.runPython(c), `
import sys
if "/home/pyodide" not in sys.path: sys.path.insert(0, "/home/pyodide")
from src.services.movement_service import load_movements
df = load_movements()
int((df["descrizione"] == "CARTELLA TEST").sum()) if len(df) else 0
`);
    if (Number(restored) < 1) failures.push("Cartella dei dati: dopo la reinstallazione il movimento non c'è");
    else console.log("  ok: dopo la reinstallazione i dati tornano dalla cartella");
    await second.ctx.close();
  } catch (error) {
    failures.push(`Errore nella prova della cartella dei dati: ${error.stack || error}`);
    for (const ctx of browser.contexts()) {
      for (const pg of ctx.pages()) {
        await pg.screenshot({ path: path.join(SHOTS, "99-errore-cartella.png") }).catch(() => {});
        const splash = await pg.locator("#ft-splash").innerText().catch(() => "");
        if (splash) console.log("  schermata di avvio:", splash.replace(/\s+/g, " ").slice(0, 300));
      }
    }
  }
}

await browser.close();
server.close();

if (external.size) {
  console.log("Richieste esterne bloccate (l'app funziona comunque offline):", [...external].join(", "));
}

if (failures.length) {
  console.error("\nPROVA FALLITA:\n" + failures.map((f) => " - " + f).join("\n"));
  process.exit(1);
}
console.log("\nProva superata: avvio offline, tutte le pagine, persistenza.");
