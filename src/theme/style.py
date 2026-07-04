import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .main {
            background: #0f172a;
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at top left, rgba(56, 189, 248, 0.18), transparent 30%),
                linear-gradient(135deg, #020617 0%, #0f172a 45%, #111827 100%);
        }

        [data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.95);
            border-right: 1px solid rgba(148, 163, 184, 0.2);
        }

        h1, h2, h3 {
            color: #f8fafc;
        }

        p, label, span, div {
            color: #e5e7eb;
        }

        .metric-card {
            padding: 22px;
            border-radius: 22px;
            background: rgba(15, 23, 42, 0.82);
            border: 1px solid rgba(148, 163, 184, 0.22);
            box-shadow: 0 20px 45px rgba(0, 0, 0, 0.25);
        }

        .metric-label {
            font-size: 14px;
            color: #94a3b8;
            margin-bottom: 8px;
        }

        .metric-value {
            font-size: 30px;
            font-weight: 800;
            color: #f8fafc;
        }

        .metric-positive {
            color: #22c55e;
        }

        .metric-negative {
            color: #ef4444;
        }

        .section-card {
            padding: 24px;
            border-radius: 24px;
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.18);
            margin-top: 18px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, tone: str = "neutral") -> None:
    tone_class = ""
    if tone == "positive":
        tone_class = "metric-positive"
    elif tone == "negative":
        tone_class = "metric-negative"

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value {tone_class}">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )