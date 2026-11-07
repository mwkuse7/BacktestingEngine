import pandas as pd
import matplotlib.pyplot as plt

from broker import Broker
from engine import BacktestEngine
from market_data import load_data
from perfomance_metrics import compute_metrics
from strategies import SMACrossover

INITIAL_CASH = 100_000

# Load historical market data for a ticker as a Pandas DataFrame (1 bar per day)
data = load_data('SPY', '2015-01-01', '2024-12-31')

# Create and run engine to execute trading strategy and return details for every bar
engine = BacktestEngine(data, SMACrossover(20, 50), Broker(), INITIAL_CASH)
history = engine.run()

# Create DataFrame with trade results for a buy-and-hold strategy to use as benchmark
# Divide every close by the first close and multiply by cash for growth relative to intial investment
buy_hold = data['Close'] / data['Close'].iloc[0] * INITIAL_CASH

# Create DataFrame comparing results of strategies
results = pd.DataFrame({
    'SMACrossover': compute_metrics(history['equity']),
    'Buy-and-Hold': compute_metrics(buy_hold), 
}).round(3)

print(results)

# Trading activity details
print('# of Trades: ', len(engine.portfolio.trades))
print('Time in market: ', round((history['shares'] > 0).mean(), 3))

# Create blank chart (10 x 5) w/ one set of axes
fig, ax = plt.subplots(figsize=(10, 5))

# Plot equity of strategies on chart
history['equity'].plot(ax=ax, label='SMACrossover')
buy_hold.plot(ax=ax, label='Buy & Hold')

# Label y-axis
ax.set_ylabel('Portfolio Value ($)')

# Show legend on chart
ax.legend()

# Adjust spacing
plt.tight_layout()

# Show chart
plt.show()