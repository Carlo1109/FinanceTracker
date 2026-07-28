import html
from pathlib import Path

import streamlit as st

from src.components.export_dialog import (
    open_export_confirm_dialog,
    render_pending_export_dialog,
)
from src.components.cards import (
    EXPENSE_COLOR,
    INCOME_COLOR,
    MUTED_COLOR,
    TEXT_COLOR,
    render_html,
    styled_panel,
)
from src.database.db import DB_PATH
from src.services.backup_service import create_backup, restore_backup
from src.services.categories import (
    USER_CATEGORY_CONFIG_PATH,
    add_category,
    add_keyword_to_category,
    delete_category,
    get_category_icon,
    load_category_definitions,
    remove_keyword_from_category,
    update_category_icon,
)
from src.services.settings_service import (
    VALID_ACCENTS,
    VALID_THEMES,
    get_accent,
    get_theme_mode,
    set_theme_preferences,
)
from src.services.movement_service import (
    delete_account,
    load_movements,
    recalculate_automatic_categories,
)
from src.theme.tokens import ACCENTS, THEMES, resolve_palette
from src.theme.style import apply_theme
from src.utils.export_excel import movements_export_filename
from src.utils.formatting import euro
from src.utils.version import get_app_version


APP_VERSION = get_app_version()
BACKUP_EXTENSIONS = {".zip"}

THEME_HINTS = {
    "dark": "Notturno",
    "light": "Diurno",
}

ACCENT_BLURBS = {
    "blue": "Oceano",
    "green": "Foresta",
    "amber": "Tramonto",
    "violet": "Aurora",
}

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


def _apply_appearance(theme_id: str, accent_id: str) -> None:
    set_theme_preferences(theme=theme_id, accent=accent_id)
    apply_theme(theme_id, accent_id)
    st.toast(
        f"Aspetto: {THEMES[theme_id].label} · {ACCENTS[accent_id].label}"
    )
    st.rerun()


def _render_appearance_hero(theme_id: str, accent_id: str) -> None:
    theme, accent = resolve_palette(theme_id, accent_id)
    render_html(
        f"""
        <div class="ft-appearance-hero">
          <div class="ft-appearance-hero-top">
            <div class="ft-appearance-brand">
              Finance<span>Tracker</span>
            </div>
            <div class="ft-appearance-chip">
              <span class="ft-appearance-chip-dot"></span>
              {THEMES[theme_id].label} · {ACCENTS[accent_id].label}
            </div>
          </div>
          <div class="ft-appearance-kpis">
            <div class="ft-appearance-kpi">
              <div class="ft-appearance-kpi-label">Saldo</div>
              <div class="ft-appearance-kpi-value">€ 2.480</div>
              <div class="ft-appearance-kpi-bar"><span></span></div>
            </div>
            <div class="ft-appearance-kpi">
              <div class="ft-appearance-kpi-label">Entrate</div>
              <div class="ft-appearance-kpi-value"
                   style="color:var(--ft-income)">+ € 890</div>
            </div>
            <div class="ft-appearance-kpi">
              <div class="ft-appearance-kpi-label">Uscite</div>
              <div class="ft-appearance-kpi-value"
                   style="color:var(--ft-danger)">− € 412</div>
            </div>
          </div>
        </div>
        """
    )


def _render_theme_card(theme_id: str, *, selected: bool, accent_hex: str) -> None:
    theme = THEMES[theme_id]
    selected_class = " is-selected" if selected else ""
    hint = "Selezionato" if selected else THEME_HINTS[theme_id]
    chrome_dot = (
        "rgba(15, 23, 42, 0.28)" if theme_id == "light" else "rgba(255, 255, 255, 0.35)"
    )
    chrome_bar = (
        "rgba(15, 23, 42, 0.06)" if theme_id == "light" else "rgba(0, 0, 0, 0.22)"
    )
    line = theme.border
    render_html(
        f"""
        <div class="ft-theme-card{selected_class}">
          <div class="ft-theme-card-window"
               style="background:linear-gradient(160deg,{theme.bg_0},{theme.bg_2});">
            <div class="ft-theme-card-chrome" style="background:{chrome_bar};">
              <span style="background:{chrome_dot};"></span>
              <span style="background:{chrome_dot};"></span>
              <span style="background:{chrome_dot};"></span>
            </div>
            <div class="ft-theme-card-body">
              <div class="ft-theme-card-nav"
                   style="background:{theme.panel};border:1px solid {theme.border};">
              </div>
              <div class="ft-theme-card-main">
                <div class="ft-theme-card-line"
                     style="background:{line};width:72%;"></div>
                <div class="ft-theme-card-line accent"
                     style="background:{accent_hex};width:42%;"></div>
                <div class="ft-theme-card-line"
                     style="background:{line};width:58%;"></div>
              </div>
            </div>
          </div>
          <div class="ft-theme-card-meta">
            <div class="ft-theme-card-title">{theme.label}</div>
            <div class="ft-theme-card-hint">{hint}</div>
          </div>
        </div>
        """
    )


def _render_accent_swatch(accent_id: str, *, selected: bool, theme_id: str) -> None:
    _, accent = resolve_palette(theme_id, accent_id)
    selected_class = " is-selected" if selected else ""
    blurb = ACCENT_BLURBS.get(accent_id, accent.label)
    render_html(
        f"""
        <div class="ft-accent-swatch{selected_class}">
          <div class="ft-accent-orb"
               style="--ft-orb-a:{accent.accent};--ft-orb-b:{accent.accent_strong};">
          </div>
          <div class="ft-accent-name">{accent.label}</div>
          <div style="font-size:11px;color:var(--ft-muted);margin-top:2px;">
            {blurb}
          </div>
        </div>
        """
    )


def _settings_section_header(
    title: str,
    *,
    chip: str | None = None,
) -> None:
    chip_html = ""
    if chip:
        chip_html = f"""
            <div class="ft-appearance-chip" style="width:fit-content;margin-bottom:10px;">
              <span class="ft-appearance-chip-dot"></span>
              {html.escape(chip)}
            </div>
        """
    render_html(
        f"""
        <div style="margin-bottom:4px;">
          {chip_html}
          <div style="
              font-family:Fraunces,Georgia,serif;
              font-size:1.2rem;
              font-weight:700;
              color:var(--ft-text);
              letter-spacing:-0.02em;
          ">{html.escape(title)}</div>
        </div>
        """
    )


def show_feedback(state_key: str) -> None:
    if state_key not in st.session_state:
        return

    feedback_type, feedback_message = st.session_state.pop(state_key)

    if feedback_type == "success":
        st.toast(feedback_message)
    elif feedback_type == "error":
        st.error(feedback_message)
    else:
        st.warning(feedback_message)


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
                    width="stretch",
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
    st.title("Impostazioni")
    st.caption("Gestisci configurazioni, dati e informazioni dell'app.")
    render_pending_export_dialog()

    df = load_movements()
    categories = load_category_definitions()

    tab_appearance, tab_accounts, tab_categories, tab_data, tab_info = st.tabs(
        ["🎨 Aspetto", "💳 Conti", "🏷️ Categorie", "💾 Dati", "ℹ️ Info"]
    )

    with tab_appearance:
        st.markdown("### Aspetto")
        st.caption(
            "Scegli atmosfera e colori: restano salvati su questo PC."
        )

        current_theme = get_theme_mode()
        current_accent = get_accent()
        _, resolved_accent = resolve_palette(current_theme, current_accent)
        current_accent_hex = resolved_accent.accent

        with styled_panel():
            _render_appearance_hero(current_theme, current_accent)

            st.markdown('<div class="ft-appearance-label">Tema</div>', unsafe_allow_html=True)
            theme_cols = st.columns(2, gap="medium")
            for index, theme_id in enumerate(VALID_THEMES):
                with theme_cols[index]:
                    is_selected = theme_id == current_theme
                    _render_theme_card(
                        theme_id,
                        selected=is_selected,
                        accent_hex=current_accent_hex,
                    )
                    if st.button(
                        "In uso" if is_selected else "Seleziona",
                        key=f"appearance_theme_{theme_id}",
                        width="stretch",
                        type="primary" if is_selected else "secondary",
                        disabled=is_selected,
                    ):
                        _apply_appearance(theme_id, current_accent)

            st.markdown(
                '<div class="ft-appearance-label" style="margin-top:18px;">'
                "Colori</div>",
                unsafe_allow_html=True,
            )
            accent_cols = st.columns(len(VALID_ACCENTS), gap="small")
            for index, accent_id in enumerate(VALID_ACCENTS):
                with accent_cols[index]:
                    is_selected = accent_id == current_accent
                    _render_accent_swatch(
                        accent_id,
                        selected=is_selected,
                        theme_id=current_theme,
                    )
                    if st.button(
                        "In uso" if is_selected else "Seleziona",
                        key=f"appearance_accent_{accent_id}",
                        width="stretch",
                        type="primary" if is_selected else "secondary",
                        disabled=is_selected,
                    ):
                        _apply_appearance(current_theme, accent_id)

    with tab_accounts:
        st.markdown("### Conti collegati")
        st.caption(
            "Rimuovere un conto cancella definitivamente dal database "
            "tutti i suoi movimenti. Utile per pulizia o per reimportare."
        )
        show_feedback("account_delete_feedback")

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
                total = float(account_df["importo"].sum())
                confirm_key = f"confirm_delete_account_{account}"
                balance_color = (
                    INCOME_COLOR if total >= 0 else EXPENSE_COLOR
                )
                safe_account = html.escape(str(account))

                with styled_panel():
                    render_html(
                        f"""
                        <div style="
                            display:flex;
                            justify-content:space-between;
                            align-items:flex-start;
                            gap:16px;
                            flex-wrap:wrap;
                            margin-bottom:4px;
                        ">
                          <div>
                            <div class="ft-appearance-chip" style="
                                width:fit-content;
                                margin-bottom:10px;
                            ">
                              <span class="ft-appearance-chip-dot"></span>
                              Conto
                            </div>
                            <div style="
                                font-family:Fraunces,Georgia,serif;
                                font-size:clamp(26px, 2.4vw, 32px);
                                font-weight:700;
                                color:{TEXT_COLOR};
                                line-height:1.1;
                                letter-spacing:-0.02em;
                            ">{safe_account}</div>
                            <div style="
                                margin-top:6px;
                                font-size:13px;
                                color:{MUTED_COLOR};
                                font-weight:650;
                            ">{movements_count} movimenti</div>
                          </div>
                          <div style="text-align:right;">
                            <div style="
                                font-size:11px;
                                font-weight:650;
                                letter-spacing:0.08em;
                                text-transform:uppercase;
                                color:{MUTED_COLOR};
                            ">Saldo movimenti</div>
                            <div style="
                                margin-top:6px;
                                font-family:Fraunces,Georgia,serif;
                                font-size:clamp(24px, 2.2vw, 30px);
                                font-weight:700;
                                color:{balance_color};
                                line-height:1.1;
                            ">{euro(total)}</div>
                          </div>
                        </div>
                        """
                    )

                    if st.session_state.get(confirm_key):
                        st.warning(
                            f"Stai per eliminare **{movements_count}** movimenti "
                            f"del conto **{account}**. Operazione irreversibile "
                            "(salvo un backup)."
                        )
                        if st.button(
                            f"Scarica prima i {movements_count} movimenti (Excel)",
                            width="stretch",
                            key=f"export_before_delete_open_{account}",
                        ):
                            open_export_confirm_dialog(
                                account_df,
                                file_name=movements_export_filename(
                                    prefix="conto",
                                    account=account,
                                ),
                                context_label=f"Conto {account}",
                                dialog_key=f"before_delete_{account}",
                            )
                            st.rerun()

                        typed = st.text_input(
                            f'Digita "{account}" per confermare',
                            key=f"type_delete_account_{account}",
                            placeholder=account,
                        )
                        can_delete = typed.strip() == account
                        if can_delete:
                            st.caption("Nome corretto — puoi eliminare il conto.")
                        else:
                            st.caption(
                                f'Il pulsante si attiva solo digitando esattamente '
                                f'"{account}".'
                            )

                        yes_col, no_col = st.columns(2)
                        with yes_col:
                            if st.button(
                                "Elimina conto",
                                key=f"delete_account_yes_{account}",
                                width="stretch",
                                type="primary" if can_delete else "secondary",
                                disabled=not can_delete,
                            ):
                                deleted = delete_account(account)
                                st.session_state[confirm_key] = False
                                st.session_state["account_delete_feedback"] = (
                                    "success",
                                    f'Conto "{account}" rimosso. '
                                    f"{deleted} movimenti eliminati.",
                                )
                                st.rerun()

                        with no_col:
                            if st.button(
                                "Annulla",
                                key=f"delete_account_no_{account}",
                                width="stretch",
                            ):
                                st.session_state[confirm_key] = False
                                st.rerun()
                    else:
                        action_col, export_col = st.columns([1.4, 1])
                        with action_col:
                            if st.button(
                                "🗑️ Rimuovi conto",
                                key=f"delete_account_{account}",
                                width="stretch",
                            ):
                                st.session_state[confirm_key] = True
                                st.rerun()
                        with export_col:
                            if st.button(
                                "Esporta Excel",
                                type="secondary",
                                key=f"export_account_open_{account}",
                                width="stretch",
                            ):
                                open_export_confirm_dialog(
                                    account_df,
                                    file_name=movements_export_filename(
                                        prefix="conto",
                                        account=account,
                                    ),
                                    context_label=f"Conto {account}",
                                    dialog_key=f"account_{account}",
                                )
                                st.rerun()

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

        with styled_panel():
            _settings_section_header("Crea nuova categoria", chip="Nuova")

            create_col_1, create_col_2 = st.columns([2, 1])

            with create_col_1:
                new_category = st.text_input(
                    "Nome categoria",
                    placeholder="Es. Animali, Regali, Formazione...",
                    key="settings_new_category",
                )

            with create_col_2:
                render_html(
                    f"""
                    <div style="
                        font-size:12px;
                        font-weight:650;
                        color:var(--ft-muted);
                        letter-spacing:0.06em;
                        text-transform:uppercase;
                        margin-bottom:6px;
                    ">Icona</div>
                    <div style="
                        font-size:44px;
                        text-align:center;
                        padding:8px 0;
                        border-radius:14px;
                        background:rgba(var(--ft-accent-rgb),0.10);
                        border:1px solid var(--ft-border);
                    ">
                        {st.session_state.get(
                            "settings_new_category_icon",
                            "🛒",
                        )}
                    </div>
                    """
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
                width="stretch",
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

        with styled_panel():
            _settings_section_header("Aggiungi parola chiave", chip="Regole")

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
                width="stretch",
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
        st.caption(f"{len(categories)} categorie configurate")

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
                            width="stretch",
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
                            category_count = int(
                                (df["categoria"] == category).sum()
                            ) if not df.empty else 0
                            st.warning(
                                f'**{category_count}** movimenti saranno '
                                'spostati in "Altro".'
                            )

                            yes_col, no_col = st.columns(2)

                            with yes_col:
                                if st.button(
                                    "Elimina",
                                    key=f"delete_category_yes_{category}",
                                    width="stretch",
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
                                    width="stretch",
                                ):
                                    st.session_state[confirm_key] = False
                                    st.rerun()
                        else:
                            if st.button(
                                "🗑️ Elimina categoria",
                                key=f"delete_category_{category}",
                                width="stretch",
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
                            width="stretch",
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
                            width="stretch",
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
                            render_html(
                                f"""
                                <div style="
                                    display:inline-flex;
                                    align-items:center;
                                    padding:6px 12px;
                                    border-radius:999px;
                                    background:rgba(var(--ft-accent-rgb),0.12);
                                    border:1px solid rgba(var(--ft-accent-rgb),0.28);
                                    color:var(--ft-accent-strong);
                                    font-size:0.86rem;
                                    font-weight:650;
                                    letter-spacing:0.02em;
                                ">{html.escape(keyword)}</div>
                                """
                            )

                        with delete_col:
                            if st.button(
                                "🗑️",
                                key=(
                                    f"delete_keyword_"
                                    f"{category}_{keyword}"
                                ),
                                width="stretch",
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

        with styled_panel():
            _settings_section_header(
                "Ricalcolo automatico",
                chip="Sync",
            )
            st.caption(
                "Riapplica le regole alle descrizioni dei movimenti "
                "già importati."
            )
            if st.button(
                "🔄 Aggiorna categorie automatiche",
                width="stretch",
                type="primary",
            ):
                updated = recalculate_automatic_categories()

                st.session_state["recalculate_feedback"] = (
                    "success",
                    f"Categorie aggiornate. Movimenti modificati: {updated}.",
                )

                st.rerun()

    with tab_data:
        st.markdown("### Dati")
        st.caption("Percorsi locali e backup di sicurezza.")

        db_path = DB_PATH.resolve()
        config_path = USER_CATEGORY_CONFIG_PATH.resolve()

        col_db, col_config = st.columns(2)

        with col_db:
            with styled_panel():
                _settings_section_header("Database", chip="SQLite")
                st.code(str(db_path))
                st.caption(
                    "Contiene i movimenti e le categorie assegnate."
                )

        with col_config:
            with styled_panel():
                _settings_section_header("Configurazione categorie", chip="JSON")
                st.code(str(config_path))
                st.caption(
                    "Contiene icone e regole automatiche "
                    "personalizzate."
                )

        movements_count = 0 if df.empty else len(df)
        with styled_panel():
            render_html(
                f"""
                <div class="ft-appearance-chip" style="width:fit-content;margin-bottom:10px;">
                  <span class="ft-appearance-chip-dot"></span>
                  Archivio
                </div>
                <div style="
                    font-family:Fraunces,Georgia,serif;
                    font-size:0.95rem;
                    color:var(--ft-muted);
                    margin-bottom:6px;
                ">Movimenti salvati</div>
                <div style="
                    font-family:Fraunces,Georgia,serif;
                    font-size:2rem;
                    font-weight:700;
                    color:var(--ft-text);
                    letter-spacing:-0.03em;
                ">{movements_count}</div>
                """
            )

        with styled_panel():
            _settings_section_header("Backup", chip="Sicurezza")
            st.caption(
                "Esporta o ripristina database e categorie in un file zip."
            )

            if st.button(
                "📦 Crea backup completo",
                width="stretch",
                type="primary",
            ):
                backup_path = create_backup()
                st.toast("Backup creato correttamente.")

                with open(backup_path, "rb") as backup_file:
                    st.download_button(
                        "⬇️ Scarica backup",
                        data=backup_file,
                        file_name=backup_path.name,
                        mime="application/zip",
                        width="stretch",
                    )

            st.markdown("#### Ripristina backup")
            st.caption(
                "Sostituisce database e categorie con quelli del file zip. "
                "Se la cartella sembra vuota, passa a 'Tutti i file' "
                "nel dialog oppure trascina lo zip qui."
            )

            uploaded_backup = st.file_uploader(
                "Seleziona un backup (.zip)",
                type=None,
                key="restore_backup_uploader",
            )

            if uploaded_backup is not None:
                suffix = Path(uploaded_backup.name).suffix.lower()
                if suffix not in BACKUP_EXTENSIONS:
                    st.error("Formato non supportato. Usa un file backup .zip.")
                    uploaded_backup = None

            if uploaded_backup is not None:
                if st.button(
                    "♻️ Ripristina backup",
                    width="stretch",
                    type="primary",
                ):
                    success, message = restore_backup(uploaded_backup)

                    if success:
                        st.toast(message)
                        st.rerun()
                    else:
                        st.error(message)

    with tab_info:
        st.markdown("### FinanceTracker")
        st.caption(
            "App desktop offline: i tuoi dati restano sul computer, "
            "senza account e senza cloud."
        )

        with styled_panel():
            render_html(
                f"""
                <div class="ft-appearance-chip" style="width:fit-content;margin-bottom:14px;">
                  <span class="ft-appearance-chip-dot"></span>
                  Locale
                </div>
                <div style="
                    font-family:Fraunces,Georgia,serif;
                    font-size:1.35rem;
                    font-weight:700;
                    color:var(--ft-text);
                    letter-spacing:-0.02em;
                    margin-bottom:18px;
                ">FinanceTracker</div>
                <div style="display:grid;gap:12px;">
                  <div style="display:flex;justify-content:space-between;gap:12px;border-bottom:1px solid var(--ft-border);padding-bottom:10px;">
                    <span style="color:var(--ft-muted);">Versione</span>
                    <span style="color:var(--ft-text);font-weight:650;">{html.escape(APP_VERSION)}</span>
                  </div>
                  <div style="display:flex;justify-content:space-between;gap:12px;border-bottom:1px solid var(--ft-border);padding-bottom:10px;">
                    <span style="color:var(--ft-muted);">Privacy</span>
                    <span style="color:var(--ft-text);font-weight:650;">Solo locale</span>
                  </div>
                  <div style="display:flex;justify-content:space-between;gap:12px;border-bottom:1px solid var(--ft-border);padding-bottom:10px;">
                    <span style="color:var(--ft-muted);">Connessione</span>
                    <span style="color:var(--ft-text);font-weight:650;">Non richiesta</span>
                  </div>
                  <div style="display:flex;justify-content:space-between;gap:12px;border-bottom:1px solid var(--ft-border);padding-bottom:10px;">
                    <span style="color:var(--ft-muted);">Database</span>
                    <span style="color:var(--ft-text);font-weight:650;">SQLite sul dispositivo</span>
                  </div>
                  <div style="display:flex;justify-content:space-between;gap:12px;">
                    <span style="color:var(--ft-muted);">Sviluppatore</span>
                    <span style="color:var(--ft-text);font-weight:650;">Carlo La Sala</span>
                  </div>
                </div>
                """
            )

        render_html(
            """
            <div style="
                text-align:center;
                color:var(--ft-muted);
                line-height:1.7;
                margin-top:8px;
                padding:18px 8px;
            ">
                <strong style="color:var(--ft-text);">FinanceTracker</strong><br>
                Personal Finance Manager<br><br>
                © 2026 Carlo La Sala
            </div>
            """
        )
