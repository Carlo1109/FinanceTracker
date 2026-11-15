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


def _fineco_file(uploaded_file, rows):
    header = ["Data_Operazione", "Data_Valuta", "Entrate", "Uscite", "Descrizione", "Descrizione_Completa", "Stato"]
    data = _xlsx([header, *rows], sheet="Movimenti", header_row=13)
    return get_importer_by_label("Fineco Excel").parse(uploaded_file("fineco.xlsx", data))


def test_fineco_contabilizzato_aggiorna_autorizzato_anche_dopo_una_modifica(uploaded_file):
    """Cambiare la categoria di un Autorizzato non deve impedire l'abbinamento."""
    from datetime import date

    from src.services.movement_service import get_movement, update_movement

    pending = _fineco_file(
        uploaded_file,
        [["", "10/05/2026", None, -42.3, "Pagamento Visa Debit", "BAR ROSSI", "Autorizzato"]],
    )
    save_movements(pending, source="Fineco", account="Fineco")
    stored = load_movements()
    assert len(stored) == 1
    movement_id = int(stored.iloc[0]["id"])
    before = get_movement(movement_id)

    # Come il modulo di modifica: parte dal titolo in lista (descrizione completa).
    update_movement(
        movement_id,
        movement_date=date(2026, 5, 10),
        description="BAR ROSSI",
        amount=42.3,
        category="Svago & Tempo libero",
        movement_type="Uscita",
        account="Fineco",
    )
    after = get_movement(movement_id)
    assert after["description"] == before["description"], "descrizione breve della banca conservata"
    assert after["full_description"] == before["full_description"]

    settled = _fineco_file(
        uploaded_file,
        [[
            "12/05/2026", "10/05/2026", None, -42.3, "Pagamento Visa Debit",
            "BAR ROSSI TORINO Data operazione 10/05/26", "Contabilizzato",
        ]],
    )
    save_movements(settled, source="Fineco", account="Fineco")
    final = load_movements()
    assert len(final) == 1, "il Contabilizzato aggiorna l'Autorizzato, niente doppione"
    assert final.iloc[0]["categoria"] == "Svago & Tempo libero", "la categoria scelta resta"


def test_modifica_descrizione_cambia_anche_il_titolo(uploaded_file):
    from datetime import date

    from src.services.movement_service import get_movement, update_movement

    save_movements(
        _fineco_file(
            uploaded_file,
            [["10/05/2026", "10/05/2026", None, -9.9, "Pagamento Visa Debit", "AMZN MKTP IT", "Contabilizzato"]],
        ),
        source="Fineco",
        account="Fineco",
    )
    movement_id = int(load_movements().iloc[0]["id"])
    update_movement(
        movement_id,
        movement_date=date(2026, 5, 10),
        description="Cavo USB",
        amount=9.9,
        category="Shopping",
        movement_type="Uscita",
        account="Fineco",
    )
    after = get_movement(movement_id)
    assert after["description"] == "Cavo USB"
    assert after["full_description"] == "Cavo USB"
