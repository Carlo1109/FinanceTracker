from datetime import datetime
from pathlib import Path
import shutil
import tempfile
import zipfile

from src.database.db import DATA_DIR, DB_PATH
from src.services.importer import (
    USER_CATEGORY_CONFIG_PATH,
    ensure_category_config,
    invalidate_category_cache,
)


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

    return backup_path


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
        archive_path = temp_path / "backup.zip"
        archive_path.write_bytes(uploaded_file.getvalue())

        try:
            with zipfile.ZipFile(archive_path, "r") as zip_file:
                names = set(zip_file.namelist())

                if "finance_tracker.db" not in names:
                    return False, "Nel backup manca finance_tracker.db."

                zip_file.extract("finance_tracker.db", path=temp_path)

                if "categories.json" in names:
                    zip_file.extract("categories.json", path=temp_path)
        except zipfile.BadZipFile:
            return False, "Il file non è uno zip di backup valido."

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
