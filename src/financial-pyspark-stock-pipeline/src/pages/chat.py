import streamlit as st
import google.generativeai as genai
import yfinance as yf
from PIL import Image
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="AI Market Assistant", page_icon="📈", layout="wide")
st.title("📈 AI Market Assistant")

# --- 1. SETUP & AUTHENTICATION ---
def configure_gemini():
    """Configures the Gemini API with the key from Streamlit secrets."""
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        if not api_key:
            st.error("API key not found. Please add 'GOOGLE_API_KEY' to .streamlit/secrets.toml")
            return False
        genai.configure(api_key=api_key)
        return True
    except KeyError:
        st.error("Missing GOOGLE_API_KEY in secrets.toml")
        return False
    except Exception as e:
        st.error(f"Error configuring Gemini: {e}")
        return False

# --- 2. DEFINE TOOLS (Real-time Data) ---
def get_stock_price(ticker: str):
    """
    Fetches real-time stock data for a given ticker.
    Args:
        ticker: The stock symbol (e.g., AAPL, TSLA).
    """
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="1d")
        if hist.empty:
            return {"error": f"No data found for {ticker}"}
        
        current = hist['Close'].iloc[-1]
        open_p = hist['Open'].iloc[-1]
        change = ((current - open_p) / open_p) * 100
        
        return {
            "ticker": ticker.upper(),
            "price": round(current, 2),
            "change_percent": f"{change:.2f}%",
            "volume": int(hist['Volume'].iloc[-1])
        }
    except Exception as e:
        return {"error": str(e)}

# --- 3. MODEL INITIALIZATION ---
def setup_chat_model():
    """Initializes the Gemini model with tools and system instructions."""
    try:
        # System instructions define the "Persona"
        sys_instruct = """
        You are an expert financial analyst AI.
        1. When asked for prices, ALWAYS use the 'get_stock_price' tool.
        2. If an image is provided, analyze the chart patterns (trends, support/resistance).
        3. Be concise and professional.
        4. Disclaimer: You do not provide financial advice.
        """
        
        # We use 1.5-flash for speed and tool capability
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash", 
            tools=[get_stock_price],
            system_instruction=sys_instruct
        )
        
        # automatic_function_calling handles the JSON tool handshake for you
        chat = model.start_chat(history=[], enable_automatic_function_calling=True)
        return chat
    except Exception as e:
        st.error(f"Error initializing model: {e}")
        return None

# --- STATE MANAGEMENT ---
if "gemini_configured" not in st.session_state:
    st.session_state.gemini_configured = configure_gemini()

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "model",
        "content": "Welcome! I can check real-time stock prices or analyze charts you upload. How can I help?"
    })

if "chat_model" not in st.session_state and st.session_state.gemini_configured:
    st.session_state.chat_model = setup_chat_model()

# --- SIDEBAR (Image Upload) ---
with st.sidebar:
    st.header("Upload Chart")
    uploaded_file = st.file_uploader("Upload a technical chart", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Chart Preview", use_column_width=True)

# --- CHAT INTERFACE ---

# 1. Display History
for message in st.session_state.messages:
    avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 2. Handle Input
if prompt := st.chat_input("Ask about a stock (e.g., 'Price of NVDA' or 'Analyze this chart')"):
    if not st.session_state.gemini_configured or not st.session_state.chat_model:
        st.error("Please configure your API key.")
    else:
        # Append User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        # Generate Response
        with st.chat_message("model", avatar="🤖"):
            with st.spinner("Analyzing..."):
                try:
                    # Logic: If image is uploaded, we must pass it explicitly.
                    # Note: Function calling (tools) is sometimes restricted when mixing images.
                    # We prioritize the image if it exists.
                    
                    if uploaded_file:
                        img = Image.open(uploaded_file)
                        response = st.session_state.chat_model.send_message([prompt, img])
                    else:
                        response = st.session_state.chat_model.send_message(prompt)
                    
                    response_text = response.text
                    st.markdown(response_text)
                    
                    # Append Model Response
                    st.session_state.messages.append({"role": "model", "content": response_text})

                except Exception as e:
                    st.error(f"An error occurred: {e}")