from pathlib import Path

import streamlit as st

from src.database.db import init_db
from src.pages.dashboard import show_dashboard
from src.pages.import_data import show_import_data
from src.pages.manual_entry import show_manual_entry
from src.pages.movements import show_movements
from src.pages.settings import show_settings
from src.theme.style import apply_theme


APP_VERSION = "v1.0.0"

PROJECT_ROOT = Path(__file__).resolve().parent
LOGO_PATH = PROJECT_ROOT / "assets" / "icons" / "logo.png"


st.set_page_config(
    page_title="FinanceTracker",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_theme()
init_db()


PAGES = {
    "Dashboard": {
        "label": "🏠 Dashboard",
        "render": show_dashboard,
    },
    "Movimenti": {
        "label": "💳 Movimenti",
        "render": show_movements,
    },
    "Nuovo movimento": {
        "label": "➕ Nuovo movimento",
        "render": show_manual_entry,
    },
    "Importa dati": {
        "label": "📥 Importa dati",
        "render": show_import_data,
    },
    "Impostazioni": {
        "label": "⚙️ Impostazioni",
        "render": show_settings,
    },
}


if "page" not in st.session_state:
    st.session_state["page"] = "Dashboard"

if "navigation_open" not in st.session_state:
    st.session_state["navigation_open"] = True


def open_navigation() -> None:
    st.session_state["navigation_open"] = True


def close_navigation() -> None:
    st.session_state["navigation_open"] = False


def change_page(page_name: str) -> None:
    st.session_state["page"] = page_name


def render_brand() -> None:
    top_left, top_right = st.columns([5, 1])

    with top_right:
        st.button(
            "☰",
            key="close_navigation",
            help="Nascondi menu",
            on_click=close_navigation,
        )

    if LOGO_PATH.exists():
        logo_left, logo_center, logo_right = st.columns([1, 8, 1])

        with logo_center:
            st.image(
                str(LOGO_PATH),
                width=450,
            )
    else:
        st.markdown("## FT")

    st.markdown(
        """
        <h1 style="
            text-align:center;
            margin-top:-8px;
            margin-bottom:0;
            font-size:34px;
            font-weight:900;
            letter-spacing:-1px;
        ">
            <span style="color:#f8fafc;">Finance</span><span style="color:#22c55e;">Tracker</span>
        </h1>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="
            text-align:center;
            color:#94a3b8;
            margin-top:4px;
            margin-bottom:10px;
            font-size:14px;
        ">
            Personal finance
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="text-align:center;">
            <span style="
                display:inline-block;
                padding:4px 12px;
                border-radius:999px;
                background:rgba(34,197,94,.15);
                color:#22c55e;
                font-weight:700;
                font-size:12px;
            ">
                {APP_VERSION}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_navigation() -> None:
    st.markdown(
        '<div class="ft-navigation-anchor"></div>',
        unsafe_allow_html=True,
    )

    render_brand()

    st.divider()

    for page_name, page_config in PAGES.items():
        is_selected = st.session_state["page"] == page_name

        st.button(
            page_config["label"],
            key=f"navigation_{page_name}",
            use_container_width=True,
            type="primary" if is_selected else "secondary",
            on_click=change_page,
            args=(page_name,),
        )

def render_current_page() -> None:
    current_page = st.session_state["page"]

    if current_page not in PAGES:
        current_page = "Dashboard"
        st.session_state["page"] = current_page

    PAGES[current_page]["render"]()


if st.session_state["navigation_open"]:
    navigation_column, content_column = st.columns(
    [1.15, 4.85],
    gap="small",
    )

    with navigation_column:
        with st.container(border=True):
            render_navigation()

    with content_column:
        render_current_page()

else:
    menu_column, spacer_column = st.columns([1, 8])

    with menu_column:
        st.button(
            "☰ Menu",
            key="open_navigation",
            use_container_width=True,
            type="primary",
            on_click=open_navigation,
        )

    render_current_page()