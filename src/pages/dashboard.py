import html

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import calendar

from src.components.cards import (
    EXPENSE_COLOR,
    INCOME_COLOR,
    INVESTMENT_COLOR,
    LIQUIDITY_COLOR,
    BALANCE_COLOR,
    render_hero_card,
    render_html,
    render_info_card,
    render_kpi_card,
)
from src.services.importer import get_category_icon
from src.services.movement_service import load_movements


INVESTMENT_CATEGORY = "Investimenti"


def euro(value: float) -> str:
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def signed_euro(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{euro(value)}"


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
        # Periodo corrente: oggi e i 3 mesi precedenti come
        # intervallo continuo di pari durata.
        current_start = today - pd.DateOffset(months=3)
        previous_end = current_start - pd.Timedelta(days=1)
        previous_start = previous_end - pd.DateOffset(months=3)

        return previous_start, previous_end

    if period == "Ultimi 6 mesi":
        current_start = today - pd.DateOffset(months=6)
        previous_end = current_start - pd.Timedelta(days=1)
        previous_start = previous_end - pd.DateOffset(months=6)

        return previous_start, previous_end

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
            "#22c55e",
        )

    return (
        f"↑ {formatted_percentage}% vs periodo prec.",
        "#ef4444",
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
    st.title("🏠 Dashboard")
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
        render_kpi_card("Entrate", euro(entrate), "💰", INCOME_COLOR)

    with k2:
        render_kpi_card("Uscite", euro(uscite), "💸", EXPENSE_COLOR)

    with k3:
        render_kpi_card(
            "Investimenti",
            euro(investimenti),
            "📈",
            INVESTMENT_COLOR,
        )

    with k4:
        render_kpi_card(
            "Liquidità",
            signed_euro(liquidita),
            "💵",
            liquidity_color,
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

    left_col, right_col = st.columns([1.4, 1])

    with left_col:
        st.markdown("### 📊 Dove sono andati i soldi?")

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
                            colors=[
                                "#22c55e",
                                "#3b82f6",
                                "#f59e0b",
                                "#8b5cf6",
                                "#ef4444",
                                "#14b8a6",
                                "#94a3b8",
                                "#ec4899",
                            ],
                            line=dict(
                                color="rgba(15,23,42,0.95)",
                                width=3,
                            ),
                        ),
                    )
                ]
            )

            fig.update_layout(
                height=390,
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
                        font=dict(size=18, color="#f8fafc"),
                        showarrow=False,
                    )
                ],
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False},
            )

            for _, item in category_df.iterrows():
                percentage = item["importo"] / total_expenses * 100
                category = str(item["categoria"])
                amount = euro(float(item["importo"]))

                render_html(
                    f"""
                    <div style="
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                        gap:12px;
                        padding:8px 0;
                        border-bottom:1px solid rgba(148,163,184,0.10);
                    ">
                        <div style="font-weight:700;">
                            {html.escape(get_category_icon(category))}
                            {html.escape(category)}
                        </div>
                        <div style="color:#94a3b8;white-space:nowrap;">
                            {html.escape(amount)} · {percentage:.1f}%
                        </div>
                    </div>
                    """
                )

    with right_col:
        st.markdown("### 🕒 Ultimi movimenti")

        latest = filtered_df.sort_values("data", ascending=False).head(6)

        for _, row in latest.iterrows():
            amount = float(row["importo"])
            category = str(row["categoria"])
            is_investment = category == INVESTMENT_CATEGORY

            if is_investment:
                amount_color = INVESTMENT_COLOR
                displayed_amount = euro(abs(amount))
            else:
                amount_color = INCOME_COLOR if amount > 0 else EXPENSE_COLOR
                displayed_amount = (
                    f"+{euro(amount)}" if amount > 0 else euro(amount)
                )

            icon = get_category_icon(category)
            title = row["descrizione_completa"] or row["descrizione"]
            date = (
                row["data"].strftime("%d/%m/%Y")
                if pd.notna(row["data"])
                else ""
            )

            with st.container(border=True):
                render_html(
                    f"""
                    <div style="
                        display:flex;
                        justify-content:space-between;
                        gap:12px;
                    ">
                        <div>
                            <div style="
                                font-size:15px;
                                font-weight:800;
                                color:#f8fafc;
                            ">
                                {html.escape(icon)} {html.escape(str(title))}
                            </div>
                            <div style="
                                font-size:12px;
                                color:#94a3b8;
                                margin-top:4px;
                            ">
                                {html.escape(category)} · {html.escape(date)}
                            </div>
                        </div>
                        <div style="
                            font-size:16px;
                            font-weight:900;
                            color:{amount_color};
                            white-space:nowrap;
                        ">
                            {html.escape(displayed_amount)}
                        </div>
                    </div>
                    """
                )

    st.markdown("### 📈 Andamento mensile")

    trend_df = df.copy()

    if selected_account != "Tutti":
        trend_df = trend_df[
            trend_df["account"] == selected_account
        ].copy()

    monthly_df = (
        trend_df.assign(
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

    monthly_df["bilancio"] = monthly_df["entrate"] - monthly_df["uscite"]
    monthly_df["liquidita"] = (
        monthly_df["bilancio"] - monthly_df["investimenti"]
    )

    fig2 = px.line(
        monthly_df,
        x="mese",
        y=[
            "entrate",
            "uscite",
            "bilancio",
            "investimenti",
            "liquidita",
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
            "bilancio": "Bilancio",
            "investimenti": "Investimenti",
            "liquidita": "Liquidità",
        },
    )

    fig2.update_layout(
        height=420,
        margin=dict(l=10, r=20, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e5e7eb",
        legend_title_text="",
        xaxis_title="",
        yaxis_title="€",
        hovermode="x unified",
    )

    st.plotly_chart(
        fig2,
        use_container_width=True,
        config={"displayModeBar": False},
    )
