import streamlit as st
import backtest
import pine
import paper
import yfinance as yf
from datetime import datetime, timedelta
import helpers
import plotly.express as px  # For visualization
import pandas as pd


def apply_custom_css():
    """Applies custom CSS to adjust layout and remove unnecessary padding."""
    st.markdown("""
        <style>
        .main .block-container { padding-left: 0 !important; padding-right: 0 !important; }
        div[data-testid="stVerticalBlock"] > div { padding-left: 0 !important; padding-right: 0 !important; }
        div[data-testid="column"] { padding-left: 0 !important; padding-right: 0 !important; }
        </style>
    """, unsafe_allow_html=True)


def categorize_sell_reason(reason):
    """Categorizes sell reasons into a standardized label."""
    if "Stop Loss" in reason:
        return "Stop Loss"
    elif "RSI >" in reason:
        return "RSI > 70"
    elif "Profit Target" in reason:
        return "Profit Target"
    return "Other"


def rsi_strategy(st, stock_symbol, start_date, end_date, timeframe, num_stocks, stop_loss, profit_target):
    """
    Runs the RSI backtest strategy with user-configurable SL & Profit Target.
    """
    st.write("This strategy Buys when RSI crosses over 40 and Sells when RSI hits 70")

    # RSI Period Input
    rsi_period = st.slider("RSI Period", 5, 30, 14)
    params = {
        "rsi_period": rsi_period,
        "qty": num_stocks,
        "timeframe": timeframe,
        "stop_loss": stop_loss,
        "profit_target": profit_target
    }

    # ✅ Button Row (Backtest, Pine Script, Paper Trade)
    col1, col2, col3 = st.columns(3)

    if col1.button("📉 Run Backtest", key="run_backtest"):
        with st.spinner(f"🔄 Running Backtest for {stock_symbol}..."):
            trades_summary_df, total_profit = backtest.run_backtest_rsi(
                st,
                stock_symbol, start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"), params)
        st.success("✅ Backtest Completed")

        # Display Total Profit
        if total_profit is not None:
            st.markdown(f"### 💰 Total Profit: ${total_profit:.2f}")

        # ✅ Win/Loss Summary (Now included after Total Profit)
        closed_trades_df = trades_summary_df[trades_summary_df["Sell Date"] != "Open"]
        if not closed_trades_df.empty:
            total_trades = len(closed_trades_df)
            winners = len(closed_trades_df[closed_trades_df["Profit ($)"] > 0])
            win_percentage = (winners / total_trades) * 100 if total_trades > 0 else 0
            reason_counts = closed_trades_df["Sell Reason"].apply(categorize_sell_reason).value_counts()
            reason_percentages = (reason_counts / total_trades * 100).round(2)

            st.subheader("📊 Win/Loss Summary")
            col1, col2 = st.columns([1, 2])

            with col1:
                st.write("**Trade Metrics:**")
                st.write(f"Winning Trades: {winners}/{total_trades}")
                st.write(f"Win Rate: {win_percentage:.2f}%")
                if not reason_counts.empty:
                    st.write("**Sell Reason Distribution:**")
                    for reason, count in reason_counts.items():
                        st.write(f"{reason}: {count} trades")

            with col2:
                if not reason_percentages.empty:
                    fig = px.pie(
                        names=reason_percentages.index,
                        values=reason_percentages.values,
                        title="Distribution of Sell Reasons",
                        color=reason_percentages.index,
                        color_discrete_map={"Stop Loss": "#EF553B", "RSI > 70": "#00CC96",
                                            "Profit Target": "#AB63FA", "Other": "#636EFA"}
                    )
                    fig.update_traces(textinfo="percent+label", textposition="inside")
                    st.plotly_chart(fig, use_container_width=True)

        # Display Trade History Table
        if trades_summary_df is not None and not trades_summary_df.empty:
            st.subheader("📜 Trade History")
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

    if col2.button("📜 Generate Pine Script", key="generate_pine"):
        pine_script = pine.generate_rsi_strategy("RSI", params)
        st.code(pine_script, language="pinescript")

    if col3.button("📈 Execute Paper Trade", key="execute_paper_trade"):
        success, message = paper.execute_paper_trade(
            stock_symbol, timeframe, "RSI", params,
            backtest.run_backtest_rsi
        )
        if success:
            st.success(message)
        else:
            st.error(message)

def calculate_sip_roi(ticker, start, end, monthly):
    """
    Calculates the SIP (Systematic Investment Plan) returns.
    """
    try:
        data = yf.download(ticker, start, end)
        if data.empty:
            return f"⚠️ No data found for {ticker} in the given period."

        monthly_data = data.resample('MS').first()
        monthly_closes = monthly_data['Close'].squeeze()
        monthly_closes = pd.to_numeric(monthly_closes, errors='coerce')

        total_investment = 0
        shares_held = 0

        for _, close_price in zip(monthly_closes.index, monthly_closes):
            total_investment += monthly
            shares_bought = monthly / close_price
            shares_held += shares_bought

        close_today = yf.Ticker(ticker).info.get("regularMarketPreviousClose", monthly_closes.iloc[-1])
        final_value_today = shares_held * close_today
        roi_percentage = ((final_value_today - total_investment) / total_investment) * 100

        return f"💰 **Total Investment:** ${total_investment:,.2f}\n📊 **Final Portfolio Value:** ${final_value_today:,.2f}\n📈 **SIP Growth:** {roi_percentage:.2f}%"

    except Exception as e:
        return f"❌ Error calculating SIP returns: {e}"


def show_sip_returns(st, ticker, start_date, end_date):
    """Displays the SIP Returns calculation with start and end date passed."""
    st.subheader("📊 SIP Returns Calculator")
    monthly_investment = st.number_input("Monthly Investment ($)", min_value=1, value=1000)

    if st.button("📈 Calculate SIP Returns"):
        with st.spinner(f"🔄 Calculating SIP returns for {ticker}..."):
            sip_result = calculate_sip_roi(ticker, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), monthly_investment)
        st.markdown(sip_result, unsafe_allow_html=True)


def show_strategies(st):
    """
    Displays the trading strategy UI in Streamlit.
    """
    apply_custom_css()
    st.title("📈 Strategy Lab")

    # Default date values
    default_start_date = datetime(2023, 1, 1)
    default_end_date = datetime.today() - timedelta(days=1)

    col1, col2, col3 = st.columns(3)
    with col1:
        stock_symbol = st.text_input("Stock Symbol", "NVDA")
    with col2:
        start_date = st.date_input("Start Date", default_start_date)
    with col3:
        end_date = st.date_input("End Date", default_end_date)

    col4, col5 = st.columns(2)
    with col4:
        timeframe = st.selectbox("Timeframe", ["1Day", "1Hour", "15Min", "5Min"], index=0)
    with col5:
        num_stocks = st.number_input("Trade Size", min_value=1, value=100, step=1)

    with st.expander("📉 RSI Strategy", expanded=False):
        rsi_strategy(st, stock_symbol, start_date, end_date, timeframe, num_stocks, 0.10, 0.30)

    with st.expander("💰 SIP Returns Calculator", expanded=False):
        show_sip_returns(st, stock_symbol, start_date, end_date)
