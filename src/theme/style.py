import streamlit as st


def apply_theme():
    st.markdown(
        """
<style>

/* =========================================================
   STREAMLIT UI
========================================================= */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header[data-testid="stHeader"]{
    display:none;
}

[data-testid="stToolbar"]{
    display:none;
}

/* =========================================================
   APP BACKGROUND
========================================================= */

[data-testid="stAppViewContainer"]{
    background:
        radial-gradient(circle at top left,
            rgba(34,197,94,.12),
            transparent 26%),
        radial-gradient(circle at top right,
            rgba(59,130,246,.10),
            transparent 28%),
        linear-gradient(
            135deg,
            #020617 0%,
            #0f172a 45%,
            #111827 100%);
}

/* =========================================================
   SIDEBAR
========================================================= */

[data-testid="stSidebar"]{

    background:
        radial-gradient(circle at top left,
            rgba(34,197,94,.14),
            transparent 28%),
        linear-gradient(
            180deg,
            #020617 0%,
            #07111f 50%,
            #020617 100%);

    border-right:1px solid rgba(148,163,184,.12);
}

[data-testid="stSidebarContent"]{
    background:transparent !important;
}

/* =========================================================
   HEADINGS
========================================================= */

h1{

    color:#f8fafc;

    font-weight:900;

    letter-spacing:-.04em;
}

h2,h3{

    color:#f8fafc;

    font-weight:800;

}

p,
label,
span,
div{

    color:#e5e7eb;

}

/* =========================================================
   METRICS
========================================================= */

[data-testid="stMetric"]{

    padding:18px;

    border-radius:22px;

    background:rgba(15,23,42,.72);

    border:1px solid rgba(148,163,184,.14);

    box-shadow:0 18px 40px rgba(0,0,0,.18);

}

[data-testid="stMetricLabel"]{

    color:#94a3b8;

    font-weight:700;

}

[data-testid="stMetricValue"]{

    color:#f8fafc;

    font-weight:900;

}

/* =========================================================
   CONTAINERS
========================================================= */

[data-testid="stVerticalBlockBorderWrapper"]{

    background:rgba(15,23,42,.55);

    border:1px solid rgba(148,163,184,.14);

    border-radius:22px;

}

/* =========================================================
   BUTTONS
========================================================= */

.stButton button{

    border-radius:14px;

    font-weight:700;

}

.stButton button[kind="primary"]{

    background:linear-gradient(
        135deg,
        #22c55e,
        #16a34a);

    border:none;

    color:white;

}

.stButton button[kind="secondary"]{

    background:transparent;

    border:1px solid rgba(148,163,184,.16);

    color:#e5e7eb;

}

/* =========================================================
   INPUTS
========================================================= */

.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stTextArea textarea{

    border-radius:12px;

}

div[data-baseweb="select"]{

    border-radius:12px;

}

/* =========================================================
   FILE UPLOADER
========================================================= */

div[data-testid="stFileUploader"] section{

    border-radius:18px;

    border:1px dashed rgba(148,163,184,.35);

    background:rgba(15,23,42,.55);

}

/* =========================================================
   EXPANDER
========================================================= */

div[data-testid="stExpander"]{

    border-radius:18px;

    background:rgba(15,23,42,.35);

}

/* =========================================================
   SCROLLBAR
========================================================= */

::-webkit-scrollbar{

    width:8px;

}

::-webkit-scrollbar-thumb{

    background:#334155;

    border-radius:999px;

}

::-webkit-scrollbar-thumb:hover{

    background:#475569;

}

</style>
""",
        unsafe_allow_html=True,
    )