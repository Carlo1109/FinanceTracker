import hashlib
import sqlite3
import uuid
from datetime import date
from typing import Any

import pandas as pd

from src.database.db import get_connection
from src.services.categories import categorize


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
                        notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                notes
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
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            ),
        )
        conn.commit()


def update_movement_category(
    movement_id: int,
    category: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE movements
            SET category = ?, category_source = 'manual'
            WHERE id = ?
            """,
            (category, movement_id),
        )
        conn.commit()


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
