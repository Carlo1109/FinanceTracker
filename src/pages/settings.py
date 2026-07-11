from pathlib import Path

import streamlit as st
from src.services.movement_service import load_movements, recalculate_automatic_categories
from src.services.backup_service import create_backup
from src.services.importer import (
    add_category,
    add_keyword_to_category,
    load_category_rules,
    remove_keyword_from_category,
)


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
        st.caption(
            "Crea nuove categorie oppure aggiungi parole chiave "
            "alle regole automatiche esistenti."
        )

        category_names = list(categories.keys())

        with st.container(border=True):
            st.markdown("#### Aggiungi parola chiave")

            keyword_col_1, keyword_col_2 = st.columns([1, 2])

            with keyword_col_1:
                selected_category = st.selectbox(
                    "Categoria",
                    category_names,
                    key="settings_keyword_category",
                )

            with keyword_col_2:
                new_keyword = st.text_input(
                    "Parola chiave",
                    placeholder="Es. BENNET, TIGOTÀ, AUTOGRILL...",
                    key="settings_new_keyword",
                )

            if "keyword_feedback" in st.session_state:
                feedback_type, feedback_message = st.session_state.pop("keyword_feedback")

                if feedback_type == "success":
                    st.success(feedback_message)
                else:
                    st.warning(feedback_message)

            if st.button(
                "Aggiungi parola chiave",
                key="add_category_keyword",
                use_container_width=True,
                type="primary",
            ):
                added = add_keyword_to_category(
                    selected_category,
                    new_keyword,
                )

                if added:
                    st.session_state["keyword_feedback"] = (
                        "success",
                        f'Parola chiave "{new_keyword.strip().upper()}" aggiunta a "{selected_category}".',
                    )
                else:
                    st.session_state["keyword_feedback"] = (
                        "warning",
                        "La parola chiave è vuota oppure è già presente.",
                    )

                st.rerun()

        with st.container(border=True):
            st.markdown("#### Crea nuova categoria")

            new_category = st.text_input(
                "Nome categoria",
                placeholder="Es. Vacanze, Animali, Regali...",
                key="settings_new_category",
            )

            if "category_feedback" in st.session_state:
                feedback_type, feedback_message = st.session_state.pop("category_feedback")

                if feedback_type == "success":
                    st.success(feedback_message)
                else:
                    st.warning(feedback_message)

            if st.button(
                "Crea categoria",
                key="create_new_category",
                use_container_width=True,
                type="primary",
            ):
                created = add_category(new_category)

                if created:
                    st.session_state["category_feedback"] = (
                        "success",
                        f'Categoria "{new_category.strip()}" creata correttamente.',
                    )
                else:
                    st.session_state["category_feedback"] = (
                        "warning",
                        "Il nome è vuoto oppure la categoria esiste già.",
                    )

                st.rerun()

        if "keyword_delete_feedback" in st.session_state:
            feedback_type, feedback_message = st.session_state.pop(
                "keyword_delete_feedback"
            )

            if feedback_type == "success":
                st.success(feedback_message)
            else:
                st.warning(feedback_message)

        st.markdown("### Regole attuali")

        for category, keywords in categories.items():
            with st.expander(f"{category} · {len(keywords)} parole chiave"):
                if not keywords:
                    st.caption("Nessuna parola chiave associata.")
                    continue

                for keyword in keywords:
                    keyword_col, delete_col = st.columns([5, 1])

                    with keyword_col:
                        st.markdown(f"`{keyword}`")

                    with delete_col:
                        if st.button(
                            "🗑️",
                            key=f"delete_keyword_{category}_{keyword}",
                            help=f'Elimina "{keyword}"',
                            use_container_width=True,
                        ):
                            removed = remove_keyword_from_category(category, keyword)

                            if removed:
                                st.session_state["keyword_delete_feedback"] = (
                                    "success",
                                    f'Parola chiave "{keyword}" eliminata da "{category}".',
                                )
                            else:
                                st.session_state["keyword_delete_feedback"] = (
                                    "warning",
                                    "Non è stato possibile eliminare la parola chiave.",
                                )

                            st.rerun()

        if st.button(
            "🔄 Aggiorna categorie automatiche",
            use_container_width=True,
        ):
            updated = recalculate_automatic_categories()
            st.success(
                f"Categorie aggiornate. Movimenti modificati: {updated}"
            )


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