import html
import time
from datetime import date

import pandas as pd
import streamlit as st

from src.components.cards import (
    EXPENSE_COLOR,
    INCOME_COLOR,
    INVESTMENT_COLOR,
    MUTED_COLOR,
    render_html,
    render_kpi_card,
    render_section_title,
    styled_panel,
)
from src.components.date_input import themed_date_input
from src.components.export_dialog import (
    open_export_confirm_dialog,
    render_pending_export_dialog,
)
from src.components.navigation import switch_to
from src.services.analytics import (
    INVESTMENT_CATEGORY,
    MOVEMENT_TYPE_FILTERS,
    PERIOD_CUSTOM,
    PERIOD_CUSTOM_ALIASES,
    accounts_chip_label,
    calculate_account_balance,
    calculate_financial_metrics,
    filter_by_accounts,
    filter_by_movement_types,
    is_initial_balance_category,
    is_loan_category,
    is_non_operating_category,
    is_transfer_category,
    loan_flow_summary,
    normalize_date_column,
    types_chip_label,
)
from src.services.categories import (
    add_keyword_to_category,
    get_category_icon,
    get_category_names,
    load_category_definitions,
    suggest_keyword_from_text,
)
from src.theme.colors import get_category_color
from src.services.loans import (
    collapse_closed_loan_rows,
    is_linked_practice,
    is_settled_practice,
    link_repayment,
    loan_child_ids,
    loan_practices,
    loan_practice_ids,
    loan_related_ids,
    movement_loan_chip,
    open_loan_options,
    parse_loan_parent_id,
    practice_by_id,
    settled_parent_id,
    suggest_loan_parent_id,
    unlink_children,
    unlink_repayment,
    unlinked_repayment_count,
)
from src.services.movement_service import (
    delete_movements,
    load_movements,
    merge_movements,
    recalculate_automatic_categories,
    snapshot_movements,
    split_movement,
    undo_movement_action,
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
_MERGE_IDS_KEY = "movements_merge_ids"
_UNDO_KEY = "movements_undo"
_UNDO_TTL_SECONDS = 15


def _queue_toast(message: str) -> None:
    """Salva il toast e mostralo dopo il rerun (altrimenti sparisce subito)."""
    st.session_state[_MOVEMENTS_TOAST_KEY] = message


def _show_queued_toast() -> None:
    message = st.session_state.pop(_MOVEMENTS_TOAST_KEY, None)
    if message:
        st.toast(message, duration=4)


def _queue_undo(
    *,
    restore: list[dict],
    delete_ids: list[int] | None = None,
    label: str,
) -> None:
    st.session_state[_UNDO_KEY] = {
        "at": time.time(),
        "restore": restore,
        "delete_ids": list(delete_ids or []),
        "label": label,
    }


def _close_undo_popup() -> None:
    st.session_state.pop(_UNDO_KEY, None)


def _rerun_app() -> None:
    st.rerun(scope="app")


def _render_pending_undo_dialog() -> None:
    if not st.session_state.get(_UNDO_KEY):
        return
    _undo_popup_tick()


@st.fragment(run_every=1)
def _undo_popup_tick() -> None:
    payload = st.session_state.get(_UNDO_KEY)
    if not payload:
        return
    elapsed = time.time() - float(payload.get("at") or 0)
    if elapsed >= _UNDO_TTL_SECONDS:
        _close_undo_popup()
        _rerun_app()
        return

    remaining = max(int(_UNDO_TTL_SECONDS - elapsed), 0)
    label = str(payload.get("label") or "Ultima azione")
    with st.container():
        render_html(
            f"""
            <span class="ft-undo-anchor" aria-hidden="true"></span>
            <div class="ft-undo-card">
              <div class="ft-appearance-chip" style="width:fit-content;">
                <span class="ft-appearance-chip-dot"></span>
                {html.escape(label)}
              </div>
              <div class="ft-undo-title">Vuoi tornare indietro?</div>
              <div class="ft-undo-copy">
                Sparisce tra {remaining} s se non fai nulla.
              </div>
            </div>
            """
        )
        undo_col, keep_col = st.columns(2)
        with undo_col:
            if st.button(
                "Annulla azione",
                type="primary",
                width="stretch",
                key="undo_last_movement",
            ):
                undo_movement_action(
                    restore=list(payload.get("restore") or []),
                    delete_ids=list(payload.get("delete_ids") or []),
                )
                _close_undo_popup()
                _queue_toast("Azione annullata")
                _rerun_app()
        with keep_col:
            if st.button("Chiudi", width="stretch", key="undo_keep"):
                _close_undo_popup()
                _rerun_app()


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


def _close_merge_dialog() -> None:
    st.session_state.pop(_MERGE_IDS_KEY, None)


def _render_pending_merge_dialog(categories: list[str]) -> None:
    ids = st.session_state.get(_MERGE_IDS_KEY)
    if not ids:
        return
    _merge_movements_dialog([int(item) for item in ids], categories)


@st.dialog("Unisci movimenti", width="large", on_dismiss=_close_merge_dialog)
def _merge_movements_dialog(movement_ids: list[int], categories: list[str]) -> None:
    df = load_movements()
    selected = df[df["id"].isin(movement_ids)].copy()
    if len(selected) < 2:
        st.warning("Seleziona almeno due movimenti.")
        return

    accounts = selected["account"].dropna().astype(str).unique().tolist()
    total = float(selected["importo"].sum())
    first = selected.sort_values(
        by=["data", "id"],
        ascending=[True, True],
        na_position="last",
    ).iloc[0]
    default_category = (
        str(first["categoria"])
        if first["categoria"] in categories
        else "Altro"
    )
    default_desc = clean_description(first["descrizione_completa"]) or (
        clean_description(first["descrizione"]) or "Movimenti uniti"
    )

    render_html(
        f"""
        <div class="ft-export-dialog" style="padding:2px 0 8px 0;">
          <div class="ft-appearance-chip" style="width:fit-content;">
            <span class="ft-appearance-chip-dot"></span>
            {len(selected)} movimenti
          </div>
          <div style="
              margin-top:12px;
              font-family:Fraunces,Georgia,serif;
              font-size:clamp(22px, 2.2vw, 28px);
              font-weight:700;
              color:var(--ft-text);
          ">{html.escape(euro(abs(total)) if total < 0 else '+' + euro(total))}</div>
          <div style="margin-top:8px;font-size:13px;color:var(--ft-muted);">
            Resta la riga più vecchia. Le altre vengono eliminate.
          </div>
        </div>
        """
    )
    if len(accounts) != 1:
        st.error("Puoi unire solo movimenti dello stesso conto.")
        if st.button("Chiudi", width="stretch"):
            _close_merge_dialog()
            st.rerun()
        return

    description = st.text_input(
        "Descrizione",
        value=default_desc,
        key="merge_description",
    )
    category = st.selectbox(
        "Categoria",
        categories,
        index=categories.index(default_category),
        format_func=lambda name: f"{get_category_icon(name)} {name}",
        key="merge_category",
    )
    notes = st.text_area(
        "Note",
        value="",
        key="merge_notes",
        height=68,
        placeholder="Opzionale",
    )
    confirm_col, cancel_col = st.columns(2)
    with confirm_col:
        if st.button("Unisci", type="primary", width="stretch"):
            related = []
            for item in movement_ids:
                related.extend(loan_related_ids(int(item)))
            snapshots = snapshot_movements(related)
            try:
                removed = merge_movements(
                    movement_ids,
                    description=description,
                    category=category,
                    notes=notes,
                )
            except ValueError as error:
                st.error(str(error))
            else:
                _close_merge_dialog()
                _queue_undo(restore=snapshots, label="Movimenti uniti")
                _queue_toast(f"Uniti {removed + 1} movimenti")
                st.rerun()
    with cancel_col:
        if st.button("Annulla", width="stretch"):
            _close_merge_dialog()
            st.rerun()


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


def _loan_option_label(practice: dict) -> str:
    date_label = format_date(practice.get("date"))
    account = str(practice.get("account") or "").strip()
    suffix = f" · {account}" if account else ""
    if practice.get("open"):
        state = f"ancora {euro(float(practice['remaining']))}"
    else:
        state = "chiuso"
    return (
        f"{date_label} · {practice['description']}{suffix} · {state}"
    )


def _render_loan_practices(source_df: pd.DataFrame) -> None:
    practices = loan_practices(source_df)
    open_ones = [item for item in practices if item["open"]]
    unlinked = unlinked_repayment_count(source_df)
    if not open_ones and unlinked <= 0:
        return
    if open_ones:
        st.caption("Prestiti aperti")
        for practice in open_ones:
            repaid = euro(float(practice["repaid"]))
            remaining = euro(float(practice["remaining"]))
            account = str(practice.get("account") or "").strip()
            where = f" · {account}" if account else ""
            st.caption(
                f"• {practice['description']}{where} · "
                f"rientrato {repaid} · ancora {remaining}"
            )
    if unlinked > 0:
        noun = "rientro non collegato" if unlinked == 1 else "rientri non collegati"
        st.caption(f"{unlinked} {noun}. Aprili e collega all’uscita.")


def _render_loan_link_editor(*, row: pd.Series, movement_id: int) -> None:
    amount = float(row["importo"])
    df = load_movements()
    practices = loan_practices(df)
    if amount < 0:
        practice = practice_by_id(practices, movement_id)
        if practice is None:
            return
        if practice["open"]:
            st.caption(
                f"Pratica aperta: rientrati {euro(float(practice['repaid']))}, "
                f"ancora {euro(float(practice['remaining']))}."
            )
        elif practice["overpaid"]:
            st.caption(
                f"Rientrato più di quanto hai dato "
                f"({euro(float(practice['repaid']))} su "
                f"{euro(float(practice['outgoing']))})."
            )
        else:
            st.caption("Pratica chiusa: il rientro copre l’uscita.")
        return

    if amount <= 0:
        return

    parent_id = parse_loan_parent_id(row.get("prestito_di"))
    if parent_id:
        practice = practice_by_id(practices, parent_id)
        if practice:
            st.caption(
                f"Collegato a: {practice['description']} · "
                f"{format_date(practice.get('date'))}."
            )
        else:
            st.caption("Collegato a un prestito che non è più in archivio.")
        return

    options = open_loan_options(df, exclude_id=movement_id)
    if not options:
        st.caption("Nessun prestito in uscita a cui collegarlo.")
        return

    suggested = suggest_loan_parent_id(row, options)
    option_ids = [int(item["id"]) for item in options]
    default_index = (
        option_ids.index(suggested) if suggested in option_ids else 0
    )
    chosen_id = st.selectbox(
        "Collega a un prestito",
        option_ids,
        index=default_index,
        format_func=lambda item: _loan_option_label(
            practice_by_id(practices, int(item)) or {
                "description": f"#{item}",
                "remaining": 0,
                "open": False,
                "overpaid": False,
                "account": "",
                "date": None,
            }
        ),
        key=f"loan_parent_{movement_id}",
        help="L’app propone la pratica più vicina; confermi tu.",
    )
    if st.button(
        "Collega",
        type="secondary",
        key=f"loan_link_{movement_id}",
    ):
        try:
            link_repayment(movement_id, int(chosen_id))
        except ValueError as error:
            st.error(str(error))
        else:
            _queue_toast("Rientro collegato")
            st.rerun()


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
    practices = loan_practices(df)
    settled_id = settled_parent_id(int(movement_id), practices)
    if settled_id is not None:
        movement_id = settled_id
        st.session_state[_OPEN_MOVEMENT_KEY] = settled_id
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
    practice = practice_by_id(practices, movement_id)
    if practice is None:
        linked_parent = parse_loan_parent_id(row.get("prestito_di"))
        if linked_parent:
            practice = practice_by_id(practices, linked_parent)
    closed_practice = (
        practice if practice and is_linked_practice(practice) else None
    )
    if category == INVESTMENT_CATEGORY:
        amount_label = euro(abs(amount))
    elif amount > 0:
        amount_label = f"+{euro(amount)}"
    else:
        amount_label = euro(amount)

    chip_label = f"{icon} {category}"
    if closed_practice:
        chip_label += (
            " · Chiuso"
            if is_settled_practice(closed_practice)
            else " · Aperto"
        )
    show_legs = bool(practice and practice["child_ids"])
    amount_block = ""
    if not show_legs:
        amount_block = f"""
          <div style="
              margin-top:6px;
              font-size:13px;
              color:var(--ft-muted);
          ">{html.escape(amount_label)}</div>
        """
    render_html(
        f"""
        <div class="ft-export-dialog" style="padding:2px 0 10px 0;">
          <div class="ft-appearance-chip" style="width:fit-content;">
            <span class="ft-appearance-chip-dot"></span>
            {html.escape(chip_label)}
          </div>
          <div style="
              margin-top:12px;
              font-family:Fraunces,Georgia,serif;
              font-size:clamp(20px, 2vw, 26px);
              font-weight:700;
              color:var(--ft-text);
              line-height:1.25;
          ">{html.escape(title or "Senza descrizione")}</div>
          {amount_block}
        </div>
        """
    )
    if show_legs:
        _render_loan_practice_legs(df, practice)
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
    )


def _loan_leg_title(row: pd.Series) -> str:
    full = clean_description(row.get("descrizione_completa"))
    short = clean_description(row.get("descrizione"))
    return full or short or "Senza descrizione"


def _render_loan_leg_row(row: pd.Series, *, role: str) -> None:
    amount = float(row["importo"])
    tone = "income" if amount > 0 else "expense"
    displayed = f"+{euro(amount)}" if amount > 0 else euro(amount)
    title = _loan_leg_title(row)
    account = clean_description(row.get("account"))
    cat_rgb = "74, 222, 128" if amount > 0 else "248, 113, 113"
    with styled_panel(kind="movement"):
        render_html(
            f"""
            <div class="ft-movement-card ft-loan-leg"
                 style="--ft-cat-rgb:{cat_rgb};">
                <span class="ft-movement-tone is-{tone}" hidden></span>
                <div class="ft-loan-leg-copy">
                    <div class="ft-movement-title">
                        {html.escape(title)}
                    </div>
                    <div class="ft-movement-meta">
                        <span class="ft-movement-cat">
                            <span class="ft-movement-cat-dot"></span>
                            {html.escape(role)}
                        </span>
                        <span>{html.escape(format_date(row.get("data")))}</span>
                        <span class="ft-movement-dot">·</span>
                        <span>{html.escape(account)}</span>
                    </div>
                </div>
                <div class="ft-movement-amount is-{tone}">
                    {html.escape(displayed)}
                </div>
            </div>
            """
        )


def _render_loan_practice_legs(
    df: pd.DataFrame,
    practice: dict,
) -> None:
    parent = df[df["id"] == int(practice["id"])]
    if parent.empty:
        return
    children = df[df["id"].isin(practice["child_ids"])].sort_values(
        by=["data", "id"],
        ascending=[True, True],
    )
    st.caption("Movimenti della pratica")
    _render_loan_leg_row(parent.iloc[0], role="Uscita")
    for _, child in children.iterrows():
        _render_loan_leg_row(child, role="Entrata")


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
) -> None:
    original_category = str(row["categoria"])
    desc_key = f"edit_desc_{movement_id}"
    notes_key = f"edit_notes_{movement_id}"
    speciale_key = f"speciale_{movement_id}"
    mesi_key = f"speciale_mesi_{movement_id}"
    split_open_key = f"split_open_{movement_id}"

    if desc_key not in st.session_state:
        st.session_state[desc_key] = title
    if notes_key not in st.session_state:
        st.session_state[notes_key] = str(row.get("notes") or "")
    if speciale_key not in st.session_state:
        st.session_state[speciale_key] = is_special
    if mesi_key not in st.session_state:
        st.session_state[mesi_key] = special_months

    current_date = _movement_date(row)
    movement_date = themed_date_input(
        "Data",
        value=current_date,
        key=f"edit_date_{movement_id}",
        min_year=min(current_date.year - 10, date.today().year - 10),
        max_year=date.today().year + 1,
    )

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
        st.caption(
            "I trasferimenti non entrano in entrate o uscite, "
            "ma contano nel saldo del conto."
        )
    elif is_initial_balance_category(new_category):
        st.caption(
            "Il saldo iniziale non è un’entrata: serve a far "
            "quadrare il saldo reale del conto."
        )
    elif is_loan_category(new_category):
        st.caption(
            "I prestiti non entrano in entrate o uscite, "
            "ma contano nel saldo del conto. "
            "Andata e ritorno nella stessa categoria."
        )

    if is_loan_category(original_category):
        _render_loan_link_editor(row=row, movement_id=movement_id)

    movement_type = "Entrata" if amount > 0 else "Uscita"
    marked_special = False
    spread_months = 0
    is_expense_type = (
        movement_type == "Uscita"
        and not is_non_operating_category(new_category)
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

    edited_amount = abs(float(amount))
    edited_account = str(row.get("account") or "Altro")

    save_col, delete_col = st.columns(2)
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
            practice_ids = loan_practice_ids(movement_id)
            if len(practice_ids) > 1:
                st.warning(
                    f"Eliminare la pratica e i suoi "
                    f"{len(practice_ids)} movimenti?"
                )
            else:
                st.warning("Eliminare questo movimento?")
            yes_col, no_col = st.columns(2)
            with yes_col:
                if st.button("Sì", key=f"delete_yes_{movement_id}", width="stretch"):
                    snapshots = snapshot_movements(practice_ids)
                    delete_movements(practice_ids)
                    _close_movement_dialog()
                    if len(practice_ids) > 1:
                        _queue_undo(
                            restore=snapshots,
                            label="Pratica eliminata",
                        )
                        _queue_toast("Pratica eliminata")
                    else:
                        _queue_undo(
                            restore=snapshots,
                            label="Movimento eliminato",
                        )
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

    linked_parent = parse_loan_parent_id(row.get("prestito_di"))
    linked_children = (
        loan_child_ids(movement_id)
        if is_loan_category(original_category) and amount < 0
        else []
    )
    can_unlink_loan = bool(linked_parent or linked_children)

    if st.session_state.get(split_open_key):
        _render_split_form(
            movement_id=movement_id,
            category=category,
            categories=categories,
            amount=amount,
        )
        return

    if can_unlink_loan:
        split_col, unlink_col = st.columns(2)
    else:
        split_col = st.container()
        unlink_col = None

    with split_col:
        if st.button(
            "Dividi movimento",
            key=f"split_open_btn_{movement_id}",
            width="stretch",
        ):
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
    if unlink_col is not None:
        with unlink_col:
            if st.button(
                "Scollega prestito",
                key=f"loan_unlink_all_{movement_id}",
                width="stretch",
            ):
                if linked_children:
                    unlink_children(movement_id)
                elif linked_parent:
                    unlink_repayment(movement_id)
                _queue_toast("Prestito scollegato")
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
                snapshots = snapshot_movements([movement_id])
                created_ids = split_movement(movement_id, parts)
            except ValueError as error:
                st.error(str(error))
            else:
                _close_movement_dialog()
                _queue_undo(
                    restore=snapshots,
                    delete_ids=created_ids,
                    label="Movimento diviso",
                )
                _queue_toast(
                    f"Movimento diviso in {len(created_ids) + 1} parti"
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
    _render_pending_undo_dialog()
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

    categories = get_category_names()
    _render_pending_movement_dialog(categories)
    _render_pending_merge_dialog(categories)
    months = sorted(df["mese"].dropna().unique(), reverse=True)
    month_options = ["Tutti"] + list(months)
    accounts = sorted(df["account"].dropna().unique().tolist())

    dated_all = normalize_date_column(df)
    min_data = (
        dated_all["data"].min().date()
        if not dated_all.empty
        else date.today()
    )
    max_data = (
        dated_all["data"].max().date()
        if not dated_all.empty
        else date.today()
    )

    render_section_title("Filtri")
    with styled_panel():
        period_options = ["Tutto", "Mese specifico", PERIOD_CUSTOM]
        if "movements_period_mode" not in st.session_state:
            st.session_state["movements_period_mode"] = "Tutto"
        period_mode = st.session_state["movements_period_mode"]
        if period_mode in PERIOD_CUSTOM_ALIASES:
            period_mode = PERIOD_CUSTOM
        elif period_mode == "Tutti":
            period_mode = "Tutto"
        elif period_mode == "Mese":
            period_mode = "Mese specifico"
        if period_mode not in period_options:
            period_mode = "Tutto"
        st.session_state["movements_period_mode"] = period_mode

        selected_month = "Tutti"
        custom_start = None
        custom_end = None

        period_mode = st.selectbox(
            "Periodo",
            period_options,
            key="movements_period_mode",
        )
        if period_mode == "Mese specifico":
            month_choices = month_options[1:] or month_options
            if month_choices:
                selected_month = st.selectbox(
                    "Mese",
                    month_choices,
                    key="movements_month",
                )
        elif period_mode == PERIOD_CUSTOM:
            from_col, to_col = st.columns(2)
            with from_col:
                custom_start = themed_date_input(
                    "Dal",
                    value=min_data,
                    key="movements_from",
                    min_year=min_data.year,
                    max_year=max_data.year + 1,
                )
            with to_col:
                custom_end = themed_date_input(
                    "Al",
                    value=max_data,
                    key="movements_to",
                    min_year=min_data.year,
                    max_year=max_data.year + 1,
                )

        selected_accounts = st.pills(
            "Conti",
            accounts,
            selection_mode="multi",
            default=[],
            key="movements_accounts",
            help="Nessuno selezionato = tutti i conti.",
        )
        selected_accounts = list(selected_accounts or [])

        selected_types = st.pills(
            "Tipo",
            list(MOVEMENT_TYPE_FILTERS),
            selection_mode="multi",
            default=[],
            key="movements_types",
            help="Nessuno selezionato = tutti i movimenti.",
        )
        selected_types = list(selected_types or [])

        cat_col, search_col = st.columns([1.4, 2.4])
        with cat_col:
            selected_category = st.selectbox(
                "Categoria",
                ["Tutte"] + categories,
                format_func=lambda name: (
                    name
                    if name == "Tutte"
                    else f"{get_category_icon(name)} {name}"
                ),
            )
        with search_col:
            search = st.text_input(
                "Cerca",
                placeholder="Lidl, PayPal, Trenitalia...",
            )

    search_term = (search or "").strip()
    if search_term:
        filtered_df = df.copy()
    elif period_mode == "Mese specifico" and selected_month != "Tutti":
        filtered_df = df[df["mese"] == selected_month].copy()
    elif period_mode == PERIOD_CUSTOM and custom_start and custom_end:
        start = pd.Timestamp(custom_start).normalize()
        end = pd.Timestamp(custom_end).normalize()
        if end < start:
            start, end = end, start
        dated = normalize_date_column(df)
        filtered_df = dated[
            dated["data"].between(start, end, inclusive="both")
        ].copy()
    else:
        filtered_df = df.copy()

    filtered_df = filter_by_accounts(filtered_df, selected_accounts)
    filtered_df = filter_by_movement_types(filtered_df, selected_types)

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
    account_scope = filter_by_accounts(df, selected_accounts)
    saldo_through = None
    if period_mode == PERIOD_CUSTOM and custom_end is not None:
        saldo_through = pd.Timestamp(custom_end).normalize()
    elif period_mode == "Mese specifico" and selected_month != "Tutti":
        month_end = pd.Period(selected_month, freq="M").end_time.normalize()
        saldo_through = month_end
    account_saldo = calculate_account_balance(
        account_scope,
        through=saldo_through,
    )

    balance_color = INCOME_COLOR if balance >= 0 else EXPENSE_COLOR
    saldo_color = INCOME_COLOR if account_saldo >= 0 else EXPENSE_COLOR

    render_section_title("Riepilogo")
    if is_loan_category(selected_category):
        loan_summary = loan_flow_summary(
            filtered_df,
            source_df=account_scope,
        )
        period_net = float(loan_summary["period_net"])
        if period_net > 0:
            net_color = INCOME_COLOR
        elif period_net < 0:
            net_color = EXPENSE_COLOR
        else:
            net_color = MUTED_COLOR
        c1, c2, c3 = st.columns(3)
        with c1:
            render_kpi_card(
                "Prestati",
                euro(float(loan_summary["outgoing"])),
                value_color=EXPENSE_COLOR,
            )
        with c2:
            render_kpi_card(
                "Rientrati",
                euro(float(loan_summary["incoming"])),
                value_color=INCOME_COLOR,
            )
        with c3:
            render_kpi_card(
                "Netto",
                signed_euro(period_net),
                value_color=net_color,
            )
        open_net = float(loan_summary["open_net"])
        if open_net < -0.004:
            st.caption(
                f"Ancora in prestito sui conti filtrati: "
                f"{euro(abs(open_net))}."
            )
        elif open_net > 0.004:
            st.caption(
                f"Hai ricevuto più di quanto hai dato: "
                f"{signed_euro(open_net)}."
            )
        else:
            st.caption(
                "Il netto è quanto è rientrato meno quanto hai dato "
                "nei filtri attuali."
            )
        _render_loan_practices(account_scope)
    else:
        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            render_kpi_card(
                "Entrate",
                euro(total_income),
                value_color=INCOME_COLOR,
            )

        with c2:
            render_kpi_card(
                "Uscite",
                euro(total_expense),
                value_color=EXPENSE_COLOR,
            )

        with c3:
            render_kpi_card(
                "Bilancio",
                signed_euro(balance),
                value_color=balance_color,
            )

        with c4:
            render_kpi_card(
                "Investimenti",
                euro(total_investments),
                value_color=INVESTMENT_COLOR,
            )

        with c5:
            render_kpi_card(
                "Liquidità",
                signed_euro(account_saldo),
                value_color=saldo_color,
            )

    account_label = accounts_chip_label(selected_accounts, accounts)
    if search_term:
        found_suffix = " (ricerca su tutti i mesi)"
    elif period_mode == PERIOD_CUSTOM:
        found_suffix = " (intervallo)"
    elif period_mode == "Mese specifico":
        found_suffix = f" ({selected_month})"
    else:
        found_suffix = " (tutto)"
    if selected_accounts:
        found_suffix += f" · {account_label}"
    if selected_types:
        found_suffix += f" · {types_chip_label(selected_types)}"

    export_df = filtered_df
    loan_chip_practices = loan_practices(df)
    list_df = collapse_closed_loan_rows(
        filtered_df,
        df,
        loan_chip_practices,
    )
    sort_column = (
        "_loan_sort_data"
        if "_loan_sort_data" in list_df.columns
        else "data"
    )
    list_df = list_df.sort_values(
        by=[sort_column, "id"],
        ascending=[False, False],
        na_position="last",
        kind="stable",
    )
    total_found = len(list_df)

    if list_df.empty:
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
    list_limit = _resolve_list_limit(
        (
            period_mode,
            selected_month,
            tuple(selected_accounts),
            tuple(selected_types),
            selected_category,
            search_term,
            str(custom_start or ""),
            str(custom_end or ""),
        )
    )
    visible_df = list_df.head(list_limit)
    hidden_count = max(total_found - len(visible_df), 0)
    if hidden_count:
        st.caption(
            f"Mostrati {len(visible_df)} di {total_found} movimenti"
            f"{found_suffix}"
        )
    else:
        st.caption(f"{total_found} movimenti trovati{found_suffix}")
    st.caption("Seleziona più movimenti dello stesso conto per unirli.")

    category_defs = load_category_definitions()
    for _, row in visible_df.iterrows():
        amount = float(row["importo"])
        category = (
            str(row["categoria"])
            if row["categoria"] in categories
            else "Altro"
        )
        is_investment = category == INVESTMENT_CATEGORY
        is_special = bool(row.get("speciale", False))
        special_months = int(row.get("speciale_mesi") or 0)
        movement_id = int(row["id"])
        closed_practice = None
        if bool(row.get("_loan_closed")):
            closed_practice = practice_by_id(loan_chip_practices, movement_id)
            if closed_practice and not is_linked_practice(closed_practice):
                closed_practice = None

        if closed_practice:
            if is_settled_practice(closed_practice):
                tone = "transfer"
                displayed_amount = euro(0)
            else:
                tone = "expense"
                displayed_amount = euro(
                    -abs(float(closed_practice["remaining"]))
                )
        elif is_investment:
            tone = "investment"
            displayed_amount = euro(abs(amount))
        elif is_non_operating_category(category):
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
        if closed_practice:
            children = df[df["id"].isin(closed_practice["child_ids"])]
            member_dates = pd.concat(
                [
                    pd.Series([pd.to_datetime(row["data"], errors="coerce")]),
                    pd.to_datetime(children["data"], errors="coerce"),
                ],
                ignore_index=True,
            )
            start_date = member_dates.min()
            end_date = member_dates.max()
            start_label = format_date(start_date)
            end_label = format_date(end_date)
            date = (
                start_label
                if start_label == end_label
                else f"{start_label} → {end_label}"
            )
            child_accounts = {
                clean_description(value)
                for value in children["account"].tolist()
                if clean_description(value)
            }
            if account:
                child_accounts.add(account)
            if len(child_accounts) > 1:
                account = " · ".join(sorted(child_accounts))
        category_rgb = _category_rgb(
            get_category_color(category, category_defs)
        )
        flags = ""
        if closed_practice:
            if is_settled_practice(closed_practice):
                flags += '<span class="ft-movement-flag">Chiuso</span>'
            else:
                flags += '<span class="ft-movement-flag">Aperto</span>'
                repaid = euro(float(closed_practice["repaid"]))
                flags += (
                    f'<span class="ft-movement-flag">'
                    f"rientrato {html.escape(repaid)}</span>"
                )
        if is_special:
            flag_label = "Speciale"
            if special_months > 0:
                flag_label = f"Speciale · {special_months} mesi"
            flags += (
                f'<span class="ft-movement-flag">'
                f"{html.escape(flag_label)}</span>"
            )
        if str(row.get("notes") or "").strip():
            flags += '<span class="ft-movement-flag">Nota</span>'
        if not closed_practice:
            loan_chip = movement_loan_chip(row, loan_chip_practices)
            if loan_chip:
                flags += (
                    f'<span class="ft-movement-flag">'
                    f"{html.escape(loan_chip)}</span>"
                )

        with styled_panel(kind="movement"):
            select_col, body_col, amount_col, action_col = st.columns(
                [0.4, 4.0, 1.3, 1.05],
                vertical_alignment="center",
            )
            with select_col:
                st.checkbox(
                    "Seleziona",
                    key=f"merge_pick_{movement_id}",
                    label_visibility="collapsed",
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

    picked_ids = [
        int(row_id)
        for row_id in visible_df["id"].tolist()
        if st.session_state.get(f"merge_pick_{int(row_id)}")
    ]
    if len(picked_ids) >= 2:
        if st.button(
            f"Unisci {len(picked_ids)} movimenti",
            type="primary",
            key="movements_merge_open",
        ):
            st.session_state[_MERGE_IDS_KEY] = picked_ids
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
        if period_mode != "Mese specifico" or search_term
        else str(selected_month)
    )
    export_account = (
        selected_accounts[0]
        if len(selected_accounts) == 1
        else None
    )
    export_name = movements_export_filename(
        month=export_month,
        account=export_account,
    )
    if search_term:
        context = f"Ricerca «{search_term}»"
    elif period_mode == PERIOD_CUSTOM and custom_start and custom_end:
        context = f"{custom_start.strftime('%d/%m/%y')} – {custom_end.strftime('%d/%m/%y')}"
    elif period_mode == "Mese specifico":
        context = f"Mese {selected_month}"
    else:
        context = "Tutto"
    if selected_accounts:
        context += f" · {accounts_chip_label(selected_accounts, accounts)}"
    if selected_types:
        context += f" · {types_chip_label(selected_types)}"
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
                    "notes",
                    "prestito_di",
                ]
            ],
            width="stretch",
            hide_index=True,
        )
