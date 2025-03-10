import alpaca_trade_api as tradeapi
import os
import requests
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, "https://paper-api.alpaca.markets", api_version="v2")

@st.cache_data
def is_valid_stock_symbol(symbol):
    """
    Check if the provided stock symbol is valid using Alpaca API.

    Args:
        symbol (str): The stock symbol to validate (e.g., "AAPL").

    Returns:
        bool: True if the symbol is valid, False otherwise.
        str: Error message if invalid, empty string if valid.
    """
    try:
        # Fetch asset information for the symbol
        asset = api.get_asset(symbol)
        if not asset.tradable:
            return False, f"Symbol {symbol} is not tradable."
        if asset.status != "active":
            return False, f"Symbol {symbol} is not active."
        return True, ""
    except alpaca_trade_api.rest.APIError as e:
        return False, f"Invalid stock symbol: {symbol} not found."
    except requests.exceptions.RequestException as e:
        return False, f"Network error while validating symbol: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error while validating symbol: {str(e)}"

def validate_input(symbol):
    """
    Validate the stock symbol input and provide feedback.

    Args:
        symbol (str): The stock symbol to validate.

    Returns:
        bool: True if valid, False otherwise.
        str: Feedback message for the user.
    """
    if not symbol or not symbol.strip():
        return False, "Stock symbol cannot be empty."
    is_valid, message = is_valid_stock_symbol(symbol.upper())
    return is_valid, message