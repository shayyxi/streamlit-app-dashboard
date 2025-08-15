import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- Page config ----------------
st.set_page_config(page_title="Property Dashboard", page_icon="🏢", layout="wide")

# ---------------- KPI styling ----------------

# Plotly chart card style — only paste this ONCE
st.markdown("""
<style>
div[data-testid="stPlotlyChart"] {
  background: #f6faf9;
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 14px;
  padding: 12px 12px 6px;
  box-shadow: 0 2px 12px rgba(0,0,0,.05);
}
@media (max-width: 640px) {
  div[data-testid="stPlotlyChart"] { padding: 10px 10px 4px; }
}
</style>
""", unsafe_allow_html=True)

# --- 1) Paste this once near the top (after set_page_config) ---
st.markdown("""
<style>
.kpi-grid { margin: .25rem 0 1rem; }
.kpi-card {
  background: #dfeeea;               /* soft green */
  border-radius: 14px;
  padding: 14px 18px;
  box-shadow: 0 2px 14px rgba(0,0,0,.05);
  border: 1px solid rgba(0,0,0,.06);
}
.kpi-label { font-size: 0.95rem; color: #4b5563; }
.kpi-value { font-size: 2rem; font-weight: 700; line-height: 1.1; }
</style>
""", unsafe_allow_html=True)

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

def _cardify(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=40, b=10),  # slightly more top margin for legend
        legend=dict(
            orientation="h",  # horizontal legend
            yanchor="bottom",  # anchor to bottom of legend box
            y=1.02,  # a bit above the plot
            xanchor="center",
            x=0.5,  # centered
            bgcolor="rgba(255,255,255,0.8)",  # light background for readability
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1
        )
    )
    return fig

# ---------------- Helpers ----------------
def k(value, currency=False):
    if pd.isna(value):
        return "—"
    if currency:
        return f"${value/1000:,.2f} K"
    return f"{value:,.0f}"

def pct(value):
    return f"{value:,.2f} %"

@st.cache_data
def sample_df():
    # 12 weekly snapshots (similar to your screenshots)
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
        # Ops metrics (latest value used for KPIs, bars show latest snapshots)
        "new_leads":           [78,92,110,45,128,59,160,55,188,70,140,104],
        "applications_started":[12,14,10,8,32,9,40,11,25,7,22,15],
        "approved_applications":[4,6,5,3,9,4,10,5,8,4,7,3],
        "open_work_orders":    [9]*12,
        "completed_work_orders":[18]*12,
    })
    return df

# ---------------- Data input ----------------
df = sample_df()

# Ensure date is datetime
if not pd.api.types.is_datetime64_any_dtype(df["date"]):
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

df = df.sort_values("date")
latest = df.iloc[-1]

# ---------------- Tabs ----------------
# ---- Segmented full-width tabs (drop-in CSS) ----
ACCENT = "#0f988f"  # teal accent; tweak if you like

st.markdown(f"""
<style>
/* Outer bar */
div[data-baseweb="tab-list"] {{
  width: 100%;
  max-width: 900px;                /* keep it elegant on widescreens */
  margin: 0.75rem auto 0.75rem;    /* center the bar */
  padding: 6px;                    /* space around pills */
  background: #eaf2f1;             /* soft track color */
  border-radius: 14px;             /* rounded bar */
  box-shadow: 0 2px 16px rgba(0,0,0,.06);
  display: flex;
  gap: 6px;
}}

/* Each tab behaves like a segmented button */
button[data-baseweb="tab"] {{
  flex: 1 1 0;                     /* equal widths */
  justify-content: center;
  border-radius: 10px;             /* rounded pills */
  background: transparent;
  color: #0b2b2b;
  font-weight: 700;
  font-size: 1.02rem;
  padding: .7rem 1.2rem;
  border: 2px solid transparent;   /* keeps height stable on active */
  transition: all .15s ease-in-out;
  outline: none !important;
}}

button[data-baseweb="tab"]:hover {{
  background: rgba(15,152,143,.08);
}}

button[data-baseweb="tab"][aria-selected="true"] {{
  background: {ACCENT};
  color: #fff;
  border-color: {ACCENT};
  box-shadow: 0 1px 6px rgba(15,152,143,.35);
}}

/* Remove the little underline BaseWeb adds on focus */
button[data-baseweb="tab"] > div:first-child {{
  border-bottom: none !important;
}}

/* Mobile: let the bar fill the screen edge-to-edge */
@media (max-width: 640px) {{
  div[data-baseweb="tab-list"] {{
    max-width: 100%;
    border-radius: 0;
  }}
}}
</style>
""", unsafe_allow_html=True)

tab_overview, tab_operations = st.tabs(["Overview", "Operations"])

# ======== OVERVIEW TAB ========
with tab_overview:
    st.markdown('<div class="kpi-grid"></div>', unsafe_allow_html=True)  # small top spacing

    a, b, c, d, e, f, g = st.columns(7)
    with a: kpi_card("Total Units", k(latest.get("total_units", None)))
    with b: kpi_card("Occupied Units", k(latest.get("occupied_units", None)))
    with c: kpi_card("Percentage Occupied", pct(latest.get("percentage_occupied", 0)))
    with d: kpi_card("Pre-leased Units", k(latest.get("pre_leased_units", None)))
    with e: kpi_card("Rent Billed", k(latest.get("rent_billed", None), currency=True))
    with f: kpi_card("Rent Collected", k(latest.get("rent_collections", None), currency=True))
    with g: kpi_card("Pct Rent Collected", pct(latest.get("percentage_rent_collected", 0)))

    st.write("")

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
        fig1.update_layout(margin=dict(l=0,r=0,b=0,t=10), legend=dict(orientation="v"))
        st.plotly_chart(_cardify(fig1), use_container_width=True, key="rent billed")

    with right:
        st.subheader("Occupancy % over time")
        fig2 = px.bar(
            df,
            x="date",
            y="percentage_occupied",
            labels={"percentage_occupied":"Pct Occupied","date":"Date"},
        )
        fig2.update_layout(margin=dict(l=0,r=0,b=0,t=10))
        st.plotly_chart(_cardify(fig2), use_container_width=True, key="occupancy")

    st.write("---")
    st.subheader("Recent data snapshot")
    st.dataframe(df.sort_values("date", ascending=False).reset_index(drop=True), use_container_width=True, key="recent_data")

# ======== OPERATIONS TAB ========
with tab_operations:
    st.markdown('<div class="kpi-grid"></div>', unsafe_allow_html=True)
    a,b,c,d,e = st.columns(5)
    with a: kpi_card("Open Work Orders", k(latest.get("open_work_orders", None)))
    with b: kpi_card("Completed Work Orders (last snap)", k(latest.get("completed_work_orders", None)))
    with c: kpi_card("New Leads", k(latest.get("new_leads", None)))
    with d: kpi_card("Applications Started", k(latest.get("applications_started", None)))
    with e: kpi_card("Approved Applications", k(latest.get("approved_applications", None)))

    st.write("")

    left, right = st.columns(2)

    with left:
        st.subheader("Leads -> Applications -> Approvals (latest snapshots)")
        # Stacked bar across the last N rows (use all rows present)
        stack_cols = ["new_leads","applications_started","approved_applications"]
        long_ops = df[["date"] + stack_cols].melt(id_vars="date", var_name="variable", value_name="value")
        fig3 = px.bar(
            long_ops,
            x="date",
            y="value",
            color="variable",
            barmode="stack",
            labels={"date":"date","value":"value","variable":"variable"},
        )
        fig3.update_layout(margin=dict(l=0,r=0,b=0,t=10))
        st.plotly_chart(_cardify(fig3), use_container_width=True, key="leads")

    with right:
        st.subheader("Occupancy % over time")
        fig4 = px.bar(
            df,
            x="date",
            y="percentage_occupied",
            labels={"percentage_occupied":"Pct Occupied","date":"Date"},
        )
        fig4.update_layout(margin=dict(l=0,r=0,b=0,t=10))
        st.plotly_chart(_cardify(fig4), use_container_width=True, key="occupancy pct")

    st.write("---")
    st.subheader("Recent data snapshot")
    st.dataframe(df.sort_values("date", ascending=False).reset_index(drop=True), use_container_width=True, key="recent_data snp")

# ---------------- Notes ----------------
with st.expander("Notes / expected columns"):
    st.markdown(
        """
- Required columns for the Overview tab:
  `date, total_units, occupied_units, pre_leased_units, percentage_occupied,
  rent_billed, rent_collections, percentage_rent_collected`
- For the Operations tab (optional but recommended):
  `new_leads, applications_started, approved_applications, open_work_orders, completed_work_orders`
- Upload a CSV in the sidebar to drive the app with real data; any missing columns will simply show as blanks.
        """
    )
