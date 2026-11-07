"""
Strato CSS per smartphone (app Android).

Si aggiunge al tema normale (src/theme/style.py) senza sostituirlo:
stessi colori, font e componenti, ma impaginazione pensata per il tocco.
Viene iniettato solo quando IS_ANDROID è vero, quindi il desktop non cambia.
"""

from __future__ import annotations

MOBILE_CSS = """
/* ---------- Base touch ---------- */

html, body {
    -webkit-tap-highlight-color: transparent;
    overscroll-behavior-y: none;
}

.stApp {
    -webkit-text-size-adjust: 100%;
    text-size-adjust: 100%;
}

/* Niente selezione accidentale del testo su pulsanti e schede. */
button, [data-testid="stPageLink"] a, [role="tab"], label {
    -webkit-user-select: none;
    user-select: none;
    touch-action: manipulation;
}

[data-testid="stStatusWidget"],
[data-testid="stDecoration"] {
    display: none !important;
}

[data-testid="stMainBlockContainer"] {
    max-width: 100% !important;
    padding-top: calc(10px + env(safe-area-inset-top)) !important;
    padding-left: 14px !important;
    padding-right: 14px !important;
    padding-bottom: calc(104px + env(safe-area-inset-bottom)) !important;
}

/* ---------- Barra superiore ---------- */

.ft-mtop {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 2px 2px 4px;
}

.ft-mtop-logo {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.22);
}

.ft-mtop-title {
    flex: 1;
    font-family: Fraunces, Georgia, serif;
    font-size: 21px;
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1;
}

.ft-mtop-version {
    padding: 3px 8px;
    border-radius: 8px;
    font-size: 11px;
    letter-spacing: 0.04em;
}

/* ---------- Barra di navigazione in basso ---------- */

.st-key-ft_mobile_tabbar {
    position: fixed !important;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 999990;
    width: auto !important;
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 2px !important;
    padding: 6px 8px calc(6px + env(safe-area-inset-bottom)) !important;
    background: color-mix(in srgb, var(--ft-panel) 86%, transparent);
    -webkit-backdrop-filter: blur(18px) saturate(1.5);
    backdrop-filter: blur(18px) saturate(1.5);
    border-top: 1px solid var(--ft-border);
    box-shadow: 0 -10px 30px rgba(0, 0, 0, 0.18);
}

.st-key-ft_mobile_tabbar > div {
    flex: 1 1 0 !important;
    min-width: 0 !important;
    width: auto !important;
    margin: 0 !important;
    gap: 0 !important;
}

.st-key-ft_mobile_tabbar [data-testid="stElementContainer"],
.st-key-ft_mobile_tabbar [data-testid="stPageLink"],
.st-key-ft_mobile_tabbar [data-testid="stPageLink"] > div {
    width: 100% !important;
    margin: 0 !important;
}

.st-key-ft_mobile_tabbar [data-testid="stPageLink"] a {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 3px !important;
    width: 100% !important;
    min-height: 56px !important;
    margin: 0 !important;
    padding: 6px 2px !important;
    border-radius: 16px !important;
    border: 1px solid transparent !important;
    background: transparent !important;
    text-decoration: none !important;
    transition: background 160ms ease, transform 120ms ease;
}

.st-key-ft_mobile_tabbar [data-testid="stIconEmoji"] {
    font-size: 21px !important;
    line-height: 1 !important;
    margin: 0 !important;
    filter: saturate(0.75);
    opacity: 0.8;
}

.st-key-ft_mobile_tabbar [data-testid="stPageLink"] a > span {
    margin: 0 !important;
}

.st-key-ft_mobile_tabbar [data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
    font-family: var(--ft-font) !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    letter-spacing: 0.01em;
    color: var(--ft-muted) !important;
    white-space: nowrap;
}

.st-key-ft_mobile_tabbar [class*="_on"] [data-testid="stPageLink"] a {
    background: rgba(var(--ft-accent-rgb), 0.16) !important;
    border-color: rgba(var(--ft-accent-rgb), 0.30) !important;
}

.st-key-ft_mobile_tabbar [class*="_on"] [data-testid="stIconEmoji"] {
    filter: none;
    opacity: 1;
}

.st-key-ft_mobile_tabbar [class*="_on"] [data-testid="stMarkdownContainer"] p {
    color: var(--ft-accent-strong) !important;
}

.st-key-ft_mobile_tabbar [data-testid="stPageLink"] a:active {
    transform: scale(0.92);
}

/* Con un dialog aperto la barra in basso si nasconde (non copre i pulsanti). */
body:has([data-testid="stDialog"]) .st-key-ft_mobile_tabbar {
    display: none !important;
}

/* Messaggi (toast) in basso, sopra la barra: non coprono titoli e pulsanti di chiusura. */
[data-testid="stToastContainer"] {
    top: auto !important;
    bottom: calc(84px + env(safe-area-inset-bottom)) !important;
    left: 12px !important;
    right: 12px !important;
    width: auto !important;
    align-items: stretch !important;
}

[data-testid="stToastContainer"] {
    margin: 0 !important;
    max-width: calc(100vw - 24px) !important;
    box-sizing: border-box !important;
    transform: none !important;
}

[data-testid="stToastContainer"] ol {
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}

[data-testid="stToastContainer"] li,
[data-testid="stToast"] {
    box-sizing: border-box !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: calc(100vw - 24px) !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
}

/* Caricamento file: sul telefono basta il pulsante (niente "trascina qui" e limite in MB). */
[data-testid="stFileUploaderDropzoneInstructions"] {
    display: none !important;
}

/* ---------- Controlli comodi per il dito ---------- */

.stButton > button,
.stDownloadButton > button,
[data-testid="stFormSubmitButton"] > button {
    min-height: 46px;
}

[data-testid="stSelectbox"] [role="combobox"],
[data-baseweb="input"],
[data-testid="stDateInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
    min-height: 46px;
}

/* 16px evita lo zoom automatico del browser quando si tocca un campo. */
input, textarea, select, [data-testid="stSelectbox"] input {
    font-size: 16px !important;
}

[data-testid="stCheckbox"] label,
[data-testid="stRadio"] label,
[data-testid="stToggle"] label {
    min-height: 34px;
    align-items: center;
}

.stButton > button:active,
.stDownloadButton > button:active {
    transform: scale(0.97);
}

/* Schede (tabs) scorrevoli in orizzontale invece di andare a capo. */
[data-baseweb="tab-list"] {
    overflow-x: auto !important;
    scrollbar-width: none;
}

[data-baseweb="tab-list"]::-webkit-scrollbar {
    display: none;
}

[data-baseweb="tab"] {
    min-height: 44px;
    flex-shrink: 0;
}

/* Tabelle e dataframe: scorrono dentro il loro riquadro. */
[data-testid="stDataFrame"],
[data-testid="stTable"] {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

/* Grafici: lo scroll verticale della pagina resta libero. */
.js-plotly-plot,
.js-plotly-plot .plotly,
[data-testid="stPlotlyChart"] {
    touch-action: pan-y;
}

/* ---------- Niente hover "appiccicoso" sugli schermi touch ---------- */

@media (hover: none) {
    .stApp *:not(svg):not(svg *):hover {
        transform: none !important;
    }
}

/* ---------- Impaginazione smartphone ---------- */

@media (max-width: 640px) {
    h1 {
        font-size: 30px !important;
        line-height: 1.12 !important;
    }

    h2 {
        font-size: 23px !important;
    }

    h3 {
        font-size: 19px !important;
    }

    /* KPI e card informative: griglia 2 x 2 invece di una colonna lunghissima. */
    [data-testid="stHorizontalBlock"]:has(.ft-kpi-card),
    [data-testid="stHorizontalBlock"]:has(.ft-info-card) {
        flex-wrap: wrap !important;
        gap: 10px !important;
    }

    [data-testid="stHorizontalBlock"]:has(.ft-kpi-card) > [data-testid="stColumn"],
    [data-testid="stHorizontalBlock"]:has(.ft-info-card) > [data-testid="stColumn"] {
        flex: 1 1 calc(50% - 5px) !important;
        width: calc(50% - 5px) !important;
        min-width: calc(50% - 5px) !important;
        max-width: calc(50% - 5px) !important;
    }

    [data-testid="stMarkdownContainer"]:has(> .ft-kpi-card),
    [data-testid="stMarkdownContainer"]:has(> .ft-info-card) {
        margin-bottom: 0 !important;
    }

    /* Numero dispari di card: l'ultima prende tutta la riga. */
    [data-testid="stHorizontalBlock"]:has(.ft-kpi-card) > [data-testid="stColumn"]:last-child:nth-child(odd),
    [data-testid="stHorizontalBlock"]:has(.ft-info-card) > [data-testid="stColumn"]:last-child:nth-child(odd) {
        flex-basis: 100% !important;
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
    }

    .ft-kpi-card {
        min-height: 98px !important;
        padding: 14px 14px !important;
    }

    .ft-kpi-value {
        font-size: clamp(15px, 13cqi, 26px) !important;
    }

    .ft-kpi-value.is-long {
        font-size: clamp(14px, 11cqi, 22px) !important;
    }

    .ft-kpi-value.is-huge {
        font-size: clamp(13px, 10cqi, 20px) !important;
    }

    /* Stessa altezza per tutte le card (il tasso di risparmio ha anche la casella). */
    .ft-info-card {
        min-height: 178px !important;
        padding: 14px 14px !important;
        container-type: inline-size;
    }

    .ft-info-card-amount {
        font-size: clamp(16px, 12cqi, 22px) !important;
        white-space: nowrap;
    }

    /* Card principale (bilancio). */
    div:has(> .ft-hero-value) {
        min-height: 0 !important;
        padding: 22px 20px !important;
    }

    .ft-hero-value,
    .ft-hero-value.is-long,
    .ft-hero-value.is-huge {
        font-size: clamp(30px, 11vw, 44px) !important;
    }

    /* Pannello movimento: niente spazio vuoto sopra la riga. */
    [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .ft-movement-anchor) {
        gap: 0 !important;
        padding: 10px 12px !important;
        border-radius: 16px !important;
    }

    [data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] .ft-movement-anchor),
    [data-testid="stElementContainer"]:has(.ft-movement-anchor):not(:has(.ft-movement-card)) {
        display: none !important;
    }

    /* Riga movimento compatta:  [✓] titolo/meta  importo
                                       ...        [Modifica]  */
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-movement-card) {
        display: grid !important;
        grid-template-columns: 26px minmax(0, 1fr) auto;
        grid-template-areas:
            "sel body amount"
            "sel body action";
        column-gap: 10px !important;
        row-gap: 6px !important;
        align-items: center !important;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-movement-card) > [data-testid="stColumn"] {
        width: auto !important;
        min-width: 0 !important;
        max-width: none !important;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-movement-card) > [data-testid="stColumn"]:nth-child(1) {
        grid-area: sel;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-movement-card) > [data-testid="stColumn"]:nth-child(2) {
        grid-area: body;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-movement-card) > [data-testid="stColumn"]:nth-child(3) {
        grid-area: amount;
        align-self: end;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-movement-card) > [data-testid="stColumn"]:nth-child(4) {
        grid-area: action;
        align-self: start;
        justify-self: end;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-movement-card) [data-testid="stMarkdownContainer"] {
        margin-bottom: 0 !important;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-movement-card) .ft-movement-amount {
        text-align: right;
        white-space: nowrap;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-movement-card) .stButton > button {
        min-height: 34px !important;
        height: 34px !important;
        width: auto !important;
        padding: 0 14px !important;
        border-radius: 999px !important;
        font-size: 13px !important;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-movement-card) .ft-movement-title {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-movement-card) .ft-movement-meta {
        flex-wrap: wrap;
        row-gap: 4px;
    }

    /* Righe elenco (conti, categorie): testo + importo, pulsanti sotto affiancati. */
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-movement-title):not(:has(.ft-movement-card)) {
        flex-wrap: wrap !important;
        gap: 8px !important;
        align-items: center !important;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-movement-title):not(:has(.ft-movement-card))
    > [data-testid="stColumn"] {
        flex: 1 1 0 !important;
        width: auto !important;
        min-width: 28% !important;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-movement-title):not(:has(.ft-movement-card))
    > [data-testid="stColumn"]:first-child {
        flex: 1 1 52% !important;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-movement-title):not(:has(.ft-movement-card))
    > [data-testid="stColumn"]:nth-child(2):not(:last-child) {
        flex: 0 0 42% !important;
        min-width: 0 !important;
        text-align: right;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-movement-title):not(:has(.ft-movement-card))
    [data-testid="stMarkdownContainer"] {
        margin-bottom: 0 !important;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-movement-title):not(:has(.ft-movement-card))
    .stButton > button {
        min-height: 40px !important;
        font-size: 14px !important;
    }

    /* Impostazioni > Aspetto: temi affiancati, colori su una riga. */
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-theme-card),
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-accent-swatch) {
        flex-wrap: nowrap !important;
        gap: 8px !important;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-theme-card) > [data-testid="stColumn"],
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-accent-swatch) > [data-testid="stColumn"] {
        flex: 1 1 0 !important;
        width: auto !important;
        min-width: 0 !important;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-accent-swatch) .stButton > button,
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-theme-card) .stButton > button {
        min-height: 38px !important;
        padding: 0 6px !important;
        font-size: 13px !important;
    }

    .ft-accent-orb {
        width: 44px !important;
        height: 44px !important;
    }

    /* Data giorno / mese / anno: restano su una riga. */
    [data-testid="stElementContainer"]:has(.ft-date-label)
    + [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"],
    [data-testid="stElementContainer"]:has(.ft-date-label)
    + [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 8px !important;
    }

    [data-testid="stElementContainer"]:has(.ft-date-label)
    + [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
    [data-testid="stElementContainer"]:has(.ft-date-label)
    + [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex: 1 1 0 !important;
        width: auto !important;
        min-width: 0 !important;
    }

    [data-testid="stElementContainer"]:has(.ft-date-label)
    + [data-testid="stLayoutWrapper"] > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2),
    [data-testid="stElementContainer"]:has(.ft-date-label)
    + [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) {
        flex-grow: 1.6 !important;
    }

    /* Card distribuzione: torta sopra, elenco sotto (niente separatore laterale). */
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-category-scroll)
    > [data-testid="stColumn"] {
        border-right: none !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-category-scroll)
    > [data-testid="stColumn"]:first-child {
        border-bottom: 1px solid var(--ft-border);
        padding-bottom: 6px !important;
    }

    /* Dialog: foglio a tutta larghezza, quasi a tutta altezza, che scorre al suo interno. */
    /* Il contenitore esterno ha margini fissi di Streamlit e overflow nascosto:
       lo allarghiamo noi e il foglio lo riempie (niente bordo destro tagliato). */
    [data-testid="stDialog"] > div:has(> section[role="dialog"]) {
        box-sizing: border-box !important;
        width: calc(100vw - 16px) !important;
        min-width: 0 !important;
        max-width: calc(100vw - 16px) !important;
        flex: 0 0 auto !important;
        margin: 10px 8px !important;
        left: 0 !important;
        right: 0 !important;
        background: transparent !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
    }

    [data-testid="stDialog"] section[role="dialog"] {
        box-sizing: border-box !important;
        display: flex !important;
        flex-direction: column !important;
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        max-height: calc(100dvh - 20px) !important;
        margin: 0 !important;
        padding: 0 0 calc(10px + env(safe-area-inset-bottom)) 0 !important;
        border-radius: 22px !important;
        /* Fondo pieno: dietro al foglio non si intravedono le card della pagina. */
        background:
            radial-gradient(circle at 12% 0%, rgba(var(--ft-accent-rgb), 0.12), transparent 42%),
            var(--ft-menu-bg) !important;
        background-color: var(--ft-menu-bg) !important;
        overflow-x: hidden !important;
        overscroll-behavior: contain;
    }

    [data-testid="stDialog"] section[role="dialog"] > h2 {
        padding: 22px 64px 8px 18px !important;
        font-size: 22px !important;
        line-height: 1.2 !important;
    }

    [data-testid="stDialog"] section[role="dialog"] > h2 * {
        margin: 0 !important;
        overflow-wrap: anywhere;
    }

    [data-testid="stDialog"] section[role="dialog"] > div {
        padding: 8px 18px 16px 18px !important;
        min-width: 0 !important;
    }

    [data-testid="stDialog"] section[role="dialog"] [data-testid="stVerticalBlock"],
    [data-testid="stDialog"] section[role="dialog"] [data-testid="stElementContainer"],
    [data-testid="stDialog"] section[role="dialog"] [data-testid="stHorizontalBlock"],
    [data-testid="stDialog"] section[role="dialog"] [data-testid="stColumn"] {
        min-width: 0 !important;
        max-width: 100% !important;
    }

    /* Pulsante di chiusura: resta in vista e si tocca facilmente (44 px). */
    /* Resta in alto a destra del foglio anche scorrendo (sticky), mai fuori dal bordo. */
    [data-testid="stDialog"] section[role="dialog"] > button:first-child {
        position: sticky !important;
        top: 12px !important;
        right: auto !important;
        left: auto !important;
        align-self: flex-end !important;
        flex: 0 0 auto !important;
        margin: 12px 12px -56px auto !important;
        z-index: 5 !important;
        width: 44px !important;
        height: 44px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 999px !important;
        background: color-mix(in srgb, var(--ft-panel) 92%, transparent) !important;
        border: 1px solid var(--ft-border) !important;
    }

    [data-testid="stDialog"] section[role="dialog"] > button:first-child svg {
        width: 18px !important;
        height: 18px !important;
    }

    /* File di soli pulsanti (Conferma/Annulla, griglia icone): restano affiancati.
       (:has non si può annidare, quindi si escludono le file con altri elementi.) */
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .stButton, > [data-testid="stColumn"] .stDownloadButton):not(:has(> [data-testid="stColumn"] [data-testid="stMarkdown"], > [data-testid="stColumn"] [data-testid="stHtml"], > [data-testid="stColumn"] [data-testid="stCaptionContainer"], > [data-testid="stColumn"] [data-testid="stTextInput"], > [data-testid="stColumn"] [data-testid="stTextArea"], > [data-testid="stColumn"] [data-testid="stSelectbox"], > [data-testid="stColumn"] [data-testid="stMultiSelect"], > [data-testid="stColumn"] [data-testid="stNumberInput"], > [data-testid="stColumn"] [data-testid="stCheckbox"], > [data-testid="stColumn"] [data-testid="stToggle"], > [data-testid="stColumn"] [data-testid="stRadio"], > [data-testid="stColumn"] [data-testid="stPills"], > [data-testid="stColumn"] [data-testid="stImage"], > [data-testid="stColumn"] [data-testid="stPlotlyChart"], > [data-testid="stColumn"] [data-testid="stIFrame"], > [data-testid="stColumn"] [data-testid="stFileUploader"], > [data-testid="stColumn"] [data-testid="stAlert"], > [data-testid="stColumn"] [data-testid="stHorizontalBlock"])) {
        flex-wrap: nowrap !important;
        gap: 8px !important;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .stButton, > [data-testid="stColumn"] .stDownloadButton):not(:has(> [data-testid="stColumn"] [data-testid="stMarkdown"], > [data-testid="stColumn"] [data-testid="stHtml"], > [data-testid="stColumn"] [data-testid="stCaptionContainer"], > [data-testid="stColumn"] [data-testid="stTextInput"], > [data-testid="stColumn"] [data-testid="stTextArea"], > [data-testid="stColumn"] [data-testid="stSelectbox"], > [data-testid="stColumn"] [data-testid="stMultiSelect"], > [data-testid="stColumn"] [data-testid="stNumberInput"], > [data-testid="stColumn"] [data-testid="stCheckbox"], > [data-testid="stColumn"] [data-testid="stToggle"], > [data-testid="stColumn"] [data-testid="stRadio"], > [data-testid="stColumn"] [data-testid="stPills"], > [data-testid="stColumn"] [data-testid="stImage"], > [data-testid="stColumn"] [data-testid="stPlotlyChart"], > [data-testid="stColumn"] [data-testid="stIFrame"], > [data-testid="stColumn"] [data-testid="stFileUploader"], > [data-testid="stColumn"] [data-testid="stAlert"], > [data-testid="stColumn"] [data-testid="stHorizontalBlock"]))
    > [data-testid="stColumn"] {
        flex: 1 1 0 !important;
        width: auto !important;
        min-width: 0 !important;
    }

    /* ...le colonne vuote usate come spaziatura non servono sul telefono. */
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:not(:has([data-testid="stElementContainer"])) {
        display: none !important;
    }

    /* Griglia icone: pulsanti compatti, emoji ben visibili. */
    div[class*="st-key-category_icon_"] button,
    div[class*="st-key-settings_new_category_icon_"] button {
        min-height: 40px !important;
        height: 40px !important;
        padding: 0 !important;
        font-size: 20px !important;
    }

    [data-testid="stHorizontalBlock"]:has(div[class*="st-key-category_icon_"]),
    [data-testid="stHorizontalBlock"]:has(div[class*="st-key-settings_new_category_icon_"]) {
        gap: 4px !important;
    }

    /* Parole chiave: etichetta e piccolo ✕ sulla stessa riga. */
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-keyword-chip) {
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 8px !important;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-keyword-chip) > [data-testid="stColumn"]:first-child {
        flex: 1 1 auto !important;
        width: auto !important;
        min-width: 0 !important;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-keyword-chip) > [data-testid="stColumn"]:last-child {
        flex: 0 0 40px !important;
        width: 40px !important;
        min-width: 40px !important;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-keyword-chip) [data-testid="stMarkdownContainer"] {
        margin-bottom: 0 !important;
    }

    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .ft-keyword-chip) .stButton > button {
        min-height: 36px !important;
        height: 36px !important;
        width: 36px !important;
        padding: 0 !important;
        border-radius: 999px !important;
        color: var(--ft-danger) !important;
        border-color: rgba(248, 113, 113, 0.35) !important;
        background: rgba(248, 113, 113, 0.08) !important;
    }
}
"""
