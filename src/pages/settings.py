from pathlib import Path

import streamlit as st

from src.services.importer import load_category_rules
from src.services.movement_service import load_movements, recalculate_automatic_categories
from src.services.backup_service import create_backup


APP_VERSION = "v0.4.0"


def show_settings() -> None:
    st.title("⚙️ Impostazioni")
    st.caption("Gestisci configurazioni, dati e informazioni dell'app.")

    df = load_movements()
    categories = load_category_rules()

    tab_accounts, tab_categories, tab_data, tab_info = st.tabs(
        ["💳 Conti", "🏷️ Categorie", "💾 Dati", "ℹ️ Info"]
    )

    with tab_accounts:
        st.markdown("### Conti collegati")

        if df.empty:
            st.info("Nessun conto trovato. Aggiungi o importa movimenti per vedere i conti.")
        else:
            accounts = sorted(df["account"].dropna().unique().tolist())

            for account in accounts:
                movements_count = len(df[df["account"] == account])
                total = df[df["account"] == account]["importo"].sum()

                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"### {account}")
                        st.caption(f"{movements_count} movimenti")


    with tab_categories:
        st.markdown("### Categorie")

        for category, keywords in categories.items():
            with st.container(border=True):
                st.markdown(f"### {category}")
                st.caption(", ".join(keywords))

        if st.button("🔄 Aggiorna categorie automatiche", use_container_width=True):
            updated = recalculate_automatic_categories()
            st.success(f"Categorie ricalcolate. Movimenti aggiornati: {updated}")


    with tab_data:
        st.markdown("### Dati")

        db_path = Path("data/finance_tracker.db").resolve()
        config_path = Path("config/categories.json").resolve()
        backup_filename = "finance_tracker_backup.db"

        c1, c2 = st.columns(2)

        with c1:
            with st.container(border=True):
                st.markdown("#### Database")
                st.code(str(db_path))
                st.caption("Contiene movimenti, categorie assegnate e dati salvati.")

        with c2:
            with st.container(border=True):
                st.markdown("#### Configurazione categorie")
                st.code(str(config_path))
                st.caption("Contiene le regole automatiche di categorizzazione.")

        if not df.empty:
            st.metric("Movimenti salvati", len(df))

        st.markdown("---")

        st.markdown("### Backup")

        if st.button(
            "📦 Crea backup completo",
            use_container_width=True,
        ):
            backup_path = create_backup()

            st.success("Backup creato correttamente.")

            with open(backup_path, "rb") as f:
                st.download_button(
                    "⬇️ Scarica backup",
                    data=f,
                    file_name=backup_path.name,
                    mime="application/zip",
                    use_container_width=True,
                )

                st.info("Per fare un backup, copia la cartella `data/` e la cartella `config/`.")

    with tab_info:
        st.markdown("### FinanceTracker")

        with st.container(border=True):
            st.markdown(f"**Versione:** {APP_VERSION}")
            st.markdown("**Database:** SQLite")
            st.markdown("**Framework:** Streamlit")  
            st.markdown("**Sviluppatore:** Carlo La Sala")

        st.caption("Creato per avere una visione chiara e semplice delle proprie finanze personali.")