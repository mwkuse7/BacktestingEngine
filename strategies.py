from abc import ABC, abstractmethod
import pandas as pd

# Abstract base class for a strategy
class Strategy(ABC):
    # Required method that must be implemented by any subclass
    # history: DataFrame containing all bars up to and including the current one
    # Returns target weight between 0.0 and 1.0, or None for no change
    @abstractmethod
    def on_bar(self, history: dict[str, pd.DataFrame], portfolio) -> dict[str, float] | None:
        pass

# Helper class for strategies that rebalance portfolio on monthly basis mitigating transaction costs
class MonthlyTrigger:
    def __init__(self):
        self._last = None

    # Check will return True on the 1st of each month
    def check_month(self, timestamp) -> bool:
        month = (timestamp.year, timestamp.month)
        if month == self._last:
            return False

        self._last = month
        return True

# Helper function to return current date for the first ticker in the history dictionary
def current_datetime(history):
    return next(iter(history.values())).index[-1]

# Simple Moving Average Crossover Strategy
# Buy when the short-term moving average crosses above the long-term moving average
# Sell when the short-term moving average crosses below the long-term moving average
class SMACrossover(Strategy):
    def __init__(self, short_window: int = 20, long_window: int = 50):
        # Short window must be shorter than long window, otherwise raise ValueError
        if short_window >= long_window:
            raise ValueError("Short window must be shorter than long window")

        self.short_window = short_window
        self.long_window = long_window

    def on_bar(self, history, portfolio):
        weights = {}

        for ticker, df in history.items():
            # Not enough bars to compute the long window
            if len(df) < self.long_window:
                continue

            # Calculate short-term and long-term moving averages of the closing price
            close = df['Close']
            short_ma = close.iloc[-self.short_window:].mean()
            long_ma = close.iloc[-self.long_window:].mean()

            # Decide to buy or sell for each ticker depending on moving averages
            weights[ticker] = 1.0 if short_ma > long_ma else 0.0

        # Return None if moving averages cannot be calculated due to insufficient data
        return weights or None

# Trend Following Strategy
# Buy when current price > 200 day average, otherwise sell shares
# Produces smaller drawdown during crash
class TrendFollowing(Strategy):
    def __init__(self, window = 200):
        self.window = window

    def on_bar(self, history, portfolio):
        weights = {}

        for ticker, df in history.items():
            if len(df) < self.window:
                continue
            close = df['Close']

            # Return 1.0 if current tickers price > 200 day average
            weights[ticker] = 1.0 if close.iloc[-1] > close[-self.window :].mean() else 0.0
        
        return weights or None

# 12-1 Momentum Strategy
# Calculate winning positions over the last year, disregarding the last month due to bounceback trends, and split investment weight
# over top_n tickers with the largest gains over that period
class MomentumRotation(Strategy):
    # lookback: how many trading days to measure performance over
    # skip: leaves one month of trading days to account for volatility
    # top_n: how many positions to hold at a time
    def __init__(self, lookback = 252, skip = 21, top_n = 2):
        self.lookback, self.skip, self.top_n = lookback, skip, top_n
        self.trigger = MonthlyTrigger()

    def on_bar(self, history, portfolio):
        # Only rotate holdings once a month
        if not self.trigger.check_month(current_datetime(history)):
            return None

        scores = {}
        for ticker, df in history.items():
            # Don't execute trades until there is one year of history for the ticker
            if len(df) < self.lookback + 1:
                continue

            close = df['Close']
            
            # Calculate momentum score for current ticker, leaving out current month due to bounce-back
            scores[ticker] = close.iloc[-1 - self.skip] / close.iloc[-1 - self.lookback] - 1

        # If no ticker has enough history, strategy cannot decide
        if not scores:
            return None

        # Sort tickers by momentum score, keeping only top_n tickers, ignore negative momentum scores
        winners = [s for s in sorted(scores, key = scores.get, reverse = True)[:self.top_n] if scores[s] > 0]

        # Split investment weight across top_n winning positions, others positions moved to cash 
        return {s: (1.0 / self.top_n if s in winners else 0.0) for s in history}
    
# Mean Reversion Strategy
# Buy when a stock has a short-term drop and a long-term uptrend expecting bounceback (low 2-day RSI and price above the 200 day average)
# Sell when the price recovers from the drop and is above the short term average
class RSIMeanReversion(Strategy):
    def __init__(self, rsi_window = 2, entry = 10, exit_window = 5, trend_window = 200):
        self.rsi_window, self.entry = rsi_window, entry
        self.exit_window, self.trend_window = exit_window, trend_window

    # Function to calculate Relative Strength Index, by comparing average gains to average losses over n days
    def calculate_rsi(close, n):
        # Calculate daily price change on close
        delta = close.diff()

        # Calculate average gain and average loss
        # Replace all negative daily changes with 0, averaging gains over last n days
        gain = delta.clip(lower=0).rolling(n).mean()
        # Replace all positive daily changes with 0, averaging losses over last n days
        loss = (-delta.clip(upper=0)).rolling(n).mean()

        # Calculate a pandas Series of RSI values on scale (0-100)
        return 100 - 100 / (1 + gain / loss)

    def on_bar(self, history, portfolio):
        # Give each ticker an equal portion of the portfolio
        size = 1.0 / len(history)
        weights = {}

        for ticker, df in history.items():
            # Skip until enough bars to calculate trend average (200 days by default)
            if len(df) < self.trend_window:
                continue

            close = df['Close']
            
            # Check if any shares of current ticker are held
            if portfolio.shares[ticker] > 0:
                # if current day's close price > average of last 5 closes then trigger sell, otherwise hold
                recovered = close.iloc[-1] > close.iloc[-self.exit_window:].mean()
                weights[ticker] = 0.0 if recovered else size
            else:
                # No shares of ticker currently held
                # Check if current close price > trend average (average price over 200 days)
                uptrend = close.iloc[-1] > close.iloc[-self.trend_window :].mean()

                # Calculate RSI for last rsi_window days, RSI < 10 indicates stock is oversold
                oversold = self.calculate_rsi(close.iloc[-(self.rsi_window + 1) :], self.rsi_window).iloc[-1] < self.entry

                weights[ticker] = size if (uptrend and oversold) else 0.0

        return weights or None

# Breakout (Donchian) Strategy
# Buy when price rises above highest price of entry_window days (55 by default)
# Sell when price falls belove lowest price of exit_window days (20 by default)
# Invests in strong moves, and sells quickly when price fades
class Breakout(Strategy):
    def __init__(self, entry_window = 55, exit_window = 20):
        self.entry_window, self.exit_window = entry_window, exit_window

    def on_bar(self, history, portfolio):
        # Each ticker gets equal portion of portfolio
        size = 1.0 / len(history)
        weights = {}

        for ticker, df in history.items():
            # Skip until entry_window days of price history
            if len(df) < self.entry_window:
                continue

            # Current day closing price
            close = df['Close'].iloc[-1]

            if portfolio.shares[ticker] > 0:
                # Check if current price < lowest price in previous exit_window days, if true trigger sell
                broke_down = close < df['Low'].iloc[-self.exit_window - 1 : -1].min()
                weights[ticker] = 0.0 if broke_down else size
            else:
                # Check if current price > highest high in previous entry_window days, if true trigger buy
                breakout = close > df['High'].iloc[-self.entry_window - 1 : -1].max()
                weights[ticker] = 1.0 if breakout else 0.0

        return weights or None

# Inverse Volatility Strategy
# Invest more cash in less volatile positions, so each asset holds a similar amount of risk
# window: how many days of returns to measure volatility of a position over
class InverseVolatility(Strategy):
    def __init__(self, window=60):
        self.window = window
        self.trigger = MonthlyTrigger()

    def on_bar(self, history, portfolio):
        # Rebalance portfolio once per month
        if not self.trigger.check_month(current_datetime(history)):
            return None

        inverse_volatility = {}

        for ticker, df in history.items():
            # Skip until self.window days of price history
            if len(df) <= self.window:
                continue

            # Take the standard deviation of return percentages over the last self.window days (daily volatility)
            volatility = df['Close'].iloc[-(self.window + 1) :].pct_change().dropna().std()

            if volatility > 0:
                # Give less volatile stocks a larger share of the portfolio (inverse volatility)
                inverse_volatility[ticker] = 1.0 / volatility

        # Rescale weights to add to 1.0 (total portfolio size)
        total = sum(inverse_volatility.values())
        return {t: w / total for t, w in inverse_volatility.items()} if total else None
