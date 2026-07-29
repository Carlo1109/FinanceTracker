"""Selettore data tematico (niente calendario Baseweb di Streamlit)."""

from __future__ import annotations

import calendar
from datetime import date

import streamlit as st

ITALIAN_MONTHS = (
    "Gennaio",
    "Febbraio",
    "Marzo",
    "Aprile",
    "Maggio",
    "Giugno",
    "Luglio",
    "Agosto",
    "Settembre",
    "Ottobre",
    "Novembre",
    "Dicembre",
)


def themed_date_input(
    label: str = "Data",
    *,
    value: date | None = None,
    key: str = "ft_date",
    min_year: int | None = None,
    max_year: int | None = None,
) -> date:
    """
    Giorno / mese / anno con select del tema.

    Evita il date picker nativo Streamlit (header nero, celle vuote, pallino blu).
    """
    initial = value or date.today()
    year_key = f"{key}_year"
    month_key = f"{key}_month"
    day_key = f"{key}_day"

    if year_key not in st.session_state:
        st.session_state[year_key] = initial.year
    if month_key not in st.session_state:
        st.session_state[month_key] = initial.month
    if day_key not in st.session_state:
        st.session_state[day_key] = initial.day

    low_year = min_year if min_year is not None else initial.year - 10
    high_year = max_year if max_year is not None else initial.year + 50
    years = list(range(low_year, high_year + 1))

    year = int(st.session_state[year_key])
    month = int(st.session_state[month_key])
    if year not in years:
        year = min(max(year, years[0]), years[-1])
        st.session_state[year_key] = year
    if month < 1 or month > 12:
        month = initial.month
        st.session_state[month_key] = month

    max_day = calendar.monthrange(year, month)[1]
    if int(st.session_state[day_key]) > max_day:
        st.session_state[day_key] = max_day

    st.markdown(
        f'<div class="ft-date-label">{label}</div>',
        unsafe_allow_html=True,
    )
    day_col, month_col, year_col = st.columns([1, 1.35, 1.05])

    with day_col:
        day = int(
            st.selectbox(
                "Giorno",
                options=list(range(1, max_day + 1)),
                key=day_key,
                label_visibility="collapsed",
            )
        )

    with month_col:
        month = int(
            st.selectbox(
                "Mese",
                options=list(range(1, 13)),
                format_func=lambda m: ITALIAN_MONTHS[m - 1],
                key=month_key,
                label_visibility="collapsed",
            )
        )

    with year_col:
        year = int(
            st.selectbox(
                "Anno",
                options=years,
                key=year_key,
                label_visibility="collapsed",
            )
        )

    max_day = calendar.monthrange(year, month)[1]
    day = min(day, max_day)
    return date(year, month, day)
