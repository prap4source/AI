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
        normalized_timeframe = normalize_timeframe(timeframe)

        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
        if end_date > datetime.now():
            end_date = datetime.now() - timedelta(days=1)

        bars = api.get_bars(symbol, normalized_timeframe, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"), limit=None)

        if not bars:
            return None

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

        return df

    except Exception as e:
        st.error(f"Error fetching historical data: {str(e)}")
        return None


class RSIStrategy(bt.Strategy):
    params = (
        ("rsi_period", 14),
        ("stop_loss", None),
        ("profit_target", None),
        ("rsi_buy_threshold", 40),  # ✅ Buy when RSI crosses over 40
        ("rsi_sell_threshold", 70),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(period=self.params.rsi_period)
        self.trades = []
        self.buy_price = None
        self.position_size = 0
        self.prev_rsi = None  # ✅ Track previous RSI value for crossover detection

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

        # ✅ Buy Condition: RSI crosses over 40 (previous RSI < 40, current RSI > 40)
        if self.position_size == 0 and self.prev_rsi is not None and self.prev_rsi < self.params.rsi_buy_threshold and self.rsi[0] >= self.params.rsi_buy_threshold:
            self.buy()
            self.log_trade("BUY", current_price, "RSI crossover 40")
            self.buy_price = current_price
            self.position_size = 1

        stop_loss_price = self.buy_price * (1 - self.params.stop_loss) if self.buy_price and self.params.stop_loss else None
        profit_target_price = self.buy_price * (1 + self.params.profit_target) if self.buy_price and self.params.profit_target else None

        # ✅ Sell Condition: RSI > 70, Stop Loss hit, or Profit Target hit
        if self.position_size > 0:
            reason = ""
            if self.rsi[0] > self.params.rsi_sell_threshold:
                reason = f"RSI > {self.params.rsi_sell_threshold}"
            elif stop_loss_price and current_price <= stop_loss_price:
                reason = f"Stop Loss hit at {stop_loss_price:.2f}"
            elif profit_target_price and current_price >= profit_target_price:
                reason = f"Profit Target hit at {profit_target_price:.2f}"
            if reason:
                self.sell()
                self.log_trade("SELL", current_price, reason)
                self.buy_price = None
                self.position_size = 0

        # ✅ Store previous RSI for next iteration
        self.prev_rsi = self.rsi[0]


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
        profit_target=params["profit_target"]
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

    trades_summary_df["Sell Reason"] = trades_summary_df["Sell Reason"].fillna("").astype(str)

    return trades_summary_df, round(total_profit, 2)