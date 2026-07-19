import streamlit as st

from src.database.db import DB_PATH
from src.services.backup_service import create_backup
from src.services.importer import (
    USER_CATEGORY_CONFIG_PATH,
    add_category,
    add_keyword_to_category,
    delete_category,
    get_category_icon,
    load_category_definitions,
    remove_keyword_from_category,
    update_category_icon,
)
from src.services.movement_service import (
    load_movements,
    recalculate_automatic_categories,
)


APP_VERSION = "v1.0.1"

CATEGORY_ICONS = [
    "🛒", "🍽️", "🍺", "☕", "🍕", "🍔", "🍟", "🌭", "🥪", "🥗",
    "🍝", "🍣", "🍰", "🍦", "🥖", "🥩", "🍎", "🥦", "🥤", "🍷",
    "🚗", "🚙", "🚕", "🚌", "🚆", "🚇", "🚲", "🛵", "🏍️", "✈️",
    "🚢", "⛽", "🅿️", "🛞", "🔧", "🧰", "🛠️", "🚦", "🗺️", "🧳",
    "🏠", "🏡", "🏢", "🛋️", "🛏️", "🚿", "🔑", "🧹", "🧺", "🪴",
    "💡", "⚡", "🔥", "💧", "📱", "☎️", "🌐", "📡", "📺", "🔌",
    "❤️", "🏥", "💊", "🩺", "🦷", "👓", "🧘", "🏋️", "🏃", "🧴",
    "🛍️", "👕", "👗", "👟", "👜", "💄", "💍", "⌚", "💻", "🎧",
    "📷", "🖨️", "🧸", "🪑", "🎁", "📦", "🏷️", "🧾", "🛠️", "🧼",
    "🎮", "🎬", "🎵", "🎭", "🎨", "📚", "⚽", "🏀", "🎾", "🏕️",
    "🎟️", "🎳", "🎯", "🎸", "🧩", "♟️", "🏖️", "⛷️", "🏊", "🚴",
    "🐶", "🐱", "🐾", "👶", "👨‍👩‍👧", "🎂", "💐", "🎓", "🏫", "📖",
    "💼", "🧑‍💻", "🏭", "🧑‍🔧", "✏️", "📎", "📊", "📌", "🗂️", "📝",
    "💰", "💳", "💸", "📈", "📉", "🏦", "💵", "💶", "🪙", "🧮",
    "🔒", "🛡️", "⭐", "✅", "❓", "⚙️", "🔔", "♻️", "🌱", "🤝",
    "🧑‍🍳", "🧑‍⚕️", "🧑‍🏫", "🧑‍🎨", "🧑‍🚀", "🧑‍🌾", "🧑‍🔬", "🧑‍💼",
    "🎤", "🎹", "🥁", "🎻", "🎺", "📻", "📰", "🧠", "🫶", "💎",
]

CATEGORY_ICONS = list(dict.fromkeys(CATEGORY_ICONS))


def show_feedback(state_key: str) -> None:
    if state_key not in st.session_state:
        return

    feedback_type, feedback_message = st.session_state.pop(state_key)

    if feedback_type == "success":
        st.success(feedback_message)
    elif feedback_type == "error":
        st.error(feedback_message)
    else:
        st.warning(feedback_message)


def format_euro(value: float) -> str:
    return (
        f"{value:,.2f} €"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def set_icon_selection(state_key: str, icon: str) -> None:
    st.session_state[state_key] = icon


def render_icon_grid(
    state_key: str,
    default_icon: str,
    columns_count: int = 10,
) -> str:
    """
    Mostra le icone come griglia di pulsanti.

    L'icona selezionata viene evidenziata usando il pulsante primary.
    """
    if state_key not in st.session_state:
        st.session_state[state_key] = default_icon

    selected_icon = st.session_state[state_key]

    for row_start in range(0, len(CATEGORY_ICONS), columns_count):
        row_icons = CATEGORY_ICONS[
            row_start:row_start + columns_count
        ]
        columns = st.columns(columns_count, gap="small")

        for column_index, icon in enumerate(row_icons):
            with columns[column_index]:
                st.button(
                    icon,
                    key=f"{state_key}_{row_start + column_index}",
                    use_container_width=True,
                    type=(
                        "primary"
                        if icon == selected_icon
                        else "secondary"
                    ),
                    on_click=set_icon_selection,
                    args=(state_key, icon),
                )

    return st.session_state[state_key]


def show_settings() -> None:
    st.title("⚙️ Impostazioni")
    st.caption("Gestisci configurazioni, dati e informazioni dell'app.")

    df = load_movements()
    categories = load_category_definitions()

    tab_accounts, tab_categories, tab_data, tab_info = st.tabs(
        ["💳 Conti", "🏷️ Categorie", "💾 Dati", "ℹ️ Info"]
    )

    with tab_accounts:
        st.markdown("### Conti collegati")

        if df.empty:
            st.info(
                "Nessun conto trovato. Aggiungi o importa movimenti "
                "per vedere i conti."
            )
        else:
            accounts = sorted(
                df["account"].dropna().unique().tolist()
            )

            for account in accounts:
                account_df = df[df["account"] == account]
                movements_count = len(account_df)
                total = account_df["importo"].sum()

                with st.container(border=True):
                    col_info, col_total = st.columns([3, 1])

                    with col_info:
                        st.markdown(f"### {account}")
                        st.caption(f"{movements_count} movimenti")

                    with col_total:
                        st.metric(
                            "Saldo movimenti",
                            format_euro(total),
                        )

    with tab_categories:
        st.markdown("### Categorie")
        st.caption(
            "Crea categorie personalizzate, scegli l'icona e gestisci "
            "le parole chiave usate dalla categorizzazione automatica."
        )

        category_names = list(categories.keys())

        show_feedback("category_feedback")
        show_feedback("keyword_feedback")
        show_feedback("keyword_delete_feedback")
        show_feedback("icon_feedback")
        show_feedback("category_delete_feedback")
        show_feedback("recalculate_feedback")

        with st.container(border=True):
            st.markdown("#### Crea nuova categoria")

            create_col_1, create_col_2 = st.columns([2, 1])

            with create_col_1:
                new_category = st.text_input(
                    "Nome categoria",
                    placeholder="Es. Animali, Regali, Formazione...",
                    key="settings_new_category",
                )

            with create_col_2:
                st.markdown("**Icona selezionata**")
                st.markdown(
                    f"""
                    <div style="
                        font-size: 44px;
                        text-align: center;
                        padding: 8px 0;
                    ">
                        {st.session_state.get(
                            "settings_new_category_icon",
                            "🛒",
                        )}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with st.expander(
                "🎨 Scegli icona",
                expanded=False,
            ):
                new_category_icon = render_icon_grid(
                    "settings_new_category_icon",
                    "🛒",
                    columns_count=10,
                )

            st.caption(
                f"Anteprima: {new_category_icon} "
                f"{new_category.strip() or 'Nuova categoria'}"
            )

            if st.button(
                "Crea categoria",
                key="create_new_category",
                use_container_width=True,
                type="primary",
            ):
                created = add_category(
                    new_category,
                    new_category_icon,
                )

                if created:
                    st.session_state["category_feedback"] = (
                        "success",
                        f'Categoria "{new_category.strip()}" creata '
                        f"con l'icona {new_category_icon}.",
                    )
                else:
                    st.session_state["category_feedback"] = (
                        "warning",
                        "Il nome è vuoto oppure la categoria esiste già.",
                    )

                st.rerun()

        with st.container(border=True):
            st.markdown("#### Aggiungi parola chiave")

            keyword_col_1, keyword_col_2 = st.columns([1, 2])

            with keyword_col_1:
                selected_category = st.selectbox(
                    "Categoria",
                    category_names,
                    format_func=lambda name: (
                        f"{get_category_icon(name)} {name}"
                    ),
                    key="settings_keyword_category",
                )

            with keyword_col_2:
                new_keyword = st.text_input(
                    "Parola chiave",
                    placeholder="Es. BENNET, TIGOTÀ, AUTOGRILL...",
                    key="settings_new_keyword",
                )

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
                        f'Parola chiave "{new_keyword.strip().upper()}" '
                        f'aggiunta a "{selected_category}".',
                    )
                else:
                    st.session_state["keyword_feedback"] = (
                        "warning",
                        "La parola chiave è vuota oppure è già presente.",
                    )

                st.rerun()

        st.markdown("### Regole attuali")

        for category, category_data in categories.items():
            icon = str(category_data["icon"])
            keywords = list(category_data["keywords"])

            with st.expander(
                f"{icon} {category} · {len(keywords)} parole chiave"
            ):
                st.markdown(f"### {icon} {category}")

                buttons_col_1, buttons_col_2 = st.columns(2)

                edit_icon_key = "editing_icon_category"

                with buttons_col_1:
                    if st.session_state.get(edit_icon_key) != category:
                        if st.button(
                            "🎨 Cambia icona",
                            key=f"edit_icon_{category}",
                            use_container_width=True,
                        ):
                            st.session_state[edit_icon_key] = category
                            st.session_state[f"category_icon_{category}"] = icon
                            st.rerun()

                with buttons_col_2:
                    if category == "Altro":
                        st.info('La categoria "Altro" non può essere eliminata.')
                    else:
                        confirm_key = f"confirm_delete_category_{category}"

                        if st.session_state.get(confirm_key):
                            st.warning('I movimenti saranno spostati in "Altro".')

                            yes_col, no_col = st.columns(2)

                            with yes_col:
                                if st.button(
                                    "Elimina",
                                    key=f"delete_category_yes_{category}",
                                    use_container_width=True,
                                    type="primary",
                                ):
                                    deleted, reassigned = delete_category(category)
                                    st.session_state[confirm_key] = False

                                    if deleted:
                                        st.session_state["category_delete_feedback"] = (
                                            "success",
                                            f'Categoria "{category}" eliminata. '
                                            f"{reassigned} movimenti spostati in 'Altro'.",
                                        )
                                    else:
                                        st.session_state["category_delete_feedback"] = (
                                            "error",
                                            "Non è stato possibile eliminare la categoria.",
                                        )

                                    st.rerun()

                            with no_col:
                                if st.button(
                                    "Annulla",
                                    key=f"delete_category_no_{category}",
                                    use_container_width=True,
                                ):
                                    st.session_state[confirm_key] = False
                                    st.rerun()
                        else:
                            if st.button(
                                "🗑️ Elimina categoria",
                                key=f"delete_category_{category}",
                                use_container_width=True,
                            ):
                                st.session_state[confirm_key] = True
                                st.rerun()

                if st.session_state.get(edit_icon_key) == category:
                    st.divider()

                    selected_icon = render_icon_grid(
                        f"category_icon_{category}",
                        icon,
                        columns_count=10,
                    )

                    st.caption(
                        f"Anteprima nuova icona: {selected_icon} {category}"
                    )

                    save_col, cancel_col = st.columns(2)

                    with save_col:
                        if st.button(
                            "💾 Salva icona",
                            key=f"save_icon_{category}",
                            use_container_width=True,
                            type="primary",
                        ):
                            updated = update_category_icon(
                                category,
                                selected_icon,
                            )

                            st.session_state.pop(edit_icon_key, None)
                            st.session_state.pop(
                                f"category_icon_{category}",
                                None,
                            )

                            if updated:
                                st.session_state["icon_feedback"] = (
                                    "success",
                                    f'Icona di "{category}" aggiornata a {selected_icon}.',
                                )
                            else:
                                st.session_state["icon_feedback"] = (
                                    "warning",
                                    "Nessuna modifica da salvare.",
                                )

                            st.rerun()

                    with cancel_col:
                        if st.button(
                            "Annulla",
                            key=f"cancel_icon_{category}",
                            use_container_width=True,
                        ):
                            st.session_state.pop(edit_icon_key, None)
                            st.session_state.pop(
                                f"category_icon_{category}",
                                None,
                            )
                            st.rerun()

                st.markdown("##### Parole chiave")

                if not keywords:
                    st.caption("Nessuna parola chiave associata.")
                else:
                    for keyword in keywords:
                        keyword_col, delete_col = st.columns([5, 1])

                        with keyword_col:
                            st.markdown(f"`{keyword}`")

                        with delete_col:
                            if st.button(
                                "🗑️",
                                key=(
                                    f"delete_keyword_"
                                    f"{category}_{keyword}"
                                ),
                                help=f'Elimina "{keyword}"',
                                use_container_width=True,
                            ):
                                removed = remove_keyword_from_category(
                                    category,
                                    keyword,
                                )

                                if removed:
                                    st.session_state[
                                        "keyword_delete_feedback"
                                    ] = (
                                        "success",
                                        f'Parola chiave "{keyword}" '
                                        f'eliminata da "{category}".',
                                    )
                                else:
                                    st.session_state[
                                        "keyword_delete_feedback"
                                    ] = (
                                        "warning",
                                        "Non è stato possibile eliminare "
                                        "la parola chiave.",
                                    )

                                st.rerun()

        if st.button(
            "🔄 Aggiorna categorie automatiche",
            use_container_width=True,
        ):
            updated = recalculate_automatic_categories()

            st.session_state["recalculate_feedback"] = (
                "success",
                f"Categorie aggiornate. Movimenti modificati: {updated}.",
            )

            st.rerun()

    with tab_data:
        st.markdown("### Dati")

        db_path = DB_PATH.resolve()
        config_path = USER_CATEGORY_CONFIG_PATH.resolve()

        col_db, col_config = st.columns(2)

        with col_db:
            with st.container(border=True):
                st.markdown("#### Database")
                st.code(str(db_path))
                st.caption(
                    "Contiene i movimenti e le categorie assegnate."
                )

        with col_config:
            with st.container(border=True):
                st.markdown("#### Configurazione categorie")
                st.code(str(config_path))
                st.caption(
                    "Contiene icone e regole automatiche "
                    "personalizzate."
                )

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

            with open(backup_path, "rb") as backup_file:
                st.download_button(
                    "⬇️ Scarica backup",
                    data=backup_file,
                    file_name=backup_path.name,
                    mime="application/zip",
                    use_container_width=True,
                )

    with tab_info:
        st.markdown("## 💰 FinanceTracker")

        with st.container(border=True):
            st.markdown(f"**Versione:** {APP_VERSION}")
            st.markdown("**Database:** SQLite")
            st.markdown("**Framework:** Streamlit")
            st.markdown("**Sviluppatore:** Carlo La Sala")

        st.divider()

        st.markdown(
            """
            <div style="text-align:center; color:#94a3b8; line-height:1.7;">
                <strong>FinanceTracker</strong><br>
                Personal Finance Manager<br><br>
                © 2026 Carlo La Sala
            </div>
            """,
            unsafe_allow_html=True,
        )
