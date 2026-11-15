from __future__ import annotations

import html
from pathlib import Path

import pandas as pd
import streamlit as st

from src.components.cards import (
    BALANCE_COLOR,
    EXPENSE_COLOR,
    INCOME_COLOR,
    INVESTMENT_COLOR,
    LIQUIDITY_COLOR,
    MUTED_COLOR,
    render_chart_card,
    render_expense_distribution_card,
    render_hero_card,
    render_html,
    render_info_card,
    render_kpi_card,
    render_section_title,
)
from src.components.charts import donut_chart, xy_chart
from src.components.date_input import themed_date_input
from src.components.navigation import switch_to
from src.database.db import database_version
from src.services.analytics import (
    MOVEMENT_TYPE_FILTERS,
    PERIOD_CUSTOM,
    PERIOD_CUSTOM_ALIASES,
    accounts_chip_label,
    calculate_account_balance,
    calculate_daily_expense,
    calculate_financial_metrics,
    calculate_period_days,
    category_expense_breakdown,
    category_income_breakdown,
    filter_by_accounts,
    filter_by_movement_types,
    format_comparison_caption,
    get_current_period_bounds,
    get_daily_expense_comparison,
    get_period_day_count,
    get_period_df,
    get_previous_period_bounds,
    get_rate_comparison,
    get_value_comparison,
    monthly_flow_totals,
    normalize_date_column,
    resolve_analysis_bounds,
    savings_rate,
    special_expense_summary,
    special_expenses_overview,
    top_expense_category,
    top_income_category,
    types_chip_label,
)
from src.services.backup_service import restore_backup
from src.services.categories import get_category_icon, load_category_definitions
from src.services.movement_service import load_movements
from src.services.reports import month_name
from src.theme.colors import get_category_colors
from src.theme.tokens import resolve_semantic
from src.utils.formatting import euro, signed_euro
from src.utils.platform import IS_ANDROID


MONTHS_SHORT_IT = (
    "Gen", "Feb", "Mar", "Apr", "Mag", "Giu",
    "Lug", "Ago", "Set", "Ott", "Nov", "Dic",
)

PERIOD_OPTIONS = [
    "Questo mese",
    "Mese scorso",
    "Mese specifico",
    PERIOD_CUSTOM,
    "Ultimi 3 mesi",
    "Ultimi 6 mesi",
    "Quest'anno",
    "Tutto",
]

_RESTORE_KEY = "dashboard_restore_open"


def month_labels(months: list[str]) -> tuple[list[str], list[str]]:
    """'2026-11' -> ('Nov 2026', "Nov '26")."""
    long_labels: list[str] = []
    short_labels: list[str] = []
    for value in months:
        stamp = pd.to_datetime(f"{value}-01", errors="coerce")
        if pd.isna(stamp):
            long_labels.append(str(value))
            short_labels.append(str(value))
            continue
        name = MONTHS_SHORT_IT[stamp.month - 1]
        long_labels.append(f"{name} {stamp.year}")
        short_labels.append(f"{name} '{str(stamp.year)[-2:]}")
    return long_labels, short_labels


# ---------------------------------------------------------------- calcoli


@st.cache_data(max_entries=24, show_spinner=False)
def _dashboard_data(
    db_version: str,
    period: str,
    selected_month: str | None,
    custom_start: pd.Timestamp | None,
    custom_end: pd.Timestamp | None,
    selected_accounts: tuple[str, ...],
    selected_types: tuple[str, ...],
) -> dict | None:
    """
    Tutti i numeri della dashboard per i filtri scelti.

    In cache finché database e filtri non cambiano: tornando sulla Home
    da un'altra pagina (o cambiando solo il tema) non si ricalcola nulla.
    Sul telefono è la differenza tra un attimo e qualche secondo.
    """
    del db_version  # serve solo come chiave della cache
    accounts_filter = list(selected_accounts)
    types_filter = list(selected_types)

    df = load_movements()
    dated_all = normalize_date_column(df)

    filtered_df = get_period_df(
        df,
        period,
        selected_month,
        custom_start=custom_start,
        custom_end=custom_end,
    )
    filtered_df = filter_by_accounts(filtered_df, accounts_filter)
    filtered_df = filter_by_movement_types(filtered_df, types_filter)
    if filtered_df.empty:
        return None

    metrics = calculate_financial_metrics(filtered_df)
    account_scope = filter_by_accounts(df, accounts_filter)
    analysis_start, analysis_end = resolve_analysis_bounds(
        filtered_df,
        period,
        selected_month,
        custom_start=custom_start,
        custom_end=custom_end,
    )
    saldo = calculate_account_balance(account_scope, through=analysis_end)

    period_days = get_period_day_count(
        filtered_df,
        period,
        selected_month,
        custom_start=custom_start,
        custom_end=custom_end,
    )
    specials_source_df = filter_by_accounts(dated_all, accounts_filter)
    avg_daily_expense = calculate_daily_expense(
        filtered_df,
        period_days,
        source_df=specials_source_df,
        period_start=analysis_start,
        period_end=analysis_end,
    )
    special_summary = special_expense_summary(
        filtered_df,
        source_df=specials_source_df,
        period_start=analysis_start,
        period_end=analysis_end,
    )

    # Riga corta: il dettaglio (ripartite / escluse) è nella sezione
    # «Spese speciali» qui sotto, nella card non ci starebbe.
    daily_footer_parts = [
        f"{period_days} giorni" if IS_ANDROID else f"su {period_days} giorni"
    ]
    specials_count = int(special_summary["amortized_count"]) + int(
        special_summary["excluded_count"]
    )
    if specials_count > 0:
        noun = "speciale" if specials_count == 1 else "speciali"
        daily_footer_parts.append(f"{specials_count} {noun}")

    previous_bounds = get_previous_period_bounds(
        period=period,
        selected_month=selected_month,
        custom_start=custom_start,
        custom_end=custom_end,
    )

    deltas: dict[str, tuple[str | None, str]] = {
        key: (None, MUTED_COLOR)
        for key in ("bilancio", "entrate", "uscite", "investimenti", "saldo", "daily", "rate")
    }
    comparison_caption = None
    if previous_bounds is not None:
        previous_start, previous_end = previous_bounds
        comparison_source_df = specials_source_df
        previous_period_df = comparison_source_df[
            comparison_source_df["data"].between(
                previous_start,
                previous_end,
                inclusive="both",
            )
        ].copy()
        previous_period_df = filter_by_movement_types(
            previous_period_df,
            types_filter,
        )
        previous_metrics = calculate_financial_metrics(previous_period_df)
        deltas["rate"] = get_rate_comparison(
            savings_rate(metrics), savings_rate(previous_metrics)
        )
        previous_daily = calculate_daily_expense(
            previous_period_df,
            calculate_period_days(previous_start, previous_end),
            source_df=comparison_source_df,
            period_start=previous_start,
            period_end=previous_end,
        )
        deltas["daily"] = get_daily_expense_comparison(
            current_average=avg_daily_expense,
            previous_average=previous_daily,
        )
        for key, better in (
            ("bilancio", True),
            ("entrate", True),
            ("uscite", False),
            ("investimenti", True),
        ):
            deltas[key] = get_value_comparison(
                metrics[key],
                previous_metrics[key],
                higher_is_better=better,
            )
        previous_saldo = calculate_account_balance(
            account_scope,
            through=previous_end,
        )
        deltas["saldo"] = get_value_comparison(
            saldo,
            previous_saldo,
            higher_is_better=True,
        )
        current_bounds = get_current_period_bounds(
            period,
            selected_month,
            custom_start=custom_start,
            custom_end=custom_end,
        )
        if current_bounds is not None:
            comparison_caption = format_comparison_caption(
                current_bounds[0],
                current_bounds[1],
                previous_start,
                previous_end,
            )

    # Andamento del bilancio negli ultimi 12 mesi (per la card principale).
    trend_scope = filter_by_movement_types(account_scope, types_filter)
    trend = monthly_flow_totals(trend_scope)
    if not trend.empty and analysis_end is not None and pd.notna(analysis_end):
        last_month = pd.Timestamp(analysis_end).strftime("%Y-%m")
        trend = trend[trend["mese"].astype(str) <= last_month]
    trend = trend.tail(12)
    spark_values = (trend["entrate"] - trend["uscite"]).round(2).tolist()

    return {
        "metrics": metrics,
        "saldo": saldo,
        "avg_daily_expense": avg_daily_expense,
        "daily_footer": " · ".join(daily_footer_parts),
        "deltas": deltas,
        "comparison_caption": comparison_caption,
        "top_expense": top_expense_category(filtered_df),
        "top_income": top_income_category(filtered_df),
        "special_overview": special_expenses_overview(
            specials_source_df,
            analysis_start,
            analysis_end,
        ),
        "expense_breakdown": category_expense_breakdown(filtered_df),
        "income_breakdown": category_income_breakdown(filtered_df),
        "monthly": monthly_flow_totals(filtered_df),
        "spark_values": spark_values,
        "spark_months": len(spark_values),
    }


# ---------------------------------------------------------------- sezioni


def _render_category_breakdown_section(
    category_df: pd.DataFrame,
    *,
    empty_message: str,
    center_caption: str,
    card_key: str,
    chart_key: str,
) -> None:
    if category_df.empty:
        render_html(
            f"""
            <div class="ft-dashboard-card">
              <div class="ft-specials-hint" style="margin:0;">
                {html.escape(empty_message)}
              </div>
            </div>
            """
        )
        return

    category_df = category_df.copy()
    total_amount = float(category_df["importo"].sum())
    colors = get_category_colors(
        category_df["categoria"].astype(str).tolist(),
        load_category_definitions(),
    )

    rows = []
    segments = []
    for index, item in enumerate(category_df.itertuples(index=False)):
        category = str(item.categoria)
        amount = float(item.importo)
        icon = get_category_icon(category)
        rows.append(
            {
                "icon": icon,
                "name": category,
                "amount": euro(amount),
                "percent": amount / total_amount * 100 if total_amount else 0,
                "color": colors[index],
            }
        )
        segments.append(
            {"label": category, "value": amount, "color": colors[index], "icon": icon}
        )

    render_expense_distribution_card(
        rows,
        total_label=euro(total_amount),
        render_pie=lambda: donut_chart(
            segments,
            key=chart_key,
            center_label=center_caption,
            height=260 if IS_ANDROID else 300,
        ),
        list_max_height=300 if IS_ANDROID else 330,
        key=card_key,
    )


def _render_specials(special_overview: pd.DataFrame) -> None:
    render_section_title("Spese speciali")
    if special_overview.empty:
        render_html(
            """
            <div class="ft-dashboard-card">
              <div class="ft-specials-hint" style="margin:0;">
                Nessuna spesa speciale nel periodo.
                Puoi segnalarle in Movimenti → Modifica.
              </div>
            </div>
            """
        )
        return

    special_count = len(special_overview)
    special_total = float(special_overview["importo"].sum())
    rows_html: list[str] = []
    for item in special_overview.to_dict("records"):
        date_label = pd.Timestamp(item["data"]).strftime("%d/%m/%Y")
        title = html.escape(str(item["descrizione"] or "Senza descrizione"))
        category = str(item["categoria"] or "")
        account = html.escape(str(item["account"] or ""))
        mesi_range = html.escape(str(item["mesi_range"] or "—"))
        amount_label = html.escape(euro(float(item["importo"])))
        quota = item["quota_mese"]
        mode_chip = html.escape(str(item["modalita"] or ""))

        if pd.notna(quota):
            detail = (
                f'<span class="ft-special-range">{mesi_range}</span>'
                f'<span class="ft-special-quota">Quota mensile '
                f"<b>{html.escape(euro(float(quota)))}</b></span>"
            )
        else:
            detail = '<span class="ft-special-quota">Nessuna ripartizione</span>'

        note_text = str(item.get("notes") or "").strip()
        note_block = (
            f'<div class="ft-special-note">{html.escape(note_text)}</div>'
            if note_text
            else ""
        )
        rows_html.append(
            f"""
            <div class="ft-special-row">
              <div class="ft-special-main">
                <div class="ft-special-title">{title}</div>
                <div class="ft-special-meta">
                  <span class="ft-special-cat">{html.escape(get_category_icon(category))} {html.escape(category)}</span>
                  <span>{html.escape(date_label)}</span>
                  <span>{account}</span>
                  <span class="ft-special-mode">{mode_chip}</span>
                </div>
                <div class="ft-special-detail">{detail}</div>
                {note_block}
              </div>
              <div class="ft-special-amount">{amount_label}</div>
            </div>
            """
        )

    special_noun = "Spesa speciale" if special_count == 1 else "Spese speciali"
    summary_label = (
        f"{special_count} {special_noun} · Totale {euro(special_total)}"
    )
    st.html(
        f"""
        <div class="ft-dashboard-card">
          <details class="ft-specials-details">
            <summary class="ft-specials-summary">
              <span class="ft-specials-summary-label">
                {html.escape(summary_label)}
              </span>
            </summary>
            <div class="ft-specials-hint">
              Nei totali del mese restano come le hai pagate.
              Nella media giornaliera puoi escluderle
              oppure spalmarle sui mesi scelti.
            </div>
            {"".join(rows_html)}
          </details>
        </div>
        """
    )


def _render_monthly_chart(monthly: pd.DataFrame) -> None:
    render_section_title("Andamento mensile")
    if monthly.empty:
        return
    monthly = monthly.copy()
    monthly["mese"] = monthly["mese"].astype(str)
    monthly = monthly.sort_values("mese", kind="stable")
    labels, short = month_labels(monthly["mese"].tolist())
    sem = resolve_semantic()
    series = [
        {"name": "Entrate", "color": sem.income, "values": monthly["entrate"].tolist(), "area": True},
        {"name": "Uscite", "color": sem.expense, "values": monthly["uscite"].tolist(), "area": True},
    ]
    if float(monthly["investimenti"].sum()) > 0:
        series.append(
            {
                "name": "Investimenti",
                "color": sem.investment,
                "values": monthly["investimenti"].tolist(),
                "dash": True,
                "width": 2,
            }
        )
    net = (monthly["entrate"] - monthly["uscite"]).tolist()
    extra = [("Bilancio", signed_euro(value)) for value in net]
    kind = "bar" if len(labels) <= 6 else "line"
    render_chart_card(
        lambda: xy_chart(
            labels,
            series,
            key="ft_dashboard_monthly",
            kind=kind,
            height=260 if IS_ANDROID else 320,
            short_labels=short,
            tooltip_extra=extra,
        )
    )


def _savings_card(metrics: dict, delta: tuple[str | None, str]) -> None:
    """Card del tasso di risparmio (rimborsi compresi tra le entrate)."""
    rate = savings_rate(metrics)
    if rate is None:
        savings_label = "—"
        savings_color = MUTED_COLOR
        savings_footer = "serve almeno un’entrata"
    else:
        savings_label = f"{rate:.1f}".replace(".", ",") + "%"
        savings_color = INCOME_COLOR if rate >= 0 else EXPENSE_COLOR
        spent_share = f"{(100.0 - rate):.1f}".replace(".", ",")
        if IS_ANDROID:
            savings_footer = None
        elif rate > 0:
            savings_footer = f"{spent_share}% delle entrate è andato in uscite"
        elif rate == 0:
            savings_footer = "tutto è andato in uscite"
        else:
            savings_footer = "hai speso più di quanto è entrato"

    render_info_card(
        title="Tasso di risparmio",
        value=savings_label,
        value_color=savings_color,
        subtitle=delta[0],
        subtitle_color=delta[1],
        footer=savings_footer,
        extra_class="ft-savings-rate-card",
    )


# ---------------------------------------------------------------- vuoto


def _close_restore_dialog() -> None:
    st.session_state.pop(_RESTORE_KEY, None)


@st.dialog("Parti da un backup", on_dismiss=_close_restore_dialog)
def _restore_backup_dialog() -> None:
    st.caption(
        "Carica database e categorie dallo zip di backup."
        if IS_ANDROID
        else "Sostituisce database e categorie con lo zip di backup. "
        "Se la cartella sembra vuota, scegli «Tutti i file»."
    )
    uploaded = st.file_uploader(
        "Seleziona un backup (.zip)",
        type=None,
        key="dashboard_restore_uploader",
    )
    if uploaded is not None and Path(uploaded.name).suffix.lower() != ".zip":
        st.error("Formato non supportato. Usa un file backup .zip.")
        uploaded = None
    if uploaded is not None:
        if st.button("Ripristina", type="primary", width="stretch"):
            success, message = restore_backup(uploaded)
            if success:
                _close_restore_dialog()
                st.toast(message)
                st.rerun()
            else:
                st.error(message)
    if st.button("Annulla", width="stretch"):
        _close_restore_dialog()
        st.rerun()


def _render_empty_state() -> None:
    st.caption("Panoramica generale delle tue finanze.")
    render_html(
        """
        <div class="ft-empty-hero">
            <div class="ft-empty-title">Finance<span>Tracker</span></div>
            <div class="ft-empty-chip"><span></span>Inizia da qui</div>
            <div class="ft-empty-copy">
                Nessun movimento ancora. Importa un estratto conto,
                aggiungi il primo movimento oppure parti da un backup.
            </div>
            <div class="ft-empty-steps">
                <div><b>1</b>Importa l’estratto conto della banca</div>
                <div><b>2</b>Controlla le categorie assegnate</div>
                <div><b>3</b>Guarda dove vanno i tuoi soldi</div>
            </div>
        </div>
        """
    )
    st.markdown("")
    if st.session_state.get(_RESTORE_KEY):
        _restore_backup_dialog()
    if IS_ANDROID:
        # Sul telefono uno sotto l'altro: tre pulsanti affiancati non ci stanno.
        c1 = c2 = c3 = st.container()
    else:
        c1, c2, c3, _ = st.columns([1.2, 1.3, 1.5, 1.2])
    with c1:
        if st.button("Importa dati", type="primary", width="stretch"):
            switch_to("import_data")
    with c2:
        if st.button("Nuovo movimento", type="secondary", width="stretch"):
            switch_to("manual_entry")
    with c3:
        if st.button("Parti da un backup", type="secondary", width="stretch"):
            st.session_state[_RESTORE_KEY] = True
            st.rerun()


# ---------------------------------------------------------------- filtri


def _filter_summary(accounts: list[str]) -> str:
    period = st.session_state.get("dashboard_period", "Tutto")
    if period == "Mese specifico" and st.session_state.get("dashboard_month"):
        period = month_name(pd.Period(str(st.session_state["dashboard_month"]), freq="M"))
    account_label = accounts_chip_label(
        list(st.session_state.get("dashboard_accounts") or []), accounts
    )
    type_label = types_chip_label(list(st.session_state.get("dashboard_types") or []))
    return f"{period} · {account_label} · {type_label}"


def _render_filters(
    months: list[str],
    accounts: list[str],
    min_data,
    max_data,
):
    if "dashboard_period" not in st.session_state:
        st.session_state["dashboard_period"] = "Tutto"
    period = st.session_state["dashboard_period"]
    if period in PERIOD_CUSTOM_ALIASES:
        period = PERIOD_CUSTOM
    if period not in PERIOD_OPTIONS:
        period = "Tutto"
    st.session_state["dashboard_period"] = period

    selected_month = None
    custom_start = None
    custom_end = None

    def period_fields() -> None:
        nonlocal selected_month, custom_start, custom_end
        if st.session_state.get("dashboard_period") == "Mese specifico" and months:
            selected_month = st.selectbox(
                "Mese",
                months,
                key="dashboard_month",
                format_func=lambda value: month_labels([value])[0][0],
            )
        elif st.session_state.get("dashboard_period") == PERIOD_CUSTOM:
            from_col, to_col = st.columns(2)
            with from_col:
                custom_start = themed_date_input(
                    "Dal",
                    value=min_data,
                    key="dashboard_from",
                    min_year=min_data.year,
                    max_year=max_data.year + 1,
                )
            with to_col:
                custom_end = themed_date_input(
                    "Al",
                    value=max_data,
                    key="dashboard_to",
                    min_year=min_data.year,
                    max_year=max_data.year + 1,
                )

    if IS_ANDROID:
        # Sul telefono i filtri stanno in un riquadro richiudibile:
        # la Home parte subito dai numeri. Il titolo resta sempre «Filtri»:
        # se cambiasse col riepilogo, Streamlit ricreerebbe il riquadro
        # chiuso a ogni scelta (es. «Mese specifico» → poi il mese).
        with st.expander("Filtri"):
            period = st.selectbox("Periodo", PERIOD_OPTIONS, key="dashboard_period")
            period_fields()
            selected_accounts = st.pills(
                "Conti",
                accounts,
                selection_mode="multi",
                default=[],
                key="dashboard_accounts",
                help="Nessuno selezionato = tutti i conti.",
            )
            selected_types = st.pills(
                "Tipo",
                list(MOVEMENT_TYPE_FILTERS),
                selection_mode="multi",
                default=[],
                key="dashboard_types",
                help="Nessuno selezionato = tutti i movimenti.",
            )
        # Riepilogo sotto il riquadro, dopo i filtri: già aggiornato.
        st.caption(_filter_summary(accounts))
    else:
        with st.container(key="ft_filter_bar"):
            c1, c2, c3 = st.columns([1.15, 1.6, 1.25], gap="medium")
            with c1:
                period = st.selectbox("Periodo", PERIOD_OPTIONS, key="dashboard_period")
            with c2:
                selected_accounts = st.pills(
                    "Conti",
                    accounts,
                    selection_mode="multi",
                    default=[],
                    key="dashboard_accounts",
                    help="Nessuno selezionato = tutti i conti.",
                )
            with c3:
                selected_types = st.pills(
                    "Tipo",
                    list(MOVEMENT_TYPE_FILTERS),
                    selection_mode="multi",
                    default=[],
                    key="dashboard_types",
                    help="Nessuno selezionato = tutti i movimenti.",
                )
            period_fields()

    return (
        period,
        selected_month,
        custom_start,
        custom_end,
        list(selected_accounts or []),
        list(selected_types or []),
    )


# ---------------------------------------------------------------- pagina


def show_dashboard() -> None:
    st.title("Dashboard")

    df = load_movements()
    if df.empty:
        _render_empty_state()
        return

    dated_all = normalize_date_column(df)
    last_data_date = dated_all["data"].max()
    if pd.notna(last_data_date):
        st.caption(
            "Panoramica generale delle tue finanze · "
            f"Dati aggiornati al {last_data_date.strftime('%d/%m/%Y')}"
        )
    else:
        st.caption("Panoramica generale delle tue finanze.")

    months = sorted(df["mese"].dropna().unique(), reverse=True)
    accounts = sorted(df["account"].dropna().unique().tolist())
    today = pd.Timestamp.today().date()
    min_data = dated_all["data"].min().date() if not dated_all.empty else today
    max_data = dated_all["data"].max().date() if not dated_all.empty else today

    (
        period,
        selected_month,
        custom_start,
        custom_end,
        selected_accounts,
        selected_types,
    ) = _render_filters(months, accounts, min_data, max_data)

    data = _dashboard_data(
        str(database_version()),
        period,
        selected_month,
        pd.Timestamp(custom_start).normalize() if custom_start else None,
        pd.Timestamp(custom_end).normalize() if custom_end else None,
        tuple(selected_accounts),
        tuple(selected_types),
    )
    if data is None:
        st.warning("Nessun movimento trovato per i filtri selezionati (0 risultati).")
        return

    metrics = data["metrics"]
    saldo = float(data["saldo"])
    deltas = data["deltas"]
    bilancio = float(metrics["bilancio"])

    period_label = period
    if period == "Mese specifico" and selected_month:
        period_label = month_labels([str(selected_month)])[0][0]
    context = (
        f"{period_label} · {accounts_chip_label(selected_accounts, accounts)}"
        f" · {types_chip_label(selected_types)}"
    )
    spark_count = int(data["spark_months"])
    render_hero_card(
        title="Bilancio del periodo",
        main_value=signed_euro(bilancio),
        main_color=BALANCE_COLOR if bilancio >= 0 else EXPENSE_COLOR,
        subtitle=deltas["bilancio"][0],
        subtitle_color=deltas["bilancio"][1],
        context=context,
        spark_values=data["spark_values"],
        spark_caption=(
            f"Bilancio mensile · ultimi {spark_count} mesi"
            if spark_count > 1
            else None
        ),
    )
    if data["comparison_caption"]:
        st.caption(f"Confronto: {data['comparison_caption']}")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card(
            "Entrate",
            euro(metrics["entrate"]),
            value_color=INCOME_COLOR,
            subtitle=deltas["entrate"][0],
            subtitle_color=deltas["entrate"][1],
        )
    with k2:
        render_kpi_card(
            "Uscite",
            euro(metrics["uscite"]),
            value_color=EXPENSE_COLOR,
            subtitle=deltas["uscite"][0],
            subtitle_color=deltas["uscite"][1],
        )
    with k3:
        render_kpi_card(
            "Investimenti",
            euro(metrics["investimenti"]),
            value_color=INVESTMENT_COLOR,
            subtitle=deltas["investimenti"][0],
            subtitle_color=deltas["investimenti"][1],
        )
    with k4:
        render_kpi_card(
            "Liquidità",
            signed_euro(saldo),
            value_color=LIQUIDITY_COLOR if saldo >= 0 else EXPENSE_COLOR,
            subtitle=deltas["saldo"][0],
            subtitle_color=deltas["saldo"][1],
            tone="accent",
        )

    top = data["top_expense"]
    top_category, top_amount = top if top else ("Nessuna", 0.0)
    top_income = data["top_income"]
    top_income_name, top_income_amount = top_income if top_income else ("Nessuna", 0.0)

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        render_info_card(
            "Spesa principale",
            f"{get_category_icon(top_category)} {top_category}",
            euro(top_amount),
        )
    with s2:
        render_info_card(
            "Fonte principale",
            f"{get_category_icon(top_income_name)} {top_income_name}",
            euro(top_income_amount),
        )
    with s3:
        render_info_card(
            title="Spesa media giornaliera",
            value=euro(data["avg_daily_expense"]),
            subtitle=deltas["daily"][0],
            subtitle_color=deltas["daily"][1],
            footer=data["daily_footer"],
        )
    with s4:
        _savings_card(metrics, deltas["rate"])

    _render_specials(data["special_overview"])

    render_section_title("Dove sono andati i soldi")
    _render_category_breakdown_section(
        data["expense_breakdown"],
        empty_message="Nessuna uscita da mostrare per questo periodo.",
        center_caption="Totale uscite",
        card_key="ft_dashboard_expense_distribution",
        chart_key="ft_donut_expenses",
    )

    render_section_title("Da dove arrivano i soldi")
    _render_category_breakdown_section(
        data["income_breakdown"],
        empty_message="Nessuna entrata da mostrare per questo periodo.",
        center_caption="Totale entrate",
        card_key="ft_dashboard_income_distribution",
        chart_key="ft_donut_income",
    )

    _render_monthly_chart(data["monthly"])
