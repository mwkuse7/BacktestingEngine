import pandas as pd
from portfolio import Portfolio

class BacktestEngine:
    def __init__(self, data: pd.DataFrame, strategy, broker, initial_cash: float = 100_000):
        self.data = data
        self.strategy = strategy
        self.broker = broker
        self.portfolio = Portfolio(initial_cash)

    def run(self) -> pd.DataFrame:
        pending_trade = None

        # Iterate through the historical data for a ticker and execute trades based on chosen strategy
        for i, (timestamp, bar) in enumerate(self.data.iterrows()):
            # Fill order placed at previous close at current bar's open price
            if pending_trade is not None:
                self.broker.execute_trade(self.portfolio, pending_trade, bar, timestamp)

                # After filling the order, reset pending_trade
                pending_trade = None

            # Record value of portfolio at current bar's closing price (Mark to Market)
            self.portfolio.record(timestamp, float(bar['Close']))

            # Have strategy decide whether to buy, sell, or hold at the next day's open
            history = self.data.iloc[:i + 1]
            pending_trade = self.strategy.on_bar(history, self.portfolio)

        # Return the portfolio's trading history as a Pandas DataFrame
        return self.portfolio.history()





