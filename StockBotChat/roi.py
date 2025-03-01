import yfinance as yf
from datetime import datetime
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

def calculate_sip_roi(symbol='TQQQ', start="2015-01-01", end="2025-02-28", investment_per_month=1000):
    """
    Calculates the Return on Investment (ROI) for a Systematic Investment Plan (SIP).

    Args:
        symbol (str): The stock ticker symbol.
        start (str): The start date for the investment period (YYYY-MM-DD).
        end (str): The end date for the investment period (YYYY-MM-DD).
        investment_per_month (int): The monthly investment amount.

    Returns:
        str: A formatted string containing the ROI details.
    """

    ticker_symbol = symbol
    data = yf.download(ticker_symbol, start, end)
    monthly_data = data.resample('MS').first()
    monthly_closes = monthly_data['Close'].squeeze()
    monthly_closes = pd.to_numeric(monthly_closes, errors='coerce')

    total_investment = 0
    shares_held = 0

    investment_df = pd.DataFrame(columns=['Date', 'Investment', 'Current Value', 'Shares Bought', 'Close Price', 'Current ROI'])

    for date, close_price in zip(monthly_closes.index, monthly_closes):
        trading_time = datetime(date.year, date.month, date.day, 9, 30)
        actual_investment = investment_per_month
        total_investment += actual_investment #Correct placement.
        shares_bought = actual_investment / close_price
        shares_held += shares_bought
        curr_val = shares_held * close_price
        if total_investment !=0 : #add check to prevent zero division error.
            curr_roi = ((curr_val - total_investment) / total_investment) * 100
        else:
            curr_roi = 0

        new_row = {
            'Date': date.strftime('%Y-%m-%d'),
            'Investment': actual_investment,
            'Current Value': curr_val,
            'Shares Bought': shares_bought,
            'Close Price': close_price,
            'Current ROI': curr_roi
        }
        investment_df = pd.concat([investment_df, pd.DataFrame([new_row])], ignore_index=True)

    ticker = yf.Ticker(ticker_symbol).info
    close_today = ticker['regularMarketPreviousClose']
    final_value_till_thatday = shares_held * monthly_closes.iloc[-1]
    final_value_today = shares_held * close_today

    roi_percentage_today = ((final_value_today - total_investment) / total_investment) * 100
    roi_percentage_till_last = ((final_value_till_thatday - total_investment) / total_investment) * 100
    msg = f"Stock: {ticker_symbol} Period from {start} to {end} Monthly:${investment_per_month} ROI:{roi_percentage_till_last:.2f}% Investment:${total_investment:.2f} Now:${final_value_today:.2f}"
    return msg

if __name__ == "__main__":
    for script in ['TQQQ', 'QQQ', 'NVDA']:
        print(calculate_sip_roi(script))