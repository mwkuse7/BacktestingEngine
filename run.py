import argparse
import math

import matplotlib.pyplot as plt
import pandas as pd

from broker import Broker
from engine import BacktestEngine
from market_data import load_all_tickers
from perfomance_metrics import compute_metrics, round_trips, summarize_pnl
from strategies import (SMACrossover, TrendFollowing, MomentumRotation, RSIMeanReversion, Breakout, InverseVolatility, EqualWeightRebalance)
from portfolio import Portfolio

DEFAULT_CASH = 100_000
START, END = '2015-01-01', '2024-12-31'
COMMISSION, SLIPPAGE = 0.001, 0.0005

STRATEGIES = [
    ('Simple-Moving-Average Crossover', SMACrossover),
    ('Trend Following', TrendFollowing),
    ('Momentum Rotation', MomentumRotation),
    ('Relative Strength Index Mean Reversion', RSIMeanReversion),
    ('Breakout', Breakout),
    ('Inverse Volatility', InverseVolatility),
    ('Equal Weight Rebalancing', EqualWeightRebalance),
]

def read_tickers(path):
    tickers = []
    with open(path) as f:
        for line in f:
            # Discard comments in input file
            line = line.split('#')[0]

            # Replace each line's commas with spaces and split on whitespace
            for token in line.replace(',', ' ').split():
                # Convert ticker to uppercase
                ticker = token.upper()
                if ticker not in tickers:
                    tickers.append(ticker)

    # Raise error and exit if no tickers in input file
    if not tickers:
        raise SystemExit(f'No tickers found in {path}')

    return tickers

def select_strategy():
    print('\nSelect a strategy:')
    # Print strategies as numbered options
    for number, (label, _) in enumerate(STRATEGIES, start=1):
        print(f'  {number}. {label}')
    
    while True:
        # Prompt user for input and strip whitespace
        answer = input(f'Enter a number (1-{len(STRATEGIES)}): ').strip()

        # Upon valid input return strategy name and fresh instance with default parameters
        if answer.isdigit() and 1 <= int(answer) <= len(STRATEGIES):
            label, strategy = STRATEGIES[int(answer) - 1]
            return label, strategy()

        print('Invalid input, try again...')

def ask_cash(default=DEFAULT_CASH):
    while True:
        # Prompt user for cash in portfolio
        answer = input(f'Starting cash: [{default:,.0f}]').strip()

        # Return default value if no answer provided
        if not answer:
            return float(default)

        # Attempt to convert user input to floating point number, stripping ',' and '$'
        try:
            value = float(answer.replace(',', '').replace('$', ''))
        except ValueError:
            # Value entered was not a number, try again
            print('Please enter a positive dollar amount, like $100,000')
            continue
        if not math.isfinite(value) or value <= 0:
            print('Cash must be a positive number.')
            continue

        return value

def parse_args():
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description='Run a backtest a trading strategy')
    
    # Define optional argument for ticker file path
    parser.add_argument('tickers_file', nargs='?', help='text file containt stock ticker symbols (ask for if omitted)')

    # Validate input and create namespace with parsed arguments
    return parser.parse_args()



def main():
    # Parse input from command line
    args = parse_args()
    try:
        path = args.tickers_file or input('Path to ticker file: ').strip()
        tickers = read_tickers(path)
        label, strategy = select_strategy()
        cash = ask_cash()
    except (KeyboardInterrupt, EOFError):
        raise SystemExit('\nCancelled.')
    except FileNotFoundError:
        raise SystemExit(f'Could not find {path}')

    # Load historical market data for multiple tickers as a dictionary of Pandas DataFrames (1 bar per day)
    try:
        data = load_all_tickers(tickers, START, END)
    except ValueError as e:
        raise SystemExit(f'Error loading data: {e}')

    # Create and run engine to execute trading strategy and return details for every bar
    engine = BacktestEngine(data, strategy, Broker(COMMISSION, SLIPPAGE), cash)
    history = engine.run()
    positions = engine.portfolio.positions()

    # Divide every close by the first close and multiply by cash for growth relative to intial investment
    buy_hold = sum(df['Close'] / df['Close'].iloc[0] for df in data.values()) / len(data) * cash

    # Create DataFrame comparing results of strategies
    results = pd.DataFrame({
        label: compute_metrics(history['equity']),
        'Buy-and-Hold': compute_metrics(buy_hold), 
    }).round(3)

    # Portfolio Details
    print(f'\nTickers: {", ".join(tickers)}')
    print(f'Period: {history.index[0].date()} to {history.index[-1].date()} ({len(history)} bars)')
    print(f'Starting Cash: ${cash:,.0f}\n')

    print(results)

    print()

    # Trading activity details
    trade_counts = pd.Series([trade.ticker for trade in engine.portfolio.trades]).value_counts()
    print('Trades per Ticker:')
    print(trade_counts.to_string())

    print()

    print('Time in market:')
    print(round((positions > 0).mean(), 3).to_string())

    print()

    # Profits/Losses on Round-Trip Trades
    trips = round_trips(engine.portfolio.trades)

    if not trips.empty: 
        print(summarize_pnl(trips['pnl']).round(3).to_string())
        print()
        print(trips.groupby('Ticker')['pnl'].apply(summarize_pnl).unstack().round(3))

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

if __name__ == '__main__':
    main()