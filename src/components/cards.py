import html

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
) -> None:
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
        </div>
        """
    )


def render_kpi_card(
    title: str,
    value: str,
    icon: str = "",
    value_color: str = TEXT_COLOR,
) -> None:
    icon_html = ""

    if icon:
        icon_html = f"{html.escape(icon)} "

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
