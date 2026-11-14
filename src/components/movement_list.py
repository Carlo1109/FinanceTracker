"""
Lista dei movimenti come UN SOLO elemento (st.components.v2).

Prima ogni riga creava ~10 elementi Streamlit (contenitore, 4 colonne,
checkbox, 2 blocchi HTML, pulsante): con 40 righe circa 400 elementi
rigenerati a ogni tocco, anche solo per spuntare una casella. Sul telefono,
dove Python gira in WebAssembly, era la parte più lenta dell'app.

Ora la lista è disegnata nel browser: toccare una riga apre la modifica,
la selezione per unire i movimenti vive nel browser (nessun ricaricamento
a ogni spunta) e Python viene richiamato solo per aprire, unire o
mostrare altre righe.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import streamlit as st

from src.utils.st_compat import ensure_component_runtime


_CSS = r"""
:host { display: block; }
.ml {
  font-family: var(--ft-font, "Manrope", system-ui, sans-serif);
  color: var(--ft-text, #e5e7eb);
  -webkit-tap-highlight-color: transparent;
}
.ml-bar {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  margin: 0 0 10px 0; min-height: 34px;
}
.ml-count { font-size: 13px; font-weight: 600; color: var(--ft-muted, #94a3b8); }
.ml-btn {
  appearance: none; border: 1px solid var(--ft-border-strong, rgba(148,163,184,.25));
  background: var(--ft-panel, rgba(17,24,39,.8)); color: var(--ft-text, #fff);
  font: 700 13px/1 var(--ft-font, system-ui); padding: 9px 14px; border-radius: 999px;
  cursor: pointer; transition: background 120ms ease, border-color 120ms ease, transform 120ms ease;
}
.ml-btn:hover { border-color: rgba(var(--ft-accent-rgb, 96,165,250), .55); }
.ml-btn:active { transform: scale(.97); }
.ml-btn.primary {
  background: var(--ft-accent, #60a5fa); border-color: transparent;
  color: var(--ft-primary-btn-text, #04203a);
}
.ml-btn.ghost { background: transparent; }
.ml-group { margin: 0 0 14px 0; }
.ml-day {
  display: flex; justify-content: space-between; align-items: baseline; gap: 10px;
  padding: 6px 6px 8px 6px; font-size: 12px; font-weight: 750; letter-spacing: .06em;
  text-transform: uppercase; color: var(--ft-subtle, #94a3b8);
}
.ml-day b { font-weight: 750; letter-spacing: 0; text-transform: none; font-size: 12.5px; font-variant-numeric: tabular-nums; }
.ml-card {
  border-radius: var(--ft-radius, 20px); overflow: hidden;
  background: var(--ft-panel, rgba(17,24,39,.8));
  border: 1px solid var(--ft-border, rgba(148,163,184,.12));
  box-shadow: var(--ft-shadow-soft, none);
}
.ml-row {
  position: relative; display: flex; align-items: center; gap: 14px;
  padding: 13px 16px; cursor: pointer; outline: none;
  transition: background 120ms ease;
}
.ml-row + .ml-row::before {
  content: ""; position: absolute; top: 0; left: 70px; right: 16px; height: 1px;
  background: var(--ft-border, rgba(148,163,184,.12));
}
.ml-row:focus-visible { background: var(--ft-raised, rgba(148,163,184,.07)); }
/* Solo con un mouse vero: sul telefono :hover resta attivo dopo il tocco. */
@media (hover: hover) {
  .ml-row:hover { background: var(--ft-raised, rgba(148,163,184,.07)); }
  .ml-row:hover .ml-chev { opacity: .8; }
}
.ml-row:active { background: rgba(var(--ft-accent-rgb, 96,165,250), .10); }
.ml-ico {
  position: relative; flex: 0 0 40px; width: 40px; height: 40px; border-radius: 13px;
  display: flex; align-items: center; justify-content: center; font-size: 19px;
  background: rgba(var(--c), .16); box-shadow: inset 0 0 0 1px rgba(var(--c), .22);
}
.ml-check {
  position: absolute; inset: 0; border-radius: 13px; display: none;
  align-items: center; justify-content: center; font-size: 18px; font-weight: 900;
  background: var(--ft-accent, #60a5fa); color: var(--ft-primary-btn-text, #04203a);
}
.ml.selecting .ml-ico { box-shadow: inset 0 0 0 2px var(--ft-border-strong, rgba(148,163,184,.4)); }
.ml-row.sel .ml-check { display: flex; }
.ml-row.sel { background: rgba(var(--ft-accent-rgb, 96,165,250), .10); }
.ml-body { flex: 1 1 auto; min-width: 0; }
.ml-title {
  font-size: 15px; font-weight: 700; line-height: 1.3; color: var(--ft-text, #fff);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.ml-meta {
  margin-top: 3px; display: flex; flex-wrap: wrap; align-items: center; gap: 4px 8px;
  font-size: 12.5px; font-weight: 600; color: var(--ft-muted, #94a3b8); line-height: 1.35;
}
.ml-meta .dot { opacity: .5; }
.ml-flag {
  display: inline-flex; align-items: center; padding: 1px 7px; border-radius: 6px;
  font-size: 11px; font-weight: 750; color: var(--ft-muted, #94a3b8);
  background: var(--ft-raised, rgba(148,163,184,.08));
  box-shadow: inset 0 0 0 1px var(--ft-border, rgba(148,163,184,.14));
}
.ml-amt {
  flex: 0 0 auto; text-align: right; font-size: 15.5px; font-weight: 800;
  font-variant-numeric: tabular-nums; letter-spacing: -0.01em; white-space: nowrap;
}
.ml-amt.income { color: var(--ft-income, #34d399); }
.ml-amt.expense { color: var(--ft-text, #fff); }
.ml-amt.investment { color: var(--ft-investment, #a78bfa); }
.ml-amt.transfer { color: var(--ft-muted, #94a3b8); }
.ml-chev { flex: 0 0 auto; color: var(--ft-subtle, #94a3b8); opacity: .0; transition: opacity 120ms ease; font-size: 18px; margin-left: -4px; }
.ml.selecting .ml-chev { display: none; }
.ml-more { display: flex; justify-content: center; margin: 6px 0 4px 0; }
.ml-sel {
  position: sticky; bottom: 10px; z-index: 3; margin-top: 10px;
  display: none; align-items: center; justify-content: space-between; gap: 10px;
  padding: 10px 10px 10px 16px; border-radius: 18px;
  background: var(--ft-menu-bg, #111827);
  border: 1px solid var(--ft-border-strong, rgba(148,163,184,.25));
  box-shadow: 0 18px 40px -16px rgba(0,0,0,.55);
}
.ml.selecting .ml-sel { display: flex; }
.ml-sel span { font-size: 13px; font-weight: 700; color: var(--ft-muted, #94a3b8); }
.ml-sel div { display: flex; gap: 8px; }
.ml-hint { font-size: 12.5px; color: var(--ft-muted, #94a3b8); margin: -4px 0 10px 2px; display: none; }
.ml.selecting .ml-hint { display: block; }
@media (max-width: 560px) {
  .ml-row { padding: 12px 12px; gap: 12px; }
  .ml-row + .ml-row::before { left: 62px; right: 12px; }
  .ml-ico { flex-basis: 38px; width: 38px; height: 38px; font-size: 18px; border-radius: 12px; }
  .ml-title { font-size: 14.5px; }
  .ml-amt { font-size: 14.5px; }
  .ml-chev { display: none; }
  .ml-sel { bottom: calc(86px + env(safe-area-inset-bottom, 0px)); }
}
"""


_JS = r"""
function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

export default function (component) {
  const { parentElement, data, setTriggerValue } = component;
  const d = data || {};
  const state = parentElement.__ftState || (parentElement.__ftState = { selecting: false, picked: new Set() });

  const ids = new Set();
  (d.groups || []).forEach((g) => g.rows.forEach((r) => ids.add(r.id)));
  for (const id of Array.from(state.picked)) if (!ids.has(id)) state.picked.delete(id);
  if (!ids.size) state.selecting = false;

  let root = parentElement.querySelector(".ml");
  if (!root) {
    root = document.createElement("div");
    root.className = "ml";
    parentElement.appendChild(root);
  }

  const groupsHtml = (d.groups || []).map((g) => {
    const rows = g.rows.map((r) => {
      const flags = (r.flags || []).map((f) => `<span class="ml-flag">${esc(f)}</span>`).join("");
      const meta = [`<span>${esc(r.category)}</span>`]
        .concat((r.meta || []).map((m) => `<span class="dot">·</span><span>${esc(m)}</span>`))
        .join("");
      return `<div class="ml-row${state.picked.has(r.id) ? " sel" : ""}" role="button" tabindex="0" data-id="${r.id}">
        <div class="ml-ico" style="--c:${esc(r.rgb)}">${esc(r.icon)}<span class="ml-check">✓</span></div>
        <div class="ml-body">
          <div class="ml-title">${esc(r.title)}</div>
          <div class="ml-meta">${meta}${flags}</div>
        </div>
        <div class="ml-amt ${esc(r.tone)}">${esc(r.amount)}</div>
        <div class="ml-chev">›</div>
      </div>`;
    }).join("");
    return `<div class="ml-group">
      <div class="ml-day"><span>${esc(g.label)}</span><b>${esc(g.total || "")}</b></div>
      <div class="ml-card">${rows}</div>
    </div>`;
  }).join("");

  const more = d.more > 0
    ? `<div class="ml-more"><button class="ml-btn" data-act="more">Mostra altri ${d.more_step}</button></div>`
    : "";

  root.innerHTML = `
    <div class="ml-bar">
      <span class="ml-count">${esc(d.count_label || "")}</span>
      ${d.can_select ? `<button class="ml-btn ghost" data-act="select">${state.selecting ? "Fine" : "Seleziona"}</button>` : ""}
    </div>
    <div class="ml-hint">Tocca i movimenti dello stesso conto da unire.</div>
    ${groupsHtml}
    ${more}
    <div class="ml-sel">
      <span data-role="sel-count"></span>
      <div>
        <button class="ml-btn ghost" data-act="cancel">Annulla</button>
        <button class="ml-btn primary" data-act="merge">Unisci</button>
      </div>
    </div>`;

  const sync = () => {
    root.classList.toggle("selecting", state.selecting);
    const n = state.picked.size;
    const label = root.querySelector('[data-role="sel-count"]');
    if (label) label.textContent = n === 1 ? "1 selezionato" : `${n} selezionati`;
    const merge = root.querySelector('[data-act="merge"]');
    if (merge) merge.disabled = n < 2, merge.style.opacity = n < 2 ? ".45" : "1";
    const toggle = root.querySelector('[data-act="select"]');
    if (toggle) toggle.textContent = state.selecting ? "Fine" : "Seleziona";
  };
  sync();

  root.onclick = (ev) => {
    const btn = ev.target.closest("[data-act]");
    if (btn) {
      const act = btn.dataset.act;
      if (act === "select") {
        state.selecting = !state.selecting;
        if (!state.selecting) { state.picked.clear(); root.querySelectorAll(".ml-row.sel").forEach((r) => r.classList.remove("sel")); }
        sync();
      } else if (act === "cancel") {
        state.selecting = false; state.picked.clear();
        root.querySelectorAll(".ml-row.sel").forEach((r) => r.classList.remove("sel"));
        sync();
      } else if (act === "merge" && state.picked.size >= 2) {
        const picked = Array.from(state.picked);
        state.selecting = false; state.picked.clear();
        setTriggerValue("merge", picked);
      } else if (act === "more") {
        btn.disabled = true; btn.textContent = "Carico…";
        setTriggerValue("more", Date.now());
      }
      return;
    }
    const row = ev.target.closest(".ml-row");
    if (!row) return;
    const id = Number(row.dataset.id);
    if (state.selecting) {
      if (state.picked.has(id)) state.picked.delete(id); else state.picked.add(id);
      row.classList.toggle("sel", state.picked.has(id));
      sync();
      return;
    }
    // Riscontro immediato del tocco, poi la riga torna normale.
    row.style.background = "rgba(var(--ft-accent-rgb, 96,165,250), .14)";
    setTimeout(() => { row.style.background = ""; row.blur(); }, 450);
    setTriggerValue("open", id);
  };
  root.onkeydown = (ev) => {
    if ((ev.key === "Enter" || ev.key === " ") && ev.target.classList.contains("ml-row")) {
      ev.preventDefault();
      ev.target.click();
    }
  };
}
"""


ensure_component_runtime()

_movement_list = st.components.v2.component(
    "ft_movement_list",
    css=_CSS,
    js=_JS,
)


def _noop() -> None:
    return None


@dataclass
class MovementListResult:
    open_id: int | None
    merge_ids: list[int]
    more: bool


def movement_list(
    groups: list[dict[str, Any]],
    *,
    key: str,
    count_label: str,
    more: int = 0,
    more_step: int = 0,
    can_select: bool = True,
) -> MovementListResult:
    """
    groups: [{label, total, rows: [{id, title, category, icon, rgb, meta,
    flags, amount, tone}]}]
    """
    result = _movement_list(
        key=key,
        data={
            "groups": groups,
            "count_label": count_label,
            "more": int(more),
            "more_step": int(more_step),
            "can_select": bool(can_select),
        },
        height="content",
        on_open_change=_noop,
        on_merge_change=_noop,
        on_more_change=_noop,
    )
    open_value = getattr(result, "open", None)
    merge_value = getattr(result, "merge", None)
    more_value = getattr(result, "more", None)
    return MovementListResult(
        open_id=int(open_value) if open_value is not None else None,
        merge_ids=[int(item) for item in (merge_value or [])],
        more=more_value is not None,
    )
