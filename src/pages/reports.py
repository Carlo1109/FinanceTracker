"""Pagina Report: riepilogo mensile e annuale con i confronti."""

from __future__ import annotations

import html
from datetime import date

import pandas as pd
import streamlit as st

from src.components.cards import (
    EXPENSE_COLOR,
    INCOME_COLOR,
    MUTED_COLOR,
    render_html,
    render_kpi_card,
    render_section_title,
)
from src.components.charts import calendar_heatmap, xy_chart
from src.components.navigation import switch_to
from src.database.db import database_version
from src.services.analytics import filter_by_accounts, get_value_comparison
from src.services.categories import get_category_icon, load_category_definitions
from src.services.movement_service import load_movements
from src.services.reports import (
    MONTHS_IT,
    Report,
    available_months,
    available_years,
    build_month_report,
    build_year_report,
    investment_split,
    month_name,
)
from src.theme.colors import get_category_colors
from src.theme.tokens import resolve_semantic
from src.utils.formatting import euro, signed_euro
from src.utils.platform import IS_ANDROID


@st.cache_data(max_entries=16, show_spinner=False)
def _cached_report(
    db_version: str,
    kind: str,
    value: str,
    accounts: tuple[str, ...],
    today: date,
) -> Report:
    """In cache finché database, periodo e conti non cambiano."""
    del db_version
    df = filter_by_accounts(load_movements(), list(accounts))
    if kind == "month":
        return build_month_report(df, value, today=today)
    return build_year_report(df, int(value), today=today)


def _short(label: str) -> str:
    """'Novembre 2026' -> 'nov'; '2025' -> '2025'."""
    first = label.split()[0]
    return first[:3].lower() if not first.isdigit() else first


def _render_kpis(report: Report) -> None:
    cur = report.current.metrics
    prev = report.previous.metrics
    prev_label = f"vs {_short(report.previous.label)}"

    def comparison(key: str, better: bool) -> tuple[str | None, str]:
        if report.previous.movements == 0:
            return None, MUTED_COLOR
        text, color = get_value_comparison(cur[key], prev[key], higher_is_better=better)
        if text and " vs " in text:
            text = text.split(" vs ")[0] + " " + prev_label
        return text, color

    rate = report.current.savings_rate
    prev_rate = report.previous.savings_rate
    rate_label = "—" if rate is None else f"{rate:.1f}".replace(".", ",") + "%"
    rate_delta = None
    rate_color = MUTED_COLOR
    if rate is not None and prev_rate is not None:
        points = rate - prev_rate
        rate_delta = (
            f"{'↑' if points >= 0 else '↓'} "
            + f"{abs(points):.1f}".replace(".", ",")
            + f" pt {prev_label}"
        )
        rate_color = INCOME_COLOR if points >= 0 else EXPENSE_COLOR

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        text, color = comparison("entrate", True)
        render_kpi_card(
            "Entrate",
            euro(cur["entrate"]),
            value_color=INCOME_COLOR,
            subtitle=text,
            subtitle_color=color,
        )
    with c2:
        text, color = comparison("uscite", False)
        render_kpi_card(
            "Uscite",
            euro(cur["uscite"]),
            value_color=EXPENSE_COLOR,
            subtitle=text,
            subtitle_color=color,
        )
    split = investment_split(cur)
    # Con qualcosa investito, Risparmio e Tasso hanno una riga in più.
    extra_class = "has-extra" if split["investito"] > 0.005 else ""
    with c3:
        text, color = comparison("bilancio", True)
        balance = float(cur["bilancio"])
        render_kpi_card(
            "Risparmio",
            signed_euro(balance),
            icon="±",
            value_color=INCOME_COLOR if balance >= 0 else EXPENSE_COLOR,
            subtitle=text,
            subtitle_color=color,
            tone="accent",
            extra_html=_savings_split_html(split, balance),
            extra_class=extra_class,
        )
    with c4:
        share = split["quota_entrate"]
        note = ""
        if split["investito"] > 0.005 and share is not None:
            note = (
                '<div class="ft-kpi-note">di cui '
                + f"{share:.1f}".replace(".", ",")
                + "% investito</div>"
            )
        render_kpi_card(
            "Tasso risparmio",
            rate_label,
            icon="%",
            value_color=INCOME_COLOR if (rate or 0) >= 0 else EXPENSE_COLOR,
            subtitle=rate_delta,
            subtitle_color=rate_color,
            tone="accent",
            extra_html=note,
            extra_class=extra_class,
        )


def _savings_split_html(split: dict, balance: float) -> str:
    """Barretta «Investito · Liquidità»: le due parti del risparmio, non un extra."""
    invested = float(split["investito"])
    cash = float(split["liquidita"])
    if invested < 0.005:
        return ""
    cash_class = "is-bad" if cash < 0 else ""
    text = (
        '<div class="ft-split-legend">'
        f'<span><i class="is-invest"></i>Investito {html.escape(euro(invested))}</span>'
        f'<span class="{cash_class}"><i class="is-cash"></i>Liquidità '
        f"{html.escape(signed_euro(cash) if cash < 0 else euro(cash))}</span>"
        "</div>"
    )
    bar = ""
    if balance > 0.005:
        invested_pct = max(0.0, min(invested / balance * 100, 100.0))
        bar = (
            '<div class="ft-split-bar">'
            f'<span class="is-invest" style="width:{invested_pct:.1f}%"></span>'
            f'<span class="is-cash" style="width:{100 - invested_pct:.1f}%"></span>'
            "</div>"
        )
    return f'<div class="ft-split">{bar}{text}</div>'


def _render_specials(report: Report) -> None:
    """Scheda «Spese speciali»: quote dei ripartiti e speciali pagati nel mese."""
    table = report.specials
    if table is None or table.empty:
        render_html(
            '<div class="ft-specials-hint">Nessuna spesa speciale in questo periodo. '
            "Segna una spesa come speciale dal suo dettaglio in Movimenti.</div>"
        )
        return
    total = float(table["quota"].sum())
    is_month = report.kind == "month"
    render_section_title(
        "Spese speciali",
        (
            f"Quote del mese delle spese ripartite e spese pagate in {report.title}"
            if is_month
            else f"Mese per mese nel {report.title}"
        ),
    )
    _card(
        "specials",
        f"Totale {'nel mese' if is_month else 'nell’anno'} · {euro(total)}",
        lambda: render_html(_specials_table_html(table, is_month)),
    )
    st.caption(
        "Le ripartite su N mesi compaiono in ogni mese con la loro quota; "
        "quelle su 0 mesi solo nel mese in cui le hai pagate. "
        "Le altre schede del report contano le uscite quando le paghi."
    )


def _specials_row_html(item) -> str:
    name = html.escape(str(item.descrizione))
    category = str(item.categoria)
    paid = pd.Timestamp(item.data).strftime("%d/%m/%Y")
    if int(item.mesi) > 0:
        mode = f"Rata {html.escape(str(item.rata))} di {html.escape(euro(float(item.importo)))}"
    else:
        mode = "Solo nel mese pagato"
    meta = (
        f"{html.escape(get_category_icon(category))} {html.escape(category)} · "
        f"pagata il {paid}"
    )
    if IS_ANDROID:
        return (
            "<tr>"
            f'<td><div class="ft-spec-name">{name}</div>'
            f'<div class="ft-spec-meta">{meta} · {mode}</div></td>'
            f"<td>{html.escape(euro(float(item.quota)))}</td>"
            "</tr>"
        )
    return (
        "<tr>"
        f'<td><div class="ft-spec-name">{name}</div>'
        f'<div class="ft-spec-meta">{meta} · {html.escape(str(item.account))}</div></td>'
        f'<td class="is-muted">{mode}</td>'
        f"<td>{html.escape(euro(float(item.quota)))}</td>"
        "</tr>"
    )


def _specials_head() -> str:
    return "<th>Spesa</th>" + ("" if IS_ANDROID else "<th>Ripartizione</th>") + "<th>Nel mese</th>"


def _specials_table_html(table: pd.DataFrame, is_month: bool) -> str:
    columns = 2 if IS_ANDROID else 3
    total_row = (
        f'<tr class="is-total"><td colspan="{columns - 1}">Totale</td>'
        f"<td>{html.escape(euro(float(table['quota'].sum())))}</td></tr>"
    )
    if is_month:
        rows = "".join(_specials_row_html(item) for item in table.itertuples(index=False))
        return (
            '<div class="ft-cmp-scroll"><table class="ft-cmp-table ft-spec-table">'
            f"<thead><tr>{_specials_head()}</tr></thead><tbody>{rows}{total_row}</tbody>"
            "</table></div>"
        )
    # Anno: un riquadro per mese, chiuso; si apre toccando il mese.
    blocks: list[str] = []
    for month, group in table.groupby("mese", sort=True):
        period = pd.Period(str(month), freq="M")
        count = len(group)
        rows = "".join(_specials_row_html(item) for item in group.itertuples(index=False))
        blocks.append(
            '<details class="ft-spec-month"><summary>'
            f'<span class="ft-spec-month-name">{html.escape(MONTHS_IT[period.month - 1])}'
            f' <em>{count} {"spesa" if count == 1 else "spese"}</em></span>'
            f'<span class="ft-spec-month-total">{html.escape(euro(float(group["quota"].sum())))}</span>'
            "</summary>"
            '<div class="ft-cmp-scroll"><table class="ft-cmp-table ft-spec-table">'
            f"<thead><tr>{_specials_head()}</tr></thead><tbody>{rows}</tbody></table></div>"
            "</details>"
        )
    total = (
        '<div class="ft-spec-year-total"><span>Totale</span>'
        f"<span>{html.escape(euro(float(table['quota'].sum())))}</span></div>"
    )
    return f'<div class="ft-spec-months">{"".join(blocks)}{total}</div>'


def _render_highlights(report: Report) -> None:
    if not report.highlights:
        return
    tones = {"good": "good", "bad": "bad", "neutral": "info"}
    cards = "".join(
        f"""
        <div class="ft-highlight">
          <span class="ft-delta is-{tones.get(item['tone'], 'info')}">{html.escape(item['kicker'])}</span>
          <div class="ft-highlight-title">{html.escape(item['title'])}</div>
          <div class="ft-highlight-copy">{item['copy']}</div>
        </div>
        """
        for item in report.highlights
    )
    render_html(f'<div class="ft-report-highlights">{cards}</div>')


def _category_table_html(report: Report) -> str:
    table = report.categories
    if table.empty:
        return '<div class="ft-specials-hint">Nessuna uscita nel periodo.</div>'
    colors = get_category_colors(
        table["categoria"].astype(str).tolist(), load_category_definitions()
    )
    is_month = report.kind == "month"
    show_last_year = is_month and report.last_year is not None and not IS_ANDROID
    show_average = not is_month and not IS_ANDROID
    # Sul telefono non c'è spazio per tutto: si tiene la differenza.
    show_previous = not IS_ANDROID

    months_count = 1
    if not is_month and report.monthly is not None:
        active = (report.monthly["entrate"] > 0) | (report.monthly["uscite"] > 0)
        months_count = max(int(active.sum()), 1)

    head = [
        "<th>Categoria</th>",
        f"<th>{html.escape(_short(report.current.label))}</th>",
        f"<th>{html.escape(_short(report.previous.label))}</th>" if show_previous else "",
        f"<th>vs {html.escape(_short(report.previous.label))}</th>" if not show_previous else "<th>Differenza</th>",
    ]
    if show_last_year:
        head.append(f"<th>{html.escape(report.last_year.label)}</th>")
    if show_average:
        head.append("<th>Media/mese</th>")

    rows = []
    for index, item in enumerate(table.itertuples(index=False)):
        current = float(item.corrente)
        previous = float(item.precedente)
        diff = current - previous
        if previous < 0.005 and current > 0:
            delta = '<span class="ft-delta is-info">nuova</span>'
        elif abs(diff) < 0.5:
            delta = '<span class="ft-delta">≈</span>'
        else:
            tone = "bad" if diff > 0 else "good"
            delta = (
                f'<span class="ft-delta is-{tone}">{"+" if diff > 0 else "−"}'
                f"{html.escape(euro(abs(diff)))}</span>"
            )
        name = html.escape(str(item.categoria))
        icon = html.escape(get_category_icon(str(item.categoria)))
        cells = [
            f'<td><span class="ft-cmp-cat"><i style="background:{colors[index]}"></i>'
            f"{icon} {name}</span></td>",
            f"<td>{html.escape(euro(current))}</td>",
            f'<td class="is-muted">{html.escape(euro(previous))}</td>' if show_previous else "",
            f"<td>{delta}</td>",
        ]
        if show_last_year:
            cells.append(
                f'<td class="is-muted">{html.escape(euro(float(item.anno_scorso)))}</td>'
            )
        if show_average:
            cells.append(
                f'<td class="is-muted">{html.escape(euro(current / months_count))}</td>'
            )
        rows.append("<tr>" + "".join(cells) + "</tr>")

    total_cur = float(table["corrente"].sum())
    total_prev = float(table["precedente"].sum())
    total = [
        "<td>Totale</td>",
        f"<td>{html.escape(euro(total_cur))}</td>",
        f'<td class="is-muted">{html.escape(euro(total_prev))}</td>' if show_previous else "",
        f"<td>{html.escape(signed_euro(total_cur - total_prev))}</td>",
    ]
    if show_last_year:
        total.append(
            f'<td class="is-muted">{html.escape(euro(float(table["anno_scorso"].sum())))}</td>'
        )
    if show_average:
        total.append(
            f'<td class="is-muted">{html.escape(euro(total_cur / months_count))}</td>'
        )
    rows.append('<tr class="is-total">' + "".join(total) + "</tr>")
    return (
        '<div class="ft-cmp-scroll"><table class="ft-cmp-table">'
        f"<thead><tr>{''.join(head)}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _top_expenses_html(report: Report) -> str:
    top = report.top_expenses
    if top.empty:
        return '<div class="ft-specials-hint">Nessuna uscita nel periodo.</div>'
    rows = []
    for rank, item in enumerate(top.itertuples(index=False), start=1):
        title = html.escape(str(item.descrizione or item.categoria))
        category = str(item.categoria)
        when = pd.Timestamp(item.data).strftime("%d/%m/%Y")
        rows.append(
            f"""
            <div class="ft-top-row">
              <span class="ft-top-rank">{rank}</span>
              <div class="ft-top-body">
                <div class="ft-top-title">{title}</div>
                <div class="ft-top-meta">{html.escape(get_category_icon(category))}
                  {html.escape(category)} · {when} · {html.escape(str(item.account))}</div>
              </div>
              <span class="ft-top-amount">{html.escape(euro(float(item.valore)))}</span>
            </div>
            """
        )
    return f'<div class="ft-top-list">{"".join(rows)}</div>'


def _card(key: str, title: str, body) -> None:
    with st.container(key=f"ft_report_card_{key}"):
        render_html(f'<div class="ft-kicker ft-card-label">{html.escape(title)}</div>')
        body()


def _render_bottom(report: Report) -> None:
    """Categorie a confronto e spese più grandi: stessa riga in mese e anno."""
    if IS_ANDROID:
        left = right = st.container()
    else:
        left, right = st.columns([1.35, 1], gap="medium")
    with left:
        if report.kind == "month":
            subtitle = f"{report.current.label} rispetto a {report.previous.label}"
            if report.last_year is not None and not IS_ANDROID:
                subtitle += f" e a {report.last_year.label}"
            card_title = "Uscite per categoria"
        else:
            subtitle = None
            card_title = f"{report.title} contro {report.previous.label}"
        render_section_title("Categorie a confronto", subtitle)
        _card(
            "categories",
            card_title,
            lambda: render_html(_category_table_html(report)),
        )
    with right:
        render_section_title("Le spese più grandi")
        _card("top", report.title, lambda: render_html(_top_expenses_html(report)))


def _render_month(report: Report) -> None:
    # Ordine comune a mese e anno: KPI, in evidenza, andamento, categorie + spese.
    _render_kpis(report)
    render_section_title("In evidenza")
    _render_highlights(report)

    render_section_title("Calendario delle uscite")
    _card(
        "calendar",
        f"{report.title} · {'tocca' if IS_ANDROID else 'passa su'} un giorno per il dettaglio",
        lambda: calendar_heatmap(
            report.days,
            key="ft_report_calendar",
            offset=report.calendar_offset,
        ),
    )

    _render_bottom(report)


def _render_year(report: Report) -> None:
    _render_kpis(report)
    render_section_title("In evidenza")
    _render_highlights(report)

    monthly = report.monthly
    sem = resolve_semantic()
    year = int(report.title)
    today = date.today()

    def savings_tip(balance: float, invested: float) -> tuple[str, str]:
        text = signed_euro(balance)
        if invested > 0.005:
            text += f" (investito {euro(invested)})"
        return ("Risparmio", text)

    render_section_title("Mese per mese")
    _card(
        "months",
        f"Entrate e uscite {report.title}",
        lambda: xy_chart(
            monthly["label"].tolist(),
            [
                {"name": "Entrate", "color": sem.income, "values": monthly["entrate"].tolist()},
                {"name": "Uscite", "color": sem.expense, "values": monthly["uscite"].tolist()},
            ],
            key="ft_report_year_bars",
            kind="bar",
            height=250 if IS_ANDROID else 300,
            tooltip_extra=[
                savings_tip(float(balance), float(invested))
                for balance, invested in zip(
                    monthly["bilancio"].tolist(), monthly["investimenti"].tolist()
                )
            ],
        ),
    )

    if report.previous.movements:
        # L'anno in corso si ferma al mese attuale: niente linea piatta nel futuro.
        last_month = today.month if year == today.year else 12
        visible = monthly[monthly["mese"] <= last_month]
        render_section_title(
            "Anno su anno",
            f"Uscite accumulate da gennaio: {report.title} contro {report.previous.label}",
        )
        _card(
            "yoy",
            "Uscite accumulate",
            lambda: xy_chart(
                visible["label"].tolist(),
                [
                    {
                        "name": report.title,
                        "color": sem.expense,
                        "values": visible["uscite"].cumsum().tolist(),
                        "area": True,
                    },
                    {
                        "name": report.previous.label,
                        "color": sem.muted,
                        "values": visible["uscite_prec"].cumsum().tolist(),
                        "dash": True,
                        "width": 2,
                    },
                ],
                key="ft_report_yoy",
                kind="line",
                height=240 if IS_ANDROID else 280,
            ),
        )

    _render_bottom(report)


def show_reports() -> None:
    st.title("Report")
    df = load_movements()
    if df.empty:
        st.caption("Riepiloghi mensili e annuali con i confronti.")
        render_html(
            """
            <div class="ft-empty-hero">
              <div class="ft-empty-title">Ancora nessun <span>report</span></div>
              <div class="ft-empty-copy">I report si riempiono da soli appena
              ci sono dei movimenti: importa un estratto conto o aggiungine uno.</div>
            </div>
            """
        )
        st.markdown("")
        if st.button("Importa dati", type="primary"):
            switch_to("import_data")
        return

    st.caption(
        "Riepiloghi mensili e annuali, con i confronti col periodo prima "
        "e con l'anno scorso."
    )

    months = available_months(df)
    years = available_years(df)
    accounts = sorted(df["account"].dropna().unique().tolist())

    if st.session_state.get("report_kind") not in ("Mese", "Anno"):
        st.session_state["report_kind"] = "Mese"
    if st.session_state.get("report_month") not in months:
        st.session_state["report_month"] = months[0]
    if st.session_state.get("report_year") not in years:
        st.session_state["report_year"] = years[0]

    with st.container(key="ft_filter_bar"):
        if IS_ANDROID:
            c1 = c2 = c3 = st.container()
        else:
            c1, c2, c3 = st.columns([0.8, 1.1, 1.8], gap="medium")
        with c1:
            kind = st.segmented_control(
                "Report",
                ["Mese", "Anno"],
                key="report_kind",
                selection_mode="single",
            ) or "Mese"
        with c2:
            if kind == "Mese":
                value = st.selectbox(
                    "Mese",
                    months,
                    key="report_month",
                    format_func=lambda m: month_name(pd.Period(m, freq="M")),
                )
            else:
                value = str(st.selectbox("Anno", years, key="report_year"))
        with c3:
            selected_accounts = st.pills(
                "Conti",
                accounts,
                selection_mode="multi",
                default=[],
                key="report_accounts",
                help="Nessuno selezionato = tutti i conti.",
            )

    report = _cached_report(
        str(database_version()),
        "month" if kind == "Mese" else "year",
        str(value),
        tuple(selected_accounts or []),
        date.today(),
    )

    if report.current.movements == 0:
        st.info("Nessun movimento in questo periodo per i conti scelti.")
        return

    # Etichette fisse: se cambiassero (es. con un conteggio) Streamlit
    # tornerebbe alla prima scheda a ogni cambio di mese.
    summary_tab, specials_tab = st.tabs(["Riepilogo", "Spese speciali"])
    with summary_tab:
        if report.kind == "month":
            _render_month(report)
        else:
            _render_year(report)
    with specials_tab:
        _render_specials(report)
