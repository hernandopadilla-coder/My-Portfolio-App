Here is the complete app.py script containing your multi-account stock and ETF portfolio tracker along with interactive Plotly asset allocation charts.
Copy the entire code block below and paste it into app.py on GitHub:
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import os

# File to store user portfolio locally in cloud session
DATA_FILE = "portfolio.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Account", "Ticker", "Shares", "Avg Price"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def get_live_prices(tickers):
    if not tickers:
        return {}
    data = yf.Tickers(" ".join(tickers))
    prices = {}
    for ticker in tickers:
        try:
            # Fetch fast current market price
            price = data.tickers[ticker].fast_info['lastPrice']
            prices[ticker] = price
        except Exception:
            prices[ticker] = 0.0
    return prices

# Page Configuration
st.set_page_config(page_title="Investment Portfolio Tracker", layout="wide")
st.title("📈 Investment Portfolio Dashboard")

# Load portfolio positions
df_portfolio = load_data()

# Sidebar Form: Add New Holdings
st.sidebar.header("Add New Position")
with st.sidebar.form("add_position_form", clear_on_submit=True):
    account = st.selectbox("Account Type", ["Taxable Brokerage", "Traditional IRA", "Roth IRA"])
    ticker = st.text_input("Ticker Symbol (e.g. AAPL, VTI, SPY)").upper().strip()
    shares = st.number_input("Number of Shares", min_value=0.0001, step=1.0, format="%.4f")
    avg_price = st.number_input("Average Purchase Price ($)", min_value=0.01, step=1.0, format="%.2f")
    
    submitted = st.form_submit_button("Add to Portfolio")
    if submitted and ticker:
        new_row = pd.DataFrame([{"Account": account, "Ticker": ticker, "Shares": shares, "Avg Price": avg_price}])
        df_portfolio = pd.concat([df_portfolio, new_row], ignore_index=True)
        save_data(df_portfolio)
        st.sidebar.success(f"Added {ticker} to {account}!")

# Main Dashboard Engine
if not df_portfolio.empty:
    # Fetch live price updates
    unique_tickers = df_portfolio["Ticker"].unique().tolist()
    live_prices = get_live_prices(unique_tickers)
    
    df_portfolio["Current Price"] = df_portfolio["Ticker"].map(live_prices)
    df_portfolio["Cost Basis"] = df_portfolio["Shares"] * df_portfolio["Avg Price"]
    df_portfolio["Market Value"] = df_portfolio["Shares"] * df_portfolio["Current Price"]
    df_portfolio["Unrealized Gain/Loss"] = df_portfolio["Market Value"] - df_portfolio["Cost Basis"]
    df_portfolio["Return (%)"] = (df_portfolio["Unrealized Gain/Loss"] / df_portfolio["Cost Basis"]) * 100

    # Key Summary Metrics
    total_val = df_portfolio["Market Value"].sum()
    total_cost = df_portfolio["Cost Basis"].sum()
    total_gain = df_portfolio["Unrealized Gain/Loss"].sum()
    total_return = (total_gain / total_cost * 100) if total_cost > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Portfolio Value", f"${total_val:,.2f}")
    col2.metric("Total Invested", f"${total_cost:,.2f}")
    col3.metric("Total Profit / Loss", f"${total_gain:,.2f}", delta=f"{total_return:.2f}%")
    col4.metric("Active Holdings", len(df_portfolio))

    st.markdown("---")

    # Plotly Visualizations
    st.subheader("Asset Allocation")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig_account = px.pie(
            df_portfolio, 
            values="Market Value", 
            names="Account", 
            title="Allocation by Account Type",
            hole=0.4
        )
        st.plotly_chart(fig_account, use_container_width=True)

    with chart_col2:
        fig_ticker = px.pie(
            df_portfolio, 
            values="Market Value", 
            names="Ticker", 
            title="Allocation by Holding",
            hole=0.4
        )
        st.plotly_chart(fig_ticker, use_container_width=True)

    st.markdown("---")

    # Detailed Holdings Table & Filters
    st.subheader("Holdings Detail")
    selected_account = st.selectbox("Filter Account", ["All Accounts"] + list(df_portfolio["Account"].unique()))
    
    view_df = df_portfolio if selected_account == "All Accounts" else df_portfolio[df_portfolio["Account"] == selected_account]
    
    st.dataframe(
        view_df.style.format({
            "Shares": "{:,.2f}",
            "Avg Price": "${:,.2f}",
            "Current Price": "${:,.2f}",
            "Cost Basis": "${:,.2f}",
            "Market Value": "${:,.2f}",
            "Unrealized Gain/Loss": "${:,.2f}",
            "Return (%)": "{:,.2f}%"
        }),
        use_container_width=True
    )

    # Clear Data Action
    if st.button("Clear All Data"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            st.rerun()

else:
    st.info("No positions added yet. Use the sidebar on the left to add your stock or ETF holdings.")

