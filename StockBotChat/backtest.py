import backtrader as bt
import pandas as pd
import alpaca_trade_api as tradeapi
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load API Keys
load_dotenv()
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, "https://paper-api.alpaca.markets", api_version="v2")


def normalize_timeframe(timeframe):
    """
    Normalize the timeframe string to match Alpaca's expected format.

    Args:
        timeframe (str): Timeframe from UI (e.g., "1Day", "1Hour", "15Min", "5Min").

    Returns:
        str: Normalized timeframe (e.g., "1D", "1H", "15Min", "5Min").
    """
    timeframe_map = {
        "1Day": "1D",
        "1Hour": "1H",
        "15Min": "15Min",
        "5Min": "5Min"
    }
    return timeframe_map.get(timeframe, "1D")  # Default to "1D" if invalid


def fetch_historical_data(st, symbol, start, end, timeframe):
    """
    Fetches historical stock data from Alpaca API.
    """
    try:
        # Normalize timeframe
        normalized_timeframe = normalize_timeframe(timeframe)

        # Convert start and end to ISO 8601 format with UTC timezone
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
        if end_date > datetime.now():
            end_date = datetime.now() - timedelta(days=1)  # Cap at yesterday
        start_iso = start_date.strftime("%Y-%m-%dT00:00:00Z")
        end_iso = end_date.strftime("%Y-%m-%dT23:59:59Z")

        # Debug: Log the request
        print(f"Fetching bars for {symbol}, timeframe={normalized_timeframe}, start={start_iso}, end={end_iso}")

        # Fetch bars from Alpaca
        bars = api.get_bars(symbol, normalized_timeframe, start=start_iso, end=end_iso, limit=None)
        if not bars:
            print(f"No bars returned for {symbol}, timeframe={normalized_timeframe}, start={start_iso}, end={end_iso}")
            return None

        # Convert to DataFrame
        df = pd.DataFrame({
            "datetime": [b.t for b in bars],
            "open": [b.o for b in bars],
            "high": [b.h for b in bars],
            "low": [b.l for b in bars],
            "close": [b.c for b in bars],
            "volume": [b.v for b in bars]
        })
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)

        # Debug: Log the fetched data
        print(f"Fetched {len(df)} bars for {symbol}")
        return df

    except Exception as e:
        st.error(f"Error fetching historical data: {str(e)}")
        print(f"Fetch error for {symbol}: {str(e)}", file=sys.stderr)
        return None


class RSIStrategy(bt.Strategy):
    params = (
        ("rsi_period", 14),
        ("stop_loss", None),
        ("profit_target", None),
        ("rsi_buy_lt", 40),
        ("rsi_buy_ht", 50),
        ("rsi_sell_threshold", 70),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(period=self.params.rsi_period)
        self.trades = []
        self.buy_price = None
        self.position_size = 0

    def log_trade(self, trade_type, price, reason=""):
        """Logs the trade with date, type, price, and reason."""
        self.trades.append({
            "Date": self.data.datetime.date(0),
            "Type": trade_type,
            "Price": round(price, 2),
            "Reason": reason if reason else "",
            "RSI": round(self.rsi[0], 2)
        })

    def next(self):
        """Trading logic for buy/sell conditions."""
        current_price = self.data.close[0]
        # Debug: Log current state
        # print(f"Date: {self.data.datetime.date(0)}, Price: {current_price:.2f}, RSI: {self.rsi[0]:.2f}, Position: {self.position_size}")

        # Buy Condition: RSI between 40-50
        if self.position_size == 0 and (self.rsi[0] > self.params.rsi_buy_lt and self.rsi[0] < self.params.rsi_buy_ht):
            self.buy()
            self.log_trade("BUY", current_price, "RSI between 40-50")
            self.buy_price = current_price
            self.position_size = 1
            # print(f"BUY executed at {current_price:.2f}")

        # Stop Loss and Profit Target Prices (calculate defaults if None)
        stop_loss_price = None
        profit_target_price = None
        if self.buy_price:
            if self.params.stop_loss is not None:
                stop_loss_price = self.buy_price * (1 - self.params.stop_loss)
            if self.params.profit_target is not None:
                profit_target_price = self.buy_price * (1 + self.params.profit_target)

        # Sell Condition: RSI > threshold, Stop Loss, Profit Target
        if self.position_size > 0:
            reason = ""
            # RSI-based sell
            if self.rsi[0] > self.params.rsi_sell_threshold:
                reason = f"RSI > {self.params.rsi_sell_threshold}"
            # Stop Loss
            elif stop_loss_price is not None and current_price <= stop_loss_price:
                reason = f"Stop Loss hit at {stop_loss_price:.2f}"
            # Profit Target
            elif profit_target_price is not None and current_price >= profit_target_price:
                reason = f"Profit Target hit at {profit_target_price:.2f}"
            if reason:
                self.sell()
                self.log_trade("SELL", current_price, reason)
                self.buy_price = None
                self.position_size = 0
                # print(f"SELL executed at {current_price:.2f}, Reason: {reason}")


def run_backtest_rsi(st, symbol, start_date, end_date, params):
    """
    Runs the RSI backtest and returns trade results.
    """
    df = fetch_historical_data(st, symbol, start_date, end_date, params["timeframe"])
    if df is None:
        return None, None

    cerebro = bt.Cerebro()
    cerebro.addstrategy(
        RSIStrategy,
        rsi_period=params["rsi_period"],
        stop_loss=params["stop_loss"],
        profit_target=params["profit_target"],
        rsi_buy_lt=40,
        rsi_buy_ht=50,
        rsi_sell_threshold=70
    )
    cerebro.addsizer(bt.sizers.FixedSize, stake=params["qty"])

    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.broker.set_cash(10000)
    results = cerebro.run()
    strategy = results[0]
    trades_df = pd.DataFrame(strategy.trades)

    # Arrange Buy and Sell in one row & calculate % profit
    trade_pairs = []
    buy_prices = []
    total_profit = 0

    for _, row in trades_df.iterrows():
        if row["Type"] == "BUY":
            buy_prices.append((row["Date"], row["Price"], row["RSI"]))
        elif row["Type"] == "SELL" and buy_prices:
            buy_date, buy_price, buy_rsi = buy_prices.pop(0)
            profit = (row["Price"] - buy_price) * params["qty"]
            percent_profit = ((row["Price"] - buy_price) / buy_price) * 100
            total_profit += profit

            trade_pairs.append({
                "Buy Date": buy_date,
                "Buy Price": buy_price,
                "Buy RSI": buy_rsi,
                "Sell Date": row["Date"],
                "Sell Price": row["Price"],
                "Sell RSI": row["RSI"],
                "Profit ($)": round(profit, 2),
                "Profit (%)": round(percent_profit, 2),
                "Sell Reason": row["Reason"]
            })

    # Add unpaired buys as open positions
    for buy_date, buy_price, buy_rsi in buy_prices:
        trade_pairs.append({
            "Buy Date": buy_date,
            "Buy Price": buy_price,
            "Buy RSI": buy_rsi,
            "Sell Date": "Open",
            "Sell Price": None,
            "Sell RSI": None,
            "Profit ($)": 0.0,
            "Profit (%)": 0.0,
            "Sell Reason": "Position still open"
        })

    trades_summary_df = pd.DataFrame(trade_pairs)

    # Convert date columns to strings to ensure Arrow compatibility
    trades_summary_df["Buy Date"] = trades_summary_df["Buy Date"].astype(str)
    trades_summary_df["Sell Date"] = trades_summary_df["Sell Date"].astype(str)

    # Ensure "Sell Reason" is always a string
    trades_summary_df["Sell Reason"] = trades_summary_df["Sell Reason"].fillna("").astype(str)

    return trades_summary_df, round(total_profit, 2)