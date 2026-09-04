import html
from datetime import date

import pandas as pd
import streamlit as st

from src.components.cards import (
    EXPENSE_COLOR,
    INCOME_COLOR,
    INVESTMENT_COLOR,
    render_html,
    render_kpi_card,
    render_section_title,
    styled_panel,
)
from src.components.export_dialog import (
    open_export_confirm_dialog,
    render_pending_export_dialog,
)
from src.components.navigation import switch_to
from src.services.analytics import (
    INVESTMENT_CATEGORY,
    calculate_financial_metrics,
    is_transfer_category,
)
from src.services.categories import (
    add_keyword_to_category,
    get_category_icon,
    get_category_names,
    load_category_definitions,
    suggest_keyword_from_text,
)
from src.theme.colors import get_category_color
from src.services.movement_service import (
    delete_movement,
    load_movements,
    recalculate_automatic_categories,
    split_movement,
    update_movement,
)
from src.utils.export_excel import (
    movements_export_filename,
)
from src.utils.formatting import euro, signed_euro


_MOVEMENTS_TOAST_KEY = "movements_toast"
_KEYWORD_SUGGEST_KEY = "keyword_suggest"
_KEYWORD_EDIT_KEY = "keyword_suggest_edit"
_OPEN_MOVEMENT_KEY = "open_movement_id"
_LIST_LIMIT_KEY = "movements_list_limit"
_LIST_FILTER_KEY = "movements_list_filter"
_LIST_PAGE_SIZE = 40


def _queue_toast(message: str) -> None:
    """Salva il toast e mostralo dopo il rerun (altrimenti sparisce subito)."""
    st.session_state[_MOVEMENTS_TOAST_KEY] = message


def _show_queued_toast() -> None:
    message = st.session_state.pop(_MOVEMENTS_TOAST_KEY, None)
    if message:
        st.toast(message, duration=4)


def _clear_movement_widget_state(movement_id: int) -> None:
    suffix = f"_{movement_id}"
    infix = f"_{movement_id}_"
    for key in list(st.session_state.keys()):
        if key.endswith(suffix) or infix in str(key):
            st.session_state.pop(key, None)


def _resolve_list_limit(filter_signature: tuple) -> int:
    if st.session_state.get(_LIST_FILTER_KEY) != filter_signature:
        st.session_state[_LIST_FILTER_KEY] = filter_signature
        st.session_state[_LIST_LIMIT_KEY] = _LIST_PAGE_SIZE
    return int(st.session_state.get(_LIST_LIMIT_KEY) or _LIST_PAGE_SIZE)


def _open_movement_dialog(movement_id: int) -> None:
    current = st.session_state.get(_OPEN_MOVEMENT_KEY)
    if current is not None and int(current) != movement_id:
        _clear_movement_widget_state(int(current))
    st.session_state[_OPEN_MOVEMENT_KEY] = movement_id


def _close_movement_dialog() -> None:
    current = st.session_state.pop(_OPEN_MOVEMENT_KEY, None)
    if current is not None:
        _clear_movement_widget_state(int(current))


def _render_pending_movement_dialog(categories: list[str]) -> None:
    movement_id = st.session_state.get(_OPEN_MOVEMENT_KEY)
    if movement_id is None:
        return
    _movement_edit_dialog(int(movement_id), categories)


def _queue_keyword_suggestion(
    description: str,
    category: str,
) -> None:
    suggested = suggest_keyword_from_text(description, category)
    if not suggested:
        return
    st.session_state[_KEYWORD_SUGGEST_KEY] = {
        "keyword": suggested,
        "category": category,
        "sample": description,
    }
    st.session_state[_KEYWORD_EDIT_KEY] = suggested


def _close_keyword_dialog() -> None:
    st.session_state.pop(_KEYWORD_SUGGEST_KEY, None)
    st.session_state.pop(_KEYWORD_EDIT_KEY, None)


def _render_keyword_suggestion() -> None:
    suggestion = st.session_state.get(_KEYWORD_SUGGEST_KEY)
    if not suggestion:
        return

    keyword = str(suggestion.get("keyword") or "")
    category = str(suggestion.get("category") or "")
    sample = str(suggestion.get("sample") or "").strip()
    if not keyword or not category:
        _close_keyword_dialog()
        return

    if _KEYWORD_EDIT_KEY not in st.session_state:
        st.session_state[_KEYWORD_EDIT_KEY] = keyword

    _keyword_suggest_dialog(
        keyword=keyword,
        category=category,
        sample=sample,
    )


@st.dialog("Parola chiave", on_dismiss=_close_keyword_dialog)
def _keyword_suggest_dialog(
    *,
    keyword: str,
    category: str,
    sample: str,
) -> None:
    icon = get_category_icon(category)
    sample_html = ""
    if sample:
        sample_html = (
            f'<div style="margin-top:10px;font-size:13px;'
            f'font-weight:650;color:var(--ft-accent-strong);">'
            f"{html.escape(sample)}</div>"
        )

    render_html(
        f"""
        <div class="ft-export-dialog" style="padding:2px 0 8px 0;">
          <div class="ft-appearance-chip" style="width:fit-content;">
            <span class="ft-appearance-chip-dot"></span>
            {html.escape(icon)} {html.escape(category)}
          </div>
          <div style="
              margin-top:14px;
              font-family:Fraunces,Georgia,serif;
              font-size:clamp(22px, 2.2vw, 28px);
              font-weight:700;
              color:var(--ft-text);
              line-height:1.2;
          ">
            Aggiungere questa regola?
          </div>
          {sample_html}
          <div style="
              margin-top:10px;
              font-size:13px;
              line-height:1.45;
              color:var(--ft-muted);
          ">
            Puoi modificare il testo. Confermando ricalcolo
            le categorie automatiche.
          </div>
        </div>
        """
    )

    edited_keyword = st.text_input(
        "Parola chiave",
        key=_KEYWORD_EDIT_KEY,
    )
    add_col, skip_col = st.columns(2)
    with add_col:
        if st.button(
            "Aggiungi e ricalcola",
            type="primary",
            width="stretch",
            key="keyword_suggest_yes",
        ):
            chosen = str(edited_keyword or "").strip()
            if not chosen:
                st.error("Inserisci una parola chiave.")
                return
            added = add_keyword_to_category(category, chosen)
            updated = recalculate_automatic_categories()
            _close_keyword_dialog()
            if added:
                _queue_toast(
                    f"Keyword «{chosen.upper()}» aggiunta a {category}. "
                    f"Ricalcolati {updated} movimenti."
                )
            else:
                _queue_toast(
                    f"Keyword già presente. Ricalcolati {updated} movimenti."
                )
            st.rerun()
    with skip_col:
        if st.button(
            "No, grazie",
            type="secondary",
            width="stretch",
            key="keyword_suggest_no",
        ):
            _close_keyword_dialog()
            st.rerun()


def clean_description(value: str) -> str:
    if pd.isna(value):
        return ""

    value = str(value).replace("\n", " ").strip()
    return " ".join(value.split())


def format_date(value) -> str:
    if pd.isna(value):
        return "Data non disponibile"

    if not isinstance(value, pd.Timestamp):
        value = pd.to_datetime(
            value,
            errors="coerce",
        )

    if pd.isna(value):
        return "Data non disponibile"

    return value.strftime("%d/%m/%y")


def get_categories() -> list[str]:
    return get_category_names()


def _category_rgb(color: str) -> str:
    raw = str(color).removeprefix("#")
    if len(raw) != 6:
        return "var(--ft-accent-rgb)"
    return (
        f"{int(raw[0:2], 16)}, "
        f"{int(raw[2:4], 16)}, "
        f"{int(raw[4:6], 16)}"
    )


@st.dialog(
    "Modifica movimento",
    width="large",
    on_dismiss=_close_movement_dialog,
)
def _movement_edit_dialog(movement_id: int, categories: list[str]) -> None:
    df = load_movements()
    match = df[df["id"] == movement_id]
    if match.empty:
        st.warning("Movimento non trovato.")
        return

    row = match.iloc[0]
    amount = float(row["importo"])
    category = (
        str(row["categoria"])
        if row["categoria"] in categories
        else "Altro"
    )
    description = clean_description(row["descrizione"])
    full_description = clean_description(row["descrizione_completa"])
    title = full_description if full_description else description
    icon = get_category_icon(category)
    if category == INVESTMENT_CATEGORY:
        amount_label = euro(abs(amount))
    elif amount > 0:
        amount_label = f"+{euro(amount)}"
    else:
        amount_label = euro(amount)

    render_html(
        f"""
        <div class="ft-export-dialog" style="padding:2px 0 10px 0;">
          <div class="ft-appearance-chip" style="width:fit-content;">
            <span class="ft-appearance-chip-dot"></span>
            {html.escape(icon)} {html.escape(category)}
          </div>
          <div style="
              margin-top:12px;
              font-family:Fraunces,Georgia,serif;
              font-size:clamp(20px, 2vw, 26px);
              font-weight:700;
              color:var(--ft-text);
              line-height:1.25;
          ">{html.escape(title or "Senza descrizione")}</div>
          <div style="
              margin-top:6px;
              font-size:13px;
              color:var(--ft-muted);
          ">{html.escape(amount_label)}</div>
        </div>
        """
    )
    _render_movement_details(
        row=row,
        movement_id=movement_id,
        category=category,
        categories=categories,
        title=title,
        description=description,
        amount=amount,
        is_special=bool(row.get("speciale", False)),
        special_months=int(row.get("speciale_mesi") or 0),
        exclude_from_metrics=bool(row.get("escludi_metriche", False)),
        is_investment=category == INVESTMENT_CATEGORY,
        is_transfer=is_transfer_category(category),
    )


def _movement_date(row: pd.Series) -> date:
    parsed = pd.to_datetime(row.get("data"), errors="coerce", dayfirst=True)
    if pd.isna(parsed):
        return date.today()
    return parsed.date()


def _render_movement_details(
    *,
    row: pd.Series,
    movement_id: int,
    category: str,
    categories: list[str],
    title: str,
    description: str,
    amount: float,
    is_special: bool,
    special_months: int,
    exclude_from_metrics: bool,
    is_investment: bool,
    is_transfer: bool,
) -> None:
    original_category = str(row["categoria"])
    desc_key = f"edit_desc_{movement_id}"
    notes_key = f"edit_notes_{movement_id}"
    exclude_key = f"escludi_metriche_{movement_id}"
    speciale_key = f"speciale_{movement_id}"
    mesi_key = f"speciale_mesi_{movement_id}"
    split_open_key = f"split_open_{movement_id}"

    if desc_key not in st.session_state:
        st.session_state[desc_key] = title
    if notes_key not in st.session_state:
        st.session_state[notes_key] = str(row.get("notes") or "")
    if exclude_key not in st.session_state:
        st.session_state[exclude_key] = exclude_from_metrics
    if speciale_key not in st.session_state:
        st.session_state[speciale_key] = is_special
    if mesi_key not in st.session_state:
        st.session_state[mesi_key] = special_months

    new_description = st.text_input(
        "Descrizione",
        key=desc_key,
    )
    new_category = st.selectbox(
        "Categoria",
        categories,
        index=categories.index(category),
        format_func=lambda name: f"{get_category_icon(name)} {name}",
        key=f"category_{movement_id}",
    )
    new_notes = st.text_area(
        "Note",
        key=notes_key,
        height=68,
        placeholder="Opzionale",
    )

    if is_transfer_category(new_category):
        marked_exclude = True
        st.caption(
            "I trasferimenti interni restano in lista ma "
            "non entrano in entrate, uscite o medie."
        )
    else:
        marked_exclude = st.checkbox(
            "Escludere dalle metriche",
            key=exclude_key,
            help=(
                "Il movimento resta in lista ma non conta "
                "in entrate, uscite, medie e grafici."
            ),
        )

    movement_type = "Entrata" if amount > 0 else "Uscita"
    marked_special = False
    spread_months = 0
    is_expense_type = (
        movement_type == "Uscita"
        and not is_transfer_category(new_category)
        and new_category != INVESTMENT_CATEGORY
    )
    if is_expense_type:
        marked_special = st.checkbox(
            "Spesa speciale",
            key=speciale_key,
            help=(
                "Segna spese fuori dalla normalità. "
                "Opzionale: ripartiscile sui mesi "
                "(es. abbonamento annuale su 12). "
                "0 mesi = esclusa dalla media giornaliera; "
                "l'importo intero resta nei totali."
            ),
        )
        if marked_special:
            spread_months = int(
                st.number_input(
                    "Ripartisci su mesi",
                    min_value=0,
                    max_value=60,
                    step=1,
                    key=mesi_key,
                    help=(
                        "Quanti mesi usare nella media giornaliera. "
                        "0 = esclusa del tutto dalla media "
                        "(resta nei totali)."
                    ),
                )
            )
            if spread_months > 0:
                st.caption(
                    f"Nella media: {euro(abs(amount) / spread_months)}/mese "
                    f"per {spread_months} mesi."
                )
    elif not is_transfer and not is_investment:
        st.caption("Spesa speciale disponibile solo sulle uscite.")

    movement_date = _movement_date(row)
    edited_amount = abs(float(amount))
    edited_account = str(row.get("account") or "Altro")

    save_col, delete_col = st.columns([1.6, 1.2])
    with save_col:
        saved = st.button(
            "Salva modifiche",
            type="primary",
            key=f"save_movement_{movement_id}",
            width="stretch",
        )
    with delete_col:
        confirm_key = f"confirm_delete_{movement_id}"
        if st.session_state.get(confirm_key):
            st.warning("Eliminare questo movimento?")
            yes_col, no_col = st.columns(2)
            with yes_col:
                if st.button("Sì", key=f"delete_yes_{movement_id}", width="stretch"):
                    delete_movement(movement_id)
                    _close_movement_dialog()
                    _queue_toast("Movimento eliminato")
                    st.rerun()
            with no_col:
                if st.button("No", key=f"delete_no_{movement_id}", width="stretch"):
                    st.session_state[confirm_key] = False
                    st.rerun()
        elif st.button("🗑️ Elimina", key=f"delete_{movement_id}", width="stretch"):
            st.session_state[confirm_key] = True
            st.rerun()

    if saved:
        if not str(new_description or "").strip():
            st.error("Inserisci una descrizione.")
        else:
            update_movement(
                movement_id,
                movement_date=movement_date,
                description=str(new_description).strip(),
                amount=edited_amount,
                category=new_category,
                movement_type=movement_type,
                account=edited_account,
                notes=str(new_notes or ""),
                speciale=marked_special,
                speciale_mesi=spread_months,
                escludi_metriche=marked_exclude,
            )
            _queue_keyword_suggestion(
                str(new_description).strip() or description,
                new_category,
            )
            _close_movement_dialog()
            _queue_toast("Movimento aggiornato")
            st.rerun()

    if short_description := description:
        if short_description != title:
            st.caption(short_description)

    if st.session_state.get(split_open_key):
        _render_split_form(
            movement_id=movement_id,
            category=category,
            categories=categories,
            amount=amount,
        )
    elif st.button("Dividi movimento", key=f"split_open_btn_{movement_id}"):
        original_abs = round(abs(float(amount)), 2)
        st.session_state[split_open_key] = True
        st.session_state[f"split_n_{movement_id}"] = 2
        first = round(original_abs / 2, 2)
        second = round(original_abs - first, 2)
        st.session_state[f"split_amt_{movement_id}_0"] = first
        st.session_state[f"split_amt_{movement_id}_1"] = second
        st.session_state[f"split_cat_{movement_id}_0"] = category
        st.session_state[f"split_cat_{movement_id}_1"] = category
        st.rerun()


def _render_split_form(
    *,
    movement_id: int,
    category: str,
    categories: list[str],
    amount: float,
) -> None:
    original_abs = round(abs(float(amount)), 2)
    st.markdown("**Dividi in più categorie**")
    st.caption(
        f"L'importo originale è {euro(original_abs)}. "
        "La somma delle parti deve coincidere."
    )
    parts_count = int(
        st.number_input(
            "Numero di parti",
            min_value=2,
            max_value=4,
            step=1,
            key=f"split_n_{movement_id}",
        )
    )

    parts: list[tuple[float, str]] = []
    assigned = 0.0
    for index in range(parts_count):
        amount_key = f"split_amt_{movement_id}_{index}"
        category_key = f"split_cat_{movement_id}_{index}"
        if amount_key not in st.session_state:
            remaining_slots = parts_count - index
            leftover = max(original_abs - assigned, 0.0)
            share = (
                round(leftover / remaining_slots, 2)
                if leftover > 0
                else 0.01
            )
            st.session_state[amount_key] = max(share, 0.01)
        if category_key not in st.session_state:
            st.session_state[category_key] = category

        part_col, cat_col = st.columns([1, 1.4])
        with part_col:
            part_amount = float(
                st.number_input(
                    f"Importo {index + 1}",
                    min_value=0.01,
                    step=0.01,
                    format="%.2f",
                    key=amount_key,
                )
            )
        with cat_col:
            part_category = st.selectbox(
                f"Categoria {index + 1}",
                categories,
                format_func=lambda name: f"{get_category_icon(name)} {name}",
                key=category_key,
            )
        parts.append((part_amount, part_category))
        assigned += part_amount

    assigned = round(assigned, 2)
    remaining = round(original_abs - assigned, 2)
    if abs(remaining) <= 0.01:
        st.caption("Somma corretta.")
    elif remaining > 0:
        st.caption(f"Mancano {euro(remaining)} da assegnare.")
    else:
        st.caption(f"{euro(abs(remaining))} in eccesso.")

    confirm_col, cancel_col, _ = st.columns([1.3, 1.2, 2])
    with confirm_col:
        if st.button(
            "Conferma divisione",
            type="primary",
            key=f"split_confirm_{movement_id}",
        ):
            try:
                created = split_movement(movement_id, parts)
            except ValueError as error:
                st.error(str(error))
            else:
                _close_movement_dialog()
                _queue_toast(
                    f"Movimento diviso in {created + 1} parti"
                )
                st.rerun()
    with cancel_col:
        if st.button("Annulla divisione", key=f"split_cancel_{movement_id}"):
            st.session_state[f"split_open_{movement_id}"] = False
            st.rerun()


def show_movements() -> None:
    st.title("Movimenti")
    st.caption("Cerca, filtra e modifica i movimenti salvati.")
    _show_queued_toast()
    _render_keyword_suggestion()
    render_pending_export_dialog()

    df = load_movements()

    if df.empty:
        render_html(
            """
            <div class="ft-empty-hero" style="
                margin-top:12px;
                padding:36px 26px 30px 26px;
                border-radius:18px;
                background:
                    radial-gradient(
                        circle at 14% 0%,
                        rgba(var(--ft-accent-rgb), 0.18),
                        transparent 44%
                    ),
                    var(--ft-panel);
                border:1px solid var(--ft-border);
                box-shadow:var(--ft-shadow);
                animation: ft-fade-up 360ms ease-out;
            ">
                <div style="
                    font-family:Fraunces,Georgia,serif;
                    font-size:clamp(28px, 3.2vw, 38px);
                    font-weight:700;
                    color:var(--ft-text);
                    letter-spacing:-0.02em;
                ">Nessun movimento</div>
                <div style="
                    margin-top:12px;
                    max-width:32rem;
                    font-size:15px;
                    line-height:1.5;
                    color:var(--ft-muted);
                ">
                    Importa un estratto conto oppure aggiungi il primo
                    movimento manualmente.
                </div>
            </div>
            """
        )
        st.markdown("")
        c1, c2, _ = st.columns([1.2, 1.2, 2])
        with c1:
            if st.button("Importa dati", type="primary", width="stretch"):
                switch_to("import_data")
        with c2:
            if st.button("Nuovo movimento", type="secondary", width="stretch"):
                switch_to("manual_entry")
        return

    categories = get_categories()
    _render_pending_movement_dialog(categories)
    months = sorted(df["mese"].dropna().unique(), reverse=True)
    month_options = ["Tutti"] + list(months)
    accounts = sorted(df["account"].dropna().unique().tolist())

    render_section_title("Filtri")
    with styled_panel():
        filter_col_1, filter_col_2, filter_col_3, filter_col_4 = st.columns(
            [1.2, 1.4, 1.4, 2.4]
        )

        with filter_col_1:
            selected_month = st.selectbox("Mese", month_options)

        with filter_col_2:
            selected_account = st.selectbox("Conto", ["Tutti"] + accounts)

        with filter_col_3:
            selected_category = st.selectbox(
                "Categoria",
                ["Tutte"] + categories,
                format_func=lambda name: (
                    name
                    if name == "Tutte"
                    else f"{get_category_icon(name)} {name}"
                ),
            )

        with filter_col_4:
            search = st.text_input(
                "Cerca",
                placeholder="Lidl, PayPal, Trenitalia...",
            )

    search_term = (search or "").strip()
    # Con testo di ricerca: guarda tutti i mesi (la data resta sulla riga).
    if search_term:
        filtered_df = df.copy()
    elif selected_month == "Tutti":
        filtered_df = df.copy()
    else:
        filtered_df = df[df["mese"] == selected_month].copy()

    if selected_account != "Tutti":
        filtered_df = filtered_df[
            filtered_df["account"] == selected_account
        ].copy()

    if selected_category != "Tutte":
        filtered_df = filtered_df[
            filtered_df["categoria"] == selected_category
        ].copy()

    if search_term:
        mask = (
            filtered_df["descrizione"]
            .fillna("")
            .str.contains(search_term, case=False, na=False)
            | filtered_df["descrizione_completa"]
            .fillna("")
            .str.contains(search_term, case=False, na=False)
            | filtered_df["categoria"]
            .fillna("")
            .str.contains(search_term, case=False, na=False)
            | filtered_df["account"]
            .fillna("")
            .str.contains(search_term, case=False, na=False)
            | filtered_df["notes"]
            .fillna("")
            .str.contains(search_term, case=False, na=False)
            | filtered_df["importo"]
            .astype(str)
            .str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask].copy()

    metrics = calculate_financial_metrics(filtered_df)
    total_income = metrics["entrate"]
    total_expense = metrics["uscite"]
    total_investments = metrics["investimenti"]
    balance = metrics["bilancio"]
    liquidity = metrics["liquidita"]

    balance_color = INCOME_COLOR if balance >= 0 else EXPENSE_COLOR
    liquidity_color = INCOME_COLOR if liquidity >= 0 else EXPENSE_COLOR

    render_section_title("Riepilogo")
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        render_kpi_card("Entrate", euro(total_income), value_color=INCOME_COLOR)

    with c2:
        render_kpi_card("Uscite", euro(total_expense), value_color=EXPENSE_COLOR)

    with c3:
        render_kpi_card("Bilancio", signed_euro(balance), value_color=balance_color)

    with c4:
        render_kpi_card(
            "Investimenti",
            euro(total_investments),
            value_color=INVESTMENT_COLOR,
        )

    with c5:
        render_kpi_card(
            "Liquidità",
            signed_euro(liquidity),
            value_color=liquidity_color,
        )

    total_found = len(filtered_df)
    if search_term:
        found_suffix = " (ricerca su tutti i mesi)"
    elif selected_month == "Tutti":
        found_suffix = " (tutti i mesi)"
    else:
        found_suffix = ""

    if filtered_df.empty:
        st.caption(f"0 movimenti trovati{found_suffix}")
        render_html(
            """
            <div class="ft-movement-empty">
                Nessun movimento con questi filtri.
            </div>
            """
        )
        return

    render_section_title("Lista")

    filtered_df = filtered_df.sort_values(
        by=["data", "id"],
        ascending=[False, False],
        na_position="last",
        kind="stable",
    )
    list_limit = _resolve_list_limit(
        (
            selected_month,
            selected_account,
            selected_category,
            search_term,
        )
    )
    visible_df = filtered_df.head(list_limit)
    hidden_count = max(total_found - len(visible_df), 0)
    if hidden_count:
        st.caption(
            f"Mostrati {len(visible_df)} di {total_found} movimenti"
            f"{found_suffix}"
        )
    else:
        st.caption(f"{total_found} movimenti trovati{found_suffix}")

    category_defs = load_category_definitions()
    for _, row in visible_df.iterrows():
        amount = float(row["importo"])
        category = (
            str(row["categoria"])
            if row["categoria"] in categories
            else "Altro"
        )
        is_investment = category == INVESTMENT_CATEGORY
        is_transfer = is_transfer_category(category)
        is_special = bool(row.get("speciale", False))
        special_months = int(row.get("speciale_mesi") or 0)
        exclude_from_metrics = bool(row.get("escludi_metriche", False))
        movement_id = int(row["id"])

        if is_investment:
            tone = "investment"
            displayed_amount = euro(abs(amount))
        elif is_transfer:
            tone = "transfer"
            displayed_amount = (
                f"+{euro(amount)}" if amount > 0 else euro(amount)
            )
        elif amount > 0:
            tone = "income"
            displayed_amount = f"+{euro(amount)}"
        else:
            tone = "expense"
            displayed_amount = euro(amount)

        icon = get_category_icon(category)
        date = format_date(row["data"])
        description = clean_description(row["descrizione"])
        full_description = clean_description(row["descrizione_completa"])
        title = full_description if full_description else description
        account = clean_description(row["account"])
        category_rgb = _category_rgb(
            get_category_color(category, category_defs)
        )
        flags = ""
        if is_special:
            flag_label = "Speciale"
            if special_months > 0:
                flag_label = f"Speciale · {special_months} mesi"
            flags += (
                f'<span class="ft-movement-flag">'
                f"{html.escape(flag_label)}</span>"
            )
        if exclude_from_metrics or is_transfer:
            flags += (
                '<span class="ft-movement-flag is-muted">Escluso</span>'
            )
        if str(row.get("notes") or "").strip():
            flags += '<span class="ft-movement-flag">Nota</span>'

        with styled_panel(kind="movement"):
            body_col, amount_col, action_col = st.columns(
                [4.2, 1.35, 1.05],
                vertical_alignment="center",
            )

            with body_col:
                render_html(
                    f"""
                    <div class="ft-movement-card"
                         style="--ft-cat-rgb:{category_rgb};">
                        <span class="ft-movement-tone is-{tone}" hidden></span>
                        <div class="ft-movement-title">
                            {html.escape(title or "Senza descrizione")}
                        </div>
                        <div class="ft-movement-meta">
                            <span class="ft-movement-cat">
                                <span class="ft-movement-cat-dot"></span>
                                {html.escape(icon)} {html.escape(category)}
                            </span>
                            {flags}
                            <span>{html.escape(date)}</span>
                            <span class="ft-movement-dot">·</span>
                            <span>{html.escape(account)}</span>
                        </div>
                    </div>
                    """
                )

            with amount_col:
                render_html(
                    f"""
                    <div class="ft-movement-amount is-{tone}">
                        {html.escape(displayed_amount)}
                    </div>
                    """
                )

            with action_col:
                if st.button(
                    "Modifica",
                    key=f"open_edit_{movement_id}",
                    width="stretch",
                    type="secondary",
                ):
                    _open_movement_dialog(movement_id)
                    st.rerun()

    if hidden_count:
        more = min(_LIST_PAGE_SIZE, hidden_count)
        _, more_col, _ = st.columns([1, 1.4, 1])
        with more_col:
            if st.button(
                f"Mostra altri {more}",
                type="secondary",
                key="movements_show_more",
                width="stretch",
            ):
                st.session_state[_LIST_LIMIT_KEY] = list_limit + more
                st.rerun()

    st.markdown("")
    export_month = (
        None
        if selected_month == "Tutti" or search_term
        else str(selected_month)
    )
    export_name = movements_export_filename(
        month=export_month,
        account=(
            selected_account
            if selected_account != "Tutti"
            else None
        ),
    )
    if search_term:
        context = f"Ricerca «{search_term}»"
    elif selected_month == "Tutti":
        context = "Tutti i mesi"
    else:
        context = f"Mese {selected_month}"
    if selected_account != "Tutti":
        context += f" · conto {selected_account}"
    if st.button(
        "Esporta Excel",
        type="secondary",
        key="export_movements_open",
    ):
        open_export_confirm_dialog(
            filtered_df,
            file_name=export_name,
            context_label=context,
            dialog_key="movements",
        )
        st.rerun()

    with st.expander("Vista avanzata"):
        st.dataframe(
            filtered_df[
                [
                    "id",
                    "data",
                    "data_operazione",
                    "data_valuta",
                    "descrizione",
                    "descrizione_completa",
                    "categoria",
                    "category_source",
                    "tipo",
                    "importo",
                    "source",
                    "account",
                    "speciale",
                    "speciale_mesi",
                    "escludi_metriche",
                    "notes",
                ]
            ],
            width="stretch",
            hide_index=True,
        )
