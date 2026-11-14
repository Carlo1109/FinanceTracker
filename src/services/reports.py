"""
Report mensili e annuali.

Funzioni pure su DataFrame (come analytics.py): niente Streamlit, quindi
facili da provare con pytest. Le regole sono le stesse della dashboard:
trasferimenti interni, saldo iniziale e anticipi & recuperi restano fuori
da entrate e uscite; gli investimenti sono a parte.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from src.services.analytics import (
    INVESTMENT_CATEGORY,
    calculate_financial_metrics,
    expense_frame,
    income_frame,
    normalize_date_column,
)

MONTHS_IT = (
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
)
MONTHS_SHORT_IT = (
    "Gen", "Feb", "Mar", "Apr", "Mag", "Giu",
    "Lug", "Ago", "Set", "Ott", "Nov", "Dic",
)
WEEKDAYS_IT = (
    "lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica",
)


def month_name(period: pd.Period) -> str:
    return f"{MONTHS_IT[period.month - 1]} {period.year}"


def available_months(df: pd.DataFrame) -> list[str]:
    """Mesi con almeno un movimento, dal più recente: ['2026-11', ...]."""
    if df.empty:
        return []
    dated = normalize_date_column(df)
    months = dated["data"].dt.to_period("M").astype(str).unique().tolist()
    return sorted(months, reverse=True)


def available_years(df: pd.DataFrame) -> list[int]:
    if df.empty:
        return []
    dated = normalize_date_column(df)
    return sorted(dated["data"].dt.year.unique().astype(int).tolist(), reverse=True)


def _between(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return df[df["data"].between(start, end, inclusive="both")].copy()


def savings_rate_of(metrics: dict[str, float]) -> float | None:
    income = float(metrics["entrate"])
    if income <= 0:
        return None
    return (income - float(metrics["uscite"])) / income * 100


def category_totals(df: pd.DataFrame) -> pd.Series:
    """Uscite operative per categoria (valori positivi)."""
    expenses = expense_frame(df)
    if expenses.empty:
        return pd.Series(dtype=float)
    return expenses.groupby("categoria")["importo"].sum().abs()


def percent_change(current: float, previous: float) -> float | None:
    if abs(previous) < 0.005:
        return None
    return (current - previous) / abs(previous) * 100


@dataclass
class PeriodSummary:
    label: str
    start: pd.Timestamp
    end: pd.Timestamp
    metrics: dict[str, float]
    savings_rate: float | None
    movements: int


def _summary(df: pd.DataFrame, label: str, start, end) -> PeriodSummary:
    part = _between(df, start, end)
    metrics = calculate_financial_metrics(part)
    return PeriodSummary(
        label=label,
        start=start,
        end=end,
        metrics=metrics,
        savings_rate=savings_rate_of(metrics),
        movements=len(part),
    )


@dataclass
class Report:
    kind: str  # "month" | "year"
    title: str
    current: PeriodSummary
    previous: PeriodSummary
    last_year: PeriodSummary | None
    categories: pd.DataFrame  # categoria, corrente, precedente, anno_scorso
    top_expenses: pd.DataFrame
    days: list[dict] = field(default_factory=list)  # solo mensile
    calendar_offset: int = 0
    monthly: pd.DataFrame | None = None  # solo annuale
    highlights: list[dict] = field(default_factory=list)
    daily_average: float = 0.0
    zero_spend_days: int = 0
    elapsed_days: int = 0


def _category_table(
    current: pd.DataFrame,
    previous: pd.DataFrame,
    last_year: pd.DataFrame | None,
) -> pd.DataFrame:
    table = pd.DataFrame(
        {
            "corrente": category_totals(current),
            "precedente": category_totals(previous),
            "anno_scorso": category_totals(last_year)
            if last_year is not None
            else pd.Series(dtype=float),
        }
    ).fillna(0.0)
    if table.empty:
        return pd.DataFrame(columns=["categoria", "corrente", "precedente", "anno_scorso"])
    table = table[(table["corrente"] > 0) | (table["precedente"] > 0)]
    table = table.sort_values(["corrente", "precedente"], ascending=False)
    return table.reset_index().rename(columns={"index": "categoria"})


def _top_expenses(df: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    expenses = expense_frame(df)
    if expenses.empty:
        return expenses
    expenses = expenses.assign(valore=expenses["importo"].abs())
    return expenses.sort_values("valore", ascending=False).head(limit)


def _elapsed_days(start: pd.Timestamp, end: pd.Timestamp, today: date) -> int:
    """Giorni del periodo già trascorsi (un mese in corso non conta il futuro)."""
    last = min(end.date(), today)
    if last < start.date():
        return 0
    return (last - start.date()).days + 1


def build_month_report(
    df: pd.DataFrame,
    month: str,
    *,
    today: date | None = None,
) -> Report:
    today = today or date.today()
    dated = normalize_date_column(df) if not df.empty else df
    period = pd.Period(month, freq="M")
    prev = period - 1
    last_year_period = period - 12

    def bounds(p: pd.Period) -> tuple[pd.Timestamp, pd.Timestamp]:
        return p.start_time.normalize(), p.end_time.normalize()

    start, end = bounds(period)
    current = _summary(dated, month_name(period), start, end)
    previous = _summary(dated, month_name(prev), *bounds(prev))
    last_year = _summary(dated, month_name(last_year_period), *bounds(last_year_period))
    if last_year.movements == 0:
        last_year = None

    current_df = _between(dated, start, end)
    previous_df = _between(dated, *bounds(prev))
    last_year_df = _between(dated, *bounds(last_year_period)) if last_year else None

    # Calendario: uscite operative per giorno, con le 3 voci più grandi.
    expenses = expense_frame(current_df)
    by_day: dict[int, list] = {}
    if not expenses.empty:
        for row in expenses.itertuples(index=False):
            by_day.setdefault(row.data.day, []).append(
                (str(row.descrizione or row.categoria), abs(float(row.importo)))
            )
    days_in_month = calendar.monthrange(period.year, period.month)[1]
    days = []
    for day in range(1, days_in_month + 1):
        items = sorted(by_day.get(day, []), key=lambda item: item[1], reverse=True)
        stamp = date(period.year, period.month, day)
        days.append(
            {
                "day": day,
                "label": f"{WEEKDAYS_IT[stamp.weekday()].capitalize()} {day} "
                f"{MONTHS_IT[period.month - 1].lower()}",
                "value": round(sum(value for _, value in items), 2),
                "count": len(items),
                "top": [[name[:28], round(value, 2)] for name, value in items[:3]],
                "today": stamp == today,
            }
        )

    elapsed = _elapsed_days(start, end, today)
    spent_days = {d["day"] for d in days if d["value"] > 0 and d["day"] <= elapsed}
    zero_spend_days = max(elapsed - len(spent_days), 0)
    daily_average = current.metrics["uscite"] / elapsed if elapsed else 0.0

    report = Report(
        kind="month",
        title=month_name(period),
        current=current,
        previous=previous,
        last_year=last_year,
        categories=_category_table(current_df, previous_df, last_year_df),
        top_expenses=_top_expenses(current_df),
        days=days,
        calendar_offset=date(period.year, period.month, 1).weekday(),
        daily_average=daily_average,
        zero_spend_days=zero_spend_days,
        elapsed_days=elapsed,
    )
    report.highlights = _month_highlights(report, current_df)
    return report


def build_year_report(
    df: pd.DataFrame,
    year: int,
    *,
    today: date | None = None,
) -> Report:
    today = today or date.today()
    dated = normalize_date_column(df) if not df.empty else df

    def bounds(y: int) -> tuple[pd.Timestamp, pd.Timestamp]:
        return pd.Timestamp(y, 1, 1), pd.Timestamp(y, 12, 31)

    start, end = bounds(year)
    current = _summary(dated, str(year), start, end)
    previous = _summary(dated, str(year - 1), *bounds(year - 1))
    current_df = _between(dated, start, end)
    previous_df = _between(dated, *bounds(year - 1))

    rows = []
    for month in range(1, 13):
        p = pd.Period(year=year, month=month, freq="M")
        q = pd.Period(year=year - 1, month=month, freq="M")
        m_cur = calculate_financial_metrics(
            _between(dated, p.start_time.normalize(), p.end_time.normalize())
        )
        m_prev = calculate_financial_metrics(
            _between(dated, q.start_time.normalize(), q.end_time.normalize())
        )
        rows.append(
            {
                "mese": month,
                "label": MONTHS_SHORT_IT[month - 1],
                "entrate": m_cur["entrate"],
                "uscite": m_cur["uscite"],
                "investimenti": m_cur["investimenti"],
                "bilancio": m_cur["bilancio"],
                "uscite_prec": m_prev["uscite"],
                "entrate_prec": m_prev["entrate"],
            }
        )
    monthly = pd.DataFrame(rows)

    elapsed = _elapsed_days(start, end, today)
    report = Report(
        kind="year",
        title=str(year),
        current=current,
        previous=previous,
        last_year=None,
        categories=_category_table(current_df, previous_df, None),
        top_expenses=_top_expenses(current_df),
        monthly=monthly,
        daily_average=current.metrics["uscite"] / elapsed if elapsed else 0.0,
        elapsed_days=elapsed,
    )
    report.highlights = _year_highlights(report, today)
    return report


# ---------------------------------------------------------------- testi


def _euro(value: float) -> str:
    from src.utils.formatting import euro

    return euro(value)


def _month_highlights(report: Report, current_df: pd.DataFrame) -> list[dict]:
    items: list[dict] = []
    table = report.categories
    if not table.empty:
        diff = (table["corrente"] - table["precedente"])
        grown = table.assign(diff=diff).sort_values("diff", ascending=False)
        top = grown.iloc[0]
        if top["diff"] > 0.5:
            items.append(
                {
                    "kicker": "Cresciuta di più",
                    "title": str(top["categoria"]),
                    "copy": f"<b>+{_euro(top['diff'])}</b> rispetto a "
                    f"{report.previous.label.split()[0].lower()} "
                    f"({_euro(top['precedente'])} → {_euro(top['corrente'])}).",
                    "tone": "bad",
                }
            )
        low = grown.iloc[-1]
        if low["diff"] < -0.5:
            items.append(
                {
                    "kicker": "Risparmiato su",
                    "title": str(low["categoria"]),
                    "copy": f"<b>{_euro(abs(low['diff']))}</b> in meno rispetto a "
                    f"{report.previous.label.split()[0].lower()}.",
                    "tone": "good",
                }
            )
    if not report.top_expenses.empty:
        big = report.top_expenses.iloc[0]
        items.append(
            {
                "kicker": "Spesa più grande",
                "title": str(big["descrizione"] or big["categoria"]),
                "copy": f"<b>{_euro(float(big['valore']))}</b> · {big['categoria']} · "
                f"{pd.Timestamp(big['data']).strftime('%d/%m')}",
                "tone": "neutral",
            }
        )
    if report.elapsed_days:
        items.append(
            {
                "kicker": "Giorni senza spese",
                "title": f"{report.zero_spend_days} su {report.elapsed_days}",
                "copy": f"Media di <b>{_euro(report.daily_average)}</b> al giorno "
                "nei giorni trascorsi.",
                "tone": "neutral",
            }
        )
    return items[:3]


def _year_highlights(report: Report, today: date) -> list[dict]:
    items: list[dict] = []
    monthly = report.monthly
    if monthly is None or monthly.empty:
        return items
    active = monthly[(monthly["entrate"] > 0) | (monthly["uscite"] > 0)]
    if not active.empty:
        best = active.sort_values("bilancio", ascending=False).iloc[0]
        items.append(
            {
                "kicker": "Mese migliore",
                "title": MONTHS_IT[int(best["mese"]) - 1],
                "copy": f"Hai messo da parte <b>{_euro(float(best['bilancio']))}</b>.",
                "tone": "good",
            }
        )
        worst = active.sort_values("uscite", ascending=False).iloc[0]
        items.append(
            {
                "kicker": "Mese più caro",
                "title": MONTHS_IT[int(worst["mese"]) - 1],
                "copy": f"Uscite per <b>{_euro(float(worst['uscite']))}</b>.",
                "tone": "bad",
            }
        )
    if not report.categories.empty:
        top = report.categories.iloc[0]
        months_count = max(len(active), 1)
        items.append(
            {
                "kicker": "Categoria principale",
                "title": str(top["categoria"]),
                "copy": f"<b>{_euro(float(top['corrente']))}</b> nell'anno, circa "
                f"<b>{_euro(float(top['corrente']) / months_count)}</b> al mese.",
                "tone": "neutral",
            }
        )
    return items[:3]


__all__ = [
    "INVESTMENT_CATEGORY",
    "Report",
    "available_months",
    "available_years",
    "build_month_report",
    "build_year_report",
    "income_frame",
    "percent_change",
]
