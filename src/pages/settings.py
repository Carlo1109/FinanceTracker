import html
import json
from pathlib import Path

import streamlit as st

from src.components.export_dialog import (
    open_export_confirm_dialog,
    render_pending_export_dialog,
)
from src.components.cards import (
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
from src.theme.colors import get_category_color
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

_OPEN_CATEGORY_KEY = "settings_open_category"
_NEW_CATEGORY_KEY = "settings_new_category_open"
_OPEN_ACCOUNT_KEY = "settings_open_account"
_ICON_GRID_KEY = "settings_icon_grid_open"
_DELETE_CATEGORY_KEY = "settings_confirm_delete_category"


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


def _render_copyable_path(path: str, *, key: str) -> None:
    path_text = str(path)
    block_id = f"ft-copy-{key}"
    st.html(
        f"""
        <div class="ft-copy-path" id="{html.escape(block_id)}">
          <code class="ft-copy-path-value">{html.escape(path_text)}</code>
          <button type="button" class="ft-copy-path-btn">Copia</button>
        </div>
        <script>
        (function () {{
          const root = document.getElementById({json.dumps(block_id)});
          if (!root) return;
          const btn = root.querySelector(".ft-copy-path-btn");
          const text = {json.dumps(path_text)};
          if (!btn || btn._ftCopyBound) return;
          btn._ftCopyBound = true;
          btn.addEventListener("click", async function () {{
            let copied = false;
            try {{
              await navigator.clipboard.writeText(text);
              copied = true;
            }} catch (error) {{
              const input = document.createElement("textarea");
              input.value = text;
              input.setAttribute("readonly", "");
              input.style.position = "fixed";
              input.style.left = "-9999px";
              document.body.appendChild(input);
              input.select();
              copied = document.execCommand("copy");
              input.remove();
            }}
            if (!copied) return;
            btn.textContent = "Copiato";
            btn.classList.add("is-copied");
            setTimeout(function () {{
              btn.textContent = "Copia";
              btn.classList.remove("is-copied");
            }}, 1400);
          }});
        }})();
        </script>
        """,
        unsafe_allow_javascript=True,
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


def _category_rgb(color: str) -> str:
    raw = str(color).removeprefix("#")
    if len(raw) != 6:
        return "var(--ft-accent-rgb)"
    return (
        f"{int(raw[0:2], 16)}, "
        f"{int(raw[2:4], 16)}, "
        f"{int(raw[4:6], 16)}"
    )


def _close_category_dialog() -> None:
    name = st.session_state.pop(_OPEN_CATEGORY_KEY, None)
    st.session_state.pop(_ICON_GRID_KEY, None)
    st.session_state.pop(_DELETE_CATEGORY_KEY, None)
    if name:
        st.session_state.pop(f"category_icon_{name}", None)
        st.session_state.pop(f"settings_add_kw_{name}", None)


def _close_new_category_dialog() -> None:
    st.session_state.pop(_NEW_CATEGORY_KEY, None)


def _close_account_dialog() -> None:
    st.session_state.pop(_OPEN_ACCOUNT_KEY, None)


def _render_pending_settings_dialogs(df, categories: dict) -> None:
    if st.session_state.get(_NEW_CATEGORY_KEY):
        _new_category_dialog()
        return
    open_category = st.session_state.get(_OPEN_CATEGORY_KEY)
    if open_category:
        _category_edit_dialog(str(open_category), df, categories)
        return
    open_account = st.session_state.get(_OPEN_ACCOUNT_KEY)
    if open_account:
        _account_delete_dialog(str(open_account), df)
        return


@st.dialog("Nuova categoria", width="large", on_dismiss=_close_new_category_dialog)
def _new_category_dialog() -> None:
    render_html(
        """
        <div class="ft-export-dialog" style="padding:2px 0 8px 0;">
          <div class="ft-appearance-chip" style="width:fit-content;">
            <span class="ft-appearance-chip-dot"></span>
            Personalizzata
          </div>
          <div style="
              margin-top:12px;
              font-family:Fraunces,Georgia,serif;
              font-size:clamp(22px, 2.2vw, 28px);
              font-weight:700;
              color:var(--ft-text);
              line-height:1.2;
          ">Crea una categoria</div>
        </div>
        """
    )
    new_category = st.text_input(
        "Nome",
        placeholder="Es. Animali, Regali, Formazione...",
        key="settings_new_category",
    )
    new_category_icon = render_icon_grid(
        "settings_new_category_icon",
        "🛒",
        columns_count=8,
    )
    st.caption(
        f"Anteprima: {new_category_icon} "
        f"{(new_category or '').strip() or 'Nuova categoria'}"
    )
    if st.button("Crea categoria", type="primary", width="stretch"):
        created = add_category(new_category, new_category_icon)
        if created:
            st.session_state["category_feedback"] = (
                "success",
                f'Categoria "{new_category.strip()}" creata '
                f"con l'icona {new_category_icon}.",
            )
            _close_new_category_dialog()
        else:
            st.session_state["category_feedback"] = (
                "warning",
                "Il nome è vuoto oppure la categoria esiste già.",
            )
        st.rerun()


@st.dialog("Categoria", width="large", on_dismiss=_close_category_dialog)
def _category_edit_dialog(category: str, df, categories: dict) -> None:
    data = categories.get(category)
    if not data:
        st.warning("Categoria non trovata.")
        return

    icon = str(data["icon"])
    keywords = list(data["keywords"])
    used = (
        int((df["categoria"] == category).sum())
        if df is not None and not df.empty
        else 0
    )
    cat_rgb = _category_rgb(get_category_color(category, categories))

    render_html(
        f"""
        <div class="ft-export-dialog" style="padding:2px 0 10px 0;">
          <div class="ft-appearance-chip" style="
              width:fit-content;
              --ft-cat-rgb:{cat_rgb};
              background:rgba(var(--ft-cat-rgb),0.16);
              color:var(--ft-text);
          ">
            <span class="ft-movement-cat-dot"></span>
            {html.escape(icon)} {html.escape(category)}
          </div>
          <div style="
              margin-top:10px;
              font-size:13px;
              color:var(--ft-muted);
              font-weight:650;
          ">{used} movimenti · {len(keywords)} parole chiave</div>
        </div>
        """
    )

    if st.session_state.get(_ICON_GRID_KEY):
        selected_icon = render_icon_grid(
            f"category_icon_{category}",
            icon,
            columns_count=8,
        )
        save_col, cancel_col = st.columns(2)
        with save_col:
            if st.button("Salva icona", type="primary", width="stretch"):
                updated = update_category_icon(category, selected_icon)
                st.session_state.pop(_ICON_GRID_KEY, None)
                if updated:
                    st.session_state["icon_feedback"] = (
                        "success",
                        f'Icona di "{category}" aggiornata a {selected_icon}.',
                    )
                st.rerun()
        with cancel_col:
            if st.button("Annulla", width="stretch"):
                st.session_state.pop(_ICON_GRID_KEY, None)
                st.rerun()
        return

    if st.button("Cambia icona", width="stretch", type="secondary"):
        st.session_state[_ICON_GRID_KEY] = True
        st.session_state[f"category_icon_{category}"] = icon
        st.rerun()

    new_keyword = st.text_input(
        "Nuova parola chiave",
        placeholder="Es. BENNET, TIGOTÀ, AUTOGRILL...",
        key=f"settings_add_kw_{category}",
    )
    if st.button("Aggiungi parola chiave", width="stretch", type="primary"):
        added = add_keyword_to_category(category, new_keyword)
        if added:
            st.session_state["keyword_feedback"] = (
                "success",
                f'Parola chiave "{new_keyword.strip().upper()}" '
                f'aggiunta a "{category}".',
            )
            st.session_state[f"settings_add_kw_{category}"] = ""
        else:
            st.session_state["keyword_feedback"] = (
                "warning",
                "La parola chiave è vuota oppure è già presente.",
            )
        st.rerun()

    if not keywords:
        st.caption("Nessuna parola chiave associata.")
    else:
        for keyword in keywords:
            chip_col, delete_col = st.columns([5, 1])
            with chip_col:
                render_html(
                    f"""
                    <div class="ft-keyword-chip">
                      {html.escape(keyword)}
                    </div>
                    """
                )
            with delete_col:
                if st.button(
                    "✕",
                    key=f"delete_keyword_{category}_{keyword}",
                    width="stretch",
                ):
                    removed = remove_keyword_from_category(category, keyword)
                    if removed:
                        st.session_state["keyword_delete_feedback"] = (
                            "success",
                            f'Parola chiave "{keyword}" '
                            f'eliminata da "{category}".',
                        )
                    st.rerun()

    if category == "Altro":
        st.caption('La categoria "Altro" non può essere eliminata.')
        return

    if st.session_state.get(_DELETE_CATEGORY_KEY):
        st.warning(
            f"{used} movimenti saranno spostati in «Altro»."
        )
        yes_col, no_col = st.columns(2)
        with yes_col:
            if st.button("Elimina", type="primary", width="stretch"):
                deleted, reassigned = delete_category(category)
                _close_category_dialog()
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
            if st.button("Annulla eliminazione", width="stretch"):
                st.session_state.pop(_DELETE_CATEGORY_KEY, None)
                st.rerun()
    elif st.button("Elimina categoria", width="stretch"):
        st.session_state[_DELETE_CATEGORY_KEY] = True
        st.rerun()


@st.dialog("Rimuovi conto", on_dismiss=_close_account_dialog)
def _account_delete_dialog(account: str, df) -> None:
    account_df = df[df["account"] == account] if df is not None else df
    movements_count = 0 if account_df is None or account_df.empty else len(account_df)
    render_html(
        f"""
        <div class="ft-export-dialog" style="padding:2px 0 8px 0;">
          <div class="ft-appearance-chip" style="width:fit-content;">
            <span class="ft-appearance-chip-dot"></span>
            Irreversibile
          </div>
          <div style="
              margin-top:12px;
              font-family:Fraunces,Georgia,serif;
              font-size:clamp(22px, 2.2vw, 28px);
              font-weight:700;
              color:var(--ft-text);
              line-height:1.2;
          ">{html.escape(account)}</div>
          <div style="
              margin-top:8px;
              font-size:13px;
              line-height:1.45;
              color:var(--ft-muted);
          ">
            Elimina {movements_count} movimenti di questo conto.
            Esporta prima se ti serve una copia.
          </div>
        </div>
        """
    )
    if movements_count and st.button(
        f"Scarica prima i {movements_count} movimenti",
        width="stretch",
        type="secondary",
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
        _close_account_dialog()
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
        st.caption(f'Scrivi esattamente "{account}" per attivare l\'eliminazione.')

    yes_col, no_col = st.columns(2)
    with yes_col:
        if st.button(
            "Elimina conto",
            width="stretch",
            type="primary" if can_delete else "secondary",
            disabled=not can_delete,
        ):
            deleted = delete_account(account)
            _close_account_dialog()
            st.session_state["account_delete_feedback"] = (
                "success",
                f'Conto "{account}" rimosso. {deleted} movimenti eliminati.',
            )
            st.rerun()
    with no_col:
        if st.button("Annulla", width="stretch"):
            _close_account_dialog()
            st.rerun()


def show_settings() -> None:
    st.title("Impostazioni")
    st.caption("Aspetto, conti, categorie e dati — tutto su questo PC.")
    render_pending_export_dialog()

    df = load_movements()
    categories = load_category_definitions()
    _render_pending_settings_dialogs(df, categories)

    show_feedback("account_delete_feedback")
    show_feedback("category_feedback")
    show_feedback("keyword_feedback")
    show_feedback("keyword_delete_feedback")
    show_feedback("icon_feedback")
    show_feedback("category_delete_feedback")
    show_feedback("recalculate_feedback")

    tab_appearance, tab_accounts, tab_categories, tab_data, tab_info = st.tabs(
        ["Aspetto", "Conti", "Categorie", "Dati", "Info"]
    )

    with tab_appearance:
        st.caption("Tema e colori restano salvati su questo PC.")

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
        st.caption(
            "Rimuovere un conto cancella i suoi movimenti dal database."
        )

        if df.empty:
            render_html(
                """
                <div class="ft-movement-empty">
                    Nessun conto. Importa o aggiungi un movimento.
                </div>
                """
            )
        else:
            accounts = sorted(df["account"].dropna().unique().tolist())
            for account in accounts:
                account_df = df[df["account"] == account]
                movements_count = len(account_df)
                total = float(account_df["importo"].sum())
                tone = "income" if total >= 0 else "expense"
                with styled_panel(kind="settings"):
                    body_col, amount_col, export_col, action_col = st.columns(
                        [3.4, 1.3, 1.1, 1.15],
                        vertical_alignment="center",
                    )
                    with body_col:
                        render_html(
                            f"""
                            <div class="ft-settings-row">
                              <span class="ft-movement-tone is-{tone}" hidden></span>
                              <div class="ft-movement-title ft-settings-account">
                                {html.escape(str(account))}
                              </div>
                              <div class="ft-movement-meta">
                                {movements_count} movimenti
                              </div>
                            </div>
                            """
                        )
                    with amount_col:
                        render_html(
                            f"""
                            <div class="ft-movement-amount is-{tone}">
                              {euro(total)}
                            </div>
                            """
                        )
                    with export_col:
                        if st.button(
                            "Esporta",
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
                    with action_col:
                        if st.button(
                            "Rimuovi",
                            key=f"delete_account_{account}",
                            width="stretch",
                        ):
                            st.session_state[_OPEN_ACCOUNT_KEY] = account
                            st.rerun()

    with tab_categories:
        st.caption(
            "Icone e parole chiave per la categorizzazione automatica."
        )
        actions, _ = st.columns([1.2, 2.8])
        with actions:
            if st.button(
                "Nuova categoria",
                type="primary",
                width="stretch",
                key="open_new_category",
            ):
                st.session_state[_NEW_CATEGORY_KEY] = True
                st.rerun()

        st.caption(f"{len(categories)} categorie")
        for category, category_data in categories.items():
            icon = str(category_data["icon"])
            keywords = list(category_data["keywords"])
            used = (
                int((df["categoria"] == category).sum())
                if not df.empty
                else 0
            )
            cat_rgb = _category_rgb(
                get_category_color(category, categories)
            )
            with styled_panel(kind="settings"):
                body_col, action_col = st.columns(
                    [4.6, 1.15],
                    vertical_alignment="center",
                )
                with body_col:
                    render_html(
                        f"""
                        <div class="ft-settings-row"
                             style="--ft-cat-rgb:{cat_rgb};">
                          <div class="ft-movement-title">
                            {html.escape(icon)} {html.escape(category)}
                          </div>
                          <div class="ft-movement-meta">
                            <span class="ft-movement-cat">
                              <span class="ft-movement-cat-dot"></span>
                              {len(keywords)} regole
                            </span>
                            <span>{used} movimenti</span>
                          </div>
                        </div>
                        """
                    )
                with action_col:
                    if st.button(
                        "Apri",
                        key=f"open_cat_{category}",
                        width="stretch",
                        type="secondary",
                    ):
                        st.session_state[_OPEN_CATEGORY_KEY] = category
                        st.rerun()

        with styled_panel(kind="settings"):
            rec_col, btn_col = st.columns(
                [3.4, 1.6],
                vertical_alignment="center",
            )
            with rec_col:
                render_html(
                    """
                    <div class="ft-settings-row">
                      <div class="ft-movement-title">Ricalcolo automatico</div>
                      <div class="ft-movement-meta">
                        Riapplica le regole alle descrizioni già importate.
                      </div>
                    </div>
                    """
                )
            with btn_col:
                if st.button(
                    "Aggiorna",
                    width="stretch",
                    type="primary",
                    key="recalculate_categories",
                ):
                    updated = recalculate_automatic_categories()
                    st.session_state["recalculate_feedback"] = (
                        "success",
                        f"Categorie aggiornate. "
                        f"Movimenti modificati: {updated}.",
                    )
                    st.rerun()

    with tab_data:
        st.caption("Percorsi locali e backup di sicurezza.")

        db_path = DB_PATH.resolve()
        config_path = USER_CATEGORY_CONFIG_PATH.resolve()

        col_db, col_config = st.columns(2)

        with col_db:
            with styled_panel():
                _settings_section_header("Database", chip="SQLite")
                _render_copyable_path(str(db_path), key="db")
                st.caption(
                    "Contiene i movimenti e le categorie assegnate."
                )

        with col_config:
            with styled_panel():
                _settings_section_header("Configurazione categorie", chip="JSON")
                _render_copyable_path(str(config_path), key="categories")
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
                        type="primary",
                    )

            st.caption(
                "Ripristino: sostituisce database e categorie. "
                "Se la cartella sembra vuota, scegli «Tutti i file» "
                "oppure trascina lo zip qui."
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
        st.caption(
            "App desktop offline: dati sul computer, senza account e senza cloud."
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
