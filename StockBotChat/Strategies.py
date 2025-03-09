import streamlit as st
import backtest
from datetime import datetime, timedelta
import helpers
import plotly.express as px  # Import Plotly for the pie chart
import pandas as pd
import sys

def apply_custom_css():
    st.markdown("""
        <style>
        /* Remove padding from the main container */
        .main .block-container {
            padding-left: 0 !important;
            padding-right: 0 !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            max-width: 100 !important;
        }
        /* Remove padding from all containers */
        div[data-testid="stVerticalBlock"] > div {
            padding-left: 0 !important;
            padding-right: 0 !important;
        }
        /* Ensure columns have no gaps */
        div[data-testid="column"] {
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

def categorize_sell_reason(reason):
    """Categorize the sell reason into a standardized label."""
    if "Stop Loss" in reason:
        return "Stop Loss"
    elif "RSI >" in reason:
        return "RSI > 70"
    elif "Profit Target" in reason:
        return "Profit Target"
    return "Other"

def rsi(st, stock_symbol, start_date, end_date, timeframe, num_stocks, stop_loss, profit_target):
    """
    Runs the RSI backtest strategy with user-configurable SL & Profit Target.
    """
    st.write("This strategy Buys when RSI is between 40-50 and Sells when RSI hits 70")

    # RSI Period Input
    rsi_period = st.slider("RSI Period", 5, 30, 14)

    # Run Backtest Button
    if st.button("📉 Run Backtest", key="run_backtest"):
        with st.spinner(f"🔄 Running Backtest for {stock_symbol}..."):
            trades_summary_df, total_profit = backtest.run_backtest_rsi(st,
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

        # Display Total Profit in a single line
        if total_profit is not None:
            st.markdown(f"### 💰 Total Profit: ${total_profit:.2f}")

        # Display Trade History Table
        if trades_summary_df is not None and not trades_summary_df.empty:
            st.subheader("📜 Trade History")
            # Define custom formatters to handle None values
            format_dict = {
                "Buy Price": lambda x: f"${x:.2f}" if x is not None else "N/A",
                "Sell Price": lambda x: f"${x:.2f}" if x is not None else "N/A",
                "Profit ($)": lambda x: f"${x:.2f}" if x is not None else "N/A",
                "Profit (%)": lambda x: f"{x:.2f}%" if x is not None else "N/A",
                "Buy RSI": lambda x: f"{x:.2f}" if x is not None else "N/A",
                "Sell RSI": lambda x: f"{x:.2f}" if x is not None else "N/A",
                "Sell Reason": lambda x: str(x) if x is not None else "N/A"
            }
            st.dataframe(
                trades_summary_df.style.format(format_dict),
                use_container_width=True
            )
            # Calculate Win/Loss Percentages and Sell Reasons (Exclude Open Positions)
            closed_trades_df = trades_summary_df[trades_summary_df["Sell Date"] != "Open"]
            if not closed_trades_df.empty:
                total_trades = len(closed_trades_df)
                winners = len(closed_trades_df[closed_trades_df["Profit ($)"] > 0])
                losers = len(closed_trades_df[closed_trades_df["Profit ($)"] <= 0])

                # Calculate win/loss percentages
                win_percentage = (winners / total_trades) * 100 if total_trades > 0 else 0
                loss_percentage = (losers / total_trades) * 100 if total_trades > 0 else 0

                # Categorize sell reasons
                closed_trades_df["Sell Category"] = closed_trades_df["Sell Reason"].apply(categorize_sell_reason)
                reason_counts = closed_trades_df["Sell Category"].value_counts()  # Fixed typo here
                reason_percentages = (reason_counts / total_trades * 100).round(2)

                # Display Win/Loss Summary with Pie Chart Side by Side
                st.subheader("📊 Win/Loss Summary")
                col1, col2 = st.columns([1, 2])  # Left column wider for text, right for chart

                with col1:
                    st.write("**Trade Metrics:**")
                    st.write(f"Winning Trades: {winners}/{total_trades}")
                    st.write(f"Win Rate: {win_percentage:.2f}%")
                    if not reason_counts.empty:
                        st.write("**Sell Reason Distribution:**")
                        for reason, count in reason_counts.items():
                            st.write(f"{reason}: {count} trades")

                with col2:
                    # Create Pie Chart with Sell Reasons
                    if not reason_percentages.empty:
                        fig = px.pie(
                            names=reason_percentages.index,
                            values=reason_percentages.values,
                            title="Distribution of Sell Reasons",
                            color=reason_percentages.index,
                            color_discrete_map={
                                "Stop Loss": "#EF553B",
                                "RSI > 70": "#00CC96",
                                "Profit Target": "#AB63FA",
                                "Other": "#636EFA"
                            }
                        )
                        fig.update_traces(textinfo="percent+label", textposition="inside")
                        fig.update_layout(showlegend=True)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.write("No sell reasons to display.")
            else:
                st.warning("No closed trades to analyze for win/loss percentage.")

        else:
            if trades_summary_df is None:
                st.error("Failed to fetch historical data for the selected symbol and date range.")
            else:
                st.warning("No trades executed.")

        # Placeholder for Chart
        st.subheader("📈 Price Chart Coming Soon!")
def show_strategies(st):
    """
    Displays the trading strategy UI in Streamlit.
    """
    apply_custom_css()
    st.title("📈 Strategy Lab")

    # Default date values
    default_start_date = datetime(2023, 1, 1)
    default_end_date = datetime.today() - timedelta(days=1)

    # Input UI (Organized in 2 Rows)
    col1, col2, col3 = st.columns(3)
    with col1:
        stock_symbol = st.text_input("Stock Symbol", "NVDA")
        is_valid, message = helpers.validate_input(stock_symbol)
        if not is_valid and stock_symbol:
            st.error(message)
    with col2:
        start_date = st.date_input("Start Date", default_start_date)
    with col3:
        end_date = st.date_input("End Date", default_end_date)

    col4, col5, col6, col7 = st.columns(4)
    with col4:
        timeframe = st.selectbox("Timeframe", ["1Day", "1Hour", "15Min", "5Min"], index=0)
    with col5:
        num_stocks = st.number_input("Trade Size", min_value=1, value=100, step=1)
    with col6:
        strategy_selected = st.selectbox("Select Strategy", ["RSI Strategy", "Momentum", "Breakout"], index=0)
    with col7:
        stop_loss_str = st.selectbox("Stop Loss (%)", ["10%", "15%", "25%", "50%", "None"], index=1)
        profit_target_str = st.selectbox("Profit Target (%)", ["10%", "15%", "25%", "50%", "None"], index=2)

    # Convert Dropdown Selection to Decimal (or None)
    stop_loss = None if stop_loss_str == "None" else int(stop_loss_str.replace("%", "")) / 100
    profit_target = None if profit_target_str == "None" else int(profit_target_str.replace("%", "")) / 100

    # Only proceed if the stock symbol is valid
    if not is_valid and stock_symbol:
        st.stop()

    st.write("")  # Spacer

    # RSI Strategy Inputs
    if strategy_selected == "RSI Strategy":
        with st.expander("📉 RSI Strategy", expanded=True):
            rsi(st, stock_symbol, start_date, end_date, timeframe, num_stocks, stop_loss, profit_target)
    elif strategy_selected == "Momentum":
        with st.expander("🚀 Momentum Strategy", expanded=True):
            st.write("Coming soon!")
    elif strategy_selected == "Breakout":
        with st.expander("📈 Breakout Strategy", expanded=True):
            st.write("Coming soon!")