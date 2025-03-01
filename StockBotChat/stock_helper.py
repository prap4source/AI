import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

def calculate_sip_roi(ticker):
    start="2015-01-01"
    end="2025-02-24"
    investment_per_month=1000
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

    data = yf.download(ticker, start, end)
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

    ticker_symbol = yf.Ticker(ticker).info
    close_today = ticker_symbol['regularMarketPreviousClose']
    final_value_till_thatday = shares_held * monthly_closes.iloc[-1]
    final_value_today = shares_held * close_today

    roi_percentage_today = ((final_value_today - total_investment) / total_investment) * 100
    roi_percentage_till_last = ((final_value_till_thatday - total_investment) / total_investment) * 100
    msg = f"{ticker} from {start} to {end}  ROI:{roi_percentage_till_last:.2f}% Monthly:${investment_per_month:.2f}"
    return msg

def get_stock_price(ticker):
    """Gets the latest stock price."""
    price = yf.Ticker(ticker).history(period='1y').iloc[-1].Close
    return f"The current stock price of {ticker} is {price:.2f}"

def calculate_SMA(ticker, window):
    """Calculates the Simple Moving Average."""
    data = yf.Ticker(ticker).history(period='1y').Close
    sma = data.rolling(window=int(window)).mean().iloc[-1]
    return f"The {window}-day SMA of {ticker} is {sma:.2f}"

def calculate_EMA(ticker, window):
    """Calculates the Exponential Moving Average."""
    data = yf.Ticker(ticker).history(period='1y').Close
    ema = data.ewm(span=int(window), adjust=False).mean().iloc[-1]
    return f"The {window}-day EMA of {ticker} is {ema:.2f}"

def calculate_RSI(ticker):
    """Calculates the Relative Strength Index."""
    data = yf.Ticker(ticker).history(period='1y').Close
    delta = data.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ema_up = up.ewm(com=13, adjust=False).mean()
    ema_down = down.ewm(com=13, adjust=False).mean()
    rs = ema_up / ema_down
    rsi = 100 - (100 / (1 + rs)).iloc[-1]
    return f"The RSI of {ticker} is {rsi:.2f}"

def calculate_MACD(ticker):
    """Calculates the Moving Average Convergence Divergence."""
    data = yf.Ticker(ticker).history(period='1y').Close
    short_ema = data.ewm(span=12, adjust=False).mean()
    long_ema = data.ewm(span=26, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    return f"The MACD of {ticker} is MACD: {macd.iloc[-1]:.2f}, Signal: {signal.iloc[-1]:.2f}, Histogram: {histogram.iloc[-1]:.2f}"

def plot_stock_price(ticker):
    """Plots the stock price over the last year."""
    data = yf.Ticker(ticker).history(period='1y').Close
    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data)
    plt.title(f'{ticker} Stock Price Over Last Year')
    plt.xlabel('Date')
    plt.ylabel('Stock Price ($)')
    plt.grid(True)
    plt.savefig('stock.png')
    plt.close()

functions = [
    {
        'name': 'calculate_sip_roi',
        'description': 'Gets the ROI of stock',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The ROI of a stock.'
                },
            },
            'required': ['ticker'],
        },
    },
    {
        'name': 'get_stock_price',
        'description': 'Gets the latest stock price given the ticker symbol of a company',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol of a company (e.g., AAPL for Apple).'
                },
            },
            'required': ['ticker'],
        },
    },
    {
        'name': 'calculate_SMA',
        'description': 'Calculate the simple moving average of a given stock ticker and a window',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol of a company (e.g., AAPL for Apple).'
                },
                'window': {
                    'type': 'string',
                    'description': 'The timeframe to consider when calculating the SMA'
                },
            },
            'required': ['ticker', 'window'],
        },
    },
    {
        'name': 'calculate_EMA',
        'description': 'Calculate the exponential moving average of a given stock ticker and a window',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol of a company (e.g., AAPL for Apple).'
                },
                'window': {
                    'type': 'string',
                    'description': 'The timeframe to consider when calculating the EMA'
                },
            },
            'required': ['ticker', 'window'],
        },
    },
    {
        'name': 'calculate_RSI',
        'description': 'Calculates the RSI of the given stock ticker',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol of a company (e.g., AAPL for Apple).'
                },
            },
            'required': ['ticker'],
        },
    },
    {
        'name': 'calculate_MACD',
        'description': 'Calculates the MACD of the given stock ticker',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol of a company (e.g., AAPL for Apple).'
                },
            },
            'required': ['ticker'],
        },
    },
    {
        'name': 'plot_stock_price',
        'description': 'Plots the stock price for the last year of the given stock ticker',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol of a company (e.g., AAPL for Apple).'
                },
            },
            'required': ['ticker'],
        },
    },
]

