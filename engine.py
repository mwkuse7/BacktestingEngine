import pandas as pd
from portfolio import Portfolio

class BacktestEngine:
    def __init__(self, data: dict[str, pd.DataFrame], strategy, broker, initial_cash: float = 100_000):
        self.data = data
        self.tickers = list(data)
        self.strategy = strategy
        self.broker = broker
        self.portfolio = Portfolio(initial_cash, self.tickers)
        self.index = data[self.symbols[0]].index
        
        # Check to make sure the indexes/dates match up for all tickers (load_all_tickers() should already do this)
        for ticker, df in data.items():
            assert df.index.equals(self.index), f'{ticker} has incorrect dates'

    def run(self) -> pd.DataFrame:
        pending_trades = None

        # Iterate through the historical data for ticker and execute trades based on chosen strategy
        for i, timestamp in enumerate(self.index):
            # Create dictionary with each ticker as a key and the current day's bar as its value
            bars = {t: df.iloc[i] for t, df in self.data.items()}

            # Fill orders placed at previous close at all current bar's open prices
            if pending_trade is not None:
                self.broker.execute_trade(self.portfolio, pending_trades, bars, timestamp)

                # After filling the order, reset pending_trades
                pending_trades = None

            # Record value of portfolio at each ticker's closing price (Mark to Market)
            closes = {t: float(bar['Close']) for t, bar in bars.items()}
            self.portfolio.record(timestamp, closes)

            # Have strategy decide whether to buy, sell, or hold at the next day's open for each ticker in portfolio
            history = {t: df.iloc[:i + 1] for t, df in self.data.items()}
            pending_trade = self.strategy.on_bar(history, self.portfolio)

        # Return the portfolio's trading history as a Pandas DataFrame
        return self.portfolio.history()





