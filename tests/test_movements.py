"""Lettura dei movimenti: date, cache e scritture."""

import datetime as dt

import pandas as pd

from src.services import movement_service as ms


def test_parse_date_series_identico_alla_versione_riga_per_riga():
    values = pd.Series([
        "2024-01-05", "2024-01-05 13:04:05", " 2024-02-03 ", None, "", "-", "NaT",
        "05/03/2024", "31/12/2023", "testo", float("nan"),
    ])

    expected = values.apply(ms._parse_date_value)
    result = ms._parse_date_series(values)

    assert result.dtype == expected.dtype
    assert result.equals(expected)


def test_cache_si_aggiorna_dopo_ogni_scrittura():
    assert ms.load_movements().empty

    ms.add_manual_movement(dt.date(2026, 1, 10), "Pane", 2.5, "Alimentari", "Uscita", "Fineco")
    first = ms.load_movements()
    assert len(first) == 1

    ms.add_manual_movement(dt.date(2026, 1, 11), "Latte", 1.2, "Alimentari", "Uscita", "Fineco")
    assert len(ms.load_movements()) == 2

    ms.delete_movements([int(first.iloc[0]["id"])])
    remaining = ms.load_movements()
    assert remaining["descrizione"].tolist() == ["Latte"]


def test_chi_modifica_il_dataframe_non_tocca_la_cache():
    ms.add_manual_movement(dt.date(2026, 1, 10), "Pane", 2.5, "Alimentari", "Uscita", "Fineco")

    df = ms.load_movements()
    df["importo"] = 999.0

    assert ms.load_movements().iloc[0]["importo"] == -2.5


def test_segno_importo_manuale():
    ms.add_manual_movement(dt.date(2026, 2, 1), "Rimborso", 30, "Rimborsi", "Entrata", "Fineco")
    ms.add_manual_movement(dt.date(2026, 2, 2), "Cena", 30, "Bar & Ristoranti", "Uscita", "Fineco")

    df = ms.load_movements().set_index("descrizione")
    assert df.loc["Rimborso", "importo"] == 30
    assert df.loc["Cena", "importo"] == -30
