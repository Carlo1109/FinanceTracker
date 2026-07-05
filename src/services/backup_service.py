from datetime import datetime
from pathlib import Path
import zipfile


DATA_DIR = Path("data")
CONFIG_DIR = Path("config")


def create_backup() -> Path:
    backup_dir = DATA_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"FinanceTracker_Backup_{timestamp}.zip"

    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        db_path = DATA_DIR / "finance_tracker.db"
        categories_path = CONFIG_DIR / "categories.json"

        if db_path.exists():
            zipf.write(db_path, arcname="finance_tracker.db")

        if categories_path.exists():
            zipf.write(categories_path, arcname="categories.json")

    return backup_path