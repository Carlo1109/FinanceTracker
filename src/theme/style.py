import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');

        :root {
            --ft-bg-0: #070b14;
            --ft-bg-1: #0b1220;
            --ft-bg-2: #111a2e;
            --ft-panel: rgba(11, 18, 32, 0.90);
            --ft-panel-soft: rgba(17, 26, 46, 0.74);
            --ft-border: rgba(148, 163, 184, 0.16);
            --ft-text: #eef3ff;
            --ft-muted: #94a3b8;
            --ft-accent: #60a5fa;
            --ft-accent-strong: #3b82f6;
            --ft-danger: #f87171;
            --ft-font: "Manrope", "Segoe UI", sans-serif;
            --ft-display: "Fraunces", Georgia, serif;
            --ft-radius: 18px;
        }

        #MainMenu,
        footer,
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"] {
            display: none !important;
        }

        html, body, [class*="css"], .stApp, .stMarkdown, .stText, .stCaption {
            font-family: var(--ft-font) !important;
        }

        .block-container {
            max-width: 100%;
            padding-top: 0.85rem;
            padding-right: 1.1rem;
            padding-bottom: 1.2rem;
            padding-left: 0.7rem;
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(
                    ellipse 70% 45% at 8% -10%,
                    rgba(96, 165, 250, 0.16),
                    transparent 55%
                ),
                linear-gradient(
                    165deg,
                    var(--ft-bg-0) 0%,
                    var(--ft-bg-1) 52%,
                    var(--ft-bg-2) 100%
                );
        }

        h1, h2, h3 {
            color: var(--ft-text) !important;
            font-family: var(--ft-display) !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
        }

        p, label, span, div, .stCaption {
            color: var(--ft-text);
        }

        [data-testid="stCaption"] {
            color: var(--ft-muted) !important;
        }

        /* ---- Custom navigation ---- */

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stPageLink"] a {
            min-height: 46px;
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 4px 0;
            padding: 0 14px;
            border-radius: 12px;
            border: 1px solid transparent;
            color: #c5d5cc !important;
            font-size: 14px;
            font-weight: 650;
            text-decoration: none !important;
            transition:
                transform 160ms ease,
                background 160ms ease,
                border-color 160ms ease;
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stPageLink"] a:hover {
            transform: translateX(2px);
            background: rgba(96, 165, 250, 0.08);
            border-color: rgba(96, 165, 250, 0.14);
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stPageLink"] a[aria-current="page"] {
            background: rgba(96, 165, 250, 0.16);
            border-color: rgba(96, 165, 250, 0.38);
            color: #ffffff !important;
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor) {
            position: sticky;
            top: 0.75rem;
            align-self: flex-start;
            height: calc(100vh - 1.5rem);
            max-height: calc(100vh - 1.5rem);
            overflow-y: auto;
            overflow-x: hidden;
            overscroll-behavior: contain;
            animation: ft-navigation-enter 220ms ease-out;
            scrollbar-width: none;
            -ms-overflow-style: none;
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)::-webkit-scrollbar {
            display: none;
        }

        @keyframes ft-navigation-enter {
            from { opacity: 0; transform: translateX(-8px); }
            to { opacity: 1; transform: translateX(0); }
        }

        @keyframes ft-fade-up {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stVerticalBlockBorderWrapper"] {
            min-height: 100%;
            padding: 0.85rem;
            border-radius: 22px;
            border: 1px solid var(--ft-border);
            background:
                radial-gradient(
                    circle at top left,
                    rgba(96, 165, 250, 0.12),
                    transparent 34%
                ),
                var(--ft-panel);
            box-shadow: 0 18px 40px rgba(0, 0, 0, 0.22);
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        .stButton > button {
            min-height: 46px;
            justify-content: flex-start;
            padding-left: 14px;
            border-radius: 12px;
            text-align: left;
            font-size: 14px;
            font-weight: 650;
            transition:
                transform 140ms ease,
                background 140ms ease,
                border-color 140ms ease;
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        .stButton > button[kind="secondary"] {
            background: transparent !important;
            border: 1px solid transparent !important;
            color: #c5d5cc !important;
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        .stButton > button[kind="secondary"]:hover {
            transform: translateX(2px);
            background: rgba(96, 165, 250, 0.08) !important;
            border-color: rgba(96, 165, 250, 0.14) !important;
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        .stButton > button[kind="primary"] {
            background: rgba(96, 165, 250, 0.18) !important;
            border: 1px solid rgba(96, 165, 250, 0.38) !important;
            color: #ffffff !important;
            box-shadow: none !important;
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stHorizontalBlock"]:first-of-type
        .stButton {
            display: flex;
            justify-content: flex-end;
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stHorizontalBlock"]:first-of-type
        .stButton > button {
            width: 38px !important;
            min-width: 38px !important;
            height: 38px !important;
            min-height: 38px !important;
            padding: 0 !important;
            margin: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #c5d5cc !important;
            font-size: 22px !important;
            font-weight: 600 !important;
            line-height: 1 !important;
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stHorizontalBlock"]:first-of-type
        .stButton > button:hover {
            color: var(--ft-accent) !important;
            transform: scale(1.06);
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stHorizontalBlock"]:first-of-type
        .stButton > button:focus,
        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stHorizontalBlock"]:first-of-type
        .stButton > button:active {
            outline: none !important;
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }

        /* ---- Content surfaces ---- */

        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: var(--ft-radius);
            border-color: var(--ft-border);
            background: var(--ft-panel-soft);
            animation: ft-fade-up 240ms ease-out;
        }

        .stButton > button {
            border-radius: 12px;
            font-weight: 700;
            border: 1px solid var(--ft-border);
            font-family: var(--ft-font) !important;
        }

        .stButton > button[kind="primary"] {
            background: linear-gradient(
                135deg,
                var(--ft-accent),
                var(--ft-accent-strong)
            );
            color: #04203a;
            border: none;
        }

        .stButton > button[kind="secondary"] {
            background: transparent;
            color: var(--ft-text);
        }

        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        .stTextArea textarea {
            border-radius: 12px;
            font-family: var(--ft-font) !important;
        }

        div[data-baseweb="select"] {
            border-radius: 12px;
        }

        div[data-testid="stFileUploader"] section {
            border-radius: 16px;
            border: 1px dashed rgba(96, 165, 250, 0.28);
            background: rgba(11, 18, 32, 0.55);
        }

        div[data-testid="stExpander"] {
            border-radius: 14px;
            border-color: var(--ft-border);
            background: rgba(11, 18, 32, 0.42);
        }

        .ft-section-title {
            font-family: var(--ft-display) !important;
            font-size: 1.35rem;
            font-weight: 700;
            color: var(--ft-text);
            margin: 1.1rem 0 0.55rem 0;
            letter-spacing: -0.02em;
        }

        .ft-movement-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            padding: 12px 4px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.10);
        }

        .ft-movement-row:last-child {
            border-bottom: none;
        }

        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-thumb {
            background: #243044;
            border-radius: 8px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #334155;
        }

        /* Pie: soft shadow + brighter slice on hover */
        .element-container:has(.ft-pie-anchor) + .element-container
        [data-testid="stPlotlyChart"] {
            filter: drop-shadow(0 16px 28px rgba(0, 0, 0, 0.45));
        }

        .element-container:has(.ft-pie-anchor) + .element-container
        .js-plotly-plot .pielayer path {
            transition: filter 0.15s ease, opacity 0.15s ease;
        }

        .element-container:has(.ft-pie-anchor) + .element-container
        .js-plotly-plot .pielayer path:hover {
            filter: brightness(1.22);
            opacity: 1 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
