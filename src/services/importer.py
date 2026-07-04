import pandas as pd


CATEGORY_RULES = {
    "ESSELUNGA": "Alimentari",
    "LIDL": "Alimentari",
    "ALDI": "Alimentari",
    "PIZZA": "Ristoranti",
    "PUB": "Ristoranti",
    "RISTOR": "Ristoranti",
    "ENI": "Auto",
    "PETROLOUTLET": "Auto",
    "ATM": "Trasporti",
    "TRENITALIA": "Trasporti",
    "PAYPAL": "Shopping",
    "AMAZON": "Shopping",
    "STIPENDIO": "Stipendio",
    "COMPRAVENDITA TITOLI": "Investimenti",
    "BOLLO": "Auto",
}


def categorize(text: str) -> str:
    text = str(text).upper()
    for key, category in CATEGORY_RULES.items():
        if key in text:
            return category
    return "Altro"


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

    df["data"] = df["data_valuta"].fillna(df["data_operazione"])
    df["mese"] = df["data"].dt.to_period("M").astype(str)

    df["testo"] = (
        df["descrizione"].fillna("")
        + " "
        + df["descrizione_completa"].fillna("")
    )

    df["categoria"] = df["testo"].apply(categorize)
    df["tipo"] = df["importo"].apply(lambda x: "Entrata" if x > 0 else "Uscita")

    return df[
        [
            "data",
            "mese",
            "descrizione",
            "descrizione_completa",
            "categoria",
            "tipo",
            "importo",
            "stato",
        ]
    ].sort_values("data", ascending=False)