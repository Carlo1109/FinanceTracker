/*
 * Ritocchi per il touch (app Android).
 *
 * 1. Menu a tendina senza tastiera: i selectbox di Streamlit hanno un campo
 *    di ricerca; su telefono toccarli aprirebbe anche la tastiera, che copre
 *    metà dell'elenco. Con inputmode="none" si apre solo l'elenco.
 * 2. Grafici: con il tocco Plotly mostra il dettaglio ma non lo toglie più
 *    (non esiste "mouse fuori"). Lo nascondiamo dopo qualche secondo o
 *    quando si tocca altrove.
 */
(function () {
  "use strict";

  // ---------------------------------------------------------------- tastiera

  function patchSelectInputs() {
    document
      .querySelectorAll(
        '[data-testid="stSelectbox"] input:not([inputmode="none"]),' +
        '[data-testid="stMultiSelect"] input:not([inputmode="none"]),' +
        'input[role="combobox"]:not([inputmode="none"])'
      )
      .forEach(function (input) {
        input.setAttribute("inputmode", "none");
      });
  }

  function watchSelects() {
    patchSelectInputs();
    new MutationObserver(patchSelectInputs).observe(document.documentElement, {
      childList: true,
      subtree: true,
    });
  }

  if (document.documentElement) watchSelects();
  else document.addEventListener("DOMContentLoaded", watchSelects);

  // ---------------------------------------------------------------- grafici

  var HOVER_TIMEOUT_MS = 2500;
  var timers = new WeakMap();

  function hideHover(plot) {
    var drag = plot.querySelector(".nsewdrag") || plot;
    drag.dispatchEvent(new MouseEvent("mouseout", { bubbles: true }));
    plot.querySelectorAll(".hoverlayer > *").forEach(function (node) {
      node.remove();
    });
  }

  document.addEventListener(
    "touchend",
    function (event) {
      var plot = event.target.closest && event.target.closest(".js-plotly-plot");
      if (!plot) return;
      clearTimeout(timers.get(plot));
      timers.set(plot, setTimeout(function () { hideHover(plot); }, HOVER_TIMEOUT_MS));
    },
    { passive: true }
  );

  document.addEventListener(
    "touchstart",
    function (event) {
      document.querySelectorAll(".js-plotly-plot").forEach(function (plot) {
        if (!plot.contains(event.target)) hideHover(plot);
      });
    },
    { passive: true }
  );
})();
