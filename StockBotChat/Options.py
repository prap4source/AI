import streamlit as st
import alpaca_trade_api as tradeapi
import os
import pandas as pd
from dotenv import load_dotenv
import requests

load_dotenv()

# --- Watchlist Management ---
def initialize_watchlist(st):
    """Initialize the stock watchlist in session state."""
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []

def add_to_watchlist(stock, st):
    """Add a stock to the watchlist."""
    stock = stock.upper()
    if stock not in st.session_state.watchlist:
        st.session_state.watchlist.append(stock)

def remove_from_watchlist(stock, st):
    """Remove a stock from the watchlist."""
    if stock in st.session_state.watchlist:
        st.session_state.watchlist.remove(stock)

def get_options_chain_polygon(ticker, st):
    api_key = os.getenv("POLYGON_API_KEY") #Replace with your api key.
    url = f"https://api.polygon.io/v3/reference/options/contracts?underlying_ticker={ticker}&apiKey={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if results:
            return pd.DataFrame(results)
        else:
            return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching options data: {e}")
        return pd.DataFrame()
# --- Show Options UI ---
def show_options(st):
    """Displays the options watchlist and options chain data."""
    st.title("📈 Stock Options Watchlist and Chain")

    initialize_watchlist(st)

    # --- Watchlist Input ---
    st.subheader("📌 Manage Your Watchlist")
    stock_input = st.text_input("Enter a stock ticker (e.g., AAPL, TSLA, MSFT)", key="stock_input")
    col1, col2 = st.columns([0.3, 0.7])
    with col1:
        if st.button("➕ Add to Watchlist", key="add_stock"):
            add_to_watchlist(stock_input, st)
    with col2:
        if st.button("🔄 Refresh Watchlist", key="refresh"):
            st.rerun()

    # --- Display Watchlist ---
    st.subheader("📋 Your Watchlist")
    if st.session_state.watchlist:
        for stock in st.session_state.watchlist:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.write(f"🔹 {stock}")
            with col2:
                if st.button(f"❌ Remove {stock}", key=f"remove_{stock}"):
                    remove_from_watchlist(stock, st)
                    st.rerun()
    else:
        st.info("Your watchlist is empty. Add stocks to track options.")

    # --- Fetch & Display Options Chain ---
    st.subheader("📊 Options Chain")
    for stock in st.session_state.watchlist:
        st.write(f"Options Chain for **{stock}**")
        options_df = get_options_chain_polygon(stock, st)
        if not options_df.empty:
            st.dataframe(options_df)
        else:
            st.warning(f"No options data available for {stock}.")
