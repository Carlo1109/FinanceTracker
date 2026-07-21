import calendar
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from src.components.cards import (
    EXPENSE_COLOR,
    INCOME_COLOR,
    INVESTMENT_COLOR,
    LIQUIDITY_COLOR,
    BALANCE_COLOR,
    render_chart_card,
    render_expense_distribution_card,
    render_hero_card,
    render_info_card,
    render_kpi_card,
)
from src.services.categories import get_category_icon, load_category_definitions
from src.services.movement_service import load_movements
from src.theme.colors import get_category_colors
from src.utils.formatting import euro, signed_euro


INVESTMENT_CATEGORY = "Investimenti"


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


def render_category_pie_chart(fig: go.Figure, *, height: int = 420) -> None:
    """
    Donut in iframe con hover luminoso.

    In WebKit/pywebview CSS filter:brightness sulle path spesso non si vede:
    usiamo Plotly.restyle dei colori (+ fill SVG di backup).
    """
    trace = fig.data[0] if fig.data else None
    base_colors = (
        [str(color) for color in (trace.marker.colors or [])]
        if trace is not None
        else []
    )
    bright_colors = [
        _mix_rgb(color, (255, 255, 255), 0.30) for color in base_colors
    ]
    dim_colors = [_mix_rgb(color, (7, 11, 20), 0.38) for color in base_colors]

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


def get_period_df(
    df: pd.DataFrame,
    period: str,
    selected_month: str | None = None,
) -> pd.DataFrame:
    today = pd.Timestamp.today()
    current_month = today.strftime("%Y-%m")
    previous_month = (today - pd.DateOffset(months=1)).strftime("%Y-%m")

    if period == "Mese specifico" and selected_month:
        return df[df["mese"] == selected_month].copy()

    if period == "Questo mese":
        return df[df["mese"] == current_month].copy()

    if period == "Mese scorso":
        return df[df["mese"] == previous_month].copy()

    if period == "Ultimi 3 mesi":
        start_month = (today - pd.DateOffset(months=2)).to_period("M")
        movement_months = pd.PeriodIndex(df["mese"], freq="M")
        return df[movement_months >= start_month].copy()

    if period == "Ultimi 6 mesi":
        start_month = (today - pd.DateOffset(months=5)).to_period("M")
        movement_months = pd.PeriodIndex(df["mese"], freq="M")
        return df[movement_months >= start_month].copy()

    if period == "Quest'anno":
        return df[df["mese"].str.startswith(str(today.year), na=False)].copy()

    return df.copy()

def normalize_date_column(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    result["data"] = pd.to_datetime(
        result["data"],
        errors="coerce",
        dayfirst=True,
    ).dt.normalize()

    return result.dropna(subset=["data"])

def get_previous_period_bounds(
    period: str,
    selected_month: str | None = None,
) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    today = pd.Timestamp.today().normalize()

    if period == "Questo mese":
        current_start = today.replace(day=1)
        previous_month_end = current_start - pd.Timedelta(days=1)
        previous_start = previous_month_end.replace(day=1)

        comparison_day = min(
            today.day,
            previous_month_end.days_in_month,
        )

        previous_end = previous_start + pd.Timedelta(
            days=comparison_day - 1
        )

        return previous_start, previous_end

    if period == "Mese scorso":
        current_month_start = today.replace(day=1)
        last_month_end = current_month_start - pd.Timedelta(days=1)

        previous_end = last_month_end.replace(day=1) - pd.Timedelta(days=1)
        previous_start = previous_end.replace(day=1)

        return previous_start, previous_end

    if period == "Mese specifico" and selected_month:
        current_period = pd.Period(selected_month, freq="M")
        previous_period = current_period - 1

        return (
            previous_period.start_time.normalize(),
            previous_period.end_time.normalize(),
        )

    if period == "Ultimi 3 mesi":
        # Allineato a get_period_df: 3 mesi di calendario (incluso quello corrente).
        current_start_month = (
            today - pd.DateOffset(months=2)
        ).to_period("M")
        previous_end_month = current_start_month - 1
        previous_start_month = previous_end_month - 2

        return (
            previous_start_month.start_time.normalize(),
            previous_end_month.end_time.normalize(),
        )

    if period == "Ultimi 6 mesi":
        # Allineato a get_period_df: 6 mesi di calendario (incluso quello corrente).
        current_start_month = (
            today - pd.DateOffset(months=5)
        ).to_period("M")
        previous_end_month = current_start_month - 1
        previous_start_month = previous_end_month - 5

        return (
            previous_start_month.start_time.normalize(),
            previous_end_month.end_time.normalize(),
        )
    if period == "Quest'anno":
        previous_start = pd.Timestamp(
            year=today.year - 1,
            month=1,
            day=1,
        )

        previous_month_days = calendar.monthrange(
            today.year - 1,
            today.month,
        )[1]

        previous_end = pd.Timestamp(
            year=today.year - 1,
            month=today.month,
            day=min(today.day, previous_month_days),
        )

        return previous_start, previous_end

    # Per "Tutto" non esiste un periodo precedente equivalente.
    return None


def calculate_period_days(
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> int:
    return max(
        int((end_date - start_date).days) + 1,
        1,
    )

def calculate_daily_expense(
    period_df: pd.DataFrame,
    period_days: int,
) -> float:
    metrics = calculate_financial_metrics(period_df)
    expenses = float(metrics["uscite"])

    if period_days <= 0:
        return 0.0

    return expenses / period_days


def get_daily_expense_comparison(
    current_average: float,
    previous_average: float,
) -> tuple[str | None, str]:
    if previous_average <= 0:
        return None, "#94a3b8"

    percentage_change = (
        (current_average - previous_average)
        / previous_average
        * 100
    )

    if abs(percentage_change) < 0.05:
        return "≈ In linea col periodo prec.", "#94a3b8"

    formatted_percentage = (
        f"{abs(percentage_change):.1f}".replace(".", ",")
    )

    if percentage_change < 0:
        return (
            f"↓ {formatted_percentage}% vs periodo prec.",
            "#34d399",
        )

    return (
        f"↑ {formatted_percentage}% vs periodo prec.",
        "#f87171",
    )


def get_period_day_count(
    df: pd.DataFrame,
    period: str,
    selected_month: str | None = None,
) -> int:
    """
    Restituisce i giorni del periodo selezionato.

    La media giornaliera deve dipendere dal periodo scelto, non solamente
    dalle date in cui sono presenti movimenti.
    """
    today = pd.Timestamp.today().normalize()

    if period == "Questo mese":
        return today.day

    if period == "Mese scorso":
        previous_month = today - pd.DateOffset(months=1)
        return int(previous_month.days_in_month)

    if period == "Mese specifico" and selected_month:
        selected_period = pd.Period(selected_month, freq="M")

        if selected_period == today.to_period("M"):
            return today.day

        return int(selected_period.days_in_month)

    if period == "Ultimi 3 mesi":
        start_date = (today - pd.DateOffset(months=2)).replace(day=1)
        return max((today - start_date).days + 1, 1)

    if period == "Ultimi 6 mesi":
        start_date = (today - pd.DateOffset(months=5)).replace(day=1)
        return max((today - start_date).days + 1, 1)

    if period == "Quest'anno":
        start_date = pd.Timestamp(year=today.year, month=1, day=1)
        return max((today - start_date).days + 1, 1)

    valid_dates = pd.to_datetime(
        df["data"],
        errors="coerce",
        dayfirst=True,
    ).dropna()

    if len(valid_dates) >= 2:
        first_date = valid_dates.min().normalize()
        last_date = valid_dates.max().normalize()

        if last_date > first_date:
            return max((last_date - first_date).days + 1, 1)

    valid_months = df["mese"].dropna().astype(str)

    if not valid_months.empty:
        month_periods = pd.PeriodIndex(valid_months, freq="M")
        first_month = month_periods.min()
        last_month = month_periods.max()

        start_date = first_month.start_time.normalize()

        if last_month == today.to_period("M"):
            end_date = today
        else:
            end_date = last_month.end_time.normalize()

        return max((end_date - start_date).days + 1, 1)

    return 1



def calculate_financial_metrics(df: pd.DataFrame) -> dict[str, float]:
    entrate = float(df.loc[df["importo"] > 0, "importo"].sum())

    uscite = float(
        abs(
            df.loc[
                (df["importo"] < 0)
                & (df["categoria"] != INVESTMENT_CATEGORY),
                "importo",
            ].sum()
        )
    )

    investimenti = float(
        abs(
            df.loc[
                (df["importo"] < 0)
                & (df["categoria"] == INVESTMENT_CATEGORY),
                "importo",
            ].sum()
        )
    )

    bilancio = entrate - uscite
    liquidita = bilancio - investimenti

    return {
        "entrate": entrate,
        "uscite": uscite,
        "bilancio": bilancio,
        "investimenti": investimenti,
        "liquidita": liquidita,
    }


def show_dashboard() -> None:
    st.title("Dashboard")
    st.caption("Panoramica generale delle tue finanze.")

    df = load_movements()

    if df.empty:
        st.info(
            "Importa un file Fineco o aggiungi un movimento manuale "
            "per visualizzare la dashboard."
        )
        return

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
        st.warning("Nessun movimento trovato per i filtri selezionati.")
        return

    metrics = calculate_financial_metrics(filtered_df)
    entrate = metrics["entrate"]
    uscite = metrics["uscite"]
    bilancio = metrics["bilancio"]
    investimenti = metrics["investimenti"]
    liquidita = metrics["liquidita"]

    expense_df = filtered_df[
        (filtered_df["importo"] < 0)
        & (filtered_df["categoria"] != INVESTMENT_CATEGORY)
    ].copy()

    period_days = get_period_day_count(
        filtered_df,
        period,
        selected_month,
    )
    avg_daily_expense = uscite / period_days if period_days > 0 else 0.0

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
    daily_comparison_color = "#94a3b8"
    previous_daily_expense = 0.0

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

    top_category = "Nessuna"
    top_category_amount = 0.0

    if not expense_df.empty:
        top_row = (
            expense_df.groupby("categoria")["importo"]
            .sum()
            .abs()
            .sort_values(ascending=False)
            .head(1)
        )
        top_category = str(top_row.index[0])
        top_category_amount = float(top_row.iloc[0])

    balance_color = BALANCE_COLOR if bilancio >= 0 else EXPENSE_COLOR
    liquidity_color = LIQUIDITY_COLOR if liquidita >= 0 else EXPENSE_COLOR

    render_hero_card(
        title="BILANCIO DEL PERIODO",
        main_value=signed_euro(bilancio),
        main_color=balance_color,
    )

    st.markdown("")

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        render_kpi_card("Entrate", euro(entrate), value_color=INCOME_COLOR)

    with k2:
        render_kpi_card("Uscite", euro(uscite), value_color=EXPENSE_COLOR)

    with k3:
        render_kpi_card(
            "Investimenti",
            euro(investimenti),
            value_color=INVESTMENT_COLOR,
        )

    with k4:
        render_kpi_card(
            "Liquidità",
            signed_euro(liquidita),
            value_color=liquidity_color,
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
            "Movimenti",
            str(len(filtered_df)),
        )

    st.markdown(
        '<div class="ft-section-title">Dove sono andati i soldi</div>',
        unsafe_allow_html=True,
    )

    category_df = (
        expense_df.groupby("categoria", as_index=False)["importo"]
        .sum()
        .assign(importo=lambda x: x["importo"].abs())
        .sort_values("importo", ascending=False)
    )

    if category_df.empty:
        st.info("Nessuna uscita da mostrare per questo periodo.")
    else:
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
                            color="rgba(7,11,20,0.95)",
                            width=2,
                        ),
                    ),
                    hoverlabel=dict(
                        bgcolor="rgba(11,18,32,0.96)",
                        bordercolor="#60a5fa",
                        font=dict(
                            size=13,
                            color="#eef3ff",
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
            font_color="#e5e7eb",
            showlegend=False,
            annotations=[
                dict(
                    text=(
                        f"<b>{euro(total_expenses)}</b><br>"
                        "<span style='font-size:12px;color:#94a3b8'>"
                        "Totale uscite"
                        "</span>"
                    ),
                    x=0.5,
                    y=0.5,
                    font=dict(
                        size=18,
                        color="#eef3ff",
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

    st.markdown(
        '<div class="ft-section-title">Andamento mensile</div>',
        unsafe_allow_html=True,
    )

    monthly_df = (
        filtered_df.assign(
            entrate=lambda x: x["importo"].where(x["importo"] > 0, 0),
            uscite=lambda x: x["importo"].where(
                (x["importo"] < 0)
                & (x["categoria"] != INVESTMENT_CATEGORY),
                0,
            ).abs(),
            investimenti=lambda x: x["importo"].where(
                (x["importo"] < 0)
                & (x["categoria"] == INVESTMENT_CATEGORY),
                0,
            ).abs(),
        )
        .groupby("mese", as_index=False)[
            ["entrate", "uscite", "investimenti"]
        ]
        .sum()
        .sort_values("mese")
    )

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
            "entrate": INCOME_COLOR,
            "uscite": EXPENSE_COLOR,
            "investimenti": INVESTMENT_COLOR,
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
        font=dict(color="#94a3b8", family="Manrope"),
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
