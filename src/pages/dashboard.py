import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import html

from src.components.cards import (
    EXPENSE_COLOR,
    INCOME_COLOR,
    INVESTMENT_COLOR,
    LIQUIDITY_COLOR,
    BALANCE_COLOR,
    MUTED_COLOR,
    render_chart_card,
    render_expense_distribution_card,
    render_hero_card,
    render_html,
    render_info_card,
    render_kpi_card,
    render_section_title,
)
from src.components.date_input import themed_date_input
from src.components.navigation import switch_to
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
    get_value_comparison,
    monthly_flow_totals,
    normalize_date_column,
    refund_income,
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
from src.theme.colors import get_category_colors
from src.theme.tokens import resolve_semantic
from src.utils.formatting import euro, signed_euro



def _mix_rgb(color: str, target: tuple[int, int, int], amount: float) -> str:
    raw = str(color).strip()
    if raw.startswith("#"):
        hex_value = raw[1:]
        if len(hex_value) == 3:
            hex_value = "".join(ch * 2 for ch in hex_value)
        rgb = (
            int(hex_value[0:2], 16),
            int(hex_value[2:4], 16),
            int(hex_value[4:6], 16),
        )
    else:
        parts = [
            int(part)
            for part in raw.replace("rgba", "rgb").strip("rgb() ").split(",")[:3]
        ]
        rgb = (parts[0], parts[1], parts[2]) if len(parts) == 3 else (128, 128, 128)

    mixed = tuple(
        max(0, min(255, int(round(channel + (goal - channel) * amount))))
        for channel, goal in zip(rgb, target)
    )
    return "rgb({},{},{})".format(*mixed)


def render_category_pie_chart(
    fig: go.Figure,
    *,
    height: int = 420,
    root_id: str = "ft-pie-root",
) -> None:
    """Donut in iframe con hover luminoso (WebKit-friendly via Plotly.restyle)."""
    trace = fig.data[0] if fig.data else None
    base_colors = (
        [str(color) for color in (trace.marker.colors or [])]
        if trace is not None
        else []
    )
    from src.services.settings_service import get_theme_mode

    is_light = get_theme_mode() == "light"
    # Sul chiaro: spegnere = scurire (non schiarire verso lo sfondo).
    if is_light:
        bright_colors = [
            _mix_rgb(color, (255, 255, 255), 0.22) for color in base_colors
        ]
        dim_colors = [
            _mix_rgb(color, (15, 23, 42), 0.42) for color in base_colors
        ]
    else:
        bright_colors = [
            _mix_rgb(color, (255, 255, 255), 0.30) for color in base_colors
        ]
        dim_colors = [
            _mix_rgb(color, (7, 11, 20), 0.38) for color in base_colors
        ]

    fig.update_layout(
        autosize=True,
        margin=dict(l=4, r=4, t=4, b=4),
        height=max(height - 20, 300),
    )

    chart_html = pio.to_html(
        fig,
        include_plotlyjs=True,
        full_html=False,
        config={"displayModeBar": False, "responsive": True},
    )

    base_json = json.dumps(base_colors)
    bright_json = json.dumps(bright_colors)
    dim_json = json.dumps(dim_colors)

    st.iframe(
        f"""
        <style>
          html, body {{
            margin: 0;
            padding: 0;
            background: transparent !important;
            overflow: hidden;
          }}
        </style>
        <div id="{root_id}" style="
          width:100%;
          height:100%;
          filter: drop-shadow(0 8px 14px rgba(0,0,0,0.22));
        ">
          {chart_html}
        </div>
        <script>
        (function () {{
          const BASE = {base_json};
          const BRIGHT = {bright_json};
          const DIM = {dim_json};
          const ROOT = {json.dumps(root_id)};

          function slicePaths(gd) {{
            let paths = gd.querySelectorAll('.pielayer g.slice path');
            if (!paths.length) {{
              paths = gd.querySelectorAll('.pielayer .trace path');
            }}
            return paths;
          }}

          function colorsFor(active) {{
            if (active < 0) return BASE;
            return BASE.map(function (_color, index) {{
              return index === active ? BRIGHT[index] : DIM[index];
            }});
          }}

          function paintFills(gd, active) {{
            const paths = slicePaths(gd);
            const colors = colorsFor(active);
            for (let i = 0; i < paths.length && i < colors.length; i++) {{
              paths[i].setAttribute('fill', colors[i]);
            }}
          }}

          function setActive(gd, active) {{
            const colors = colorsFor(active);
            Plotly.restyle(gd, {{ 'marker.colors': [colors] }}, [0]).then(function () {{
              paintFills(gd, active);
            }}).catch(function () {{
              paintFills(gd, active);
            }});
          }}

          function bind(gd) {{
            if (!gd || gd._ftPieHoverBound) return;
            gd._ftPieHoverBound = true;
            let last = -1;

            gd.on('plotly_hover', function (ev) {{
              if (!ev.points || !ev.points.length) return;
              const index = ev.points[0].pointNumber;
              if (index === last) return;
              last = index;
              setActive(gd, index);
            }});

            gd.on('plotly_unhover', function () {{
              last = -1;
              setActive(gd, -1);
            }});
          }}

          function tryBind(left) {{
            const plots = document.querySelectorAll('#' + ROOT + ' .js-plotly-plot');
            const gd = plots[plots.length - 1];
            if (gd && typeof Plotly !== 'undefined' && gd.data) {{
              bind(gd);
              try {{ Plotly.Plots.resize(gd); }} catch (error) {{}}
              return;
            }}
            if (left <= 0) return;
            setTimeout(function () {{ tryBind(left - 1); }}, 40);
          }}

          tryBind(50);
        }})();
        </script>
        """,
        height=height,
        width="stretch",
    )



def _render_category_breakdown_section(
    category_df: pd.DataFrame,
    *,
    empty_message: str,
    center_caption: str,
    card_key: str,
    pie_root_id: str,
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
    category_df["label"] = category_df["categoria"].apply(
        lambda category: f"{get_category_icon(category)} {category}"
    )
    total_amount = float(category_df["importo"].sum())
    category_definitions = load_category_definitions()
    pie_colors = get_category_colors(
        category_df["categoria"].astype(str).tolist(),
        category_definitions,
    )
    sem = resolve_semantic()

    fig = go.Figure(
        data=[
            go.Pie(
                labels=category_df["label"],
                values=category_df["importo"],
                hole=0.68,
                sort=False,
                direction="clockwise",
                textinfo="none",
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "%{value:.2f} €<br>"
                    "%{percent}<extra></extra>"
                ),
                marker=dict(
                    colors=pie_colors,
                    line=dict(
                        color=sem.pie_outline,
                        width=2,
                    ),
                ),
                hoverlabel=dict(
                    bgcolor=sem.hover_bg,
                    bordercolor=sem.info,
                    font=dict(
                        size=13,
                        color=sem.text,
                        family="Manrope",
                    ),
                ),
            )
        ]
    )

    fig.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=sem.text,
        showlegend=False,
        annotations=[
            dict(
                text=(
                    f"<b>{euro(total_amount)}</b><br>"
                    f"<span style='font-size:12px;color:{sem.muted}'>"
                    f"{html.escape(center_caption)}"
                    "</span>"
                ),
                x=0.5,
                y=0.5,
                font=dict(
                    size=18,
                    color=sem.text,
                    family="Manrope",
                ),
                showarrow=False,
            )
        ],
    )

    breakdown_rows = []
    for _, item in category_df.iterrows():
        percentage = float(item["importo"]) / total_amount * 100
        category = str(item["categoria"])
        breakdown_rows.append(
            {
                "icon": get_category_icon(category),
                "name": category,
                "amount": euro(float(item["importo"])),
                "percent": percentage,
                "color": pie_colors[len(breakdown_rows)],
            }
        )

    render_expense_distribution_card(
        breakdown_rows,
        total_label=euro(total_amount),
        render_pie=lambda: render_category_pie_chart(
            fig,
            height=420,
            root_id=pie_root_id,
        ),
        list_max_height=360,
        key=card_key,
    )


_RESTORE_KEY = "dashboard_restore_open"


def _close_restore_dialog() -> None:
    st.session_state.pop(_RESTORE_KEY, None)


@st.dialog("Parti da un backup", on_dismiss=_close_restore_dialog)
def _restore_backup_dialog() -> None:
    st.caption(
        "Sostituisce database e categorie con lo zip di backup. "
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


def show_dashboard() -> None:
    st.title("Dashboard")

    df = load_movements()

    if df.empty:
        st.caption("Panoramica generale delle tue finanze.")
        render_html(
            f"""
            <div class="ft-empty-hero" style="
                margin-top:12px;
                padding:42px 28px 36px 28px;
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
                text-align:left;
            ">
                <div style="
                    font-family:Fraunces,Georgia,serif;
                    font-size:clamp(34px, 4vw, 48px);
                    font-weight:700;
                    color:var(--ft-text);
                    letter-spacing:-0.03em;
                    line-height:1.05;
                ">Finance<span style="color:var(--ft-accent)">Tracker</span></div>
                <div style="
                    margin-top:10px;
                    display:inline-flex;
                    align-items:center;
                    gap:8px;
                    padding:6px 12px;
                    border-radius:999px;
                    background:rgba(var(--ft-accent-rgb), 0.14);
                    color:var(--ft-accent);
                    font-size:12px;
                    font-weight:700;
                ">
                    <span style="
                        width:8px;height:8px;border-radius:999px;
                        background:var(--ft-accent);
                        box-shadow:0 0 0 3px rgba(var(--ft-accent-rgb), 0.25);
                    "></span>
                    Inizia da qui
                </div>
                <div style="
                    margin-top:14px;
                    max-width:34rem;
                    font-size:16px;
                    line-height:1.5;
                    color:var(--ft-muted);
                ">
                    Nessun movimento ancora. Importa un estratto conto,
                    aggiungi il primo movimento oppure parti da un backup.
                </div>
            </div>
            """
        )
        st.markdown("")
        if st.session_state.get(_RESTORE_KEY):
            _restore_backup_dialog()
        c1, c2, c3, _ = st.columns([1.2, 1.3, 1.5, 1.2])
        with c1:
            if st.button(
                "Importa dati",
                type="primary",
                width="stretch",
            ):
                switch_to("import_data")
        with c2:
            if st.button(
                "Nuovo movimento",
                type="secondary",
                width="stretch",
            ):
                switch_to("manual_entry")
        with c3:
            if st.button(
                "Parti da un backup",
                type="secondary",
                width="stretch",
            ):
                st.session_state[_RESTORE_KEY] = True
                st.rerun()
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

    period_options = [
        "Questo mese",
        "Mese scorso",
        "Mese specifico",
        PERIOD_CUSTOM,
        "Ultimi 3 mesi",
        "Ultimi 6 mesi",
        "Quest'anno",
        "Tutto",
    ]
    if "dashboard_period" not in st.session_state:
        st.session_state["dashboard_period"] = "Tutto"
    period = st.session_state["dashboard_period"]
    if period in PERIOD_CUSTOM_ALIASES:
        period = PERIOD_CUSTOM
    if period not in period_options:
        period = "Tutto"
    st.session_state["dashboard_period"] = period

    selected_month = None
    custom_start = None
    custom_end = None
    dated_all_bounds = dated_all
    min_data = (
        dated_all_bounds["data"].min().date()
        if not dated_all_bounds.empty
        else pd.Timestamp.today().date()
    )
    max_data = (
        dated_all_bounds["data"].max().date()
        if not dated_all_bounds.empty
        else pd.Timestamp.today().date()
    )

    period = st.selectbox(
        "Periodo",
        period_options,
        key="dashboard_period",
    )
    if period == "Mese specifico" and months:
        selected_month = st.selectbox(
            "Mese",
            months,
            key="dashboard_month",
        )
    elif period == PERIOD_CUSTOM:
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

    selected_accounts = st.pills(
        "Conti",
        accounts,
        selection_mode="multi",
        default=[],
        key="dashboard_accounts",
        help="Nessuno selezionato = tutti i conti.",
    )
    selected_accounts = list(selected_accounts or [])

    selected_types = st.pills(
        "Tipo",
        list(MOVEMENT_TYPE_FILTERS),
        selection_mode="multi",
        default=[],
        key="dashboard_types",
        help="Nessuno selezionato = tutti i movimenti.",
    )
    selected_types = list(selected_types or [])

    custom_start_ts = (
        pd.Timestamp(custom_start).normalize() if custom_start else None
    )
    custom_end_ts = (
        pd.Timestamp(custom_end).normalize() if custom_end else None
    )

    filtered_df = get_period_df(
        df,
        period,
        selected_month,
        custom_start=custom_start_ts,
        custom_end=custom_end_ts,
    )
    filtered_df = filter_by_accounts(filtered_df, selected_accounts)
    filtered_df = filter_by_movement_types(filtered_df, selected_types)

    if filtered_df.empty:
        st.warning(
            "Nessun movimento trovato per i filtri selezionati (0 risultati)."
        )
        return

    metrics = calculate_financial_metrics(filtered_df)
    entrate = metrics["entrate"]
    uscite = metrics["uscite"]
    bilancio = metrics["bilancio"]
    investimenti = metrics["investimenti"]
    account_scope = filter_by_accounts(df, selected_accounts)
    analysis_start, analysis_end = resolve_analysis_bounds(
        filtered_df,
        period,
        selected_month,
        custom_start=custom_start_ts,
        custom_end=custom_end_ts,
    )
    saldo = calculate_account_balance(account_scope, through=analysis_end)

    period_days = get_period_day_count(
        filtered_df,
        period,
        selected_month,
        custom_start=custom_start_ts,
        custom_end=custom_end_ts,
    )
    specials_source_df = filter_by_accounts(dated_all, selected_accounts)

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

    daily_footer_parts = [f"su {period_days} giorni"]
    amortized_count = int(special_summary["amortized_count"])
    amortized_amount = float(special_summary["amortized_amount"])
    excluded_count = int(special_summary["excluded_count"])
    excluded_total = float(special_summary["excluded_total"])
    if amortized_count > 0:
        noun = "ripartita" if amortized_count == 1 else "ripartite"
        daily_footer_parts.append(
            f"{amortized_count} {noun} ({euro(amortized_amount)} nel periodo)"
        )
    if excluded_count > 0:
        noun = "esclusa" if excluded_count == 1 else "escluse"
        daily_footer_parts.append(
            f"{excluded_count} {noun} ({euro(excluded_total)})"
        )
    daily_footer = " · ".join(daily_footer_parts)

    comparison_source_df = filter_by_accounts(
        normalize_date_column(df),
        selected_accounts,
    )

    previous_bounds = get_previous_period_bounds(
        period=period,
        selected_month=selected_month,
        custom_start=custom_start_ts,
        custom_end=custom_end_ts,
    )

    daily_comparison_text = None
    daily_comparison_color = MUTED_COLOR
    previous_metrics: dict[str, float] | None = None

    if previous_bounds is not None:
        previous_start, previous_end = previous_bounds

        previous_period_df = comparison_source_df[
            comparison_source_df["data"].between(
                previous_start,
                previous_end,
                inclusive="both",
            )
        ].copy()
        previous_period_df = filter_by_movement_types(
            previous_period_df,
            selected_types,
        )

        previous_period_days = calculate_period_days(
            previous_start,
            previous_end,
        )

        previous_metrics = calculate_financial_metrics(previous_period_df)
        previous_daily_expense = calculate_daily_expense(
            previous_period_df,
            previous_period_days,
            source_df=comparison_source_df,
            period_start=previous_start,
            period_end=previous_end,
        )

        daily_comparison_text, daily_comparison_color = (
            get_daily_expense_comparison(
                current_average=avg_daily_expense,
                previous_average=previous_daily_expense,
            )
        )

    def metric_delta(
        key: str,
        *,
        higher_is_better: bool,
    ) -> tuple[str | None, str]:
        if previous_metrics is None:
            return None, MUTED_COLOR
        return get_value_comparison(
            metrics[key],
            previous_metrics[key],
            higher_is_better=higher_is_better,
        )

    bilancio_delta, bilancio_delta_color = metric_delta(
        "bilancio",
        higher_is_better=True,
    )
    entrate_delta, entrate_delta_color = metric_delta(
        "entrate",
        higher_is_better=True,
    )
    uscite_delta, uscite_delta_color = metric_delta(
        "uscite",
        higher_is_better=False,
    )
    investimenti_delta, investimenti_delta_color = metric_delta(
        "investimenti",
        higher_is_better=True,
    )
    previous_saldo = None
    if previous_bounds is not None:
        previous_saldo = calculate_account_balance(
            account_scope,
            through=previous_bounds[1],
        )
    if previous_saldo is None:
        saldo_delta, saldo_delta_color = None, MUTED_COLOR
    else:
        saldo_delta, saldo_delta_color = get_value_comparison(
            saldo,
            previous_saldo,
            higher_is_better=True,
        )

    comparison_caption = None
    if previous_bounds is not None:
        current_bounds = get_current_period_bounds(
            period,
            selected_month,
            custom_start=custom_start_ts,
            custom_end=custom_end_ts,
        )
        if current_bounds is not None:
            comparison_caption = format_comparison_caption(
                current_bounds[0],
                current_bounds[1],
                previous_bounds[0],
                previous_bounds[1],
            )

    top = top_expense_category(filtered_df)
    if top is None:
        top_category = "Nessuna"
        top_category_amount = 0.0
    else:
        top_category, top_category_amount = top

    top_income = top_income_category(filtered_df)
    if top_income is None:
        top_income_category_name = "Nessuna"
        top_income_amount = 0.0
    else:
        top_income_category_name, top_income_amount = top_income

    balance_color = BALANCE_COLOR if bilancio >= 0 else EXPENSE_COLOR
    liquidity_color = LIQUIDITY_COLOR if saldo >= 0 else EXPENSE_COLOR

    exclude_refunds = bool(
        st.session_state.get("dashboard_savings_ex_refunds", False)
    )
    refunds = refund_income(filtered_df)
    rate = savings_rate(
        metrics,
        exclude_refunds=exclude_refunds,
        refunds=refunds,
    )
    if rate is None:
        savings_label = "—"
        savings_color = MUTED_COLOR
        if exclude_refunds and refunds > 0:
            savings_footer = "serve almeno un’entrata oltre i rimborsi"
        else:
            savings_footer = "serve almeno un’entrata"
    else:
        savings_label = f"{rate:.1f}".replace(".", ",") + "%"
        savings_color = INCOME_COLOR if rate >= 0 else EXPENSE_COLOR
        spent_share = f"{(100.0 - rate):.1f}".replace(".", ",")
        refunds_prefix = "senza rimborsi · " if exclude_refunds else ""
        if rate > 0:
            savings_footer = (
                f"{refunds_prefix}{spent_share}% delle entrate è andato in uscite"
            )
        elif rate == 0:
            savings_footer = f"{refunds_prefix}tutto è andato in uscite"
        else:
            savings_footer = f"{refunds_prefix}hai speso più di quanto è entrato"

    if comparison_caption:
        st.caption(f"Confronto: {comparison_caption}")

    account_chip = html.escape(
        accounts_chip_label(selected_accounts, accounts)
    )
    type_chip = html.escape(types_chip_label(selected_types))
    period_chip = html.escape(period)
    render_html(
        f"""
        <div class="ft-appearance-chip" style="margin:4px 0 14px 0;width:fit-content;">
          <span class="ft-appearance-chip-dot"></span>
          {period_chip} · {account_chip} · {type_chip}
        </div>
        """
    )

    render_hero_card(
        title="BILANCIO DEL PERIODO",
        main_value=signed_euro(bilancio),
        main_color=balance_color,
        subtitle=bilancio_delta,
        subtitle_color=bilancio_delta_color,
    )

    st.markdown("")

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        render_kpi_card(
            "Entrate",
            euro(entrate),
            value_color=INCOME_COLOR,
            subtitle=entrate_delta,
            subtitle_color=entrate_delta_color,
        )

    with k2:
        render_kpi_card(
            "Uscite",
            euro(uscite),
            value_color=EXPENSE_COLOR,
            subtitle=uscite_delta,
            subtitle_color=uscite_delta_color,
        )

    with k3:
        render_kpi_card(
            "Investimenti",
            euro(investimenti),
            value_color=INVESTMENT_COLOR,
            subtitle=investimenti_delta,
            subtitle_color=investimenti_delta_color,
        )

    with k4:
        render_kpi_card(
            "Liquidità",
            signed_euro(saldo),
            value_color=liquidity_color,
            subtitle=saldo_delta,
            subtitle_color=saldo_delta_color,
        )

    st.markdown("")

    s1, s2, s3, s4 = st.columns(4)

    with s1:
        render_info_card(
            "Spesa principale",
            f"{get_category_icon(top_category)} {top_category}",
            euro(top_category_amount),
        )

    with s2:
        render_info_card(
            "Fonte principale",
            (
                f"{get_category_icon(top_income_category_name)} "
                f"{top_income_category_name}"
            ),
            euro(top_income_amount),
        )

    with s3:
        render_info_card(
            title="Spesa media giornaliera",
            value=euro(avg_daily_expense),
            subtitle=daily_comparison_text,
            subtitle_color=daily_comparison_color,
            footer=daily_footer,
        )

    with s4:
        render_info_card(
            title="Tasso di risparmio",
            value=savings_label,
            value_color=savings_color,
            footer=savings_footer,
            extra_class="ft-savings-rate-card",
        )
        st.checkbox(
            "Tieni fuori i rimborsi",
            key="dashboard_savings_ex_refunds",
            help=(
                "I rimborsi non sono reddito: toglierli evita di gonfiare "
                "il risparmio. Regali, donazioni e prestiti restano."
            ),
        )

    special_overview = special_expenses_overview(
        specials_source_df,
        analysis_start,
        analysis_end,
    )
    if special_overview.empty:
        render_section_title("Spese speciali")
        render_html(
            """
            <div class="ft-dashboard-card">
              <div class="ft-specials-hint" style="margin:0;">
                Nessuna spesa speciale nel periodo.
                Puoi segnalarle in Movimenti → Dettagli.
              </div>
            </div>
            """
        )
    else:
        special_count = len(special_overview)
        special_total = float(special_overview["importo"].sum())
        render_section_title("Spese speciali")
        rows_html: list[str] = []
        for index, item in special_overview.iterrows():
            date_label = pd.Timestamp(item["data"]).strftime("%d/%m/%Y")
            title = html.escape(
                str(item["descrizione"] or "Senza descrizione")
            )
            category = html.escape(str(item["categoria"] or ""))
            account = html.escape(str(item["account"] or ""))
            mesi_range = html.escape(str(item["mesi_range"] or "—"))
            amount_label = html.escape(euro(float(item["importo"])))
            quota = item["quota_mese"]
            mode_chip = html.escape(str(item["modalita"] or ""))

            if pd.notna(quota):
                quota_block = f"""
                    <div style="
                        margin-top:8px;
                        font-size:12px;
                        color:var(--ft-muted);
                    ">
                      Quota mensile
                      <span style="
                          color:var(--ft-accent-strong);
                          font-weight:700;
                      ">{html.escape(euro(float(quota)))}</span>
                    </div>
                """
                range_block = f"""
                    <div style="
                        display:inline-flex;
                        align-items:center;
                        gap:6px;
                        margin-top:8px;
                        padding:4px 10px;
                        border-radius:999px;
                        background:rgba(var(--ft-accent-rgb),0.10);
                        border:1px solid rgba(var(--ft-accent-rgb),0.22);
                        color:var(--ft-accent-strong);
                        font-size:11px;
                        font-weight:700;
                        letter-spacing:0.01em;
                    ">
                      {mesi_range}
                    </div>
                """
            else:
                quota_block = ""
                range_block = """
                    <div style="
                        margin-top:8px;
                        font-size:12px;
                        color:var(--ft-muted);
                    ">Nessuna ripartizione</div>
                """

            note_text = str(item.get("notes") or "").strip()
            note_block = ""
            if note_text:
                note_block = f"""
                    <div style="
                        margin-top:10px;
                        font-size:13px;
                        line-height:1.45;
                        color:var(--ft-muted);
                        font-style:italic;
                    ">{html.escape(note_text)}</div>
                """

            border = (
                "border-bottom:1px solid var(--ft-border);"
                if int(index) < len(special_overview) - 1
                else ""
            )
            rows_html.append(
                f"""
                <div style="
                    display:flex;
                    justify-content:space-between;
                    gap:18px;
                    padding:16px 2px;
                    {border}
                    flex-wrap:wrap;
                ">
                  <div style="min-width:min(100%, 280px);flex:1;">
                    <div style="
                        font-size:15px;
                        font-weight:700;
                        color:var(--ft-text);
                        line-height:1.35;
                    ">{title}</div>
                    <div style="
                        margin-top:8px;
                        display:flex;
                        flex-wrap:wrap;
                        gap:8px;
                        align-items:center;
                        font-size:12px;
                        color:var(--ft-muted);
                    ">
                      <span style="
                          background:rgba(var(--ft-accent-rgb),0.14);
                          color:var(--ft-accent-strong);
                          padding:3px 8px;
                          border-radius:8px;
                          font-size:11px;
                          font-weight:750;
                      ">{html.escape(get_category_icon(str(item['categoria'])))} {category}</span>
                      <span>{html.escape(date_label)}</span>
                      <span>{account}</span>
                      <span style="
                          padding:3px 8px;
                          border-radius:8px;
                          border:1px solid var(--ft-border);
                          background:var(--ft-panel-soft);
                          font-weight:650;
                      ">{mode_chip}</span>
                    </div>
                    {range_block}
                    {quota_block}
                    {note_block}
                  </div>
                  <div style="
                      text-align:right;
                      font-family:Fraunces,Georgia,serif;
                      font-size:22px;
                      font-weight:700;
                      color:var(--ft-danger);
                      white-space:nowrap;
                      padding-top:2px;
                  ">{amount_label}</div>
                </div>
                """
            )

        special_noun = (
            "Spesa speciale" if special_count == 1 else "Spese speciali"
        )
        summary_label = (
            f"{special_count} {special_noun} · "
            f"Totale {euro(special_total)}"
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

    render_section_title("Dove sono andati i soldi")
    _render_category_breakdown_section(
        category_expense_breakdown(filtered_df),
        empty_message="Nessuna uscita da mostrare per questo periodo.",
        center_caption="Totale uscite",
        card_key="ft_dashboard_expense_distribution",
        pie_root_id="ft-pie-expenses",
    )

    render_section_title("Da dove arrivano i soldi")
    _render_category_breakdown_section(
        category_income_breakdown(filtered_df),
        empty_message="Nessuna entrata da mostrare per questo periodo.",
        center_caption="Totale entrate",
        card_key="ft_dashboard_income_distribution",
        pie_root_id="ft-pie-income",
    )

    render_section_title("Andamento mensile")

    sem = resolve_semantic()

    monthly_df = monthly_flow_totals(filtered_df).copy()
    monthly_df["mese"] = monthly_df["mese"].astype(str)

    italian_months = {
        1: "Gen",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "Mag",
        6: "Giu",
        7: "Lug",
        8: "Ago",
        9: "Set",
        10: "Ott",
        11: "Nov",
        12: "Dic",
    }

    monthly_df["_mese_data"] = pd.to_datetime(
        monthly_df["mese"] + "-01",
        format="%Y-%m-%d",
        errors="coerce",
    )

    monthly_df = monthly_df.sort_values(
        "_mese_data",
        kind="stable",
    )

    monthly_df["mese_label"] = monthly_df["_mese_data"].apply(
        lambda value: (
            f"{italian_months[value.month]} {value.year}"
            if pd.notna(value)
            else ""
        )
    )

    month_order = monthly_df["mese_label"].tolist()

    fig2 = px.line(
        monthly_df,
        x="mese_label",
        y=[
            "entrate",
            "uscite",
            "investimenti",
        ],
        markers=True,
        category_orders={
            "mese_label": month_order,
        },
        color_discrete_map={
            "entrate": sem.income,
            "uscite": sem.expense,
            "investimenti": sem.investment,
        },
        labels={
            "mese_label": "",
            "value": "€",
            "variable": "",
            "entrate": "Entrate",
            "uscite": "Uscite",
            "investimenti": "Investimenti",
        },
    )

    flow_labels = {
        "entrate": "Entrate",
        "uscite": "Uscite",
        "investimenti": "Investimenti",
    }

    for trace in fig2.data:
        trace.name = flow_labels.get(trace.name, trace.name)
        trace.hovertemplate = "%{y:,.2f} €<extra></extra>"

    fig2.update_layout(
        height=400,
        margin=dict(l=16, r=20, t=18, b=34),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color=sem.text,
            family="Manrope",
            size=13,
        ),
        legend_title_text="",
        xaxis_title="",
        yaxis_title="",
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=sem.hover_bg,
            bordercolor=sem.info,
            font=dict(
                color=sem.text,
                family="Manrope",
                size=13,
            ),
            namelength=-1,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(
                color=sem.text,
                family="Manrope",
                size=13,
            ),
        ),
        xaxis=dict(
            type="category",
            categoryorder="array",
            categoryarray=month_order,
            tickmode="array",
            tickvals=month_order,
            ticktext=month_order,
            showgrid=False,
            zeroline=False,
            automargin=True,
            tickangle=0,
            tickfont=dict(
                color=sem.muted,
                family="Manrope",
                size=12,
            ),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(148,163,184,0.18)",
            zeroline=False,
            automargin=True,
            tickfont=dict(
                color=sem.muted,
                family="Manrope",
                size=12,
            ),
            tickformat=",.0f",
            ticksuffix=" €",
        ),
    )

    render_chart_card(
        lambda: st.plotly_chart(
            fig2,
            width="stretch",
            theme=None,
            config={
                "displayModeBar": False,
                "responsive": True,
            },
        )
    )
