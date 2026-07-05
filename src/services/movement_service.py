import hashlib
import sqlite3
import pandas as pd
from src.database.db import get_connection
from datetime import date
import uuid


def generate_movement_hash(row) -> str:
    raw = "|".join(
        [
            str(row.get("data", "")),
            str(row.get("descrizione", "")),
            str(row.get("descrizione_completa", "")),
            str(row.get("importo", "")),
            str(row.get("source", "Fineco")),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def save_movements(df: pd.DataFrame, source: str = "Fineco") -> tuple[int, int]:
    inserted = 0
    skipped = 0

    with get_connection() as conn:
        for _, row in df.iterrows():
            movement_hash = generate_movement_hash(row)

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
                        movement_type,
                        amount,
                        status,
                        source,
                        account,
                        notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        movement_hash,
                        str(row.get("data", "")),
                        str(row.get("data_operazione", "")),
                        str(row.get("data_valuta", "")),
                        str(row.get("mese", "")),
                        str(row.get("descrizione", "")),
                        str(row.get("descrizione_completa", "")),
                        str(row.get("categoria", "Altro")),
                        str(row.get("tipo", "")),
                        float(row.get("importo", 0)),
                        str(row.get("stato", "")),
                        source,
                        "Fineco",
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

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["data_operazione"] = pd.to_datetime(df["data_operazione"], errors="coerce")
    df["data_valuta"] = pd.to_datetime(df["data_valuta"], errors="coerce")

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
    signed_amount = abs(amount) if movement_type == "Entrata" else -abs(amount)
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
                movement_type,
                amount,
                status,
                source,
                account,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                movement_hash,
                movement_date.isoformat(),
                movement_date.isoformat(),
                movement_date.isoformat(),
                month,
                description,
                description,
                category,
                movement_type,
                signed_amount,
                "Manuale",
                "Manuale",
                account,
                notes,
            ),
        )
        conn.commit()

def update_movement_category(movement_id: int, category: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE movements
            SET category = ?
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
