import html
from pathlib import Path

import streamlit as st

from src.components.cards import (
    EXPENSE_COLOR,
    INCOME_COLOR,
    MUTED_COLOR,
    TEXT_COLOR,
    render_html,
    render_kpi_card,
    render_section_title,
    styled_panel,
)
from src.services.categories import get_category_icon
from src.services.imports import get_importer_by_label, list_importers
from src.services.movement_service import preview_movements, save_movements
from src.utils.formatting import euro


IMPORT_RESULT_KEY = "import_last_result"
IMPORT_PREVIEW_KEY = "import_preview_payload"


def _file_signature(uploaded_file) -> str:
    return f"{uploaded_file.name}|{uploaded_file.size}|{uploaded_file.type}"


def _render_preview_panel(preview: dict) -> None:
    new_count = int(preview["new_count"])
    skip_count = int(preview["skip_count"])
    total_count = int(preview["total_count"])
    account = html.escape(str(preview.get("account") or ""))

    render_section_title("Anteprima import")
    with styled_panel():
        render_html(
            f"""
            <div style="
                margin-bottom:14px;
                animation: ft-fade-up 280ms ease-out;
            ">
                <div style="
                    font-family:Fraunces,Georgia,serif;
                    font-size:clamp(24px, 2.4vw, 30px);
                    font-weight:700;
                    color:{TEXT_COLOR};
                    line-height:1.15;
                ">
                    {new_count} nuovi · {skip_count} già presenti
                </div>
                <div style="
                    margin-top:8px;
                    font-size:13px;
                    color:{MUTED_COLOR};
                ">
                    Su {total_count} righe nel file · conto {account}
                </div>
            </div>
            """
        )

        m1, m2, m3 = st.columns(3)
        with m1:
            render_kpi_card("Nuovi", str(new_count), value_color=INCOME_COLOR)
        with m2:
            render_kpi_card("Duplicati", str(skip_count), value_color=MUTED_COLOR)
        with m3:
            render_kpi_card(
                "Uscite nuove",
                euro(float(preview["total_new_expense"])),
                value_color=EXPENSE_COLOR,
            )

        top_categories = list(preview.get("top_categories") or [])
        if top_categories:
            chips = " · ".join(
                f"{get_category_icon(name)} {name} ({euro(amount)})"
                for name, amount in top_categories
            )
            st.caption(f"Top categorie nei nuovi movimenti: {chips}")

        for warning in preview.get("warnings") or []:
            st.warning(warning)


def _render_import_wow(result: dict) -> None:
    inserted = int(result["inserted"])
    skipped = int(result["skipped"])
    top_categories = list(result.get("top_categories") or [])
    top_line = ""
    if top_categories:
        name, amount = top_categories[0]
        top_line = (
            f"Top: {get_category_icon(name)} {name} · {euro(amount)}"
        )

    with styled_panel():
        render_html(
            f"""
            <div style="
                padding:6px 2px 2px 2px;
                animation: ft-import-pop 520ms cubic-bezier(0.22, 1, 0.36, 1);
            ">
                <div style="
                    font-family:Manrope,sans-serif;
                    font-size:12px;
                    font-weight:650;
                    letter-spacing:0.1em;
                    text-transform:uppercase;
                    color:#86efac;
                ">Import completato</div>
                <div style="
                    margin-top:10px;
                    font-family:Fraunces,Georgia,serif;
                    font-size:clamp(28px, 3vw, 36px);
                    font-weight:700;
                    color:{TEXT_COLOR};
                    line-height:1.15;
                ">
                    +{inserted} movimenti
                </div>
                <div style="
                    margin-top:8px;
                    font-size:14px;
                    color:{MUTED_COLOR};
                ">
                    {skipped} già presenti · uscite
                    {euro(float(result.get("total_new_expense") or 0))}
                    · entrate {euro(float(result.get("total_new_income") or 0))}
                </div>
                <div style="
                    margin-top:10px;
                    font-size:14px;
                    font-weight:650;
                    color:#bbf7d0;
                ">
                    {html.escape(top_line)}
                </div>
            </div>
            """
        )

    if inserted == 0 and skipped > 0:
        st.info(
            "Il file era già stato importato. "
            "Nessun nuovo movimento aggiunto."
        )


def show_import_data() -> None:
    st.title("Importa dati")
    st.caption(
        "Importa movimenti da file esterni. "
        "Prima vedi l’anteprima, poi confermi."
    )

    result = st.session_state.pop(IMPORT_RESULT_KEY, None)
    if result:
        inserted = int(result.get("inserted") or 0)
        st.toast(f"Import completato: +{inserted} movimenti")
        _render_import_wow(result)
        st.markdown("")

    importers = list_importers()
    labels = [info.label for info in importers]

    render_section_title("Sorgente dati")
    with styled_panel():
        source_label = st.selectbox("Origine", labels)
        importer = get_importer_by_label(source_label)
        info = importer.info
        allowed_extensions = {ext.lower() for ext in info.extensions}

        uploaded_file = st.file_uploader(
            f"File {info.label}",
            type=None,
            help=info.help_text,
        )

        if uploaded_file:
            suffix = Path(uploaded_file.name).suffix.lower()
            if suffix not in allowed_extensions:
                expected = ", ".join(sorted(allowed_extensions))
                st.error(
                    f"Formato non supportato per {info.label}. "
                    f"Usa: {expected}"
                )
                uploaded_file = None

        if uploaded_file:
            render_html(
                f"""
                <div style="
                    margin-top:18px;
                    margin-bottom:4px;
                    padding:14px 16px;
                    border-radius:14px;
                    background:rgba(52,211,153,0.10);
                    border:1px solid rgba(52,211,153,0.22);
                    color:{TEXT_COLOR};
                    font-size:14px;
                ">
                    File selezionato:
                    <b>{html.escape(uploaded_file.name)}</b>
                </div>
                """
            )
        else:
            st.session_state.pop(IMPORT_PREVIEW_KEY, None)
            expected = ", ".join(sorted(allowed_extensions))
            st.info(
                f"Seleziona un file {info.label} ({expected}) per vedere "
                "l’anteprima. Puoi anche trascinarlo sulla zona di upload."
            )

    if not uploaded_file:
        return

    signature = _file_signature(uploaded_file)
    cached = st.session_state.get(IMPORT_PREVIEW_KEY)
    needs_parse = (
        not cached
        or cached.get("signature") != signature
        or cached.get("source") != info.label
    )

    if needs_parse:
        with st.spinner("Analisi del file..."):
            try:
                imported_df = importer.parse(uploaded_file)
                preview = preview_movements(
                    imported_df,
                    source=info.label,
                    account=info.account,
                )
                st.session_state[IMPORT_PREVIEW_KEY] = {
                    "signature": signature,
                    "source": info.label,
                    "account": info.account,
                    "preview": preview,
                }
            except Exception as error:  # noqa: BLE001
                st.session_state.pop(IMPORT_PREVIEW_KEY, None)
                st.error(f"Analisi fallita: {error}")
                return

    payload = st.session_state.get(IMPORT_PREVIEW_KEY) or {}
    preview = payload.get("preview") or {}

    _render_preview_panel(preview)

    st.markdown("")
    can_import = int(preview.get("new_count") or 0) > 0
    if st.button(
        "Conferma import",
        width="stretch",
        type="primary",
        disabled=not can_import,
    ):
        with st.spinner("Importazione in corso..."):
            try:
                uploaded_file.seek(0)
                imported_df = importer.parse(uploaded_file)
                inserted, skipped = save_movements(
                    imported_df,
                    source=info.label,
                    account=info.account,
                )
            except Exception as error:  # noqa: BLE001
                st.error(f"Import fallito: {error}")
                return

        st.session_state[IMPORT_RESULT_KEY] = {
            "inserted": inserted,
            "skipped": skipped,
            "total_new_income": preview.get("total_new_income", 0),
            "total_new_expense": preview.get("total_new_expense", 0),
            "top_categories": preview.get("top_categories") or [],
        }
        st.session_state.pop(IMPORT_PREVIEW_KEY, None)
        st.rerun()

    if not can_import:
        st.caption("Niente da importare: conferma disabilitata.")
