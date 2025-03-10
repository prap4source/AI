from datetime import datetime

def generate_rsi_strategy(strategy_type, params):
    """
    Generate TradingView Pine Script for a given strategy with configurable inputs.

    Args:
        strategy_type (str): The type of strategy ("RSI", "Momentum", "Breakout").
        params (dict): Parameters for the strategy (e.g., rsi_period, stop_loss, profit_target, start_date, end_date).

    Returns:
        str: The generated Pine Script code.
    """
    # ✅ Convert start_date & end_date to datetime if they are date objects
    start_date = params.get("start_date", datetime(2023, 1, 1))
    end_date = params.get("end_date", datetime.now())

    if isinstance(start_date, datetime):  # Ensure it's a datetime object
        start_timestamp = int(start_date.timestamp() * 1000)  # Convert to milliseconds
    else:
        start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp() * 1000)

    if isinstance(end_date, datetime):
        end_timestamp = int(end_date.timestamp() * 1000)
    else:
        end_timestamp = int(datetime.combine(end_date, datetime.min.time()).timestamp() * 1000)

    if strategy_type == "RSI":
        # Extract parameters with default values
        rsi_period = params.get("rsi_period", 14)
        stop_loss = params.get("stop_loss", 0.15)  # Default to 15% if not provided
        profit_target = params.get("profit_target", 0.15)  # Default to 15% if not provided

        # ✅ Generate Pine Script with inputs
        pine_script = f"""//@version=5
strategy("RSI Strategy", overlay=false)

// Define configurable inputs
rsi_period = input.int({rsi_period}, title="RSI Period", minval=1, step=1)
stop_loss_pct = input.float({stop_loss * 100 if stop_loss else 0}, title="Stop Loss (%)", minval=0, step=0.1)
profit_target_pct = input.float({profit_target * 100 if profit_target else 0}, title="Profit Target (%)", minval=0, step=0.1)
start_date = input.time({start_timestamp}, title="Start Date")
end_date = input.time({end_timestamp}, title="End Date")

// RSI calculation and strategy logic
rsi = ta.rsi(close, rsi_period)
buy_signal = ta.crossover(rsi, 40) and rsi < 50
sell_signal = ta.crossunder(rsi, 70)

// Restrict trading to the specified date range
if time >= start_date and time <= end_date
    if (buy_signal)
        strategy.entry("Long", strategy.long)
        if (stop_loss_pct > 0 or profit_target_pct > 0)
            strategy.exit("Exit", "Long", stop=strategy.position_avg_price * (1 - stop_loss_pct / 100), limit=strategy.position_avg_price * (1 + profit_target_pct / 100))

    if (sell_signal)
        strategy.close("Long")
"""
        return pine_script

    elif strategy_type == "Momentum":
        # Placeholder for Momentum strategy with time period
        momentum_period = params.get("momentum_period", 14)
        pine_script = f"""//@version=5
strategy("Momentum Strategy", overlay=true)

// Define configurable inputs
momentum_period = input.int({momentum_period}, title="Momentum Period", minval=1, step=1)
start_date = input.time({start_timestamp}, title="Start Date")
end_date = input.time({end_timestamp}, title="End Date")

// Momentum logic placeholder
momentum = ta.mom(close, momentum_period)
buy_signal = ta.crossover(momentum, 0)
sell_signal = ta.crossunder(momentum, 0)

if time >= start_date and time <= end_date
    if (buy_signal)
        strategy.entry("Long", strategy.long)
    if (sell_signal)
        strategy.close("Long")
"""
        return pine_script

    elif strategy_type == "Breakout":
        # Placeholder for Breakout strategy with time period
        pine_script = f"""//@version=5
strategy("Breakout Strategy", overlay=true)

// Define configurable inputs
start_date = input.time({start_timestamp}, title="Start Date")
end_date = input.time({end_timestamp}, title="End Date")

// Breakout logic placeholder
// Add Breakout logic here

if time >= start_date and time <= end_date
    // Add trading logic here
"""
        return pine_script

    else:
        return "// Unsupported strategy type"