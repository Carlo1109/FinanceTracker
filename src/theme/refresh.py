"""
Strato grafico "2026": si applica sopra al tema di base (style.py) e a quello
per telefono (mobile.py) senza toccarli.

Linee guida:
- superfici più pulite (niente sfumature radiali su ogni card), bordi sottili
  e ombre morbide, uguali in chiaro e in scuro grazie alle variabili --ft-*;
- importi in Manrope con cifre a larghezza fissa (si leggono in colonna),
  Fraunces solo per titoli e marchio;
- colori con un significato: entrate verdi, uscite rosa/rosse,
  investimenti viola, accento scelto dall'utente per il resto.

Usa solo variabili CSS: è un testo fisso, sul telefono viene caricato una
volta sola dalla pagina di avvio (ft.css).
"""

REFRESH_CSS = r"""
/* ================================================================ base */

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(1200px 520px at 12% -12%, rgba(var(--ft-accent-rgb), var(--ft-glow-alpha)), transparent 60%),
        radial-gradient(900px 480px at 100% 0%, rgba(var(--ft-investment-rgb), 0.06), transparent 60%),
        linear-gradient(180deg, var(--ft-bg-0) 0%, var(--ft-bg-1) 60%, var(--ft-bg-2) 100%) !important;
    background-attachment: fixed !important;
}

.block-container,
[data-testid="stMainBlockContainer"] {
    max-width: 1480px;
}

h1 {
    font-size: clamp(30px, 2.6vw, 40px) !important;
    letter-spacing: -0.035em !important;
    line-height: 1.05 !important;
    margin-bottom: 0.1rem !important;
}

[data-testid="stCaption"],
[data-testid="stCaptionContainer"] {
    color: var(--ft-muted) !important;
}

.ft-kicker {
    font-family: var(--ft-font);
    font-size: 11.5px;
    line-height: 1.2;
    font-weight: 750;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ft-muted);
}

.ft-section-title {
    font-size: 1.28rem !important;
    margin: 1.6rem 0 0.7rem 0 !important;
    display: flex;
    align-items: center;
    gap: 10px;
}

.ft-section-title::after {
    content: "";
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, var(--ft-border-strong), transparent);
    margin-left: 6px;
}

.ft-section-sub {
    margin: -0.45rem 0 0.8rem 0;
    font-size: 13px;
    color: var(--ft-muted);
}

/* Superfici: card, pannelli e contenitori con bordo hanno tutti lo stesso aspetto. */
.ft-dashboard-card,
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .ft-distribution-anchor),
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .ft-chart-card-anchor),
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .ft-panel-anchor),
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .ft-settings-anchor),
div[class*="st-key-ft_dashboard_chart_card"],
div[class*="st-key-ft_dashboard_distribution_card"],
div[class*="st-key-ft_dashboard_expense_distribution"],
div[class*="st-key-ft_dashboard_income_distribution"],
div[class*="st-key-ft_report_card"] {
    background: var(--ft-panel) !important;
    border: 1px solid var(--ft-border) !important;
    border-radius: var(--ft-radius) !important;
    box-shadow: var(--ft-shadow) !important;
}

div[class*="st-key-ft_report_card"] {
    padding: 18px 18px 14px 18px !important;
}

/* ================================================================ chip delta */

.ft-delta {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    width: fit-content;
    max-width: 100%;
    padding: 3px 9px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 750;
    line-height: 1.35;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: var(--ft-muted);
    background: var(--ft-raised);
    box-shadow: inset 0 0 0 1px var(--ft-border);
}

.ft-delta.is-good {
    color: var(--ft-income);
    background: rgba(var(--ft-income-rgb), 0.12);
    box-shadow: inset 0 0 0 1px rgba(var(--ft-income-rgb), 0.22);
}

.ft-delta.is-bad {
    color: var(--ft-danger);
    background: rgba(var(--ft-danger-rgb), 0.12);
    box-shadow: inset 0 0 0 1px rgba(var(--ft-danger-rgb), 0.22);
}

.ft-delta.is-info {
    color: var(--ft-accent-strong);
    background: rgba(var(--ft-accent-rgb), 0.12);
    box-shadow: inset 0 0 0 1px rgba(var(--ft-accent-rgb), 0.22);
}

/* ================================================================ hero */

.ft-hero {
    position: relative;
    display: grid;
    grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
    align-items: stretch;
    gap: 28px;
    margin: 6px 0 14px 0;
    padding: 30px 32px;
    border-radius: 26px;
    overflow: hidden;
    background:
        radial-gradient(600px 260px at 0% 0%, rgba(var(--ft-accent-rgb), 0.20), transparent 70%),
        var(--ft-panel);
    border: 1px solid var(--ft-border);
    box-shadow: var(--ft-shadow);
    animation: ft-fade-up 260ms ease-out;
}

.ft-hero::after {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    pointer-events: none;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), transparent 40%);
}

.ft-hero-main {
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-width: 0;
}

.ft-hero-value {
    margin-top: 10px;
    font-family: var(--ft-font) !important;
    font-weight: 800 !important;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.045em;
    line-height: 1 !important;
    font-size: clamp(38px, 4.6vw, 64px) !important;
}

.ft-hero-value.is-long,
.ft-hero-value.is-huge {
    font-size: clamp(32px, 3.8vw, 52px) !important;
}

.ft-hero-row {
    margin-top: 16px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px 12px;
}

.ft-hero-context {
    font-size: 13px;
    font-weight: 650;
    color: var(--ft-muted);
}

.ft-hero-stats {
    display: flex;
    flex-wrap: wrap;
    gap: 22px;
    margin-top: 18px;
}

.ft-hero-stat span {
    display: block;
    font-size: 12px;
    font-weight: 650;
    color: var(--ft-muted);
}

.ft-hero-stat strong {
    font-size: 17px;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
}

.ft-hero-spark {
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    min-width: 0;
}

.ft-hero-spark-caption {
    align-self: flex-end;
    margin-bottom: 8px;
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: var(--ft-subtle);
}

.ft-spark {
    width: 100%;
    height: 110px;
    overflow: visible;
}

.ft-spark-zero {
    stroke: var(--ft-border-strong);
    stroke-width: 1;
    stroke-dasharray: 3 5;
    vector-effect: non-scaling-stroke;
}

/* ================================================================ KPI */

.ft-kpi {
    position: relative;
    min-height: 136px;
    height: 100%;
    padding: 18px 18px 16px 18px;
    border-radius: var(--ft-radius);
    background: var(--ft-panel);
    border: 1px solid var(--ft-border);
    box-shadow: var(--ft-shadow);
    display: flex;
    flex-direction: column;
    gap: 10px;
    box-sizing: border-box;
    container-type: inline-size;
    overflow: hidden;
    transition: transform 160ms ease, border-color 160ms ease;
    animation: ft-fade-up 280ms ease-out;
}

.ft-kpi:hover {
    transform: translateY(-2px);
    border-color: var(--ft-border-strong);
}

.ft-kpi::before {
    content: "";
    position: absolute;
    inset: 0 0 auto 0;
    height: 2px;
    background: linear-gradient(90deg, rgba(var(--tone-rgb), 0.9), rgba(var(--tone-rgb), 0));
}

.ft-kpi.is-income { --tone-rgb: var(--ft-income-rgb); }
.ft-kpi.is-expense { --tone-rgb: var(--ft-danger-rgb); }
.ft-kpi.is-investment { --tone-rgb: var(--ft-investment-rgb); }
.ft-kpi.is-accent { --tone-rgb: var(--ft-accent-rgb); }

.ft-kpi-head {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
}

.ft-kpi-icon {
    flex: 0 0 30px;
    width: 30px;
    height: 30px;
    border-radius: 10px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    font-weight: 900;
    color: rgb(var(--tone-rgb));
    background: rgba(var(--tone-rgb), 0.14);
    box-shadow: inset 0 0 0 1px rgba(var(--tone-rgb), 0.22);
}

.ft-kpi-value {
    margin-top: 0 !important;
    font-family: var(--ft-font) !important;
    font-weight: 800 !important;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.035em;
    line-height: 1.05 !important;
    font-size: clamp(18px, 12cqi, 32px) !important;
}

/* Il valore non si schiaccia mai, anche con righe in più nella card. */
.ft-kpi-value { flex-shrink: 0; }

.ft-kpi-value.is-long { font-size: clamp(16px, 10cqi, 27px) !important; }
.ft-kpi-value.is-huge { font-size: clamp(14px, 8.6cqi, 23px) !important; }

/* Spazio tra la riga dei KPI e quella delle card informative. */
[data-testid="stHorizontalBlock"]:has(.ft-kpi-card) {
    margin-bottom: 4px;
}

.ft-kpi-foot {
    margin-top: auto;
    min-height: 22px;
}

.ft-kpi-foot:empty {
    display: none;
}

.ft-kpi:not(:has(.ft-delta)) {
    min-height: 104px;
}

/* ================================================================ info card */

.ft-info-card {
    min-height: 170px !important;
    padding: 18px !important;
    border-radius: var(--ft-radius) !important;
    background: var(--ft-panel) !important;
    border: 1px solid var(--ft-border) !important;
    box-shadow: var(--ft-shadow) !important;
    color: var(--ft-info-value, var(--ft-text)) !important;
    gap: 0;
}

.ft-info-card-value {
    margin-top: 12px !important;
    font-family: var(--ft-font) !important;
    font-size: clamp(17px, 1.35vw, 21px) !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em;
    color: var(--ft-info-value, var(--ft-text)) !important;
    min-height: 0 !important;
}

.ft-info-card-amount {
    margin-top: auto !important;
    padding-top: 8px;
    font-family: var(--ft-font) !important;
    font-weight: 800 !important;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.03em;
    font-size: clamp(20px, 1.7vw, 27px) !important;
    color: var(--ft-accent-strong) !important;
}

.ft-info-card-sub {
    margin-top: 10px;
}

.ft-info-card-footer {
    margin-top: 8px;
    font-size: 12px;
    line-height: 1.35;
    font-weight: 600;
    color: var(--ft-muted);
}

/* ================================================================ categorie */

.ft-card-label {
    margin-bottom: 6px;
}

.ft-category-scroll {
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 6px;
    margin-right: -2px;
    overscroll-behavior: contain;
}

.ft-cat-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 9px 4px;
    border-radius: 12px;
}

.ft-cat-row + .ft-cat-row {
    border-top: 1px solid var(--ft-border);
}

.ft-cat-icon {
    flex: 0 0 34px;
    width: 34px;
    height: 34px;
    border-radius: 11px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    background: var(--ft-raised);
    background: color-mix(in srgb, var(--c) 16%, transparent);
    box-shadow: inset 0 0 0 1px var(--ft-border);
    box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--c) 28%, transparent);
}

.ft-cat-body {
    flex: 1;
    min-width: 0;
}

.ft-cat-line {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.ft-cat-line.is-sub {
    margin-top: 6px;
}

.ft-cat-name {
    font-size: 14px;
    font-weight: 700;
    color: var(--ft-text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.ft-cat-amount {
    flex-shrink: 0;
    font-size: 14.5px;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
    color: var(--ft-text);
}

.ft-cat-track {
    flex: 1;
    height: 6px;
    border-radius: 99px;
    background: var(--ft-raised);
    overflow: hidden;
}

.ft-cat-track > div {
    height: 100%;
    border-radius: 99px;
    background: var(--c);
}

.ft-cat-pct {
    flex: 0 0 46px;
    text-align: right;
    font-size: 12px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    color: var(--ft-muted);
}

.ft-cat-total {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid var(--ft-border-strong);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
}

.ft-cat-total strong {
    font-size: 19px;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.02em;
    color: var(--ft-text);
}

/* ================================================================ spese speciali */

.ft-special-row {
    display: flex;
    justify-content: space-between;
    gap: 18px;
    padding: 16px 2px;
    flex-wrap: wrap;
}

.ft-special-row + .ft-special-row {
    border-top: 1px solid var(--ft-border);
}

.ft-special-main {
    min-width: min(100%, 280px);
    flex: 1;
}

.ft-special-title {
    font-size: 15px;
    font-weight: 750;
    color: var(--ft-text);
}

.ft-special-meta,
.ft-special-detail {
    margin-top: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    font-size: 12px;
    color: var(--ft-muted);
}

.ft-special-cat,
.ft-special-range,
.ft-special-mode {
    padding: 3px 9px;
    border-radius: 8px;
    font-size: 11.5px;
    font-weight: 750;
    background: var(--ft-raised);
    box-shadow: inset 0 0 0 1px var(--ft-border);
}

.ft-special-range {
    color: var(--ft-accent-strong);
    background: rgba(var(--ft-accent-rgb), 0.10);
    box-shadow: inset 0 0 0 1px rgba(var(--ft-accent-rgb), 0.22);
}

.ft-special-quota b {
    color: var(--ft-accent-strong);
}

.ft-special-note {
    margin-top: 10px;
    font-size: 13px;
    font-style: italic;
    color: var(--ft-muted);
}

.ft-special-amount {
    font-size: 20px;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
    color: var(--ft-danger);
    white-space: nowrap;
}

/* ================================================================ vuoto */

.ft-empty-hero {
    margin-top: 12px;
    padding: 40px 32px 34px 32px;
    border-radius: 26px;
    background:
        radial-gradient(520px 260px at 0% 0%, rgba(var(--ft-accent-rgb), 0.22), transparent 70%),
        var(--ft-panel);
    border: 1px solid var(--ft-border);
    box-shadow: var(--ft-shadow);
    animation: ft-fade-up 320ms ease-out;
}

.ft-empty-title {
    font-family: var(--ft-display);
    font-size: clamp(34px, 4vw, 50px);
    font-weight: 700;
    letter-spacing: -0.035em;
    line-height: 1.04;
    color: var(--ft-text);
}

.ft-empty-title span {
    color: var(--ft-accent-strong);
}

.ft-empty-chip {
    margin-top: 12px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(var(--ft-accent-rgb), 0.14);
    color: var(--ft-accent-strong);
    font-size: 12px;
    font-weight: 750;
}

.ft-empty-chip span {
    width: 8px;
    height: 8px;
    border-radius: 99px;
    background: var(--ft-accent);
    box-shadow: 0 0 0 3px rgba(var(--ft-accent-rgb), 0.25);
}

.ft-empty-copy {
    margin-top: 14px;
    max-width: 36rem;
    font-size: 16px;
    line-height: 1.55;
    color: var(--ft-muted);
}

.ft-empty-steps {
    margin-top: 22px;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.ft-empty-steps > div {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    border-radius: 14px;
    background: var(--ft-raised);
    box-shadow: inset 0 0 0 1px var(--ft-border);
    font-size: 13.5px;
    font-weight: 650;
    color: var(--ft-text);
}

.ft-empty-steps b {
    width: 24px;
    height: 24px;
    border-radius: 8px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: var(--ft-accent);
    color: var(--ft-primary-btn-text);
    font-size: 12px;
}

/* ================================================================ filtri */

.st-key-ft_filter_bar {
    padding: 14px 18px 6px 18px;
    margin-bottom: 6px;
    border-radius: var(--ft-radius);
    background: var(--ft-panel-soft);
    border: 1px solid var(--ft-border);
}

[data-testid="stPills"] button,
[data-testid="stButtonGroup"] button {
    border-radius: 999px !important;
    font-weight: 650 !important;
    transition: background 120ms ease, border-color 120ms ease, color 120ms ease !important;
}

[data-testid="stPills"] button[kind*="Active"],
[data-testid="stPills"] button[aria-pressed="true"],
[data-testid="stButtonGroup"] button[kind*="Active"],
[data-testid="stButtonGroup"] button[aria-pressed="true"] {
    background: rgba(var(--ft-accent-rgb), 0.16) !important;
    border-color: rgba(var(--ft-accent-rgb), 0.55) !important;
    color: var(--ft-text) !important;
}

/* Expander (filtri su telefono, sezioni impostazioni). */
div[data-testid="stExpander"] details {
    border-radius: var(--ft-radius-sm) !important;
    border: 1px solid var(--ft-border) !important;
    background: var(--ft-panel-soft) !important;
}

div[data-testid="stExpander"] summary p {
    font-weight: 700 !important;
}

/* ================================================================ pulsanti */

.stButton > button,
.stDownloadButton > button,
[data-testid="stDownloadButton"] button,
[data-testid="stFormSubmitButton"] button {
    border-radius: 12px !important;
    font-weight: 700 !important;
    transition: transform 120ms ease, background 140ms ease, border-color 140ms ease, box-shadow 140ms ease !important;
}

.stButton > button:active,
.stDownloadButton > button:active {
    transform: scale(0.98);
}

.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"] {
    background: linear-gradient(180deg, var(--ft-accent), var(--ft-accent-strong)) !important;
    border: 0 !important;
    color: var(--ft-primary-btn-text) !important;
    box-shadow: 0 8px 20px -10px rgba(var(--ft-accent-rgb), 0.9) !important;
}

.stButton > button[kind="primary"] p,
[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"] p {
    color: var(--ft-primary-btn-text) !important;
}

/* ================================================================ navigazione desktop */

.ft-nav-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 2px 0;
    min-width: 0;
}

.ft-nav-brand > div {
    min-width: 0;
}

.ft-nav-brand img {
    flex: 0 0 38px;
    width: 38px;
    height: 38px;
    border-radius: 13px;
    box-shadow: 0 8px 18px -8px rgba(0, 0, 0, 0.5);
}

.ft-nav-brand-name {
    font-family: var(--ft-display);
    font-size: clamp(15px, 1.25vw, 19px);
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1.05;
    white-space: nowrap;
}

.ft-nav-brand-sub {
    margin-top: 3px;
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11.5px;
    font-weight: 650;
    color: var(--ft-muted);
}

.ft-nav-brand-sub .ft-version-chip {
    padding: 1px 7px;
    border-radius: 6px;
    font-size: 10.5px;
}

[data-testid="stColumn"]:has(.ft-navigation-anchor)
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .ft-navigation-anchor) {
    background: var(--ft-panel) !important;
    border-radius: 24px !important;
}

[data-testid="stColumn"]:has(.ft-navigation-anchor) [data-testid="stPageLink"] a {
    min-height: 42px !important;
    margin: 2px 0 !important;
    border-radius: 12px !important;
}

[data-testid="stColumn"]:has(.ft-navigation-anchor) [data-testid="stPageLink"] a[aria-current="page"] {
    background: rgba(var(--ft-accent-rgb), 0.14) !important;
    border-color: transparent !important;
    box-shadow: inset 3px 0 0 var(--ft-accent);
}

[data-testid="stColumn"]:has(.ft-navigation-anchor) hr {
    margin: 12px 0 6px 0 !important;
    border-color: var(--ft-border) !important;
}

/* ================================================================ annulla */

.ft-undo-timer {
    margin-top: 12px;
    height: 4px;
    border-radius: 99px;
    background: var(--ft-raised);
    overflow: hidden;
}

.ft-undo-timer > span {
    display: block;
    height: 100%;
    width: 100%;
    border-radius: 99px;
    background: var(--ft-accent);
    transform-origin: left center;
    animation-name: ft-undo-shrink;
    animation-timing-function: linear;
    animation-fill-mode: forwards;
}

@keyframes ft-undo-shrink {
    from { transform: scaleX(1); }
    to { transform: scaleX(0); }
}

/* ================================================================ report */

/* Risparmio diviso in investito e liquidità (parti dello stesso totale). */
.ft-split {
    margin: 8px 0 6px 0;
}

.ft-split-bar {
    display: flex;
    height: 6px;
    border-radius: 999px;
    overflow: hidden;
    background: rgba(148, 163, 184, 0.18);
}

.ft-split-bar span.is-invest,
.ft-split-legend i.is-invest { background: rgb(var(--ft-investment-rgb)); }
.ft-split-bar span.is-cash,
.ft-split-legend i.is-cash { background: rgba(var(--ft-income-rgb), 0.75); }

.ft-split-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 2px 12px;
    margin-top: 6px;
    font-size: 11.5px;
    font-weight: 650;
    color: var(--ft-muted);
    font-variant-numeric: tabular-nums;
}

.ft-split-legend span { white-space: nowrap; }
.ft-split-legend span.is-bad { color: rgb(var(--ft-danger-rgb)); }

.ft-split-legend i {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 3px;
    margin-right: 5px;
}

.ft-kpi-note {
    margin: 6px 0 4px 0;
    font-size: 11.5px;
    font-weight: 650;
    color: var(--ft-muted);
}

/* Scheda spese speciali del report. */
.ft-spec-table td:first-child { white-space: normal; }
.ft-spec-name { font-weight: 700; }
.ft-spec-meta {
    margin-top: 2px;
    font-size: 11.5px;
    font-weight: 600;
    color: var(--ft-muted);
}
.ft-spec-name {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    overflow-wrap: anywhere;
}

/* Anno: un mese per riga, chiuso; toccandolo si aprono le spese. */
.ft-spec-month {
    border-bottom: 1px solid var(--ft-border);
}

.ft-spec-month > summary {
    list-style: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 2px;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
}

.ft-spec-month > summary::-webkit-details-marker { display: none; }

.ft-spec-month > summary::before {
    content: "›";
    display: inline-block;
    width: 14px;
    margin-right: 4px;
    color: var(--ft-muted);
    transition: transform 140ms ease;
}

.ft-spec-month[open] > summary::before { transform: rotate(90deg); }

.ft-spec-month-name { flex: 1; }

.ft-spec-month-name em {
    font-style: normal;
    font-weight: 600;
    font-size: 12px;
    color: var(--ft-muted);
    margin-left: 6px;
}

.ft-spec-month .ft-cmp-scroll { padding-bottom: 8px; }

.ft-spec-year-total {
    display: flex;
    justify-content: space-between;
    padding: 12px 2px 4px 20px;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
}

.ft-report-kpis {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
}

.ft-report-highlights {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
}

.ft-highlight {
    padding: 16px 18px;
    border-radius: var(--ft-radius);
    background: var(--ft-panel);
    border: 1px solid var(--ft-border);
    box-shadow: var(--ft-shadow);
}

.ft-highlight-title {
    margin-top: 8px;
    font-size: 15px;
    font-weight: 750;
    line-height: 1.35;
    color: var(--ft-text);
}

.ft-highlight-copy {
    margin-top: 6px;
    font-size: 13px;
    line-height: 1.45;
    color: var(--ft-muted);
}

.ft-highlight-copy b {
    color: var(--ft-text);
    font-variant-numeric: tabular-nums;
}

.ft-cmp-scroll {
    overflow-x: auto;
}

.ft-cmp-table {
    width: 100%;
    border-collapse: collapse;
    border: 0 !important;
    font-size: 13.5px;
}

.ft-cmp-table th,
.ft-cmp-table td {
    border-left: 0 !important;
    border-right: 0 !important;
    border-top: 0 !important;
    background: transparent !important;
}

.ft-cmp-table th {
    text-align: right;
    padding: 0 8px 10px 8px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ft-subtle);
    border-bottom: 1px solid var(--ft-border-strong);
}

.ft-cmp-table th:first-child,
.ft-cmp-table td:first-child {
    text-align: left;
    padding-left: 2px;
}

.ft-cmp-table td {
    padding: 10px 8px;
    text-align: right;
    font-variant-numeric: tabular-nums;
    font-weight: 700;
    color: var(--ft-text);
    border-bottom: 1px solid var(--ft-border);
    white-space: nowrap;
}

.ft-cmp-table tr:last-child td {
    border-bottom: 0;
}

.ft-cmp-table tr.is-total td {
    border-top: 1px solid var(--ft-border-strong);
    font-weight: 800;
}

.ft-cmp-table td.is-muted {
    color: var(--ft-muted);
    font-weight: 600;
}

.ft-cmp-table td .ft-delta {
    font-size: 11.5px;
    padding: 2px 8px;
}

.ft-cmp-cat {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-weight: 700;
}

.ft-cmp-cat i {
    width: 8px;
    height: 8px;
    border-radius: 99px;
    display: inline-block;
}

.ft-top-list {
    display: flex;
    flex-direction: column;
}

.ft-top-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 2px;
}

.ft-top-row + .ft-top-row {
    border-top: 1px solid var(--ft-border);
}

.ft-top-rank {
    flex: 0 0 26px;
    width: 26px;
    height: 26px;
    border-radius: 8px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 800;
    color: var(--ft-muted);
    background: var(--ft-raised);
}

.ft-top-body {
    flex: 1;
    min-width: 0;
}

.ft-top-title {
    font-size: 14px;
    font-weight: 700;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.ft-top-meta {
    margin-top: 2px;
    font-size: 12px;
    color: var(--ft-muted);
}

.ft-top-amount {
    font-size: 14.5px;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}

@media (max-width: 1100px) {
    .ft-report-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .ft-report-highlights { grid-template-columns: 1fr; }
}

@media (max-width: 900px) {
    .ft-hero {
        grid-template-columns: 1fr;
        gap: 14px;
        padding: 24px 22px;
    }

    .ft-hero-spark-caption {
        align-self: flex-start;
    }
}

/* ================================================================ scrollbar */

::-webkit-scrollbar-track {
    background: transparent;
}
"""


# Solo PC (sul telefono le KPI hanno altezze fisse in MOBILE_REFRESH_CSS).
DESKTOP_REFRESH_CSS = r"""
/* Riga dei KPI: tutte le card alte come la più alta (nel report Risparmio e
   Tasso hanno la riga investito / liquidità in più). La colonna passa la sua
   altezza fino alla card. Solo la riga più interna: anche la pagina
   (menu + contenuto) è fatta di colonne. */
[data-testid="stHorizontalBlock"]:has(.ft-kpi-card):not(:has([data-testid="stHorizontalBlock"] .ft-kpi-card)) {
    align-items: stretch !important;
}

[data-testid="stHorizontalBlock"]:has(.ft-kpi-card):not(:has([data-testid="stHorizontalBlock"] .ft-kpi-card)) > [data-testid="stColumn"],
[data-testid="stHorizontalBlock"]:has(.ft-kpi-card):not(:has([data-testid="stHorizontalBlock"] .ft-kpi-card)) > [data-testid="stColumn"] div:has(.ft-kpi-card) {
    display: flex !important;
    flex-direction: column !important;
}

[data-testid="stHorizontalBlock"]:has(.ft-kpi-card):not(:has([data-testid="stHorizontalBlock"] .ft-kpi-card)) > [data-testid="stColumn"] {
    align-self: stretch !important;
}

[data-testid="stHorizontalBlock"]:has(.ft-kpi-card):not(:has([data-testid="stHorizontalBlock"] .ft-kpi-card)) > [data-testid="stColumn"] div:has(.ft-kpi-card) {
    flex: 1 1 auto !important;
}

[data-testid="stHorizontalBlock"]:has(.ft-kpi-card):not(:has([data-testid="stHorizontalBlock"] .ft-kpi-card)) .ft-kpi-card {
    flex: 1 1 auto;
    height: auto;
}
"""

MOBILE_REFRESH_CSS = r"""
/* ================================================================ telefono */

[data-testid="stAppViewContainer"] {
    background-attachment: scroll !important;
}

h1 {
    font-size: 27px !important;
}

.ft-section-title {
    font-size: 1.12rem !important;
    margin: 1.25rem 0 0.55rem 0 !important;
}

.ft-hero {
    padding: 20px 18px 16px 18px !important;
    border-radius: 22px;
    margin-top: 2px;
}

.ft-hero-value,
.ft-hero-value.is-long,
.ft-hero-value.is-huge {
    font-size: clamp(32px, 11vw, 44px) !important;
}

.ft-hero-row {
    margin-top: 12px;
}

.ft-spark {
    height: 72px;
}

/* KPI su telefono: più basse (prima 172 px), tutte uguali. */
.ft-kpi-card.ft-kpi {
    height: 116px !important;
    min-height: 116px !important;
    max-height: 116px !important;
    padding: 13px 13px 12px 13px !important;
    justify-content: flex-start !important;
    gap: 8px;
}

.ft-kpi:hover {
    transform: none;
}

/* Senza confronto (es. Movimenti, periodo "Tutto"): card più basse. */
.ft-kpi-card.ft-kpi:not(:has(.ft-delta)) {
    height: 96px !important;
    min-height: 96px !important;
    max-height: 96px !important;
}

/* Report: Risparmio e Tasso hanno una riga in più (investito / liquidità):
   altezza libera, ma uguale per le due card della riga. */
.ft-kpi-card.ft-kpi.has-extra.has-extra {
    height: auto !important;
    min-height: 196px !important;
    max-height: none !important;
}

.ft-hero-context {
    display: none;
}

.ft-kpi-icon {
    flex-basis: 26px;
    width: 26px;
    height: 26px;
    border-radius: 9px;
    font-size: 13px;
}

.ft-kpi .ft-kicker {
    font-size: 10.5px;
    letter-spacing: 0.06em;
}

.ft-kpi-value {
    font-size: clamp(16px, 13.5cqi, 24px) !important;
}

.ft-kpi-value.is-long { font-size: clamp(15px, 11.5cqi, 21px) !important; }
.ft-kpi-value.is-huge { font-size: clamp(14px, 10cqi, 19px) !important; }

.ft-kpi .ft-delta {
    font-size: 11px;
    padding: 2px 7px;
}

.ft-info-card {
    height: 148px !important;
    min-height: 148px !important;
    max-height: 148px !important;
    padding: 13px !important;
}

.ft-info-card-value {
    margin-top: 8px !important;
    font-size: 15.5px !important;
}

.ft-info-card-amount {
    font-size: clamp(16px, 12cqi, 21px) !important;
}

.ft-info-card-sub {
    margin-top: 6px;
}

.ft-info-card .ft-delta {
    font-size: 11px;
    padding: 2px 7px;
}

.ft-info-card-footer {
    font-size: 11px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.ft-cat-row {
    padding: 8px 2px;
}

.ft-report-kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
}

.ft-report-highlights {
    grid-template-columns: 1fr;
    gap: 10px;
}

div[class*="st-key-ft_report_card"] {
    padding: 14px 12px 10px 12px !important;
}

/* Tabella categorie del report: entra nello schermo senza scorrere di lato.
   Il nome della categoria può andare a capo, i numeri restano su una riga. */
.ft-cmp-table {
    font-size: 12.5px;
}

.ft-cmp-table th {
    padding: 0 4px 8px 4px;
    font-size: 10px;
    letter-spacing: 0.04em;
}

.ft-cmp-table td {
    padding: 9px 4px;
}

.ft-cmp-table td:first-child {
    white-space: normal;
    line-height: 1.25;
}

.ft-cmp-cat {
    gap: 5px;
}

.ft-cmp-cat i {
    display: none;
}

.ft-cmp-table td .ft-delta {
    font-size: 11px;
    padding: 2px 6px;
}

/* ---- Barra in basso: 6 voci ---- */

.st-key-ft_mobile_tabbar {
    gap: 0 !important;
    padding: 6px 6px calc(6px + env(safe-area-inset-bottom)) !important;
    background: var(--ft-panel-solid) !important;
    box-shadow: 0 -12px 30px -8px rgba(0, 0, 0, 0.28) !important;
}

.st-key-ft_mobile_tabbar [data-testid="stPageLink"] a {
    min-height: 54px !important;
    padding: 6px 0 !important;
    border-radius: 14px !important;
}

.st-key-ft_mobile_tabbar [data-testid="stMarkdownContainer"] p {
    font-size: 10.5px !important;
}

.st-key-ft_mobile_tabbar [class*="_on"] [data-testid="stPageLink"] a {
    background: rgba(var(--ft-accent-rgb), 0.14) !important;
    border-color: transparent !important;
}

/* Icone Material nella barra in basso (es. "Nuovo"): stessa misura delle emoji. */
.st-key-ft_mobile_tabbar [data-testid="stIconMaterial"] {
    font-size: 26px !important;
    line-height: 1 !important;
    margin: 0 !important;
    color: var(--ft-muted) !important;
}

.st-key-ft_mobile_tabbar [class*="_on"] [data-testid="stIconMaterial"] {
    color: var(--ft-accent-strong) !important;
}

/* Menu a tendina: l'elenco non deve mai essere più alto del riquadro che lo
   contiene. Quando sotto il campo c'è poco spazio (es. Categoria nella
   modifica di un movimento) il riquadro si accorcia e prima le ultime voci
   (Anticipi & Recuperi, Altro) restavano tagliate fuori e irraggiungibili. */
[data-testid$="VirtualDropdown"] {
    display: flex !important;
    flex-direction: column !important;
}

[data-testid$="VirtualDropdown"] > [role="listbox"] {
    flex: 1 1 auto !important;
    min-height: 0 !important;
}

/* Filtri della Home nel riquadro richiudibile. */
div[data-testid="stExpander"] summary {
    padding-top: 12px !important;
    padding-bottom: 12px !important;
}
"""
