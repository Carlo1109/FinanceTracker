from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st

from src.utils.platform import IS_ANDROID
from src.utils.version import get_app_version


NAVIGATION_OPEN_KEY = "navigation_open"

_PAGES: dict[str, Any] = {}


@dataclass(frozen=True)
class NavItem:
    page: Any
    label: str
    icon: str


def register_pages(**pages: Any) -> None:
    """Registra gli oggetti st.Page per st.switch_page da altri moduli."""
    _PAGES.update(pages)


def switch_to(page_key: str) -> None:
    page = _PAGES.get(page_key)
    if page is None:
        raise KeyError(f"Pagina non registrata: {page_key}")
    st.switch_page(page)


def ensure_navigation_state(*, default_open: bool = True) -> None:
    if NAVIGATION_OPEN_KEY not in st.session_state:
        st.session_state[NAVIGATION_OPEN_KEY] = default_open


def open_navigation() -> None:
    st.session_state[NAVIGATION_OPEN_KEY] = True


def close_navigation() -> None:
    st.session_state[NAVIGATION_OPEN_KEY] = False


def is_navigation_open() -> bool:
    return bool(st.session_state.get(NAVIGATION_OPEN_KEY, True))


def _square_logo(logo_path: Path) -> Path:
    """Versione quadrata del logo (quella originale è rettangolare)."""
    square = logo_path.with_name("ft_logo_square.png")
    return square if square.exists() else logo_path


@st.cache_data(show_spinner=False)
def _logo_data_uri(logo_path: str, mtime: float) -> str:
    import base64

    data = Path(logo_path).read_bytes()
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


def render_brand(logo_path: Path, app_version: str | None = None) -> None:
    version = app_version or get_app_version()

    brand_col, toggle_col = st.columns([5, 1], vertical_alignment="center")
    with brand_col:
        logo_html = ""
        square = _square_logo(logo_path)
        if square.exists():
            uri = _logo_data_uri(str(square), square.stat().st_mtime)
            logo_html = f'<img src="{uri}" alt="" />'
        st.html(
            f"""
            <div class="ft-nav-brand">
              {logo_html}
              <div>
                <div class="ft-nav-brand-name">
                  <span class="ft-brand-finance">Finance</span><span class="ft-brand-tracker">Tracker</span>
                </div>
                <div class="ft-nav-brand-sub">
                  <span class="ft-version-chip">{version}</span>
                </div>
              </div>
            </div>
            """
        )
    with toggle_col:
        st.button(
            "☰",
            key="close_navigation",
            on_click=close_navigation,
            help="Nascondi il menu",
        )


def render_navigation(
    items: list[NavItem],
    *,
    logo_path: Path,
    app_version: str | None = None,
) -> None:
    st.markdown(
        '<div class="ft-navigation-anchor"></div>',
        unsafe_allow_html=True,
    )

    render_brand(logo_path, app_version)
    st.divider()

    for item in items:
        st.page_link(item.page, label=item.label, icon=item.icon)


MOBILE_TAB_LABELS = {
    "Dashboard": "Home",
    "Movimenti": "Movimenti",
    "Nuovo movimento": "Nuovo",
    "Report": "Report",
    "Importa dati": "Importa",
    "Impostazioni": "Opzioni",
}


def render_mobile_shell(
    navigation: Any,
    items: list[NavItem],
    *,
    logo_path: Path,
    app_version: str | None = None,
) -> None:
    """
    Guscio per smartphone (app Android): barra superiore compatta
    e barra di navigazione fissa in basso, come un'app nativa.
    Il contenuto delle pagine è lo stesso della versione desktop.
    """
    version = app_version or get_app_version()

    logo_html = ""
    square = _square_logo(logo_path)
    if square.exists():
        uri = _logo_data_uri(str(square), square.stat().st_mtime)
        logo_html = f'<img class="ft-mtop-logo" src="{uri}" alt="" />'

    st.html(
        f"""
        <div class="ft-mtop">
          {logo_html}
          <div class="ft-mtop-title">
            <span class="ft-brand-finance">Finance</span><span class="ft-brand-tracker">Tracker</span>
          </div>
          <span class="ft-version-chip ft-mtop-version">{version}</span>
        </div>
        """
    )

    navigation.run()

    current_path = getattr(navigation, "url_path", None)

    with st.container(key="ft_mobile_tabbar", horizontal=True):
        for index, item in enumerate(items):
            is_current = getattr(item.page, "url_path", None) == current_path
            state = "on" if is_current else "off"

            with st.container(key=f"ft_mtab_{index}_{state}"):
                st.page_link(
                    item.page,
                    label=MOBILE_TAB_LABELS.get(item.label, item.label),
                    icon=item.icon,
                )


def render_app_shell(
    navigation: Any,
    items: list[NavItem],
    *,
    logo_path: Path,
    app_version: str | None = None,
) -> None:
    if IS_ANDROID:
        render_mobile_shell(
            navigation,
            items,
            logo_path=logo_path,
            app_version=app_version,
        )
        return

    ensure_navigation_state()

    if is_navigation_open():
        navigation_column, content_column = st.columns(
            [1.15, 4.85],
            gap="small",
        )

        with navigation_column:
            with st.container(border=True):
                render_navigation(
                    items,
                    logo_path=logo_path,
                    app_version=app_version,
                )

        with content_column:
            navigation.run()
        return

    menu_column, content_column = st.columns(
        [0.42, 5.58],
        gap="small",
    )

    with menu_column:
        st.button(
            "☰",
            key="open_navigation",
            width="stretch",
            type="primary",
            on_click=open_navigation,
        )

    with content_column:
        navigation.run()
