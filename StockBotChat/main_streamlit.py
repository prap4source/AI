import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import StockBot as sb_func  # Renamed from `import stock_helper as st_func`
import json
import botsystem

# Mapping of function names to actual implementations
available_functions = {
    'calculate_sip_roi': sb_func.calculate_sip_roi,
    'get_stock_price': sb_func.get_stock_price,
    'calculate_SMA': sb_func.calculate_SMA,
    'calculate_EMA': sb_func.calculate_EMA,
    'calculate_RSI': sb_func.calculate_RSI,
    'calculate_MACD': sb_func.calculate_MACD,
    'plot_stock_price': sb_func.plot_stock_price,
}

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
        st.session_state.selected_tab = "Stockbot"
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

    tabs = ["Stockbot", "Strategies", "Analysis", "News", "Picks", "Options"]
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

def show_chatbot_page(api_key, llm, model_name):
    """Displays the chatbot conversation on the main page, with user input at the bottom."""
    st.title("Chatbot")
    st.write("Below is the conversation with your stock bot. Enter your question and press **Send** or **Enter**.")

    # Display existing conversation
    for msg in st.session_state.chat_log:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            pass  # Typically hidden
        elif role == "user":
            st.write(f"**User:** {content}")
        else:
            st.write(f"**Assistant:** {content}")

    st.write("---")

    # Use a form so that pressing Enter in the text input also sends the message
    with st.form("chat_form", clear_on_submit=True):
        user_query = st.text_input(
            "Type your question here",
            key="chat_prompt_main",
            placeholder="Ask me anything about stocks..."
        )

        # Two columns for "Send" and "Reset Chat"
        col_send, col_reset = st.columns([0.2, 0.2])
        with col_send:
            send_clicked = st.form_submit_button("Send")  # triggered by Enter or click
        with col_reset:
            reset_clicked = st.form_submit_button("Reset Chat")

        # Process form actions
        if send_clicked and user_query.strip():
            st.session_state.chat_log.append({"role": "user", "content": user_query})
            try:
                openai = OpenAI(api_key=api_key)
                response = openai.chat.completions.create(
                    model=llm,
                    messages=st.session_state.chat_log,
                    functions=sb_func.functions,  # Updated reference
                    function_call='auto',
                    temperature=0.6,
                )
                ai_response = response.choices[0].message

                # Check for function call
                if hasattr(ai_response, 'function_call') and ai_response.function_call:
                    function_name = ai_response.function_call.name
                    function_args = json.loads(ai_response.function_call.arguments)

                    args_dict = {}
                    if function_name in [
                        'calculate_sip_roi',
                        'get_stock_price',
                        'plot_stock_price',
                        'calculate_RSI',
                        'calculate_MACD'
                    ]:
                        args_dict = {'ticker': function_args.get('ticker')}
                    elif function_name in ['calculate_SMA', 'calculate_EMA']:
                        args_dict = {
                            'ticker': function_args.get('ticker'),
                            'window': function_args.get('window')
                        }

                    function_to_call = available_functions[function_name]
                    function_response = function_to_call(**args_dict)

                    # Display results
                    if function_name == 'plot_stock_price':
                        st.image('stock.png')
                    elif function_name == 'calculate_sip_roi':
                        st.markdown(
                            function_response.replace('\n', '<br>'),
                            unsafe_allow_html=True
                        )
                        st.session_state.chat_log.append({'role': 'assistant', 'content': function_response})
                    else:
                        combined_content = function_response
                        if ai_response.content:
                            combined_content = f"{ai_response.content}\n{function_response}"
                        st.session_state.chat_log.append({'role': 'assistant', 'content': combined_content})
                else:
                    # Plain text response
                    st.session_state.chat_log.append(dict(ai_response))

            except Exception as e:
                st.error(f"An error occurred: {e}")

            st.rerun()

        elif reset_clicked:
            st.session_state.chat_log = [{"role": "system", "content": botsystem.prompt}]
            st.rerun()

def main():
    st.set_page_config(page_title="Stock Analysis Dashboard", layout="wide")

    initialize_session_state()
    api_key, llm, model_name = configure_models(st.session_state.model_choice)

    # Sidebar for tab navigation
    sidebar_nav()

    # Render content based on selected tab
    tab = st.session_state.selected_tab
    if tab == "Stockbot":
        show_chatbot_page(api_key, llm, model_name)
    elif tab == "Strategies":
        st.title("Strategies")
        st.write("Here you can find various stock trading strategies.")
    elif tab == "Analysis":
        st.title("Analysis")
        st.write("Stock analysis tools and data.")
    elif tab == "News":
        st.title("News")
        st.write("Latest stock news and updates.")
    elif tab == "Picks":
        st.title("Picks")
        st.write("Curated stock picks and recommendations.")
    elif tab == "Options":
        st.title("Options")
        st.write("Options trading tools and information.")

if __name__ == "__main__":
    main()
