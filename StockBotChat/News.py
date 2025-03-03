import requests
import streamlit as st
import os

# 🔹 Replace this with your own Alpha Vantage API Key
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "YOUR_API_KEY_HERE")

def get_stock_news(ticker):
    """Fetches latest summarized news for a stock using Alpha Vantage API."""
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if "feed" not in data:
            return f"❌ No news available for {ticker} or API limit reached."

        news_list = []
        for article in data["feed"][:5]:  # Get top 5 articles
            title = article.get("title", "No title available")
            link = article.get("url", "#")
            source = article.get("source", "Unknown Source")
            summary = article.get("summary", "No summary available")

            news_list.append({"title": title, "link": link, "source": source, "summary": summary})

        return news_list if news_list else None

    except Exception as e:
        return f"❌ Error fetching news: {e}"

def show_news(st):
    """Displays stock news in a Streamlit app."""
    st.title("Stock News")
    st.write("Get summarized stock news from Alpha Vantage.")

    ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, TSLA, MSFT):", key="stock_news_ticker")

    if st.button("Get News"):
        if not ticker.strip():
            st.warning("⚠️ Please enter a valid stock ticker.")
            return

        news = get_stock_news(ticker)

        if isinstance(news, str):  # Error case
            st.error(news)
        elif not news:
            st.warning(f"⚠️ No news found for {ticker}. Try another ticker.")
        else:
            for article in news:
                st.markdown(f"### [{article['title']}]({article['link']})")
                st.write(f"📰 {article['source']}")
                st.write(f"📌 **Summary:** {article['summary']}")
                st.write("---")  # Separator for articles