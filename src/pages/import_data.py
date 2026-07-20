import streamlit as st

from src.services.importer import import_fineco_excel
from src.services.movement_service import save_movements


def show_import_data() -> None:
    st.title("Importa dati")
    st.caption("Importa movimenti da file esterni. I duplicati vengono ignorati automaticamente.")

    with st.container(border=True):
        st.markdown("### Sorgente dati")

        source = st.selectbox(
            "Origine",
            ["Fineco Excel"],
        )

        uploaded_file = st.file_uploader(
            "File",
            type=["xlsx"],
            help="Carica l'export movimenti Fineco in formato Excel.",
        )

        if uploaded_file:
            st.markdown(
                f"""
                <div style="
                    margin-top: 12px;
                    padding: 14px 16px;
                    border-radius: 16px;
                    background: rgba(34, 197, 94, 0.10);
                    border: 1px solid rgba(34, 197, 94, 0.22);
                    color: #e5e7eb;
                ">
                    File selezionato: <b>{uploaded_file.name}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("")

            if st.button("Importa movimenti", width="stretch", type="primary"):
                if source == "Fineco Excel":
                    with st.spinner("Importazione in corso..."):
                        imported_df = import_fineco_excel(uploaded_file)
                        inserted, skipped = save_movements(imported_df, source="Fineco")

                    st.success("Import completato")

                    c1, c2 = st.columns(2)

                    with c1:
                        st.metric("Nuovi movimenti", inserted)

                    with c2:
                        st.metric("Già presenti", skipped)

                    if inserted == 0 and skipped > 0:
                        st.info("Il file era già stato importato. Nessun nuovo movimento aggiunto.")
        else:
            st.info("Seleziona un file Excel Fineco per iniziare.")