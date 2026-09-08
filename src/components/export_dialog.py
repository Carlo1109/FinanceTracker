"""Dialog di conferma per export Excel movimenti."""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from src.components.cards import render_html
from src.utils.export_excel import movements_to_export_bytes
from src.utils.file_save import save_and_reveal


EXPORT_DIALOG_KEY = "ft_export_dialog"


def open_export_confirm_dialog(
    df: pd.DataFrame,
    *,
    file_name: str,
    context_label: str | None = None,
    dialog_key: str = "export",
) -> None:
    """Apre il popup di conferma export (persistente fino a chiusura)."""
    st.session_state[EXPORT_DIALOG_KEY] = {
        "df": df,
        "file_name": file_name,
        "context_label": context_label,
        "dialog_key": dialog_key,
    }


def render_pending_export_dialog() -> None:
    """Se c’è un export in attesa, mostra il popup."""
    payload = st.session_state.get(EXPORT_DIALOG_KEY)
    if not payload:
        return

    _export_confirm_dialog(
        payload["df"],
        file_name=payload["file_name"],
        context_label=payload.get("context_label"),
        dialog_key=str(payload.get("dialog_key") or "export"),
    )


def _close_export_dialog() -> None:
    st.session_state.pop(EXPORT_DIALOG_KEY, None)


@st.dialog("Esporta Excel")
def _export_confirm_dialog(
    df: pd.DataFrame,
    *,
    file_name: str,
    context_label: str | None = None,
    dialog_key: str = "export",
) -> None:
    count = len(df)
    context_html = ""
    if context_label:
        context_html = (
            f'<div style="margin-top:8px;font-size:13px;'
            f'font-weight:650;color:var(--ft-accent-strong);">'
            f"{html.escape(context_label)}</div>"
        )

    render_html(
        f"""
        <div class="ft-export-dialog" style="padding:2px 0 8px 0;">
          <div class="ft-appearance-chip" style="width:fit-content;">
            <span class="ft-appearance-chip-dot"></span>
            Excel brandizzato
          </div>
          <div style="
              margin-top:14px;
              font-family:Fraunces,Georgia,serif;
              font-size:clamp(22px, 2.2vw, 28px);
              font-weight:700;
              color:var(--ft-text);
              line-height:1.2;
          ">
            Esporta {count} movimenti
          </div>
          {context_html}
          <div style="
              margin-top:10px;
              font-size:13px;
              line-height:1.45;
              color:var(--ft-muted);
          ">
            Il file include logo FinanceTracker e
            Personal Finance Manager.
            Si salva nella cartella Download.
          </div>
        </div>
        """
    )

    confirm_col, cancel_col = st.columns(2)
    with confirm_col:
        if st.button(
            "Conferma e scarica",
            type="primary",
            width="stretch",
            key=f"export_dialog_save_{dialog_key}",
        ):
            saved = save_and_reveal(
                movements_to_export_bytes(df),
                file_name,
            )
            _close_export_dialog()
            st.toast(f"Salvato in Download: {saved.name}")
            st.rerun()

    with cancel_col:
        if st.button(
            "Annulla",
            width="stretch",
            type="secondary",
            key=f"export_dialog_cancel_{dialog_key}",
        ):
            _close_export_dialog()
            st.rerun()
