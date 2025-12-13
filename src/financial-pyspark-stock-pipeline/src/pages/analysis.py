import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# --- IMPORTS FROM UTILS ---
from utils.engine import TradingEngine
from utils.visualizer import TechnicalVisualizer
from utils.data_loader import get_stock_data, get_company_info

# --- PAGE CONFIG ---
st.set_page_config(page_title="Strategy Arena Pro", layout="wide")
st.title("⚔️ Strategy Arena: Backtester & Signal Visualizer")

# ==========================================
# SIDEBAR CONTROLS
# ==========================================
st.sidebar.header("⚙️ Simulation Settings")

default_tickers = "NVDA, INTC, AMD, TSLA"
ticker_input = st.sidebar.text_area("Tickers (comma separated)", value=default_tickers, height=70)
tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

col1, col2 = st.sidebar.columns(2)
start_date = col1.date_input("Start Date", value=pd.to_datetime("2023-01-01"))
end_date = col2.date_input("End Date", value=datetime.today())
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

            # --- HEADER & PRICE TREND ---
            c_name = company_info.get('longName', ticker)
            
            if len(raw_data) >= 2:
                current_price = raw_data['Close'].iloc[-1]
                prev_price = raw_data['Close'].iloc[-2]
                delta = current_price - prev_price
                delta_pct = (delta / prev_price) * 100
                
                head_col1, head_col2 = st.columns([3, 1])
                with head_col1:
                    st.markdown(f"### {c_name} ({ticker})")
                    st.caption(f"Sector: {company_info.get('sector', 'N/A')} | Industry: {company_info.get('industry', 'N/A')}")
                with head_col2:
                    st.metric(
                        label="Current Price",
                        value=f"${current_price:.2f}",
                        delta=f"{delta:.2f} ({delta_pct:.2f}%)"
                    )
            
            st.divider()

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
                        "Return %": res["total_return"] * 100,
                        "Sharpe": res["sharpe_ratio"]
                    })

            if results_list:
                results_list.sort(key=lambda x: x['final_equity'], reverse=True)
                winner = results_list[0]
                
                # --- METRICS ROW ---
                st.markdown("##### 🏁 Backtest Performance")
                colA, colB, colC, colD = st.columns(4)
                colA.metric("Best Strategy", winner['name'])
                colB.metric("Total Return", f"{winner['total_return']:.2%}")
                colC.metric("Final Equity", f"${winner['final_equity']:,.0f}")
                colD.metric("Sharpe Ratio", f"{winner['sharpe_ratio']:.2f}")

                # --- DUAL CHARTS (EQUITY + SHARPE) ---
                chart_col1, chart_col2 = st.columns([2, 1])
                
                # Chart 1: Equity Curves
                with chart_col1:
                    st.caption("Growth of $10,000 Investment")
                    fig_eq, ax_eq = plt.subplots(figsize=(8, 5))
                    bench = results_list[0]['market_curve']
                    ax_eq.plot(bench.index, bench, label='Benchmark', color='black', linestyle='--', alpha=0.5)
                    
                    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
                    for idx, res in enumerate(results_list):
                        ax_eq.plot(res['equity_curve'].index, res['equity_curve'], 
                                label=res['name'], color=colors[idx % len(colors)])
                    
                    ax_eq.set_ylabel("Equity ($)")
                    ax_eq.legend(fontsize='small')
                    ax_eq.grid(True, alpha=0.2)
                    st.pyplot(fig_eq)

                # Chart 2: Sharpe Ratio Comparison
                with chart_col2:
                    st.caption("Risk-Adjusted Return (Sharpe Ratio)")
                    fig_sh, ax_sh = plt.subplots(figsize=(4, 5))
                    
                    # Prepare Data
                    names = [r['name'].replace(' ', '\n') for r in results_list] # Break lines for labels
                    values = [r['sharpe_ratio'] for r in results_list]
                    
                    # Dynamic Color Coding
                    # Green > 1, Orange > 0, Red < 0
                    bar_colors = ['green' if v >= 1 else 'orange' if v > 0 else 'red' for v in values]
                    
                    bars = ax_sh.bar(names, values, color=bar_colors, alpha=0.7)
                    ax_sh.axhline(0, color='black', linewidth=0.8)
                    ax_sh.axhline(1, color='green', linestyle='--', alpha=0.5, label='Good (>1.0)')
                    
                    ax_sh.set_title("Higher is Better")
                    ax_sh.grid(axis='y', alpha=0.2)
                    plt.xticks(rotation=45, ha='right')
                    st.pyplot(fig_sh)

            # --- 3. TECHNICAL VISUALIZER ---
            if show_viz:
                st.markdown("---")
                viz = TechnicalVisualizer(raw_data)
                viz.calculate_indicators()
                
                modes_to_show = []
                if viz_mode == "Show Both":
                    modes_to_show = ["Entry", "Exit"]
                elif "Entry" in viz_mode:
                    modes_to_show = ["Entry"]
                else:
                    modes_to_show = ["Exit"]
                
                for m in modes_to_show:
                    color = "🟢" if m == "Entry" else "🔴"
                    st.subheader(f"{color} Technical Dashboard: {m} Signals")
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
                    "Return %": "{:.2f}%",
                    "Sharpe": "{:.2f}"
                }).background_gradient(subset=["Return %"], cmap="RdYlGn")
                  .background_gradient(subset=["Sharpe"], cmap="Blues"),
                use_container_width=True
            )
            
            best = df_summary.iloc[0]
            st.success(f"🥇 Winner: **{best['Strategy']}** on **{best['Ticker']}** (Return: {best['Return %']:.2f}%, Sharpe: {best['Sharpe']:.2f})")
        else:
            st.info("Run analysis to generate results.")