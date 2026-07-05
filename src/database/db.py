import sqlite3
from pathlib import Path

DB_PATH = Path("data/finance_tracker.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movement_hash TEXT UNIQUE,
                date TEXT NOT NULL,
                operation_date TEXT,
                value_date TEXT,
                month TEXT NOT NULL,
                description TEXT,
                full_description TEXT,
                category TEXT NOT NULL,
                movement_type TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT,
                source TEXT NOT NULL DEFAULT 'manual',
                account TEXT NOT NULL DEFAULT 'Fineco',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()