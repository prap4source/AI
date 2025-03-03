import yfinance as yf
import pandas as pd
from datetime import datetime


def calculate_sip_roi(ticker, start, end, monthly):
    """
    Calculates the SIP (Systematic Investment Plan) returns.

    Args:
        ticker (str): The stock ticker symbol.
        start (str): The start date for the investment period (YYYY-MM-DD).
        end (str): The end date for the investment period (YYYY-MM-DD).
        monthly (int): The monthly investment amount.

    Returns:
        str: A formatted string containing SIP return details.
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

        for date, close_price in zip(monthly_closes.index, monthly_closes):
            total_investment += monthly
            shares_bought = monthly / close_price
            shares_held += shares_bought

        # Fetch latest stock price
        ticker_info = yf.Ticker(ticker).info
        close_today = ticker_info.get("regularMarketPreviousClose", monthly_closes.iloc[-1])

        final_value_today = shares_held * close_today
        roi_percentage = ((final_value_today - total_investment) / total_investment) * 100

        # Beautified result for Streamlit
        result = (
            f"### 📈 **{ticker} SIP Returns**\n"
            f"✅ **SIP Growth:** **{roi_percentage:.2f}%**  \n"
            f"💰 **Total Investment:** **${total_investment:,.2f}**  \n"
            f"📊 **Final Portfolio Value:** **${final_value_today:,.2f}**"
        )

        return result  # Markdown formatted

    except Exception as e:
        return f"❌ Error calculating SIP returns: {e}"


def show_analysis(st):
    """Displays stock trading analysis, with SIP Returns as one of the options."""
    st.title("Stock Analysis")
    st.write("Choose an analysis type and enter the required details.")

    analysis_options = ["Select Analysis", "SIP Returns", "Technical Indicators", "Stock Trends"]
    selected_analysis = st.selectbox("Choose Analysis Type:", analysis_options)

    ticker = st.text_input("Enter Ticker Symbol (e.g., AAPL)", "AAPL")

    if selected_analysis == "SIP Returns":
        start = st.date_input("Start Date", datetime(2015, 1, 1))
        end = st.date_input("End Date", datetime(2025, 2, 24))
        monthly = st.number_input("Monthly Investment ($)", min_value=1, value=1000)

        if st.button("Analyze SIP Returns"):
            if not ticker.strip():
                st.warning("⚠️ Please enter a valid stock ticker.")
                return

            sip_result = calculate_sip_roi(ticker, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'), monthly)
            st.markdown(sip_result, unsafe_allow_html=True)  # Display with markdown

    elif selected_analysis == "Technical Indicators":
        st.write("📊 Technical indicators like SMA, EMA, RSI, and MACD will be implemented here.")

    elif selected_analysis == "Stock Trends":
        st.write("📈 Trend analysis for stock performance over time will be displayed here.")
