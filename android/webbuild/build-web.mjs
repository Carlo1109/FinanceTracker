/**
 * Costruisce il bundle web OFFLINE dell'app Android.
 *
 *   node build-web.mjs [cartella-output]
 *
 * Output (default): android/app/src/main/assets/web
 *
 *   index.html, android-bridge.js,    pagina che avvia l'app (android/web)
 *   native.js, touch.js               cartella dei dati e blocco; ritocchi per il touch
 *   stlite/                           Streamlit per il browser (@stlite/browser)
 *   pyodide/                          Python 3.14 WebAssembly + SOLO i pacchetti
 *                                     necessari + pyodide-lock.json "congelato"
 *   app/                              il codice Python dell'app (app.py, src/, ...)
 *   app-manifest.json                 elenco file da montare + requisiti
 *   vendor/plotly.min.js              plotly.js per il grafico a ciambella
 *   fonts/                            Manrope e Fraunces (da static/fonts, come il desktop)
 *
 * Come funziona l'offline: qui (con internet) si avvia Pyodide in Node,
 * si installano Streamlit (versione stlite), plotly e openpyxl con micropip,
 * poi micropip.freeze() produce un lockfile con TUTTI i pacchetti usati.
 * Scarichiamo quei file accanto a Pyodide e riscriviamo il lockfile perché
 * punti ai file locali: sul telefono micropip trova tutto lì e non va in rete.
 */

import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { unzipSync } from "fflate";
import { loadPyodide } from "pyodide";

// ---------------------------------------------------------------- config

// Pacchetti dell'app oltre a Streamlit (stesse versioni del desktop).
const APP_REQUIREMENTS = ["plotly==6.8.0", "openpyxl==3.1.5"];

// File dell'app da includere (relativi alla radice della repo).
const APP_FILE_PATTERNS = [
  "app.py",
  "VERSION",
  ".streamlit/config.toml",
  "config/categories.json",
  "assets/icons/ft_logo.png",
  "src/**/*.py",
];

// Font: gli stessi file della versione desktop (static/fonts nella repo).
const FONT_DIR_IN_REPO = "static/fonts";

// ---------------------------------------------------------------- paths

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "..", "..");
const WEB_TEMPLATE = path.resolve(HERE, "..", "web");
const OUT = path.resolve(
  process.argv[2] || path.join(REPO, "android", "app", "src", "main", "assets", "web"),
);
const CACHE = path.join(HERE, ".cache");
const PKG_CACHE = path.join(CACHE, "pyodide-packages");
const NODE_MODULES = path.join(HERE, "node_modules");
const PYODIDE_DIR = path.join(NODE_MODULES, "pyodide");
const STLITE_DIR = path.join(NODE_MODULES, "@stlite", "browser", "build");

// ---------------------------------------------------------------- helpers

const log = (...args) => console.log("[build-web]", ...args);

function rmrf(p) {
  fs.rmSync(p, { recursive: true, force: true });
}

function mkdirp(p) {
  fs.mkdirSync(p, { recursive: true });
}

function copyFile(src, dst) {
  mkdirp(path.dirname(dst));
  fs.copyFileSync(src, dst);
}

function copyDir(src, dst, filter = () => true) {
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dst, entry.name);
    if (!filter(s, entry)) continue;
    if (entry.isDirectory()) copyDir(s, d, filter);
    else copyFile(s, d);
  }
}

function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

function canonicalName(name) {
  return String(name).toLowerCase().replace(/[-_.]+/g, "-");
}

function globToRegExp(pattern) {
  const escaped = pattern
    .split("**/")
    .map((part) =>
      part
        .replace(/[.+^${}()|[\]\\]/g, "\\$&")
        .replace(/\*/g, "[^/]*")
        .replace(/\?/g, "[^/]"),
    )
    .join("(?:.*/)?");
  return new RegExp(`^${escaped}$`);
}

function listRepoFiles(dir = REPO, prefix = "") {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (["node_modules", ".git", "__pycache__", "android", "build", "dist"].includes(entry.name)) {
      continue;
    }
    const rel = prefix ? `${prefix}/${entry.name}` : entry.name;
    if (entry.isDirectory()) out.push(...listRepoFiles(path.join(dir, entry.name), rel));
    else out.push(rel);
  }
  return out;
}

async function download(url, attempts = 4) {
  let lastError;
  for (let i = 1; i <= attempts; i++) {
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return Buffer.from(await response.arrayBuffer());
    } catch (error) {
      lastError = error;
      log(`  download fallito (${i}/${attempts}) ${url}: ${error.message}`);
      await new Promise((r) => setTimeout(r, 1500 * i));
    }
  }
  throw new Error(`Impossibile scaricare ${url}: ${lastError?.message}`);
}

// ---------------------------------------------------------------- steps

function copyTemplateAndStlite() {
  log("Pagina di avvio e stlite");
  copyFile(path.join(WEB_TEMPLATE, "index.html"), path.join(OUT, "index.html"));
  copyFile(path.join(WEB_TEMPLATE, "android-bridge.js"), path.join(OUT, "android-bridge.js"));
  copyFile(path.join(WEB_TEMPLATE, "native.js"), path.join(OUT, "native.js"));
  copyFile(path.join(WEB_TEMPLATE, "touch.js"), path.join(OUT, "touch.js"));
  copyDir(STLITE_DIR, path.join(OUT, "stlite"), (p) => !p.endsWith(".map"));
}

function copyFonts() {
  log("Font locali");
  const src = path.join(REPO, FONT_DIR_IN_REPO);
  const css = [];
  for (const file of fs.readdirSync(src).sort()) {
    if (file.endsWith(".txt")) {
      copyFile(path.join(src, file), path.join(OUT, "fonts", file)); // licenze OFL
      continue;
    }
    const match = /^([a-z]+)-latin-(\d+)-normal\.woff2$/.exec(file);
    if (!match) continue;
    const family = match[1][0].toUpperCase() + match[1].slice(1);
    copyFile(path.join(src, file), path.join(OUT, "fonts", file));
    css.push(
      `@font-face{font-family:"${family}";font-style:normal;font-weight:${match[2]};` +
        `font-display:swap;src:url("/fonts/${file}") format("woff2");}`,
    );
  }
  if (!css.length) throw new Error(`Nessun font trovato in ${FONT_DIR_IN_REPO}`);
  fs.writeFileSync(path.join(OUT, "fonts", "fonts.css"), css.join("\n") + "\n");
}

function copyAppFiles() {
  log("Codice dell'app");
  const regexps = APP_FILE_PATTERNS.map(globToRegExp);
  const files = listRepoFiles().filter((rel) => regexps.some((re) => re.test(rel)));
  if (!files.includes("app.py")) throw new Error("app.py non trovato nella radice della repo");
  for (const rel of files) copyFile(path.join(REPO, rel), path.join(OUT, "app", rel));
  log(`  ${files.length} file`);
  return files.sort();
}

async function freezePythonEnvironment(appFiles) {
  log("Pyodide: installazione pacchetti e lockfile offline");
  mkdirp(PKG_CACHE);

  const pyodide = await loadPyodide({
    indexURL: PYODIDE_DIR + path.sep,
    packageCacheDir: PKG_CACHE,
    stdout: (s) => console.log("  [py]", s),
    stderr: (s) => console.error("  [py]", s),
  });

  await pyodide.loadPackage("micropip");
  const micropip = pyodide.pyimport("micropip");

  // Wheel di Streamlit / stlite_lib inclusi in @stlite/browser.
  const wheelDir = path.join(STLITE_DIR, "wheels");
  const systemWheels = [];
  pyodide.FS.mkdirTree("/tmp/wheels");
  for (const name of fs.readdirSync(wheelDir).filter((n) => n.endsWith(".whl"))) {
    pyodide.FS.writeFile(`/tmp/wheels/${name}`, fs.readFileSync(path.join(wheelDir, name)));
    systemWheels.push(`emfs:/tmp/wheels/${name}`);
  }

  await micropip.install.callKwargs([...systemWheels, ...APP_REQUIREMENTS], {
    keep_going: true,
  });

  // Il codice dell'app gira davvero sotto Python 3.14 / WebAssembly:
  // compilazione di tutti i file + un giro completo su un database di prova.
  for (const rel of appFiles) {
    pyodide.FS.mkdirTree(path.posix.dirname(`/home/pyodide/ftcheck/${rel}`));
    pyodide.FS.writeFile(`/home/pyodide/ftcheck/${rel}`, fs.readFileSync(path.join(REPO, rel)));
  }
  await pyodide.runPythonAsync(`
import compileall, os, sys, datetime
os.environ["FT_DATA_DIR"] = "/tmp/ftcheck-data"
os.environ["FT_PLATFORM"] = "android"
sys.path.insert(0, "/home/pyodide/ftcheck")
assert compileall.compile_dir("/home/pyodide/ftcheck", quiet=1), "Errori di sintassi nel codice"

import sqlite3, pandas, numpy, pyarrow, plotly, openpyxl, PIL, streamlit
print("streamlit", streamlit.__version__, "| pandas", pandas.__version__, "| plotly", plotly.__version__)

from src.database.db import init_db
from src.services.movement_service import add_manual_movement, load_movements
from src.services.backup_service import build_backup_bytes
from src.utils.export_excel import movements_to_export_bytes

init_db()
add_manual_movement(datetime.date(2026, 1, 15), "Prova build", 12.5, "Alimentari", "Uscita", "Fineco")
df = load_movements()
assert len(df) == 1, df
assert len(movements_to_export_bytes(df)) > 1000
name, data = build_backup_bytes()
assert data[:2] == b"PK", name
print("Controllo app OK:", len(df), "movimento, export Excel e backup generati")
`);

  const lock = JSON.parse(micropip.freeze());
  const installed = pyodide
    .runPython("import micropip\n[str(name) for name in micropip.list()]")
    .toJs()
    .map(canonicalName);

  return { lock, installed };
}

// Il lockfile congelato può indicare i file in tre modi:
//  - URL (pacchetti presi da PyPI da micropip)          -> download
//  - percorso assoluto nella cache locale di Node       -> lettura dal disco
//  - nome relativo (pacchetti della distribuzione Pyodide) -> cache o CDN
async function fetchPackageFile(key, source, cdn) {
  if (/^https?:\/\//.test(source)) {
    const fileName = decodeURIComponent(new URL(source).pathname.split("/").pop());
    return { fileName, data: await download(source) };
  }
  if (source.startsWith("emfs:")) {
    throw new Error(`Pacchetto ${key} installato da file locale non previsto: ${source}`);
  }

  const localPath = source.startsWith("file://") ? fileURLToPath(source) : source;
  const fileName = path.basename(localPath);
  const candidates = [
    path.isAbsolute(localPath) ? localPath : null,
    path.join(PKG_CACHE, fileName),
    path.join(PYODIDE_DIR, fileName),
  ].filter(Boolean);

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) return { fileName, data: fs.readFileSync(candidate) };
  }
  return { fileName, data: await download(cdn + fileName) };
}

async function writeOfflinePyodide({ lock, installed }) {
  const outDir = path.join(OUT, "pyodide");
  log("Pyodide offline in", path.relative(REPO, outDir));

  // Nucleo di Pyodide (interprete + libreria standard).
  copyDir(PYODIDE_DIR, outDir, (p, entry) => {
    if (entry.isDirectory()) return false;
    const name = path.basename(p);
    return !(
      name.endsWith(".map") ||
      name.endsWith(".d.ts") ||
      name.endsWith(".html") ||
      name === "package.json" ||
      name === "README.md" ||
      name === "pyodide-lock.json"
    );
  });

  const byCanonical = new Map(
    Object.entries(lock.packages).map(([key, pkg]) => [canonicalName(key), key]),
  );

  // Pacchetti necessari = installati + dipendenze (librerie condivise incluse).
  const needed = new Set();
  const queue = [...installed, "micropip"];
  while (queue.length) {
    const name = canonicalName(queue.pop());
    if (needed.has(name)) continue;
    const key = byCanonical.get(name);
    if (!key) continue;
    needed.add(name);
    for (const dep of lock.packages[key].depends || []) queue.push(dep);
  }

  // Streamlit e stlite_lib li installa stlite dai suoi wheel locali.
  for (const name of ["streamlit", "stlite-lib"]) needed.delete(name);

  const missing = installed.filter(
    (n) => !needed.has(n) && !["streamlit", "stlite-lib"].includes(n) && !byCanonical.has(n),
  );
  if (missing.length) log("  (senza voce nel lockfile, ignorati):", missing.join(", "));

  const packages = {};
  let totalBytes = 0;
  const cdn = `https://cdn.jsdelivr.net/pyodide/v${lock.info.version ?? pyodideVersion()}/full/`;

  for (const name of [...needed].sort()) {
    const key = byCanonical.get(name);
    const pkg = { ...lock.packages[key] };
    const source = String(pkg.file_name);

    const { fileName, data } = await fetchPackageFile(key, source, cdn);
    if (pkg.sha256 && sha256(data) !== pkg.sha256) {
      throw new Error(`Checksum errato per ${fileName}`);
    }

    fs.writeFileSync(path.join(outDir, fileName), data);
    totalBytes += data.length;
    pkg.file_name = fileName;
    packages[key] = pkg;
  }

  fs.writeFileSync(
    path.join(outDir, "pyodide-lock.json"),
    JSON.stringify({ info: lock.info, packages }, null, 1),
  );

  log(`  ${Object.keys(packages).length} pacchetti, ${(totalBytes / 1e6).toFixed(1)} MB`);
  return packages;
}

function pyodideVersion() {
  return JSON.parse(fs.readFileSync(path.join(PYODIDE_DIR, "package.json"), "utf8")).version;
}

function extractPlotlyJs(packages) {
  log("plotly.js locale");
  const entry = Object.values(packages).find((p) => canonicalName(p.name) === "plotly");
  if (!entry) throw new Error("plotly non presente nel lockfile");
  const wheel = fs.readFileSync(path.join(OUT, "pyodide", entry.file_name));
  const files = unzipSync(new Uint8Array(wheel), {
    filter: (f) => f.name === "plotly/package_data/plotly.min.js",
  });
  const js = files["plotly/package_data/plotly.min.js"];
  if (!js) throw new Error("plotly.min.js non trovato nel wheel di plotly");
  copyBuffer(js, path.join(OUT, "vendor", "plotly.min.js"));
}

function copyBuffer(buffer, dst) {
  mkdirp(path.dirname(dst));
  fs.writeFileSync(dst, buffer);
}

function writeManifest(appFiles) {
  const manifest = {
    files: appFiles,
    requirements: APP_REQUIREMENTS,
    builtAt: new Date().toISOString(),
  };
  fs.writeFileSync(path.join(OUT, "app-manifest.json"), JSON.stringify(manifest, null, 2));
}

function dirSize(dir) {
  let total = 0;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    total += entry.isDirectory() ? dirSize(p) : fs.statSync(p).size;
  }
  return total;
}

// ---------------------------------------------------------------- main

const onlyStatic = process.env.FT_SKIP_PYODIDE === "1";

rmrf(OUT);
mkdirp(OUT);
copyTemplateAndStlite();
copyFonts();
const appFiles = copyAppFiles();
writeManifest(appFiles);

if (onlyStatic) {
  log("FT_SKIP_PYODIDE=1: salto Pyodide (solo per prove locali)");
} else {
  const frozen = await freezePythonEnvironment(appFiles);
  const packages = await writeOfflinePyodide(frozen);
  extractPlotlyJs(packages);
}

log(`Fatto: ${path.relative(REPO, OUT)} (${(dirSize(OUT) / 1e6).toFixed(1)} MB)`);
