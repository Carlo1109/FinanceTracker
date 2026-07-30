import os
import sqlite3
import sys
from pathlib import Path


APP_NAME = "FinanceTracker"


def get_app_data_dir() -> Path:
    if sys.platform == "win32":
        local_app_data = os.getenv("LOCALAPPDATA")

        if local_app_data:
            return Path(local_app_data) / APP_NAME

        return Path.home() / "AppData" / "Local" / APP_NAME

    if sys.platform == "darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / APP_NAME
        )

    xdg_data_home = os.getenv("XDG_DATA_HOME")

    if xdg_data_home:
        return Path(xdg_data_home) / APP_NAME

    return Path.home() / ".local" / "share" / APP_NAME


DATA_DIR = get_app_data_dir()
DB_PATH = DATA_DIR / "finance_tracker.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with get_connection() as connection:
        connection.execute(
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
                category_source TEXT NOT NULL DEFAULT 'automatic',
                movement_type TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT,
                source TEXT NOT NULL DEFAULT 'manual',
                account TEXT NOT NULL DEFAULT 'Fineco',
                notes TEXT,
                speciale INTEGER NOT NULL DEFAULT 0,
                speciale_mesi INTEGER NOT NULL DEFAULT 0,
                escludi_metriche INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        columns = connection.execute(
            "PRAGMA table_info(movements)"
        ).fetchall()

        column_names = {
            column["name"]
            for column in columns
        }

        if "category_source" not in column_names:
            connection.execute(
                """
                ALTER TABLE movements
                ADD COLUMN category_source TEXT
                NOT NULL DEFAULT 'automatic'
                """
            )

        if "account" not in column_names:
            connection.execute(
                """
                ALTER TABLE movements
                ADD COLUMN account TEXT
                NOT NULL DEFAULT 'Fineco'
                """
            )

        if "notes" not in column_names:
            connection.execute(
                """
                ALTER TABLE movements
                ADD COLUMN notes TEXT
                """
            )

        if "speciale" not in column_names:
            connection.execute(
                """
                ALTER TABLE movements
                ADD COLUMN speciale INTEGER
                NOT NULL DEFAULT 0
                """
            )

        if "speciale_mesi" not in column_names:
            connection.execute(
                """
                ALTER TABLE movements
                ADD COLUMN speciale_mesi INTEGER
                NOT NULL DEFAULT 0
                """
            )

        if "escludi_metriche" not in column_names:
            connection.execute(
                """
                ALTER TABLE movements
                ADD COLUMN escludi_metriche INTEGER
                NOT NULL DEFAULT 0
                """
            )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.commit()
