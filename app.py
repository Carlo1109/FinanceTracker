from pathlib import Path

import streamlit as st

from src.components.navigation import NavItem, register_pages, render_app_shell
from src.database.db import ensure_db
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

ensure_db()
apply_theme()


# Le pagine si importano solo quando vengono aperte: all'avvio (soprattutto
# sul telefono, dove Python gira in WebAssembly) si carica solo la Dashboard
# e non import delle banche, export Excel, impostazioni, …
def _dashboard() -> None:
    from src.pages.dashboard import show_dashboard

    show_dashboard()


def _movements() -> None:
    from src.pages.movements import show_movements

    show_movements()


def _manual_entry() -> None:
    from src.pages.manual_entry import show_manual_entry

    show_manual_entry()


def _reports() -> None:
    from src.pages.reports import show_reports

    show_reports()


def _import_data() -> None:
    from src.pages.import_data import show_import_data

    show_import_data()


def _settings() -> None:
    from src.pages.settings import show_settings

    show_settings()


dashboard_page = st.Page(
    _dashboard,
    title="Dashboard",
    icon="🏠",
    url_path="dashboard",
    default=True,
)

movements_page = st.Page(
    _movements,
    title="Movimenti",
    icon="💳",
    url_path="movimenti",
)

manual_entry_page = st.Page(
    _manual_entry,
    title="Nuovo movimento",
    icon="➕",
    url_path="nuovo-movimento",
)

reports_page = st.Page(
    _reports,
    title="Report",
    icon="📊",
    url_path="report",
)

import_page = st.Page(
    _import_data,
    title="Importa dati",
    icon="📥",
    url_path="importa-dati",
)

settings_page = st.Page(
    _settings,
    title="Impostazioni",
    icon="⚙️",
    url_path="impostazioni",
)

NAV_ITEMS = [
    NavItem(dashboard_page, "Dashboard", "🏠"),
    NavItem(movements_page, "Movimenti", "💳"),
    NavItem(manual_entry_page, "Nuovo movimento", "➕"),
    NavItem(reports_page, "Report", "📊"),
    NavItem(import_page, "Importa dati", "📥"),
    NavItem(settings_page, "Impostazioni", "⚙️"),
]

register_pages(
    dashboard=dashboard_page,
    movements=movements_page,
    manual_entry=manual_entry_page,
    reports=reports_page,
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
