import html

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
)
from src.services.categories import (
    get_category_icon,
    get_category_names,
)
from src.services.movement_service import (
    delete_movement,
    load_movements,
    update_movement_category,
)
from src.utils.export_excel import (
    movements_export_filename,
)
from src.utils.formatting import euro, signed_euro


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


def show_movements() -> None:
    st.title("Movimenti")
    st.caption("Cerca, filtra e modifica i movimenti salvati.")
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
    accounts = sorted(df["account"].dropna().unique().tolist())

    render_section_title("Filtri")
    with styled_panel():
        filter_col_1, filter_col_2, filter_col_3, filter_col_4 = st.columns(
            [1.2, 1.4, 1.4, 2.4]
        )

        with filter_col_1:
            selected_month = st.selectbox("Mese", months)

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

    filtered_df = df[df["mese"] == selected_month].copy()

    if selected_account != "Tutti":
        filtered_df = filtered_df[
            filtered_df["account"] == selected_account
        ].copy()

    if selected_category != "Tutte":
        filtered_df = filtered_df[
            filtered_df["categoria"] == selected_category
        ].copy()

    if search:
        mask = (
            filtered_df["descrizione"]
            .fillna("")
            .str.contains(search, case=False, na=False)
            | filtered_df["descrizione_completa"]
            .fillna("")
            .str.contains(search, case=False, na=False)
            | filtered_df["categoria"]
            .fillna("")
            .str.contains(search, case=False, na=False)
            | filtered_df["account"]
            .fillna("")
            .str.contains(search, case=False, na=False)
            | filtered_df["notes"]
            .fillna("")
            .str.contains(search, case=False, na=False)
            | filtered_df["importo"]
            .astype(str)
            .str.contains(search, case=False, na=False)
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

        if is_investment:
            amount_color = INVESTMENT_COLOR
            displayed_amount = euro(abs(amount))
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
                edit_col_1, edit_col_2 = st.columns([2, 1])

                with edit_col_1:
                    new_category = st.selectbox(
                        "Categoria",
                        categories,
                        index=categories.index(category),
                        format_func=lambda name: (
                            f"{get_category_icon(name)} {name}"
                        ),
                        key=f"category_{row['id']}",
                    )

                    if new_category != row["categoria"]:
                        update_movement_category(
                            int(row["id"]),
                            new_category,
                        )
                        st.toast("Categoria aggiornata")
                        st.rerun()

                    if row.get("notes"):
                        st.caption(f"Note: {row['notes']}")

                    st.caption(description)

                with edit_col_2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    confirm_key = f"confirm_delete_{row['id']}"

                    if st.session_state.get(confirm_key):
                        st.warning(
                            "Eliminare questo movimento? "
                            "L'operazione non si può annullare."
                        )
                        c_yes, c_no = st.columns(2)

                        with c_yes:
                            if st.button(
                                "Sì",
                                key=f"delete_yes_{row['id']}",
                                width="stretch",
                            ):
                                delete_movement(int(row["id"]))
                                st.session_state[confirm_key] = False
                                st.toast("Movimento eliminato")
                                st.rerun()

                        with c_no:
                            if st.button(
                                "No",
                                key=f"delete_no_{row['id']}",
                                width="stretch",
                            ):
                                st.session_state[confirm_key] = False
                                st.rerun()
                    else:
                        if st.button(
                            "🗑️ Elimina",
                            key=f"delete_{row['id']}",
                            width="stretch",
                        ):
                            st.session_state[confirm_key] = True
                            st.rerun()

    st.markdown("")
    export_name = movements_export_filename(
        month=str(selected_month),
        account=(
            selected_account
            if selected_account != "Tutti"
            else None
        ),
    )
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
                    "notes",
                ]
            ],
            width="stretch",
            hide_index=True,
        )
