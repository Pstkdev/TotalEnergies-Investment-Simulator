import streamlit as st
import plotly.express as px

from src.tte_simulation import TTESimulation
from src.calibration import tte_vol_annual_last_20y

st.set_page_config(page_title="TotalEnergies Simulator", layout="wide")
st.title("TotalEnergies Investment Simulator (TTE)")

with st.expander("Model assumptions"):
    st.markdown(
        """
    - Price model: mean reversion toward a user-defined target + annual volatility
    - Dividends paid quarterly + optional reinvestment
    - No taxes, no fees, no spreads
    """
    )

# ---- Sidebar ----
st.sidebar.header("Parameters")

initial_share_price = st.sidebar.number_input(
    "Initial share price (€)",
    min_value=0.01,
    value=55.0,
    max_value=10000.0,
    step=1.0,
)

initial_shares = st.sidebar.number_input(
    "Initial number of shares",
    min_value=0,
    value=10,
    max_value=1000000,
    step=1,
)

monthly_investment = st.sidebar.number_input(
    "Monthly investment (€)",
    min_value=0.0,
    value=100.0,
    max_value=100000.0,
    step=100.0,
)

reinvest_dividends = st.sidebar.checkbox("Reinvest dividends", value=False)

st.sidebar.divider()
st.sidebar.subheader("Dividends")

initial_dividend = st.sidebar.number_input(
    "Initial dividend per share (€/year)",
    min_value=0.0,
    value=3.0,
    max_value=30.0,
    step=0.1,
)

dividend_growth_rate = st.sidebar.number_input(
    "Dividend growth rate (annual)",
    value=0.02,
    step=0.01,
    format="%.4f",
)

st.sidebar.divider()
st.sidebar.subheader("Simulation horizon")

years = st.sidebar.number_input("Years", min_value=1, value=20, max_value=115, step=1)
start_year = st.sidebar.number_input("Start year", min_value=2026, value=2026, step=1)

st.sidebar.divider()
st.sidebar.subheader("Price model")

long_run_price = st.sidebar.number_input(
    "Long-run price target (€)",
    min_value=0.01,
    value=50.0,
    max_value=500.0,
    step=1.0,
    help="Target price used by mean reversion (model assumption).",
)

reversion_speed = st.sidebar.number_input(
    "Mean reversion speed",
    min_value=0.0,
    value=0.20,
    step=0.05,
    format="%.3f",
    help="How strongly price is pulled toward the long-run target each year.",
)


colv1, colv2 = st.sidebar.columns([2, 1])

with colv1:
    vol_annual = st.number_input(
        "Annualised volatility",
        min_value=0.0,
        value=0.19,
        step=0.01,
        format="%.3f",
        help="Used in yearly price shocks. Example: 0.19 ≈ 19% annual volatility.",
    )

with colv2:
    if st.button("Auto", help="Estimate vol from last 20 years using historical data"):
        try:
            stats = tte_vol_annual_last_20y("TTE.PA")
            vol_annual = float(stats["vol_annual"])
            st.session_state["vol_annual_override"] = vol_annual
            st.success(f"Vol set to {vol_annual:.3f}")
        except Exception as e:
            st.error(f"Calibration failed: {e}")

if "vol_annual_override" in st.session_state:
    vol_annual = float(st.session_state["vol_annual_override"])

seed = st.sidebar.number_input(
    "Random seed",
    min_value=0,
    value=42,
    step=1,
    help="Same seed = same simulated price path.",
)

# ---- Run simulation ----
sim = TTESimulation(
    initial_share_price=float(initial_share_price),
    initial_shares=int(initial_shares),
    monthly_investment=float(monthly_investment),
    reinvest_dividends=bool(reinvest_dividends),
    initial_dividend=float(initial_dividend),
    dividend_growth_rate=float(dividend_growth_rate),
    years=int(years),
    start_year=int(start_year),
    long_run_price=float(long_run_price),
    reversion_speed=float(reversion_speed),
    vol_annual=float(vol_annual),
    seed=int(seed),
)

df = sim.run_simulation()

# ---- Summary ----
last = df.iloc[-1]
final_value = float(last["Portfolio value"])
final_shares = int(last["Total shares"])
total_invested = float(last["Total invested"])
total_div = float(last["Total dividends received"])
final_cash = float(last["Cash"])

total_return_pct = 0.0
if total_invested > 0:
    total_return_pct = (final_value - total_invested) / total_invested * 100.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Final portfolio value", f"€{final_value:,.2f}")
col1.metric("Final shares", f"{final_shares}")

col2.metric("Total invested", f"€{total_invested:,.2f}")
col2.metric("Total dividends received", f"€{total_div:,.2f}")

col3.metric("Final cash", f"€{final_cash:,.2f}")
col3.metric("Total return", f"{total_return_pct:.2f}%")

col4.metric("Vol (annual)", f"{vol_annual:.3f}")
col4.metric("Long-run target", f"€{long_run_price:,.2f}")

st.divider()

# ---- Charts ----
st.subheader("Charts")

fig_value = px.line(df, x="Calendar year", y="Portfolio value", title="Portfolio value over time")
fig_value.update_traces(line=dict(color="#DCBB37"))
st.plotly_chart(fig_value, use_container_width=True)

fig_price = px.line(df, x="Calendar year", y="Share price", title="Simulated share price over time")
st.plotly_chart(fig_price, use_container_width=True)

fig_shares = px.bar(df, x="Calendar year", y="Total shares", title="Total shares over time")
st.plotly_chart(fig_shares, use_container_width=True)

st.divider()

# ---- Table ----
st.subheader("Simulation results")
st.dataframe(df, use_container_width=True)
