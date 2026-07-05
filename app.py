import streamlit as st

from src.pages.dashboard import show_dashboard
from src.pages.movements import show_movements
from src.pages.manual_entry import show_manual_entry
from src.theme.style import apply_theme
from src.database.db import init_db

st.set_page_config(
    page_title="FinanceTracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
init_db()

st.sidebar.markdown("# 💰 FinanceTracker")
st.sidebar.caption("Personal finance dashboard")

page = st.sidebar.radio(
    "Navigazione",
    ["Dashboard", "Movimenti", "Aggiungi movimento"],
)

if page == "Dashboard":
    show_dashboard()
elif page == "Movimenti":
    show_movements()
elif page == "Aggiungi movimento":
    show_manual_entry()