import backtrader as bt
import pandas as pd
import alpaca_trade_api as tradeapi
import os
from dotenv import load_dotenv

# Load API Keys
load_dotenv()
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, "https://paper-api.alpaca.markets", api_version="v2")


def fetch_historical_data(symbol, start, end, timeframe):
    """
    Fetches historical stock data from Alpaca API.
    """
    try:
        bars = api.get_bars(symbol, timeframe, start=start, end=end, limit=None)
        if not bars:
            return None
        df = pd.DataFrame({
            "datetime": [b.t for b in bars], "open": [b.o for b in bars], "high": [b.h for b in bars],
            "low": [b.l for b in bars], "close": [b.c for b in bars], "volume": [b.v for b in bars]
        })
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)

        # Calculate RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)  # Avoid division by zero
        df["rsi"] = 100 - (100 / (1 + rs))

        return df.dropna()
    except Exception as e:
        return None


class RSIStrategy(bt.Strategy):
    params = (("rsi_period", 14), ("stop_loss", 0.10), ("profit_target", 0.30))  # ✅ Default SL = 10%, PT = 30%

    def __init__(self):
        self.rsi = bt.indicators.RSI(period=self.params.rsi_period)
        self.trades = []
        self.buy_price = None  # ✅ Track buy price
        self.position_size = 0  # ✅ Track position size

    def log_trade(self, trade_type, price):
        """Logs the trade with date, type, and price."""
        self.trades.append({"Date": self.data.datetime.date(0), "Type": trade_type, "Price": round(price, 2)})

    def next(self):
        """Trading logic for buy/sell conditions."""
        current_price = self.data.close[0]

        # ✅ Buy Condition: RSI crosses between 40-50
        if self.position_size == 0 and (self.rsi[0] > 40 and self.rsi[0] < 50):
            self.buy()
            self.log_trade("BUY", current_price)
            self.buy_price = current_price  # Store buy price
            self.position_size = 1  # ✅ Track position

        # ✅ Stop Loss and Profit Target Prices
        if self.buy_price:
            stop_loss_price = self.buy_price * (1 - self.params.stop_loss)  # ✅ SL%
            profit_target_price = self.buy_price * (1 + self.params.profit_target)  # ✅ PT%

        # ✅ Sell Condition: RSI above 70, Stop Loss hit, or Profit Target hit
        if self.position_size > 0:
            if self.rsi[0] > 70 or current_price <= stop_loss_price or current_price >= profit_target_price:
                self.sell()
                self.log_trade("SELL", current_price)
                self.position_size = 0  # ✅ Reset position
                self.buy_price = None  # ✅ Reset buy price


def run_backtest_rsi(symbol, start_date, end_date, params):
    """
    Runs the RSI backtest and returns trade results.
    """
    df = fetch_historical_data(symbol, start_date, end_date, params["timeframe"])
    if df is None:
        return None, None, None

    cerebro = bt.Cerebro()
    cerebro.addstrategy(RSIStrategy, rsi_period=params["rsi_period"], stop_loss=params["stop_loss"], profit_target=params["profit_target"])
    cerebro.addsizer(bt.sizers.FixedSize, stake=params["qty"])

    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.broker.set_cash(10000)
    results = cerebro.run()
    strategy = results[0]
    trades_df = pd.DataFrame(strategy.trades)

    # ✅ Arrange Buy and Sell in one row & calculate % profit
    trade_pairs = []
    buy_prices = []
    total_profit = 0

    for _, row in trades_df.iterrows():
        if row["Type"] == "BUY":
            buy_prices.append((row["Date"], row["Price"]))  # Store buy date & price
        elif row["Type"] == "SELL" and buy_prices:
            buy_date, buy_price = buy_prices.pop(0)  # Get corresponding buy trade
            profit = (row["Price"] - buy_price) * params["qty"]  # ✅ Calculate profit
            percent_profit = ((row["Price"] - buy_price) / buy_price) * 100  # ✅ % profit
            total_profit += profit

            trade_pairs.append({
                "Buy Date": buy_date,
                "Buy Price": buy_price,
                "Sell Date": row["Date"],
                "Sell Price": row["Price"],
                "Profit ($)": round(profit, 2),
                "Profit (%)": round(percent_profit, 2)
            })

    # Convert to DataFrame
    trades_summary_df = pd.DataFrame(trade_pairs)
    return trades_summary_df, round(total_profit, 2)
