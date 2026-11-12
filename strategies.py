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