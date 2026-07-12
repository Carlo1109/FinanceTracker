import pandas as pd
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go

from src.services.importer import get_category_icon
from src.services.movement_service import load_movements


def euro(value: float) -> str:
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")




def get_period_df(
    df: pd.DataFrame,
    period: str,
    selected_month: str | None = None,
) -> pd.DataFrame:
    today = pd.Timestamp.today()

    current_month = today.strftime("%Y-%m")
    previous_month = (today - pd.DateOffset(months=1)).strftime("%Y-%m")

    if period == "Mese specifico" and selected_month:
        return df[df["mese"] == selected_month].copy()

    if period == "Questo mese":
        return df[df["mese"] == current_month].copy()

    if period == "Mese scorso":
        return df[df["mese"] == previous_month].copy()

    if period == "Ultimi 3 mesi":
        start_month = (today - pd.DateOffset(months=2)).to_period("M")
        movement_months = pd.PeriodIndex(df["mese"], freq="M")

        return df[movement_months >= start_month].copy()

    if period == "Ultimi 6 mesi":
        start_month = (today - pd.DateOffset(months=5)).to_period("M")
        movement_months = pd.PeriodIndex(df["mese"], freq="M")

        return df[movement_months >= start_month].copy()

    if period == "Quest'anno":
        return df[df["mese"].str.startswith(str(today.year), na=False)].copy()

    return df.copy()


def show_dashboard() -> None:
    st.title("🏠 Dashboard")
    st.caption("Panoramica generale delle tue finanze.")

    df = load_movements()

    if df.empty:
        st.info("Importa un file Fineco o aggiungi un movimento manuale per visualizzare la dashboard.")
        return

    months = sorted(df["mese"].dropna().unique(), reverse=True)
    accounts = sorted(df["account"].dropna().unique().tolist())

    f1, f2, f3 = st.columns([1.4, 1.4, 1.4])

    with f1:
        period = st.selectbox(
            "Periodo",
            ["Questo mese", "Mese scorso", "Mese specifico", "Ultimi 3 mesi", "Ultimi 6 mesi", "Quest'anno", "Tutto"],
            index=6,
        )

    selected_month = None
    with f2:
        if period == "Mese specifico":
            selected_month = st.selectbox("Mese", months)
        else:
            st.selectbox("Mese", ["Automatico"], disabled=True)

    with f3:
        selected_account = st.selectbox("Conto", ["Tutti"] + accounts)

    filtered_df = get_period_df(df, period, selected_month)

    if selected_account != "Tutti":
        filtered_df = filtered_df[filtered_df["account"] == selected_account]

    if filtered_df.empty:
        st.warning("Nessun movimento trovato per i filtri selezionati.")
        return

    entrate = filtered_df[filtered_df["importo"] > 0]["importo"].sum()
    uscite = abs(filtered_df[filtered_df["importo"] < 0]["importo"].sum())
    bilancio = entrate - uscite
    investimenti = abs(
        filtered_df[
            (filtered_df["categoria"] == "Investimenti")
            & (filtered_df["importo"] < 0)
        ]["importo"].sum()
    )

    expense_df = filtered_df[
        (filtered_df["importo"] < 0)
        & (filtered_df["categoria"] != "Investimenti")
    ].copy()

    avg_daily_expense = 0
    if not filtered_df["data"].dropna().empty:
        days = max((filtered_df["data"].max() - filtered_df["data"].min()).days + 1, 1)
        avg_daily_expense = uscite / days

    top_category = "Nessuna"
    top_category_amount = 0
    if not expense_df.empty:
        top_row = (
            expense_df.groupby("categoria")["importo"]
            .sum()
            .abs()
            .sort_values(ascending=False)
            .head(1)
        )
        top_category = top_row.index[0]
        top_category_amount = top_row.iloc[0]

    balance_color = "#22c55e" if bilancio >= 0 else "#ef4444"
    balance_sign = "+" if bilancio >= 0 else ""

    st.markdown(
        f"""
        <div style="
            margin-top: 20px;
            padding: 34px;
            border-radius: 28px;
            background:
                radial-gradient(circle at top left, rgba(34, 197, 94, 0.18), transparent 28%),
                rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(148, 163, 184, 0.18);
            box-shadow: 0 24px 60px rgba(0, 0, 0, 0.28);
            text-align: center;
        ">
            <div style="font-size: 14px; color: #94a3b8; font-weight: 700; letter-spacing: 1px;">
                BILANCIO DEL PERIODO
            </div>
            <div style="font-size: 54px; font-weight: 950; color: {balance_color}; margin-top: 12px;">
                {balance_sign}{euro(bilancio)}
            </div>
            <div style="font-size: 15px; color: #cbd5e1; margin-top: 10px;">
                Entrate {euro(entrate)} · Uscite {euro(uscite)} · Investimenti {euro(investimenti)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    k1, k2, k3 = st.columns(3)

    with k1:
        st.metric("Categoria principale", f"{get_category_icon(top_category)} {top_category}", euro(top_category_amount))

    with k2:
        st.metric("Spesa media giornaliera", euro(avg_daily_expense))

    with k3:
        st.metric("Movimenti", len(filtered_df))

    left_col, right_col = st.columns([1.4, 1])

    with left_col:
        st.markdown("### 📊 Dove sono andati i soldi?")

        category_df = (
            expense_df.groupby("categoria", as_index=False)["importo"]
            .sum()
            .assign(importo=lambda x: x["importo"].abs())
            .sort_values("importo", ascending=False)
        )

        if category_df.empty:
            st.info("Nessuna uscita da mostrare per questo periodo.")
        else:
            category_df["label"] = category_df["categoria"].apply(
                lambda c: f"{get_category_icon(c)} {c}"
            )

            total_expenses = category_df["importo"].sum()

            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=category_df["label"],
                        values=category_df["importo"],
                        hole=0.68,
                        sort=False,
                        direction="clockwise",
                        textinfo="none",
                        hovertemplate="<b>%{label}</b><br>%{value:.2f} €<br>%{percent}<extra></extra>",
                        marker=dict(
                            colors=[
                                "#22c55e",
                                "#3b82f6",
                                "#f59e0b",
                                "#8b5cf6",
                                "#ef4444",
                                "#14b8a6",
                                "#94a3b8",
                                "#ec4899",
                            ],
                            line=dict(color="rgba(15, 23, 42, 0.95)", width=3),
                        ),
                    )
                ]
            )

            fig.update_layout(
                height=390,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e5e7eb",
                showlegend=False,
                annotations=[
                    dict(
                        text=f"<b>{euro(total_expenses)}</b><br><span style='font-size:12px;color:#94a3b8'>Totale uscite</span>",
                        x=0.5,
                        y=0.5,
                        font=dict(size=18, color="#f8fafc"),
                        showarrow=False,
                    )
                ],
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False},
            )

            for _, item in category_df.iterrows():
                percentage = (item["importo"] / total_expenses) * 100

                st.markdown(
                    f"""
                    <div style="
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                        padding:8px 0;
                        border-bottom:1px solid rgba(148,163,184,0.10);
                    ">
                        <div style="font-weight:700;">
                            {get_category_icon(item["categoria"])} {item["categoria"]}
                        </div>
                        <div style="color:#94a3b8;">
                            {euro(item["importo"])} · {percentage:.1f}%
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with right_col:
        st.markdown("### 🕒 Ultimi movimenti")

        latest = filtered_df.sort_values("data", ascending=False).head(6)

        for _, row in latest.iterrows():
            amount = float(row["importo"])
            color = "#22c55e" if amount > 0 else "#ef4444"
            sign = "+" if amount > 0 else ""

            category = row["categoria"]
            icon = get_category_icon(category)

            title = row["descrizione_completa"] or row["descrizione"]
            date = row["data"].strftime("%d/%m/%Y") if pd.notna(row["data"]) else ""

            with st.container(border=True):
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: space-between; gap: 12px;">
                        <div>
                            <div style="font-size: 15px; font-weight: 800; color: #f8fafc;">
                                {icon} {title}
                            </div>
                            <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">
                                {category} · {date}
                            </div>
                        </div>
                        <div style="font-size: 16px; font-weight: 900; color: {color}; white-space: nowrap;">
                            {sign}{euro(amount)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("### 📈 Andamento mensile")

    trend_df = df.copy()

    if selected_account != "Tutti":
        trend_df = trend_df[trend_df["account"] == selected_account]

    monthly_df = (
        trend_df.assign(
            entrate=lambda x: x["importo"].where(x["importo"] > 0, 0),
            uscite=lambda x: x["importo"].where(x["importo"] < 0, 0).abs(),
        )
        .groupby("mese", as_index=False)[["entrate", "uscite"]]
        .sum()
        .sort_values("mese")
    )

    fig2 = px.line(
        monthly_df,
        x="mese",
        y=["entrate", "uscite"],
        markers=True,
    )

    fig2.update_layout(
        height=390,
        margin=dict(l=10, r=20, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e5e7eb",
        legend_title_text="",
        xaxis_title="",
        yaxis_title="€",
    )

    st.plotly_chart(fig2, use_container_width=True)