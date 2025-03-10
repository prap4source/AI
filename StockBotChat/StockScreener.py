import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pytz

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
        /* Style the dataframe */
        .stDataFrame {
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            overflow: hidden;
        }
        .stDataFrame thead th {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
            text-align: center;
            padding: 10px;
            border-bottom: 2px solid #45a049;
        }
        .stDataFrame tbody td {
            text-align: center;
            padding: 8px;
            border-bottom: 1px solid #ddd;
        }
        .stDataFrame tbody tr:hover {
            background-color: #f5f5f5;
        }
        </style>
    """, unsafe_allow_html=True)

@st.cache_data
def fetch_stock_universe(category):
    """Fetch stock universe based on market cap category from Wikipedia or a proxy."""
    try:
        if category == "WatchList":
            # Watchlist of Known stocks
            tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "DOCS","AVGO","NFLX","AWK","BJ","CCI"]
        elif category == "Large Cap":
            # Approximate Large Cap (market cap > $10B) using S&P 500 as a proxy
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            df = pd.read_html(url)[0]
            tickers = df["Symbol"].tolist()
        elif category == "Mid Cap":
            # Use S&P MidCap 400 as a proxy for Mid Cap ($2B - $10B)
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies"
            df = pd.read_html(url)[0]  # First table contains ticker symbols
            tickers = df["Symbol"].tolist() if "Symbol" in df.columns else []
            # Note: Market caps may range beyond $2B-$10B; filter if needed with real-time data
        elif category == "Small Cap":
            # Use S&P SmallCap 600 as a proxy for Small Cap (< $2B)
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_600_companies"
            df = pd.read_html(url)[0]  # First table contains ticker symbols
            tickers = df["Symbol"].tolist() if "Symbol" in df.columns else []
            # Note: Market caps may exceed $2B; filter if needed with real-time data
        else:
            raise ValueError(f"Unsupported category: {category}")

        # Clean tickers (e.g., replace '.' with '-' for Yahoo Finance compatibility)
        tickers = [ticker.replace('.', '-') for ticker in tickers]
        return tickers
    except Exception as e:
        st.error(f"Error fetching stock universe for {category}: {str(e)}")
        return []

@st.cache_data
def fetch_stock_data(symbol, lookback_days, timeframe="1d"):
    """Fetch historical stock data using yfinance for the specified lookback and timeframe."""
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=lookback_days)
        stock = yf.Ticker(symbol)
        start_ts = ny_timezone.localize(datetime.combine(start_date, datetime.min.time()))
        end_ts = ny_timezone.localize(datetime.combine(end_date, datetime.min.time()))
        # Map timeframe to yfinance intervals
        interval_map = {
            "1 Hour": "1h",
            "1 Day": "1d",
            "1 Week": "1wk",
            "1 Month": "1mo"
        }
        interval = interval_map.get(timeframe, "1d")  # Default to "1d" if timeframe not found
        df = stock.history(start=start_ts, end=end_ts, interval=interval)
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
        return None

def calculate_reversal_breakout(symbol, df, timeframe="1d"):
    """Calculate reversal breakout metrics based on MA and RSI."""
    if df is None or len(df) < 21:  # Ensure enough data for 21-day SMA
        return None

    # Calculate MAs
    df["sma_8"] = df["Close"].rolling(window=8).mean()
    df["sma_21"] = df["Close"].rolling(window=21).mean()

    # Calculate RSI
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss.replace(0, 1e-10)  # Avoid division by zero
    rsi = 100 - (100 / (1 + rs))

    # Initialize variables
    trend_found_date = None
    price_at_trend_found = None
    signal_type = None

    # Iterate through the DataFrame to find the first signal
    for idx in range(len(df)):
        window_df = df.iloc[:idx + 1]
        if len(window_df) < 21:
            continue

        current_price = window_df["Close"].iloc[-1]
        sma_8 = window_df["sma_8"].iloc[-1]
        sma_21 = window_df["sma_21"].iloc[-1]
        current_rsi = rsi.iloc[-1] if idx > 0 else 0  # Ensure RSI is calculated

        # Manual crossover implementation
        price_cross_above_sma = (window_df["Close"].iloc[-1] > window_df["sma_8"].iloc[-1] and
                                window_df["Close"].shift(1).iloc[-1] <= window_df["sma_8"].shift(1).iloc[-1]) if idx > 0 else False
        sma_cross_above = (window_df["sma_8"].iloc[-1] > window_df["sma_21"].iloc[-1] and
                          window_df["sma_8"].shift(1).iloc[-1] <= window_df["sma_21"].shift(1).iloc[-1]) if idx > 0 else False
        rsi_above_30 = current_rsi > 30
        rsi_increasing = (current_rsi > rsi.shift(1).iloc[-1]) if idx > 0 else False

        buy_signal = price_cross_above_sma and sma_cross_above and rsi_above_30 and rsi_increasing

        # Manual crossunder implementation
        price_cross_below_sma = (window_df["Close"].iloc[-1] < window_df["sma_8"].iloc[-1] and
                                window_df["Close"].shift(1).iloc[-1] >= window_df["sma_8"].shift(1).iloc[-1]) if idx > 0 else False
        sma_cross_below = (window_df["sma_8"].iloc[-1] < window_df["sma_21"].iloc[-1] and
                          window_df["sma_8"].shift(1).iloc[-1] >= window_df["sma_21"].shift(1).iloc[-1]) if idx > 0 else False
        rsi_below_70 = current_rsi < 70
        rsi_decreasing = (current_rsi < rsi.shift(1).iloc[-1]) if idx > 0 else False

        sell_signal = price_cross_below_sma and sma_cross_below and rsi_below_70 and rsi_decreasing

        # Check for first signal
        if buy_signal or sell_signal:
            trend_found_date = window_df.index[-1].date()
            price_at_trend_found = current_price
            signal_type = "Buy" if buy_signal else "Sell"
            break

    if trend_found_date is None:
        return None

    return {
        "symbol": symbol,
        "signal_type": signal_type,
        "trend_found_date": trend_found_date,
        "price_at_trend_found": price_at_trend_found,
        "current_price": df["Close"].iloc[-1]
    }

def screen_stocks(st, universe_symbols, lookback_days, timeframe):
    """Screen stocks based on the reversal breakout strategy."""
    st.write(f"**Reversal Breakout Strategy Overview:** This strategy identifies stocks experiencing a reversal breakout. A **Buy** signal occurs when the price crosses above the 8-day SMA, the 8-day SMA crosses above the 21-day SMA, and the RSI rises above 30 with an increasing trend. A **Sell** signal occurs when the price crosses below the 8-day SMA, the 8-day SMA crosses below the 21-day SMA, and the RSI drops below 70 with a decreasing trend. The analysis is performed over a {lookback_days}-day lookback period using a {timeframe} timeframe.")

    strategy_data = []
    with st.spinner(f"🔄 Analyzing {len(universe_symbols)} stocks..."):
        for symbol in universe_symbols:
            df = fetch_stock_data(symbol, lookback_days, timeframe)
            data = calculate_reversal_breakout(symbol, df, timeframe)
            if data:
                strategy_data.append(data)

    return strategy_data

def show_screen(st):
    """Displays the stock screener UI in Streamlit."""
    apply_custom_css()
    st.title("📈 Stock Screener")

    # Input UI
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        stock_category = st.selectbox("Stock Category", ["WatchList", "Large Cap", "Mid Cap", "Small Cap"], index=0)
    with col2:
        timeframe = st.selectbox("Time Frame", ["1 Hour", "1 Day", "1 Week", "1 Month"], index=1)  # Default to "1 Day"
    with col3:
        condition = st.selectbox("Condition", ["Reversal Breakout"], index=0)  # Single condition for now
    with col4:
        lookback_days = st.number_input("Lookback (days)", min_value=1, value=90, step=1)

    # Fetch stock universe dynamically (only on button click)
    universe_symbols = []

    # Screen button to trigger analysis
    if st.button("Screen"):
        universe_symbols = fetch_stock_universe(stock_category)
        if not universe_symbols:
            st.error("Failed to fetch stock universe. Please try again.")
            return

        # Apply screening strategy
        result = screen_stocks(st, universe_symbols, lookback_days, timeframe)
        strategy_data = result if isinstance(result, list) else []

        if not strategy_data:
            st.error("No stocks meet the reversal breakout criteria.")
            return

        strategy_df = pd.DataFrame(strategy_data)
        # Calculate profit percentage (adjusted for Sell signals)
        strategy_df["profit_percent"] = strategy_df.apply(
            lambda row: ((row["current_price"] - row["price_at_trend_found"]) / row["price_at_trend_found"] * 100
                        if row["signal_type"] == "Buy"
                        else (row["price_at_trend_found"] - row["current_price"]) / row["price_at_trend_found"] * 100),
            axis=1
        ).round(2)

        # Stylish table with custom headers
        st.subheader("📈 Screened Stocks")
        styled_df = strategy_df[["symbol", "signal_type", "price_at_trend_found", "current_price", "profit_percent", "trend_found_date"]]
        styled_df.columns = ["Stock", "Signal", "Entry", "Current", "Profit", "Date"]
        styled_df = styled_df.style\
            .set_properties(**{'text-align': 'center'})\
            .set_table_styles([
                {'selector': 'th',
                 'props': [('background-color', '#4CAF50'),
                           ('color', 'white'),
                           ('font-weight', 'bold'),
                           ('text-align', 'center'),
                           ('padding', '10px'),
                           ('border-bottom', '2px solid #45a049')]},
                {'selector': 'td',
                 'props': [('padding', '8px'),
                           ('border-bottom', '1px solid #ddd')]},
                {'selector': 'tr:hover',
                 'props': [('background-color', '#f5f5f5')]},
            ])\
            .apply(lambda row: ['color: #2e7d32; font-weight: bold;' if row["Profit"] > 0 else 'color: #d32f2f; font-weight: bold;' if row["Profit"] < 0 else ''], axis=1, subset=["Profit"])\
            .format({
                "Entry": lambda x: f"${x:.2f}",
                "Current": lambda x: f"${x:.2f}",
                "Profit": lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A",
                "Date": lambda x: x.strftime("%Y-%m-%d")
            })
        st.dataframe(styled_df, use_container_width=True, hide_index=True)