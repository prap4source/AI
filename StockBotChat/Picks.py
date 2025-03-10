import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import numpy as np
import requests

# Set timezone to America/New_York
ny_timezone = pytz.timezone("America/New_York")


def apply_custom_css():
    """Apply custom CSS to ensure full-width layout and clean UI."""
    st.markdown("""
        <style>
        .main .block-container {
            padding-left: 0 !important;
            padding-right: 0 !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            max-width: 100% !important;
            width: 100% !important;
        }
        div[data-testid="stVerticalBlock"] > div {
            padding-left: 0 !important;
            padding-right: 0 !important;
            width: 100% !important;
        }
        div[data-testid="column"] {
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
            width: 100% !important;
            display: flex;
            justify-content: space-between;
        }
        div[data-testid="stDataFrame"] {
            width: 100% !important;
        }
        .backtest-section {
            margin-top: 10px;
            transition: opacity 0.3s ease;
        }
        .backtest-section.hidden {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)


@st.cache_data
def fetch_stock_universe(universe_name):
    """Fetch stock universe dynamically from Wikipedia."""
    try:
        if universe_name == "S&P 500":
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            df = pd.read_html(url)[0]  # First table contains the S&P 500 components
            tickers = df["Symbol"].tolist()
        elif universe_name == "Nasdaq 100":
            url = "https://en.wikipedia.org/wiki/Nasdaq-100"
            df = pd.read_html(url)[4]  # Nasdaq-100 components table (index may vary, adjust if needed)
            tickers = df["Ticker"].tolist()
        else:
            raise ValueError(f"Unsupported universe: {universe_name}")

        # Clean tickers (e.g., replace '.' with '-' for Yahoo Finance compatibility)
        tickers = [ticker.replace('.', '-') for ticker in tickers]
        return tickers
    except Exception as e:
        st.error(f"Error fetching stock universe for {universe_name}: {str(e)}")
        return []


@st.cache_data
def fetch_stock_data(symbol, start_date, end_date):
    """Fetch historical stock data using yfinance."""
    try:
        stock = yf.Ticker(symbol)
        start_ts = ny_timezone.localize(datetime.combine(start_date, datetime.min.time()))
        end_ts = ny_timezone.localize(datetime.combine(end_date, datetime.min.time()))
        df = stock.history(start=start_ts, end=end_ts, interval="1d")
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
        return None


def calculate_bollinger_bands(df, window=20, std_dev=2):
    """Calculate Bollinger Bands."""
    sma = df["Close"].rolling(window=window).mean()
    std = df["Close"].rolling(window=window).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, lower_band


def calculate_macd(df):
    """Calculate MACD and Signal Line with shorter periods."""
    exp1 = df["Close"].ewm(span=9, adjust=False).mean()  # Shortened to 9-day
    exp2 = df["Close"].ewm(span=21, adjust=False).mean()  # Shortened to 21-day
    macd = exp1 - exp2
    signal = macd.ewm(span=5, adjust=False).mean()  # Shortened to 5-day
    return macd, signal


def calculate_reversal_breakout(symbol, start_date, end_date, is_backtest=False):
    """Calculate reversal breakout metrics and find the first trend detection date."""
    momentum_start_date = start_date - timedelta(days=180) if not is_backtest else start_date
    df = fetch_stock_data(symbol, momentum_start_date, end_date)
    if df is None or len(df) < 180:
        return None

    if is_backtest:
        momentum_df = df[(df.index.date >= start_date) & (df.index.date <= end_date)]
        if len(momentum_df) == 0:
            return None
    else:
        momentum_df = df

    # Initialize variables for trend detection
    trend_found_date = None
    price_at_trend_found = None
    composite_score = 0
    current_price = momentum_df["Close"].iloc[-1]

    # Iterate through the DataFrame to find the first date where the trend is detected
    for idx in range(len(momentum_df)):
        window_df = momentum_df.iloc[:idx + 1]
        if len(window_df) < 21:  # Need enough data for SMA and MACD
            continue

        # Trend confirmation: Price above 8-day and 21-day SMA
        window_df["sma_8"] = window_df["Close"].rolling(window=8).mean()
        window_df["sma_21"] = window_df["Close"].rolling(window=21).mean()
        price = window_df["Close"].iloc[-1]
        sma_8 = window_df["sma_8"].iloc[-1]
        sma_21 = window_df["sma_21"].iloc[-1]
        is_above_mas = price > sma_8 > sma_21

        # MACD Bullish Cross (check last 3 days in the window)
        macd, signal = calculate_macd(window_df)
        macd_values = macd.tail(3)
        signal_values = signal.tail(3)
        is_bullish_cross = False
        macd_score = 0
        for i in range(1, len(macd_values)):
            macd_prev, macd_curr = macd_values.iloc[i - 1], macd_values.iloc[i]
            signal_prev, signal_curr = signal_values.iloc[i - 1], signal_values.iloc[i]
            if macd_curr > signal_curr and macd_prev <= signal_prev:
                is_bullish_cross = True
                macd_score = 1
                break

        # Bollinger Bands (within bands)
        upper_band, lower_band = calculate_bollinger_bands(window_df)
        upper = upper_band.iloc[-1]
        lower = lower_band.iloc[-1]
        is_within_bands = lower <= price <= upper
        bollinger_score = 1 if is_within_bands else 0

        # Volume Score (no surge required)
        volume_score = 1 if len(window_df) >= 20 else 0

        # Composite Score
        composite_score = (
                    0.4 * (1 if is_above_mas else 0) + 0.4 * macd_score + 0.2 * bollinger_score + 0.2 * volume_score)

        # Check if trend is detected
        if composite_score > 0:
            trend_found_date = window_df.index[-1].date()
            price_at_trend_found = price
            break

    # If no trend is found, return None
    if trend_found_date is None:
        return None

    # Debug output
    if st.session_state.get("debug_mode", False):
        st.write(
            f"Symbol: {symbol}, is_above_mas: {is_above_mas}, macd_score: {macd_score}, bollinger_score: {bollinger_score}, volume_score: {volume_score}, composite_score: {composite_score}, trend_found_date: {trend_found_date}")

    # Liquidity metrics
    avg_volume = momentum_df["Volume"].tail(30).mean() if len(momentum_df) >= 30 else 0

    return {
        "symbol": symbol,
        "composite_score": composite_score,
        "trend_detected": composite_score > 0,
        "current_price": current_price,
        "price_at_start": current_price if is_backtest else current_price,
        # For consistency, use current price in backtest
        "trend_found_date": trend_found_date,
        "price_at_trend_found": price_at_trend_found,
        "avg_volume": avg_volume
    }


def reversal_breakout_strategy(st, universe_symbols, start_date, end_date, is_backtest=False):
    """Identify top 10 stocks using reversal breakout strategy."""
    st.write(
        "This strategy identifies top 10 stocks based on price above 8-day and 21-day MAs, MACD bullish cross, Bollinger Bands, and volume.")

    strategy_data = []
    with st.spinner(f"🔄 Analyzing {len(universe_symbols)} stocks..."):
        for symbol in universe_symbols:
            data = calculate_reversal_breakout(
                symbol,
                start_date,
                end_date,
                is_backtest=is_backtest
            )
            if data and data["current_price"] >= 5 and data["avg_volume"] >= 500000 and data["composite_score"] > 0:
                strategy_data.append(data)

    return strategy_data


def show_picks(st):
    """Displays the stock picks UI in Streamlit."""
    apply_custom_css()
    st.title("📈 Stock Picks")

    # Default date range
    default_end_date = datetime.today().date()
    default_start_date = default_end_date - timedelta(days=180)

    # Input UI with debug option
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        universe = st.selectbox("Stock Universe", ["S&P 500", "Nasdaq 100"], index=0)
    with col2:
        enable_backtest = st.checkbox("Enable Backtest Mode", value=False)
    with col3:
        debug_mode = st.checkbox("Debug Mode", value=False)
        st.session_state["debug_mode"] = debug_mode

    # Fetch stock universe dynamically
    universe_symbols = fetch_stock_universe(universe)
    if not universe_symbols:
        st.error("Failed to fetch stock universe. Please try again later.")
        return

    # Date inputs (hidden unless Backtest mode is enabled)
    start_date = default_start_date
    end_date = default_end_date
    if enable_backtest:
        with st.expander("Backtest Settings", expanded=True):
            col4, col5 = st.columns(2)
            with col4:
                start_date = st.date_input("Start Date", default_start_date, key="start_date_input")
            with col5:
                end_date = st.date_input("End Date", default_end_date, key="end_date_input")

    st.write("")  # Spacer

    # Validate date range (only for Backtest mode)
    if enable_backtest and start_date >= end_date:
        st.error("Start Date must be before End Date.")
        return

    # Apply strategy
    with st.expander("🚀 Reversal/Breakout Picks", expanded=True):
        if st.button("Run Analysis"):
            if enable_backtest:
                result = reversal_breakout_strategy(st, universe_symbols, start_date, end_date, is_backtest=True)
                st.write(f"**Date Range Used:** {start_date} to {end_date}")
            else:
                result = reversal_breakout_strategy(st, universe_symbols, default_end_date, default_end_date,
                                                    is_backtest=False)
                st.write("**Current Reversal/Breakout Stocks**")

            strategy_data = result if isinstance(result, list) else []
            if not strategy_data:
                st.error("No stocks meet the reversal breakout criteria.")
                return

            strategy_df = pd.DataFrame(strategy_data)
            top_stocks = strategy_df.sort_values(by="composite_score", ascending=False).head(10)

            st.subheader("📈 Top 10 Reversal/Breakout Stocks")
            if enable_backtest:
                format_dict = {
                    "trend_detected": lambda x: "Yes" if x else "No",
                    "current_price": lambda x: f"${x:.2f}",
                    "price_at_start": lambda x: f"${x:.2f}",
                    "price_at_trend_found": lambda x: f"${x:.2f}",
                    "trend_found_date": lambda x: x.strftime("%Y-%m-%d"),
                    "avg_volume": lambda x: f"{int(x):,}"
                }
                st.dataframe(
                    top_stocks[["symbol", "trend_detected", "price_at_start", "current_price", "price_at_trend_found",
                                "trend_found_date", "avg_volume"]].style.format(format_dict),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                format_dict = {
                    "composite_score": lambda x: f"{x:.2f}",
                    "current_price": lambda x: f"${x:.2f}",
                    "price_at_trend_found": lambda x: f"${x:.2f}",
                    "trend_found_date": lambda x: x.strftime("%Y-%m-%d"),
                    "avg_volume": lambda x: f"{int(x):,}"
                }
                st.dataframe(
                    top_stocks[
                        ["symbol", "composite_score", "current_price", "price_at_trend_found", "trend_found_date",
                         "avg_volume"]].style.format(format_dict),
                    use_container_width=True,
                    hide_index=True
                )