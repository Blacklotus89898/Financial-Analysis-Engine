import streamlit as st
import yfinance as yf
import pandas as pd

@st.cache_data(ttl=3600) # Cache data for 1 hour
def get_stock_data(ticker, start, end):
    try:
        data = yf.download(ticker, start=start, end=end, progress=False)
        # Handle MultiIndex (common in new yfinance)
        if isinstance(data.columns, pd.MultiIndex):
            data = data.xs(ticker, axis=1, level=1)
        if data.empty:
            return None
        return data
    except Exception:
        return None

@st.cache_data(ttl=86400) # Cache company info for 24 hours
def get_company_info(ticker):
    try:
        ticker_obj = yf.Ticker(ticker)
        return ticker_obj.info
    except:
        return {}