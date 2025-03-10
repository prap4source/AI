import requests
import os
import pandas as pd
import plotly.graph_objects as go

# Function to fetch Fear & Greed Index from RapidAPI
def fetch_fear_and_greed_index(st):
    RAPID_API_KEY = os.getenv('RAPID_API_KEY')  # Store your API key in environment variables
    url = "https://fear-and-greed-index.p.rapidapi.com/v1/fgi"
    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "fear-and-greed-index.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data['fgi']
    else:
        st.error("⚠️ Failed to fetch Fear & Greed Index data.")
        return None


# Function to determine the color based on sentiment
def get_sentiment_color(sentiment):
    if "Extreme Fear" in sentiment:
        return "red"
    elif "Fear" in sentiment:
        return "orange"
    elif "Neutral" in sentiment:
        return "gray"
    elif "Greed" in sentiment:
        return "green"
    elif "Extreme Greed" in sentiment:
        return "darkgreen"
    return "blue"


# Function to display the Fear & Greed Index in Streamlit (Compact Version)
def show_sentiment(st):
    st.markdown("<h3 style='text-align: center;'>📊 Fear & Greed Index</h3>", unsafe_allow_html=True)

    index_data = fetch_fear_and_greed_index(st)

    if index_data:
        sentiment = index_data['now']['valueText']
        sentiment_color = get_sentiment_color(sentiment)

        # --- Layout and Styling ---

        # Use columns for better layout
        col1, col2 = st.columns([1, 2])  # Adjust ratio as needed

        # Display current sentiment with color
        with col1:
            st.markdown(
                f"<div style='background-color: {sentiment_color}; color: white; padding: 10px; border-radius: 5px; text-align: center;'>"
                f"<h4 style='margin: 0;'>Current Sentiment:</h4>"
                f"<p style='font-size: 1.2em; margin: 0;'>{sentiment}</p>"
                f"</div>",
                unsafe_allow_html=True
            )

        # Display gauge chart
        with col2:
            gauge_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=index_data['now']['value'],
                title={'text': "Fear & Greed Gauge"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': sentiment_color},
                    'steps': [
                        {'range': [0, 25], 'color': "red"},
                        {'range': [25, 50], 'color': "orange"},
                        {'range': [50, 75], 'color': "green"},
                        {'range': [75, 100], 'color': "darkgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': index_data['now']['value']
                    }
                }
            ))
            st.plotly_chart(gauge_fig, use_container_width=True)

        # Display bar chart
        df = pd.DataFrame({
            'Time': ['Now', 'Prev Close', '1 Week', '1 Month', '1 Year'],
            'Value': [
                index_data['now']['value'],
                index_data['previousClose']['value'],
                index_data['oneWeekAgo']['value'],
                index_data['oneMonthAgo']['value'],
                index_data['oneYearAgo']['value']
            ]
        })

        fig = go.Figure(data=[
            go.Bar(
                x=df['Time'],
                y=df['Value'],
                marker=dict(color=['red', 'orange', 'gray', 'green', 'darkgreen']),
                text=df['Value'],
                textposition='auto'
            )
        ])
        fig.update_layout(
            title="📉 Fear & Greed Index Over Time",
            xaxis_title="",
            yaxis_title="Index Value",
            yaxis=dict(range=[0, 100]),
            template="plotly_white",
            height=300,
            margin=dict(l=30, r=30, t=40, b=30)
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("⚠️ Could not retrieve Fear and Greed Index data at this time.")