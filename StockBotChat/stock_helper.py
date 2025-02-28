import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import yfinance as yf

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
