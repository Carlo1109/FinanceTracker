/*
 * Funzioni native dell'app Android (cartella dei dati e blocco).
 *
 * Cartella dei dati
 *   L'utente sceglie una cartella sul telefono. All'avvio l'app legge da lì
 *   finance_tracker.db e categories.json; poi, ogni 2 secondi e quando l'app
 *   va in background, se Python li ha modificati li ricopia nella cartella.
 *   Se il file nella cartella è stato cambiato da altri (es. un'app di
 *   sincronizzazione), non lo sovrascrive e chiede cosa fare.
 *
 * Blocco
 *   Attiva/disattiva lo sblocco con impronta, volto o PIN del telefono
 *   (gestito da MainActivity).
 *
 * I controlli compaiono in Opzioni → Dati: Python disegna dei segnaposto
 * <div data-ft-widget="storage|lock"> e questo file li riempie.
 *
 * Fuori dall'app Android (window.FTAndroid assente) non fa nulla.
 */

const bridge = window.FTAndroid;

/*
 * Cartella dei dati sul telefono: per ora SPENTA (v1.7.0).
 * Il codice è completo ma la prova automatica su GitHub non riusciva a
 * superare la scelta della cartella al primo avvio. Per riattivarla:
 * true qui e FT_TEST_FOLDER=1 nella prova (android/webbuild/smoke-test.mjs).
 */
const FOLDER_STORAGE_ENABLED = false;

export const DATA_FILES = ["finance_tracker.db", "categories.json"];
const SYNC_INTERVAL_MS = 2000;

export function available() {
  return !!(bridge && typeof bridge.storageState === "function");
}

function call(name, ...args) {
  try {
    return JSON.parse(bridge[name](...args));
  } catch (error) {
    return { ok: false, error: String(error) };
  }
}

// ------------------------------------------------------------------ utilità

function base64ToBytes(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

function bytesToBase64(bytes) {
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
  }
  return btoa(binary);
}

/** Impronta veloce del contenuto (FNV-1a + lunghezza). */
function fingerprint(bytes) {
  let hash = 0x811c9dc5;
  for (let i = 0; i < bytes.length; i++) {
    hash ^= bytes[i];
    hash = Math.imul(hash, 0x01000193);
  }
  return `${bytes.length}:${(hash >>> 0).toString(16)}`;
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

function timeLabel(date) {
  return date.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
}

// ------------------------------------------------------------------ cartella

const sync = {
  configured: false,
  label: "",
  known: {},          // file -> { size, modified, hash } come sono nella cartella
  conflict: null,     // nome del file cambiato da fuori
  pendingChoice: false,
  lastSaved: null,
  lastError: null,
};

let kernel = null;
let mirrorRunning = false;
const listeners = new Set();

function notify() {
  listeners.forEach((fn) => fn());
}

export function storageState() {
  return available() ? call("storageState") : { configured: false, prompted: true, label: "" };
}

export function pickFolder() {
  return new Promise((resolve) => {
    window.__ftFolderPicked = (result) => {
      window.__ftFolderPicked = null;
      resolve(result || { ok: false });
    };
    bridge.pickFolder();
  });
}

/**
 * Primo avvio: se l'utente non ha ancora scelto, mostra la scelta della
 * cartella dentro la schermata di avvio e aspetta la risposta.
 */
export async function firstRunFolderChoice(ui) {
  if (!available() || !FOLDER_STORAGE_ENABLED) return;
  const state = storageState();
  if (state.configured || state.prompted) return;

  ui.show();
  await new Promise((resolve) => {
    ui.pick.onclick = async () => {
      ui.error.textContent = "";
      const result = await pickFolder();
      if (result.ok) resolve();
      else if (result.error) ui.error.textContent = result.error;
    };
    ui.skip.onclick = () => {
      bridge.skipFolderPrompt();
      resolve();
    };
  });
  ui.hide();
}

/**
 * File della cartella da montare in Python all'avvio (la cartella vince
 * sulla copia interna). Restituisce { "/data/<file>": { data } }.
 */
export function loadInitialFiles() {
  const files = {};
  if (!available() || !FOLDER_STORAGE_ENABLED) return files;

  const state = storageState();
  sync.configured = !!state.configured;
  sync.label = state.label || "";
  if (!sync.configured) return files;

  for (const name of DATA_FILES) {
    const result = call("folderRead", name);
    if (!result.ok) {
      sync.lastError = `Lettura di ${name} non riuscita: ${result.error}`;
      continue;
    }
    if (result.missing) continue;
    const bytes = base64ToBytes(result.data);
    files[`/data/${name}`] = { data: bytes };
    sync.known[name] = { size: result.size, modified: result.modified, hash: fingerprint(bytes) };
  }
  return files;
}

// Lettura dei file di Python tramite un piccolo codice Python: se il file
// non esiste ancora restituisce "" invece di un errore (la lettura diretta
// del filesystem di stlite, in quel caso, non risponde più).
const PY_STAT = (path) => `
import os
_ft_p = ${JSON.stringify(path)}
"" if not os.path.exists(_ft_p) else f"{os.stat(_ft_p).st_size}:{os.stat(_ft_p).st_mtime_ns}"
`;

const PY_READ = (path) => `
import os, base64
_ft_p = ${JSON.stringify(path)}
"" if not os.path.exists(_ft_p) else base64.b64encode(open(_ft_p, "rb").read()).decode("ascii")
`;

const pythonStat = {}; // file -> "dimensione:modifica" dell'ultima lettura

function withTimeout(promise, ms) {
  return Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), ms)),
  ]);
}

/**
 * Contenuto del file in Python: { bytes, stat }, oppure null se non esiste
 * o se non è cambiato dall'ultimo salvataggio riuscito.
 */
async function readFromPython(name, { force = false } = {}) {
  const path = `/data/${name}`;
  const stat = String(await withTimeout(kernel.runPython(PY_STAT(path)), 10000) ?? "");
  if (!stat) return null;
  if (!force && pythonStat[name] === stat) return null;

  const base64 = String(await withTimeout(kernel.runPython(PY_READ(path)), 10000) ?? "");
  if (!base64) return null;
  return { bytes: base64ToBytes(base64), stat };
}

/** True se il file nella cartella non è quello che ci aspettiamo. */
function changedOutside(name, info) {
  if (!info.exists) return false;
  const known = sync.known[name];
  if (known && info.size === known.size && info.modified === known.modified) return false;

  // Metadati diversi: controlliamo il contenuto (alcuni provider, come quelli
  // cloud, aggiornano la data da soli dopo il caricamento).
  const current = call("folderRead", name);
  if (!current.ok || current.missing) return false;
  const hash = fingerprint(base64ToBytes(current.data));
  if (known && hash === known.hash) {
    sync.known[name] = { size: current.size, modified: current.modified, hash };
    return false;
  }
  return true;
}

export async function mirrorOnce({ force = false } = {}) {
  if (!kernel || !sync.configured || mirrorRunning) return;
  if ((sync.conflict || sync.pendingChoice) && !force) return;

  mirrorRunning = true;
  try {
    for (const name of DATA_FILES) {
      let snapshot;
      try {
        snapshot = await readFromPython(name, { force });
      } catch (error) {
        continue; // Python occupato o non ancora pronto: si riprova al giro dopo
      }
      if (!snapshot) continue;
      const { bytes, stat } = snapshot;

      const hash = fingerprint(bytes);
      if (!force && sync.known[name]?.hash === hash) {
        pythonStat[name] = stat; // già uguale nella cartella
        continue;
      }

      if (!force) {
        const info = call("folderInfo", name);
        if (!info.ok) {
          sync.lastError = info.error;
          continue;
        }
        if (changedOutside(name, info)) {
          sync.conflict = name;
          return;
        }
      }

      const result = call("folderWrite", name, bytesToBase64(bytes));
      if (result.ok) {
        sync.known[name] = { size: result.size, modified: result.modified, hash };
        pythonStat[name] = stat; // salvato: fino alla prossima modifica non serve rileggerlo
        sync.lastSaved = new Date();
        sync.lastError = null;
      } else {
        sync.lastError = `Salvataggio nella cartella non riuscito: ${result.error}`;
      }
    }
    if (force) {
      sync.conflict = null;
      sync.pendingChoice = false;
    }
  } finally {
    mirrorRunning = false;
    notify();
  }
}

async function changeFolder() {
  const result = await pickFolder();
  if (!result.ok) {
    if (result.error) sync.lastError = result.error;
    notify();
    return;
  }
  sync.configured = true;
  sync.label = result.label || "";
  sync.known = {};
  sync.conflict = null;
  sync.lastError = null;
  if (result.hasData) {
    sync.pendingChoice = true; // la nuova cartella ha già dei dati: chiediamo
    notify();
  } else {
    await mirrorOnce({ force: true });
  }
}

// ------------------------------------------------------------------ blocco

let lockMessage = null;

window.__ftLockChanged = (result) => {
  lockMessage = result && !result.ok ? result.error : null;
  notify();
};

function lockState() {
  return bridge && typeof bridge.lockState === "function"
    ? call("lockState")
    : { available: false, enabled: false };
}

// ------------------------------------------------------------------ interfaccia

const STYLES = `
/* Controlli nativi in Opzioni → Dati e avviso di conflitto. */
[data-ft-widget] {
  font-family: var(--ft-font, "Manrope", system-ui, sans-serif);
  color: var(--ft-text, #eef3ff);
}

.ft-nw-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 650;
}

.ft-nw-dot {
  width: 9px;
  height: 9px;
  flex: none;
  border-radius: 99px;
  background: var(--ft-muted, #94a3b8);
}

.ft-nw-dot.is-ok { background: #34d399; }
.ft-nw-dot.is-warn { background: #fbbf24; }

.ft-nw-text { font-size: 14px; line-height: 1.5; }

.ft-nw-sub {
  margin-top: 6px;
  color: var(--ft-muted, #94a3b8);
  font-size: 13px;
  line-height: 1.5;
}

.ft-nw-error {
  margin-top: 8px;
  color: var(--ft-danger, #f87171);
  font-size: 13px;
  line-height: 1.45;
}

.ft-nw-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.ft-nw-btn {
  flex: 1 1 auto;
  min-height: 42px;
  padding: 0 16px;
  border-radius: 12px;
  border: 1px solid var(--ft-border, rgba(148, 163, 184, 0.3));
  background: transparent;
  color: var(--ft-text, #eef3ff);
  font: 700 14px var(--ft-font, "Manrope", system-ui, sans-serif);
  -webkit-tap-highlight-color: transparent;
}

.ft-nw-btn.is-primary {
  border: 0;
  background: var(--ft-accent, #60a5fa);
  color: var(--ft-primary-btn-text, #04203a);
}

.ft-nw-btn:active { transform: scale(0.97); }

#ft-conflict {
  position: fixed;
  left: 10px;
  right: 10px;
  top: calc(10px + env(safe-area-inset-top));
  z-index: 1000000;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(251, 191, 36, 0.45);
  background-color: var(--ft-bg-1, #0b1220);
  background-image: linear-gradient(var(--ft-panel, #111a2e), var(--ft-panel, #111a2e));
  box-shadow: 0 14px 40px rgba(0, 0, 0, 0.45);
  color: var(--ft-text, #eef3ff);
  font-family: var(--ft-font, "Manrope", system-ui, sans-serif);
}
`;

function injectStyles() {
  if (document.getElementById("ft-native-styles")) return;
  const style = document.createElement("style");
  style.id = "ft-native-styles";
  style.textContent = STYLES;
  document.head.appendChild(style);
}

function renderStorage(el) {
  let html;
  if (!FOLDER_STORAGE_ENABLED) {
    el.innerHTML = `
      <div class="ft-nw-status"><span class="ft-nw-dot is-ok"></span>Memoria interna dell'app</div>
      <div class="ft-nw-sub">Movimenti, categorie e impostazioni restano sul telefono, privati e offline,
        esclusi dal backup automatico di Google. Si perdono solo disinstallando l'app:
        fai ogni tanto un backup (qui sotto).</div>`;
    return;
  }
  if (sync.pendingChoice) {
    html = `
      <div class="ft-nw-text"><b>${escapeHtml(sync.label)}</b> contiene già dei dati FinanceTracker.</div>
      <div class="ft-nw-actions">
        <button class="ft-nw-btn is-primary" data-act="use-folder">Usa i dati della cartella</button>
        <button class="ft-nw-btn" data-act="overwrite">Sostituiscili con questi</button>
      </div>
      <div class="ft-nw-sub">«Usa i dati della cartella» riapre l'app con quei dati.</div>`;
  } else if (sync.configured) {
    const saved = sync.lastSaved ? ` Ultimo salvataggio: ${timeLabel(sync.lastSaved)}.` : "";
    html = `
      <div class="ft-nw-status"><span class="ft-nw-dot is-ok"></span>
        Cartella: <b>${escapeHtml(sync.label || "scelta")}</b></div>
      <div class="ft-nw-sub">Database, categorie e backup vengono salvati qui dopo ogni modifica:
        li vedi dall'app File e restano anche se disinstalli l'app.${saved}</div>
      <div class="ft-nw-actions"><button class="ft-nw-btn" data-act="change">Cambia cartella</button></div>`;
  } else {
    html = `
      <div class="ft-nw-status"><span class="ft-nw-dot is-warn"></span>
        Dati solo nella memoria interna dell'app</div>
      <div class="ft-nw-sub">Si perdono se disinstalli l'app. Scegli una cartella del telefono
        per averli visibili e al sicuro, come sul PC.</div>
      <div class="ft-nw-actions"><button class="ft-nw-btn is-primary" data-act="change">Scegli una cartella</button></div>`;
  }
  if (sync.lastError) html += `<div class="ft-nw-error">${escapeHtml(sync.lastError)}</div>`;
  el.innerHTML = html;
}

function renderLock(el) {
  const state = lockState();
  let html;
  if (!state.available && !state.enabled) {
    html = `
      <div class="ft-nw-status"><span class="ft-nw-dot"></span>Non disponibile</div>
      <div class="ft-nw-sub">Per usarlo imposta prima un blocco schermo (PIN, sequenza o impronta)
        nelle impostazioni del telefono.</div>`;
  } else if (state.enabled) {
    html = `
      <div class="ft-nw-status"><span class="ft-nw-dot is-ok"></span>Attivo</div>
      <div class="ft-nw-sub">L'app chiede impronta, volto o PIN all'apertura e quando ci torni dopo
        30 secondi. Screenshot e anteprima tra le app recenti sono nascosti.</div>
      <div class="ft-nw-actions"><button class="ft-nw-btn" data-act="lock-off">Disattiva blocco</button></div>`;
  } else {
    html = `
      <div class="ft-nw-status"><span class="ft-nw-dot"></span>Disattivo</div>
      <div class="ft-nw-sub">Usa lo stesso sblocco del telefono: impronta, volto o PIN.
        Nessuna password in più da ricordare.</div>
      <div class="ft-nw-actions"><button class="ft-nw-btn is-primary" data-act="lock-on">Attiva blocco</button></div>`;
  }
  if (lockMessage) html += `<div class="ft-nw-error">${escapeHtml(lockMessage)}</div>`;
  el.innerHTML = html;
}

const RENDERERS = { storage: renderStorage, lock: renderLock };

function renderWidgets() {
  document.querySelectorAll("[data-ft-widget]").forEach((el) => {
    const render = RENDERERS[el.dataset.ftWidget];
    if (render) render(el);
  });
  renderConflictBanner();
}

function renderConflictBanner() {
  let banner = document.getElementById("ft-conflict");
  if (!sync.conflict) {
    banner?.remove();
    return;
  }
  if (!banner) {
    banner = document.createElement("div");
    banner.id = "ft-conflict";
    document.body.appendChild(banner);
  }
  banner.innerHTML = `
    <div class="ft-nw-text"><b>Il file ${escapeHtml(sync.conflict)} nella cartella è cambiato fuori dall'app</b>
      (per esempio da una sincronizzazione). Per non perdere nulla non l'ho sovrascritto.</div>
    <div class="ft-nw-actions">
      <button class="ft-nw-btn is-primary" data-act="use-folder">Carica quello della cartella</button>
      <button class="ft-nw-btn" data-act="overwrite">Tieni quello dell'app</button>
    </div>
    <div class="ft-nw-sub">«Carica quello della cartella» riapre l'app: le modifiche fatte qui dopo
      l'ultimo salvataggio non verranno tenute.</div>`;
}

async function handleAction(action) {
  if (action === "change") await changeFolder();
  else if (action === "use-folder") location.reload();
  else if (action === "overwrite") await mirrorOnce({ force: true });
  else if (action === "lock-on") bridge.setLockEnabled(true);
  else if (action === "lock-off") bridge.setLockEnabled(false);
  renderWidgets();
}

/** Avvia salvataggi nella cartella e controlli in Opzioni (dopo il mount di stlite). */
export function start(stlite) {
  if (!available()) return;
  kernel = stlite;

  injectStyles();
  listeners.add(renderWidgets);

  document.addEventListener("click", (event) => {
    const button = event.target.closest?.("[data-act]");
    if (!button || !button.closest("[data-ft-widget], #ft-conflict")) return;
    event.preventDefault();
    handleAction(button.dataset.act);
  });

  // Riempie i segnaposto quando Streamlit li (ri)disegna.
  const observer = new MutationObserver(() => {
    document.querySelectorAll("[data-ft-widget]:not([data-ft-ready])").forEach((el) => {
      el.dataset.ftReady = "1";
      const render = RENDERERS[el.dataset.ftWidget];
      if (render) render(el);
    });
  });
  observer.observe(document.body, { childList: true, subtree: true });

  if (!FOLDER_STORAGE_ENABLED) return;

  // I salvataggi nella cartella partono solo ad app pronta (mai durante l'avvio).
  const startMirroring = () => {
    setInterval(() => mirrorOnce(), SYNC_INTERVAL_MS);
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) mirrorOnce();
    });
  };
  if (document.querySelector(".ft-mtop")) {
    startMirroring();
  } else {
    const ready = new MutationObserver(() => {
      if (document.querySelector(".ft-mtop")) {
        ready.disconnect();
        startMirroring();
      }
    });
    ready.observe(document.body, { childList: true, subtree: true });
  }
}
