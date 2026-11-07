"""Import degli estratti conto: lettura file, categorie, niente duplicati."""

import io

import pandas as pd
from openpyxl import Workbook

from src.services.imports import get_importer_by_label
from src.services.movement_service import load_movements, save_movements


def _xlsx(rows: list[list], *, sheet: str | None = None, header_row: int = 1) -> bytes:
    """Excel con l'intestazione alla riga indicata (righe sopra vuote, come le banche)."""
    workbook = Workbook()
    worksheet = workbook.active
    if sheet:
        worksheet.title = sheet
    for _ in range(header_row - 1):
        worksheet.append([])
    for row in rows:
        worksheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_revolut_csv(uploaded_file):
    csv = (
        "Tipo,Prodotto,Data di inizio,Data di completamento,Descrizione,Importo,Costo,Valuta,State,Saldo\n"
        "PAGAMENTO,Attuale,2026-03-02 10:00:00,2026-03-03 09:00:00,Esselunga,-42.30,0,EUR,COMPLETATO,100\n"
        "RICARICA,Attuale,2026-03-05 08:00:00,2026-03-05 08:00:00,Stipendio marzo,1500,0,EUR,COMPLETATO,1600\n"
    ).encode()

    df = get_importer_by_label("Revolut CSV").parse(uploaded_file("revolut.csv", csv))

    assert len(df) == 2
    spesa = df[df["importo"] < 0].iloc[0]
    assert spesa["categoria"] == "Alimentari"
    assert spesa["tipo"] == "Uscita"
    assert spesa["mese"] == "2026-03"
    entrata = df[df["importo"] > 0].iloc[0]
    assert entrata["categoria"] == "Stipendio"
    assert entrata["tipo"] == "Entrata"


def test_paypal_csv_virgola_decimale_e_solo_completati(uploaded_file):
    csv = (
        '"Data","Nome","Tipo","Stato","Netto"\n'
        '"15/04/2026","Spotify","Pagamento","Completato","-10,99"\n'
        '"16/04/2026","Negozio","Pagamento","In sospeso","-99,00"\n'
    ).encode()

    df = get_importer_by_label("PayPal CSV").parse(uploaded_file("paypal.csv", csv))

    assert len(df) == 1, "le righe non completate vanno ignorate"
    row = df.iloc[0]
    assert row["importo"] == -10.99
    assert row["data"] == pd.Timestamp("2026-04-15"), "date PayPal in formato giorno/mese"
    assert row["categoria"] == "Abbonamenti"


def test_fineco_excel(uploaded_file):
    data = _xlsx(
        [
            ["Data_Operazione", "Data_Valuta", "Entrate", "Uscite", "Descrizione", "Descrizione_Completa", "Stato"],
            ["10/05/2026", "11/05/2026", None, -25.5, "Pagamento Visa Debit", "CONAD SETTIMO", "Contabilizzato"],
            ["12/05/2026", "12/05/2026", 2000, None, "Bonifico", "STIPENDIO MAGGIO", "Contabilizzato"],
        ],
        sheet="Movimenti",
        header_row=13,
    )

    df = get_importer_by_label("Fineco Excel").parse(uploaded_file("fineco.xlsx", data))

    assert sorted(df["importo"].tolist()) == [-25.5, 2000.0]
    carta = df[df["importo"] < 0].iloc[0]
    assert carta["data"] == pd.Timestamp("2026-05-11"), "carta di debito: conta la data valuta"
    assert carta["categoria"] == "Alimentari"


def test_postepay_excel(uploaded_file):
    data = _xlsx(
        [
            ["Data contabile", "Data valuta", "Importo (euro)", "Descrizione operazioni"],
            ["03/06/2026", "03/06/2026", -3.2, "PAGAMENTO POS TRENITALIA"],
        ],
        header_row=3,
    )

    df = get_importer_by_label("PostePay Excel").parse(uploaded_file("postepay.xlsx", data))

    assert len(df) == 1
    assert df.iloc[0]["importo"] == -3.2
    assert df.iloc[0]["categoria"] == "Trasporti"


def test_reimport_non_crea_duplicati(uploaded_file):
    csv = (
        "Data di inizio,Data di completamento,Descrizione,Importo,State\n"
        "2026-03-02,2026-03-02,Esselunga,-42.30,COMPLETATO\n"
        "2026-03-02,2026-03-02,Esselunga,-42.30,COMPLETATO\n"
        "2026-03-04,2026-03-04,Netflix,-12.99,COMPLETATO\n"
    ).encode()
    importer = get_importer_by_label("Revolut CSV")

    first = save_movements(importer.parse(uploaded_file("a.csv", csv)), source="Revolut", account="Revolut")
    second = save_movements(importer.parse(uploaded_file("a.csv", csv)), source="Revolut", account="Revolut")

    assert first[0] == 3, "due spese identiche nello stesso giorno sono due movimenti distinti"
    assert second[0] == 0, "il secondo import dello stesso file non aggiunge nulla"
    assert len(load_movements()) == 3
