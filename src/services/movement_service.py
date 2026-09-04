import hashlib
import sqlite3
import uuid
from datetime import date
from typing import Any

import pandas as pd

from src.database.db import get_connection
from src.services.analytics import INVESTMENT_CATEGORY
from src.services.categories import categorize

KNOWN_ACCOUNTS = [
    "Fineco",
    "Revolut",
    "PostePay",
    "Contanti",
    "PayPal",
    "Altro",
]


def account_choices(*extra: str) -> list[str]:
    """Conti noti + eventuali conti già presenti nei dati."""
    seen: list[str] = []
    for name in [*extra, *KNOWN_ACCOUNTS]:
        cleaned = str(name or "").strip()
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    return seen


def _money(value: float) -> float:
    return round(float(value), 2)


def _clean_text_value(value: Any) -> str:
    """Converte un valore in testo evitando None, NaN e NaT."""
    if value is None or pd.isna(value):
        return ""

    return str(value).strip()


def _parse_date_value(value: Any) -> pd.Timestamp:
    """
    Converte una data senza confondere giorno e mese.

    Le date del database sono in formato ISO:
    YYYY-MM-DD oppure YYYY-MM-DD HH:MM:SS.

    Le eventuali date italiane vengono gestite solo come fallback.
    """
    if value is None or pd.isna(value):
        return pd.NaT

    if isinstance(value, pd.Timestamp):
        return value

    if isinstance(value, (date,)):
        return pd.Timestamp(value)

    text = str(value).strip()

    if text in {
        "",
        "-",
        "--",
        "None",
        "none",
        "nan",
        "NaN",
        "NaT",
    }:
        return pd.NaT

    # Prima prova sempre il formato ISO usato nel database.
    parsed_value = pd.to_datetime(
        text,
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce",
    )

    if pd.isna(parsed_value):
        parsed_value = pd.to_datetime(
            text,
            format="%Y-%m-%d",
            errors="coerce",
        )

    # Solo come fallback prova un'eventuale data italiana.
    if pd.isna(parsed_value):
        parsed_value = pd.to_datetime(
            text,
            dayfirst=True,
            errors="coerce",
        )

    return parsed_value


def _serialize_date(value: Any) -> str:
    """
    Converte una data in formato ISO per SQLite.
    """
    parsed_value = _parse_date_value(value)

    if pd.isna(parsed_value):
        return ""

    return parsed_value.strftime("%Y-%m-%d")


def generate_movement_hash(
    row: pd.Series,
    occurrence: int = 1,
    source: str = "Fineco",
) -> str:
    raw = "|".join(
        [
            _serialize_date(row.get("data")),
            _serialize_date(row.get("data_operazione")),
            _serialize_date(row.get("data_valuta")),
            _clean_text_value(row.get("descrizione")),
            _clean_text_value(row.get("descrizione_completa")),
            _clean_text_value(row.get("importo")),
            _clean_text_value(row.get("stato")),
            source,
            str(occurrence),
        ]
    )

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _existing_movement_hashes() -> set[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT movement_hash FROM movements"
        ).fetchall()
    return {str(row[0]) for row in rows if row and row[0]}


def preview_movements(
    df: pd.DataFrame,
    source: str = "Fineco",
    account: str | None = None,
) -> dict[str, Any]:
    """
    Analizza un file importato senza scrivere sul database.

    Restituisce conteggi nuovi/duplicati, top categorie dei nuovi
    movimenti e eventuali avvisi.
    """
    existing_hashes = _existing_movement_hashes()
    occurrences: dict[str, int] = {}
    new_rows: list[dict[str, Any]] = []
    skipped = 0
    account_name = account or source

    for _, row in df.iterrows():
        data = _serialize_date(row.get("data"))
        data_operazione = _serialize_date(row.get("data_operazione"))
        data_valuta = _serialize_date(row.get("data_valuta"))

        base_key = "|".join(
            [
                data,
                data_operazione,
                data_valuta,
                _clean_text_value(row.get("descrizione")),
                _clean_text_value(row.get("descrizione_completa")),
                _clean_text_value(row.get("importo")),
                _clean_text_value(row.get("stato")),
                source,
            ]
        )
        occurrences[base_key] = occurrences.get(base_key, 0) + 1

        movement_hash = generate_movement_hash(
            row,
            occurrence=occurrences[base_key],
            source=source,
        )

        if movement_hash in existing_hashes:
            skipped += 1
            continue

        amount = float(row.get("importo", 0) or 0)
        category = (
            _clean_text_value(row.get("categoria", "Altro")) or "Altro"
        )
        new_rows.append(
            {
                "data": data,
                "importo": amount,
                "categoria": category,
                "descrizione": _clean_text_value(row.get("descrizione")),
                "account": account_name,
            }
        )

    new_df = pd.DataFrame(new_rows)
    top_categories: list[tuple[str, float]] = []
    total_new_expense = 0.0
    total_new_income = 0.0
    warnings: list[str] = []

    if not new_df.empty:
        total_new_income = float(
            new_df.loc[new_df["importo"] > 0, "importo"].sum()
        )
        expense_mask = new_df["importo"] < 0
        total_new_expense = float(
            abs(new_df.loc[expense_mask, "importo"].sum())
        )
        if expense_mask.any():
            ranked = (
                new_df.loc[expense_mask]
                .groupby("categoria")["importo"]
                .sum()
                .abs()
                .sort_values(ascending=False)
                .head(3)
            )
            top_categories = [
                (str(name), float(value))
                for name, value in ranked.items()
            ]

        missing_dates = int(new_df["data"].fillna("").eq("").sum())
        if missing_dates:
            warnings.append(
                f"{missing_dates} movimenti senza data valida."
            )

    if len(new_rows) == 0 and skipped > 0:
        warnings.append(
            "Tutti i movimenti di questo file risultano già presenti."
        )

    return {
        "new_count": len(new_rows),
        "skip_count": skipped,
        "total_count": len(df),
        "total_new_income": total_new_income,
        "total_new_expense": total_new_expense,
        "top_categories": top_categories,
        "warnings": warnings,
        "account": account_name,
        "source": source,
    }


def save_movements(
    df: pd.DataFrame,
    source: str = "Fineco",
    account: str | None = None,
) -> tuple[int, int]:
    inserted = 0
    skipped = 0
    occurrences: dict[str, int] = {}
    account_name = account or source

    with get_connection() as conn:
        for _, row in df.iterrows():
            data = _serialize_date(row.get("data"))
            data_operazione = _serialize_date(
                row.get("data_operazione")
            )
            data_valuta = _serialize_date(row.get("data_valuta"))

            base_key = "|".join(
                [
                    data,
                    data_operazione,
                    data_valuta,
                    _clean_text_value(row.get("descrizione")),
                    _clean_text_value(
                        row.get("descrizione_completa")
                    ),
                    _clean_text_value(row.get("importo")),
                    _clean_text_value(row.get("stato")),
                    source,
                ]
            )

            occurrences[base_key] = occurrences.get(base_key, 0) + 1

            movement_hash = generate_movement_hash(
                row,
                occurrence=occurrences[base_key],
                source=source,
            )

            try:
                conn.execute(
                    """
                    INSERT INTO movements (
                        movement_hash,
                        date,
                        operation_date,
                        value_date,
                        month,
                        description,
                        full_description,
                        category,
                        category_source,
                        movement_type,
                        amount,
                        status,
                        source,
                        account,
                        notes,
                        speciale,
                        speciale_mesi,
                        escludi_metriche
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        movement_hash,
                        data,
                        data_operazione,
                        data_valuta,
                        _clean_text_value(row.get("mese")),
                        _clean_text_value(row.get("descrizione")),
                        _clean_text_value(
                            row.get("descrizione_completa")
                        ),
                        _clean_text_value(
                            row.get("categoria", "Altro")
                        ) or "Altro",
                        _clean_text_value(
                            row.get(
                                "category_source",
                                "automatic",
                            )
                        ) or "automatic",
                        _clean_text_value(row.get("tipo")),
                        float(row.get("importo", 0)),
                        _clean_text_value(row.get("stato")),
                        source,
                        account_name,
                        "",
                        0,
                        0,
                        0,
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                skipped += 1

        conn.commit()

    return inserted, skipped


def load_movements() -> pd.DataFrame:
    with get_connection() as conn:
        df = pd.read_sql_query(
            """
            SELECT
                id,
                date AS data,
                operation_date AS data_operazione,
                value_date AS data_valuta,
                month AS mese,
                description AS descrizione,
                full_description AS descrizione_completa,
                category AS categoria,
                category_source,
                movement_type AS tipo,
                amount AS importo,
                status AS stato,
                source,
                account,
                notes,
                speciale,
                speciale_mesi,
                escludi_metriche
            FROM movements
            ORDER BY date DESC
            """,
            conn,
        )

    if df.empty:
        return df

    date_columns = [
        "data",
        "data_operazione",
        "data_valuta",
    ]

    for column in date_columns:
        df[column] = df[column].apply(_parse_date_value)

    df["speciale"] = (
        pd.to_numeric(df["speciale"], errors="coerce")
        .fillna(0)
        .astype(int)
        .astype(bool)
    )
    df["speciale_mesi"] = (
        pd.to_numeric(df["speciale_mesi"], errors="coerce")
        .fillna(0)
        .astype(int)
        .clip(lower=0)
    )
    df["escludi_metriche"] = (
        pd.to_numeric(df["escludi_metriche"], errors="coerce")
        .fillna(0)
        .astype(int)
        .astype(bool)
    )

    df = df.sort_values(
        by=["data", "id"],
        ascending=[False, False],
        na_position="last",
        kind="stable",
    ).reset_index(drop=True)

    return df


def add_manual_movement(
    movement_date: date,
    description: str,
    amount: float,
    category: str,
    movement_type: str,
    account: str,
    notes: str = "",
    speciale: bool = False,
    speciale_mesi: int = 0,
    escludi_metriche: bool = False,
) -> None:
    signed_amount = (
        abs(amount)
        if movement_type == "Entrata"
        else -abs(amount)
    )

    movement_date_string = movement_date.isoformat()
    month = movement_date.strftime("%Y-%m")
    movement_hash = f"manual-{uuid.uuid4()}"

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO movements (
                movement_hash,
                date,
                operation_date,
                value_date,
                month,
                description,
                full_description,
                category,
                category_source,
                movement_type,
                amount,
                status,
                source,
                account,
                notes,
                speciale,
                speciale_mesi,
                escludi_metriche
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                movement_hash,
                movement_date_string,
                movement_date_string,
                movement_date_string,
                month,
                description,
                description,
                category,
                "manual",
                movement_type,
                signed_amount,
                "Manuale",
                "Manuale",
                account,
                notes,
                1 if speciale else 0,
                max(0, int(speciale_mesi)) if speciale else 0,
                1 if escludi_metriche else 0,
            ),
        )
        conn.commit()


def get_movement(movement_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                id,
                date,
                operation_date,
                value_date,
                month,
                description,
                full_description,
                category,
                category_source,
                movement_type,
                amount,
                status,
                source,
                account,
                notes,
                speciale,
                speciale_mesi,
                escludi_metriche
            FROM movements
            WHERE id = ?
            """,
            (movement_id,),
        ).fetchone()
    if row is None:
        return None
    return dict(row)


def update_movement(
    movement_id: int,
    *,
    movement_date: date,
    description: str,
    amount: float,
    category: str,
    movement_type: str,
    account: str,
    notes: str = "",
    full_description: str | None = None,
    speciale: bool = False,
    speciale_mesi: int = 0,
    escludi_metriche: bool = False,
) -> None:
    """Aggiorna i campi modificabili di un movimento. L'hash resta invariato."""
    signed_amount = (
        abs(amount)
        if movement_type == "Entrata"
        else -abs(amount)
    )
    is_expense = movement_type == "Uscita" and category != INVESTMENT_CATEGORY
    if not is_expense:
        speciale = False
        speciale_mesi = 0

    description = description.strip()
    resolved_full = (
        description
        if full_description is None
        else str(full_description).strip() or description
    )
    notes = notes.strip()
    account = account.strip() or "Altro"
    month = movement_date.strftime("%Y-%m")
    date_string = movement_date.isoformat()

    current = get_movement(movement_id)
    category_source = "manual"
    if current is not None and str(current.get("category") or "") == category:
        category_source = (
            str(current.get("category_source") or "manual") or "manual"
        )

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE movements
            SET date = ?,
                month = ?,
                description = ?,
                full_description = ?,
                category = ?,
                category_source = ?,
                movement_type = ?,
                amount = ?,
                account = ?,
                notes = ?,
                speciale = ?,
                speciale_mesi = ?,
                escludi_metriche = ?
            WHERE id = ?
            """,
            (
                date_string,
                month,
                description,
                resolved_full,
                category,
                category_source,
                movement_type,
                _money(signed_amount),
                account,
                notes,
                1 if speciale else 0,
                max(0, int(speciale_mesi)) if speciale else 0,
                1 if escludi_metriche else 0,
                movement_id,
            ),
        )
        conn.commit()


def split_movement(
    movement_id: int,
    parts: list[tuple[float, str]],
) -> int:
    """
    Divide un movimento in più quote.

    La prima quota aggiorna la riga originale (hash invariato, così
    un re-import non duplica). Le altre diventano nuovi movimenti.
    Restituisce quante nuove righe sono state create.
    """
    if len(parts) < 2:
        raise ValueError("Servono almeno due parti.")

    original = get_movement(movement_id)
    if original is None:
        raise ValueError("Movimento non trovato.")

    cleaned: list[tuple[float, str]] = []
    for raw_amount, raw_category in parts:
        amount = _money(abs(float(raw_amount)))
        category = str(raw_category).strip() or "Altro"
        if amount <= 0:
            raise ValueError("Ogni parte deve avere un importo maggiore di zero.")
        cleaned.append((amount, category))

    original_abs = _money(abs(float(original["amount"])))
    parts_total = _money(sum(amount for amount, _ in cleaned))
    if abs(parts_total - original_abs) > 0.011:
        raise ValueError(
            "La somma delle parti deve coincidere con l'importo originale."
        )

    original_amount = float(original["amount"])
    movement_type = (
        "Entrata" if original_amount >= 0 else "Uscita"
    )
    sign = 1 if original_amount >= 0 else -1

    parsed_date = _parse_date_value(original["date"])
    if pd.isna(parsed_date):
        raise ValueError("Data originale non valida.")

    first_amount, first_category = cleaned[0]
    original_description = _clean_text_value(original.get("description"))
    original_full = _clean_text_value(original.get("full_description"))
    update_movement(
        movement_id,
        movement_date=parsed_date.date(),
        description=original_description or original_full,
        full_description=original_full or original_description,
        amount=first_amount,
        category=first_category,
        movement_type=movement_type,
        account=_clean_text_value(original.get("account")) or "Altro",
        notes=_clean_text_value(original.get("notes")),
        speciale=bool(original.get("speciale")),
        speciale_mesi=int(original.get("speciale_mesi") or 0),
        escludi_metriche=bool(original.get("escludi_metriche")),
    )

    created = 0
    with get_connection() as conn:
        for amount, category in cleaned[1:]:
            signed_amount = _money(sign * amount)
            conn.execute(
                """
                INSERT INTO movements (
                    movement_hash,
                    date,
                    operation_date,
                    value_date,
                    month,
                    description,
                    full_description,
                    category,
                    category_source,
                    movement_type,
                    amount,
                    status,
                    source,
                    account,
                    notes,
                    speciale,
                    speciale_mesi,
                    escludi_metriche
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"split-{uuid.uuid4()}",
                    original.get("date") or "",
                    original.get("operation_date") or "",
                    original.get("value_date") or "",
                    original.get("month") or "",
                    _clean_text_value(original.get("description")),
                    _clean_text_value(original.get("full_description"))
                    or _clean_text_value(original.get("description")),
                    category,
                    "manual",
                    movement_type,
                    signed_amount,
                    _clean_text_value(original.get("status")),
                    _clean_text_value(original.get("source")) or "Manuale",
                    _clean_text_value(original.get("account")) or "Altro",
                    "",
                    0,
                    0,
                    1 if original.get("escludi_metriche") else 0,
                ),
            )
            created += 1
        conn.commit()

    return created


def delete_movement(movement_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM movements
            WHERE id = ?
            """,
            (movement_id,),
        )
        conn.commit()


def delete_account(account: str) -> int:
    """Elimina dal DB tutti i movimenti del conto. Restituisce quante righe sono state cancellate."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            DELETE FROM movements
            WHERE account = ?
            """,
            (account,),
        )
        conn.commit()
        return int(cursor.rowcount)


def recalculate_automatic_categories() -> int:
    updated = 0
    df = load_movements()

    if df.empty:
        return 0

    with get_connection() as conn:
        for _, row in df.iterrows():
            if row.get("category_source") == "manual":
                continue

            text = (
                f"{row.get('descrizione', '')} "
                f"{row.get('descrizione_completa', '')}"
            )

            new_category = categorize(text)

            if new_category != row.get("categoria"):
                conn.execute(
                    """
                    UPDATE movements
                    SET category = ?
                    WHERE id = ?
                    """,
                    (new_category, int(row["id"])),
                )
                updated += 1

        conn.commit()

    return updated
