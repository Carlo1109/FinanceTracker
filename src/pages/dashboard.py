import plotly.express as px
import streamlit as st

from src.services.importer import import_fineco_excel
from src.theme.style import metric_card


def euro(value: float) -> str:
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def show_dashboard() -> None:
    st.title("Dashboard")

    uploaded_file = st.file_uploader(
        "Importa export Fineco",
        type=["xlsx"],
    )

    if uploaded_file:
        df = import_fineco_excel(uploaded_file)
        st.session_state["movements"] = df

    df = st.session_state.get("movements")

    if df is None:
        st.info("Carica un file Fineco per visualizzare la dashboard.")
        return

    months = sorted(df["mese"].unique(), reverse=True)
    selected_month = st.selectbox("Mese", months)

    month_df = df[df["mese"] == selected_month]

    entrate = month_df[month_df["importo"] > 0]["importo"].sum()
    uscite = abs(month_df[month_df["importo"] < 0]["importo"].sum())
    bilancio = entrate - uscite

    investimenti = abs(
        month_df[
            month_df["categoria"].isin(["Investimenti"])
        ]["importo"].sum()
    )

    spese_ordinarie = abs(
        month_df[
            (month_df["importo"] < 0)
            & (~month_df["categoria"].isin(["Investimenti"]))
        ]["importo"].sum()
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card("Entrate", euro(entrate), "positive")
    with c2:
        metric_card("Uscite", euro(uscite), "negative")
    with c3:
        metric_card("Investimenti", euro(investimenti), "positive")
    with c4:
        metric_card(
            "Bilancio",
            euro(bilancio),
            "positive" if bilancio >= 0 else "negative",
        )

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Spese per categoria")

    expense_df = month_df[month_df["importo"] < 0].copy()
    category_df = (
        expense_df.groupby("categoria", as_index=False)["importo"]
        .sum()
        .assign(importo=lambda x: x["importo"].abs())
        .sort_values("importo", ascending=True)
    )

    fig = px.bar(
        category_df,
        x="importo",
        y="categoria",
        orientation="h",
        text="importo",
    )

    fig.update_layout(
        height=430,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e5e7eb",
        xaxis_title="€",
        yaxis_title="",
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Entrate vs uscite")

    monthly_df = (
        df.assign(
            entrate=lambda x: x["importo"].where(x["importo"] > 0, 0),
            uscite=lambda x: x["importo"].where(x["importo"] < 0, 0).abs(),
        )
        .groupby("mese", as_index=False)[["entrate", "uscite"]]
        .sum()
        .sort_values("mese")
    )

    fig2 = px.line(
        monthly_df,
        x="mese",
        y=["entrate", "uscite"],
        markers=True,
    )

    fig2.update_layout(
        height=430,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e5e7eb",
        legend_title_text="",
    )

    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)