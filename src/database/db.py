import os
import sqlite3
import sys
import threading
from pathlib import Path


APP_NAME = "FinanceTracker"


def get_app_data_dir() -> Path:
    # Override esplicito (usato dall'app Android: cartella persistente IndexedDB).
    override = os.getenv("FT_DATA_DIR", "").strip()

    if override:
        return Path(override)

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


_probe_lock = threading.Lock()
_probe_connection: sqlite3.Connection | None = None
_probe_identity: tuple[int, int] | None = None


def database_version() -> object:
    """
    Identificativo che cambia a ogni scrittura sul database.

    Usa PRAGMA data_version su una connessione "sonda" separata:
    SQLite lo incrementa quando un'altra connessione salva modifiche.
    I metadati del file coprono il caso del ripristino da backup.
    Serve a tenere in cache i dati letti senza rischiare dati vecchi.
    """
    global _probe_connection, _probe_identity

    try:
        stat = DB_PATH.stat()
    except OSError:
        return object()

    identity = (stat.st_dev, stat.st_ino)

    with _probe_lock:
        try:
            if _probe_connection is None or _probe_identity != identity:
                if _probe_connection is not None:
                    _probe_connection.close()

                _probe_connection = sqlite3.connect(
                    DB_PATH,
                    check_same_thread=False,
                )
                _probe_identity = identity

            data_version = _probe_connection.execute(
                "PRAGMA data_version"
            ).fetchone()[0]
        except sqlite3.Error:
            _probe_connection = None
            return object()

    return (identity, stat.st_size, stat.st_mtime_ns, data_version)


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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS movement_hash_aliases (
                movement_hash TEXT PRIMARY KEY,
                movement_id INTEGER NOT NULL
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

        if "escludi_metriche" in column_names:
            try:
                connection.execute(
                    """
                    ALTER TABLE movements
                    DROP COLUMN escludi_metriche
                    """
                )
            except sqlite3.OperationalError:
                pass

        if "prestito_di" not in column_names:
            connection.execute(
                """
                ALTER TABLE movements
                ADD COLUMN prestito_di INTEGER
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

        _ensure_sync_schema(connection, column_names)

        connection.commit()


# Formato delle date di modifica usate dalla sincronizzazione (UTC, con ms).
SYNC_NOW_SQL = "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"

# Colonne che, se cambiano, contano come "modifica" da sincronizzare.
SYNC_TRACKED_COLUMNS = (
    "movement_hash",
    "date",
    "operation_date",
    "value_date",
    "month",
    "description",
    "full_description",
    "category",
    "category_source",
    "movement_type",
    "amount",
    "status",
    "source",
    "account",
    "notes",
    "speciale",
    "speciale_mesi",
    "prestito_di",
)


def _ensure_sync_schema(connection: sqlite3.Connection, column_names: set[str]) -> None:
    """
    Dati per la sincronizzazione tra dispositivi.

    - uid: codice del movimento uguale su tutti i dispositivi (l'id numerico
      cambia da un database all'altro);
    - updated_at: ultima modifica, per decidere quale versione vince;
    - sync_tombstones: movimenti cancellati, così la cancellazione arriva
      anche sull'altro dispositivo.

    Lo aggiornano dei trigger SQLite: nessuna funzione che scrive i
    movimenti deve ricordarsene.
    """
    if "uid" not in column_names:
        connection.execute("ALTER TABLE movements ADD COLUMN uid TEXT")
    if "updated_at" not in column_names:
        connection.execute("ALTER TABLE movements ADD COLUMN updated_at TEXT")

    connection.execute(
        "UPDATE movements SET uid = lower(hex(randomblob(16))) WHERE uid IS NULL"
    )
    connection.execute(
        f"""
        UPDATE movements
        SET updated_at = COALESCE(
            strftime('%Y-%m-%dT%H:%M:%fZ', created_at), {SYNC_NOW_SQL}
        )
        WHERE updated_at IS NULL
        """
    )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_movements_uid ON movements(uid)"
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS sync_tombstones (
            uid TEXT PRIMARY KEY,
            deleted_at TEXT NOT NULL
        )
        """
    )

    # Riga presente solo mentre la sincronizzazione applica i dati arrivati
    # dall'altro dispositivo (dentro la stessa transazione): in quel momento
    # i trigger non devono segnare le righe come "modificate adesso".
    connection.execute(
        "CREATE TABLE IF NOT EXISTS sync_applying (flag INTEGER PRIMARY KEY)"
    )
    connection.execute("DELETE FROM sync_applying")
    not_applying = "NOT EXISTS (SELECT 1 FROM sync_applying)"

    connection.execute(
        f"""
        CREATE TRIGGER IF NOT EXISTS ft_sync_movement_insert
        AFTER INSERT ON movements
        WHEN NEW.uid IS NULL OR NEW.updated_at IS NULL
        BEGIN
            UPDATE movements SET
                uid = COALESCE(NEW.uid, lower(hex(randomblob(16)))),
                updated_at = COALESCE(NEW.updated_at, {SYNC_NOW_SQL})
            WHERE id = NEW.id;
        END
        """
    )
    changed = " OR ".join(
        f"NEW.{name} IS NOT OLD.{name}" for name in SYNC_TRACKED_COLUMNS
    )
    connection.execute(
        f"""
        CREATE TRIGGER IF NOT EXISTS ft_sync_movement_update
        AFTER UPDATE OF {", ".join(SYNC_TRACKED_COLUMNS)} ON movements
        WHEN NEW.updated_at IS OLD.updated_at AND ({changed}) AND {not_applying}
        BEGIN
            UPDATE movements SET updated_at = {SYNC_NOW_SQL} WHERE id = NEW.id;
        END
        """
    )
    connection.execute(
        f"""
        CREATE TRIGGER IF NOT EXISTS ft_sync_movement_delete
        AFTER DELETE ON movements
        WHEN OLD.uid IS NOT NULL AND {not_applying}
        BEGIN
            INSERT OR REPLACE INTO sync_tombstones (uid, deleted_at)
            VALUES (OLD.uid, {SYNC_NOW_SQL});
        END
        """
    )


_ensured_identity: tuple | None = None


def ensure_db() -> None:
    """
    init_db() una volta sola per file di database (non a ogni interazione).

    Se il file viene sostituito (ripristino di un backup, cartella dati
    diversa) cambia identità e lo schema viene ricontrollato.
    """
    global _ensured_identity
    try:
        stat = DB_PATH.stat()
        identity: tuple | None = (str(DB_PATH), stat.st_dev, stat.st_ino)
    except OSError:
        identity = None
    if identity is not None and identity == _ensured_identity:
        return
    init_db()
    try:
        stat = DB_PATH.stat()
        _ensured_identity = (str(DB_PATH), stat.st_dev, stat.st_ino)
    except OSError:
        _ensured_identity = None
