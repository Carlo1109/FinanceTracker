import streamlit as st

from src.components.cards import (
    render_section_title,
    styled_panel,
)
from src.services.categories import get_category_icon, get_category_names
from src.services.movement_service import add_manual_movement
from src.utils.formatting import euro


def get_categories() -> list[str]:
    return get_category_names()


def show_manual_entry() -> None:
    st.title("Nuovo movimento")
    st.caption(
        "Aggiungi manualmente una spesa o un'entrata "
        "non presente negli import."
    )

    categories = get_categories()

    render_section_title("Dettagli movimento")
    with styled_panel():
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
            account = st.selectbox(
                "Conto",
                ["Fineco", "Revolut", "PostePay", "Contanti", "PayPal", "Altro"],
            )
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

        is_special = False
        speciale_mesi = 0
        if movement_type == "Uscita":
            is_special = st.checkbox(
                "Spesa speciale",
                value=False,
                key="manual_speciale",
            )
            if is_special:
                speciale_mesi = int(
                    st.number_input(
                        "Ripartisci su mesi",
                        min_value=0,
                        max_value=60,
                        value=0,
                        step=1,
                        key="manual_speciale_mesi",
                    )
                )
                if speciale_mesi > 0:
                    st.caption(
                        f"Nella media giornaliera conterà "
                        f"{euro(amount / speciale_mesi)}/mese "
                        f"per {speciale_mesi} mesi. L'importo intero resta nei totali."
                    )
                else:
                    st.caption(
                        "0 mesi = esclusa del tutto dalla media giornaliera "
                        "(resta nei totali)."
                    )
            else:
                st.caption(
                    "Segna spese fuori ritmo e, se vuoi, ripartiscile "
                    "sui mesi (es. abbonamento annuale su 12)."
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
            speciale=is_special,
            speciale_mesi=speciale_mesi,
        )

        st.toast("Movimento salvato")
