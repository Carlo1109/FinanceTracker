"""
Unione "intelligente" di due database FinanceTracker (PC ↔ telefono).

Si usa quando si unisce un backup (Impostazioni → Dati → Unisci): invece di
aggiungere solo i movimenti che mancano, porta anche modifiche e
cancellazioni fatte sull'altro dispositivo.

- movimento nuovo → aggiunto;
- stesso movimento (stesso ``uid``, o stesso hash di import) → vince la
  versione modificata per ultima (``updated_at``);
- movimento cancellato di là (``sync_tombstones``) → cancellato anche qui,
  a meno che qui sia stato modificato dopo la cancellazione.

``uid``, ``updated_at`` e ``sync_tombstones`` li tiene aggiornati il
database stesso con dei trigger (vedi src/database/db.py).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any

from src.database.db import get_connection

FORMAT_VERSION = 1

# Campi del movimento che viaggiano nel file (oltre a uid e updated_at).
FIELDS = (
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
    "created_at",
)


def export_package(conn: sqlite3.Connection | None = None) -> dict[str, Any]:
    """Movimenti e cancellazioni di un database (di default quello dell'app)."""
    own = conn is None
    if own:
        conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"""
            SELECT m.uid, m.updated_at, {", ".join("m." + f for f in FIELDS)},
                   parent.uid AS prestito_di_uid
            FROM movements m
            LEFT JOIN movements parent ON parent.id = m.prestito_di
            WHERE m.uid IS NOT NULL
            ORDER BY m.id
            """
        ).fetchall()
        alias_rows = conn.execute(
            """
            SELECT a.movement_hash, m.uid
            FROM movement_hash_aliases a JOIN movements m ON m.id = a.movement_id
            """
        ).fetchall()
        has_tombstones = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='sync_tombstones'"
        ).fetchone() is not None
        tombstones = (
            conn.execute("SELECT uid, deleted_at FROM sync_tombstones ORDER BY uid").fetchall()
            if has_tombstones
            else []
        )
    finally:
        if own:
            conn.close()

    aliases: dict[str, list[str]] = {}
    for alias in alias_rows:
        aliases.setdefault(alias["uid"], []).append(alias["movement_hash"])

    movements = []
    for row in rows:
        item = {key: row[key] for key in row.keys()}
        if item["uid"] in aliases:
            item["aliases"] = sorted(aliases[item["uid"]])
        movements.append(item)

    return {
        "format": FORMAT_VERSION,
        "app": "FinanceTracker",
        "movements": movements,
        "deleted": [{"uid": t["uid"], "deleted_at": t["deleted_at"]} for t in tombstones],
    }


@dataclass
class ImportResult:
    added: int = 0
    updated: int = 0
    deleted: int = 0
    skipped: int = 0
    unchanged: int = 0

    @property
    def changed(self) -> bool:
        return bool(self.added or self.updated or self.deleted)

    def summary(self) -> str:
        def word(count: int, one: str, many: str) -> str:
            return f"{count} {one if count == 1 else many}"

        parts = []
        if self.added:
            parts.append(word(self.added, "aggiunto", "aggiunti"))
        if self.updated:
            parts.append(word(self.updated, "aggiornato", "aggiornati"))
        if self.deleted:
            parts.append(word(self.deleted, "eliminato", "eliminati"))
        return ", ".join(parts) if parts else "nessuna novità"


def _content_key(row: dict[str, Any]) -> str:
    """Spareggio deterministico quando due versioni hanno la stessa data."""
    return json.dumps([row.get(name) for name in FIELDS], ensure_ascii=False, default=str)


def _remote_wins(remote: dict[str, Any], local: sqlite3.Row) -> bool:
    remote_at = str(remote.get("updated_at") or "")
    local_at = str(local["updated_at"] or "")
    if remote_at != local_at:
        return remote_at > local_at
    local_row = {name: local[name] for name in FIELDS}
    return _content_key(remote) > _content_key(local_row)


def import_package(package: dict[str, Any]) -> ImportResult:
    """Unisce il file di un altro dispositivo nel database di questo."""
    from src.services.loans import sanitize_loan_links

    result = ImportResult()
    if not isinstance(package, dict) or package.get("app") != "FinanceTracker":
        raise ValueError("Il file non è un file di sincronizzazione di FinanceTracker.")
    if int(package.get("format") or 0) > FORMAT_VERSION:
        raise ValueError("Il file viene da una versione più nuova: aggiorna l'app.")

    remote_rows = [r for r in package.get("movements") or [] if r.get("uid")]
    remote_uids = {r["uid"] for r in remote_rows}

    conn = get_connection()
    try:
        conn.execute("BEGIN")
        conn.execute("INSERT OR IGNORE INTO sync_applying (flag) VALUES (1)")

        def local_by_uid(uid: str) -> sqlite3.Row | None:
            return conn.execute("SELECT * FROM movements WHERE uid = ?", (uid,)).fetchone()

        def local_by_hash(movement_hash: str | None) -> sqlite3.Row | None:
            if not movement_hash:
                return None
            row = conn.execute(
                "SELECT * FROM movements WHERE movement_hash = ?", (movement_hash,)
            ).fetchone()
            if row is None:
                row = conn.execute(
                    """
                    SELECT m.* FROM movement_hash_aliases a
                    JOIN movements m ON m.id = a.movement_id
                    WHERE a.movement_hash = ?
                    """,
                    (movement_hash,),
                ).fetchone()
            return row

        tombstones = {
            row["uid"]: row["deleted_at"]
            for row in conn.execute("SELECT uid, deleted_at FROM sync_tombstones")
        }

        # 1) Cancellazioni fatte sull'altro dispositivo.
        for item in package.get("deleted") or []:
            uid, deleted_at = item.get("uid"), str(item.get("deleted_at") or "")
            if not uid or not deleted_at:
                continue
            local = local_by_uid(uid)
            if local is not None and str(local["updated_at"] or "") <= deleted_at:
                conn.execute("DELETE FROM movement_hash_aliases WHERE movement_id = ?", (local["id"],))
                conn.execute("DELETE FROM movements WHERE id = ?", (local["id"],))
                result.deleted += 1
            if deleted_at > str(tombstones.get(uid) or ""):
                conn.execute(
                    "INSERT OR REPLACE INTO sync_tombstones (uid, deleted_at) VALUES (?, ?)",
                    (uid, deleted_at),
                )
                tombstones[uid] = deleted_at

        # 2) Movimenti nuovi o modificati.
        touched: list[tuple[int, str | None]] = []  # (id locale, uid del "padre")
        for remote in remote_rows:
            uid = remote["uid"]
            remote_at = str(remote.get("updated_at") or "")
            if str(tombstones.get(uid) or "") >= remote_at and uid in tombstones:
                result.skipped += 1  # cancellato qui dopo l'ultima modifica di là
                continue

            local = local_by_uid(uid)
            if local is None:
                local = local_by_hash(remote.get("movement_hash"))
                if local is not None:
                    if local["uid"] in remote_uids and local["uid"] != uid:
                        result.skipped += 1  # due movimenti diversi con lo stesso hash
                        continue
                    # Stesso movimento importato su entrambi i dispositivi:
                    # si tiene il codice "più piccolo", così tutti e due
                    # finiscono per usare lo stesso.
                    if uid < str(local["uid"]):
                        conn.execute("UPDATE movements SET uid = ? WHERE id = ?", (uid, local["id"]))
                        local = local_by_uid(uid)

            if local is None:
                columns = ["uid", "updated_at", *FIELDS]
                values = [uid, remote_at, *[remote.get(name) for name in FIELDS]]
                cursor = conn.execute(
                    f"INSERT INTO movements ({', '.join(columns)}) "
                    f"VALUES ({', '.join('?' for _ in columns)})",
                    values,
                )
                new_id = int(cursor.lastrowid)
                conn.execute("DELETE FROM sync_tombstones WHERE uid = ?", (uid,))
                touched.append((new_id, remote.get("prestito_di_uid")))
                result.added += 1
                local_id = new_id
            else:
                local_id = int(local["id"])
                if _remote_wins(remote, local):
                    assignments = ", ".join(f"{name} = ?" for name in FIELDS if name != "created_at")
                    values = [remote.get(name) for name in FIELDS if name != "created_at"]
                    if remote.get("movement_hash") and remote.get("movement_hash") != local["movement_hash"]:
                        clash = conn.execute(
                            "SELECT id FROM movements WHERE movement_hash = ? AND id != ?",
                            (remote["movement_hash"], local_id),
                        ).fetchone()
                        if clash is not None:
                            result.skipped += 1
                            continue
                    conn.execute(
                        f"UPDATE movements SET {assignments}, updated_at = ? WHERE id = ?",
                        [*values, remote_at, local_id],
                    )
                    touched.append((local_id, remote.get("prestito_di_uid")))
                    result.updated += 1
                else:
                    result.unchanged += 1

            for alias in remote.get("aliases") or []:
                conn.execute(
                    "INSERT OR IGNORE INTO movement_hash_aliases (movement_hash, movement_id) VALUES (?, ?)",
                    (alias, local_id),
                )

        # 3) Collegamenti degli anticipi: gli id cambiano tra i database.
        for local_id, parent_uid in touched:
            parent_id = None
            if parent_uid:
                parent = conn.execute("SELECT id FROM movements WHERE uid = ?", (parent_uid,)).fetchone()
                parent_id = int(parent["id"]) if parent else None
            conn.execute("UPDATE movements SET prestito_di = ? WHERE id = ?", (parent_id, local_id))

        sanitize_loan_links(conn)
        conn.execute("DELETE FROM sync_applying")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    if result.changed:
        from src.services import movement_service

        movement_service._movements_cache = None
    return result
