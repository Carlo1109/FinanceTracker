import streamlit as st
from src.services.movement_service import (
    load_movements,
    update_movement_category,
    delete_movement,
)
import pandas as pd

CATEGORIES = [
    "Alimentari",
    "Auto",
    "Casa",
    "Svago",
    "Trasporti",
    "Salute",
    "Investimenti",
    "Stipendio",
    "Altro",
]


def euro(value: float) -> str:
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def clean_description(value: str) -> str:
    value = str(value).replace("\n", " ").strip()
    return " ".join(value.split())

def format_date(value) -> str:
    if pd.isna(value):
        return "Data non disponibile"

    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")

    return str(value)

def show_movements() -> None:
    st.title("Movimenti")

    df = load_movements()

    if df is None:
        st.info("Importa prima un file Fineco dalla Dashboard.")
        return

    months = sorted(df["mese"].unique(), reverse=True)
    selected_month = st.selectbox("Mese", months)

    month_df = df[df["mese"] == selected_month].copy()

    search = st.text_input("Cerca movimento", placeholder="Es. Lidl, PayPal, Trenitalia...")

    selected_category = st.selectbox(
        "Filtra categoria",
        ["Tutte"] + CATEGORIES,
    )

    if search:
        mask = (
            month_df["descrizione"].fillna("").str.contains(search, case=False, na=False)
            | month_df["descrizione_completa"].fillna("").str.contains(search, case=False, na=False)
            | month_df["categoria"].fillna("").str.contains(search, case=False, na=False)
        )
        month_df = month_df[mask]

    if selected_category != "Tutte":
        month_df = month_df[month_df["categoria"] == selected_category]

    st.caption(f"{len(month_df)} movimenti trovati")

    for index, row in month_df.iterrows():
        amount = float(row["importo"])
        amount_class = "metric-positive" if amount > 0 else "metric-negative"

        description = clean_description(row["descrizione"])
        full_description = clean_description(row["descrizione_completa"])
        date = format_date(row["data"])

        with st.container():
            col1, col2, col3, col4 = st.columns([5, 2, 2, 1])
            with col1:
                st.markdown(
                    f"""
                    <div class="section-card" style="margin-top: 10px;">
                        <div style="font-size: 17px; font-weight: 700; color: #f8fafc;">
                            {full_description if full_description else description}
                        </div>
                        <div style="font-size: 13px; color: #94a3b8; margin-top: 6px;">
                            {description} · {date}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col2:
                new_category = st.selectbox(
                    "Categoria",
                    CATEGORIES,
                    index=CATEGORIES.index(row["categoria"]) if row["categoria"] in CATEGORIES else CATEGORIES.index("Altro"),
                    key=f"category_{index}",
                    label_visibility="collapsed",
                )

                if new_category != row["categoria"]:
                    update_movement_category(int(row["id"]), new_category)
                    st.success("Categoria aggiornata.")
                    st.rerun()

            with col3:
                st.markdown(
                    f"""
                    <div class="section-card" style="margin-top: 10px; text-align: right;">
                        <div class="metric-value {amount_class}" style="font-size: 22px;">
                            {euro(amount)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col4:
                st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)

                if st.button("🗑️", key=f"delete_{row['id']}"):
                    delete_movement(int(row["id"]))
                    st.success("Movimento eliminato.")
                    st.rerun()

    with st.expander("Vista avanzata"):
        st.dataframe(
            month_df[
                [
                    "data",
                    "data_operazione",
                    "data_valuta",
                    "descrizione",
                    "descrizione_completa",
                    "categoria",
                    "tipo",
                    "importo",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )