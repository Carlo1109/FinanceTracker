"""Backup: creazione, ripristino e unione tra due dispositivi."""

import datetime as dt
import json
import sqlite3

from src.database.db import DATA_DIR, get_connection, init_db
from src.services import backup_service as backup
from src.services.categories import add_category, get_category_names
from src.services.movement_service import add_manual_movement, load_movements


def _snapshot(uploaded_file):
    name, data = backup.build_backup_bytes()
    return uploaded_file(name, data)


def test_ripristino_sostituisce_tutto(uploaded_file):
    add_manual_movement(dt.date(2026, 1, 1), "Prima", 10, "Altro", "Uscita", "Fineco")
    saved = _snapshot(uploaded_file)
    add_manual_movement(dt.date(2026, 1, 2), "Dopo", 20, "Altro", "Uscita", "Fineco")

    ok, _ = backup.restore_backup(saved)

    assert ok
    assert load_movements()["descrizione"].tolist() == ["Prima"]


def test_unione_aggiunge_solo_i_mancanti(uploaded_file):
    add_manual_movement(dt.date(2026, 1, 1), "Comune", 10, "Altro", "Uscita", "Fineco")
    shared = _snapshot(uploaded_file)

    # "Telefono": parte dal backup comune e aggiunge un movimento.
    backup.restore_backup(shared)
    add_manual_movement(dt.date(2026, 1, 3), "Solo telefono", 5, "Altro", "Uscita", "Revolut")
    phone = _snapshot(uploaded_file)

    # "PC": stesso backup comune più un movimento suo.
    backup.restore_backup(shared)
    add_manual_movement(dt.date(2026, 1, 2), "Solo PC", 7, "Altro", "Uscita", "Fineco")

    ok, message = backup.merge_backup(phone)

    assert ok, message
    assert sorted(load_movements()["descrizione"]) == ["Comune", "Solo PC", "Solo telefono"]
    assert "1 movimenti aggiunti" in message and "1 già presenti" in message

    again, message = backup.merge_backup(phone)
    assert again and "0 movimenti aggiunti" in message
    assert len(load_movements()) == 3


def test_unione_mantiene_i_collegamenti_prestito(uploaded_file):
    # Un altro dispositivo con una pratica prestito: uscita + rientro collegato.
    add_manual_movement(dt.date(2026, 1, 1), "Occupa id", 1, "Altro", "Uscita", "Fineco")
    add_manual_movement(dt.date(2026, 1, 5), "Prestito a Luca", 100, "Anticipi & Recuperi", "Uscita", "Fineco")
    add_manual_movement(dt.date(2026, 1, 9), "Luca restituisce", 100, "Anticipi & Recuperi", "Entrata", "Fineco")
    with get_connection() as conn:
        out_id = conn.execute("SELECT id FROM movements WHERE description = 'Prestito a Luca'").fetchone()[0]
        conn.execute("UPDATE movements SET prestito_di = ? WHERE description = 'Luca restituisce'", (out_id,))
        conn.commit()
    other_device = _snapshot(uploaded_file)

    # Database locale diverso (gli id non coincidono).
    backup.restore_backup(_empty_backup(uploaded_file))
    init_db()  # come fa l'app a ogni ricarica
    add_manual_movement(dt.date(2026, 2, 1), "Locale", 3, "Altro", "Uscita", "Fineco")

    ok, _ = backup.merge_backup(other_device)

    assert ok
    df = load_movements().set_index("descrizione")
    assert df.loc["Luca restituisce", "prestito_di"] == df.loc["Prestito a Luca", "id"]


def test_unione_aggiunge_categorie_nuove(uploaded_file):
    add_category("Animali", "🐶")
    with_category = _snapshot(uploaded_file)
    backup.restore_backup(_empty_backup(uploaded_file))
    init_db()
    assert "Animali" not in get_category_names()

    ok, message = backup.merge_backup(with_category)

    assert ok
    assert "Animali" in get_category_names()
    assert "categorie nuove" in message


def test_backup_non_valido(uploaded_file):
    ok, message = backup.merge_backup(uploaded_file("x.zip", b"non sono uno zip"))
    assert not ok and "zip" in message


def test_promemoria_backup():
    assert backup.days_since_last_backup() is None
    backup.mark_backup_done()
    assert backup.days_since_last_backup() == 0


def _empty_backup(uploaded_file):
    """Backup di un database vuoto con le categorie di default."""
    import io
    import zipfile

    empty_db = DATA_DIR / "empty.db"
    empty_db.unlink(missing_ok=True)
    sqlite3.connect(empty_db).close()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.write(empty_db, arcname="finance_tracker.db")
        archive.writestr("categories.json", json.dumps({"Altro": {"icon": "❓", "keywords": []}}))
    return uploaded_file("empty.zip", buffer.getvalue())
