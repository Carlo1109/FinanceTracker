"""Collegamento andata/ritorno della categoria Prestiti."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from src.database.db import get_connection
from src.services.analytics import LOAN_CATEGORY, is_loan_category


_OPEN_EPS = 0.004
_TOKEN_RE = re.compile(r"[A-Z0-9']{3,}")
_TOKEN_STOP = {
    "PAGAMENTO",
    "BONIFICO",
    "SEPA",
    "ISTANTANEO",
    "BENEFICIARIO",
    "ORDINANTE",
    "CARTA",
    "DATA",
    "OPERAZIONE",
    "INSERIMENTO",
    "CANALE",
    "CAUSALE",
    "PHONE",
    "VOICE",
    "TRN",
    "IBAN",
}


def parse_loan_parent_id(value: object) -> int | None:
    if value is None or pd.isna(value):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _money(value: object) -> float:
    return round(float(pd.to_numeric(value, errors="coerce") or 0), 2)


def _is_loan_out(category: object, amount: object) -> bool:
    return is_loan_category(category) and _money(amount) < -_OPEN_EPS


def _is_loan_in(category: object, amount: object) -> bool:
    return is_loan_category(category) and _money(amount) > _OPEN_EPS


def _tokens(*parts: object) -> set[str]:
    text = " ".join(str(part or "") for part in parts).upper()
    tokens: set[str] = set()
    for raw in _TOKEN_RE.findall(text):
        token = raw.replace("'", "")
        if token in _TOKEN_STOP or token.isdigit():
            continue
        tokens.add(token)
    return tokens


def loan_child_ids(parent_id: int) -> list[int]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id FROM movements
            WHERE prestito_di = ?
            ORDER BY date ASC, id ASC
            """,
            (int(parent_id),),
        ).fetchall()
    return [int(row["id"]) for row in rows]


def loan_related_ids(movement_id: int) -> list[int]:
    """Il movimento più eventuali rientri collegati (per snapshot/undo)."""
    related = [int(movement_id)]
    for child_id in loan_child_ids(movement_id):
        if child_id not in related:
            related.append(child_id)
    return related


def loan_practice_ids(movement_id: int) -> list[int]:
    """Uscita e tutti i rientri della pratica, o solo questo movimento."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, prestito_di FROM movements WHERE id = ?",
            (int(movement_id),),
        ).fetchone()
    if row is None:
        return [int(movement_id)]
    parent_id = parse_loan_parent_id(row["prestito_di"]) or int(row["id"])
    members = [parent_id]
    for child_id in loan_child_ids(parent_id):
        if child_id not in members:
            members.append(child_id)
    if int(movement_id) not in members:
        members.append(int(movement_id))
    return members


def unlink_repayment(child_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE movements SET prestito_di = NULL WHERE id = ?",
            (int(child_id),),
        )
        conn.commit()


def unlink_children(parent_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE movements SET prestito_di = NULL WHERE prestito_di = ?",
            (int(parent_id),),
        )
        conn.commit()


def sanitize_loan_links(conn: Any | None = None) -> None:
    """Toglie link se uscita/entrata non sono più Prestiti validi."""
    own = conn is None
    if own:
        conn = get_connection()
    try:
        valid_parents = {
            int(row["id"])
            for row in conn.execute(
                """
                SELECT id FROM movements
                WHERE category = ? AND amount < 0
                """,
                (LOAN_CATEGORY,),
            ).fetchall()
        }
        linked = conn.execute(
            """
            SELECT id, category, amount, prestito_di
            FROM movements
            WHERE prestito_di IS NOT NULL
            """
        ).fetchall()
        for row in linked:
            parent_id = parse_loan_parent_id(row["prestito_di"])
            invalid = (
                not is_loan_category(row["category"])
                or _money(row["amount"]) <= 0
                or parent_id is None
                or parent_id not in valid_parents
            )
            if invalid:
                conn.execute(
                    "UPDATE movements SET prestito_di = NULL WHERE id = ?",
                    (int(row["id"]),),
                )
        if own:
            conn.commit()
    finally:
        if own:
            conn.close()


def sync_loan_links_after_edit(movement_id: int) -> None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, category, amount
            FROM movements WHERE id = ?
            """,
            (int(movement_id),),
        ).fetchone()
        if row is None:
            return
        category = row["category"]
        amount = _money(row["amount"])
        if not is_loan_category(category):
            conn.execute(
                "UPDATE movements SET prestito_di = NULL WHERE id = ?",
                (int(movement_id),),
            )
            conn.execute(
                "UPDATE movements SET prestito_di = NULL WHERE prestito_di = ?",
                (int(movement_id),),
            )
        elif amount >= 0:
            conn.execute(
                "UPDATE movements SET prestito_di = NULL WHERE prestito_di = ?",
                (int(movement_id),),
            )
        else:
            conn.execute(
                "UPDATE movements SET prestito_di = NULL WHERE id = ?",
                (int(movement_id),),
            )
        sanitize_loan_links(conn)
        conn.commit()


def link_repayment(child_id: int, parent_id: int) -> None:
    if int(child_id) == int(parent_id):
        raise ValueError("Non puoi collegare un movimento a se stesso.")
    with get_connection() as conn:
        child = conn.execute(
            "SELECT id, category, amount, prestito_di FROM movements WHERE id = ?",
            (int(child_id),),
        ).fetchone()
        parent = conn.execute(
            "SELECT id, category, amount, prestito_di FROM movements WHERE id = ?",
            (int(parent_id),),
        ).fetchone()
        if child is None or parent is None:
            raise ValueError("Movimento non trovato.")
        if not _is_loan_in(child["category"], child["amount"]):
            raise ValueError("Si collega solo un rientro Prestiti.")
        if not _is_loan_out(parent["category"], parent["amount"]):
            raise ValueError("Il prestito di destinazione deve essere un’uscita Prestiti.")
        if parse_loan_parent_id(parent["prestito_di"]):
            raise ValueError("Quel movimento è già un rientro, non una pratica.")
        conn.execute(
            "UPDATE movements SET prestito_di = ? WHERE id = ?",
            (int(parent_id), int(child_id)),
        )
        conn.commit()


def _row_label(row: pd.Series) -> str:
    full = str(row.get("descrizione_completa") or "").strip()
    short = str(row.get("descrizione") or "").strip()
    title = full or short or "Senza descrizione"
    title = " ".join(title.split())
    if len(title) > 42:
        title = title[:41].rstrip() + "…"
    return title


def _practice_from_parent(
    parent: pd.Series,
    children: pd.DataFrame,
) -> dict[str, Any]:
    outgoing = abs(_money(parent["importo"]))
    repaid = float(
        pd.to_numeric(children["importo"], errors="coerce").fillna(0).sum()
    ) if not children.empty else 0.0
    repaid = round(repaid, 2)
    remaining = round(outgoing - repaid, 2)
    full = str(parent.get("descrizione_completa") or "").strip()
    short = str(parent.get("descrizione") or "").strip()
    return {
        "id": int(parent["id"]),
        "description": _row_label(parent),
        "search_text": f"{full} {short}",
        "account": str(parent.get("account") or ""),
        "date": parent.get("data"),
        "outgoing": outgoing,
        "repaid": repaid,
        "remaining": remaining,
        "open": remaining > _OPEN_EPS,
        "overpaid": remaining < -_OPEN_EPS,
        "child_ids": (
            [int(item) for item in children["id"].tolist()]
            if not children.empty
            else []
        ),
    }


def loan_practices(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df is None or df.empty or "categoria" not in df.columns:
        return []
    loans = df.loc[df["categoria"].map(is_loan_category)].copy()
    if loans.empty:
        return []
    loans["importo"] = pd.to_numeric(loans["importo"], errors="coerce").fillna(0)
    if "prestito_di" not in loans.columns:
        loans["prestito_di"] = pd.NA
    outgoing = loans.loc[loans["importo"] < -_OPEN_EPS].copy()
    incoming = loans.loc[loans["importo"] > _OPEN_EPS].copy()
    practices: list[dict[str, Any]] = []
    for _, parent in outgoing.iterrows():
        parent_id = int(parent["id"])
        children = incoming.loc[
            incoming["prestito_di"].map(parse_loan_parent_id) == parent_id
        ]
        practices.append(_practice_from_parent(parent, children))
    practices.sort(
        key=lambda item: (
            item["open"],
            str(item.get("date") or ""),
            item["id"],
        ),
        reverse=True,
    )
    return practices


def unlinked_repayment_count(df: pd.DataFrame) -> int:
    if df is None or df.empty or "categoria" not in df.columns:
        return 0
    loans = df.loc[df["categoria"].map(is_loan_category)]
    if loans.empty:
        return 0
    amounts = pd.to_numeric(loans["importo"], errors="coerce").fillna(0)
    incoming = loans.loc[amounts > _OPEN_EPS]
    if incoming.empty:
        return 0
    parents = incoming["prestito_di"].map(parse_loan_parent_id) if (
        "prestito_di" in incoming.columns
    ) else pd.Series([None] * len(incoming), index=incoming.index)
    return int(parents.isna().sum())


def movement_loan_chip(row: pd.Series, practices: list[dict[str, Any]]) -> str:
    if not is_loan_category(row.get("categoria")):
        return ""
    amount = _money(row.get("importo"))
    movement_id = int(row["id"])
    if amount < -_OPEN_EPS:
        for practice in practices:
            if practice["id"] == movement_id:
                return "Aperto" if practice["open"] else "Chiuso"
        return "Aperto"
    if amount > _OPEN_EPS:
        parent_id = parse_loan_parent_id(row.get("prestito_di"))
        return "Collegato" if parent_id else "Da collegare"
    return ""


def open_loan_options(
    df: pd.DataFrame,
    *,
    exclude_id: int | None = None,
) -> list[dict[str, Any]]:
    options: list[dict[str, Any]] = []
    for practice in loan_practices(df):
        if exclude_id is not None and practice["id"] == int(exclude_id):
            continue
        options.append(practice)
    options.sort(key=lambda item: (not item["open"], item["remaining"]))
    return options


def suggest_loan_parent_id(
    incoming: pd.Series,
    options: list[dict[str, Any]],
) -> int | None:
    if not options:
        return None
    incoming_amount = _money(incoming.get("importo"))
    incoming_tokens = _tokens(
        incoming.get("descrizione"),
        incoming.get("descrizione_completa"),
        incoming.get("notes"),
    )
    scored: list[tuple[int, int]] = []
    for practice in options:
        if not practice["open"]:
            continue
        score = 0
        remaining = float(practice["remaining"])
        if abs(remaining - incoming_amount) <= 0.02:
            score += 4
        elif incoming_amount <= remaining + 0.02:
            score += 2
        parent_tokens = _tokens(
            practice.get("search_text"),
            practice["description"],
            practice["account"],
        )
        shared = incoming_tokens & parent_tokens
        score += min(len(shared), 3)
        if score <= 0:
            continue
        scored.append((score, practice["id"]))
    if not scored:
        open_ones = [item for item in options if item["open"]]
        return int(open_ones[0]["id"]) if open_ones else int(options[0]["id"])
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[0][1]


def practice_by_id(
    practices: list[dict[str, Any]],
    parent_id: int,
) -> dict[str, Any] | None:
    for practice in practices:
        if practice["id"] == int(parent_id):
            return practice
    return None


def is_linked_practice(practice: dict[str, Any]) -> bool:
    return bool(practice.get("child_ids"))


def is_settled_practice(practice: dict[str, Any]) -> bool:
    return (not practice.get("open")) and is_linked_practice(practice)


def settled_parent_id(
    movement_id: int,
    practices: list[dict[str, Any]],
) -> int | None:
    """Se il movimento è parte di una pratica collegata, id dell’uscita."""
    for practice in practices:
        if not is_linked_practice(practice):
            continue
        members = {int(practice["id"]), *practice["child_ids"]}
        if int(movement_id) in members:
            return int(practice["id"])
    return None


def collapse_closed_loan_rows(
    filtered_df: pd.DataFrame,
    source_df: pd.DataFrame,
    practices: list[dict[str, Any]] | None = None,
) -> pd.DataFrame:
    """Una riga per pratica Prestiti collegata (anche parziale)."""
    if filtered_df is None or filtered_df.empty:
        return filtered_df
    working = filtered_df.copy()
    working["_loan_closed"] = False
    working["_loan_sort_data"] = working["data"]
    if source_df is None or source_df.empty:
        return working
    if practices is None:
        practices = loan_practices(source_df)
    linked = [item for item in practices if is_linked_practice(item)]
    if not linked:
        return working

    visible_ids = {
        int(item) for item in pd.to_numeric(working["id"], errors="coerce")
        if pd.notna(item)
    }
    hide_ids: set[int] = set()
    show_parent_ids: list[int] = []
    for practice in linked:
        members = {int(practice["id"]), *practice["child_ids"]}
        if members & visible_ids:
            show_parent_ids.append(int(practice["id"]))
            hide_ids.update(members)

    leftover = working.loc[~working["id"].isin(hide_ids)].copy()
    leftover["_loan_closed"] = False
    if not show_parent_ids:
        leftover["_loan_sort_data"] = leftover["data"]
        return leftover

    parents = source_df.loc[source_df["id"].isin(show_parent_ids)].copy()
    if parents.empty:
        leftover["_loan_sort_data"] = leftover["data"]
        return leftover
    parents["_loan_closed"] = True
    sort_dates: dict[int, object] = {}
    for practice in linked:
        parent_id = int(practice["id"])
        if parent_id not in show_parent_ids:
            continue
        members = [parent_id, *practice["child_ids"]]
        member_dates = pd.to_datetime(
            source_df.loc[source_df["id"].isin(members), "data"],
            errors="coerce",
        )
        sort_dates[parent_id] = member_dates.max()
    parents["_loan_sort_data"] = parents["id"].map(sort_dates)
    leftover["_loan_sort_data"] = leftover["data"]
    combined = pd.concat([leftover, parents], ignore_index=True)
    return combined.drop_duplicates(subset=["id"], keep="last")
