from datetime import datetime
from io import BytesIO
import json
import os
import re
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
from src.utils.platform import IS_ANDROID

LAST_BACKUP_SETTING = "last_backup_at"
SHARED_FOLDER_SETTING = "shared_backup_folder"

# Il nome del backup dice da dove arriva: utile nella cartella condivisa.
DEVICE_TAG = "telefono" if IS_ANDROID else "pc"
BACKUP_PREFIX = "FinanceTracker_Backup_"
# Backup tenuti nella cartella condivisa per ogni dispositivo (i più vecchi si tolgono).
SHARED_KEEP_PER_DEVICE = 10


def backup_file_name() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{BACKUP_PREFIX}{timestamp}_{DEVICE_TAG}.zip"


def create_backup() -> Path:
    backup_dir = DATA_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_dir / backup_file_name()

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
    file_name = backup_file_name()

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

        updated = deleted = 0
        try:
            if _has_sync_columns(backup_db):
                # Backup della v2.0 o successiva: arrivano anche modifiche e
                # cancellazioni (vince la modifica più recente).
                result = _smart_merge(backup_db)
                added, skipped = result.added, result.unchanged
                updated, deleted = result.updated, result.deleted
            else:
                added, skipped = _merge_movements(backup_db)
        except sqlite3.DatabaseError:
            return False, "Il database nel backup non è leggibile."

        new_categories = 0
        if backup_categories is not None:
            new_categories = _merge_categories(backup_categories)

    parts = [f"{added} movimenti aggiunti"]
    if updated:
        parts.append(f"{updated} aggiornati")
    if deleted:
        parts.append(f"{deleted} eliminati")
    parts.append(f"{skipped} già presenti")
    if new_categories:
        parts.append(f"{new_categories} categorie nuove")
    return True, "Backup unito: " + ", ".join(parts) + "."


def _has_sync_columns(backup_db: Path) -> bool:
    source = sqlite3.connect(backup_db)
    try:
        columns = {row[1] for row in source.execute("PRAGMA table_info(movements)")}
    finally:
        source.close()
    return "uid" in columns and "updated_at" in columns


def _smart_merge(backup_db: Path):
    from src.services.backup_merge import export_package, import_package

    source = sqlite3.connect(backup_db)
    try:
        package = export_package(source)
    finally:
        source.close()
    return import_package(package)


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
        # uid e updated_at (sincronizzazione) li assegna questo database.
        columns = [
            c
            for c in source_columns
            if c in target_columns and c not in ("id", "uid", "updated_at")
        ]

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

    # Un backup di una versione precedente può avere uno schema più vecchio.
    init_db()
    return True, "Backup ripristinato correttamente."


# ---------------------------------------------------------------- cartella condivisa
#
# Una cartella che il PC tiene sincronizzata con Google Drive (Drive per
# desktop, Insync, rclone, …). "Crea backup" può mandarci lo zip e
# "Unisci / Sostituisci" può prenderlo da lì. Sul telefono la cartella non
# serve: lo zip si salva su Drive con "Salva in…" e si apre dal selettore file.


class LocalFile:
    """Imita il file caricato da st.file_uploader per un file su disco."""

    def __init__(self, path: Path):
        self.path = path
        self.name = path.name

    def getvalue(self) -> bytes:
        return self.path.read_bytes()


# La scelta sta in un file di questo dispositivo, fuori dal database: così un
# backup ripristinato non la cambia. "off" = tolta di proposito dall'utente.
_SHARED_FOLDER_FILE = "shared_folder.txt"
_SHARED_OFF = "off"


def _shared_folder_file() -> Path:
    return DATA_DIR / _SHARED_FOLDER_FILE


def _read_shared_choice() -> str | None:
    try:
        return _shared_folder_file().read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _write_shared_choice(value: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _shared_folder_file().write_text(value, encoding="utf-8")


def _auto_shared_folder() -> str | None:
    """Prima volta: la cartella vecchia (nel database) o quella di Drive trovata."""
    legacy = (get_setting(SHARED_FOLDER_SETTING) or "").strip()
    if legacy:
        return legacy
    for drive in suggest_shared_folders():
        target = drive / "FinanceTracker"
        try:
            target.mkdir(parents=True, exist_ok=True)
        except OSError:
            continue
        return str(target)
    return None


def shared_folder() -> Path | None:
    if IS_ANDROID:
        return None
    choice = _read_shared_choice()
    if choice is None:
        choice = _auto_shared_folder()
        if choice is None:
            return None  # riprova al prossimo avvio (Drive magari non c'è ancora)
        _write_shared_choice(choice)
    if not choice or choice == _SHARED_OFF:
        return None
    return Path(choice).expanduser()


def set_shared_folder(path: str | None) -> tuple[bool, str]:
    if not path or not path.strip():
        _write_shared_choice(_SHARED_OFF)
        return True, "Cartella condivisa tolta."
    folder = Path(path.strip().strip('"')).expanduser()
    try:
        folder.mkdir(parents=True, exist_ok=True)
        probe = folder / ".financetracker-prova"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as error:
        return False, f"Non riesco a scrivere in questa cartella: {error}"
    _write_shared_choice(str(folder))
    return True, f"Cartella condivisa: {folder}"


def suggest_shared_folders() -> list[Path]:
    """Cartelle di Google Drive che si trovano spesso su un PC."""
    home = Path.home()
    candidates: list[Path] = [
        home / "Google Drive",
        home / "GoogleDrive",
        home / "gdrive",
        home / "Il mio Drive",
    ]
    for pattern in (
        "Library/CloudStorage/GoogleDrive-*/Il mio Drive",
        "Library/CloudStorage/GoogleDrive-*/My Drive",
        "Insync/*/Google Drive",
        "Insync/*/Il mio Drive",
        "Insync/*/My Drive",
    ):
        candidates += sorted(home.glob(pattern))
    if os.name == "nt":
        for letter in "GHIJKLM":
            candidates += [Path(f"{letter}:/Il mio Drive"), Path(f"{letter}:/My Drive")]
    found: list[Path] = []
    for path in candidates:
        try:
            if path.is_dir() and path not in found:
                found.append(path)
        except OSError:
            continue
    return found


_BACKUP_NAME = re.compile(
    rf"^{BACKUP_PREFIX}(\d{{8}}_\d{{6}})(?:_(pc|telefono))?.*\.zip$",
    re.IGNORECASE,
)


def describe_backup(path: Path) -> dict:
    """Da dove arriva e quando è stato fatto un backup (dal nome del file)."""
    match = _BACKUP_NAME.match(path.name)
    when = None
    device = None
    if match:
        try:
            when = datetime.strptime(match.group(1), "%Y%m%d_%H%M%S")
        except ValueError:
            when = None
        device = (match.group(2) or "").lower() or None
    if when is None:
        try:
            when = datetime.fromtimestamp(path.stat().st_mtime)
        except OSError:
            when = datetime.min
    try:
        size = path.stat().st_size
    except OSError:
        size = 0
    return {"path": path, "name": path.name, "device": device, "when": when, "size": size}


def list_shared_backups() -> list[dict]:
    """Backup nella cartella condivisa, dal più recente."""
    folder = shared_folder()
    if folder is None or not folder.is_dir():
        return []
    items = [
        describe_backup(path)
        for path in folder.glob("*.zip")
        if path.name.lower().startswith(BACKUP_PREFIX.lower())
    ]
    return sorted(items, key=lambda item: item["when"], reverse=True)


def send_to_shared_folder(data: bytes, file_name: str) -> Path:
    """Copia lo zip nella cartella condivisa e toglie i backup più vecchi."""
    folder = shared_folder()
    if folder is None:
        raise OSError("nessuna cartella condivisa impostata")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / file_name
    temp = folder / f".{file_name}.tmp"
    temp.write_bytes(data)
    os.replace(temp, target)

    # Ordine nella cartella: per ogni dispositivo solo gli ultimi N backup.
    mine = [
        item
        for item in list_shared_backups()
        if (item["device"] or "") == DEVICE_TAG
    ]
    for old in mine[SHARED_KEEP_PER_DEVICE:]:
        try:
            old["path"].unlink()
        except OSError:
            pass
    return target
