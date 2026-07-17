from pathlib import Path

import streamlit as st

from src.database.db import init_db
from src.pages.dashboard import show_dashboard
from src.pages.import_data import show_import_data
from src.pages.manual_entry import show_manual_entry
from src.pages.movements import show_movements
from src.pages.settings import show_settings
from src.theme.style import apply_theme


APP_VERSION = "v1.0.1"

PROJECT_ROOT = Path(__file__).resolve().parent
LOGO_PATH = PROJECT_ROOT / "assets" / "icons" / "ft_logo.png"


st.set_page_config(
    page_title="FinanceTracker",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_theme()
init_db()


dashboard_page = st.Page(
    show_dashboard,
    title="Dashboard",
    icon="🏠",
    url_path="dashboard",
    default=True,
)

movements_page = st.Page(
    show_movements,
    title="Movimenti",
    icon="💳",
    url_path="movimenti",
)

manual_entry_page = st.Page(
    show_manual_entry,
    title="Nuovo movimento",
    icon="➕",
    url_path="nuovo-movimento",
)

import_page = st.Page(
    show_import_data,
    title="Importa dati",
    icon="📥",
    url_path="importa-dati",
)

settings_page = st.Page(
    show_settings,
    title="Impostazioni",
    icon="⚙️",
    url_path="impostazioni",
)


navigation = st.navigation(
    [
        dashboard_page,
        movements_page,
        manual_entry_page,
        import_page,
        settings_page,
    ],
    position="hidden",
)


if "navigation_open" not in st.session_state:
    st.session_state["navigation_open"] = True


def open_navigation() -> None:
    st.session_state["navigation_open"] = True


def close_navigation() -> None:
    st.session_state["navigation_open"] = False


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
            st.image(str(LOGO_PATH), width=450)


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
            Personal Finance Manager
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

    st.page_link(dashboard_page, label="Dashboard", icon="🏠")
    st.page_link(movements_page, label="Movimenti", icon="💳")
    st.page_link(
        manual_entry_page,
        label="Nuovo movimento",
        icon="➕",
    )
    st.page_link(import_page, label="Importa dati", icon="📥")
    st.page_link(settings_page, label="Impostazioni", icon="⚙️")


if st.session_state["navigation_open"]:
    navigation_column, content_column = st.columns(
        [1.15, 4.85],
        gap="small",
    )

    with navigation_column:
        with st.container(border=True):
            render_navigation()

    with content_column:
        navigation.run()

else:
    menu_column, content_column = st.columns(
        [0.42, 5.58],
        gap="small",
    )

    with menu_column:
        st.button(
            "☰",
            key="open_navigation",
            help="Mostra menu",
            use_container_width=True,
            type="primary",
            on_click=open_navigation,
        )

    with content_column:
        navigation.run()