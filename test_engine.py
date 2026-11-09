import pandas as pd

from broker import Broker
from engine import BacktestEngine
from strategies import Strategy

# Simple strategy used to test BacktestEngine and Broker
class InvestAll(Strategy):
    def on_bar(self, history, portfolio):
        return 1.0

def create_data(prices):
    # Create range of dates with len(prices) periods, starting at the first parameter, using only business days
    index = pd.date_range('2025-01-01', periods=len(prices), freq='B')

    # Return DataFrame with each bar being indexed by a date in the range above, and each OHLCV having the same value for each bar
    return pd.DataFrame({
        'Open': prices,
        'High': prices,
        'Low': prices,
        'Close': prices,
        'Volume': 1_000,
    }, index=index
    )

# Make sure trade is not executed on first bar and fill on open price
def test_orders_fill_on_open():
    # Create DataFrame with fixed values
    data = create_data([100, 110, 120, 130])

    # Create Engine
    engine = BacktestEngine(data, InvestAll, Broker(0, 0), initial_cash=10_000)
    engine.run()

    first = engine.portfolio.trades[0]
    assert first.timestamp == data.index[1]
    assert first.price == 110

# Make sure account value doesn't change if stock price doesn't change
def test_constant_prices_constant_equity():
    data = create_data([100] * 5)
    engine = BacktestEngine(data, InvestAll, Broker(0, 0), initial_cash=10_000)
    history = engine.run()

    # Check if final account value is within .000001 of starting account value
    assert abs(history['equity'].iloc[-1] - 10_000) < 1e-6

# Make sure commission costs and slippage correctly reduces purchasable shares and total equity
def test_transaction_costs_reduce_equity():
    data = create_data([100] * 5)

    # Create engine with a broker charging 1% commission and account for 1% slippage
    engine = BacktestEngine(data, InvestAll, Broker(0.01, 0.01), initial_cash=10_000)
    history = engine.run()

    # Constant stock price and transaction costs result in a lower portfolio value than the initial value
    assert history['equity'].iloc[-1] < 10_000



# TODO: TEST LOGIC FOR SELLING SHARES