import streamlit as st


def show_movements() -> None:
    st.title("Movimenti")

    df = st.session_state.get("movements")

    if df is None:
        st.info("Importa prima un file Fineco dalla Dashboard.")
        return

    months = sorted(df["mese"].unique(), reverse=True)
    selected_month = st.selectbox("Mese", months)

    filtered = df[df["mese"] == selected_month]

    st.dataframe(
        filtered[
            [
                "data",
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