from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st

from src.utils.version import get_app_version


NAVIGATION_OPEN_KEY = "navigation_open"


@dataclass(frozen=True)
class NavItem:
    page: Any
    label: str
    icon: str


def ensure_navigation_state(*, default_open: bool = True) -> None:
    if NAVIGATION_OPEN_KEY not in st.session_state:
        st.session_state[NAVIGATION_OPEN_KEY] = default_open


def open_navigation() -> None:
    st.session_state[NAVIGATION_OPEN_KEY] = True


def close_navigation() -> None:
    st.session_state[NAVIGATION_OPEN_KEY] = False


def is_navigation_open() -> bool:
    return bool(st.session_state.get(NAVIGATION_OPEN_KEY, True))


def render_brand(logo_path: Path, app_version: str | None = None) -> None:
    version = app_version or get_app_version()

    top_left, top_right = st.columns([5, 1])

    with top_right:
        st.button(
            "☰",
            key="close_navigation",
            help="Nascondi menu",
            on_click=close_navigation,
        )

    if logo_path.exists():
        logo_left, logo_center, logo_right = st.columns([1, 8, 1])

        with logo_center:
            st.image(str(logo_path), width=450)

    st.markdown(
        """
        <h1 style="
            text-align:center;
            margin-top:-4px;
            margin-bottom:0;
            font-family:Fraunces,Georgia,serif;
            font-size:32px;
            font-weight:700;
            letter-spacing:-0.03em;
        ">
            <span style="color:#ffffff;">Finance</span><span style="color:#80e848;">Tracker</span>
        </h1>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="
            text-align:center;
            color:#94a3b8;
            margin-top:2px;
            margin-bottom:12px;
            font-size:13px;
            font-weight:500;
            letter-spacing:0.04em;
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
                padding:3px 10px;
                border-radius:8px;
                background:rgba(96,165,250,.12);
                color:#60a5fa;
                font-weight:700;
                font-size:11px;
                letter-spacing:0.04em;
            ">
                {version}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
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


def render_app_shell(
    navigation: Any,
    items: list[NavItem],
    *,
    logo_path: Path,
    app_version: str | None = None,
) -> None:
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
            help="Mostra menu",
            width="stretch",
            type="primary",
            on_click=open_navigation,
        )

    with content_column:
        navigation.run()
