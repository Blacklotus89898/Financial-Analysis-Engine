import pandas as pd
import numpy as np

class TradingEngine:
    def __init__(self, ticker, data, initial_capital):
        self.ticker = ticker
        self.initial_capital = initial_capital
        self.raw_data = data # Immutable original
        self.data = None     # Working copy
        self.results = None
        self.active_strategy_name = ""

    def reset_data(self):
        """Resets self.data to the original raw state."""
        self.data = self.raw_data.copy()
        self.data['Returns'] = self.data['Close'].pct_change()

    # --- STRATEGIES ---
    def strategy_sma_crossover(self, short_window=50, long_window=200):
        self.active_strategy_name = "SMA Crossover"
        self.data['SMA_Short'] = self.data['Close'].rolling(window=short_window).mean()
        self.data['SMA_Long'] = self.data['Close'].rolling(window=long_window).mean()
        self.data['Signal'] = np.where(self.data['SMA_Short'] > self.data['SMA_Long'], 1.0, 0.0)
        self.data['Position'] = self.data['Signal'].shift(1)

    def strategy_macd(self, fast=12, slow=26, signal=9):
        self.active_strategy_name = "MACD Momentum"
        exp1 = self.data['Close'].ewm(span=fast, adjust=False).mean()
        exp2 = self.data['Close'].ewm(span=slow, adjust=False).mean()
        self.data['MACD'] = exp1 - exp2
        self.data['Signal_Line'] = self.data['MACD'].ewm(span=signal, adjust=False).mean()
        self.data['Signal'] = np.where(self.data['MACD'] > self.data['Signal_Line'], 1.0, 0.0)
        self.data['Position'] = self.data['Signal'].shift(1)

    def strategy_rsi(self, window=14, sell_threshold=70):
        self.active_strategy_name = "RSI Filter"
        delta = self.data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        self.data['RSI'] = 100 - (100 / (1 + rs))
        self.data['Signal'] = np.where(self.data['RSI'] < sell_threshold, 1.0, 0.0) 
        self.data['Position'] = self.data['Signal'].shift(1)

    def strategy_bollinger(self, window=20, num_std=2):
        self.active_strategy_name = "Bollinger Bands"
        self.data['BB_Middle'] = self.data['Close'].rolling(window=window).mean()
        self.data['BB_Std'] = self.data['Close'].rolling(window=window).std()
        self.data['Signal'] = np.where(self.data['Close'] < self.data['BB_Middle'], 1.0, 0.0)
        self.data['Position'] = self.data['Signal'].shift(1)

    def backtest(self):
        if self.data is None: return None
        
        # Calculate Returns
        self.data['Strategy_Returns'] = self.data['Returns'] * self.data['Position']
        self.data['Cumulative_Market_Returns'] = (1 + self.data['Returns']).cumprod() * self.initial_capital
        self.data['Cumulative_Strategy_Returns'] = (1 + self.data['Strategy_Returns']).cumprod() * self.initial_capital
        
        # Performance Metrics
        final_equity = self.data['Cumulative_Strategy_Returns'].iloc[-1]
        total_return = (final_equity / self.initial_capital) - 1
        
        # Sharpe Ratio Calculation (Annualized)
        # Assuming Risk Free Rate = 0 for simplicity
        daily_std = self.data['Strategy_Returns'].std()
        daily_mean = self.data['Strategy_Returns'].mean()
        
        sharpe_ratio = 0.0
        if daily_std > 0:
            sharpe_ratio = (daily_mean / daily_std) * np.sqrt(252)
        
        return {
            "name": self.active_strategy_name,
            "equity_curve": self.data['Cumulative_Strategy_Returns'],
            "market_curve": self.data['Cumulative_Market_Returns'],
            "final_equity": final_equity,
            "total_return": total_return,
            "sharpe_ratio": sharpe_ratio
        }