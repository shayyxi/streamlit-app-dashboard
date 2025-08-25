import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# GLOBALS
# =========================
ACCENT = "#0f988f"  # brand teal


# =========================
# PAGE SETUP & STYLES
# =========================
def setup_page():
    st.set_page_config(page_title="Property Dashboard", page_icon="🏢", layout="wide")

def inject_css():
    st.markdown(f"""
    <style>
    /* Remove default top padding */
    .main > div:first-child {{ padding-top: 0rem; }}
    .block-container {{ padding-top: 1rem; }}

    /* KPI cards */
    .kpi-grid {{ margin: .25rem 0 1rem; }}
    .kpi-card {{
      background: #dfeeea;               /* soft green */
      border-radius: 14px;
      padding: 14px 18px;
      box-shadow: 0 2px 14px rgba(0,0,0,.05);
      border: 1px solid rgba(0,0,0,.06);
    }}
    .kpi-label {{ font-size: 0.95rem; color: #4b5563; }}
    .kpi-value {{ font-size: 2rem; font-weight: 700; line-height: 1.1; }}

    /* Plotly chart "card" container */
    div[data-testid="stPlotlyChart"] {{
      background: #f6faf9;
      border: 1px solid rgba(0,0,0,.08);
      border-radius: 14px;
      padding: 12px 12px 6px;
      box-shadow: 0 2px 12px rgba(0,0,0,.05);
    }}
    @media (max-width: 640px) {{
      div[data-testid="stPlotlyChart"] {{ padding: 10px 10px 4px; }}
    }}

    /* Segmented, centered tabs */
    div[data-baseweb="tab-list"] {{
      width: 100%;
      max-width: 900px;                  /* elegant width on large screens */
      margin: 0rem auto 0.75rem;         /* minimal gap above */
      padding: 6px;                      /* track padding */
      background: #eaf2f1;               /* soft track color */
      border-radius: 14px;
      box-shadow: 0 2px 16px rgba(0,0,0,.06);
      display: flex;
      gap: 6px;
    }}
    button[data-baseweb="tab"] {{
      flex: 1 1 0;                       /* equal width pills */
      justify-content: center;
      border-radius: 10px;
      background: transparent;
      color: #0b2b2b;
      font-weight: 700;
      font-size: 1.02rem;
      padding: .7rem 1.2rem;
      border: 2px solid transparent;     /* stable height when active */
      transition: all .15s ease-in-out;
      outline: none !important;
    }}
    button[data-baseweb="tab"]:hover {{ background: rgba(15,152,143,.08); }}
    button[data-baseweb="tab"][aria-selected="true"] {{
      background: {ACCENT};
      color: #fff;
      border-color: {ACCENT};
      box-shadow: 0 1px 6px rgba(15,152,143,.35);
    }}
    button[data-baseweb="tab"] > div:first-child {{ border-bottom: none !important; }}

    /* Mobile */
    @media (max-width: 640px) {{
      div[data-baseweb="tab-list"] {{ max-width: 100%; border-radius: 0; }}
    }}
    </style>
    """, unsafe_allow_html=True)


# =========================
# HELPERS
# =========================
def k(value, currency=False):
    if pd.isna(value):
        return "—"
    return f"${value/1000:,.2f} K" if currency else f"{value:,.0f}"

def pct(value):
    return f"{value:,.2f} %"

def kpi_card(label: str, value: str):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def cardify(fig):
    """Make Plotly figs blend with the CSS card + keep legend inside."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="center", x=0.5,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.1)", borderwidth=1
        )
    )
    return fig


# =========================
# DATA
# =========================
@st.cache_data
def sample_df():
    df = pd.DataFrame({
        "date": pd.date_range("2025-06-01", periods=12, freq="W"),
        "total_units": [232]*12,
        "total_rentable_units": [231]*12,
        "excluded_downed_units": [1]*12,
        "pre_leased_units": [222,220,222,217,216,215,221,217,222,220,222,222],
        "occupied_units":      [215,210,212,217,216,215,221,217,222,220,215,215],
        "percentage_occupied": [90.40,88.01,88.82,89.99,88.91,89.22,89.92,89.30,89.92,88.82,90.00,90.40],
        "percentage_leased":   [97.09,97.21,97.54,97.10,97.52,96.84,97.72,96.84,97.18,96.74,97.20,97.09],
        "rent_billed":         [248130,240876,259190,241060,243987,249208,244931,249474,257868,242027,248130,246900],
        "rent_collections":    [246035,244563,259469,231295,245573,239313,245253,242280,260643,232163,246035,246040],
        "percentage_rent_collected":[99.16,101.53,100.11,95.95,100.65,96.03,100.13,97.12,101.08,95.92,99.16,99.16],
        "new_leads":           [78,92,110,45,128,59,160,55,188,70,140,104],
        "applications_started":[12,14,10,8,32,9,40,11,25,7,22,15],
        "approved_applications":[4,6,5,3,9,4,10,5,8,4,7,3],
        "open_work_orders":    [9]*12,
        "completed_work_orders":[18]*12,
    })
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.sort_values("date").reset_index(drop=True)


# =========================
# TABS
# =========================
def render_overview_tab(df: pd.DataFrame):
    latest = df.iloc[-1]
    st.markdown('<div class="kpi-grid"></div>', unsafe_allow_html=True)
    a, b, c, d, e, f, g = st.columns(7, gap="large")
    with a: kpi_card("Total Units", k(latest.get("total_units")))
    with b: kpi_card("Occupied Units", k(latest.get("occupied_units")))
    with c: kpi_card("Percentage Occupied", pct(latest.get("percentage_occupied", 0)))
    with d: kpi_card("Pre-leased Units", k(latest.get("pre_leased_units")))
    with e: kpi_card("Rent Billed", k(latest.get("rent_billed"), currency=True))
    with f: kpi_card("Rent Collected", k(latest.get("rent_collections"), currency=True))
    with g: kpi_card("Pct Rent Collected", pct(latest.get("percentage_rent_collected", 0)))

    left, right = st.columns(2)
    with left:
        st.subheader("Rent billed vs collected over time")
        fig1 = px.line(
            df,
            x="date",
            y=["rent_billed","rent_collections"],
            labels={"value":"Amount","date":"Date","variable":""},
        )
        fig1.update_traces(mode="lines+markers")
        st.plotly_chart(cardify(fig1), use_container_width=True, key="chart_rent_overview")

    with right:
        st.subheader("Occupancy % over time")
        fig2 = px.bar(
            df, x="date", y="percentage_occupied",
            labels={"percentage_occupied":"Pct Occupied","date":"Date"},
        )
        st.plotly_chart(cardify(fig2), use_container_width=True, key="chart_occupancy_overview")

    st.write("---")
    st.subheader("Recent data snapshot")
    st.dataframe(
        df.sort_values("date", ascending=False).reset_index(drop=True),
        use_container_width=True, hide_index=True, key="table_overview"
    )

def render_operations_tab(df: pd.DataFrame):
    latest = df.iloc[-1]
    st.markdown('<div class="kpi-grid"></div>', unsafe_allow_html=True)
    a, b, c, d, e = st.columns(5, gap="large")
    with a: kpi_card("Open Work Orders", k(latest.get("open_work_orders")))
    with b: kpi_card("Completed Work Orders (last snap)", k(latest.get("completed_work_orders")))
    with c: kpi_card("New Leads", k(latest.get("new_leads")))
    with d: kpi_card("Applications Started", k(latest.get("applications_started")))
    with e: kpi_card("Approved Applications", k(latest.get("approved_applications")))

    left, right = st.columns(2)
    with left:
        st.subheader("Leads → Applications → Approvals (latest snapshots)")
        stack_cols = ["new_leads","applications_started","approved_applications"]
        long_ops = df[["date"] + stack_cols].melt(id_vars="date", var_name="variable", value_name="value")
        fig3 = px.bar(
            long_ops, x="date", y="value", color="variable",
            barmode="stack", labels={"date":"date","value":"value","variable":"variable"},
        )
        st.plotly_chart(cardify(fig3), use_container_width=True, key="chart_funnel_ops")

    with right:
        st.subheader("Occupancy % over time")
        fig4 = px.bar(
            df, x="date", y="percentage_occupied",
            labels={"percentage_occupied":"Pct Occupied","date":"Date"},
        )
        st.plotly_chart(cardify(fig4), use_container_width=True, key="chart_occupancy_ops")

    st.write("---")
    st.subheader("Recent data snapshot")
    st.dataframe(
        df.sort_values("date", ascending=False).reset_index(drop=True),
        use_container_width=True, hide_index=True, key="table_ops"
    )


# =========================
# ENTRY POINT
# =========================
def main():
    setup_page()
    inject_css()

    # Data
    df = sample_df()

    # Title (optional)
    st.title("🏢 Property Dashboard")

    # Tabs
    tab_overview, tab_operations = st.tabs(["Overview", "Operations"])
    with tab_overview:
        render_overview_tab(df)
    with tab_operations:
        render_operations_tab(df)

if __name__ == "__main__":
    main()
