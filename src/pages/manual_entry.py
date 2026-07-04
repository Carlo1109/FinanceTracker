import streamlit as st


def show_manual_entry() -> None:
    st.title("Aggiungi movimento")

    with st.form("manual_entry"):
        date = st.date_input("Data")
        description = st.text_input("Descrizione")
        amount = st.number_input("Importo", step=0.01)
        movement_type = st.selectbox("Tipo", ["Uscita", "Entrata"])
        category = st.selectbox(
            "Categoria",
            ["Alimentari", "Auto", "Casa", "Ristoranti", "Shopping", "Investimenti", "Straordinarie", "Altro"],
        )
        account = st.selectbox("Conto", ["Fineco", "Contanti", "PayPal", "Altro"])
        notes = st.text_area("Note")

        submitted = st.form_submit_button("Salva movimento")

    if submitted:
        st.success("Movimento salvato. Nel prossimo step lo colleghiamo al database.")