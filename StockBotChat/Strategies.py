import streamlit as st

def show_strategies(st):
    st.title("Strategies")
    st.write("Get Stock trading strategies.")
    strategy_choice = st.selectbox("Select a Strategy", ["Moving Average Crossover", "RSI Strategy", "MACD Strategy"])
    st.write(f"Selected Strategy: {strategy_choice}")
