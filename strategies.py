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