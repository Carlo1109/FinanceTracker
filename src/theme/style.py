"""CSS globale FinanceTracker: temi chiaro/scuro + accenti via CSS variables."""

from __future__ import annotations

import streamlit as st

from src.services.settings_service import get_accent, get_theme_mode
from src.theme.tokens import resolve_palette


def _sync_streamlit_native_theme(theme_id: str) -> None:
    """
    Allinea il tema nativo Streamlit (select, uploader, …) alla preferenza FT.

    Lo sfondo custom via CSS non basta: Baseweb legge Light/Dark da
    localStorage. Se non coincide, i widget restano neri sul tema chiaro.
    """
    desired = "Light" if theme_id == "light" else "Dark"
    st.html(
        f"""
        <div hidden aria-hidden="true" data-ft-theme-sync="{desired}"></div>
        <script>
        (function () {{
          const desired = {desired!r};
          const path = window.location.pathname || "/";
          const key = "stActiveTheme-" + path + "-v2";
          const payload = JSON.stringify(desired);
          let current = null;
          try {{
            current = JSON.parse(window.localStorage.getItem(key));
          }} catch (err) {{
            current = null;
          }}
          for (let i = 0; i < window.localStorage.length; i++) {{
            const k = window.localStorage.key(i);
            if (k && k.indexOf("stActiveTheme") === 0 && k.slice(-3) === "-v2") {{
              window.localStorage.setItem(k, payload);
            }}
          }}
          window.localStorage.setItem(key, payload);
          if (current !== desired) {{
            window.location.reload();
          }}
        }})();
        </script>
        """,
        width="content",
        unsafe_allow_javascript=True,
    )


def apply_theme(
    theme_id: str | None = None,
    accent_id: str | None = None,
) -> None:
    theme_id = theme_id or get_theme_mode()
    accent_id = accent_id or get_accent()
    theme, accent = resolve_palette(theme_id, accent_id)

    primary_btn_text = "#04203a" if theme_id == "dark" else "#ffffff"
    # Sfondi solidi per popover (niente navy Streamlit sotto il trasparente)
    menu_bg = "#ffffff" if theme_id == "light" else "#111a2e"
    field_border = "#e2e8f0" if theme_id == "light" else "rgba(148, 163, 184, 0.32)"

    _sync_streamlit_native_theme(theme_id)

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');

        :root {{
            --ft-bg-0: {theme.bg_0};
            --ft-bg-1: {theme.bg_1};
            --ft-bg-2: {theme.bg_2};
            --ft-panel: {theme.panel};
            --ft-panel-soft: {theme.panel_soft};
            --ft-border: {theme.border};
            --ft-text: {theme.text};
            --ft-muted: {theme.muted};
            --ft-nav-text: {theme.nav_text};
            --ft-accent: {accent.accent};
            --ft-accent-strong: {accent.accent_strong};
            --ft-accent-rgb: {accent.accent_rgb};
            --ft-danger: {theme.danger};
            --ft-income: #34d399;
            --ft-investment: {theme.investment};
            --ft-shadow: {theme.shadow};
            --ft-scrollbar: {theme.scrollbar};
            --ft-input-bg: {theme.input_bg};
            --ft-glow-alpha: {theme.glow_alpha};
            --ft-primary-btn-text: {primary_btn_text};
            --ft-font: "Manrope", "Segoe UI", sans-serif;
            --ft-display: "Fraunces", Georgia, serif;
            --ft-radius: 18px;

            /* Variabili usate internamente da Streamlit/Baseweb */
            --background-color: {theme.bg_1};
            --secondary-background-color: {theme.input_bg};
            --text-color: {theme.text};
            --primary-color: {accent.accent};
            --secondary-text: {theme.muted};
        }}

        html, body, .stApp, [data-testid="stAppViewContainer"] {{
            color-scheme: {theme_id} !important;
        }}

        #MainMenu,
        footer,
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"] {{
            display: none !important;
        }}

        /* Niente toolbar fullscreen sulle immagini (logo, …) */
        [data-testid="stElementToolbar"],
        [data-testid="stElementToolbarButton"],
        [data-testid="stElementToolbarButtonContainer"],
        [data-testid="stImage"] [data-testid="stElementToolbar"],
        [data-testid="stImageContainer"] [data-testid="stElementToolbar"],
        .stImage button {{
            display: none !important;
            visibility: hidden !important;
            pointer-events: none !important;
            opacity: 0 !important;
        }}

        html, body, [class*="css"], .stApp, .stMarkdown, .stText, .stCaption {{
            font-family: var(--ft-font) !important;
        }}

        .block-container {{
            max-width: 100%;
            padding-top: 0.85rem;
            padding-right: 1.1rem;
            padding-bottom: 1.2rem;
            padding-left: 0.7rem;
        }}

        [data-testid="stAppViewContainer"] {{
            background:
                radial-gradient(
                    ellipse 70% 45% at 8% -10%,
                    rgba(var(--ft-accent-rgb), var(--ft-glow-alpha)),
                    transparent 55%
                ),
                linear-gradient(
                    165deg,
                    var(--ft-bg-0) 0%,
                    var(--ft-bg-1) 52%,
                    var(--ft-bg-2) 100%
                );
        }}

        h1, h2, h3 {{
            color: var(--ft-text) !important;
            font-family: var(--ft-display) !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
        }}

        p, label, span, div, .stCaption {{
            color: var(--ft-text);
        }}

        [data-testid="stCaption"] {{
            color: var(--ft-muted) !important;
        }}

        /* ---- Custom navigation ---- */

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stPageLink"] a {{
            min-height: 46px;
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 4px 0;
            padding: 0 14px;
            border-radius: 12px;
            border: 1px solid transparent;
            color: var(--ft-nav-text) !important;
            font-size: 14px;
            font-weight: 650;
            text-decoration: none !important;
            transition:
                transform 160ms ease,
                background 160ms ease,
                border-color 160ms ease;
        }}

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stPageLink"] a:hover {{
            transform: translateX(2px);
            background: rgba(var(--ft-accent-rgb), 0.08);
            border-color: rgba(var(--ft-accent-rgb), 0.14);
        }}

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stPageLink"] a[aria-current="page"] {{
            background: rgba(var(--ft-accent-rgb), 0.16);
            border-color: rgba(var(--ft-accent-rgb), 0.38);
            color: var(--ft-text) !important;
        }}

        [data-testid="stColumn"]:has(.ft-navigation-anchor) {{
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
        }}

        [data-testid="stColumn"]:has(.ft-navigation-anchor)::-webkit-scrollbar {{
            display: none;
        }}

        @keyframes ft-navigation-enter {{
            from {{ opacity: 0; transform: translateX(-8px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}

        @keyframes ft-fade-up {{
            from {{ opacity: 0; transform: translateY(8px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        @keyframes ft-import-pop {{
            0% {{
                opacity: 0;
                transform: translateY(14px) scale(0.97);
            }}
            60% {{
                opacity: 1;
                transform: translateY(-2px) scale(1.01);
            }}
            100% {{
                opacity: 1;
                transform: translateY(0) scale(1);
            }}
        }}

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stVerticalBlockBorderWrapper"] {{
            min-height: 100%;
            padding: 0.85rem;
            border-radius: 22px;
            border: 1px solid var(--ft-border);
            background:
                radial-gradient(
                    circle at top left,
                    rgba(var(--ft-accent-rgb), 0.12),
                    transparent 34%
                ),
                var(--ft-panel);
            box-shadow: var(--ft-shadow);
        }}

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        .stButton > button {{
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
        }}

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        .stButton > button[kind="secondary"] {{
            background: transparent !important;
            border: 1px solid transparent !important;
            color: var(--ft-nav-text) !important;
        }}

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        .stButton > button[kind="secondary"]:hover {{
            transform: translateX(2px);
            background: rgba(var(--ft-accent-rgb), 0.08) !important;
            border-color: rgba(var(--ft-accent-rgb), 0.14) !important;
        }}

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        .stButton > button[kind="primary"] {{
            background: rgba(var(--ft-accent-rgb), 0.18) !important;
            border: 1px solid rgba(var(--ft-accent-rgb), 0.38) !important;
            color: var(--ft-text) !important;
            box-shadow: none !important;
        }}

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stHorizontalBlock"]:first-of-type
        .stButton {{
            display: flex;
            justify-content: flex-end;
        }}

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stHorizontalBlock"]:first-of-type
        .stButton > button {{
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
            color: var(--ft-nav-text) !important;
            font-size: 22px !important;
            font-weight: 600 !important;
            line-height: 1 !important;
        }}

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stHorizontalBlock"]:first-of-type
        .stButton > button:hover {{
            color: var(--ft-accent) !important;
            transform: scale(1.06);
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }}

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stHorizontalBlock"]:first-of-type
        .stButton > button:focus,
        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stHorizontalBlock"]:first-of-type
        .stButton > button:active {{
            outline: none !important;
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }}

        /* ---- Content surfaces ---- */

        [data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: var(--ft-radius);
            border-color: var(--ft-border);
            background: var(--ft-panel-soft);
            animation: ft-fade-up 240ms ease-out;
        }}

        .stButton > button {{
            border-radius: 12px;
            font-weight: 700;
            border: 1px solid var(--ft-border);
            font-family: var(--ft-font) !important;
        }}

        .stButton > button[kind="primary"],
        [data-testid="stBaseButton-primary"],
        [data-testid="stDownloadButton"] button[kind="primary"],
        [data-testid="stBaseButton-primaryDownload"],
        [data-testid="stDownloadButton"] [data-testid="stBaseButton-primary"] {{
            background: linear-gradient(
                135deg,
                var(--ft-accent),
                var(--ft-accent-strong)
            ) !important;
            color: var(--ft-primary-btn-text) !important;
            border: none !important;
        }}

        .stButton > button[kind="secondary"] {{
            background: {theme.input_bg} !important;
            background-color: {theme.input_bg} !important;
            color: {theme.text} !important;
            border: 1px solid {theme.border} !important;
        }}

        .stButton > button[kind="secondary"]:hover {{
            border-color: rgba(var(--ft-accent-rgb), 0.45) !important;
            background: rgba(var(--ft-accent-rgb), 0.08) !important;
        }}

        /* Dialog export / popup Streamlit a tema */
        [data-testid="stDialog"],
        div[role="dialog"],
        .stDialog {{
            color: {theme.text} !important;
        }}

        [data-testid="stDialog"] > div,
        div[role="dialog"] > div,
        [data-testid="stDialog"] [data-baseweb="modal"],
        div[data-baseweb="modal"] {{
            background:
                radial-gradient(
                    circle at 12% 0%,
                    rgba(var(--ft-accent-rgb), 0.12),
                    transparent 42%
                ),
                {theme.panel} !important;
            background-color: {theme.panel} !important;
            color: {theme.text} !important;
            border: 1px solid {theme.border} !important;
            border-radius: 18px !important;
            box-shadow: var(--ft-shadow) !important;
        }}

        [data-testid="stDialog"] h1,
        [data-testid="stDialog"] h2,
        [data-testid="stDialog"] h3,
        [data-testid="stDialog"] p,
        [data-testid="stDialog"] span,
        [data-testid="stDialog"] label,
        div[role="dialog"] h1,
        div[role="dialog"] h2,
        div[role="dialog"] p,
        div[role="dialog"] span {{
            color: {theme.text} !important;
        }}

        [data-testid="stDialog"] button[kind="secondary"],
        div[role="dialog"] button[kind="secondary"] {{
            background: {theme.input_bg} !important;
            color: {theme.text} !important;
            border: 1px solid {theme.border} !important;
        }}

        /* Nasconde il marker HTML del sync tema (nessun iframe) */
        [data-ft-theme-sync] {{
            display: none !important;
        }}

        /* ---- Appearance picker (Impostazioni → Aspetto) ---- */

        .ft-appearance-hero {{
            position: relative;
            overflow: hidden;
            border-radius: 20px;
            padding: 22px 22px 20px 22px;
            border: 1px solid var(--ft-border);
            background:
                radial-gradient(
                    circle at 12% 0%,
                    rgba(var(--ft-accent-rgb), 0.28),
                    transparent 42%
                ),
                radial-gradient(
                    circle at 88% 20%,
                    rgba(var(--ft-accent-rgb), 0.12),
                    transparent 40%
                ),
                linear-gradient(
                    145deg,
                    var(--ft-bg-0),
                    var(--ft-bg-1) 55%,
                    var(--ft-bg-2)
                );
            box-shadow: var(--ft-shadow);
            animation: ft-fade-up 280ms ease-out;
        }}

        .ft-appearance-hero-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 16px;
        }}

        .ft-appearance-brand {{
            font-family: var(--ft-display) !important;
            font-size: 1.55rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            color: var(--ft-text);
            line-height: 1.1;
        }}

        .ft-appearance-brand span {{
            color: var(--ft-accent);
        }}

        .ft-appearance-chip {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(var(--ft-accent-rgb), 0.14);
            color: var(--ft-accent-strong);
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.02em;
            white-space: nowrap;
        }}

        .ft-appearance-chip-dot {{
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: var(--ft-accent);
            box-shadow: 0 0 0 3px rgba(var(--ft-accent-rgb), 0.25);
        }}

        .ft-appearance-kpis {{
            display: grid;
            grid-template-columns: 1.2fr 1fr 1fr;
            gap: 10px;
        }}

        .ft-appearance-kpi {{
            border-radius: 14px;
            padding: 12px 14px;
            background: var(--ft-panel);
            border: 1px solid var(--ft-border);
            backdrop-filter: blur(8px);
        }}

        .ft-appearance-kpi-label {{
            font-size: 11px;
            font-weight: 650;
            color: var(--ft-muted);
            margin-bottom: 6px;
        }}

        .ft-appearance-kpi-value {{
            font-family: var(--ft-display) !important;
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--ft-text);
            letter-spacing: -0.02em;
        }}

        .ft-appearance-kpi-bar {{
            margin-top: 10px;
            height: 6px;
            border-radius: 999px;
            background: rgba(var(--ft-accent-rgb), 0.14);
            overflow: hidden;
        }}

        .ft-appearance-kpi-bar > span {{
            display: block;
            height: 100%;
            width: 68%;
            border-radius: 999px;
            background: linear-gradient(
                90deg,
                var(--ft-accent),
                var(--ft-accent-strong)
            );
        }}

        .ft-theme-card {{
            border-radius: 18px;
            padding: 12px;
            border: 1px solid var(--ft-border);
            background: var(--ft-panel-soft);
            transition:
                transform 160ms ease,
                border-color 160ms ease,
                box-shadow 160ms ease;
        }}

        .ft-theme-card.is-selected {{
            border-color: rgba(var(--ft-accent-rgb), 0.55);
            box-shadow:
                0 0 0 3px rgba(var(--ft-accent-rgb), 0.16),
                var(--ft-shadow);
            transform: translateY(-1px);
        }}

        .ft-theme-card-window {{
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(148, 163, 184, 0.22);
            min-height: 108px;
        }}

        .ft-theme-card-chrome {{
            display: flex;
            gap: 5px;
            padding: 8px 10px;
            background: rgba(0, 0, 0, 0.18);
        }}

        .ft-theme-card-chrome span {{
            width: 7px;
            height: 7px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.35);
        }}

        .ft-theme-card-body {{
            display: grid;
            grid-template-columns: 34px 1fr;
            gap: 8px;
            padding: 10px;
            min-height: 72px;
        }}

        .ft-theme-card-nav {{
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.08);
        }}

        .ft-theme-card-main {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        .ft-theme-card-line {{
            height: 10px;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.12);
        }}

        .ft-theme-card-line.accent {{
            width: 42%;
            background: var(--ft-card-accent, #60a5fa);
        }}

        .ft-theme-card-meta {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 10px;
            padding: 0 2px;
        }}

        .ft-theme-card-title {{
            font-weight: 750;
            font-size: 14px;
            color: var(--ft-text);
        }}

        .ft-theme-card-hint {{
            font-size: 11px;
            font-weight: 650;
            color: var(--ft-muted);
        }}

        .ft-theme-card.is-selected .ft-theme-card-hint {{
            color: var(--ft-accent);
        }}

        .ft-accent-swatch {{
            text-align: center;
            padding: 4px 2px 2px 2px;
        }}

        .ft-accent-orb {{
            width: 52px;
            height: 52px;
            margin: 0 auto 4px auto;
            border-radius: 999px;
            background: linear-gradient(
                145deg,
                var(--ft-orb-a),
                var(--ft-orb-b)
            );
            box-shadow:
                0 10px 22px rgba(0, 0, 0, 0.18),
                inset 0 1px 0 rgba(255, 255, 255, 0.35);
            border: 3px solid transparent;
            transition:
                transform 160ms ease,
                box-shadow 160ms ease,
                border-color 160ms ease;
        }}

        .ft-accent-swatch.is-selected .ft-accent-orb {{
            transform: scale(1.06);
            border-color: var(--ft-text);
            box-shadow:
                0 0 0 3px rgba(var(--ft-accent-rgb), 0.28),
                0 12px 24px rgba(0, 0, 0, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.4);
        }}

        .ft-accent-name {{
            font-size: 12px;
            font-weight: 700;
            color: var(--ft-muted);
        }}

        .ft-accent-swatch.is-selected .ft-accent-name {{
            color: var(--ft-text);
        }}

        .ft-appearance-label {{
            font-size: 13px;
            font-weight: 750;
            color: var(--ft-text);
            margin: 4px 0 10px 0;
            letter-spacing: -0.01em;
        }}

        /* ---- Form widgets: stesso bordo chiaro per tutti ---- */
        label[data-testid="stWidgetLabel"] p,
        label[data-testid="stWidgetLabel"] span {{
            color: var(--ft-muted) !important;
        }}

        /* Contenitori Streamlit (qui sta il bordo scuro nativo) */
        [data-testid="stNumberInputContainer"],
        [data-testid="stNumberInputContainer"].focused,
        [data-testid="stTextAreaRootElement"],
        [data-testid="stTextInputRootElement"],
        .stApp [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        .stApp [data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
        .stApp div[data-baseweb="select"] > div {{
            border: 1px solid {field_border} !important;
            border-color: {field_border} !important;
            border-top-color: {field_border} !important;
            border-right-color: {field_border} !important;
            border-bottom-color: {field_border} !important;
            border-left-color: {field_border} !important;
            border-radius: 12px !important;
            background: {theme.input_bg} !important;
            background-color: {theme.input_bg} !important;
            box-shadow: none !important;
            outline: none !important;
        }}

        [data-testid="stNumberInputContainer"].focused,
        [data-testid="stTextAreaRootElement"]:focus-within,
        [data-testid="stTextInputRootElement"]:focus-within,
        [data-testid="stTextInputRootElement"]:has(input:focus),
        [data-testid="stTextAreaRootElement"]:has(textarea:focus),
        .stApp [data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within,
        .stApp div[data-baseweb="select"] > div:focus-within {{
            border: 1px solid rgba(var(--ft-accent-rgb), 0.55) !important;
            border-color: rgba(var(--ft-accent-rgb), 0.55) !important;
            border-top-color: rgba(var(--ft-accent-rgb), 0.55) !important;
            border-right-color: rgba(var(--ft-accent-rgb), 0.55) !important;
            border-bottom-color: rgba(var(--ft-accent-rgb), 0.55) !important;
            border-left-color: rgba(var(--ft-accent-rgb), 0.55) !important;
            box-shadow: none !important;
            outline: none !important;
        }}

        /* Interno campi: niente secondo bordo (solo input/textarea, non i wrapper) */
        .stApp .stTextInput input,
        .stApp .stNumberInput input,
        .stApp .stTextArea textarea,
        .stApp [data-testid="stTextInput"] input,
        .stApp [data-testid="stNumberInput"] input,
        .stApp [data-testid="stNumberInputField"],
        .stApp [data-testid="stTextArea"] textarea {{
            border: none !important;
            border-width: 0 !important;
            border-color: transparent !important;
            border-radius: 12px !important;
            font-family: var(--ft-font) !important;
            background-color: {theme.input_bg} !important;
            background: {theme.input_bg} !important;
            color: {theme.text} !important;
            caret-color: {theme.text} !important;
            box-shadow: none !important;
            outline: none !important;
        }}

        .stApp [data-testid="stNumberInput"] div[data-baseweb="input"],
        .stApp [data-testid="stNumberInput"] div[data-baseweb="base-input"],
        .stApp [data-testid="stSelectbox"] div[data-baseweb="select"] > div > div,
        .stApp [data-testid="stMultiSelect"] div[data-baseweb="select"] > div > div {{
            border: none !important;
            border-width: 0 !important;
            background-color: {theme.input_bg} !important;
            background: {theme.input_bg} !important;
            color: {theme.text} !important;
            box-shadow: none !important;
        }}

        .stApp [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        .stApp [data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
        .stApp div[data-baseweb="select"] > div {{
            min-height: 42px;
        }}

        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {{
            color: {theme.muted} !important;
            opacity: 0.85;
        }}

        .stApp [data-testid="stSelectbox"] div[data-baseweb="select"],
        .stApp [data-testid="stMultiSelect"] div[data-baseweb="select"],
        .stApp div[data-baseweb="select"] {{
            border-radius: 12px !important;
        }}

        .stApp div[data-baseweb="select"] span,
        .stApp div[data-baseweb="select"] div,
        .stApp div[data-baseweb="select"] p,
        .stApp div[data-baseweb="select"] svg,
        .stApp [data-testid="stSelectbox"] span,
        .stApp [data-testid="stSelectbox"] svg {{
            color: {theme.text} !important;
            fill: {theme.text} !important;
        }}

        /* ---- Select menu: sfondo tema, scelta solo riquadrata ---- */
        ul[role="listbox"],
        div[data-baseweb="menu"],
        div[data-baseweb="popover"] ul[role="listbox"],
        div[data-baseweb="popover"] div[data-baseweb="menu"] {{
            background: {menu_bg} !important;
            background-color: {menu_bg} !important;
            color: {theme.text} !important;
            border-color: {theme.border} !important;
        }}

        li[role="option"],
        li[role="option"] > div,
        div[data-baseweb="popover"] li[role="option"],
        div[data-baseweb="popover"] li[role="option"] > div {{
            background: {menu_bg} !important;
            background-color: {menu_bg} !important;
            background-image: none !important;
            color: {theme.text} !important;
            box-shadow: none !important;
            border: 2px solid transparent !important;
        }}

        li[role="option"][aria-selected="true"],
        li[role="option"][aria-selected="true"] > div,
        div[data-baseweb="popover"] li[role="option"][aria-selected="true"],
        div[data-baseweb="popover"] li[role="option"][aria-selected="true"] > div {{
            background: {menu_bg} !important;
            background-color: {menu_bg} !important;
            background-image: none !important;
            color: {theme.text} !important;
            border: 2px solid {accent.accent} !important;
            border-radius: 8px !important;
            box-shadow: none !important;
        }}

        li[role="option"] * {{
            color: {theme.text} !important;
        }}

        .ft-date-label {{
            color: var(--ft-muted) !important;
            font-size: 0.875rem !important;
            font-weight: 500 !important;
            margin: 0 0 0.35rem 0 !important;
            font-family: var(--ft-font) !important;
        }}

        /* Help (?): solo .stTooltipIcon (NON tutti gli stTooltipHoverTarget —
           Streamlit li usa anche sulle voci dei select per l’overflow). */
        [data-testid="stTooltipIcon"] {{
            display: inline-flex !important;
            align-items: center !important;
            vertical-align: middle !important;
            margin-left: 0.25rem !important;
            opacity: 1 !important;
        }}

        [data-testid="stTooltipIcon"] [data-testid="stTooltipHoverTarget"] {{
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            color: {theme.muted} !important;
            opacity: 1 !important;
            cursor: help !important;
        }}

        [data-testid="stTooltipIcon"] svg.icon,
        [data-testid="stTooltipIcon"] svg {{
            stroke: {theme.muted} !important;
            fill: none !important;
            color: {theme.muted} !important;
            opacity: 1 !important;
        }}

        [data-testid="stTooltipIcon"]:hover [data-testid="stTooltipHoverTarget"],
        [data-testid="stTooltipIcon"]:hover svg.icon,
        [data-testid="stTooltipIcon"]:hover svg {{
            color: {accent.accent_strong} !important;
            stroke: {accent.accent_strong} !important;
        }}

        div[role="tooltip"],
        div[data-baseweb="tooltip"],
        [data-testid="stTooltipContent"] {{
            background: {menu_bg} !important;
            background-color: {menu_bg} !important;
            color: {theme.text} !important;
            border: 1px solid {theme.border} !important;
            border-radius: 10px !important;
            box-shadow: var(--ft-shadow) !important;
            padding: 0.55rem 0.75rem !important;
        }}

        [data-testid="stTooltipContent"] *,
        [data-testid="stTooltipContent"] p,
        [data-testid="stTooltipContent"] span {{
            background: transparent !important;
            background-color: transparent !important;
            color: {theme.text} !important;
        }}

        /* Select options: testo normale (niente side-effect dei tooltip) */
        [data-testid="stSelectboxVirtualDropdown"] [data-testid="stTooltipHoverTarget"],
        ul[role="listbox"] [data-testid="stTooltipHoverTarget"],
        li[role="option"] [data-testid="stTooltipHoverTarget"] {{
            width: auto !important;
            height: auto !important;
            min-width: 0 !important;
            max-width: none !important;
            color: {theme.text} !important;
            opacity: 1 !important;
            position: static !important;
            display: block !important;
        }}

        [data-testid="stSelectboxVirtualDropdown"] [data-testid="stTooltipHoverTarget"]::after,
        ul[role="listbox"] [data-testid="stTooltipHoverTarget"]::after,
        li[role="option"] [data-testid="stTooltipHoverTarget"]::after {{
            content: none !important;
            display: none !important;
        }}

        /* File uploader */
        .stApp div[data-testid="stFileUploader"] section,
        .stApp div[data-testid="stFileUploaderDropzone"],
        .stApp [data-testid="stFileUploaderDropzone"] {{
            border-radius: 16px !important;
            border: 1px dashed rgba(var(--ft-accent-rgb), 0.35) !important;
            background: {theme.input_bg} !important;
            background-color: {theme.input_bg} !important;
            color: {theme.text} !important;
        }}

        .stApp [data-testid="stFileUploaderDropzone"] *,
        .stApp [data-testid="stFileUploaderDropzoneInstructions"] *,
        .stApp [data-testid="stFileUploader"] small,
        .stApp [data-testid="stFileUploader"] span,
        .stApp [data-testid="stFileUploader"] p {{
            color: {theme.muted} !important;
        }}

        .stApp [data-testid="stFileUploader"] button,
        .stApp [data-testid="stFileUploaderDropzone"] button,
        .stApp [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"],
        .stApp [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] > button {{
            background: {theme.panel} !important;
            background-color: {theme.input_bg} !important;
            color: {theme.text} !important;
            border: 1px solid {theme.border} !important;
            border-radius: 12px !important;
            box-shadow: none !important;
        }}

        .stApp [data-testid="stFileUploader"] button:hover,
        .stApp [data-testid="stFileUploaderDropzone"] button:hover {{
            border-color: rgba(var(--ft-accent-rgb), 0.45) !important;
            background: rgba(var(--ft-accent-rgb), 0.08) !important;
        }}

        /* Alert / info / warning / toast */
        [data-testid="stAlert"],
        [data-testid="stAlert"] > div,
        [data-testid="stNotification"],
        [data-testid="stToast"],
        [data-testid="stToast"] > div,
        div[data-testid="toastContainer"] [data-testid="stToast"] {{
            border-radius: 14px !important;
            border: 1px solid var(--ft-border) !important;
            background: {theme.panel} !important;
            background-color: {theme.input_bg} !important;
            color: {theme.text} !important;
            box-shadow: var(--ft-shadow) !important;
        }}

        [data-testid="stAlert"] p,
        [data-testid="stAlert"] span,
        [data-testid="stAlert"] div,
        [data-testid="stToast"] p,
        [data-testid="stToast"] span,
        [data-testid="stToast"] div,
        [data-testid="stNotification"] p,
        [data-testid="stNotification"] span {{
            color: {theme.text} !important;
        }}

        /* Tabs */
        button[data-baseweb="tab"] {{
            color: var(--ft-muted) !important;
        }}

        button[data-baseweb="tab"][aria-selected="true"] {{
            color: var(--ft-text) !important;
        }}

        div[data-baseweb="tab-highlight"] {{
            background-color: var(--ft-accent) !important;
            background: var(--ft-accent) !important;
            height: 3px !important;
            border-radius: 999px !important;
        }}

        div[data-baseweb="tab-border"] {{
            background-color: var(--ft-border) !important;
            background: var(--ft-border) !important;
        }}

        /* Expander: contenitore chiaro, senza forzare ogni span (rompe i label) */
        div[data-testid="stExpander"],
        div[data-testid="stExpander"] details,
        div[data-testid="stExpander"] > details > summary,
        [data-testid="stExpanderDetails"],
        .streamlit-expanderContent,
        .streamlit-expanderHeader {{
            background: {theme.input_bg} !important;
            background-color: {theme.input_bg} !important;
            border-color: {theme.border} !important;
        }}

        div[data-testid="stExpander"] {{
            border-radius: 14px !important;
            border: 1px solid {theme.border} !important;
            overflow: hidden;
        }}

        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary p,
        div[data-testid="stExpander"] summary span {{
            color: {theme.text} !important;
        }}

        div[data-testid="stExpander"] summary svg {{
            fill: {theme.text} !important;
            color: {theme.text} !important;
        }}

        /* Card dashboard generica (spese speciali, empty states, …) */
        .ft-dashboard-card {{
            background:
                radial-gradient(
                    circle at 12% 0%,
                    rgba(var(--ft-accent-rgb), 0.12),
                    transparent 42%
                ),
                var(--ft-panel) !important;
            border: 1px solid var(--ft-border) !important;
            border-radius: var(--ft-radius) !important;
            box-shadow: var(--ft-shadow) !important;
            padding: 18px 16px 20px 16px !important;
            margin-bottom: 4px !important;
            animation: ft-fade-up 300ms ease-out;
        }}

        .ft-specials-details {{
            background: transparent !important;
        }}

        .ft-specials-summary {{
            list-style: none !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            gap: 0.55rem !important;
            padding: 0.1rem 0.05rem !important;
            color: var(--ft-text) !important;
            font-size: 0.98rem !important;
            font-weight: 650 !important;
            user-select: none !important;
        }}

        .ft-specials-summary::-webkit-details-marker {{
            display: none !important;
        }}

        .ft-specials-summary::before {{
            content: "▸" !important;
            color: var(--ft-muted) !important;
            font-size: 0.85rem !important;
            line-height: 1 !important;
        }}

        .ft-specials-details[open] > .ft-specials-summary::before {{
            content: "▾" !important;
        }}

        .ft-specials-summary-label {{
            color: var(--ft-text) !important;
        }}

        .ft-specials-hint {{
            margin: 0.65rem 0 0.25rem 0 !important;
            font-size: 0.84rem !important;
            line-height: 1.45 !important;
            color: var(--ft-muted) !important;
        }}

        /* Checkbox / radio: solo colore testo (niente override di layout) */
        .stRadio label,
        .stCheckbox label,
        [data-testid="stCheckbox"] label {{
            color: {theme.text} !important;
        }}

        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p {{
            color: {theme.muted} !important;
        }}

        /* Number input: solo il campo; label fuori; niente stepper */
        [data-testid="stNumberInput"] {{
            background: transparent !important;
            background-color: transparent !important;
        }}

        [data-testid="stNumberInput"] label[data-testid="stWidgetLabel"],
        [data-testid="stNumberInput"] label[data-testid="stWidgetLabel"] p,
        [data-testid="stNumberInput"] label[data-testid="stWidgetLabel"] span {{
            background: transparent !important;
            color: var(--ft-muted) !important;
        }}

        [data-testid="stNumberInput"] button,
        .stNumberInput button,
        [data-testid="stNumberInput"] [data-baseweb="button"],
        [data-testid="stNumberInput"] [class*="stepper"] button,
        [data-testid="stNumberInput"] [class*="Stepper"] button {{
            display: none !important;
        }}

        /* Divider / hr */
        hr,
        [data-testid="stDivider"] {{
            border: none !important;
            border-top: 1px solid {theme.border} !important;
            background: transparent !important;
            height: 0 !important;
        }}

        /* Code / path blocks */
        [data-testid="stCode"],
        [data-testid="stCode"] pre,
        [data-testid="stCode"] code {{
            background: rgba(var(--ft-accent-rgb), 0.06) !important;
            color: var(--ft-text) !important;
            border: 1px solid var(--ft-border) !important;
            border-radius: 12px !important;
            user-select: text !important;
        }}

        /* La toolbar globale è nascosta (fullscreen immagini).
           Su st.code serve il pulsante Copia. */
        [data-testid="stCode"] [data-testid="stElementToolbar"],
        [data-testid="stCode"] [data-testid="stElementToolbarButton"],
        [data-testid="stCode"] [data-testid="stElementToolbarButtonContainer"] {{
            display: flex !important;
            visibility: visible !important;
            pointer-events: auto !important;
            opacity: 1 !important;
        }}

        .ft-copy-path {{
            display: flex;
            align-items: stretch;
            gap: 8px;
            margin: 10px 0 8px 0;
        }}

        .ft-copy-path-value {{
            flex: 1;
            min-width: 0;
            margin: 0;
            padding: 10px 12px;
            border-radius: 12px;
            border: 1px solid var(--ft-border);
            background: rgba(var(--ft-accent-rgb), 0.06);
            color: var(--ft-text);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 12px;
            line-height: 1.45;
            word-break: break-all;
            user-select: text;
            -webkit-user-select: text;
        }}

        .ft-copy-path-btn {{
            flex-shrink: 0;
            align-self: center;
            min-height: 38px;
            padding: 0 14px;
            border-radius: 12px;
            border: 1px solid var(--ft-border);
            background: var(--ft-panel);
            color: var(--ft-text);
            font-family: var(--ft-font);
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
        }}

        .ft-copy-path-btn:hover {{
            border-color: rgba(var(--ft-accent-rgb), 0.45);
            color: var(--ft-accent-strong);
        }}

        .ft-copy-path-btn.is-copied {{
            border-color: rgba(var(--ft-accent-rgb), 0.45);
            color: var(--ft-accent-strong);
        }}

        /* Icone Streamlit (uploader / material) */
        [data-testid="stIconMaterial"],
        [data-testid="stIconEmoji"],
        [data-testid="stFileUploader"] svg,
        [data-testid="stFileUploaderDropzone"] svg {{
            color: {theme.text} !important;
            fill: {theme.text} !important;
        }}

        /* Evita “blocchi neri” residui nei controlli */
        .stApp [class*="st-"] input,
        .stApp [class*="st-"] textarea {{
            background-color: {theme.input_bg} !important;
            color: {theme.text} !important;
        }}

        .ft-section-title {{
            font-family: var(--ft-display) !important;
            font-size: 1.35rem;
            font-weight: 700;
            color: var(--ft-text);
            margin: 1.1rem 0 0.55rem 0;
            letter-spacing: -0.02em;
        }}

        /* Card pannello: distribuzione + grafici dashboard */
        [data-testid="stVerticalBlockBorderWrapper"]:has(.ft-distribution-anchor),
        [data-testid="stVerticalBlockBorderWrapper"]:has(.ft-chart-card-anchor),
        [data-testid="stVerticalBlockBorderWrapper"]:has(.ft-panel-anchor),
        [data-testid="stVerticalBlockBorderWrapper"]:has(.ft-movement-anchor),
        div[class*="st-key-ft_dashboard_chart_card"],
        div[class*="st-key-ft_dashboard_distribution_card"],
        div[class*="st-key-ft_dashboard_expense_distribution"],
        div[class*="st-key-ft_dashboard_income_distribution"],
        div[class*="st-key-ft_dashboard_chart_card"]
            [data-testid="stVerticalBlockBorderWrapper"],
        div[class*="st-key-ft_dashboard_distribution_card"]
            [data-testid="stVerticalBlockBorderWrapper"],
        div[class*="st-key-ft_dashboard_expense_distribution"]
            [data-testid="stVerticalBlockBorderWrapper"],
        div[class*="st-key-ft_dashboard_income_distribution"]
            [data-testid="stVerticalBlockBorderWrapper"] {{
            background:
                radial-gradient(
                    circle at 12% 0%,
                    rgba(var(--ft-accent-rgb), 0.12),
                    transparent 42%
                ),
                var(--ft-panel) !important;
            background-color: var(--ft-panel) !important;
            border: 1px solid var(--ft-border) !important;
            border-radius: var(--ft-radius) !important;
            box-shadow: var(--ft-shadow) !important;
            padding: 18px 16px 20px 16px !important;
            margin-bottom: 4px;
            animation: ft-fade-up 300ms ease-out;
        }}

        div[class*="st-key-ft_dashboard_chart_card"] > div,
        div[class*="st-key-ft_dashboard_distribution_card"] > div,
        div[class*="st-key-ft_dashboard_expense_distribution"] > div,
        div[class*="st-key-ft_dashboard_income_distribution"] > div,
        [data-testid="stVerticalBlockBorderWrapper"]:has(.ft-chart-card-anchor) > div,
        [data-testid="stVerticalBlockBorderWrapper"]:has(.ft-distribution-anchor) > div {{
            background: transparent !important;
            background-color: transparent !important;
        }}

        div[class*="st-key-ft_dashboard_chart_card"] [data-testid="stPlotlyChart"],
        div[class*="st-key-ft_dashboard_chart_card"] .stPlotlyChart,
        div[class*="st-key-ft_dashboard_chart_card"] .js-plotly-plot,
        div[class*="st-key-ft_dashboard_chart_card"] .plot-container,
        [data-testid="stVerticalBlockBorderWrapper"]:has(.ft-chart-card-anchor)
            [data-testid="stPlotlyChart"],
        [data-testid="stVerticalBlockBorderWrapper"]:has(.ft-chart-card-anchor)
            .stPlotlyChart,
        [data-testid="stVerticalBlockBorderWrapper"]:has(.ft-chart-card-anchor)
            .js-plotly-plot,
        [data-testid="stVerticalBlockBorderWrapper"]:has(.ft-distribution-anchor)
            iframe {{
            background: transparent !important;
            background-color: transparent !important;
        }}

        [data-testid="stVerticalBlockBorderWrapper"]:has(.ft-movement-anchor) {{
            padding: 14px 14px 12px 14px !important;
            margin-bottom: 10px;
            background:
                radial-gradient(
                    circle at 8% 0%,
                    rgba(var(--ft-accent-rgb), 0.08),
                    transparent 40%
                ),
                var(--ft-panel) !important;
        }}

        [data-testid="stVerticalBlockBorderWrapper"]:has(.ft-distribution-anchor)
        [data-testid="stHorizontalBlock"]
        > div[data-testid="stColumn"]:first-child,
        div[class*="st-key-ft_dashboard_distribution_card"]
        [data-testid="stHorizontalBlock"]
        > div[data-testid="stColumn"]:first-child,
        div[class*="st-key-ft_dashboard_expense_distribution"]
        [data-testid="stHorizontalBlock"]
        > div[data-testid="stColumn"]:first-child,
        div[class*="st-key-ft_dashboard_income_distribution"]
        [data-testid="stHorizontalBlock"]
        > div[data-testid="stColumn"]:first-child {{
            border-right: 1px solid var(--ft-border);
            padding-right: 12px;
        }}

        [data-testid="stVerticalBlockBorderWrapper"]:has(.ft-distribution-anchor)
        [data-testid="stHorizontalBlock"]
        > div[data-testid="stColumn"]:last-child,
        div[class*="st-key-ft_dashboard_distribution_card"]
        [data-testid="stHorizontalBlock"]
        > div[data-testid="stColumn"]:last-child,
        div[class*="st-key-ft_dashboard_expense_distribution"]
        [data-testid="stHorizontalBlock"]
        > div[data-testid="stColumn"]:last-child,
        div[class*="st-key-ft_dashboard_income_distribution"]
        [data-testid="stHorizontalBlock"]
        > div[data-testid="stColumn"]:last-child {{
            padding-left: 8px;
        }}

        .ft-category-scroll {{
            scrollbar-width: thin;
            scrollbar-color: var(--ft-scrollbar) transparent;
        }}

        .ft-category-scroll::-webkit-scrollbar {{
            width: 6px;
        }}

        .ft-category-scroll::-webkit-scrollbar-thumb {{
            background: var(--ft-scrollbar);
            border-radius: 8px;
        }}

        .ft-movement-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            padding: 12px 4px;
            border-bottom: 1px solid var(--ft-border);
        }}

        .ft-movement-row:last-child {{
            border-bottom: none;
        }}

        .ft-brand-finance {{
            color: var(--ft-text);
        }}

        .ft-brand-tracker {{
            color: var(--ft-accent-strong);
        }}

        .ft-brand-subtitle {{
            color: var(--ft-muted);
        }}

        .ft-version-chip {{
            background: rgba(var(--ft-accent-rgb), 0.14);
            color: var(--ft-accent-strong);
            font-weight: 750;
        }}

        ::-webkit-scrollbar {{
            width: 8px;
        }}

        ::-webkit-scrollbar-thumb {{
            background: var(--ft-scrollbar);
            border-radius: 8px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
