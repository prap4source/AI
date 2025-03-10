import pandas as pd

# Function to fetch S&P 500 symbols from Wikipedia
def get_sp500_symbols():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        sp500_table = pd.read_html(url)[0]
        sp500_symbols = sp500_table["Symbol"].tolist()
        # Replace any problematic characters (e.g., '.' in BRK.B to BRK-B)
        sp500_symbols = [symbol.replace(".", "-") for symbol in sp500_symbols]
        return sp500_symbols
    except Exception as e:
        print(f"Error fetching S&P 500 symbols: {str(e)}")
        # Fallback to a partial list if fetching fails
        return [
            "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B", "JPM", "JNJ",
            "V", "PG", "MA", "HD", "DIS", "PYPL", "NFLX", "ADBE", "CRM", "INTC",
            "CSCO", "PFE", "WMT", "KO", "PEP", "MRK", "T", "VZ", "CMCSA", "NKE",
            "ABT", "ACN", "ADSK", "AIG", "ALL", "AMGN", "AXP", "BA", "BAC", "BBY",
            "BDX", "BIIB", "BK", "BLK", "BMY", "C", "CAT", "CL", "COF", "COP",
            # Add more as a fallback; ideally, this will be populated dynamically
        ]

# Function to fetch Nasdaq 100 symbols from Wikipedia
def get_nasdaq100_symbols():
    try:
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        nasdaq100_table = pd.read_html(url, match="Ticker")[0]  # Match the table with 'Ticker' column
        nasdaq100_symbols = nasdaq100_table["Ticker"].tolist()
        return nasdaq100_symbols
    except Exception as e:
        print(f"Error fetching Nasdaq 100 symbols: {str(e)}")
        # Fallback to a partial list if fetching fails
        return [
            "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "ADBE", "NFLX", "CSCO",
            "INTC", "PEP", "COST", "CMCSA", "AMD", "QCOM", "TXN", "AMGN", "SBUX", "ISRG",
            "MDLZ", "GILD", "ADP", "INTU", "BKNG", "FISV", "LRCX", "KHC", "MNST", "REGN",
            # Add more as a fallback; ideally, this will be populated dynamically
        ]

# Define stock universes
sp500_symbols = get_sp500_symbols()
nasdaq100_symbols = get_nasdaq100_symbols()

stock_universes = {
    "S&P 500": sp500_symbols,
    "Nasdaq 100": nasdaq100_symbols
}