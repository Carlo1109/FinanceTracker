import json

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
from src.components.navigation import switch_to
from src.services.analytics import (
    calculate_daily_expense,
    calculate_financial_metrics,
    calculate_period_days,
    category_expense_breakdown,
    format_comparison_caption,
    get_current_period_bounds,
    get_daily_expense_comparison,
    get_period_day_count,
    get_period_df,
    get_previous_period_bounds,
    get_value_comparison,
    monthly_flow_totals,
    normalize_date_column,
    savings_rate,
    top_expense_category,
)
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
        <div id="ft-pie-root" style="
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
            const plots = document.querySelectorAll('#ft-pie-root .js-plotly-plot');
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
                    Nessun movimento ancora. Importa un estratto conto
                    oppure aggiungi il primo movimento manualmente.
                </div>
            </div>
            """
        )
        st.markdown("")
        c1, c2, _ = st.columns([1.2, 1.2, 2])
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

    f1, f2, f3 = st.columns([1.4, 1.4, 1.4])

    with f1:
        period = st.selectbox(
            "Periodo",
            [
                "Questo mese",
                "Mese scorso",
                "Mese specifico",
                "Ultimi 3 mesi",
                "Ultimi 6 mesi",
                "Quest'anno",
                "Tutto",
            ],
            index=6,
        )

    selected_month = None

    with f2:
        if period == "Mese specifico":
            selected_month = st.selectbox("Mese", months)
        else:
            st.selectbox("Mese", ["Automatico"], disabled=True)

    with f3:
        selected_account = st.selectbox("Conto", ["Tutti"] + accounts)

    filtered_df = get_period_df(df, period, selected_month)

    if selected_account != "Tutti":
        filtered_df = filtered_df[
            filtered_df["account"] == selected_account
        ].copy()

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
    liquidita = metrics["liquidita"]

    period_days = get_period_day_count(
        filtered_df,
        period,
        selected_month,
    )
    avg_daily_expense = calculate_daily_expense(filtered_df, period_days)

    comparison_source_df = normalize_date_column(df)

    if selected_account != "Tutti":
        comparison_source_df = comparison_source_df[
            comparison_source_df["account"] == selected_account
        ].copy()


    previous_bounds = get_previous_period_bounds(
        period=period,
        selected_month=selected_month,
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

        previous_period_days = calculate_period_days(
            previous_start,
            previous_end,
        )

        previous_metrics = calculate_financial_metrics(previous_period_df)
        previous_daily_expense = calculate_daily_expense(
            previous_period_df,
            previous_period_days,
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
    liquidita_delta, liquidita_delta_color = metric_delta(
        "liquidita",
        higher_is_better=True,
    )

    comparison_caption = None
    if previous_bounds is not None:
        current_bounds = get_current_period_bounds(period, selected_month)
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

    balance_color = BALANCE_COLOR if bilancio >= 0 else EXPENSE_COLOR
    liquidity_color = LIQUIDITY_COLOR if liquidita >= 0 else EXPENSE_COLOR

    rate = savings_rate(metrics)
    if rate is None:
        savings_label = "—"
        savings_color = MUTED_COLOR
        savings_footer = "serve almeno un’entrata"
    else:
        savings_label = f"{rate:.1f}".replace(".", ",") + "%"
        savings_color = INCOME_COLOR if rate >= 0 else EXPENSE_COLOR
        savings_footer = "(entrate − uscite) / entrate"

    if comparison_caption:
        st.caption(f"Confronto: {comparison_caption}")

    account_chip = html.escape(
        selected_account
        if selected_account != "Tutti"
        else "Tutti i conti"
    )
    period_chip = html.escape(period)
    render_html(
        f"""
        <div class="ft-appearance-chip" style="margin:4px 0 14px 0;width:fit-content;">
          <span class="ft-appearance-chip-dot"></span>
          {period_chip} · {account_chip}
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
            signed_euro(liquidita),
            value_color=liquidity_color,
            subtitle=liquidita_delta,
            subtitle_color=liquidita_delta_color,
        )

    st.markdown("")

    s1, s2, s3 = st.columns(3)

    with s1:
        render_info_card(
            "Categoria principale",
            f"{get_category_icon(top_category)} {top_category}",
            euro(top_category_amount),
        )

    with s2:
        render_info_card(
            title="Spesa media giornaliera",
            value=euro(avg_daily_expense),
            subtitle=daily_comparison_text,
            subtitle_color=daily_comparison_color,
            footer=f"su {period_days} giorni",
        )

    with s3:
        render_info_card(
            title="Tasso di risparmio",
            value=savings_label,
            value_color=savings_color,
            footer=savings_footer,
        )

    render_section_title("Dove sono andati i soldi")

    category_df = category_expense_breakdown(filtered_df)
    sem = resolve_semantic()

    if category_df.empty:
        st.info("Nessuna uscita da mostrare per questo periodo.")
    else:
        category_df = category_df.copy()
        category_df["label"] = category_df["categoria"].apply(
            lambda category: f"{get_category_icon(category)} {category}"
        )
        total_expenses = float(category_df["importo"].sum())
        category_definitions = load_category_definitions()
        pie_colors = get_category_colors(
            category_df["categoria"].astype(str).tolist(),
            category_definitions,
        )

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
                        f"<b>{euro(total_expenses)}</b><br>"
                        f"<span style='font-size:12px;color:{sem.muted}'>"
                        "Totale uscite"
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
            percentage = float(item["importo"]) / total_expenses * 100
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
            total_label=euro(total_expenses),
            render_pie=lambda: render_category_pie_chart(fig, height=420),
            list_max_height=360,
        )

    render_section_title("Andamento mensile")

    monthly_df = monthly_flow_totals(filtered_df)

    fig2 = px.line(
        monthly_df,
        x="mese",
        y=[
            "entrate",
            "uscite",
            "investimenti",
        ],
        markers=True,
        color_discrete_map={
            "entrate": sem.income,
            "uscite": sem.expense,
            "investimenti": sem.investment,
        },
        labels={
            "mese": "",
            "value": "€",
            "variable": "",
            "entrate": "Entrate",
            "uscite": "Uscite",
            "investimenti": "Investimenti",
        },
    )

    fig2.update_layout(
        height=400,
        margin=dict(l=10, r=20, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=sem.muted, family="Manrope"),
        legend_title_text="",
        xaxis_title="",
        yaxis_title="",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(148,163,184,0.12)",
            zeroline=False,
        ),
    )

    render_chart_card(
        lambda: st.plotly_chart(
            fig2,
            width="stretch",
            config={"displayModeBar": False},
        )
    )
