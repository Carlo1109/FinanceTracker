import html
from pathlib import Path

import streamlit as st

from src.services.imports import get_importer_by_label, list_importers
from src.services.movement_service import save_movements


def show_import_data() -> None:
    st.title("Importa dati")
    st.caption(
        "Importa movimenti da file esterni. "
        "I duplicati vengono ignorati automaticamente."
    )

    importers = list_importers()
    labels = [info.label for info in importers]

    with st.container(border=True):
        st.markdown("### Sorgente dati")

        source_label = st.selectbox("Origine", labels)
        importer = get_importer_by_label(source_label)
        info = importer.info
        allowed_extensions = {ext.lower() for ext in info.extensions}

        uploaded_file = st.file_uploader(
            f"File {info.label}",
            type=None,
            help=info.help_text,
        )

        if uploaded_file:
            suffix = Path(uploaded_file.name).suffix.lower()
            if suffix not in allowed_extensions:
                expected = ", ".join(sorted(allowed_extensions))
                st.error(
                    f"Formato non supportato per {info.label}. "
                    f"Usa: {expected}"
                )
                uploaded_file = None

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
                    File selezionato: <b>{html.escape(uploaded_file.name)}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("")

            if st.button("Importa movimenti", width="stretch", type="primary"):
                with st.spinner("Importazione in corso..."):
                    try:
                        imported_df = importer.parse(uploaded_file)
                        inserted, skipped = save_movements(
                            imported_df,
                            source=info.label,
                            account=info.account,
                        )
                    except Exception as error:  # noqa: BLE001
                        st.error(f"Import fallito: {error}")
                        return

                st.success("Import completato")

                c1, c2 = st.columns(2)

                with c1:
                    st.metric("Nuovi movimenti", inserted)

                with c2:
                    st.metric("Già presenti", skipped)

                if inserted == 0 and skipped > 0:
                    st.info(
                        "Il file era già stato importato. "
                        "Nessun nuovo movimento aggiunto."
                    )
        else:
            expected = ", ".join(sorted(allowed_extensions))
            st.info(
                f"Seleziona un file {info.label} ({expected}) per iniziare. "
                "Puoi anche trascinarlo sulla zona di upload."
            )
