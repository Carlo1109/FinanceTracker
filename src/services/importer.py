import pandas as pd


CATEGORY_RULES = {
    # Alimentari
    "ESSELUNGA": "Alimentari",
    "LIDL": "Alimentari",
    "ALDI": "Alimentari",
    "COOP": "Alimentari",
    "CONAD": "Alimentari",
    "EUROSPIN": "Alimentari",

    # Trasporti
    "TRENITALIA": "Trasporti",
    "ATM": "Trasporti",
    "ITALO": "Trasporti",
    "BUS": "Trasporti",
    "METRO": "Trasporti",
    "LISCIO": "Trasporti",
    "SETA": "Trasporti",

    # Auto
    "ENI": "Auto",
    "Q8": "Auto",
    "IP ": "Auto",
    "PETROLOUTLET": "Auto",
    "AUTOSTRADE": "Auto",
    "TELEPASS": "Auto",
    "PEDAGGIO": "Auto",
    "CASELL": "Auto",
    "TANGENZIALE": "Auto",
    "BOLLO": "Auto",
    "ASPIT": "Auto",
    "PARKING": "Auto",
    "PARCHEGGIO": "Auto",

    # Svago
    "PIZZA": "Svago",
    "PIZZERIA": "Svago",
    "RISTOR": "Svago",
    "PUB": "Svago",
    "BAR ": "Svago",
    "CAFFE": "Svago",
    "CAFFÈ": "Svago",
    "CINEMA": "Svago",
    "AMAZON": "Svago",
    "PAYPAL": "Svago",
    "ZARA": "Svago",
    "H&M": "Svago",
    "DECATHLON": "Svago",
    "MEDIAWORLD": "Svago",
    "UNIEURO": "Svago",

    # Casa
    "ENEL": "Casa",
    "GAS": "Casa",
    "LUCE": "Casa",
    "ACQUA": "Casa",
    "AFFITTO": "Casa",
    "IKEA": "Casa",

    # Salute
    "FARMACIA": "Salute",
    "PARAFARMACIA": "Salute",
    "MEDICO": "Salute",

    # Investimenti
    "COMPRAVENDITA TITOLI": "Investimenti",
    "PAC": "Investimenti",
    "ETF": "Investimenti",

    # Entrate
    "STIPENDIO": "Stipendio",
}


def categorize(text: str) -> str:
    text = str(text).upper()

    for key, category in CATEGORY_RULES.items():
        if key in text:
            return category

    return "Altro"


def get_transaction_date(row) -> pd.Timestamp:
    description = str(row.get("descrizione", "")).upper()
    full_description = str(row.get("descrizione_completa", "")).upper()
    text = f"{description} {full_description}"

    is_debit_card = (
        "VISA DEBIT" in text
        or "PAGAMENTO VISA" in text
        or "PAGAMENTO POS" in text
        or "CARTA DI DEBITO" in text
    )

    if is_debit_card and pd.notna(row.get("data_valuta")):
        return row["data_valuta"]

    if pd.notna(row.get("data_operazione")):
        return row["data_operazione"]

    return row["data_valuta"]


def import_fineco_excel(uploaded_file) -> pd.DataFrame:
    df = pd.read_excel(uploaded_file, sheet_name="Movimenti", header=12)

    df = df.rename(
        columns={
            "Data_Operazione": "data_operazione",
            "Data_Valuta": "data_valuta",
            "Entrate": "entrate",
            "Uscite": "uscite",
            "Descrizione": "descrizione",
            "Descrizione_Completa": "descrizione_completa",
            "Stato": "stato",
        }
    )

    df["entrate"] = df["entrate"].fillna(0)
    df["uscite"] = df["uscite"].fillna(0)
    df["importo"] = df["entrate"] + df["uscite"]

    df["testo"] = (
        df["descrizione"].fillna("")
        + " "
        + df["descrizione_completa"].fillna("")
    )

    df["data"] = df.apply(get_transaction_date, axis=1)
    df["mese"] = df["data"].dt.to_period("M").astype(str)

    df["categoria"] = df["testo"].apply(categorize)
    df["tipo"] = df["importo"].apply(lambda x: "Entrata" if x > 0 else "Uscita")

    return df[
        [
            "data",
            "data_operazione",
            "data_valuta",
            "mese",
            "descrizione",
            "descrizione_completa",
            "categoria",
            "tipo",
            "importo",
            "stato",
        ]
    ].sort_values("data", ascending=False)