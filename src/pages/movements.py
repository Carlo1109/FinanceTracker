import html
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
    suggest_keyword_from_text,
)
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
_KEYWORD_SCROLL_KEY = "keyword_suggest_scroll"


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
    st.session_state[_KEYWORD_SCROLL_KEY] = True


def _scroll_page_to_top() -> None:
    """Riporta in cima dopo il salvataggio (Streamlit resta sullo scroll)."""
    st.html(
        """
        <div id="ft-keyword-suggest-anchor" aria-hidden="true"></div>
        <script>
        (function () {
          function scrollUp() {
            const win = window.top || window.parent || window;
            const doc = win.document;
            const nodes = [
              doc.querySelector('[data-testid="stMain"]'),
              doc.querySelector('[data-testid="stAppViewContainer"]'),
              doc.querySelector('section.main'),
              doc.scrollingElement,
              doc.documentElement,
              doc.body
            ];
            for (const node of nodes) {
              if (!node) continue;
              try {
                if (typeof node.scrollTo === "function") {
                  node.scrollTo({ top: 0, left: 0, behavior: "smooth" });
                } else {
                  node.scrollTop = 0;
                }
              } catch (error) {}
            }
            try { win.scrollTo({ top: 0, left: 0, behavior: "smooth" }); } catch (error) {}
            const anchor = doc.getElementById("ft-keyword-suggest-anchor");
            if (anchor && typeof anchor.scrollIntoView === "function") {
              anchor.scrollIntoView({ behavior: "smooth", block: "start" });
            }
          }
          scrollUp();
          setTimeout(scrollUp, 80);
          setTimeout(scrollUp, 280);
          setTimeout(scrollUp, 600);
        })();
        </script>
        """,
        width="content",
        unsafe_allow_javascript=True,
    )


def _render_keyword_suggestion() -> None:
    suggestion = st.session_state.get(_KEYWORD_SUGGEST_KEY)
    if not suggestion:
        return

    keyword = str(suggestion.get("keyword") or "")
    category = str(suggestion.get("category") or "")
    if not keyword or not category:
        st.session_state.pop(_KEYWORD_SUGGEST_KEY, None)
        st.session_state.pop(_KEYWORD_EDIT_KEY, None)
        return

    if _KEYWORD_EDIT_KEY not in st.session_state:
        st.session_state[_KEYWORD_EDIT_KEY] = keyword

    if st.session_state.pop(_KEYWORD_SCROLL_KEY, False):
        _scroll_page_to_top()

    st.info(
        f"Vuoi aggiungere una parola chiave a "
        f"**{get_category_icon(category)} {category}**? "
        "Puoi modificare il testo prima di confermare. "
        "Poi ricalcolo le categorie automatiche."
    )
    edited_keyword = st.text_input(
        "Parola chiave",
        key=_KEYWORD_EDIT_KEY,
    )
    add_col, skip_col, _ = st.columns([1.4, 1.2, 3])
    with add_col:
        if st.button(
            "Aggiungi e ricalcola",
            type="primary",
            key="keyword_suggest_yes",
        ):
            chosen = str(edited_keyword or "").strip()
            if not chosen:
                st.error("Inserisci una parola chiave.")
                return
            added = add_keyword_to_category(category, chosen)
            updated = recalculate_automatic_categories()
            st.session_state.pop(_KEYWORD_SUGGEST_KEY, None)
            st.session_state.pop(_KEYWORD_EDIT_KEY, None)
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
        if st.button("No, grazie", key="keyword_suggest_no"):
            st.session_state.pop(_KEYWORD_SUGGEST_KEY, None)
            st.session_state.pop(_KEYWORD_EDIT_KEY, None)
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
                    _clear_movement_widget_state(movement_id)
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
            if new_category != original_category:
                _queue_keyword_suggestion(
                    str(new_description).strip() or description,
                    new_category,
                )
            _clear_movement_widget_state(movement_id)
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
                _clear_movement_widget_state(movement_id)
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

    if search_term:
        st.caption(
            f"{len(filtered_df)} movimenti trovati "
            f"(ricerca su tutti i mesi)"
        )
    elif selected_month == "Tutti":
        st.caption(f"{len(filtered_df)} movimenti trovati (tutti i mesi)")
    else:
        st.caption(f"{len(filtered_df)} movimenti trovati")

    if filtered_df.empty:
        st.warning(
            "Nessun movimento trovato con i filtri selezionati (0 risultati)."
        )
        return

    render_section_title("Lista")

    filtered_df = filtered_df.sort_values(
        by=["data", "id"],
        ascending=[False, False],
        na_position="last",
        kind="stable",
    )

    for _, row in filtered_df.iterrows():
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
            amount_color = INVESTMENT_COLOR
            displayed_amount = euro(abs(amount))
        elif is_transfer:
            amount_color = MUTED_COLOR
            displayed_amount = (
                f"+{euro(amount)}" if amount > 0 else euro(amount)
            )
        elif amount > 0:
            amount_color = INCOME_COLOR
            displayed_amount = f"+{euro(amount)}"
        else:
            amount_color = EXPENSE_COLOR
            displayed_amount = euro(amount)

        icon = get_category_icon(category)
        date = format_date(row["data"])
        description = clean_description(row["descrizione"])
        full_description = clean_description(row["descrizione_completa"])
        title = full_description if full_description else description
        account = clean_description(row["account"])
        meta_chips = ""
        if is_special:
            chip_label = "Speciale"
            if special_months > 0:
                chip_label = f"Speciale · {special_months} mesi"
            meta_chips += f"""
                                <span style="
                                    background:rgba(var(--ft-accent-rgb),0.10);
                                    color:var(--ft-muted);
                                    padding:3px 8px;
                                    border-radius:8px;
                                    font-size:11px;
                                    font-weight:700;
                                    border:1px solid var(--ft-border);
                                ">{html.escape(chip_label)}</span>
            """
        if exclude_from_metrics or is_transfer:
            meta_chips += f"""
                                <span style="
                                    background:rgba(148,163,184,0.16);
                                    color:var(--ft-muted);
                                    padding:3px 8px;
                                    border-radius:8px;
                                    font-size:11px;
                                    font-weight:700;
                                    border:1px solid var(--ft-border);
                                ">Escluso dalle metriche</span>
            """

        with styled_panel(kind="movement"):
            top_left, top_right = st.columns([4.2, 1.2])

            with top_left:
                render_html(
                    f"""
                    <div class="ft-movement-row" style="border-bottom:none;padding:2px 0;">
                        <div>
                            <div style="
                                font-size:15px;
                                font-weight:700;
                                color:var(--ft-text);
                                line-height:1.35;
                            ">
                                {html.escape(title)}
                            </div>
                            <div style="
                                margin-top:6px;
                                font-size:12px;
                                color:var(--ft-muted);
                                display:flex;
                                align-items:center;
                                flex-wrap:wrap;
                                gap:8px;
                            ">
                                <span style="
                                    background:rgba(var(--ft-accent-rgb),0.14);
                                    color:var(--ft-accent-strong);
                                    padding:3px 8px;
                                    border-radius:8px;
                                    font-size:11px;
                                    font-weight:750;
                                ">{html.escape(icon)} {html.escape(category)}</span>
                                {meta_chips}
                                <span>{html.escape(date)}</span>
                                <span>{html.escape(account)}</span>
                            </div>
                        </div>
                    </div>
                    """
                )

            with top_right:
                render_html(
                    f"""
                    <div style="
                        text-align:right;
                        font-family:Fraunces,Georgia,serif;
                        font-size:22px;
                        font-weight:700;
                        color:{amount_color};
                        padding-top:2px;
                        white-space:nowrap;
                    ">
                        {html.escape(displayed_amount)}
                    </div>
                    """
                )

            with st.expander("Dettagli"):
                _render_movement_details(
                    row=row,
                    movement_id=movement_id,
                    category=category,
                    categories=categories,
                    title=title,
                    description=description,
                    amount=amount,
                    is_special=is_special,
                    special_months=special_months,
                    exclude_from_metrics=exclude_from_metrics,
                    is_investment=is_investment,
                    is_transfer=is_transfer,
                )

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
