import html

import streamlit as st


INCOME_COLOR = "#22c55e"
EXPENSE_COLOR = "#ff4d4f"
INVESTMENT_COLOR = "#60a5fa"
LIQUIDITY_COLOR = "#34d399"
BALANCE_COLOR = "#22c55e"
TEXT_COLOR = "#f8fafc"
MUTED_COLOR = "#94a3b8"

CARD_RADIUS = "22px"
CARD_BORDER = "1px solid rgba(148,163,184,.16)"
CARD_SHADOW = "0 14px 34px rgba(0,0,0,.40)"
CARD_BACKGROUND = "rgba(15,23,42,.82)"


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
            margin-top:20px;
            min-height:240px;
            padding:28px 34px;
            border-radius: {CARD_RADIUS};
            background:
                radial-gradient(
                    circle at top left,
                    rgba(34,197,94,0.18),
                    transparent 28%
                ),
                {CARD_BACKGROUND};
            border:{CARD_BORDER};
            box-shadow:{CARD_SHADOW};
            display:flex;
            flex-direction:column;
            align-items:center;
            justify-content:center;
            text-align:center;
            box-sizing:border-box;
        ">
            <div style="
                font-size:14px;
                color:#94a3b8;
                font-weight:700;
                letter-spacing:1px;
                text-transform:uppercase;
            ">
                {html.escape(title)}
            </div>

            <div style="
                margin-top:14px;
                font-size:clamp(42px,4vw,54px);
                line-height:1.08;
                font-weight:950;
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
    icon: str,
    value_color: str = TEXT_COLOR,
) -> None:
    render_html(
        f"""
        <div style="
            min-height:176px;
            padding:20px 18px;
            border-radius:{CARD_RADIUS};
            background:{CARD_BACKGROUND};
            border:{CARD_BORDER};
            box-shadow:{CARD_SHADOW};

            display:flex;
            flex-direction:column;
            justify-content:center;
            align-items:center;
            text-align:center;
            box-sizing:border-box;
        ">
            <div style="
                font-size:14px;
                color:#94a3b8;
                font-weight:700;
                letter-spacing:0.8px;
                text-transform:uppercase;
            ">
                {icon} {title}
            </div>

            <div style="
                margin-top:12px;
                font-size:clamp(28px,2vw,36px);
                line-height:1.1;
                font-weight:950;
                color:{value_color};
                white-space:normal;
                overflow-wrap:anywhere;
                word-break:break-word;
            ">
                {value}
            </div>
        </div>
        """
    )


def render_info_card(
    title: str,
    value: str,
    secondary_value: str | None = None,
    subtitle: str | None = None,
    subtitle_color: str = "#94a3b8",
    footer: str | None = None,
    value_color: str = "#f8fafc",
) -> None:
    secondary_value_html = ""

    if secondary_value:
        secondary_value_html = f"""
            <div style="
                margin-top:16px;
                font-size:clamp(26px,2.1vw,36px);
                line-height:1.15;
                font-weight:950;
                color:#e2e8f0;
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
                margin-top:10px;
                font-size:13px;
                line-height:1.25;
                font-weight:750;
                color:{subtitle_color};
                text-align:center;
            ">
                {html.escape(str(subtitle))}
            </div>
        """

    footer_html = ""

    if footer:
        footer_html = f"""
            <div style="
                margin-top:7px;
                font-size:12px;
                line-height:1.25;
                font-weight:600;
                color:#64748b;
                text-align:center;
            ">
                {html.escape(str(footer))}
            </div>
        """

    render_html(
        f"""
        <div style="
            min-height:210px;
            padding:22px 18px;
            border-radius:22px;
            background:rgba(15,23,42,0.82);
            border:1px solid rgba(148,163,184,0.16);
            box-shadow:0 14px 34px rgba(0,0,0,0.20);

            display:flex;
            flex-direction:column;
            justify-content:center;
            align-items:center;
            text-align:center;

            box-sizing:border-box;
            overflow:hidden;
        ">
            <div style="
                font-size:13px;
                line-height:1.2;
                color:#94a3b8;
                font-weight:750;
                letter-spacing:0.7px;
                text-transform:uppercase;
            ">
                {html.escape(str(title))}
            </div>

            <div style="
                margin-top:16px;
                font-size:clamp(26px,2.1vw,36px);
                line-height:1.15;
                font-weight:950;
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