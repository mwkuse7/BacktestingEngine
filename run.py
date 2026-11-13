import pandas as pd
import matplotlib.pyplot as plt

from broker import Broker
from engine import BacktestEngine
from market_data import load_all_tickers
from perfomance_metrics import compute_metrics, round_trips, summarize_pnl
from strategies import SMACrossover
from portfolio import Portfolio

INITIAL_CASH = 100_000

# Load historical market data for multiple tickers as a dictionary of Pandas DataFrames (1 bar per day)
tickers = ['SPY', 'QQQ', 'TLT']
data = load_all_tickers(tickers, '2015-01-01', '2024-12-31')

# Create and run engine to execute trading strategy and return details for every bar
engine = BacktestEngine(data, SMACrossover(20, 50), Broker(), INITIAL_CASH)
history = engine.run()
positions = engine.portfolio.positions()

# Divide every close by the first close and multiply by cash for growth relative to intial investment
buy_hold = sum(df['Close'] / df['Close'].iloc[0] for df in data.values()) / len(data) * INITIAL_CASH

# Create DataFrame comparing results of strategies
results = pd.DataFrame({
    'Simple-Mean-Average Crossover': compute_metrics(history['equity']),
    'Buy-and-Hold': compute_metrics(buy_hold), 
}).round(3)

print(results)

print()

# Trading activity details
trade_counts = pd.Series([trade.ticker for trade in engine.portfolio.trades]).value_counts()
print('Trades per Ticker:', trade_counts)
print('Time in market:', round((positions > 0).mean(), 3))

print()

# Profits/Losses on Round-Trip Trades
trips = round_trips(engine.portfolio.trades)

if not trips.empty: 
    print(summarize_pnl(trips['pnl']).round(3))
    print(trips.groupby('ticker')['pnl'].apply(summarize_pnl).unstack().round(3))

# Create blank chart (10 x 5) w/ one set of axes
fig, ax = plt.subplots(figsize=(10, 5))

# Plot equity of strategies on chart
history['equity'].plot(ax=ax, label='SMA Crossover')
buy_hold.plot(ax=ax, label='Buy & Hold')

# Label y-axis
ax.set_ylabel('Portfolio Value ($)')

# Show legend on chart
ax.legend()

# Adjust spacing
plt.tight_layout()

# Show chart
plt.show()