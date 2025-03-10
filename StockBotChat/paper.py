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
        timeframe (str): Timeframe from Streamlit UI (e.g., "1Day", "1Hour", "15Min").

    Returns:
        str: Normalized timeframe (e.g., "1D", "1H", "15Min").
    """
    timeframe_map = {
        "1Day": "1D",
        "1Hour": "1H",
        "15Min": "15Min",
        "5Min": "5Min"
    }
    return timeframe_map.get(timeframe, "1D")  # Default to "1D" if invalid


def validate_symbol(symbol):
    """
    Validate if the symbol is supported by Alpaca.

    Args:
        symbol (str): Stock symbol (e.g., "NVDA").

    Returns:
        bool: True if the symbol is valid, False otherwise.
    """
    try:
        asset = api.get_asset(symbol)
        return asset.tradable and asset.status == "active"
    except Exception:
        return False


def round_price(price):
    """
    Rounds the price to the correct decimal places:
    - Stocks ≥ $1: Rounded to **2 decimal places**
    - Stocks < $1: Rounded to **4 decimal places** (sub-dollar stocks)

    Args:
        price (float): The price to round.

    Returns:
        float: Rounded price.
    """
    return round(price, 2) if price >= 1 else round(price, 4)


def execute_paper_trade(symbol, timeframe, strategy_type, params, strategy_logic):
    """
    Execute paper trading for a given strategy using Alpaca API.

    Args:
        symbol (str): Stock symbol (e.g., "NVDA").
        timeframe (str): Timeframe for data (e.g., "1Day", "1Hour").
        strategy_type (str): The type of strategy ("RSI", "Momentum", "Breakout").
        params (dict): Parameters for the strategy (e.g., rsi_period, qty, stop_loss, profit_target).
        strategy_logic (callable): A function that defines the strategy logic, returning a tuple (action, stop_price, target_price).

    Returns:
        tuple: (bool, str) - Success status and message.
    """
    try:
        # ✅ Validate symbol
        if not validate_symbol(symbol):
            return False, f"Invalid symbol: {symbol}. Please check the stock symbol."

        # ✅ Normalize timeframe
        normalized_timeframe = normalize_timeframe(timeframe)

        # ✅ Define a date range (last 30 days to yesterday) to ensure data availability
        end_date = datetime.now() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=30)  # 30 days ago
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        # ✅ Fetch recent bars for strategy calculation
        limit = params.get("rsi_period", 14) + 1
        bars = api.get_bars(
            symbol=symbol,
            timeframe=normalized_timeframe,
            start=start_date_str,
            end=end_date_str,
            limit=limit
        ).df

        if bars.empty:
            return False, "No data available for strategy calculation. The market might be closed, or the symbol/timeframe might not have recent data."

        # ✅ Call the strategy logic to determine action
        action, stop_price, target_price = strategy_logic(bars, params)

        # ✅ Ensure stop & target prices are correctly rounded
        stop_price = round_price(stop_price)
        target_price = round_price(target_price)

        # ✅ Check if there is already an open position
        position = None
        for pos in api.list_positions():
            if pos.symbol == symbol:
                position = pos
                break

        # ✅ Execute Buy Order (If No Open Position)
        if action == "buy" and not position:
            order = api.submit_order(
                symbol=symbol,
                qty=params.get("qty", 100),
                side="buy",
                type="market",
                time_in_force="day"
            )
            message = f"✅ Buy order placed: {order.id}, Price: ${bars['close'].iloc[-1]:.2f}"

            # ✅ Set Stop Loss & Profit Target Orders
            if params.get("stop_loss"):
                stop_order = api.submit_order(
                    symbol=symbol,
                    qty=params.get("qty", 100),
                    side="sell",
                    type="stop",
                    stop_price=stop_price,  # ✅ Rounded Stop Loss Price
                    time_in_force="day"
                )
                message += f"\n🚨 Stop Loss set at: ${stop_price:.2f}"

            if params.get("profit_target"):
                target_order = api.submit_order(
                    symbol=symbol,
                    qty=params.get("qty", 100),
                    side="sell",
                    type="limit",
                    limit_price=target_price,  # ✅ Rounded Target Price
                    time_in_force="day"
                )
                message += f"\n🏆 Profit Target set at: ${target_price:.2f}"

            return True, message

        # ✅ Execute Sell Order (If Position Exists)
        elif action == "sell" and position:
            order = api.submit_order(
                symbol=symbol,
                qty=params.get("qty", 100),
                side="sell",
                type="market",
                time_in_force="day"
            )
            message = f"✅ Sell order placed: {order.id}, Price: ${bars['close'].iloc[-1]:.2f}"
            return True, message

        else:
            return False, f"🔵 No action taken for {strategy_type} strategy."

    except Exception as e:
        return False, f"❌ Paper trading error: {str(e)}"