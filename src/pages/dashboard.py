import pandas as pd
import plotly.express as px
import streamlit as st

from src.theme.style import metric_card


def euro(value: float) -> str:
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def show_dashboard() -> None:
    st.title("Dashboard")

    entrate = 1617.00
    ordinarie = 895.00
    investimenti = 123.00
    straordinarie = 398.00
    bilancio_reale = -104.09
    risparmio_operativo = entrate - ordinarie - investimenti

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Entrate", euro(entrate), "positive")
    with c2:
        metric_card("Spese ordinarie", euro(ordinarie), "negative")
    with c3:
        metric_card("Investimenti", euro(investimenti), "positive")
    with c4:
        metric_card("Bilancio reale", euro(bilancio_reale), "negative")

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Spese per categoria")

    df_cat = pd.DataFrame(
        {
            "Categoria": ["Alimentari", "Auto", "Ristoranti", "Shopping", "Palestra", "Altro"],
            "Importo": [230, 120, 95, 80, 398, 370],
        }
    )

    fig = px.bar(
        df_cat,
        x="Importo",
        y="Categoria",
        orientation="h",
        text="Importo",
        title=None,
    )
    fig.update_layout(
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e5e7eb",
        xaxis_title="€",
        yaxis_title="",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Andamento mensile")

    df_months = pd.DataFrame(
        {
            "Mese": ["Maggio", "Giugno"],
            "Entrate": [1650, 1617],
            "Uscite": [1837.3, 1721.09],
            "Investimenti": [118, 123],
            "Risparmio operativo": [140, 417],
        }
    )

    fig2 = px.line(
        df_months,
        x="Mese",
        y=["Entrate", "Uscite", "Risparmio operativo"],
        markers=True,
    )
    fig2.update_layout(
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e5e7eb",
        legend_title_text="",
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)