import streamlit as st

from src.services.importer import get_category_icon, get_category_names
from src.services.movement_service import add_manual_movement


def get_categories() -> list[str]:
    return get_category_names()


def show_manual_entry() -> None:
    st.title("Nuovo movimento")
    st.caption("Aggiungi manualmente una spesa o un'entrata non presente negli import.")

    categories = get_categories()

    with st.container(border=True):
        st.markdown("### Dettagli movimento")

        movement_type = st.radio(
            "Tipo movimento",
            ["Uscita", "Entrata"],
            horizontal=True,
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            movement_date = st.date_input("Data")
            amount = st.number_input("Importo (€)", min_value=0.01, step=0.01)

        with col2:
            account = st.selectbox("Conto", ["Fineco", "Contanti", "PayPal", "Altro"])
            category = st.selectbox(
                "Categoria",
                categories,
                format_func=lambda name: f"{get_category_icon(name)} {name}",
            )

        description = st.text_input(
            "Descrizione",
            placeholder="Es. Gelato, rimborso, spesa contanti...",
        )

        notes = st.text_area(
            "Note",
            placeholder="Opzionale",
        )

        submitted = st.button(
            "Salva movimento",
            width="stretch",
            type="primary",
        )

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
        st.toast("Movimento aggiunto")