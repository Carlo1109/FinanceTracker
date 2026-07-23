import html
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

import streamlit as st


INCOME_COLOR = "#34d399"
EXPENSE_COLOR = "#f87171"
INVESTMENT_COLOR = "#fbbf24"
LIQUIDITY_COLOR = "#34d399"
BALANCE_COLOR = "#34d399"
TEXT_COLOR = "#eef3ff"
MUTED_COLOR = "#94a3b8"

CARD_RADIUS = "18px"
CARD_BORDER = "1px solid rgba(148,163,184,.16)"
CARD_SHADOW = "0 16px 36px rgba(0,0,0,.28)"
CARD_BACKGROUND = "rgba(11,18,32,.90)"


def compact_html(value: str) -> str:
    """
    Compatta l'HTML su una singola riga.

    Streamlit può interpretare righe HTML indentate come blocchi Markdown
    di codice. La compattazione evita questo comportamento.
    """
    return " ".join(line.strip() for line in value.splitlines() if line.strip())


def render_html(value: str) -> None:
    st.markdown(compact_html(value), unsafe_allow_html=True)


def render_hero_card(
    title: str,
    main_value: str,
    main_color: str,
    subtitle: str | None = None,
    subtitle_color: str = MUTED_COLOR,
) -> None:
    subtitle_html = ""
    if subtitle:
        subtitle_html = f"""
            <div style="
                margin-top:12px;
                font-family:Manrope,sans-serif;
                font-size:14px;
                font-weight:650;
                color:{subtitle_color};
            ">
                {html.escape(subtitle)}
            </div>
        """

    render_html(
        f"""
        <div style="
            margin-top:8px;
            min-height:200px;
            padding:36px 40px;
            border-radius:{CARD_RADIUS};
            background:
                radial-gradient(
                    circle at 18% 0%,
                    rgba(96,165,250,0.22),
                    transparent 42%
                ),
                {CARD_BACKGROUND};
            border:{CARD_BORDER};
            box-shadow:{CARD_SHADOW};
            display:flex;
            flex-direction:column;
            align-items:flex-start;
            justify-content:center;
            text-align:left;
            box-sizing:border-box;
            animation: ft-fade-up 280ms ease-out;
        ">
            <div style="
                font-family:Manrope,sans-serif;
                font-size:13px;
                color:{MUTED_COLOR};
                font-weight:650;
                letter-spacing:0.12em;
                text-transform:uppercase;
            ">
                {html.escape(title)}
            </div>

            <div style="
                margin-top:10px;
                font-family:Fraunces,Georgia,serif;
                font-size:clamp(46px,5vw,64px);
                line-height:1.02;
                font-weight:700;
                color:{main_color};
                white-space:normal;
                overflow-wrap:anywhere;
            ">
                {html.escape(main_value)}
            </div>
            {subtitle_html}
        </div>
        """
    )


def render_kpi_card(
    title: str,
    value: str,
    icon: str = "",
    value_color: str = TEXT_COLOR,
    subtitle: str | None = None,
    subtitle_color: str = MUTED_COLOR,
) -> None:
    icon_html = ""

    if icon:
        icon_html = f"{html.escape(icon)} "

    subtitle_html = ""
    if subtitle:
        subtitle_html = f"""
            <div style="
                margin-top:8px;
                font-size:12px;
                line-height:1.3;
                font-weight:650;
                color:{subtitle_color};
            ">
                {html.escape(subtitle)}
            </div>
        """

    render_html(
        f"""
        <div style="
            min-height:132px;
            padding:18px 18px;
            border-radius:{CARD_RADIUS};
            background:{CARD_BACKGROUND};
            border:{CARD_BORDER};
            box-shadow:{CARD_SHADOW};
            display:flex;
            flex-direction:column;
            justify-content:center;
            align-items:flex-start;
            text-align:left;
            box-sizing:border-box;
            animation: ft-fade-up 300ms ease-out;
        ">
            <div style="
                font-family:Manrope,sans-serif;
                font-size:12px;
                color:{MUTED_COLOR};
                font-weight:650;
                letter-spacing:0.08em;
                text-transform:uppercase;
            ">
                {icon_html}{html.escape(title)}
            </div>

            <div style="
                margin-top:10px;
                font-family:Fraunces,Georgia,serif;
                font-size:clamp(26px,2vw,34px);
                line-height:1.1;
                font-weight:700;
                color:{value_color};
                white-space:normal;
                overflow-wrap:anywhere;
                word-break:break-word;
            ">
                {html.escape(value)}
            </div>
            {subtitle_html}
        </div>
        """
    )


def render_info_card(
    title: str,
    value: str,
    secondary_value: str | None = None,
    subtitle: str | None = None,
    subtitle_color: str = MUTED_COLOR,
    footer: str | None = None,
    value_color: str = TEXT_COLOR,
) -> None:
    secondary_value_html = ""

    if secondary_value:
        secondary_value_html = f"""
            <div style="
                margin-top:12px;
                font-family:Fraunces,Georgia,serif;
                font-size:clamp(22px,1.8vw,30px);
                line-height:1.15;
                font-weight:700;
                color:#dbeafe;
                overflow-wrap:anywhere;
                word-break:break-word;
            ">
                {html.escape(str(secondary_value))}
            </div>
        """

    subtitle_html = ""

    if subtitle:
        subtitle_html = f"""
            <div style="
                margin-top:8px;
                font-size:13px;
                line-height:1.3;
                font-weight:650;
                color:{subtitle_color};
                text-align:left;
            ">
                {html.escape(str(subtitle))}
            </div>
        """

    footer_html = ""

    if footer:
        footer_html = f"""
            <div style="
                margin-top:6px;
                font-size:12px;
                line-height:1.25;
                font-weight:550;
                color:#64748b;
                text-align:left;
            ">
                {html.escape(str(footer))}
            </div>
        """

    render_html(
        f"""
        <div style="
            min-height:168px;
            padding:20px 18px;
            border-radius:{CARD_RADIUS};
            background:{CARD_BACKGROUND};
            border:{CARD_BORDER};
            box-shadow:{CARD_SHADOW};
            display:flex;
            flex-direction:column;
            justify-content:center;
            align-items:flex-start;
            text-align:left;
            box-sizing:border-box;
            overflow:hidden;
            animation: ft-fade-up 320ms ease-out;
        ">
            <div style="
                font-family:Manrope,sans-serif;
                font-size:12px;
                line-height:1.2;
                color:{MUTED_COLOR};
                font-weight:650;
                letter-spacing:0.08em;
                text-transform:uppercase;
            ">
                {html.escape(str(title))}
            </div>

            <div style="
                margin-top:12px;
                font-family:Fraunces,Georgia,serif;
                font-size:clamp(22px,1.8vw,30px);
                line-height:1.15;
                font-weight:700;
                color:{value_color};
                overflow-wrap:anywhere;
                word-break:break-word;
            ">
                {html.escape(str(value))}
            </div>

            {secondary_value_html}
            {subtitle_html}
            {footer_html}
        </div>
        """
    )


def _section_label(text: str) -> None:
    render_html(
        f"""
        <div style="
            font-family:Manrope,sans-serif;
            font-size:12px;
            color:{MUTED_COLOR};
            font-weight:650;
            letter-spacing:0.1em;
            text-transform:uppercase;
            margin-bottom:8px;
        ">
            {html.escape(text)}
        </div>
        """
    )


def _category_rows_html(rows: list[dict]) -> str:
    items: list[str] = []

    for index, row in enumerate(rows):
        percent = max(0.0, min(100.0, float(row.get("percent", 0))))
        color = html.escape(str(row.get("color") or "#60a5fa"))
        border = (
            "border-bottom:1px solid rgba(148,163,184,0.10);"
            if index < len(rows) - 1
            else ""
        )

        items.append(
            f"""
            <div style="padding:12px 0;{border}">
                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    gap:12px;
                ">
                    <div style="
                        display:flex;
                        align-items:center;
                        gap:10px;
                        min-width:0;
                    ">
                        <span style="
                            width:10px;
                            height:10px;
                            border-radius:999px;
                            background:{color};
                            box-shadow:0 0 0 3px {color}22;
                            flex-shrink:0;
                        "></span>
                        <span style="
                            font-family:Manrope,sans-serif;
                            font-size:14px;
                            font-weight:700;
                            color:{TEXT_COLOR};
                            white-space:nowrap;
                            overflow:hidden;
                            text-overflow:ellipsis;
                        ">
                            {html.escape(str(row.get("icon", "")))}
                            {html.escape(str(row.get("name", "")))}
                        </span>
                    </div>
                    <div style="text-align:right;flex-shrink:0;">
                        <div style="
                            font-family:Fraunces,Georgia,serif;
                            font-size:16px;
                            font-weight:700;
                            color:{TEXT_COLOR};
                            white-space:nowrap;
                        ">
                            {html.escape(str(row.get("amount", "")))}
                        </div>
                        <div style="
                            margin-top:2px;
                            font-size:12px;
                            font-weight:600;
                            color:{MUTED_COLOR};
                        ">
                            {percent:.1f}%
                        </div>
                    </div>
                </div>
                <div style="
                    margin-top:8px;
                    height:4px;
                    border-radius:999px;
                    background:rgba(148,163,184,0.12);
                    overflow:hidden;
                ">
                    <div style="
                        width:{percent:.2f}%;
                        height:100%;
                        border-radius:999px;
                        background:linear-gradient(90deg,{color}aa,{color});
                    "></div>
                </div>
            </div>
            """
        )

    return "".join(items)


def render_expense_distribution_card(
    rows: list[dict],
    *,
    total_label: str,
    render_pie: Callable[[], None],
    list_max_height: int = 360,
) -> None:
    """
    Card unica con torta a sinistra e lista scorrevole a destra.

    ``render_pie`` è una callback senza argomenti (es. iframe Plotly).
    """
    with st.container(border=True):
        render_html(
            '<span class="ft-distribution-anchor" aria-hidden="true"></span>'
        )
        left_col, right_col = st.columns([1.15, 1], gap="large")

        with left_col:
            _section_label("Distribuzione")
            render_pie()

        with right_col:
            _section_label("Per categoria")
            render_html(
                f"""
                <div class="ft-category-scroll" style="
                    max-height:{list_max_height}px;
                    overflow-y:auto;
                    overflow-x:hidden;
                    padding-right:6px;
                    margin-right:-2px;
                    overscroll-behavior:contain;
                ">
                    {_category_rows_html(rows)}
                </div>
                <div style="
                    margin-top:14px;
                    padding-top:14px;
                    border-top:1px solid rgba(148,163,184,0.14);
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    gap:12px;
                ">
                    <span style="
                        font-size:12px;
                        font-weight:650;
                        letter-spacing:0.08em;
                        text-transform:uppercase;
                        color:{MUTED_COLOR};
                    ">Totale</span>
                    <span style="
                        font-family:Fraunces,Georgia,serif;
                        font-size:20px;
                        font-weight:700;
                        color:{TEXT_COLOR};
                    ">{html.escape(total_label)}</span>
                </div>
                """
            )


def render_chart_card(render_chart: Callable[[], None]) -> None:
    """Card semplice che avvolge un grafico (callback senza argomenti)."""
    with st.container(border=True):
        render_html(
            '<span class="ft-chart-card-anchor" aria-hidden="true"></span>'
        )
        render_chart()


def render_section_title(text: str) -> None:
    render_html(
        f'<div class="ft-section-title">{html.escape(text)}</div>'
    )


@contextmanager
def styled_panel(*, kind: str = "panel") -> Any:
    """
    Pannello con lo stesso look delle card Dashboard.

    kind: panel | movement
    """
    with st.container(border=True):
        render_html(
            f'<span class="ft-{html.escape(kind)}-anchor" '
            'aria-hidden="true"></span>'
        )
        yield
