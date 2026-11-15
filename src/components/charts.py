"""
Grafici leggeri disegnati in SVG nel browser (st.components.v2).

Sostituiscono Plotly in tutta l'app:
- niente libreria Python pesante da importare (sul telefono, in WebAssembly,
  plotly era uno dei pacchetti più pesanti da installare e importare all'avvio);
- niente plotly.js (4-5 MB) da caricare nella WebView;
- stesso aspetto su PC e telefono, chiaro e scuro (usano le variabili --ft-*).

Il dettaglio di un punto/fetta compare al passaggio del mouse o al tocco.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.utils.st_compat import ensure_component_runtime


_CSS = r"""
:host { display: block; }
.ftc {
  position: relative;
  width: 100%;
  font-family: var(--ft-font, "Manrope", system-ui, sans-serif);
  color: var(--ft-text, #e5e7eb);
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}
.ftc svg { display: block; width: 100%; overflow: visible; }
.ftc text { font-family: inherit; }
.ftc .axis { fill: var(--ft-subtle, #94a3b8); font-size: 11px; font-weight: 600; }
.ftc .grid { stroke: var(--ft-border, rgba(148,163,184,.14)); stroke-width: 1; }
.ftc .zero { stroke: var(--ft-border-strong, rgba(148,163,184,.3)); stroke-width: 1; }
.ftc .cross { stroke: var(--ft-border-strong, rgba(148,163,184,.4)); stroke-width: 1; stroke-dasharray: 3 4; }
.ftc .legend { display: flex; flex-wrap: wrap; gap: 6px 16px; margin: 0 0 12px 2px; }
.ftc .legend span { display: inline-flex; align-items: center; gap: 7px; font-size: 12.5px; font-weight: 650; color: var(--ft-muted, #94a3b8); }
.ftc .legend i { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
.ftc .tip {
  position: absolute; z-index: 5; pointer-events: none;
  min-width: 150px; padding: 10px 12px; border-radius: 12px;
  background: var(--ft-menu-bg, #111827);
  border: 1px solid var(--ft-border-strong, rgba(148,163,184,.25));
  box-shadow: 0 14px 34px -12px rgba(0,0,0,.45);
  font-size: 12.5px; line-height: 1.35; opacity: 0;
  transform: translateY(4px); transition: opacity 120ms ease, transform 120ms ease;
}
.ftc .tip.on { opacity: 1; transform: translateY(0); }
.ftc .tip b { display: block; font-size: 12px; color: var(--ft-muted, #94a3b8); font-weight: 700; margin-bottom: 6px; letter-spacing: .02em; }
.ftc .tip div { display: flex; justify-content: space-between; gap: 14px; align-items: center; margin-top: 3px; }
.ftc .tip div span { display: inline-flex; align-items: center; gap: 6px; color: var(--ft-muted, #94a3b8); font-weight: 600; }
.ftc .tip div span i { width: 8px; height: 8px; border-radius: 99px; display: inline-block; }
.ftc .tip div strong { font-variant-numeric: tabular-nums; font-weight: 800; color: var(--ft-text, #fff); }
.ftc .seg { transition: opacity 140ms ease, transform 160ms ease; transform-origin: center; cursor: pointer; }
.ftc.has-active .seg { opacity: .32; }
.ftc.has-active .seg.on { opacity: 1; }
.ftc .center-v { font-size: 22px; font-weight: 800; fill: var(--ft-text, #fff); font-variant-numeric: tabular-nums; letter-spacing: -0.02em; }
.ftc .center-l { font-size: 12px; font-weight: 650; fill: var(--ft-muted, #94a3b8); }
.ftc .center-p { font-size: 12px; font-weight: 800; }
.ftc .bar { transition: opacity 120ms ease; }
.ftc.has-active .bar { opacity: .45; }
.ftc.has-active .bar.on { opacity: 1; }
.ftc .cal { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; }
/* Il calendario del report sta a tutta larghezza: celle quadrate, non oltre 620px. */
.ftc .cal, .ftc .cal-scale { max-width: 620px; margin-left: auto; margin-right: auto; }
.ftc .cal .dow { font-size: 11px; font-weight: 700; color: var(--ft-subtle, #94a3b8); text-align: center; padding-bottom: 2px; }
.ftc .cal .day {
  position: relative; aspect-ratio: 1 / 1; border-radius: 9px;
  background: var(--ft-raised, rgba(148,163,184,.08));
  display: flex; align-items: flex-start; justify-content: flex-start;
  padding: 5px 6px; box-sizing: border-box; cursor: pointer;
  font-size: 11px; font-weight: 700; color: var(--ft-muted, #94a3b8);
  transition: transform 120ms ease, box-shadow 120ms ease;
}
.ftc .cal .day.empty { background: transparent; cursor: default; }
.ftc .cal .day.today { box-shadow: 0 0 0 2px var(--ft-accent, #60a5fa) inset; }
.ftc .cal .day.on { transform: scale(1.06); box-shadow: 0 0 0 2px var(--ft-text, #fff) inset; }
.ftc .cal .day.hot { color: #fff; }
.ftc .cal-scale { display: flex; align-items: center; gap: 6px; justify-content: flex-end; margin-top: 10px; font-size: 11px; font-weight: 650; color: var(--ft-subtle, #94a3b8); }
.ftc .cal-scale i { width: 14px; height: 14px; border-radius: 4px; display: inline-block; }
@media (max-width: 520px) {
  .ftc .cal { gap: 4px; }
  .ftc .cal .day { border-radius: 7px; padding: 3px 4px; font-size: 10px; }
}
"""


_JS = r"""
const NS = "http://www.w3.org/2000/svg";
const touch = typeof window !== "undefined" && window.matchMedia && window.matchMedia("(hover: none)").matches;

// Stesso formato di Python (src/utils/formatting.py): 5.279,83 €.
// Intl in italiano non mette il punto nei numeri a 4 cifre (5279,83).
function group(intPart) { return intPart.replace(/\B(?=(\d{3})+(?!\d))/g, "."); }
function num(v, decimals) {
  const fixed = Math.abs(v || 0).toFixed(decimals);
  const [i, d] = fixed.split(".");
  return (v < 0 && Number(fixed) !== 0 ? "-" : "") + group(i) + (d ? "," + d : "");
}
function eur(v) { return num(v, 2) + "\u00a0€"; }
function short(v) {
  const a = Math.abs(v);
  if (a >= 1e6) return num(v / 1e6, 1) + " M";
  if (a >= 1e4) return num(v / 1e3, 0) + "k";
  return num(v, 0);
}
function el(tag, attrs, parent) {
  const n = document.createElementNS(NS, tag);
  for (const k in attrs || {}) n.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(n);
  return n;
}
function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function niceMax(v) {
  if (v <= 0) return 1;
  const p = Math.pow(10, Math.floor(Math.log10(v)));
  const n = v / p;
  const step = n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10;
  return step * p;
}

function placeTip(root, tip, x, y) {
  const w = root.clientWidth;
  const tw = tip.offsetWidth || 160;
  const th = tip.offsetHeight || 60;
  let left = x + 14;
  if (left + tw > w) left = Math.max(0, x - tw - 14);
  let top = Math.max(0, y - th - 10);
  tip.style.left = left + "px";
  tip.style.top = top + "px";
}

/* ---------------------------------------------------------------- donut */
function drawDonut(root, data) {
  const size = Math.min(root.clientWidth || 300, data.height || 300);
  const segs = (data.segments || []).filter((s) => s.value > 0);
  const total = segs.reduce((a, s) => a + s.value, 0) || 1;
  const svg = el("svg", { viewBox: `0 0 ${size} ${size}`, height: size, role: "img" });
  svg.style.maxWidth = size + "px";
  svg.style.margin = "0 auto";
  const cx = size / 2, cy = size / 2;
  const r = size / 2 - 6;
  const thick = Math.max(16, size * 0.13);
  const ri = r - thick;
  const gap = segs.length > 1 ? Math.min(0.025, 0.6 / segs.length) : 0;
  let a0 = -Math.PI / 2;
  const paths = [];
  segs.forEach((s, i) => {
    const frac = s.value / total;
    const a1 = a0 + frac * Math.PI * 2;
    const s0 = a0 + gap / 2, s1 = Math.max(s0 + 0.0001, a1 - gap / 2);
    const large = s1 - s0 > Math.PI ? 1 : 0;
    const p = (rad, ang) => [cx + rad * Math.cos(ang), cy + rad * Math.sin(ang)];
    let d;
    if (segs.length === 1) {
      d = `M ${cx} ${cy - r} A ${r} ${r} 0 1 1 ${cx - 0.01} ${cy - r} L ${cx - 0.01} ${cy - ri} A ${ri} ${ri} 0 1 0 ${cx} ${cy - ri} Z`;
    } else {
      const [x0, y0] = p(r, s0), [x1, y1] = p(r, s1), [x2, y2] = p(ri, s1), [x3, y3] = p(ri, s0);
      d = `M ${x0} ${y0} A ${r} ${r} 0 ${large} 1 ${x1} ${y1} L ${x2} ${y2} A ${ri} ${ri} 0 ${large} 0 ${x3} ${y3} Z`;
    }
    const path = el("path", { d, class: "seg" }, svg);
    path.style.fill = s.color;
    path.dataset.i = i;
    paths.push(path);
    a0 = a1;
  });
  const cv = el("text", { x: cx, y: cy - 2, "text-anchor": "middle", class: "center-v" }, svg);
  const cl = el("text", { x: cx, y: cy + 18, "text-anchor": "middle", class: "center-l" }, svg);
  const cp = el("text", { x: cx, y: cy - 30, "text-anchor": "middle", class: "center-p" }, svg);
  function center(i) {
    if (i == null || i < 0) {
      cv.textContent = eur(total);
      cl.textContent = data.center_label || "Totale";
      cp.textContent = "";
      root.classList.remove("has-active");
      paths.forEach((p) => p.classList.remove("on"));
      return;
    }
    const s = segs[i];
    cv.textContent = eur(s.value);
    const label = (s.icon ? s.icon + " " : "") + s.label;
    cl.textContent = label.length > 26 ? label.slice(0, 25) + "…" : label;
    cp.textContent = ((s.value / total) * 100).toFixed(1).replace(".", ",") + "%";
    cp.style.fill = s.color;
    root.classList.add("has-active");
    paths.forEach((p, j) => p.classList.toggle("on", j === i));
  }
  center(-1);
  let timer = null;
  paths.forEach((p) => {
    const i = Number(p.dataset.i);
    p.addEventListener("pointerenter", () => { if (!touch) center(i); });
    p.addEventListener("pointerleave", () => { if (!touch) center(-1); });
    p.addEventListener("click", (ev) => {
      ev.stopPropagation();
      center(i);
      clearTimeout(timer);
      timer = setTimeout(() => center(-1), 3200);
    });
  });
  svg.addEventListener("click", () => center(-1));
  root.appendChild(svg);
}

/* ---------------------------------------------------------------- linee / barre */
function drawXY(root, data) {
  const series = data.series || [];
  const labels = data.labels || [];
  const n = labels.length;
  const W = Math.max(260, root.clientWidth || 600);
  const H = data.height || 300;
  const narrow = W < 520;
  if (data.legend !== false && series.length > 1) {
    const lg = document.createElement("div");
    lg.className = "legend";
    lg.innerHTML = series.map((s) => `<span><i style="background:${s.color}"></i>${esc(s.name)}</span>`).join("");
    root.appendChild(lg);
  }
  const padL = narrow ? 38 : 52, padR = 10, padT = 8, padB = 26;
  const iw = W - padL - padR, ih = H - padT - padB;
  let maxV = 0, minV = 0;
  series.forEach((s) => s.values.forEach((v) => { maxV = Math.max(maxV, v || 0); minV = Math.min(minV, v || 0); }));
  maxV = niceMax(maxV);
  if (minV < 0) minV = -niceMax(-minV);
  const span = maxV - minV || 1;
  const y = (v) => padT + ih - ((v - minV) / span) * ih;
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, height: H });
  const ticks = 4;
  for (let t = 0; t <= ticks; t++) {
    const v = minV + (span * t) / ticks;
    const yy = y(v);
    el("line", { x1: padL, x2: W - padR, y1: yy, y2: yy, class: Math.abs(v) < 1e-9 ? "zero" : "grid" }, svg);
    const tx = el("text", { x: padL - 8, y: yy + 4, "text-anchor": "end", class: "axis" }, svg);
    tx.textContent = short(v);
  }
  const kind = data.kind || "line";
  const step = n > 0 ? iw / n : iw;
  const xc = (i) => padL + step * i + step / 2;
  // etichette asse x: al massimo ~6 su telefono, ~12 su PC
  const maxLabels = narrow ? 5 : 12;
  const every = Math.max(1, Math.ceil(n / maxLabels));
  labels.forEach((lab, i) => {
    if (i % every !== 0 && i !== n - 1) return;
    if (i !== n - 1 && n - 1 - i < every && i % every === 0 && i !== 0 && n > maxLabels) return;
    const tx = el("text", { x: xc(i), y: H - 6, "text-anchor": "middle", class: "axis" }, svg);
    tx.textContent = (data.short_labels || labels)[i];
  });
  const groups = [];
  if (kind === "bar") {
    const k = series.length;
    const gw = Math.min(step * 0.74, 22 * k + 8);
    const bw = Math.max(3, (gw - (k - 1) * 3) / k);
    for (let i = 0; i < n; i++) {
      const g = el("g", { class: "bar" }, svg);
      series.forEach((s, j) => {
        const v = s.values[i] || 0;
        const x = xc(i) - gw / 2 + j * (bw + 3);
        const y0 = y(Math.max(0, v)), y1 = y(Math.min(0, v));
        const h = Math.max(v === 0 ? 0 : 2, y1 - y0);
        const rect = el("rect", { x, y: y0, width: bw, height: h, rx: Math.min(5, bw / 2) }, g);
        rect.style.fill = s.color;
        if (s.dim && s.dim[i]) rect.style.opacity = "0.45";
      });
      groups.push(g);
    }
  } else {
    series.forEach((s) => {
      const pts = s.values.map((v, i) => [xc(i), y(v || 0)]);
      if (!pts.length) return;
      let d = "";
      pts.forEach(([px, py], i) => {
        if (i === 0) { d += `M ${px} ${py}`; return; }
        const [qx, qy] = pts[i - 1];
        const mx = (qx + px) / 2;
        d += ` C ${mx} ${qy} ${mx} ${py} ${px} ${py}`;
      });
      if (s.area) {
        const gid = "g" + Math.random().toString(36).slice(2);
        const defs = el("defs", {}, svg);
        const lg = el("linearGradient", { id: gid, x1: 0, x2: 0, y1: 0, y2: 1 }, defs);
        const s1 = el("stop", { offset: "0%" }, lg); s1.style.stopColor = s.color; s1.style.stopOpacity = "0.28";
        const s2 = el("stop", { offset: "100%" }, lg); s2.style.stopColor = s.color; s2.style.stopOpacity = "0";
        const area = el("path", { d: d + ` L ${pts[pts.length - 1][0]} ${y(Math.max(0, minV))} L ${pts[0][0]} ${y(Math.max(0, minV))} Z` }, svg);
        area.style.fill = `url(#${gid})`;
      }
      const path = el("path", { d, fill: "none" }, svg);
      path.style.stroke = s.color;
      path.style.strokeWidth = s.width || 2.4;
      path.style.strokeLinecap = "round";
      if (s.dash) path.style.strokeDasharray = "5 5";
      if (n <= 24) {
        pts.forEach(([px, py]) => {
          const c = el("circle", { cx: px, cy: py, r: narrow ? 2.6 : 3.2 }, svg);
          c.style.fill = "var(--ft-panel-solid, #111)";
          c.style.stroke = s.color;
          c.style.strokeWidth = 2;
        });
      }
    });
  }
  const cross = el("line", { y1: padT, y2: padT + ih, class: "cross", visibility: "hidden" }, svg);
  const hit = el("rect", { x: padL, y: padT, width: iw, height: ih, fill: "transparent" }, svg);
  root.appendChild(svg);
  const tip = document.createElement("div");
  tip.className = "tip";
  root.appendChild(tip);
  let active = -1, timer = null;
  function show(i, evX, evY) {
    if (i < 0 || i >= n) return hide();
    active = i;
    const rows = series.map((s) => `<div><span><i style="background:${s.color}"></i>${esc(s.name)}</span><strong>${eur(s.values[i] || 0)}</strong></div>`).join("");
    const extra = (data.tooltip_extra && data.tooltip_extra[i]) ? `<div><span>${esc(data.tooltip_extra[i][0])}</span><strong>${esc(data.tooltip_extra[i][1])}</strong></div>` : "";
    tip.innerHTML = `<b>${esc(labels[i])}</b>${rows}${extra}`;
    tip.classList.add("on");
    const rect = svg.getBoundingClientRect();
    const scale = rect.width / W;
    const cx = xc(i);
    if (kind === "bar") {
      root.classList.add("has-active");
      groups.forEach((g, j) => g.classList.toggle("on", j === i));
    } else {
      cross.setAttribute("x1", cx); cross.setAttribute("x2", cx); cross.setAttribute("visibility", "visible");
    }
    placeTip(root, tip, cx * scale, (evY != null ? evY : padT + 30) );
  }
  function hide() {
    active = -1;
    tip.classList.remove("on");
    cross.setAttribute("visibility", "hidden");
    root.classList.remove("has-active");
    groups.forEach((g) => g.classList.remove("on"));
  }
  function idxFrom(ev) {
    const rect = svg.getBoundingClientRect();
    const x = (ev.clientX - rect.left) * (W / rect.width);
    return { i: Math.floor((x - padL) / step), y: ev.clientY - root.getBoundingClientRect().top };
  }
  hit.addEventListener("pointermove", (ev) => { if (touch) return; const r = idxFrom(ev); if (r.i !== active) show(r.i, null, r.y); else placeTip(root, tip, xc(r.i) * (svg.getBoundingClientRect().width / W), r.y); });
  hit.addEventListener("pointerleave", () => { if (!touch) hide(); });
  hit.addEventListener("click", (ev) => {
    const r = idxFrom(ev);
    show(r.i, null, r.y);
    clearTimeout(timer);
    if (touch) timer = setTimeout(hide, 3500);
  });
}

/* ---------------------------------------------------------------- calendario */
function drawCalendar(root, data) {
  const days = data.days || [];
  const maxV = Math.max(1, ...days.map((d) => d.value || 0));
  const rgb = data.rgb || "251, 113, 133";
  const tint = (a) => `rgba(${rgb}, ${a.toFixed(2)})`;
  const grid = document.createElement("div");
  grid.className = "cal";
  ["L", "M", "M", "G", "V", "S", "D"].forEach((d) => {
    const c = document.createElement("div"); c.className = "dow"; c.textContent = d; grid.appendChild(c);
  });
  for (let i = 0; i < (data.offset || 0); i++) {
    const c = document.createElement("div"); c.className = "day empty"; grid.appendChild(c);
  }
  const tip = document.createElement("div");
  tip.className = "tip";
  const cells = [];
  let timer = null;
  days.forEach((d) => {
    const c = document.createElement("div");
    c.className = "day" + (d.today ? " today" : "");
    c.textContent = d.day;
    const t = (d.value || 0) / maxV;
    if (d.value > 0) {
      const alpha = 0.14 + 0.86 * Math.sqrt(t);
      c.style.background = tint(alpha);
      if (alpha > 0.55) c.classList.add("hot");
    }
    function show() {
      cells.forEach((x) => x.classList.remove("on"));
      c.classList.add("on");
      const items = (d.top || []).map((x) => `<div><span>${esc(x[0])}</span><strong>${eur(x[1])}</strong></div>`).join("");
      tip.innerHTML = `<b>${esc(d.label)}</b><div><span>Uscite</span><strong>${eur(d.value || 0)}</strong></div>${d.count ? `<div><span>Movimenti</span><strong>${d.count}</strong></div>` : ""}${items}`;
      tip.classList.add("on");
      const rr = root.getBoundingClientRect(), cr = c.getBoundingClientRect();
      placeTip(root, tip, cr.left - rr.left + cr.width / 2, cr.top - rr.top);
    }
    function hide() { c.classList.remove("on"); tip.classList.remove("on"); }
    c.addEventListener("pointerenter", () => { if (!touch) show(); });
    c.addEventListener("pointerleave", () => { if (!touch) hide(); });
    c.addEventListener("click", (ev) => { ev.stopPropagation(); show(); clearTimeout(timer); timer = setTimeout(hide, 3200); });
    cells.push(c);
    grid.appendChild(c);
  });
  root.appendChild(grid);
  const scale = document.createElement("div");
  scale.className = "cal-scale";
  scale.innerHTML = "meno " + [0.14, 0.4, 0.7, 1].map((a) => `<i style="background:${tint(a)}"></i>`).join("") + " più";
  root.appendChild(scale);
  root.appendChild(tip);
}

const DRAW = { donut: drawDonut, line: drawXY, bar: drawXY, calendar: drawCalendar };

export default function (component) {
  const { parentElement, data } = component;
  let root = parentElement.querySelector(".ftc");
  if (!root) {
    root = document.createElement("div");
    root.className = "ftc";
    parentElement.appendChild(root);
  }
  const render = () => {
    root.innerHTML = "";
    root.classList.remove("has-active");
    const draw = DRAW[(data && data.type) || "line"];
    if (draw) draw(root, data || {});
  };
  render();
  let lastW = root.clientWidth;
  const ro = new ResizeObserver(() => {
    const w = root.clientWidth;
    if (Math.abs(w - lastW) > 4) { lastW = w; render(); }
  });
  ro.observe(root);
  return () => ro.disconnect();
}
"""


ensure_component_runtime()

_chart = st.components.v2.component(
    "ft_chart",
    css=_CSS,
    js=_JS,
)


def _mount(data: dict[str, Any], key: str) -> None:
    _chart(data=data, key=key, height="content")


def donut_chart(
    segments: list[dict[str, Any]],
    *,
    key: str,
    center_label: str = "Totale",
    height: int = 300,
) -> None:
    """segments: [{label, value, color, icon}] (value > 0)."""
    _mount(
        {
            "type": "donut",
            "segments": [
                {
                    "label": str(item.get("label", "")),
                    "value": round(float(item.get("value") or 0), 2),
                    "color": str(item.get("color") or "#60a5fa"),
                    "icon": str(item.get("icon") or ""),
                }
                for item in segments
            ],
            "center_label": center_label,
            "height": int(height),
        },
        key,
    )


def xy_chart(
    labels: list[str],
    series: list[dict[str, Any]],
    *,
    key: str,
    kind: str = "line",
    height: int = 300,
    short_labels: list[str] | None = None,
    tooltip_extra: list[tuple[str, str]] | None = None,
    legend: bool = True,
) -> None:
    """
    Grafico a linee (kind="line") o a barre affiancate (kind="bar").

    series: [{name, color, values, area?, dash?, width?, dim?}]
    """
    _mount(
        {
            "type": kind,
            "kind": kind,
            "labels": [str(label) for label in labels],
            "short_labels": [str(label) for label in (short_labels or labels)],
            "series": [
                {
                    **{k: v for k, v in item.items() if k != "values"},
                    "values": [round(float(v or 0), 2) for v in item["values"]],
                }
                for item in series
            ],
            "height": int(height),
            "tooltip_extra": [list(item) for item in tooltip_extra]
            if tooltip_extra
            else None,
            "legend": legend,
        },
        key,
    )


def calendar_heatmap(
    days: list[dict[str, Any]],
    *,
    key: str,
    offset: int,
    rgb: str = "var(--ft-danger-rgb)",
) -> None:
    """
    Calendario di un mese colorato in base a quanto si è speso ogni giorno.

    days: [{day, label, value, count, top: [(nome, importo)], today}]
    offset: giorni vuoti prima del primo (0 = lunedì).
    """
    _mount(
        {
            "type": "calendar",
            "days": days,
            "offset": int(offset),
            "rgb": rgb,
        },
        key,
    )
