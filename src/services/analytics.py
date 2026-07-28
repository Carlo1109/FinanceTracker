"""Helper per KPI, periodi e confronti finanziari."""

from __future__ import annotations

import calendar

import pandas as pd

INVESTMENT_CATEGORY = "Investimenti"

_MONTHS_IT = (
    "gen",
    "feb",
    "mar",
    "apr",
    "mag",
    "giu",
    "lug",
    "ago",
    "set",
    "ott",
    "nov",
    "dic",
)


def format_short_date(value: pd.Timestamp, *, with_year: bool = False) -> str:
    stamp = pd.Timestamp(value).normalize()
    month = _MONTHS_IT[stamp.month - 1]
    if with_year:
        return f"{stamp.day} {month} {stamp.year}"
    return f"{stamp.day} {month}"


def format_date_range(
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> str:
    start = pd.Timestamp(start).normalize()
    end = pd.Timestamp(end).normalize()

    if start == end:
        return format_short_date(start, with_year=True)

    different_years = start.year != end.year
    if different_years:
        return (
            f"{format_short_date(start, with_year=True)} – "
            f"{format_short_date(end, with_year=True)}"
        )

    if start.month == end.month:
        return f"{start.day}–{end.day} {_MONTHS_IT[start.month - 1]}"

    return (
        f"{format_short_date(start)} – {format_short_date(end)}"
    )


def format_comparison_caption(
    current_start: pd.Timestamp,
    current_end: pd.Timestamp,
    previous_start: pd.Timestamp,
    previous_end: pd.Timestamp,
) -> str:
    return (
        f"{format_date_range(current_start, current_end)} "
        f"vs {format_date_range(previous_start, previous_end)}"
    )


def get_current_period_bounds(
    period: str,
    selected_month: str | None = None,
) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    today = pd.Timestamp.today().normalize()

    if period == "Questo mese":
        return today.replace(day=1), today

    if period == "Mese scorso":
        current_month_start = today.replace(day=1)
        last_month_end = current_month_start - pd.Timedelta(days=1)
        return last_month_end.replace(day=1), last_month_end

    if period == "Mese specifico" and selected_month:
        current_period = pd.Period(selected_month, freq="M")
        start = current_period.start_time.normalize()
        end = current_period.end_time.normalize()
        if current_period == today.to_period("M"):
            end = today
        return start, end

    if period == "Ultimi 3 mesi":
        start_month = (today - pd.DateOffset(months=2)).to_period("M")
        return start_month.start_time.normalize(), today

    if period == "Ultimi 6 mesi":
        start_month = (today - pd.DateOffset(months=5)).to_period("M")
        return start_month.start_time.normalize(), today

    if period == "Quest'anno":
        return pd.Timestamp(year=today.year, month=1, day=1), today

    return None


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
        comparison_day = min(today.day, previous_month_end.days_in_month)
        previous_end = previous_start + pd.Timedelta(days=comparison_day - 1)
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
        current_start_month = (today - pd.DateOffset(months=2)).to_period("M")
        previous_end_month = current_start_month - 1
        previous_start_month = previous_end_month - 2
        return (
            previous_start_month.start_time.normalize(),
            previous_end_month.end_time.normalize(),
        )

    if period == "Ultimi 6 mesi":
        current_start_month = (today - pd.DateOffset(months=5)).to_period("M")
        previous_end_month = current_start_month - 1
        previous_start_month = previous_end_month - 5
        return (
            previous_start_month.start_time.normalize(),
            previous_end_month.end_time.normalize(),
        )

    if period == "Quest'anno":
        previous_start = pd.Timestamp(year=today.year - 1, month=1, day=1)
        previous_month_days = calendar.monthrange(today.year - 1, today.month)[1]
        previous_end = pd.Timestamp(
            year=today.year - 1,
            month=today.month,
            day=min(today.day, previous_month_days),
        )
        return previous_start, previous_end

    return None


def calculate_period_days(
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> int:
    return max(int((end_date - start_date).days) + 1, 1)


def calculate_financial_metrics(df: pd.DataFrame) -> dict[str, float]:
    if df.empty:
        return {
            "entrate": 0.0,
            "uscite": 0.0,
            "bilancio": 0.0,
            "investimenti": 0.0,
            "liquidita": 0.0,
        }

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


def calculate_daily_expense(
    period_df: pd.DataFrame,
    period_days: int,
) -> float:
    metrics = calculate_financial_metrics(period_df)
    expenses = float(metrics["uscite"])
    if period_days <= 0:
        return 0.0
    return expenses / period_days


def get_value_comparison(
    current_value: float,
    previous_value: float,
    *,
    higher_is_better: bool,
) -> tuple[str | None, str]:
    muted = "var(--ft-muted)"
    good = "var(--ft-income)"
    bad = "var(--ft-danger)"

    if previous_value == 0 and current_value == 0:
        return None, muted

    if previous_value == 0:
        return (
            "Nessun confronto possibile vs periodo prec.",
            "var(--ft-accent)",
        )

    percentage_change = (
        (current_value - previous_value) / abs(previous_value) * 100
    )

    if abs(percentage_change) < 0.05:
        return "≈ In linea col periodo prec.", muted

    formatted_percentage = f"{abs(percentage_change):.1f}".replace(".", ",")
    improved = (
        percentage_change > 0 if higher_is_better else percentage_change < 0
    )
    arrow = "↑" if percentage_change > 0 else "↓"
    color = good if improved else bad
    return f"{arrow} {formatted_percentage}% vs periodo prec.", color


def get_daily_expense_comparison(
    current_average: float,
    previous_average: float,
) -> tuple[str | None, str]:
    return get_value_comparison(
        current_average,
        previous_average,
        higher_is_better=False,
    )


def get_period_day_count(
    df: pd.DataFrame,
    period: str,
    selected_month: str | None = None,
) -> int:
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


def expense_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Uscite operative (esclude investimenti)."""
    if df.empty:
        return df.iloc[0:0].copy()
    return df[
        (df["importo"] < 0) & (df["categoria"] != INVESTMENT_CATEGORY)
    ].copy()


def savings_rate(metrics: dict[str, float]) -> float | None:
    """Tasso di risparmio in %: (bilancio / entrate) * 100."""
    entrate = float(metrics.get("entrate") or 0)
    if entrate <= 0:
        return None
    return float(metrics["bilancio"]) / entrate * 100


def top_expense_category(
    df: pd.DataFrame,
) -> tuple[str, float] | None:
    expenses = expense_frame(df)
    if expenses.empty:
        return None
    ranked = (
        expenses.groupby("categoria")["importo"]
        .sum()
        .abs()
        .sort_values(ascending=False)
    )
    if ranked.empty:
        return None
    return str(ranked.index[0]), float(ranked.iloc[0])


def category_expense_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    expenses = expense_frame(df)
    if expenses.empty:
        return pd.DataFrame(columns=["categoria", "importo"])
    return (
        expenses.groupby("categoria", as_index=False)["importo"]
        .sum()
        .assign(importo=lambda frame: frame["importo"].abs())
        .sort_values("importo", ascending=False)
        .reset_index(drop=True)
    )


def monthly_flow_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Aggrega entrate / uscite / investimenti per mese."""
    if df.empty:
        return pd.DataFrame(
            columns=["mese", "entrate", "uscite", "investimenti"]
        )

    return (
        df.assign(
            entrate=lambda frame: frame["importo"].where(
                frame["importo"] > 0,
                0,
            ),
            uscite=lambda frame: frame["importo"]
            .where(
                (frame["importo"] < 0)
                & (frame["categoria"] != INVESTMENT_CATEGORY),
                0,
            )
            .abs(),
            investimenti=lambda frame: frame["importo"]
            .where(
                (frame["importo"] < 0)
                & (frame["categoria"] == INVESTMENT_CATEGORY),
                0,
            )
            .abs(),
        )
        .groupby("mese", as_index=False)[
            ["entrate", "uscite", "investimenti"]
        ]
        .sum()
        .sort_values("mese")
        .reset_index(drop=True)
    )
