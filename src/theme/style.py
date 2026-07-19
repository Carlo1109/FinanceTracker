import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        /* =====================================================
           STREAMLIT CHROME
        ===================================================== */

        #MainMenu {
            display: none !important;
        }

        footer {
            display: none !important;
        }

        header[data-testid="stHeader"] {
            display: none !important;
        }

        [data-testid="stToolbar"] {
            display: none !important;
        }

        /* La sidebar nativa non viene utilizzata. */
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"] {
            display: none !important;
        }

        /* =====================================================
           PAGE
        ===================================================== */

        /* Link delle pagine nella navigazione custom */
        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stPageLink"] a {
            min-height: 48px;
            display: flex;
            align-items: center;
            gap: 10px;

            margin: 5px 0;
            padding: 0 16px;

            border-radius: 15px;
            border: 1px solid transparent;

            color: #cbd5e1 !important;
            font-size: 15px;
            font-weight: 800;
            text-decoration: none !important;

            transition:
                transform 140ms ease,
                background 140ms ease,
                border-color 140ms ease;
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stPageLink"] a:hover {
            transform: translateX(3px);
            background: rgba(148, 163, 184, 0.08);
            border-color: rgba(148, 163, 184, 0.12);
        }

        /* Pagina attiva */
        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stPageLink"] a[aria-current="page"] {
            background:
                linear-gradient(
                    135deg,
                    rgba(34, 197, 94, 0.30),
                    rgba(59, 130, 246, 0.18)
                );

            border-color: rgba(34, 197, 94, 0.46);
            color: #ffffff !important;
            box-shadow: 0 12px 28px rgba(34, 197, 94, 0.10);
        }


        .block-container {
            max-width: 100%;
            padding-top: 0.75rem;
            padding-right: 1rem;
            padding-bottom: 1rem;
            padding-left: 0.6rem;
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(
                    circle at top left,
                    rgba(34, 197, 94, 0.12),
                    transparent 26%
                ),
                radial-gradient(
                    circle at top right,
                    rgba(59, 130, 246, 0.10),
                    transparent 28%
                ),
                linear-gradient(
                    135deg,
                    #020617 0%,
                    #0f172a 48%,
                    #111827 100%
                );
        }

        /* =====================================================
           TEXT
        ===================================================== */

        h1,
        h2,
        h3 {
            color: #f8fafc;
            font-weight: 900;
            letter-spacing: -0.03em;
        }

        p,
        label,
        span,
        div {
            color: #e5e7eb;
        }

        /* =====================================================
           CUSTOM NAVIGATION COLUMN
        ===================================================== */

        [data-testid="stColumn"]:has(.ft-navigation-anchor) {
            position: sticky;
            top: 0.75rem;
            align-self: flex-start;

            height: calc(100vh - 1.5rem);
            max-height: calc(100vh - 1.5rem);

            overflow-y: auto;
            overflow-x: hidden;
            overscroll-behavior: contain;

            animation: ft-navigation-enter 180ms ease-out;

            /* Nasconde visivamente la scrollbar */
            scrollbar-width: none;
            -ms-overflow-style: none;
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)::-webkit-scrollbar {
            display: none;
        }

        @keyframes ft-navigation-enter {
            from {
                opacity: 0;
                transform: translateX(-10px);
            }

            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stVerticalBlockBorderWrapper"] {
            min-height: 100%;
            padding: 0.75rem;

            border-radius: 24px;
            border: 1px solid rgba(148, 163, 184, 0.14);

            background:
                radial-gradient(
                    circle at top left,
                    rgba(34, 197, 94, 0.14),
                    transparent 28%
                ),
                linear-gradient(
                    180deg,
                    rgba(2, 6, 23, 0.96),
                    rgba(7, 17, 31, 0.94)
                );

            box-shadow: 0 22px 55px rgba(0, 0, 0, 0.24);
        }

        /* =====================================================
           NAVIGATION BUTTONS
        ===================================================== */

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        .stButton > button {
            min-height: 48px;
            justify-content: flex-start;
            padding-left: 16px;

            border-radius: 15px;
            text-align: left;
            font-size: 15px;
            font-weight: 800;

            transition:
                transform 140ms ease,
                background 140ms ease,
                border-color 140ms ease,
                box-shadow 140ms ease;
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        .stButton > button[kind="secondary"] {
            background: transparent !important;
            border: 1px solid transparent !important;
            color: #cbd5e1 !important;
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        .stButton > button[kind="secondary"]:hover {
            transform: translateX(3px);
            background: rgba(148, 163, 184, 0.08) !important;
            border-color: rgba(148, 163, 184, 0.12) !important;
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        .stButton > button[kind="primary"] {
            background:
                linear-gradient(
                    135deg,
                    rgba(34, 197, 94, 0.30),
                    rgba(59, 130, 246, 0.18)
                ) !important;

            border: 1px solid rgba(34, 197, 94, 0.46) !important;
            color: #ffffff !important;
            box-shadow: 0 12px 28px rgba(34, 197, 94, 0.10);
        }

        /* =====================================================
           HAMBURGER BUTTON
        ===================================================== */

        /*
        Interessa solamente il primo blocco di colonne presente
        nella navigazione, cioè quello del pulsante hamburger.
        */

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stHorizontalBlock"]:first-of-type
        .stButton {
            display: flex;
            justify-content: flex-end;
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stHorizontalBlock"]:first-of-type
        .stButton > button {
            width: 38px !important;
            min-width: 38px !important;
            height: 38px !important;
            min-height: 38px !important;

            padding: 0 !important;
            margin: 0 !important;

            display: flex !important;
            align-items: center !important;
            justify-content: center !important;

            background: transparent !important;
            border: none !important;
            box-shadow: none !important;

            color: #cbd5e1 !important;
            font-size: 24px !important;
            font-weight: 700 !important;
            line-height: 1 !important;

            transition:
                color 150ms ease,
                transform 150ms ease !important;
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stHorizontalBlock"]:first-of-type
        .stButton > button:hover {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;

            color: #22c55e !important;
            transform: scale(1.08);
        }

        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stHorizontalBlock"]:first-of-type
        .stButton > button:focus,
        [data-testid="stColumn"]:has(.ft-navigation-anchor)
        [data-testid="stHorizontalBlock"]:first-of-type
        .stButton > button:active {
            outline: none !important;
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }


        /* =====================================================
           CONTAINERS
        ===================================================== */

        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 22px;
            border-color: rgba(148, 163, 184, 0.16);
            background: rgba(15, 23, 42, 0.52);
        }

        /* =====================================================
           GLOBAL BUTTONS
        ===================================================== */

        .stButton > button {
            border-radius: 14px;
            font-weight: 800;
            border: 1px solid rgba(148, 163, 184, 0.18);
        }

        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: #ffffff;
            border: none;
        }

        .stButton > button[kind="secondary"] {
            background: transparent;
            color: #e5e7eb;
        }

        /* =====================================================
           INPUTS
        ===================================================== */

        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        .stTextArea textarea {
            border-radius: 12px;
        }

        div[data-baseweb="select"] {
            border-radius: 12px;
        }

        /* =====================================================
           FILE UPLOADER
        ===================================================== */

        div[data-testid="stFileUploader"] section {
            border-radius: 18px;
            border: 1px dashed rgba(148, 163, 184, 0.35);
            background: rgba(15, 23, 42, 0.55);
        }

        /* =====================================================
           EXPANDER
        ===================================================== */

        div[data-testid="stExpander"] {
            border-radius: 18px;
            border-color: rgba(148, 163, 184, 0.16);
            background: rgba(15, 23, 42, 0.35);
        }

        /* =====================================================
           GLOBAL SCROLLBAR
        ===================================================== */

        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-thumb {
            background: #334155;
            border-radius: 999px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #475569;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )