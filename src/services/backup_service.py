from datetime import datetime
from io import BytesIO
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import zipfile

from src.database.db import DATA_DIR, DB_PATH, get_connection, init_db
from src.services.categories import (
    USER_CATEGORY_CONFIG_PATH,
    ensure_category_config,
    invalidate_category_cache,
    load_category_definitions,
    save_category_definitions,
)
from src.services.loans import sanitize_loan_links
from src.services.settings_service import get_setting, set_setting

LAST_BACKUP_SETTING = "last_backup_at"


def create_backup() -> Path:
    backup_dir = DATA_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"FinanceTracker_Backup_{timestamp}.zip"

    categories_path = ensure_category_config()

    with zipfile.ZipFile(
        backup_path,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as zip_file:
        if DB_PATH.exists():
            zip_file.write(
                DB_PATH,
                arcname="finance_tracker.db",
            )

        if categories_path.exists():
            zip_file.write(
                categories_path,
                arcname="categories.json",
            )

    mark_backup_done()
    return backup_path


def build_backup_bytes() -> tuple[str, bytes]:
    """
    Come create_backup, ma interamente in memoria (usato su Android,
    dove il file viene consegnato con un download invece che scritto su disco).
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"FinanceTracker_Backup_{timestamp}.zip"

    categories_path = ensure_category_config()
    buffer = BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        if DB_PATH.exists():
            zip_file.write(DB_PATH, arcname="finance_tracker.db")

        if categories_path.exists():
            zip_file.write(categories_path, arcname="categories.json")

    return file_name, buffer.getvalue()


def mark_backup_done() -> None:
    """Ricorda quando è stato fatto l'ultimo backup (per il promemoria)."""
    set_setting(LAST_BACKUP_SETTING, datetime.now().isoformat(timespec="seconds"))


def days_since_last_backup() -> int | None:
    """Giorni dall'ultimo backup, None se non è mai stato fatto."""
    raw = get_setting(LAST_BACKUP_SETTING)
    if not raw:
        return None
    try:
        last = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return max(0, (datetime.now() - last).days)


def _read_backup_archive(uploaded_file, temp_path: Path) -> tuple[Path | None, Path | None, str]:
    """Estrae database e categorie dallo zip. Restituisce (db, categorie, errore)."""
    archive_path = temp_path / "backup.zip"
    archive_path.write_bytes(uploaded_file.getvalue())

    try:
        with zipfile.ZipFile(archive_path, "r") as zip_file:
            names = set(zip_file.namelist())

            if "finance_tracker.db" not in names:
                return None, None, "Nel backup manca finance_tracker.db."

            zip_file.extract("finance_tracker.db", path=temp_path)

            categories = None
            if "categories.json" in names:
                zip_file.extract("categories.json", path=temp_path)
                categories = temp_path / "categories.json"
    except zipfile.BadZipFile:
        return None, None, "Il file non è uno zip di backup valido."

    return temp_path / "finance_tracker.db", categories, ""


def merge_backup(uploaded_file) -> tuple[bool, str]:
    """
    Unisce un backup ai dati attuali senza cancellare nulla.

    Aggiunge solo i movimenti che mancano (riconosciuti dall'hash, come
    negli import) e le categorie che non esistono ancora. Utile per
    tenere allineati PC e telefono.
    """
    init_db()

    with tempfile.TemporaryDirectory() as temp_dir:
        backup_db, backup_categories, error = _read_backup_archive(
            uploaded_file, Path(temp_dir)
        )
        if error:
            return False, error

        try:
            added, skipped = _merge_movements(backup_db)
        except sqlite3.DatabaseError:
            return False, "Il database nel backup non è leggibile."

        new_categories = 0
        if backup_categories is not None:
            new_categories = _merge_categories(backup_categories)

    parts = [f"{added} movimenti aggiunti", f"{skipped} già presenti"]
    if new_categories:
        parts.append(f"{new_categories} categorie nuove")
    return True, "Backup unito: " + ", ".join(parts) + "."


def _merge_movements(backup_db: Path) -> tuple[int, int]:
    source = sqlite3.connect(backup_db)
    source.row_factory = sqlite3.Row

    try:
        source_columns = [
            row["name"] for row in source.execute("PRAGMA table_info(movements)")
        ]
        if not source_columns:
            return 0, 0
        rows = source.execute("SELECT * FROM movements ORDER BY id").fetchall()
        has_aliases = source.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='movement_hash_aliases'"
        ).fetchone() is not None
        source_aliases = (
            source.execute("SELECT movement_hash, movement_id FROM movement_hash_aliases").fetchall()
            if has_aliases
            else []
        )
    finally:
        source.close()

    aliases_by_old_id: dict[int, list[str]] = {}
    for alias in source_aliases:
        aliases_by_old_id.setdefault(int(alias["movement_id"]), []).append(alias["movement_hash"])

    added = 0
    skipped = 0
    id_map: dict[int, int] = {}
    pending_loans: list[tuple[int, int]] = []

    with get_connection() as conn:
        target_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(movements)")
        }
        columns = [c for c in source_columns if c in target_columns and c != "id"]

        known_hashes = {
            row[0]: int(row[1])
            for row in conn.execute("SELECT movement_hash, id FROM movements WHERE movement_hash IS NOT NULL")
        }
        known_hashes.update(
            {
                row[0]: int(row[1])
                for row in conn.execute("SELECT movement_hash, movement_id FROM movement_hash_aliases")
            }
        )

        for row in rows:
            old_id = int(row["id"])
            movement_hash = row["movement_hash"] if "movement_hash" in row.keys() else None
            existing_id = known_hashes.get(movement_hash) if movement_hash else None

            if existing_id is None and not movement_hash:
                existing_id = _find_same_movement(conn, row)

            if existing_id is not None:
                id_map[old_id] = existing_id
                skipped += 1
                continue

            values = [row[c] for c in columns]
            if "prestito_di" in columns:
                values[columns.index("prestito_di")] = None
            cursor = conn.execute(
                f"INSERT INTO movements ({', '.join(columns)}) "
                f"VALUES ({', '.join('?' for _ in columns)})",
                values,
            )
            new_id = int(cursor.lastrowid)
            id_map[old_id] = new_id
            if movement_hash:
                known_hashes[movement_hash] = new_id
            added += 1

            for alias in aliases_by_old_id.get(old_id, []):
                if alias not in known_hashes:
                    conn.execute(
                        "INSERT INTO movement_hash_aliases (movement_hash, movement_id) VALUES (?, ?)",
                        (alias, new_id),
                    )
                    known_hashes[alias] = new_id

            parent = row["prestito_di"] if "prestito_di" in row.keys() else None
            if parent is not None:
                try:
                    pending_loans.append((new_id, int(parent)))
                except (TypeError, ValueError):
                    pass

        # Collegamenti dei prestiti: gli id cambiano tra i due database.
        for new_id, old_parent in pending_loans:
            new_parent = id_map.get(old_parent)
            if new_parent is not None:
                conn.execute(
                    "UPDATE movements SET prestito_di = ? WHERE id = ?",
                    (new_parent, new_id),
                )

        sanitize_loan_links(conn)
        conn.commit()

    return added, skipped


def _find_same_movement(conn: sqlite3.Connection, row: sqlite3.Row) -> int | None:
    """Per movimenti senza hash: stesso giorno, importo, descrizione e conto."""
    keys = row.keys()
    found = conn.execute(
        """
        SELECT id FROM movements
        WHERE date = ? AND amount = ? AND IFNULL(description, '') = ?
          AND IFNULL(account, '') = ?
        LIMIT 1
        """,
        (
            row["date"],
            row["amount"],
            row["description"] if "description" in keys else "",
            row["account"] if "account" in keys else "",
        ),
    ).fetchone()
    return int(found[0]) if found else None


def _merge_categories(backup_categories: Path) -> int:
    try:
        raw = json.loads(backup_categories.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    if not isinstance(raw, dict):
        return 0

    definitions = load_category_definitions()
    added = 0
    for name, data in raw.items():
        if name.startswith("_") or name in definitions or not isinstance(data, dict):
            continue
        definitions[name] = data
        added += 1

    if added:
        save_category_definitions(definitions)
        invalidate_category_cache()
    return added


def restore_backup(uploaded_file) -> tuple[bool, str]:
    """
    Ripristina database e categorie da uno zip di backup.

    Si aspetta gli stessi nomi usati in create_backup:
    - finance_tracker.db
    - categories.json
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        _, _, error = _read_backup_archive(uploaded_file, temp_path)
        if error:
            return False, error

        extracted_db = temp_path / "finance_tracker.db"
        shutil.copy2(extracted_db, DB_PATH)

        extracted_categories = temp_path / "categories.json"

        if extracted_categories.exists():
            shutil.copy2(
                extracted_categories,
                USER_CATEGORY_CONFIG_PATH,
            )
            invalidate_category_cache()

    return True, "Backup ripristinato correttamente."
