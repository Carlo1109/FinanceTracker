import pandas as pd

from src.services.category_service import categorize


def _normalize_date_column(series: pd.Series) -> pd.Series:
    """
    Normalizza una colonna di date Fineco.

    Gestisce:
    - celle vuote;
    - trattini;
    - valori None/NaN/NaT;
    - date con o senza orario;
    - formati misti.
    """
    cleaned = (
        series
        .astype("string")
        .str.strip()
        .replace(
            {
                "": pd.NA,
                " ": pd.NA,
                "-": pd.NA,
                "--": pd.NA,
                "None": pd.NA,
                "none": pd.NA,
                "nan": pd.NA,
                "NaN": pd.NA,
                "NaT": pd.NA,
            }
        )
    )

    return pd.to_datetime(
        cleaned,
        format="mixed",
        dayfirst=True,
        errors="coerce",
    )


def get_transaction_date(row: pd.Series) -> pd.Timestamp:
    """
    Determina la data principale del movimento.

    Per i pagamenti con carta di debito viene preferita la data valuta.
    Negli altri casi viene usata la data operazione; se manca,
    viene utilizzata la data valuta.
    """
    description = str(
        row.get("descrizione", "")
    ).upper()

    full_description = str(
        row.get("descrizione_completa", "")
    ).upper()

    text = f"{description} {full_description}"

    operation_date = row.get("data_operazione")
    value_date = row.get("data_valuta")

    is_debit_card = any(
        keyword in text
        for keyword in (
            "VISA DEBIT",
            "PAGAMENTO VISA",
            "PAGAMENTO POS",
            "CARTA DI DEBITO",
        )
    )

    if is_debit_card and pd.notna(value_date):
        return value_date

    if pd.notna(operation_date):
        return operation_date

    if pd.notna(value_date):
        return value_date

    return pd.NaT


def import_fineco_excel(uploaded_file) -> pd.DataFrame:
    df = pd.read_excel(
        uploaded_file,
        sheet_name="Movimenti",
        header=12,
    )

    df = df.rename(
        columns={
            "Data_Operazione": "data_operazione",
            "Data_Valuta": "data_valuta",
            "Entrate": "entrate",
            "Uscite": "uscite",
            "Descrizione": "descrizione",
            "Descrizione_Completa": (
                "descrizione_completa"
            ),
            "Stato": "stato",
        }
    )

    required_columns = {
        "data_operazione": pd.NA,
        "data_valuta": pd.NA,
        "entrate": 0,
        "uscite": 0,
        "descrizione": "",
        "descrizione_completa": "",
        "stato": "",
    }

    for column, default_value in required_columns.items():
        if column not in df.columns:
            df[column] = default_value

    df["data_operazione"] = _normalize_date_column(
        df["data_operazione"]
    )

    df["data_valuta"] = _normalize_date_column(
        df["data_valuta"]
    )

    df["entrate"] = pd.to_numeric(
        df["entrate"],
        errors="coerce",
    ).fillna(0)

    df["uscite"] = pd.to_numeric(
        df["uscite"],
        errors="coerce",
    ).fillna(0)

    df["importo"] = df["entrate"] + df["uscite"]

    for column in (
        "descrizione",
        "descrizione_completa",
        "stato",
    ):
        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    df["testo"] = (
        df["descrizione"]
        + " "
        + df["descrizione_completa"]
    ).str.strip()

    df["data"] = df.apply(
        get_transaction_date,
        axis=1,
    )

    # Vengono scartate solo le righe che non hanno
    # né data operazione né data valuta.
    df = df[df["data"].notna()].copy()

    df["mese"] = (
        df["data"]
        .dt.to_period("M")
        .astype(str)
    )

    df["categoria"] = df["testo"].apply(categorize)

    df["tipo"] = df["importo"].apply(
        lambda value: (
            "Entrata"
            if value > 0
            else "Uscita"
        )
    )

    df["category_source"] = "automatic"

    result_columns = [
        "data",
        "data_operazione",
        "data_valuta",
        "mese",
        "descrizione",
        "descrizione_completa",
        "categoria",
        "category_source",
        "tipo",
        "importo",
        "stato",
    ]

    return (
        df[result_columns]
        .sort_values(
            "data",
            ascending=False,
        )
        .reset_index(drop=True)
    )
