import streamlit as st
import backtest
from datetime import datetime, timedelta
import helpers

def rsi(st, stock_symbol, start_date, end_date, timeframe, num_stocks, stop_loss, profit_target):
    """
    Runs the RSI backtest strategy with user-configurable SL & Profit Target.
    """
    st.write("This strategy Buys when RSI is in between 40-50 and Sells when RSI hits 70")

    # ✅ RSI Period Input
    rsi_period = st.slider("RSI Period", 5, 30, 14)

    # ✅ Run Backtest Button
    if st.button("📉 Run Backtest", key="run_backtest"):
        with st.spinner(f"🔄 Running Backtest for {stock_symbol}..."):
            trades_summary_df, total_profit = backtest.run_backtest_rsi(
                stock_symbol, start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                {
                    "rsi_period": rsi_period,
                    "qty": num_stocks,
                    "timeframe": timeframe,
                    "stop_loss": stop_loss,
                    "profit_target": profit_target
                }
            )
        st.success("✅ Backtest Completed")

        # ✅ Display Trade History Table
        if trades_summary_df is not None and not trades_summary_df.empty:
            st.subheader("📜 Trade History")
            st.dataframe(
                trades_summary_df.style.format({
                    "Buy Price": "${:.2f}",
                    "Sell Price": "${:.2f}",
                    "Profit ($)": "${:.2f}",
                    "Profit (%)": "{:.2f}%"
                }),
                use_container_width=True
            )
        else:
            st.warning("No trades executed.")

        # ✅ Display Total Profit
        st.subheader("💰 Total Profit")
        st.metric("Profit", f"${total_profit:.2f}")

        # ✅ Placeholder for Chart
        st.subheader("📊 Chart Coming Soon!")


def show_strategies(st):
    """
    Displays the trading strategy UI in Streamlit.
    """
    st.title("📈 RSI Trading Strategy")

    # Default date values
    default_start_date = datetime(2023, 1, 1)
    default_end_date = datetime.today() - timedelta(days=1)

    # --- Input UI (Organized in 2 Rows) ---
    col1, col2, col3 = st.columns(3)
    with col1:
        stock_symbol = st.text_input("Stock Symbol", "AAPL")
        is_valid, message = helpers.validate_input(stock_symbol)
        if not is_valid and stock_symbol:
            st.error(message)
    with col2:
        start_date = st.date_input("Start Date", default_start_date)
    with col3:
        end_date = st.date_input("End Date", default_end_date)

    col4, col5, col6, col7= st.columns(4)
    with col4:
        timeframe = st.selectbox("Timeframe", ["1Day", "1Hour", "15Min", "5Min"], index=0)
    with col5:
        num_stocks = st.number_input("Trade Size", min_value=1, value=100, step=1)
    with col6:
        strategy_selected = st.selectbox("Select Strategy", ["RSI Strategy", "Momentum", "Breakout"], index=0)
    with col7:
        stop_loss_str = st.selectbox("Stop Loss (%)", ["10%", "15%", "25%", "50%", "None"], index=1)
        profit_target_str = st.selectbox("Profit Target (%)", ["10%", "15%", "25%", "50%", "None"], index=2)

    # ✅ Convert Dropdown Selection to Decimal (or None)
    stop_loss = None if stop_loss_str == "None" else int(stop_loss_str.replace("%", "")) / 100
    profit_target = None if profit_target_str == "None" else int(profit_target_str.replace("%", "")) / 100

    # Only proceed if the stock symbol is valid
    if not is_valid and stock_symbol:
        st.stop()  # Halt execution if symbol is invalid and input is provided

    st.write("")  # Spacer

    # ✅ RSI Strategy Inputs
    if strategy_selected == "RSI Strategy":
        with st.expander("📉 RSI Strategy", expanded=True):
            rsi(st, stock_symbol, start_date, end_date, timeframe, num_stocks, stop_loss, profit_target)
    elif strategy_selected == "Momentum":
        with st.expander("🚀 Momentum Strategy", expanded=True):
            st.write("Coming soon!")
    elif strategy_selected == "Breakout":
        with st.expander("📈 Breakout Strategy", expanded=True):
            st.write("Coming soon!")