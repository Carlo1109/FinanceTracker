"""Unione intelligente PC ↔ telefono: due database simulati uno dopo l'altro."""

import time
from datetime import date

from src.database import db
from src.database.db import get_connection, init_db
from src.services import backup_merge
from src.services.movement_service import (
    add_manual_movement,
    delete_movements,
    restore_movement_snapshots,
    snapshot_movements,
)


def _device_bytes() -> bytes:
    return db.DB_PATH.read_bytes()


def _switch_to(data: bytes | None) -> None:
    """Simula l'altro dispositivo: sostituisce il file del database."""
    db.DB_PATH.unlink(missing_ok=True)
    if data is not None:
        db.DB_PATH.write_bytes(data)
    init_db()


def _rows():
    with get_connection() as conn:
        return {
            row["uid"]: dict(row)
            for row in conn.execute("SELECT * FROM movements")
        }


def _by_description(description):
    return next(r for r in _rows().values() if r["description"] == description)


def _tick():
    time.sleep(0.01)  # updated_at ha i millisecondi


def test_nuovi_movimenti_arrivano_sull_altro_dispositivo():
    add_manual_movement(date(2026, 11, 2), "Lidl", 20, "Alimentari", "Uscita", "Fineco")
    add_manual_movement(date(2026, 11, 3), "Stipendio", 2000, "Stipendio", "Entrata", "Fineco")
    package = backup_merge.export_package()
    assert len(package["movements"]) == 2
    assert all(m["uid"] and m["updated_at"] for m in package["movements"])

    _switch_to(None)  # telefono vuoto
    result = backup_merge.import_package(package)
    assert (result.added, result.updated) == (2, 0)
    assert {r["description"] for r in _rows().values()} == {"Lidl", "Stipendio"}

    # Reimportare lo stesso file non cambia nulla.
    again = backup_merge.import_package(package)
    assert not again.changed


def test_modifica_e_cancellazione_si_propagano():
    add_manual_movement(date(2026, 11, 2), "Lidl", 20, "Alimentari", "Uscita", "Fineco")
    add_manual_movement(date(2026, 11, 4), "Zara", 50, "Shopping", "Uscita", "Revolut")
    pc = _device_bytes()

    _switch_to(None)
    backup_merge.import_package(_export_from(pc))
    _tick()
    with get_connection() as conn:  # sul telefono: cambio categoria
        conn.execute("UPDATE movements SET category = 'Bar & Ristoranti' WHERE description = 'Lidl'")
        conn.commit()
    zara = _by_description("Zara")
    delete_movements([zara["id"]])
    phone = backup_merge.export_package()

    _switch_to(pc)
    result = backup_merge.import_package(phone)
    assert (result.updated, result.deleted) == (1, 1)
    assert _by_description("Lidl")["category"] == "Bar & Ristoranti"
    assert all(r["description"] != "Zara" for r in _rows().values())


def _export_from(data: bytes):
    current = _device_bytes()
    _switch_to(data)
    package = backup_merge.export_package()
    _switch_to(current)
    return package


def test_vince_la_modifica_piu_recente():
    add_manual_movement(date(2026, 11, 2), "Lidl", 20, "Alimentari", "Uscita", "Fineco")
    pc_start = _device_bytes()

    _switch_to(None)
    backup_merge.import_package(_export_from(pc_start))
    phone_start = _device_bytes()

    # PC modifica prima, telefono dopo: deve vincere il telefono, su tutti e due.
    _switch_to(pc_start)
    with get_connection() as conn:
        conn.execute("UPDATE movements SET notes = 'dal PC'")
        conn.commit()
    pc_edit = backup_merge.export_package()
    pc_after = _device_bytes()
    _tick()
    _switch_to(phone_start)
    with get_connection() as conn:
        conn.execute("UPDATE movements SET notes = 'dal telefono'")
        conn.commit()
    phone_edit = backup_merge.export_package()

    assert not backup_merge.import_package(pc_edit).changed  # il telefono è più recente
    assert _by_description("Lidl")["notes"] == "dal telefono"

    _switch_to(pc_after)
    assert backup_merge.import_package(phone_edit).updated == 1
    assert _by_description("Lidl")["notes"] == "dal telefono"


def test_stesso_import_su_due_dispositivi_non_si_duplica():
    def import_fineco_row():
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO movements (movement_hash, date, month, description,
                    category, movement_type, amount, source, account)
                VALUES ('fineco-abc', '2026-11-05', '2026-11', 'ESSELUNGA',
                    'Alimentari', 'Uscita', -42.5, 'Fineco', 'Fineco')
                """
            )
            conn.commit()

    import_fineco_row()
    pc = _device_bytes()
    _switch_to(None)
    import_fineco_row()  # lo stesso estratto conto importato anche sul telefono

    result = backup_merge.import_package(_export_from(pc))
    assert result.added == 0
    assert len(_rows()) == 1
    phone_uid = next(iter(_rows()))

    # Dopo il giro completo i due dispositivi usano lo stesso uid.
    phone_package = backup_merge.export_package()
    _switch_to(pc)
    backup_merge.import_package(phone_package)
    assert set(_rows()) == {phone_uid}


def test_annulla_dopo_cancellazione_vince_sulla_cancellazione():
    add_manual_movement(date(2026, 11, 2), "Lidl", 20, "Alimentari", "Uscita", "Fineco")
    pc = _device_bytes()
    _switch_to(None)
    backup_merge.import_package(_export_from(pc))
    phone_with_row = _device_bytes()

    # Sul PC: cancella e poi annulla.
    _switch_to(pc)
    row = _by_description("Lidl")
    snapshot = snapshot_movements([row["id"]])
    delete_movements([row["id"]])
    _tick()
    restore_movement_snapshots(snapshot)
    package = backup_merge.export_package()
    assert package["deleted"] == []

    _switch_to(phone_with_row)
    result = backup_merge.import_package(package)
    assert result.deleted == 0
    assert len(_rows()) == 1


def test_unisci_backup_porta_modifiche_e_cancellazioni(uploaded_file):
    from src.services import backup_service as backup

    add_manual_movement(date(2026, 11, 2), "Lidl", 20, "Alimentari", "Uscita", "Fineco")
    add_manual_movement(date(2026, 11, 4), "Zara", 50, "Shopping", "Uscita", "Revolut")
    name, data = backup.build_backup_bytes()
    pc = _device_bytes()

    # Telefono: parte dal backup del PC, poi modifica e cancella.
    _switch_to(None)
    backup.restore_backup(uploaded_file(name, data))
    _tick()
    with get_connection() as conn:
        conn.execute("UPDATE movements SET notes = 'pagato in due' WHERE description = 'Lidl'")
        conn.commit()
    delete_movements([_by_description("Zara")["id"]])
    add_manual_movement(date(2026, 11, 6), "Bar", 3, "Bar & Ristoranti", "Uscita", "Contanti")
    phone_name, phone_data = backup.build_backup_bytes()

    # PC: unisce il backup del telefono.
    _switch_to(pc)
    ok, message = backup.merge_backup(uploaded_file(phone_name, phone_data))
    assert ok, message
    assert "1 movimenti aggiunti" in message
    assert "1 aggiornati" in message and "1 eliminati" in message
    rows = {r["description"]: r for r in _rows().values()}
    assert set(rows) == {"Lidl", "Bar"}
    assert rows["Lidl"]["notes"] == "pagato in due"


def test_cartella_condivisa_invio_elenco_e_pulizia(tmp_path):
    from src.services import backup_service as backup

    ok, _ = backup.set_shared_folder(str(tmp_path / "Drive" / "FinanceTracker"))
    assert ok
    folder = backup.shared_folder()
    for day in range(1, 13):
        name = f"FinanceTracker_Backup_202611{day:02d}_100000_pc.zip"
        backup.send_to_shared_folder(b"zip", name)
    (folder / "FinanceTracker_Backup_20261113_090000_telefono.zip").write_bytes(b"zip")

    items = backup.list_shared_backups()
    devices = [item["device"] for item in items]
    assert devices.count("pc") == backup.SHARED_KEEP_PER_DEVICE  # i più vecchi tolti
    assert devices.count("telefono") == 1  # quelli dell'altro dispositivo non si toccano
    assert items[0]["device"] == "telefono"  # dal più recente
    assert backup.LocalFile(items[0]["path"]).getvalue() == b"zip"


def test_nome_backup_dice_il_dispositivo():
    from src.services import backup_service as backup

    name = backup.backup_file_name()
    assert name.startswith("FinanceTracker_Backup_") and name.endswith("_pc.zip")
