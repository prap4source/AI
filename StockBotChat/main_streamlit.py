import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
@st.cache_resource
def configure_models(model_choice):
    """Configures the selected model (Gemini or OpenAI)."""
    if model_choice == "Gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.error("Please set the GEMINI_API_KEY environment variable.")
            st.stop()
        model = os.getenv("GEMINI_MODEL")
        if not model:
            st.error("Please set the GEMINI_MODEL environment variable.")
            st.stop()
        return api_key, model, "Gemini"
    elif model_choice == "OpenAI":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("Please set the OPENAI_API_KEY environment variable.")
            st.stop()
        model = os.getenv("OPENAI_MODEL")
        if not model:
            st.error("Please set the OPENAI_MODEL environment variable.")
            st.stop()
        return api_key, model, "OpenAI"
    else:
        st.error("Invalid model choice.")
        st.stop()

# --- Session State Management ---
def initialize_session_state(model_choice):
    """Initializes session state variables."""
    if 'model_choice' not in st.session_state or st.session_state.model_choice != model_choice:
        st.session_state.chat_log = []
        st.session_state.messages = []
        st.session_state.model_choice = model_choice

# --- Display Functions ---
def display_title_bar():
    """Displays the title bar with a fancy design."""
    st.markdown(
        """
        <style>
        .title-bar {
            background-color: #4A90E2;
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="title-bar"><h1>✨ Stock Bot Chat 🤖</h1></div>', unsafe_allow_html=True)

def display_chat_messages():
    """Displays chat messages from session state."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- Chatbot Logic ---
def handle_user_input(api_key, llm, model_name):
    """Handles user input and generates responses."""
    if prompt := st.chat_input("Enter your message here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)

        if model_name == "Gemini":
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(llm)
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
        elif model_name == "OpenAI":
            openai = OpenAI(api_key=api_key)
            st.session_state.chat_log.append({"role": "user", "content": prompt})
            try:
                response = openai.chat.completions.create(
                    model=llm,
                    messages=st.session_state.chat_log,
                    temperature=0.6
                )
                ai_response = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                st.chat_message("assistant").markdown(ai_response)
                st.session_state.chat_log.append({"role": "assistant", "content": ai_response})
            except Exception as e:
                st.error(f"An error occurred: {e}")

# --- Main App ---
def main():
    """Main function to run the Streamlit app."""
    model_choice = st.selectbox("Select AI Model:", ["Gemini", "OpenAI"])
    initialize_session_state(model_choice)
    api_key, llm, model_name = configure_models(model_choice)
    display_title_bar()
    display_chat_messages()
    handle_user_input(api_key, llm, model_name)

if __name__ == "__main__":
    main()