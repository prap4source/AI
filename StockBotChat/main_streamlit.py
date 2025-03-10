import streamlit as st
import os
from dotenv import load_dotenv
import botsystem

# Importing individual modules
import Chatbot as cb_func
import Strategies as strat_func
import Picks as picks_func
import News as news_func
import Options as options_func
import Markets as market_func

load_dotenv()

# --- Configuration ---
@st.cache_resource
def configure_models(model_choice):
    """Configures the selected model (OpenAI)."""
    if model_choice == "OpenAI":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("⚠️ Please set the OPENAI_API_KEY environment variable.")
            st.stop()
        model = os.getenv("OPENAI_MODEL")
        if not model:
            st.error("⚠️ Please set the OPENAI_MODEL environment variable.")
            st.stop()
        return api_key, model, "OpenAI"
    else:
        st.error("⚠️ Invalid model choice.")
        st.stop()

# --- Initialize Session State ---
def initialize_session_state():
    """Initializes session state variables if not already set."""
    if "selected_tab" not in st.session_state:
        st.session_state.selected_tab = "Markets"
    if "chat_log" not in st.session_state:
        st.session_state.chat_log = [{"role": "system", "content": botsystem.prompt}]
    if "model_choice" not in st.session_state:
        st.session_state.model_choice = "OpenAI"

# --- Sidebar Navigation with Hover Effect ---
def sidebar_nav():
    """
    Creates a sleek, collapsible sidebar that expands on hover.
    """

    st.sidebar.markdown(
        """
        <style>
        /* Hide sidebar by default */
        [data-testid="stSidebar"] {
            width: 60px !important;
            transition: width 0.3s ease-in-out;
            background-color: #212529 !important; /* Dark sidebar */
        }

        /* Expand sidebar on hover */
        [data-testid="stSidebar"]:hover {
            width: 250px !important;
        }

        /* Sidebar text color */
        [data-testid="stSidebarNav"] span {
            color: white !important;
        }

        /* Sidebar Buttons: Consistent width & center alignment */
        .sidebar-btn {
            display: flex;
            align-items: center;
            justify-content: left;
            width: 100%;
            height: 40px;
            padding: 10px;
            margin-bottom: 8px;
            font-size: 16px;
            font-weight: 500;
            color: white;
            border-radius: 5px;
            background-color: #343A40;
            cursor: pointer;
            transition: 0.3s ease;
        }

        /* Hover effect */
        .sidebar-btn:hover {
            background-color: #495057 !important;
        }

        /* Selected Tab Highlight */
        .selected-tab {
            background-color: #FF5C8D !important; /* Pink highlight */
            font-weight: bold;
        }

        /* Ensuring icons and text are aligned */
        .sidebar-btn span {
            margin-left: 10px;
            display: inline-block;
        }

        </style>
        """,
        unsafe_allow_html=True
    )

    # Tab Configuration with Icons
    tabs = {
        "Markets": "📊",
        "ChatBot": "🤖",
        "Stock Screener": "⭐",
        "Strategy Lab": "📈",
        "News": "📰",
        "Options": "💹",
    }

    # Sidebar Header
    st.sidebar.markdown("<h2 style='color:white; text-align:center;'>📌 Stock Dashboard</h2>", unsafe_allow_html=True)

    # Display Tabs with Proper Alignment & Click Handling
    for tab, icon in tabs.items():
        is_selected = st.session_state.selected_tab == tab

        # Use only buttons for switching, without HTML duplication
        if st.sidebar.button(f"{icon} {tab}", key=f"btn_{tab}"):
            st.session_state.selected_tab = tab  # Store selected tab
            st.rerun()  # Refresh UI

# --- Main Application ---
def main():
    """Runs the Streamlit app."""
    st.set_page_config(page_title="Stock Analysis Dashboard", layout="wide")

    initialize_session_state()
    sidebar_nav()

    # Render Content Based on Selected Tab
    tab = st.session_state.selected_tab

    if tab == "Markets":
        market_func.show_sentiment(st)
    elif tab == "ChatBot":
        api_key, llm, model_name = configure_models(st.session_state.model_choice)
        cb_func.show_chatbot_page(st, api_key, llm, model_name)
    elif tab == "Stock Screener":
        picks_func.show_picks(st)
    elif tab == "Strategy Lab":
        strat_func.show_strategies(st)
    elif tab == "News":
        news_func.show_news(st)
    elif tab == "Options":
        options_func.show_options(st)


if __name__ == "__main__":
    main()
