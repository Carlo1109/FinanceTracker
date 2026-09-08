import hashlib
import re
import sqlite3
import uuid
from datetime import date
from typing import Any

import pandas as pd

from src.database.db import get_connection
from src.services.analytics import INVESTMENT_CATEGORY
from src.services.categories import categorize

KNOWN_ACCOUNTS = [
    "Fineco",
    "Revolut",
    "PostePay",
    "Contanti",
    "PayPal",
    "Altro",
]


def account_choices(*extra: str) -> list[str]:
    """Conti noti + eventuali conti già presenti nei dati."""
    seen: list[str] = []
    for name in [*extra, *KNOWN_ACCOUNTS]:
        cleaned = str(name or "").strip()
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    return seen


def _money(value: float) -> float:
    return round(float(value), 2)


def _clean_text_value(value: Any) -> str:
    """Converte un valore in testo evitando None, NaN e NaT."""
    if value is None or pd.isna(value):
        return ""

    return str(value).strip()


def _parse_date_value(value: Any) -> pd.Timestamp:
    """
    Converte una data senza confondere giorno e mese.

    Le date del database sono in formato ISO:
    YYYY-MM-DD oppure YYYY-MM-DD HH:MM:SS.

    Le eventuali date italiane vengono gestite solo come fallback.
    """
    if value is None or pd.isna(value):
        return pd.NaT

    if isinstance(value, pd.Timestamp):
        return value

    if isinstance(value, (date,)):
        return pd.Timestamp(value)

    text = str(value).strip()

    if text in {
        "",
        "-",
        "--",
        "None",
        "none",
        "nan",
        "NaN",
        "NaT",
    }:
        return pd.NaT

    # Prima prova sempre il formato ISO usato nel database.
    parsed_value = pd.to_datetime(
        text,
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce",
    )

    if pd.isna(parsed_value):
        parsed_value = pd.to_datetime(
            text,
            format="%Y-%m-%d",
            errors="coerce",
        )

    # Solo come fallback prova un'eventuale data italiana.
    if pd.isna(parsed_value):
        parsed_value = pd.to_datetime(
            text,
            dayfirst=True,
            errors="coerce",
        )

    return parsed_value


def _serialize_date(value: Any) -> str:
    """
    Converte una data in formato ISO per SQLite.
    """
    parsed_value = _parse_date_value(value)

    if pd.isna(parsed_value):
        return ""

    return parsed_value.strftime("%Y-%m-%d")


def generate_movement_hash(
    row: pd.Series,
    occurrence: int = 1,
    source: str = "Fineco",
) -> str:
    raw = "|".join(
        [
            _serialize_date(row.get("data")),
            _serialize_date(row.get("data_operazione")),
            _serialize_date(row.get("data_valuta")),
            _clean_text_value(row.get("descrizione")),
            _clean_text_value(row.get("descrizione_completa")),
            _clean_text_value(row.get("importo")),
            _clean_text_value(row.get("stato")),
            source,
            str(occurrence),
        ]
    )

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


_SETTLE_DATE_WINDOW = 2
_DATA_OPERAZIONE_IN_TEXT = re.compile(
    r"Data operazione\s+(\d{2}/\d{2}/\d{2,4})",
    re.IGNORECASE,
)
_MERCHANT_STOP = {
    "PAGAMENTO",
    "VISA",
    "DEBIT",
    "CARTA",
    "DATA",
    "OPERAZIONE",
    "MILANO",
    "MILAN",
    "ITALIA",
    "ITALY",
    "IT",
    "POS",
    "GOOGLE",
    "PAY",
}


def _is_fineco_source(source: str) -> bool:
    return "fineco" in str(source).casefold()


def _status_name(value: Any) -> str:
    return _clean_text_value(value).casefold()


def _is_authorized(status: str, operation_date: str) -> bool:
    name = _status_name(status)
    if name == "autorizzato":
        return True
    if name == "contabilizzato":
        return False
    return not operation_date


def _is_settled(status: str, operation_date: str) -> bool:
    name = _status_name(status)
    if name == "contabilizzato":
        return True
    if name == "autorizzato":
        return False
    return bool(operation_date)


def _merchant_tokens(description: str, full_description: str) -> tuple[str, ...]:
    text = f"{description} {full_description}".upper()
    text = re.sub(r"S\.R\.L\.?", " SRL ", text)
    tokens: list[str] = []
    for raw in re.findall(r"[A-Z0-9']{2,}", text):
        token = raw.replace("'", "")
        if token in _MERCHANT_STOP:
            continue
        if token.isdigit() and len(token) <= 4:
            continue
        tokens.append(token)
    return tuple(tokens)


def _tokens_match(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
    if not left or not right:
        return False
    shorter, longer = (
        (set(left), set(right))
        if len(left) <= len(right)
        else (set(right), set(left))
    )
    if not shorter <= longer:
        return False
    return any(len(token) >= 4 for token in shorter) or len(shorter) >= 2


def _collect_row_dates(
    *,
    data: str,
    value_date: str,
    text: str,
) -> list[pd.Timestamp]:
    # Data_Operazione Fineco è la contabilizzazione in banca: non entra
    # nella finestra, altrimenti un Autorizzato recente si aggancierebbe
    # a un Contabilizzato più vecchio dello stesso esercente.
    dates: list[pd.Timestamp] = []
    for value in (data, value_date):
        parsed = _parse_date_value(value)
        if pd.notna(parsed):
            dates.append(pd.Timestamp(parsed).normalize())
    for match in _DATA_OPERAZIONE_IN_TEXT.finditer(text):
        parsed = pd.to_datetime(match.group(1), dayfirst=True, errors="coerce")
        if pd.notna(parsed):
            dates.append(pd.Timestamp(parsed).normalize())
    return dates


def _min_date_delta(
    left: list[pd.Timestamp],
    right: list[pd.Timestamp],
) -> int | None:
    if not left or not right:
        return None
    return min(abs((first - second).days) for first in left for second in right)


def _as_import_record(row: Any, *, from_prepared: bool = False) -> dict[str, Any]:
    if from_prepared:
        description = str(row["descrizione"])
        full_description = str(row["descrizione_completa"])
        data = str(row["data"])
        operation_date = str(row["data_operazione"])
        value_date = str(row["data_valuta"])
        status = str(row["stato"])
        amount = _money(row["importo"])
        record_id = int(row["id"]) if "id" in row else None
        movement_hash = str(row.get("movement_hash") or "")
        mese = str(row.get("mese") or "")
    else:
        description = _clean_text_value(row["description"])
        full_description = _clean_text_value(row["full_description"])
        data = _serialize_date(row["date"])
        operation_date = _serialize_date(row["operation_date"])
        value_date = _serialize_date(row["value_date"])
        status = _clean_text_value(row["status"])
        amount = _money(row["amount"] or 0)
        record_id = int(row["id"])
        movement_hash = str(row["movement_hash"] or "")
        mese = _clean_text_value(row["month"]) if "month" in row.keys() else ""
    text = f"{description} {full_description}"
    return {
        "id": record_id,
        "hash": movement_hash,
        "amount": amount,
        "status": status,
        "data": data,
        "operation_date": operation_date,
        "value_date": value_date,
        "mese": mese,
        "description": description,
        "full_description": full_description,
        "tokens": _merchant_tokens(description, full_description),
        "dates": _collect_row_dates(
            data=data,
            value_date=value_date,
            text=text,
        ),
        "authorized": _is_authorized(status, operation_date),
        "settled": _is_settled(status, operation_date),
    }


def _unique_settlement_twin(
    incoming: dict[str, Any],
    existing: list[dict[str, Any]],
    used_ids: set[int],
) -> tuple[dict[str, Any] | None, bool]:
    """Una sola riga complementare, o ambiguo se due hanno la stessa distanza."""
    matches: list[tuple[int, dict[str, Any]]] = []
    for candidate in existing:
        candidate_id = candidate["id"]
        if candidate_id is None or candidate_id in used_ids:
            continue
        delta = _settlement_candidates(incoming, candidate)
        if delta is None:
            continue
        matches.append((delta, candidate))
    if not matches:
        return None, False
    matches.sort(key=lambda item: (item[0], int(item[1]["id"])))
    best_delta = matches[0][0]
    tied = [item for item in matches if item[0] == best_delta]
    if len(tied) > 1:
        return None, True
    return tied[0][1], False


def _settlement_candidates(
    left: dict[str, Any],
    right: dict[str, Any],
) -> int | None:
    if left["amount"] != right["amount"]:
        return None
    complementary = (
        (left["settled"] and right["authorized"])
        or (left["authorized"] and right["settled"])
    )
    if not complementary:
        return None
    if not _tokens_match(left["tokens"], right["tokens"]):
        return None
    delta = _min_date_delta(left["dates"], right["dates"])
    if delta is None or delta > _SETTLE_DATE_WINDOW:
        return None
    return delta


def _existing_settlement_pairs(
    rows: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    authorized = [row for row in rows if row["authorized"]]
    settled = [row for row in rows if row["settled"] and not row["authorized"]]
    candidates: list[tuple[int, dict[str, Any], dict[str, Any]]] = []
    for pending in authorized:
        for done in settled:
            delta = _settlement_candidates(pending, done)
            if delta is None:
                continue
            candidates.append((delta, pending, done))

    rejected_auth: set[int] = set()
    rejected_settled: set[int] = set()
    by_auth: dict[int, list[tuple[int, int]]] = {}
    by_settled: dict[int, list[tuple[int, int]]] = {}
    for delta, pending, done in candidates:
        by_auth.setdefault(int(pending["id"]), []).append(
            (delta, int(done["id"]))
        )
        by_settled.setdefault(int(done["id"]), []).append(
            (delta, int(pending["id"]))
        )
    for auth_id, matches in by_auth.items():
        best = min(item[0] for item in matches)
        if sum(1 for item in matches if item[0] == best) > 1:
            rejected_auth.add(auth_id)
    for settled_id, matches in by_settled.items():
        best = min(item[0] for item in matches)
        if sum(1 for item in matches if item[0] == best) > 1:
            rejected_settled.add(settled_id)

    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    used_auth: set[int] = set()
    used_settled: set[int] = set()
    candidates.sort(
        key=lambda item: (item[0], int(item[1]["id"]), int(item[2]["id"]))
    )
    for _delta, pending, done in candidates:
        auth_id = int(pending["id"])
        settled_id = int(done["id"])
        if auth_id in rejected_auth or settled_id in rejected_settled:
            continue
        if auth_id in used_auth or settled_id in used_settled:
            continue
        pairs.append((pending, done))
        used_auth.add(auth_id)
        used_settled.add(settled_id)
    return pairs


def _overlay_settled(
    keep: dict[str, Any],
    settled: dict[str, Any],
) -> None:
    keep["authorized"] = False
    keep["settled"] = True
    keep["status"] = settled["status"] or keep["status"]
    keep["hash"] = settled["hash"] or keep["hash"]
    keep["data"] = settled["data"] or keep["data"]
    keep["operation_date"] = (
        settled["operation_date"] or keep["operation_date"]
    )
    keep["value_date"] = settled["value_date"] or keep["value_date"]
    keep["mese"] = settled.get("mese") or keep.get("mese") or ""
    keep["description"] = settled["description"] or keep["description"]
    keep["full_description"] = (
        settled["full_description"] or keep["full_description"]
    )
    if settled.get("tokens"):
        keep["tokens"] = settled["tokens"]
    if settled.get("dates"):
        keep["dates"] = settled["dates"]


def _collapse_fineco_pairs(
    conn: sqlite3.Connection,
    account_name: str,
    inserted_ids: set[int],
) -> tuple[int, int]:
    updated = 0
    retracted = 0
    while True:
        leftover = _existing_settlement_pairs(
            _load_fineco_records(conn, account_name)
        )
        if not leftover:
            break
        progressed = False
        for pending, settled in leftover:
            if not _apply_settlement_merge(conn, pending, settled):
                continue
            updated += 1
            progressed = True
            settled_id = settled.get("id")
            if settled_id and int(settled_id) in inserted_ids:
                retracted += 1
        if not progressed:
            break
    return updated, retracted


def _apply_settlement_merge(
    conn: sqlite3.Connection,
    keep: dict[str, Any],
    settled: dict[str, Any],
) -> bool:
    new_hash = settled["hash"] or keep["hash"]
    if new_hash:
        owner = conn.execute(
            "SELECT id FROM movements WHERE movement_hash = ?",
            (new_hash,),
        ).fetchone()
        owner_id = int(owner[0]) if owner else None
        reserved = {int(keep["id"])}
        settled_id = settled.get("id")
        if settled_id:
            reserved.add(int(settled_id))
        if owner_id is not None and owner_id not in reserved:
            return False
    settled_id = settled.get("id")
    if settled_id and settled_id != keep["id"]:
        conn.execute("DELETE FROM movements WHERE id = ?", (settled_id,))
    conn.execute(
        """
        UPDATE movements
        SET movement_hash = ?,
            date = ?,
            operation_date = ?,
            value_date = ?,
            month = ?,
            description = ?,
            full_description = ?,
            status = ?
        WHERE id = ?
        """,
        (
            new_hash,
            settled["data"] or keep["data"],
            settled["operation_date"] or keep["operation_date"],
            settled["value_date"] or keep["value_date"],
            settled.get("mese") or keep.get("mese") or "",
            settled["description"] or keep["description"],
            settled["full_description"] or keep["full_description"],
            settled["status"] or keep["status"],
            keep["id"],
        ),
    )
    return True


def _hash_occurrence_key(
    *,
    data: str,
    data_operazione: str,
    data_valuta: str,
    description: str,
    full_description: str,
    amount_text: str,
    status: str,
    source: str,
) -> str:
    return "|".join(
        [
            data,
            data_operazione,
            data_valuta,
            description,
            full_description,
            amount_text,
            status,
            source,
        ]
    )


def _prepare_import_row(
    row: pd.Series,
    *,
    source: str,
    occurrences: dict[str, int],
) -> dict[str, Any]:
    data = _serialize_date(row.get("data"))
    data_operazione = _serialize_date(row.get("data_operazione"))
    data_valuta = _serialize_date(row.get("data_valuta"))
    description = _clean_text_value(row.get("descrizione"))
    full_description = _clean_text_value(row.get("descrizione_completa"))
    status = _clean_text_value(row.get("stato"))
    amount_text = _clean_text_value(row.get("importo"))
    base_key = _hash_occurrence_key(
        data=data,
        data_operazione=data_operazione,
        data_valuta=data_valuta,
        description=description,
        full_description=full_description,
        amount_text=amount_text,
        status=status,
        source=source,
    )
    occurrences[base_key] = occurrences.get(base_key, 0) + 1
    return {
        "data": data,
        "data_operazione": data_operazione,
        "data_valuta": data_valuta,
        "mese": _clean_text_value(row.get("mese")),
        "descrizione": description,
        "descrizione_completa": full_description,
        "stato": status,
        "importo": float(row.get("importo", 0) or 0),
        "categoria": _clean_text_value(row.get("categoria", "Altro")) or "Altro",
        "category_source": (
            _clean_text_value(row.get("category_source", "automatic"))
            or "automatic"
        ),
        "tipo": _clean_text_value(row.get("tipo")),
        "movement_hash": generate_movement_hash(
            row,
            occurrence=occurrences[base_key],
            source=source,
        ),
    }


def _load_fineco_records(
    conn: sqlite3.Connection,
    account: str,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, movement_hash, date, operation_date, value_date,
               month, description, full_description, amount, status,
               source, account
        FROM movements
        WHERE account = ?
          AND instr(lower(source), 'fineco') > 0
        """,
        (account,),
    ).fetchall()
    return [_as_import_record(row) for row in rows]


def _hash_set(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT movement_hash FROM movements").fetchall()
    return {str(row[0]) for row in rows if row and row[0]}


def preview_movements(
    df: pd.DataFrame,
    source: str = "Fineco",
    account: str | None = None,
) -> dict[str, Any]:
    """
    Analizza un file importato senza scrivere sul database.

    Restituisce conteggi nuovi/duplicati/aggiornamenti, top categorie
    dei nuovi movimenti e eventuali avvisi.
    """
    occurrences: dict[str, int] = {}
    new_rows: list[dict[str, Any]] = []
    skipped = 0
    update_count = 0
    review_count = 0
    account_name = account or source
    fineco = _is_fineco_source(source)
    existing_records: list[dict[str, Any]] = []
    used_ids: set[int] = set()

    virtual_to_new_idx: dict[int, int] = {}
    next_virtual_id = -1

    with get_connection() as conn:
        existing_hashes = _hash_set(conn)
        if fineco:
            existing_records = _load_fineco_records(conn, account_name)
            existing_pairs = _existing_settlement_pairs(existing_records)
            update_count += len(existing_pairs)
            for pending, settled in existing_pairs:
                used_ids.add(int(pending["id"]))
                used_ids.add(int(settled["id"]))
                _overlay_settled(pending, settled)

    for _, row in df.iterrows():
        prepared = _prepare_import_row(
            row,
            source=source,
            occurrences=occurrences,
        )
        if prepared["movement_hash"] in existing_hashes:
            skipped += 1
            continue

        incoming = _as_import_record(prepared, from_prepared=True)
        if fineco:
            twin, ambiguous = _unique_settlement_twin(
                incoming,
                existing_records,
                used_ids,
            )
            if ambiguous:
                review_count += 1
            elif twin is not None:
                twin_id = int(twin["id"])
                if incoming["settled"] and twin["authorized"]:
                    used_ids.add(twin_id)
                    _overlay_settled(twin, incoming)
                    if twin_id > 0:
                        update_count += 1
                    continue
                if incoming["authorized"] and twin["settled"]:
                    skipped += 1
                    used_ids.add(twin_id)
                    continue

        new_rows.append(
            {
                "data": prepared["data"],
                "importo": float(prepared["importo"]),
                "categoria": prepared["categoria"],
                "descrizione": prepared["descrizione"],
                "account": account_name,
            }
        )
        existing_hashes.add(prepared["movement_hash"])
        if fineco:
            incoming["id"] = next_virtual_id
            incoming["hash"] = prepared["movement_hash"]
            existing_records.append(incoming)
            virtual_to_new_idx[next_virtual_id] = len(new_rows) - 1
            next_virtual_id -= 1

    if fineco:
        drop_new: set[int] = set()
        for pending, settled in _existing_settlement_pairs(existing_records):
            pending_id = int(pending["id"])
            settled_id = int(settled["id"])
            if pending_id in used_ids or settled_id in used_ids:
                continue
            used_ids.add(pending_id)
            used_ids.add(settled_id)
            update_count += 1
            for virtual_id in (pending_id, settled_id):
                index = virtual_to_new_idx.get(virtual_id)
                if index is not None:
                    drop_new.add(index)
        if drop_new:
            new_rows = [
                row
                for index, row in enumerate(new_rows)
                if index not in drop_new
            ]

    new_df = pd.DataFrame(new_rows)
    top_categories: list[tuple[str, float]] = []
    total_new_expense = 0.0
    total_new_income = 0.0
    warnings: list[str] = []

    if not new_df.empty:
        total_new_income = float(
            new_df.loc[new_df["importo"] > 0, "importo"].sum()
        )
        expense_mask = new_df["importo"] < 0
        total_new_expense = float(
            abs(new_df.loc[expense_mask, "importo"].sum())
        )
        if expense_mask.any():
            ranked = (
                new_df.loc[expense_mask]
                .groupby("categoria")["importo"]
                .sum()
                .abs()
                .sort_values(ascending=False)
                .head(3)
            )
            top_categories = [
                (str(name), float(value))
                for name, value in ranked.items()
            ]

        missing_dates = int(new_df["data"].fillna("").eq("").sum())
        if missing_dates:
            warnings.append(
                f"{missing_dates} movimenti senza data valida."
            )

    if review_count:
        warnings.append(
            f"{review_count} movimenti da rivedere: più di un "
            "Autorizzato compatibile, non unificati."
        )

    if not new_rows and skipped > 0 and update_count == 0:
        warnings.append(
            "Tutti i movimenti di questo file risultano già presenti."
        )
    elif not new_rows and skipped > 0 and update_count > 0:
        warnings.append(
            "Il file è già in archivio. Conferma per aggiornare "
            f"{update_count} movimenti Autorizzato → Contabilizzato."
        )

    return {
        "new_count": len(new_rows),
        "skip_count": skipped,
        "update_count": update_count,
        "review_count": review_count,
        "total_count": len(df),
        "total_new_income": total_new_income,
        "total_new_expense": total_new_expense,
        "top_categories": top_categories,
        "warnings": warnings,
        "account": account_name,
        "source": source,
    }


def save_movements(
    df: pd.DataFrame,
    source: str = "Fineco",
    account: str | None = None,
) -> tuple[int, int, int]:
    inserted = 0
    skipped = 0
    updated = 0
    occurrences: dict[str, int] = {}
    account_name = account or source
    fineco = _is_fineco_source(source)

    with get_connection() as conn:
        existing_hashes = _hash_set(conn)
        existing_records: list[dict[str, Any]] = []
        used_ids: set[int] = set()
        inserted_ids: set[int] = set()

        if fineco:
            existing_records = _load_fineco_records(conn, account_name)
            collapsed, _retracted = _collapse_fineco_pairs(
                conn,
                account_name,
                inserted_ids,
            )
            updated += collapsed
            existing_records = _load_fineco_records(conn, account_name)
            existing_hashes = _hash_set(conn)

        for _, row in df.iterrows():
            prepared = _prepare_import_row(
                row,
                source=source,
                occurrences=occurrences,
            )
            movement_hash = prepared["movement_hash"]
            if movement_hash in existing_hashes:
                skipped += 1
                continue

            incoming = _as_import_record(prepared, from_prepared=True)
            if fineco:
                twin, ambiguous = _unique_settlement_twin(
                    incoming,
                    existing_records,
                    used_ids,
                )
                if not ambiguous and twin is not None:
                    twin_id = int(twin["id"])
                    if incoming["settled"] and twin["authorized"]:
                        settled_payload = {
                            "id": None,
                            "hash": movement_hash,
                            "data": prepared["data"],
                            "operation_date": prepared["data_operazione"],
                            "value_date": prepared["data_valuta"],
                            "mese": prepared["mese"],
                            "description": prepared["descrizione"],
                            "full_description": prepared[
                                "descrizione_completa"
                            ],
                            "status": prepared["stato"],
                        }
                        if _apply_settlement_merge(
                            conn,
                            twin,
                            settled_payload,
                        ):
                            if twin_id not in inserted_ids:
                                updated += 1
                            used_ids.add(twin_id)
                            existing_hashes.add(movement_hash)
                            incoming["hash"] = movement_hash
                            _overlay_settled(twin, incoming)
                            continue
                    elif incoming["authorized"] and twin["settled"]:
                        skipped += 1
                        used_ids.add(twin_id)
                        continue

            try:
                conn.execute(
                    """
                    INSERT INTO movements (
                        movement_hash,
                        date,
                        operation_date,
                        value_date,
                        month,
                        description,
                        full_description,
                        category,
                        category_source,
                        movement_type,
                        amount,
                        status,
                        source,
                        account,
                        notes,
                        speciale,
                        speciale_mesi,
                        escludi_metriche
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        movement_hash,
                        prepared["data"],
                        prepared["data_operazione"],
                        prepared["data_valuta"],
                        prepared["mese"],
                        prepared["descrizione"],
                        prepared["descrizione_completa"],
                        prepared["categoria"],
                        prepared["category_source"],
                        prepared["tipo"],
                        float(prepared["importo"]),
                        prepared["stato"],
                        source,
                        account_name,
                        "",
                        0,
                        0,
                        0,
                    ),
                )
                inserted += 1
                existing_hashes.add(movement_hash)
                if fineco:
                    new_id = int(
                        conn.execute(
                            "SELECT last_insert_rowid()"
                        ).fetchone()[0]
                    )
                    incoming["id"] = new_id
                    incoming["hash"] = movement_hash
                    existing_records.append(incoming)
                    inserted_ids.add(new_id)
            except sqlite3.IntegrityError:
                skipped += 1

        if fineco:
            collapsed, retracted = _collapse_fineco_pairs(
                conn,
                account_name,
                inserted_ids,
            )
            updated += collapsed
            inserted = max(0, inserted - retracted)

        conn.commit()

    return inserted, skipped, updated


def load_movements() -> pd.DataFrame:
    with get_connection() as conn:
        df = pd.read_sql_query(
            """
            SELECT
                id,
                date AS data,
                operation_date AS data_operazione,
                value_date AS data_valuta,
                month AS mese,
                description AS descrizione,
                full_description AS descrizione_completa,
                category AS categoria,
                category_source,
                movement_type AS tipo,
                amount AS importo,
                status AS stato,
                source,
                account,
                notes,
                speciale,
                speciale_mesi,
                escludi_metriche
            FROM movements
            ORDER BY date DESC
            """,
            conn,
        )

    if df.empty:
        return df

    date_columns = [
        "data",
        "data_operazione",
        "data_valuta",
    ]

    for column in date_columns:
        df[column] = df[column].apply(_parse_date_value)

    df["speciale"] = (
        pd.to_numeric(df["speciale"], errors="coerce")
        .fillna(0)
        .astype(int)
        .astype(bool)
    )
    df["speciale_mesi"] = (
        pd.to_numeric(df["speciale_mesi"], errors="coerce")
        .fillna(0)
        .astype(int)
        .clip(lower=0)
    )
    df["escludi_metriche"] = (
        pd.to_numeric(df["escludi_metriche"], errors="coerce")
        .fillna(0)
        .astype(int)
        .astype(bool)
    )

    df = df.sort_values(
        by=["data", "id"],
        ascending=[False, False],
        na_position="last",
        kind="stable",
    ).reset_index(drop=True)

    return df


def add_manual_movement(
    movement_date: date,
    description: str,
    amount: float,
    category: str,
    movement_type: str,
    account: str,
    notes: str = "",
    speciale: bool = False,
    speciale_mesi: int = 0,
    escludi_metriche: bool = False,
) -> None:
    signed_amount = (
        abs(amount)
        if movement_type == "Entrata"
        else -abs(amount)
    )

    movement_date_string = movement_date.isoformat()
    month = movement_date.strftime("%Y-%m")
    movement_hash = f"manual-{uuid.uuid4()}"

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO movements (
                movement_hash,
                date,
                operation_date,
                value_date,
                month,
                description,
                full_description,
                category,
                category_source,
                movement_type,
                amount,
                status,
                source,
                account,
                notes,
                speciale,
                speciale_mesi,
                escludi_metriche
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                movement_hash,
                movement_date_string,
                movement_date_string,
                movement_date_string,
                month,
                description,
                description,
                category,
                "manual",
                movement_type,
                signed_amount,
                "Manuale",
                "Manuale",
                account,
                notes,
                1 if speciale else 0,
                max(0, int(speciale_mesi)) if speciale else 0,
                1 if escludi_metriche else 0,
            ),
        )
        conn.commit()


def get_movement(movement_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                id,
                date,
                operation_date,
                value_date,
                month,
                description,
                full_description,
                category,
                category_source,
                movement_type,
                amount,
                status,
                source,
                account,
                notes,
                speciale,
                speciale_mesi,
                escludi_metriche
            FROM movements
            WHERE id = ?
            """,
            (movement_id,),
        ).fetchone()
    if row is None:
        return None
    return dict(row)


def snapshot_movements(movement_ids: list[int]) -> list[dict[str, Any]]:
    """Copia completa delle righe, per annullare delete / unisci / dividi."""
    unique_ids = [int(item) for item in dict.fromkeys(movement_ids)]
    if not unique_ids:
        return []
    placeholders = ", ".join("?" for _ in unique_ids)
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM movements WHERE id IN ({placeholders})",
            unique_ids,
        ).fetchall()
    by_id = {int(row["id"]): dict(row) for row in rows}
    return [by_id[item] for item in unique_ids if item in by_id]


def restore_movement_snapshots(rows: list[dict[str, Any]]) -> None:
    """Reinserisce le righe (stesso id e hash)."""
    if not rows:
        return
    with get_connection() as conn:
        columns = [column["name"] for column in conn.execute(
            "PRAGMA table_info(movements)"
        ).fetchall()]
        for row in rows:
            usable = [name for name in columns if name in row]
            if not usable:
                continue
            col_sql = ", ".join(usable)
            placeholders = ", ".join("?" for _ in usable)
            conn.execute(
                f"""
                INSERT OR REPLACE INTO movements ({col_sql})
                VALUES ({placeholders})
                """,
                [row.get(name) for name in usable],
            )
        conn.commit()


def delete_movements(movement_ids: list[int]) -> None:
    unique_ids = [int(item) for item in dict.fromkeys(movement_ids)]
    if not unique_ids:
        return
    with get_connection() as conn:
        conn.executemany(
            "DELETE FROM movements WHERE id = ?",
            [(item,) for item in unique_ids],
        )
        conn.commit()


def undo_movement_action(
    *,
    restore: list[dict[str, Any]],
    delete_ids: list[int] | None = None,
) -> None:
    """Ripristina lo stato precedente di delete / unisci / dividi."""
    if delete_ids:
        delete_movements(delete_ids)
    restore_movement_snapshots(restore)


def update_movement(
    movement_id: int,
    *,
    movement_date: date,
    description: str,
    amount: float,
    category: str,
    movement_type: str,
    account: str,
    notes: str = "",
    full_description: str | None = None,
    speciale: bool = False,
    speciale_mesi: int = 0,
    escludi_metriche: bool = False,
) -> None:
    """Aggiorna i campi modificabili di un movimento. L'hash resta invariato."""
    signed_amount = (
        abs(amount)
        if movement_type == "Entrata"
        else -abs(amount)
    )
    is_expense = movement_type == "Uscita" and category != INVESTMENT_CATEGORY
    if not is_expense:
        speciale = False
        speciale_mesi = 0

    description = description.strip()
    resolved_full = (
        description
        if full_description is None
        else str(full_description).strip() or description
    )
    notes = notes.strip()
    account = account.strip() or "Altro"
    month = movement_date.strftime("%Y-%m")
    date_string = movement_date.isoformat()

    current = get_movement(movement_id)
    category_source = "manual"
    if current is not None and str(current.get("category") or "") == category:
        category_source = (
            str(current.get("category_source") or "manual") or "manual"
        )

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE movements
            SET date = ?,
                month = ?,
                description = ?,
                full_description = ?,
                category = ?,
                category_source = ?,
                movement_type = ?,
                amount = ?,
                account = ?,
                notes = ?,
                speciale = ?,
                speciale_mesi = ?,
                escludi_metriche = ?
            WHERE id = ?
            """,
            (
                date_string,
                month,
                description,
                resolved_full,
                category,
                category_source,
                movement_type,
                _money(signed_amount),
                account,
                notes,
                1 if speciale else 0,
                max(0, int(speciale_mesi)) if speciale else 0,
                1 if escludi_metriche else 0,
                movement_id,
            ),
        )
        conn.commit()


def split_movement(
    movement_id: int,
    parts: list[tuple[float, str]],
) -> list[int]:
    """
    Divide un movimento in più quote.

    La prima quota aggiorna la riga originale (hash invariato, così
    un re-import non duplica). Le altre diventano nuovi movimenti.
    Restituisce gli id delle nuove righe.
    """
    if len(parts) < 2:
        raise ValueError("Servono almeno due parti.")

    original = get_movement(movement_id)
    if original is None:
        raise ValueError("Movimento non trovato.")

    cleaned: list[tuple[float, str]] = []
    for raw_amount, raw_category in parts:
        amount = _money(abs(float(raw_amount)))
        category = str(raw_category).strip() or "Altro"
        if amount <= 0:
            raise ValueError("Ogni parte deve avere un importo maggiore di zero.")
        cleaned.append((amount, category))

    original_abs = _money(abs(float(original["amount"])))
    parts_total = _money(sum(amount for amount, _ in cleaned))
    if abs(parts_total - original_abs) > 0.011:
        raise ValueError(
            "La somma delle parti deve coincidere con l'importo originale."
        )

    original_amount = float(original["amount"])
    movement_type = (
        "Entrata" if original_amount >= 0 else "Uscita"
    )
    sign = 1 if original_amount >= 0 else -1

    parsed_date = _parse_date_value(original["date"])
    if pd.isna(parsed_date):
        raise ValueError("Data originale non valida.")

    first_amount, first_category = cleaned[0]
    original_description = _clean_text_value(original.get("description"))
    original_full = _clean_text_value(original.get("full_description"))
    update_movement(
        movement_id,
        movement_date=parsed_date.date(),
        description=original_description or original_full,
        full_description=original_full or original_description,
        amount=first_amount,
        category=first_category,
        movement_type=movement_type,
        account=_clean_text_value(original.get("account")) or "Altro",
        notes=_clean_text_value(original.get("notes")),
        speciale=bool(original.get("speciale")),
        speciale_mesi=int(original.get("speciale_mesi") or 0),
        escludi_metriche=bool(original.get("escludi_metriche")),
    )

    created_ids: list[int] = []
    with get_connection() as conn:
        for amount, category in cleaned[1:]:
            signed_amount = _money(sign * amount)
            cursor = conn.execute(
                """
                INSERT INTO movements (
                    movement_hash,
                    date,
                    operation_date,
                    value_date,
                    month,
                    description,
                    full_description,
                    category,
                    category_source,
                    movement_type,
                    amount,
                    status,
                    source,
                    account,
                    notes,
                    speciale,
                    speciale_mesi,
                    escludi_metriche
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"split-{uuid.uuid4()}",
                    original.get("date") or "",
                    original.get("operation_date") or "",
                    original.get("value_date") or "",
                    original.get("month") or "",
                    _clean_text_value(original.get("description")),
                    _clean_text_value(original.get("full_description"))
                    or _clean_text_value(original.get("description")),
                    category,
                    "manual",
                    movement_type,
                    signed_amount,
                    _clean_text_value(original.get("status")),
                    _clean_text_value(original.get("source")) or "Manuale",
                    _clean_text_value(original.get("account")) or "Altro",
                    "",
                    0,
                    0,
                    1 if original.get("escludi_metriche") else 0,
                ),
            )
            created_ids.append(int(cursor.lastrowid))
        conn.commit()

    return created_ids


def merge_movements(
    movement_ids: list[int],
    *,
    description: str,
    category: str,
    notes: str = "",
) -> int:
    """
    Unisce più movimenti in uno.

    Resta la riga più vecchia (hash invariato). Le altre vengono
    eliminate. Devono appartenere allo stesso conto.
    """
    unique_ids = list(dict.fromkeys(int(item) for item in movement_ids))
    if len(unique_ids) < 2:
        raise ValueError("Seleziona almeno due movimenti.")

    rows = [get_movement(item) for item in unique_ids]
    if any(row is None for row in rows):
        raise ValueError("Uno dei movimenti non è stato trovato.")
    loaded = [row for row in rows if row is not None]

    accounts = {
        _clean_text_value(row.get("account")) or "Altro"
        for row in loaded
    }
    if len(accounts) != 1:
        raise ValueError("Puoi unire solo movimenti dello stesso conto.")

    total = _money(sum(float(row["amount"]) for row in loaded))
    if abs(total) < 0.01:
        raise ValueError("La somma dei movimenti è zero.")

    def _sort_key(row: dict[str, Any]) -> tuple:
        parsed = _parse_date_value(row.get("date"))
        stamp = (
            parsed.normalize()
            if not pd.isna(parsed)
            else pd.Timestamp.max
        )
        return stamp, int(row["id"])

    loaded.sort(key=_sort_key)
    survivor = loaded[0]
    drop_ids = [int(row["id"]) for row in loaded[1:]]
    parsed_date = _parse_date_value(survivor.get("date"))
    if pd.isna(parsed_date):
        raise ValueError("Data originale non valida.")

    movement_type = "Entrata" if total >= 0 else "Uscita"
    update_movement(
        int(survivor["id"]),
        movement_date=parsed_date.date(),
        description=description.strip() or _clean_text_value(
            survivor.get("description")
        ),
        full_description=_clean_text_value(survivor.get("full_description"))
        or description.strip(),
        amount=abs(total),
        category=category.strip() or "Altro",
        movement_type=movement_type,
        account=_clean_text_value(survivor.get("account")) or "Altro",
        notes=notes.strip(),
        speciale=False,
        speciale_mesi=0,
        escludi_metriche=False,
    )

    with get_connection() as conn:
        conn.executemany(
            "DELETE FROM movements WHERE id = ?",
            [(item,) for item in drop_ids],
        )
        conn.commit()

    return len(drop_ids)


def delete_movement(movement_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM movements
            WHERE id = ?
            """,
            (movement_id,),
        )
        conn.commit()


def delete_account(account: str) -> int:
    """Elimina dal DB tutti i movimenti del conto. Restituisce quante righe sono state cancellate."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            DELETE FROM movements
            WHERE account = ?
            """,
            (account,),
        )
        conn.commit()
        return int(cursor.rowcount)


def recalculate_automatic_categories() -> int:
    updated = 0
    df = load_movements()

    if df.empty:
        return 0

    with get_connection() as conn:
        for _, row in df.iterrows():
            if row.get("category_source") == "manual":
                continue

            text = (
                f"{row.get('descrizione', '')} "
                f"{row.get('descrizione_completa', '')}"
            )

            new_category = categorize(text)

            if new_category != row.get("categoria"):
                conn.execute(
                    """
                    UPDATE movements
                    SET category = ?
                    WHERE id = ?
                    """,
                    (new_category, int(row["id"])),
                )
                updated += 1

        conn.commit()

    return updated
