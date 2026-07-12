import pandas as pd
import streamlit as st

from src.services.importer import (
    get_category_icon,
    get_category_names,
)
from src.services.movement_service import (
    delete_movement,
    load_movements,
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
    return get_category_names()




def show_movements() -> None:
    st.title("💳 Movimenti")
    st.caption("Cerca, filtra e modifica i movimenti salvati.")

    df = load_movements()

    if df.empty:
        st.info("Non ci sono ancora movimenti. Importa un file o aggiungi un movimento manuale.")
        return

    categories = get_categories()
    months = sorted(df["mese"].dropna().unique(), reverse=True)
    accounts = sorted(df["account"].dropna().unique().tolist())

    filter_col_1, filter_col_2, filter_col_3, filter_col_4 = st.columns([1.2, 1.4, 1.4, 2.4])

    with filter_col_1:
        selected_month = st.selectbox("Mese", months)

    with filter_col_2:
        selected_account = st.selectbox("Conto", ["Tutti"] + accounts)

    with filter_col_3:
        selected_category = st.selectbox(
            "Categoria",
            ["Tutte"] + categories,
            format_func=lambda name: (
                name if name == "Tutte"
                else f"{get_category_icon(name)} {name}"
            ),
        )

    with filter_col_4:
        search = st.text_input("Cerca", placeholder="Lidl, PayPal, Trenitalia...")

    filtered_df = df[df["mese"] == selected_month].copy()

    if selected_account != "Tutti":
        filtered_df = filtered_df[filtered_df["account"] == selected_account]

    if selected_category != "Tutte":
        filtered_df = filtered_df[filtered_df["categoria"] == selected_category]

    if search:
        mask = (
            filtered_df["descrizione"].fillna("").str.contains(search, case=False, na=False)
            | filtered_df["descrizione_completa"].fillna("").str.contains(search, case=False, na=False)
            | filtered_df["categoria"].fillna("").str.contains(search, case=False, na=False)
            | filtered_df["account"].fillna("").str.contains(search, case=False, na=False)
            | filtered_df["notes"].fillna("").str.contains(search, case=False, na=False)
            | filtered_df["importo"].astype(str).str.contains(search, case=False, na=False)
        )
        filtered_df = filtered_df[mask]

    total_income = filtered_df[filtered_df["importo"] > 0]["importo"].sum()
    total_expense = abs(filtered_df[filtered_df["importo"] < 0]["importo"].sum())
    balance = total_income - total_expense

    summary_col_1, summary_col_2, summary_col_3, summary_col_4 = st.columns(4)

    with summary_col_1:
        st.metric("Movimenti", len(filtered_df))

    with summary_col_2:
        st.metric("Entrate", euro(total_income))

    with summary_col_3:
        st.metric("Uscite", euro(total_expense))

    with summary_col_4:
        st.metric("Bilancio", euro(balance))

    st.divider()

    if filtered_df.empty:
        st.warning("Nessun movimento trovato con i filtri selezionati.")
        return

    for _, row in filtered_df.sort_values("data", ascending=False).iterrows():
        amount = float(row["importo"])
        amount_color = "#22c55e" if amount > 0 else "#ef4444"
        sign = "+" if amount > 0 else ""

        category = row["categoria"] if row["categoria"] in categories else "Altro"
        icon = get_category_icon(category)

        date = format_date(row["data"])

        description = clean_description(row["descrizione"])
        full_description = clean_description(row["descrizione_completa"])
        title = full_description if full_description else description

        with st.container(border=True):
            top_left, top_right = st.columns([4, 1.4])

            with top_left:
                st.markdown(
                    f"""
                    <div style="font-size: 18px; font-weight: 850; color: #f8fafc;">
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
                        <span style="margin-left: 8px;">{date}</span>
                        <span style="margin-left: 8px;">{row["account"]}</span>
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
                        font-weight: 950;
                        color: {amount_color};
                        padding-top: 4px;
                    ">
                        {sign}{euro(amount)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with st.expander("Dettagli"):
                edit_col_1, edit_col_2 = st.columns([2, 1])

                with edit_col_1:
                    new_category = st.selectbox(
                        "Categoria",
                        categories,
                        index=categories.index(category),
                        format_func=lambda name: (
                            f"{get_category_icon(name)} {name}"
                        ),
                        key=f"category_{row['id']}",
                    )

                    if new_category != row["categoria"]:
                        update_movement_category(int(row["id"]), new_category)
                        st.toast("Categoria aggiornata")
                        st.rerun()

                    if row.get("notes"):
                        st.caption(f"Note: {row['notes']}")

                    st.caption(description)

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

    with st.expander("Vista avanzata"):
        st.dataframe(
            filtered_df[
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