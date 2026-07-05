import streamlit as st

from src.database.db import init_db
from src.pages.dashboard import show_dashboard
from src.pages.import_data import show_import_data
from src.pages.manual_entry import show_manual_entry
from src.pages.movements import show_movements
from src.pages.settings import show_settings
from src.theme.style import apply_theme

APP_VERSION = "v0.4.0"


st.set_page_config(
    page_title="FinanceTracker",
    page_icon="assets/icons/ft_logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
init_db()


st.sidebar.image(
    "assets/icons/ft_logo.png",
    width=145,
)

st.sidebar.markdown(
    f"""
    <div style="margin-bottom: 22px;">
        <div style="font-size: 30px; font-weight: 950; color: #f8fafc;">
            Finance<span style="color:#22c55e;">Tracker</span>
        </div>
        <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">
            Personal finance
        </div>
        <div style="
            display: inline-block;
            margin-top: 12px;
            padding: 4px 10px;
            border-radius: 999px;
            background: rgba(34, 197, 94, 0.14);
            color: #22c55e;
            font-size: 12px;
            font-weight: 800;
        ">
            {APP_VERSION}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.divider()

if "page" not in st.session_state:
    st.session_state["page"] = "Dashboard"


def sidebar_button(label: str, page_name: str) -> None:
    selected = st.session_state["page"] == page_name

    if st.sidebar.button(
        label,
        key=f"nav_{page_name}",
        use_container_width=True,
        type="primary" if selected else "secondary",
    ):
        st.session_state["page"] = page_name
        st.rerun()


sidebar_button("🏠 Dashboard", "Dashboard")
sidebar_button("💳 Movimenti", "Movimenti")
sidebar_button("➕ Nuovo movimento", "Nuovo movimento")
sidebar_button("📥 Importa dati", "Importa dati")
sidebar_button("⚙️ Impostazioni", "Impostazioni")

st.sidebar.markdown(
    """
    <div style="
        position: fixed;
        bottom: 24px;
        font-size: 12px;
        color: #64748b;
    ">
    </div>
    """,
    unsafe_allow_html=True,
)

page = st.session_state["page"]

if page == "Dashboard":
    show_dashboard()
elif page == "Movimenti":
    show_movements()
elif page == "Nuovo movimento":
    show_manual_entry()
elif page == "Importa dati":
    show_import_data()
elif page == "Impostazioni":
    show_settings()