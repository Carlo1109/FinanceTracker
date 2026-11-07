"""Calcoli della dashboard su dati noti."""

import pandas as pd

from src.services.analytics import calculate_account_balance, calculate_financial_metrics


def _movements(rows):
    return pd.DataFrame(
        [
            {
                "data": pd.Timestamp(date),
                "importo": amount,
                "categoria": category,
                "account": "Fineco",
                "speciale": False,
                "speciale_mesi": 0,
                "prestito_di": None,
            }
            for date, amount, category in rows
        ]
    )


def test_metriche_escludono_trasferimenti_e_separano_investimenti():
    df = _movements([
        ("2026-01-27", 2000.0, "Stipendio"),
        ("2026-01-05", -100.0, "Alimentari"),
        ("2026-01-06", -50.0, "Trasporti"),
        ("2026-01-10", -300.0, "Investimenti"),
        ("2026-01-12", -500.0, "Trasferimenti interni"),
        ("2026-01-12", 500.0, "Trasferimenti interni"),
        ("2026-01-01", 1000.0, "Saldo iniziale"),
    ])

    metrics = calculate_financial_metrics(df)

    assert metrics["entrate"] == 2000.0
    assert metrics["uscite"] == 150.0
    assert metrics["investimenti"] == 300.0
    assert metrics["bilancio"] == 1850.0


def test_saldo_conto_include_tutto_fino_alla_data():
    df = _movements([
        ("2026-01-01", 1000.0, "Saldo iniziale"),
        ("2026-01-05", -100.0, "Alimentari"),
        ("2026-01-12", -500.0, "Trasferimenti interni"),
        ("2026-02-01", -40.0, "Alimentari"),
    ])

    assert calculate_account_balance(df) == 360.0
    assert calculate_account_balance(df, through=pd.Timestamp("2026-01-31")) == 400.0


def test_metriche_vuote():
    assert calculate_financial_metrics(pd.DataFrame()) == {
        "entrate": 0.0, "uscite": 0.0, "bilancio": 0.0, "investimenti": 0.0,
    }
