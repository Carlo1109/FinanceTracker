import pandas as pd
import streamlit as st

from src.services.importer import load_category_rules
from src.services.movement_service import (
    delete_movement,
    load_movements,
    recalculate_automatic_categories,
    update_movement_category,
)


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


def get_categories() -> list[str]:
    categories = list(load_category_rules().keys())
    if "Altro" not in categories:
        categories.append("Altro")
    return categories


def category_icon(category: str) -> str:
    return {
        "Alimentari": "🛒",
        "Auto": "🚗",
        "Casa": "🏠",
        "Svago": "🎉",
        "Trasporti": "🚆",
        "Salute": "🏥",
        "Investimenti": "📈",
        "Stipendio": "💼",
        "Altro": "❓",
    }.get(category, "❓")


def show_movements() -> None:
    st.title("💳 Movimenti")

    df = load_movements()

    if df.empty:
        st.info("Non ci sono ancora movimenti. Importa un file Fineco o aggiungi un movimento manuale.")
        return

    categories = get_categories()

    with st.container(border=True):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown("Gestisci i movimenti salvati, correggi le categorie e controlla le spese.")

        with col2:
            if st.button("🔄 Ricalcola categorie", use_container_width=True):
                updated = recalculate_automatic_categories()
                st.toast(f"Movimenti aggiornati: {updated}")
                st.rerun()

    months = sorted(df["mese"].dropna().unique(), reverse=True)

    filter_col_1, filter_col_2, filter_col_3 = st.columns([1.4, 1.4, 3])

    with filter_col_1:
        selected_month = st.selectbox("Mese", months)

    with filter_col_2:
        selected_category = st.selectbox("Categoria", ["Tutte"] + categories)

    with filter_col_3:
        search = st.text_input("Cerca", placeholder="Lidl, PayPal, Trenitalia...")

    month_df = df[df["mese"] == selected_month].copy()

    if selected_category != "Tutte":
        month_df = month_df[month_df["categoria"] == selected_category]

    if search:
        mask = (
            month_df["descrizione"].fillna("").str.contains(search, case=False, na=False)
            | month_df["descrizione_completa"].fillna("").str.contains(search, case=False, na=False)
            | month_df["categoria"].fillna("").str.contains(search, case=False, na=False)
        )
        month_df = month_df[mask]

    total_income = month_df[month_df["importo"] > 0]["importo"].sum()
    total_expense = abs(month_df[month_df["importo"] < 0]["importo"].sum())
    balance = total_income - total_expense

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Movimenti", len(month_df))
    k2.metric("Entrate", euro(total_income))
    k3.metric("Uscite", euro(total_expense))
    k4.metric("Bilancio", euro(balance))

    st.divider()

    for _, row in month_df.iterrows():
        amount = float(row["importo"])
        amount_color = "#22c55e" if amount > 0 else "#ef4444"
        sign = "+" if amount > 0 else ""

        category = row["categoria"] if row["categoria"] in categories else "Altro"
        icon = category_icon(category)
        date = format_date(row["data"])

        description = clean_description(row["descrizione"])
        full_description = clean_description(row["descrizione_completa"])
        title = full_description if full_description else description

        with st.container(border=True):
            top_left, top_right = st.columns([4, 1.4])

            with top_left:
                st.markdown(
                    f"""
                    <div style="font-size: 18px; font-weight: 800; color: #f8fafc;">
                        {icon} {title}
                    </div>
                   <div style="font-size: 13px; color: #94a3b8; margin-top: 8px;">
                        <span style="
                            background: rgba(148, 163, 184, 0.16);
                            color: #e5e7eb;
                            padding: 4px 10px;
                            border-radius: 999px;
                            font-size: 12px;
                            font-weight: 700;
                        ">{category}</span>
                        <span style="margin-left: 8px; color: #94a3b8;">{date}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with top_right:
                st.markdown(
                    f"""
                    <div style="
                        text-align: right;
                        font-size: 24px;
                        font-weight: 900;
                        color: {amount_color};
                        padding-top: 4px;
                    ">
                        {sign}{euro(amount)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with st.expander("Modifica movimento"):
                edit_col_1, edit_col_2 = st.columns([2, 1])

                with edit_col_1:
                    new_category = st.selectbox(
                        "Categoria",
                        categories,
                        index=categories.index(category),
                        key=f"category_{row['id']}",
                    )

                    if new_category != row["categoria"]:
                        update_movement_category(int(row["id"]), new_category)
                        st.toast("Categoria aggiornata")
                        st.rerun()

                with edit_col_2:
                    st.markdown("<br>", unsafe_allow_html=True)

                    confirm_key = f"confirm_delete_{row['id']}"

                    if st.session_state.get(confirm_key):
                        st.warning("Eliminare?")

                        c_yes, c_no = st.columns(2)

                        with c_yes:
                            if st.button("Sì", key=f"delete_yes_{row['id']}", use_container_width=True):
                                delete_movement(int(row["id"]))
                                st.session_state[confirm_key] = False
                                st.toast("Movimento eliminato")
                                st.rerun()

                        with c_no:
                            if st.button("No", key=f"delete_no_{row['id']}", use_container_width=True):
                                st.session_state[confirm_key] = False
                                st.rerun()
                    else:
                        if st.button("🗑️ Elimina", key=f"delete_{row['id']}", use_container_width=True):
                            st.session_state[confirm_key] = True
                            st.rerun()

                st.caption(description)

    with st.expander("Vista avanzata"):
        st.dataframe(
            month_df[
                [
                    "id",
                    "data",
                    "data_operazione",
                    "data_valuta",
                    "descrizione",
                    "descrizione_completa",
                    "categoria",
                    "category_source",
                    "tipo",
                    "importo",
                    "source",
                    "account",
                    "notes",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )