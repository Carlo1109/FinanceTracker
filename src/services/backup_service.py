from datetime import datetime
from pathlib import Path
import zipfile

from src.database.db import DATA_DIR, DB_PATH
from src.services.importer import ensure_category_config


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