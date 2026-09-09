import streamlit as st

from src.components.cards import (
    render_section_title,
    styled_panel,
)
from src.components.date_input import themed_date_input
from src.services.analytics import (
    is_initial_balance_category,
    is_loan_category,
    is_non_operating_category,
    is_transfer_category,
)
from src.services.categories import get_category_icon, get_category_names
from src.services.movement_service import (
    account_choices,
    add_manual_movement,
    load_movements,
)
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

        movement_date = themed_date_input("Data", key="manual_date")

        amount_col, account_col, category_col = st.columns(3)

        with amount_col:
            amount = st.number_input(
                "Importo (€)",
                min_value=0.01,
                step=0.01,
                format="%.2f",
            )

        with account_col:
            discovered = []
            movements = load_movements()
            if not movements.empty:
                discovered = (
                    movements["account"].dropna().astype(str).tolist()
                )
            account = st.selectbox(
                "Conto",
                account_choices(*discovered),
            )

        with category_col:
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

        if is_transfer_category(category):
            st.caption(
                "I trasferimenti non entrano in entrate o uscite, "
                "ma contano nel saldo del conto."
            )
        elif is_initial_balance_category(category):
            st.caption(
                "Il saldo iniziale non è un’entrata: serve a far "
                "quadrare il saldo reale del conto."
            )
        elif is_loan_category(category):
            st.caption(
                "I prestiti non entrano in entrate o uscite, "
                "ma contano nel saldo del conto. "
                "Andata e ritorno nella stessa categoria."
            )

        if (
            movement_type == "Uscita"
            and not is_non_operating_category(category)
        ):
            is_special = st.checkbox(
                "Spesa speciale",
                key="manual_speciale",
                help=(
                    "Segna spese fuori dalla normalità. "
                    "Opzionale: ripartiscile sui mesi "
                    "(es. abbonamento annuale su 12). "
                    "0 mesi = esclusa dalla media giornaliera; "
                    "l'importo intero resta nei totali."
                ),
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
                        help=(
                            "Quanti mesi usare nella media giornaliera. "
                            "0 = esclusa del tutto dalla media "
                            "(resta nei totali)."
                        ),
                    )
                )
                if speciale_mesi > 0:
                    st.caption(
                        f"Nella media: {euro(amount / speciale_mesi)}/mese "
                        f"per {speciale_mesi} mesi."
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
