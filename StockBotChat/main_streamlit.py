import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    st.error("Please set the GEMINI_API_KEY environment variable.")
    st.stop()
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-1.5-pro-latest')

st.title("StockBotChat")

if 'chat_log' not in st.session_state:
    st.session_state.chat_log = [{'role': 'user', 'parts': ["You are a helpful assistant."]}]

if 'messages' not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    st.session_state.chat_log.append({'role': 'user', 'parts': [prompt]})

    try:
        response = model.generate_content(
            st.session_state.chat_log,
            stream=False,
            generation_config=genai.types.GenerationConfig(temperature=0.6)
        )
        ai_response = response.text

        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        st.chat_message("assistant").markdown(ai_response)

        st.session_state.chat_log.append({'role': 'assistant', 'parts': [ai_response]})

    except Exception as e:
        st.error(f"An error occurred: {e}")