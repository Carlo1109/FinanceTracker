import streamlit as st

from src.services.movement_service import add_manual_movement


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


def show_manual_entry() -> None:
    st.title("Aggiungi movimento")

    with st.form("manual_entry"):
        movement_date = st.date_input("Data")
        description = st.text_input("Descrizione")
        amount = st.number_input("Importo", min_value=0.01, step=0.01)
        movement_type = st.selectbox("Tipo", ["Uscita", "Entrata"])
        category = st.selectbox("Categoria", CATEGORIES)
        account = st.selectbox("Conto", ["Fineco", "Contanti", "PayPal", "Altro"])
        notes = st.text_area("Note")

        submitted = st.form_submit_button("Salva movimento")

    if submitted:
        if not description.strip():
            st.error("Inserisci una descrizione.")
            return

        add_manual_movement(
            movement_date=movement_date,
            description=description.strip(),
            amount=amount,
            category=category,
            movement_type=movement_type,
            account=account,
            notes=notes.strip(),
        )

        st.success("Movimento salvato correttamente.")