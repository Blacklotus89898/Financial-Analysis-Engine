import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- IMPORTS FROM UTILS ---
# Make sure your folder is named 'utils' and contains __init__.py
from utils.engine import TradingEngine
from utils.visualizer import TechnicalVisualizer
from utils.dataloader import get_stock_data, get_company_info

# --- PAGE CONFIG ---
st.set_page_config(page_title="Strategy Arena Pro", layout="wide")
st.title("⚔️ Strategy Arena: Backtester & Signal Visualizer")

# ==========================================
# SIDEBAR CONTROLS
# ==========================================
st.sidebar.header("⚙️ Simulation Settings")

# Ticker Input
default_tickers = "NVDA, INTC, AMD, TSLA"
ticker_input = st.sidebar.text_area("Tickers (comma separated)", value=default_tickers, height=70)
tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

# Date & Capital
col1, col2 = st.sidebar.columns(2)
start_date = col1.date_input("Start Date", value=pd.to_datetime("2023-01-01"))
end_date = col2.date_input("End Date", value=pd.to_datetime("2025-01-01"))
initial_capital = st.sidebar.number_input("Initial Capital ($)", value=10000, step=1000)

st.sidebar.markdown("---")
st.sidebar.header("🔬 Visualizer Settings")
show_viz = st.sidebar.checkbox("Show Technical Dashboard", value=True)
viz_mode = st.sidebar.radio("Signal Mode", ["Entry (Buy Signals)", "Exit (Sell Signals)", "Show Both"])

run_btn = st.sidebar.button("🚀 Run Analysis", type="primary")

# ==========================================
# MAIN EXECUTION
# ==========================================
if run_btn:
    all_summaries = []
    
    # Create Tabs
    tabs = st.tabs(tickers + ["🏆 Leaderboard"])

    for i, ticker in enumerate(tickers):
        with tabs[i]:
            # --- 1. FETCH DATA ---
            with st.spinner(f"Downloading {ticker}..."):
                raw_data = get_stock_data(ticker, start_date, end_date)
                company_info = get_company_info(ticker)

            if raw_data is None:
                st.error(f"Could not fetch data for {ticker}")
                continue

            # Display Header
            c_name = company_info.get('longName', ticker)
            st.markdown(f"### {c_name} ({ticker})")

            # --- 2. STRATEGY BACKTESTING ---
            engine = TradingEngine(ticker, raw_data, initial_capital)
            results_list = []
            
            strategies = [
                ("SMA Crossover", engine.strategy_sma_crossover, (50, 200)),
                ("MACD Momentum", engine.strategy_macd, (12, 26, 9)),
                ("RSI Filter", engine.strategy_rsi, (14, 70)),
                ("Bollinger Bands", engine.strategy_bollinger, (20, 2))
            ]

            for name, func, args in strategies:
                engine.reset_data()
                func(*args)
                res = engine.backtest()
                if res:
                    res["ticker"] = ticker
                    results_list.append(res)
                    all_summaries.append({
                        "Ticker": ticker,
                        "Strategy": res["name"],
                        "Final Equity": res["final_equity"],
                        "Return %": res["total_return"] * 100
                    })

            if results_list:
                results_list.sort(key=lambda x: x['final_equity'], reverse=True)
                winner = results_list[0]
                
                # Metrics
                colA, colB, colC = st.columns(3)
                colA.metric("Best Strategy", winner['name'])
                colB.metric("Return", f"{winner['total_return']:.2%}")
                colC.metric("Equity", f"${winner['final_equity']:,.0f}")

                # Plot Equity Curves
                fig, ax = plt.subplots(figsize=(10, 4))
                bench = results_list[0]['market_curve']
                ax.plot(bench.index, bench, label='Benchmark', color='black', linestyle='--', alpha=0.5)
                
                colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
                for idx, res in enumerate(results_list):
                    ax.plot(res['equity_curve'].index, res['equity_curve'], 
                            label=res['name'], color=colors[idx % len(colors)])
                
                ax.set_ylabel("Equity ($)")
                ax.legend(fontsize='small')
                ax.grid(True, alpha=0.2)
                st.pyplot(fig)

            # --- 3. TECHNICAL VISUALIZER ---
            if show_viz:
                st.markdown("---")
                viz = TechnicalVisualizer(raw_data)
                viz.calculate_indicators()
                
                # Logic to determine which modes to show
                modes_to_show = []
                if viz_mode == "Show Both":
                    modes_to_show = ["Entry", "Exit"]
                elif "Entry" in viz_mode:
                    modes_to_show = ["Entry"]
                else:
                    modes_to_show = ["Exit"]
                
                for m in modes_to_show:
                    st.subheader(f"🔬 Technical Dashboard: {m} Signals")
                    fig_viz = viz.plot_dashboard(mode=m)
                    st.pyplot(fig_viz)

    # --- LEADERBOARD TAB ---
    with tabs[-1]:
        st.header("🏆 Overall Strategy Leaderboard")
        if all_summaries:
            df_summary = pd.DataFrame(all_summaries)
            df_summary = df_summary.sort_values(by="Return %", ascending=False).reset_index(drop=True)
            
            st.dataframe(
                df_summary.style.format({
                    "Final Equity": "${:,.2f}",
                    "Return %": "{:.2f}%"
                }).background_gradient(subset=["Return %"], cmap="RdYlGn"),
                use_container_width=True
            )
            
            best = df_summary.iloc[0]
            st.success(f"🥇 Winner: **{best['Strategy']}** on **{best['Ticker']}** ({best['Return %']:.2f}%)")
        else:
            st.info("Run analysis to generate results.")