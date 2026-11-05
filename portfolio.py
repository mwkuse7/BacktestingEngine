from dataclasses import dataclass
import pandas as pd

@dataclass
class Trade:
    timestamp: pd.Timestamp
    trade_type: str
    quantity: float
    price: float
    commission: float

class Portfolio:
    def __init__(self, initial_cash: float):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.shares = 0.0
        self.trades: list[Trade] = []
        self._history: list[dict] = []

    # Get total value of a stock at a given ticker price
    def equity(self, price: float) -> float:
        return self.cash + self.shares * price

    # Record a trade in the portfolio
    def record(self, timestamp, price: float) -> None:
        self._history.append({
            'timestamp': timestamp,
            'cash': self.cash,
            'shares': self.shares,
            'price': price,
            'equity': self.equity(price),
        })

    # Return trading history as a Pandas DataFrame
    def history(self) -> pd.DataFrame:
        return pd.DataFrame(self._history).set_index('timestamp')