import streamlit as st
import os
from dotenv import load_dotenv
import botsystem
import Chatbot as cb_func
import Strategies as strat_func
import Analysis as analys_func
import Picks as picks_func
import News as news_func
import Options as options_func


load_dotenv()

@st.cache_resource
def configure_models(model_choice):
    """Configures the selected model (Gemini or OpenAI)."""
    if model_choice == "OpenAI":
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

def initialize_session_state():
    """Initializes session state variables if not already set."""
    if "selected_tab" not in st.session_state:
        st.session_state.selected_tab = "ChatBot"
    if "chat_log" not in st.session_state:
        st.session_state.chat_log = [{"role": "system", "content": botsystem.prompt}]
    if "model_choice" not in st.session_state:
        st.session_state.model_choice = "OpenAI"

def sidebar_nav():
    """
    Displays each tab name in the sidebar as:
      - A clickable button if it is NOT selected
      - A static highlighted 'button' if it IS selected
    """
    st.sidebar.markdown(
        """
        <style>
        div[data-testid="stSidebar"] div.stButton > button {
            background-color: #fafafa;
            color: #333;
            border: 1px solid #ccc;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: 500;
            margin-bottom: 8px;
            cursor: pointer;
        }
        div[data-testid="stSidebar"] div.stButton > button:hover {
            background-color: #ddd;
        }
        .selected-tab {
            background-color: #aadffd;
            border: 1px solid #3399ff;
            color: #000;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: 500;
            margin-bottom: 8px;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    tabs = ["ChatBot", "Strategies", "Analysis", "News", "Picks", "Options"]
    for tab in tabs:
        if tab == st.session_state.selected_tab:
            # Highlighted tab (non-clickable)
            st.sidebar.markdown(
                f"<div class='selected-tab'>{tab}</div>",
                unsafe_allow_html=True
            )
        else:
            # Actual Streamlit button for unselected tabs
            if st.sidebar.button(tab, key=f"btn_{tab}"):
                st.session_state.selected_tab = tab
                st.rerun()

def main():
    st.set_page_config(page_title="Stock Analysis Dashboard", layout="wide")

    initialize_session_state()
    api_key, llm, model_name = configure_models(st.session_state.model_choice)

    # Sidebar for tab navigation
    sidebar_nav()

    # Render content based on selected tab
    tab = st.session_state.selected_tab
    if tab == "ChatBot":
        cb_func.show_chatbot_page(st, api_key, llm, model_name)
    elif tab == "Strategies":
        strat_func.show_strategies(st)
    elif tab == "Analysis":
        analys_func.show_analysis(st)
    elif tab == "News":
        news_func.show_news(st)
    elif tab == "Picks":
        picks_func.show_picks(st)
    elif tab == "Options":
        options_func.show_options(st)


if __name__ == "__main__":
    main()
