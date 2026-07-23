from pathlib import Path

import streamlit as st

from src.components.navigation import NavItem, register_pages, render_app_shell
from src.database.db import init_db
from src.pages.dashboard import show_dashboard
from src.pages.import_data import show_import_data
from src.pages.manual_entry import show_manual_entry
from src.pages.movements import show_movements
from src.pages.settings import show_settings
from src.theme.style import apply_theme
from src.utils.version import get_app_version


APP_VERSION = get_app_version()

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

NAV_ITEMS = [
    NavItem(dashboard_page, "Dashboard", "🏠"),
    NavItem(movements_page, "Movimenti", "💳"),
    NavItem(manual_entry_page, "Nuovo movimento", "➕"),
    NavItem(import_page, "Importa dati", "📥"),
    NavItem(settings_page, "Impostazioni", "⚙️"),
]

register_pages(
    dashboard=dashboard_page,
    movements=movements_page,
    manual_entry=manual_entry_page,
    import_data=import_page,
    settings=settings_page,
)

navigation = st.navigation(
    [item.page for item in NAV_ITEMS],
    position="hidden",
)

render_app_shell(
    navigation,
    NAV_ITEMS,
    logo_path=LOGO_PATH,
    app_version=APP_VERSION,
)
