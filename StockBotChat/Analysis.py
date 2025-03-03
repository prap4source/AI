import streamlit as st

def show_analysis(st):
    st.title("analysis")
    st.write("Get Stock trading analysis.")
    ticker = st.text_input("Enter Ticker Symbol", "AAPL")
    st.button("Analyze")
