import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -------------------------------
# 1. PAGE CONFIGURATION
# -------------------------------
st.set_page_config(
    page_title="Stock Technical Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Stock Technical Analysis Dashboard")

# -------------------------------
# 2. SIDEBAR INPUTS
# -------------------------------
st.sidebar.header("Configuration")
ticker = st.sidebar.text_input("Ticker Symbol", value="AAPL").upper()
period = st.sidebar.selectbox("Period", options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=3)
interval = st.sidebar.selectbox("Interval", options=["1d", "1wk", "1mo"], index=0)

st.sidebar.markdown("---")
st.sidebar.subheader("Indicator Settings")
show_bollinger = st.sidebar.checkbox("Show Bollinger Bands", value=True)
show_ma = st.sidebar.checkbox("Show Moving Averages", value=True)

# -------------------------------
# 3. DATA LOADING (Cached)
# -------------------------------
@st.cache_data(ttl=300)  # Cache data for 5 minutes
def get_data(ticker, period, interval):
    """Downloads and cleans data, handling MultiIndex issues."""
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        
        if df.empty:
            return None

        # Fix yfinance MultiIndex bug if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        return df
    except Exception as e:
        return None

# -------------------------------
# 4. INDICATOR LOGIC
# -------------------------------
def add_indicators(df):
    """Adds technical indicators to the DataFrame."""
    df = df.copy()

    # --- Moving Averages ---
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()

    # --- Bollinger Bands ---
    std_dev = df["Close"].rolling(window=20).std()
    df["Upper_BB"] = df["SMA_20"] + (std_dev * 2)
    df["Lower_BB"] = df["SMA_20"] - (std_dev * 2)

    # --- Wilder's RSI ---
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # --- MACD ---
    k = df['Close'].ewm(span=12, adjust=False, min_periods=12).mean()
    d = df['Close'].ewm(span=26, adjust=False, min_periods=26).mean()
    df['MACD'] = k - d
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False, min_periods=9).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    return df

# -------------------------------
# 5. PLOTTING LOGIC
# -------------------------------
def create_chart(df, ticker):
    # Create 4 rows: Price (50%), Volume (10%), RSI (20%), MACD (20%)
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.5, 0.1, 0.2, 0.2],
        subplot_titles=(f"{ticker} Price", "Volume", "RSI (14)", "MACD")
    )

    # --- ROW 1: Price & Overlays ---
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name='OHLC'
    ), row=1, col=1)

    # MA Lines
    if show_ma:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='orange', width=1), name='SMA 20'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], line=dict(color='cyan', width=1), name='EMA 20'), row=1, col=1)

    # Bollinger Bands
    if show_bollinger:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Lower_BB'], 
            line=dict(color='rgba(173, 216, 230, 0.5)', width=1), 
            name='Lower BB', showlegend=False
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Upper_BB'], 
            line=dict(color='rgba(173, 216, 230, 0.5)', width=1), 
            fill='tonexty', fillcolor='rgba(173, 216, 230, 0.1)',
            name='Bollinger Bands'
        ), row=1, col=1)

    # --- ROW 2: Volume ---
    colors = ['green' if row['Open'] - row['Close'] <= 0 else 'red' for index, row in df.iterrows()]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'],
        marker_color=colors, name='Volume'
    ), row=2, col=1)

    # --- ROW 3: RSI ---
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=2), name='RSI'), row=3, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="green", row=3, col=1)

    # --- ROW 4: MACD ---
    hist_colors = np.where(df['MACD_Hist'] < 0, '#EA4335', '#34A853')
    fig.add_trace(go.Bar(
        x=df.index, y=df['MACD_Hist'], 
        marker_color=hist_colors, name='Histogram'
    ), row=4, col=1)
    
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='#4285F4', width=1.5), name='MACD'), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='#FBBC05', width=1.5), name='Signal'), row=4, col=1)

    # --- Layout Update ---
    fig.update_layout(
        template="plotly_dark",
        height=900,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Hide range slider and handle weekends (if daily data)
    rangebreaks = []
    if interval == '1d':
        rangebreaks.append(dict(bounds=["sat", "mon"]))
        
    fig.update_xaxes(rangeslider_visible=False, rangebreaks=rangebreaks)

    return fig

# -------------------------------
# 6. MAIN APP LOGIC
# -------------------------------
if ticker:
    with st.spinner(f"Loading data for {ticker}..."):
        raw_data = get_data(ticker, period, interval)
        
        if raw_data is not None and not raw_data.empty:
            processed_data = add_indicators(raw_data)
            
            # Display Metrics
            last_close = processed_data['Close'].iloc[-1]
            prev_close = processed_data['Close'].iloc[-2]
            change = last_close - prev_close
            pct_change = (change / prev_close) * 100
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Current Price", f"${last_close:.2f}", f"{change:.2f} ({pct_change:.2f}%)")
            col2.metric("RSI (14)", f"{processed_data['RSI'].iloc[-1]:.2f}")
            col3.metric("Volume", f"{processed_data['Volume'].iloc[-1]:,}")

            # Plot Chart
            st.plotly_chart(create_chart(processed_data, ticker), use_container_width=True)
            
            # Show Data Tail
            with st.expander("View Raw Data"):
                st.dataframe(processed_data.tail(10))
        else:
            st.error(f"No data found for {ticker}. Please check the symbol and try again.")