"""Report mensili e annuali su dati noti."""

from datetime import date

import pandas as pd

from src.services.reports import (
    available_months,
    available_years,
    build_month_report,
    build_year_report,
)


def _movements(rows):
    return pd.DataFrame(
        [
            {
                "data": pd.Timestamp(day),
                "importo": amount,
                "categoria": category,
                "descrizione": description,
                "account": "Fineco",
                "speciale": False,
                "speciale_mesi": 0,
                "prestito_di": None,
            }
            for day, amount, category, description in rows
        ]
    )


DATA = _movements([
    ("2025-11-03", -40.0, "Alimentari", "Coop"),
    ("2026-10-01", 2000.0, "Stipendio", "Stipendio"),
    ("2026-10-05", -100.0, "Alimentari", "Esselunga"),
    ("2026-10-07", -20.0, "Shopping", "Zara"),
    ("2026-11-01", 2000.0, "Stipendio", "Stipendio"),
    ("2026-11-02", -60.0, "Alimentari", "Lidl"),
    ("2026-11-02", -15.0, "Alimentari", "Bar"),
    ("2026-11-04", -220.0, "Shopping", "Decathlon"),
    ("2026-11-05", -300.0, "Investimenti", "PAC"),
    ("2026-11-06", -500.0, "Trasferimenti interni", "Giroconto"),
])


def test_mesi_e_anni_disponibili():
    assert available_months(DATA)[:2] == ["2026-11", "2026-10"]
    assert available_years(DATA) == [2026, 2025]


def test_report_mensile_confronti_e_categorie():
    report = build_month_report(DATA, "2026-11", today=date(2026, 11, 10))

    assert report.title == "Novembre 2026"
    assert report.current.metrics["uscite"] == 295.0  # niente investimenti e trasferimenti
    assert report.current.metrics["investimenti"] == 300.0
    assert report.previous.metrics["uscite"] == 120.0
    assert report.last_year is not None and report.last_year.metrics["uscite"] == 40.0

    table = report.categories.set_index("categoria")
    assert table.loc["Shopping", "corrente"] == 220.0
    assert table.loc["Shopping", "precedente"] == 20.0
    assert table.loc["Alimentari", "anno_scorso"] == 40.0
    assert "Investimenti" not in table.index

    # Spesa più grande e testo "cresciuta di più".
    assert report.top_expenses.iloc[0]["descrizione"] == "Decathlon"
    assert report.highlights[0]["title"] == "Shopping"


def test_calendario_del_mese():
    report = build_month_report(DATA, "2026-11", today=date(2026, 11, 10))

    assert len(report.days) == 30
    assert report.calendar_offset == 6  # 1 novembre 2026 è domenica
    day2 = report.days[1]
    assert day2["value"] == 75.0 and day2["count"] == 2
    assert day2["top"][0][0] == "Lidl"
    # 10 giorni trascorsi, uscite solo il 2 e il 4 (investimenti e giroconti non contano)
    assert report.elapsed_days == 10
    assert report.zero_spend_days == 8


def test_report_annuale_mese_per_mese():
    report = build_year_report(DATA, 2026, today=date(2026, 11, 10))

    monthly = report.monthly.set_index("mese")
    assert monthly.loc[11, "uscite"] == 295.0
    assert monthly.loc[10, "entrate"] == 2000.0
    assert monthly.loc[11, "uscite_prec"] == 40.0
    assert report.previous.metrics["uscite"] == 40.0
    assert {item["kicker"] for item in report.highlights} >= {"Mese migliore", "Mese più caro"}


def test_investito_e_parte_del_risparmio():
    from src.services.reports import investment_split

    report = build_month_report(DATA, "2026-11", today=date(2026, 11, 10))
    metrics = report.current.metrics
    # Risparmio = entrate - uscite: comprende l'investito (300).
    assert metrics["bilancio"] == 2000.0 - 295.0
    split = investment_split(metrics)
    assert split["investito"] == 300.0
    assert split["liquidita"] == 1705.0 - 300.0
    assert split["investito"] + split["liquidita"] == metrics["bilancio"]
    assert round(split["quota_entrate"], 1) == 15.0

    year = build_year_report(DATA, 2026, today=date(2026, 11, 10))
    assert year.current.metrics["investimenti"] == 300.0, "investito totale dell'anno"


def test_rimborsi_contano_come_entrate_nel_tasso():
    from src.services.analytics import savings_rate

    data = _movements([
        ("2026-11-01", 1000.0, "Stipendio", "Stipendio"),
        ("2026-11-03", 100.0, "Rimborsi", "Rimborso 730"),
        ("2026-11-04", -550.0, "Alimentari", "Spesa"),
        ("2026-11-05", -200.0, "Anticipi & Recuperi", "Occhiali (quota assicurata)"),
        ("2026-11-20", 200.0, "Anticipi & Recuperi", "Rimborso assicurazione"),
    ])
    report = build_month_report(data, "2026-11", today=date(2026, 11, 30))
    metrics = report.current.metrics
    assert metrics["entrate"] == 1100.0, "rimborso tra le entrate, anticipi fuori"
    assert metrics["uscite"] == 550.0
    assert report.current.savings_rate == savings_rate(metrics) == 50.0


def test_spese_speciali_mese_per_mese():
    from src.services.reports import special_rows

    data = _movements([
        ("2026-10-01", 2000.0, "Stipendio", "Stipendio"),
        ("2026-10-10", -120.0, "Abbonamenti", "Palestra annuale"),
        ("2026-11-06", -400.0, "Viaggi & Vacanze", "Voli"),
        ("2026-11-08", -30.0, "Alimentari", "Lidl"),
    ])
    data.loc[data["descrizione"] == "Palestra annuale", ["speciale", "speciale_mesi"]] = [True, 12]
    data.loc[data["descrizione"] == "Voli", ["speciale", "speciale_mesi"]] = [True, 0]

    november = build_month_report(data, "2026-11", today=date(2026, 11, 15)).specials
    rows = november.set_index("descrizione")
    assert set(rows.index) == {"Palestra annuale", "Voli"}
    assert rows.loc["Palestra annuale", "quota"] == 10.0
    assert rows.loc["Palestra annuale", "rata"] == "2/12"
    assert rows.loc["Voli", "quota"] == 400.0, "su 0 mesi: intera nel mese pagato"

    december = special_rows(data, pd.Timestamp("2026-12-01"), pd.Timestamp("2026-12-31"))
    assert december["descrizione"].tolist() == ["Palestra annuale"], "i voli non tornano"
    assert december.iloc[0]["rata"] == "3/12"

    year = build_year_report(data, 2026, today=date(2026, 11, 15)).specials
    assert year["mese"].tolist() == ["2026-10", "2026-11", "2026-11"], "fino al mese attuale"
    assert year["quota"].sum() == 420.0

    # Il riepilogo resta di cassa: i voli pesano interi a novembre.
    report = build_month_report(data, "2026-11", today=date(2026, 11, 15))
    assert report.current.metrics["uscite"] == 430.0
