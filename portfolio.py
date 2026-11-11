from dataclasses import dataclass
import pandas as pd

@dataclass
class Trade:
    timestamp: pd.Timestamp
    trade_type: str
    ticker: str
    quantity: float
    price: float
    commission: float

class Portfolio:
    def __init__(self, initial_cash: float, tickers: list[str]):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.shares = {t: 0.0 for t in tickers}
        self.trades: list[Trade] = []
        self._history: list[dict] = []
        self._positions: list[dict] = []

    # Get total value of a stock at a given ticker price
    def equity(self, prices: dict) -> float:
        return self.cash + sum(self.shares[s] * prices[s] for s in self.shares)

    # Record a trade in the portfolio
    def record(self, timestamp, prices: dict) -> None:
        self._history.append({
            'timestamp': timestamp,
            'cash': self.cash,
            'equity': self.equity(prices),
        })
        # Add dictionary with the current timestamp and key-value pairs for each ticker symbol and shares owned
        self._positions.append({'timestamp': timestamp, **self.shares})

    # Return trading history as a Pandas DataFrame
    def history(self) -> pd.DataFrame:
        return pd.DataFrame(self._history).set_index('timestamp')

    def positions(self) -> pd.DataFrame:
        return pd.DataFrame(self._positions).set_index('timestamp')