import matplotlib.pyplot as plt
import pandas as pd

class TechnicalVisualizer:
    def __init__(self, data):
        self.df = data.copy() if data is not None else None

    def calculate_indicators(self):
        if self.df is None: return None
        df = self.df
        
        # MAs
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        # Entry Signals
        df['Signal_SMA_Golden'] = (df['SMA_50'] > df['SMA_200']) & (df['SMA_50'].shift(1) < df['SMA_200'].shift(1))
        
        # Exit Signals
        df['Signal_Death_Cross'] = (df['SMA_50'] < df['SMA_200']) & (df['SMA_50'].shift(1) > df['SMA_200'].shift(1))
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

        # Extensions & Drawdowns
        df['All_Time_High'] = df['Close'].cummax()
        df['Drawdown_Pct'] = (df['Close'] / df['All_Time_High']) - 1
        df['Extension_Pct'] = (df['Close'] - df['SMA_200']) / df['SMA_200']
        
        return df

    def plot_dashboard(self, mode="Entry"):
        if self.df is None: return None
        df = self.df
        
        fig = plt.figure(figsize=(15, 14))
        plt.style.use('bmh')

        # --- PANEL 1: Trend ---
        ax1 = plt.subplot(4, 1, 1)
        ax1.plot(df.index, df['Close'], color='black', alpha=0.4, label='Price')
        ax1.plot(df.index, df['SMA_50'], color='green', linestyle='--', alpha=0.6, label='SMA 50')
        ax1.plot(df.index, df['SMA_200'], color='red', linewidth=2, label='SMA 200')
        
        if mode == "Entry":
            sig = df[df['Signal_SMA_Golden'] == True]
            ax1.scatter(sig.index, sig['SMA_200'], color='gold', s=150, marker='^', edgecolors='black', zorder=5, label='Golden Cross (Buy)')
            title_text = "Trend Entry (Golden Cross)"
        else:
            sig = df[df['Signal_Death_Cross'] == True]
            ax1.scatter(sig.index, sig['SMA_200'], color='red', s=150, marker='v', edgecolors='black', zorder=5, label='Death Cross (Sell)')
            title_text = "Trend Break (Death Cross)"

        ax1.set_title(f"1. {title_text}", fontsize=12, fontweight='bold')
        ax1.legend(loc='upper left')

        # --- PANEL 2: RSI ---
        ax2 = plt.subplot(4, 1, 2, sharex=ax1)
        ax2.plot(df.index, df['RSI'], color='purple', linewidth=1)
        ax2.axhline(70, color='red', linestyle='--', alpha=0.5)
        ax2.axhline(30, color='green', linestyle='--', alpha=0.5)
        
        if mode == "Entry":
            ax2.fill_between(df.index, df['RSI'], 30, where=(df['RSI'] < 30), color='green', alpha=0.3, label='Oversold (Buy Zone)')
        else:
            ax2.fill_between(df.index, df['RSI'], 70, where=(df['RSI'] > 70), color='red', alpha=0.3, label='Overbought (Sell Zone)')
        
        ax2.set_title("2. RSI Momentum", fontsize=10)
        ax2.legend(loc='upper left')

        # --- PANEL 3: MACD ---
        ax3 = plt.subplot(4, 1, 3, sharex=ax1)
        ax3.plot(df.index, df['MACD'], color='black', label='MACD')
        ax3.plot(df.index, df['Signal_Line'], color='orange', linestyle='--', label='Signal')
        
        if mode == "Entry":
            ax3.fill_between(df.index, df['MACD'], df['Signal_Line'], where=(df['MACD'] > df['Signal_Line']), color='green', alpha=0.3, label='Bullish')
        else:
            ax3.fill_between(df.index, df['MACD'], df['Signal_Line'], where=(df['MACD'] < df['Signal_Line']), color='red', alpha=0.3, label='Bearish')
            
        ax3.set_title("3. MACD Momentum", fontsize=10)
        ax3.legend(loc='upper left')

        # --- PANEL 4: Value vs Euphoria ---
        ax4 = plt.subplot(4, 1, 4, sharex=ax1)
        
        if mode == "Entry":
            ax4.plot(df.index, df['Drawdown_Pct'], color='red', linewidth=1)
            ax4.fill_between(df.index, df['Drawdown_Pct'], -0.15, where=(df['Drawdown_Pct'] < -0.15), color='red', alpha=0.3, label='Discount > 15%')
            ax4.set_title("4. Value Zone (Drawdowns)", fontsize=10)
        else:
            ax4.plot(df.index, df['Extension_Pct'], color='blue', linewidth=1)
            ax4.axhline(0.30, color='red', linestyle='--', alpha=0.8)
            ax4.fill_between(df.index, df['Extension_Pct'], 0.30, where=(df['Extension_Pct'] > 0.30), color='orange', alpha=0.5, label='Euphoria > 30%')
            ax4.set_title("4. Price Extension (Bubble Check)", fontsize=10)

        vals = ax4.get_yticks()
        ax4.set_yticklabels(['{:,.0%}'.format(x) for x in vals])
        ax4.legend(loc='upper left')
        plt.tight_layout()
        
        return fig