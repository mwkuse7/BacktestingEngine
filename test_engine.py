import numpy as np
import pandas as pd
import pytest


from broker import Broker
from engine import BacktestEngine
from perfomance_metrics import round_trips
from portfolio import Trade
from strategies import Strategy, SMACrossover

# Simple strategy used to test BacktestEngine and Broker
class InvestAll(Strategy):
    def on_bar(self, history, portfolio):
        return {ticker: 1.0 for ticker in history}

# Hold 'A' for the first 3 days then switch to 'B'
class RotateHoldingsAfterThreeBars(Strategy):
    def on_bar(self, history, portfolio):
        if len(history['A']) < 3:
            return {'A': 1.0, 'B': 0.0}
        return {'A': 0.0, 'B': 1.0}

def create_data(prices):
    # Create range of dates with len(prices) periods, starting at the first parameter, using only business days
    index = pd.date_range('2024-01-01', periods=len(prices), freq='B')

    # Return DataFrame with each bar being indexed by a date in the range above, and each OHLCV having the same value for each bar
    return pd.DataFrame({
        'Open': prices,
        'High': prices,
        'Low': prices,
        'Close': prices,
        'Volume': 1_000,
    }, index=index
    )

# ----- Tests for portfolio with a single ticker ------ #

# Make sure trade is not executed on first bar and fill on open price
def test_orders_fill_on_open():
    # Create DataFrame with fixed values
    data = {'TEST': create_data([100, 110, 120, 130])}

    # Create Engine
    engine = BacktestEngine(data, InvestAll(), Broker(0, 0), 10_000)
    engine.run()

    first = engine.portfolio.trades[0]
    assert first.ticker == 'TEST'
    assert first.timestamp == data['TEST'].index[1]
    assert first.price == 110

# Make sure account value doesn't change if stock price doesn't change
def test_constant_prices_constant_equity():
    data = {'TEST': create_data([100] * 5)}

    engine = BacktestEngine(data, InvestAll(), Broker(0, 0), 10_000)
    history = engine.run()

    # Check if final account value is within .000001 of starting account value
    assert abs(history['equity'].iloc[-1] - 10_000) < 1e-6

# Make sure commission costs and slippage correctly reduces purchasable shares and total equity
def test_transaction_costs_reduce_equity():
    data = {'TEST': create_data([100] * 5)}

    # Create engine with a broker charging 1% commission and account for 1% slippage
    engine = BacktestEngine(data, InvestAll(), Broker(0.01, 0.01), 10_000)
    history = engine.run()

    # Constant stock price and transaction costs result in a lower portfolio value than the initial value
    assert history['equity'].iloc[-1] < 10_000

# Test if SMACrossover strategy executes both buys and sells
def test_smacross_buys_and_sells():
    # Create list of prices from 100-160 then 160-100
    prices = list(range(100, 160)) + list(range(160, 100, -1))
    data = {'TEST': create_data(prices)}
    engine = BacktestEngine(data, SMACrossover(5, 20), Broker(0, 0), 10_000)
    engine.run()

    # Check if there are buys and sells in portfolio
    trade_types = [trade.trade_type for trade in engine.portfolio.trades]
    assert 'BUY' in trade_types and 'SELL' in trade_types



# ----- TESTS FOR PORTFOLIO WITH MULTIPLE TICKERS ----- #

# If all strategies return weight of 1.0 then Broker should scale weights to add to 1.0
def test_weights_over_100_scaled_and_split_equally():
    data = {'A': create_data([100] * 5), 'B': create_data([50] * 5)}

    engine = BacktestEngine(data, InvestAll(), Broker(0, 0), 10_000)
    history = engine.run()

    # Each ticker wants 100% of equity, when scaled down each ticker should get 50%
    assert engine.portfolio.shares == {'A': 50, 'B': 100}
    # Strategy should buy once and hold, so equity never changes
    assert abs(history['equity'].iloc[-1] - 10_000) < 1e-6
    # Cash should not be negative
    assert history['equity'].iloc[-1] >= 1e-9

# Test if sells executed before buys, so the $ earned can fund the next buy
def test_sells_before_buys():
    data = {'A': create_data([100] * 5), 'B': create_data([50] * 5)}

    engine = BacktestEngine(data, RotateHoldingsAfterThreeBars(), Broker(0, 0), 10_000)
    history = engine.run()

    # Check portfolio correctly rotated holdings from one share to another
    assert engine.portfolio.shares == {'A': 0, 'B': 200}
    # Check equity never falls below 0 after trades
    assert (history['equity'] >= -1e-9).all()

    # Check portfolio rotates holdings after the third day, first selling then buying shares of other ticker
    rotation = [trade for trade in engine.portfolio.trades if trade.timestamp == data['A'].index[3]]
    assert [trade.trade_type for trade in rotation] == ['SELL', 'BUY']

# Test engine only runs on ticker data containing the same dates in the same order
def test_mismatched_dates_rejected():
    data = {'A': create_data([100] * 5), 'B': create_data([100] * 4)}

    # Start watching for an AssertionError raised by engine initialization and catch if raised
    with pytest.raises(AssertionError):
        BacktestEngine(data, InvestAll(), Broker(0, 0), 10_000)

# Test for lookahead bias with multiple tickers
def test_lookahead_bias_with_multiple_tickers():
    # Create random number generator with a seed of 1
    random = np.random.default_rng(1)

    # Create artificial prices for tickers over a 300 bar period
    data = {t: create_data(list(100 + random.normal(0, 1, 300).cumsum())) for t in ('A', 'B')}

    # Keep only the first 200 bars of data
    cutoff = 200
    truncated = {t: df.iloc[:cutoff] for t, df in data.items()}

    # Run trading strategy with original data and truncated data
    full = BacktestEngine(data, SMACrossover(5, 20), Broker(0, 0), 10_000)
    cut = BacktestEngine(truncated, SMACrossover(5, 20), Broker(0, 0), 10_000)
    full_history, cut_history = full.run(), cut.run()

    # Compare trading histories and positions to determine if any bias
    pd.testing.assert_frame_equal(full_history.iloc[:200], cut_history)
    pd.testing.assert_frame_equal(full.portfolio.positions().iloc[:200], cut.portfolio.positions())




# ----- TESTS FOR ROUND-TRIP TRADES ----- #

# Test round-trip profit/loss caluculated by ticker
def test_round_trips_tracked_by_symbol():
    t = pd.Timestamp
    trades = [
        Trade(t('2024-01-02'), 'BUY', 'A', 10, 100, 0),
        Trade(t('2024-01-03'), 'BUY', 'B', 20, 50, 0),
        Trade(t('2024-01-04'), 'SELL', 'A', 10, 110, 0),
        Trade(t('2024-01-05'), 'SELL', 'B', 20, 45, 0),
    ]

    # round_trips returns DataFrame with profit/loss for a ticker when position is sold off
    trips = round_trips(trades)

    # Pair each ticker with its profit or loss
    profit_loss = dict(zip(trips['ticker'], trips['pnl']))
    assert profit_loss == {'A': 100, 'B': -100}

# Test two partial trades only record one round-trip trade when position is completely sold
def test_two_partial_sells_one_round_trip():
    t = pd.Timestamp
    trades = [
        Trade(t('2024-01-02'), 'BUY', 'A', 10, 100, 0),
        Trade(t('2024-01-03'), 'SELL', 'A', 4, 110, 0),
        Trade(t('2024-01-04'), 'SELL', 'A', 6, 90, 0),
    ]

    # BUY 10 shares at $100, SELL 4 shares at $110, SELL 6 shares at $90 == $20 total loss on round-trip trade
    trips = round_trips(trades)
    assert len(trips) == 1
    assert trips['pnl'].iloc[0] == -20