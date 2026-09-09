"""Helper per KPI, periodi e confronti finanziari."""

from __future__ import annotations

import calendar

import pandas as pd

INVESTMENT_CATEGORY = "Investimenti"
TRANSFER_CATEGORY = "Trasferimenti interni"
INITIAL_BALANCE_CATEGORY = "Saldo iniziale"
LOAN_CATEGORY = "Prestiti"
RIMBORSO_CATEGORY = "Rimborsi"
PERIOD_CUSTOM = "Intervallo personalizzato"
PERIOD_CUSTOM_ALIASES = ("Da – a", "Da - a")


def is_transfer_category(category: object) -> bool:
    return str(category) == TRANSFER_CATEGORY


def is_initial_balance_category(category: object) -> bool:
    return str(category) == INITIAL_BALANCE_CATEGORY


def is_loan_category(category: object) -> bool:
    return str(category) == LOAN_CATEGORY


def is_non_operating_category(category: object) -> bool:
    """Trasferimenti, saldo iniziale e prestiti: fuori da entrate/uscite, nel saldo conto."""
    name = str(category)
    return name in {
        TRANSFER_CATEGORY,
        INITIAL_BALANCE_CATEGORY,
        LOAN_CATEGORY,
    }


def _excluded_from_metrics_mask(df: pd.DataFrame) -> pd.Series:
    """Trasferimenti interni e saldo iniziale."""
    if df.empty:
        return pd.Series(dtype=bool)

    if "categoria" not in df.columns:
        return pd.Series(False, index=df.index)
    return df["categoria"].map(is_non_operating_category)


def _for_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Esclude trasferimenti e saldo iniziale da entrate, uscite e medie."""
    if df.empty:
        return df
    return df.loc[~_excluded_from_metrics_mask(df)].copy()


def filter_by_accounts(
    df: pd.DataFrame,
    selected: list[str] | None,
) -> pd.DataFrame:
    """Lista vuota = tutti i conti."""
    if df.empty or not selected:
        return df
    return df[df["account"].isin(selected)].copy()


MOVEMENT_TYPE_FILTERS = ("Entrate", "Uscite", "Investimenti")


def filter_by_movement_types(
    df: pd.DataFrame,
    selected: list[str] | None,
) -> pd.DataFrame:
    """Lista vuota = tutti i tipi."""
    if df.empty or not selected:
        return df
    chosen = {str(item) for item in selected}
    mask = pd.Series(False, index=df.index)
    non_operating = df["categoria"].map(is_non_operating_category)
    if "Entrate" in chosen:
        mask |= (df["importo"] > 0) & ~non_operating
    if "Uscite" in chosen:
        mask |= (
            (df["importo"] < 0)
            & (df["categoria"] != INVESTMENT_CATEGORY)
            & ~non_operating
        )
    if "Investimenti" in chosen:
        mask |= df["categoria"] == INVESTMENT_CATEGORY
    return df.loc[mask].copy()


def types_chip_label(selected: list[str]) -> str:
    if not selected or set(selected) == set(MOVEMENT_TYPE_FILTERS):
        return "Tutti i tipi"
    if len(selected) == 1:
        return selected[0]
    return " + ".join(selected)


def accounts_chip_label(selected: list[str], all_accounts: list[str]) -> str:
    if not selected or set(selected) == set(all_accounts):
        return "Tutti i conti"
    if len(selected) == 1:
        return selected[0]
    if len(selected) == 2:
        return f"{selected[0]} + {selected[1]}"
    return f"{len(selected)} conti"


def calculate_account_balance(
    df: pd.DataFrame,
    *,
    through: pd.Timestamp | None = None,
) -> float:
    """
    Saldo di cassa dei movimenti passati, trasferimenti e saldo iniziale
    inclusi. Serve a mostrare quanto c’è davvero sul conto.
    """
    if df.empty or "importo" not in df.columns:
        return 0.0
    working = df
    if through is not None and "data" in df.columns:
        dated = normalize_date_column(df)
        cutoff = pd.Timestamp(through).normalize()
        working = dated[dated["data"] <= cutoff]
    if working.empty:
        return 0.0
    return float(
        pd.to_numeric(working["importo"], errors="coerce").fillna(0).sum()
    )


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
    *,
    custom_start: pd.Timestamp | None = None,
    custom_end: pd.Timestamp | None = None,
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

    if period == PERIOD_CUSTOM and custom_start is not None and custom_end is not None:
        start = pd.Timestamp(custom_start).normalize()
        end = pd.Timestamp(custom_end).normalize()
        if end < start:
            start, end = end, start
        return start, end

    return None


def get_period_df(
    df: pd.DataFrame,
    period: str,
    selected_month: str | None = None,
    *,
    custom_start: pd.Timestamp | None = None,
    custom_end: pd.Timestamp | None = None,
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

    if period == PERIOD_CUSTOM and custom_start is not None and custom_end is not None:
        dated = normalize_date_column(df)
        start = pd.Timestamp(custom_start).normalize()
        end = pd.Timestamp(custom_end).normalize()
        if end < start:
            start, end = end, start
        return dated[
            dated["data"].between(start, end, inclusive="both")
        ].copy()

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
    *,
    custom_start: pd.Timestamp | None = None,
    custom_end: pd.Timestamp | None = None,
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

    if period == PERIOD_CUSTOM and custom_start is not None and custom_end is not None:
        start = pd.Timestamp(custom_start).normalize()
        end = pd.Timestamp(custom_end).normalize()
        if end < start:
            start, end = end, start
        duration = int((end - start).days) + 1
        previous_end = start - pd.Timedelta(days=1)
        previous_start = previous_end - pd.Timedelta(days=duration - 1)
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
        }

    working = _for_metrics(df)
    if working.empty:
        return {
            "entrate": 0.0,
            "uscite": 0.0,
            "bilancio": 0.0,
            "investimenti": 0.0,
        }

    entrate = float(working.loc[working["importo"] > 0, "importo"].sum())
    uscite = float(
        abs(
            working.loc[
                (working["importo"] < 0)
                & (working["categoria"] != INVESTMENT_CATEGORY),
                "importo",
            ].sum()
        )
    )
    investimenti = float(
        abs(
            working.loc[
                (working["importo"] < 0)
                & (working["categoria"] == INVESTMENT_CATEGORY),
                "importo",
            ].sum()
        )
    )
    bilancio = entrate - uscite
    return {
        "entrate": entrate,
        "uscite": uscite,
        "bilancio": bilancio,
        "investimenti": investimenti,
    }


def _speciale_mask(df: pd.DataFrame) -> pd.Series:
    if df.empty or "speciale" not in df.columns:
        return pd.Series(False, index=df.index)
    return df["speciale"].fillna(False).astype(bool)


def _speciale_mesi_series(df: pd.DataFrame) -> pd.Series:
    if df.empty or "speciale_mesi" not in df.columns:
        return pd.Series(0, index=df.index, dtype=int)
    return (
        pd.to_numeric(df["speciale_mesi"], errors="coerce")
        .fillna(0)
        .astype(int)
        .clip(lower=0)
    )


def operational_expense_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Uscite operative escluse investimenti e spese speciali."""
    expenses = expense_frame(df)
    if expenses.empty:
        return expenses
    return expenses.loc[~_speciale_mask(expenses)].copy()


def resolve_analysis_bounds(
    df: pd.DataFrame,
    period: str,
    selected_month: str | None = None,
    *,
    custom_start: pd.Timestamp | None = None,
    custom_end: pd.Timestamp | None = None,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Limiti calendario usati per ripartire le spese speciali."""
    bounds = get_current_period_bounds(
        period,
        selected_month,
        custom_start=custom_start,
        custom_end=custom_end,
    )
    if bounds is not None:
        return bounds

    today = pd.Timestamp.today().normalize()
    dated = normalize_date_column(df)
    valid = dated["data"].dropna()
    if valid.empty:
        return today, today
    start = valid.min().normalize()
    end = max(valid.max().normalize(), today)
    return start, end


def amortized_special_in_period(
    source_df: pd.DataFrame,
    period_start: pd.Timestamp,
    period_end: pd.Timestamp,
) -> tuple[float, int]:
    """
    Quota delle spese speciali ripartite che cade nel periodo.

    Ogni spesa con speciale_mesi = N contribuisce importo/N interi
    per ciascun mese di ripartizione che interseca il periodo
    (quota fissa mensile).
    """
    period_start = pd.Timestamp(period_start).normalize()
    period_end = pd.Timestamp(period_end).normalize()
    if period_end < period_start:
        return 0.0, 0

    expenses = expense_frame(source_df)
    if expenses.empty:
        return 0.0, 0

    special = expenses.loc[_speciale_mask(expenses)].copy()
    if special.empty:
        return 0.0, 0

    special["speciale_mesi"] = _speciale_mesi_series(special)
    special = special.loc[special["speciale_mesi"] > 0]
    if special.empty:
        return 0.0, 0

    special = normalize_date_column(special)
    total = 0.0
    contributing_ids: set[int] = set()

    for _, row in special.iterrows():
        expense_date = row.get("data")
        if pd.isna(expense_date):
            continue
        months = int(row["speciale_mesi"])
        monthly_share = abs(float(row["importo"])) / months
        start_period = pd.Timestamp(expense_date).to_period("M")

        for offset in range(months):
            month = start_period + offset
            month_start = month.start_time.normalize()
            month_end = month.end_time.normalize()
            if period_end < month_start or period_start > month_end:
                continue
            total += monthly_share
            row_id = row.get("id")
            if pd.notna(row_id):
                contributing_ids.add(int(row_id))

    return float(total), len(contributing_ids)


def special_expense_summary(
    period_df: pd.DataFrame,
    *,
    source_df: pd.DataFrame | None = None,
    period_start: pd.Timestamp | None = None,
    period_end: pd.Timestamp | None = None,
) -> dict[str, float | int]:
    """
    Riepilogo spese speciali per caption Dashboard.

    - excluded_*: speciali nel periodo con mesi=0 (fuori dalle medie)
    - amortized_*: quota ripartita che cade nel periodo (anche se il
      pagamento è fuori dal periodo filtrato)
    """
    expenses = expense_frame(period_df)
    excluded_count = 0
    excluded_total = 0.0
    if not expenses.empty:
        special = expenses.loc[_speciale_mask(expenses)].copy()
        if not special.empty:
            special["speciale_mesi"] = _speciale_mesi_series(special)
            excluded = special.loc[special["speciale_mesi"] <= 0]
            excluded_count = int(len(excluded))
            excluded_total = (
                float(abs(excluded["importo"].sum())) if excluded_count else 0.0
            )

    amortized_amount = 0.0
    amortized_count = 0
    if (
        source_df is not None
        and period_start is not None
        and period_end is not None
    ):
        amortized_amount, amortized_count = amortized_special_in_period(
            source_df,
            period_start,
            period_end,
        )

    return {
        "excluded_count": excluded_count,
        "excluded_total": excluded_total,
        "amortized_count": amortized_count,
        "amortized_amount": amortized_amount,
    }


def _format_month_period(period: pd.Period) -> str:
    return f"{_MONTHS_IT[period.month - 1]} {period.year}"


def special_expenses_overview(
    source_df: pd.DataFrame,
    period_start: pd.Timestamp,
    period_end: pd.Timestamp,
) -> pd.DataFrame:
    """
    Tabella spese speciali rilevanti per il periodo.

    Include:
    - speciali con pagamento nel periodo
    - speciali ripartite la cui finestra mesi interseca il periodo
    """
    columns = [
        "data",
        "descrizione",
        "categoria",
        "account",
        "importo",
        "modalita",
        "quota_mese",
        "mesi_range",
        "notes",
    ]
    empty = pd.DataFrame(columns=columns)

    expenses = expense_frame(source_df)
    if expenses.empty:
        return empty

    special = expenses.loc[_speciale_mask(expenses)].copy()
    if special.empty:
        return empty

    special = normalize_date_column(special)
    special["speciale_mesi"] = _speciale_mesi_series(special)
    period_start = pd.Timestamp(period_start).normalize()
    period_end = pd.Timestamp(period_end).normalize()

    rows: list[dict] = []
    for _, row in special.iterrows():
        expense_date = row.get("data")
        if pd.isna(expense_date):
            continue

        amount = abs(float(row["importo"]))
        months = int(row["speciale_mesi"])
        stamp = pd.Timestamp(expense_date).normalize()
        in_period_cash = period_start <= stamp <= period_end

        monthly_share = None
        mesi_range = "—"
        overlaps_period = False

        if months > 0:
            monthly_share = amount / months
            start_month = stamp.to_period("M")
            end_month = start_month + (months - 1)
            mesi_range = (
                f"{_format_month_period(start_month)}"
                f" → {_format_month_period(end_month)}"
            )
            for offset in range(months):
                month = start_month + offset
                month_start = month.start_time.normalize()
                month_end = month.end_time.normalize()
                if not (period_end < month_start or period_start > month_end):
                    overlaps_period = True
                    break
            modalita = f"Ripartita · {months} mesi"
        else:
            modalita = "Esclusa dalle medie"

        if not (in_period_cash or overlaps_period):
            continue

        description = row.get("descrizione_completa") or row.get("descrizione") or ""
        note = str(row.get("notes") or "").strip()
        rows.append(
            {
                "data": stamp,
                "descrizione": str(description).strip(),
                "categoria": str(row.get("categoria") or ""),
                "account": str(row.get("account") or ""),
                "importo": amount,
                "modalita": modalita,
                "quota_mese": monthly_share,
                "mesi_range": mesi_range,
                "notes": note,
            }
        )

    if not rows:
        return empty

    overview = pd.DataFrame(rows)
    return overview.sort_values(
        by=["data", "importo"],
        ascending=[False, False],
        kind="stable",
    ).reset_index(drop=True)


def calculate_daily_expense(
    period_df: pd.DataFrame,
    period_days: int,
    *,
    source_df: pd.DataFrame | None = None,
    period_start: pd.Timestamp | None = None,
    period_end: pd.Timestamp | None = None,
) -> float:
    """
    Spesa media giornaliera operativa.

    Esclude le spese speciali; se hanno speciale_mesi > 0, aggiunge la
    quota ripartita che cade nel periodo analizzato.
    """
    if period_days <= 0:
        return 0.0
    operational = float(abs(operational_expense_frame(period_df)["importo"].sum()))
    amortized = 0.0
    if (
        source_df is not None
        and period_start is not None
        and period_end is not None
    ):
        amortized, _ = amortized_special_in_period(
            source_df,
            period_start,
            period_end,
        )
    return (operational + amortized) / period_days


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
    *,
    custom_start: pd.Timestamp | None = None,
    custom_end: pd.Timestamp | None = None,
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

    if period == PERIOD_CUSTOM and custom_start is not None and custom_end is not None:
        start = pd.Timestamp(custom_start).normalize()
        end = pd.Timestamp(custom_end).normalize()
        if end < start:
            start, end = end, start
        return max(int((end - start).days) + 1, 1)

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
    """Uscite operative (esclude investimenti, trasferimenti e saldo iniziale)."""
    if df.empty:
        return df.iloc[0:0].copy()
    working = _for_metrics(df)
    return working[
        (working["importo"] < 0)
        & (working["categoria"] != INVESTMENT_CATEGORY)
    ].copy()


def loan_flow_summary(
    period_df: pd.DataFrame,
    *,
    source_df: pd.DataFrame | None = None,
) -> dict[str, float]:
    """Flussi Prestiti: dati e rientrati nel periodo, netto aperto sui conti."""

    def _loan_frame(frame: pd.DataFrame) -> pd.DataFrame:
        if frame is None or frame.empty or "categoria" not in frame.columns:
            return pd.DataFrame()
        return frame.loc[frame["categoria"].map(is_loan_category)].copy()

    period = _loan_frame(period_df)
    if period.empty:
        outgoing = 0.0
        incoming = 0.0
        count = 0
    else:
        amounts = pd.to_numeric(period["importo"], errors="coerce").fillna(0)
        outgoing = float(abs(amounts[amounts < 0].sum()))
        incoming = float(amounts[amounts > 0].sum())
        count = int(len(period))

    open_source = _loan_frame(
        source_df if source_df is not None else period_df
    )
    if open_source.empty:
        open_net = 0.0
        open_count = 0
    else:
        open_net = float(
            pd.to_numeric(open_source["importo"], errors="coerce")
            .fillna(0)
            .sum()
        )
        open_count = int(len(open_source))

    return {
        "count": count,
        "outgoing": outgoing,
        "incoming": incoming,
        "period_net": incoming - outgoing,
        "open_net": open_net,
        "open_count": open_count,
    }


def refund_income(df: pd.DataFrame) -> float:
    """Entrate operative in categoria Rimborsi (regali e donazioni restano fuori)."""
    if df.empty:
        return 0.0
    working = _for_metrics(df)
    if working.empty:
        return 0.0
    mask = (working["importo"] > 0) & (working["categoria"] == RIMBORSO_CATEGORY)
    return float(working.loc[mask, "importo"].sum())


def savings_rate(
    metrics: dict[str, float],
    *,
    exclude_refunds: bool = False,
    refunds: float = 0.0,
) -> float | None:
    """Tasso di risparmio in %: (bilancio / entrate) * 100.

    Con exclude_refunds i rimborsi non contano come reddito; regali e donazioni sì.
    """
    refunds_cut = max(float(refunds or 0), 0.0) if exclude_refunds else 0.0
    entrate = float(metrics.get("entrate") or 0) - refunds_cut
    if entrate <= 0:
        return None
    bilancio = float(metrics.get("bilancio") or 0) - refunds_cut
    return bilancio / entrate * 100


def income_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Entrate operative (esclude trasferimenti e saldo iniziale)."""
    if df.empty:
        return df.iloc[0:0].copy()
    working = _for_metrics(df)
    return working[working["importo"] > 0].copy()


def top_income_category(
    df: pd.DataFrame,
) -> tuple[str, float] | None:
    incomes = income_frame(df)
    if incomes.empty:
        return None
    ranked = (
        incomes.groupby("categoria")["importo"]
        .sum()
        .sort_values(ascending=False)
    )
    if ranked.empty:
        return None
    return str(ranked.index[0]), float(ranked.iloc[0])


def category_income_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    incomes = income_frame(df)
    if incomes.empty:
        return pd.DataFrame(columns=["categoria", "importo"])
    return (
        incomes.groupby("categoria", as_index=False)["importo"]
        .sum()
        .sort_values("importo", ascending=False)
        .reset_index(drop=True)
    )


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

    eligible = ~_excluded_from_metrics_mask(df)
    return (
        df.assign(
            entrate=df["importo"].where(
                (df["importo"] > 0) & eligible,
                0,
            ),
            uscite=df["importo"]
            .where(
                (df["importo"] < 0)
                & (df["categoria"] != INVESTMENT_CATEGORY)
                & eligible,
                0,
            )
            .abs(),
            investimenti=df["importo"]
            .where(
                (df["importo"] < 0)
                & (df["categoria"] == INVESTMENT_CATEGORY)
                & eligible,
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
