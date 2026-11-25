# Backtesting Engine
An event-driven backtesting engine written in Python for testing stock trading strategies on historical data provided by the yfincance package and the Yahoo Finance API. Give it a list of stock tickers, choose a strategy, and it replays the historical market data one day at a time, simulates realistic fills with slippage and commission rates, and reports the strategy's performance compared to a buy-and-hold strategy as a benchmark.

$\color{red}{\textbf{DISCLAIMER:}}$ This project is for educational and research purposes ONLY. Backtest results do not guarantee future stock performance and should not be taken as financial advice.

## Features
* **Event-Driven Design** - The engine steps through historical data day-by-day, or bar-by-bar, to simulate the behavior of live trading in real life, so strategies can't look into the future.
* **Portfolios with Multiple Assets** - Trade one or more tickers at once, and a chosen strategy will assign each stock a portion, or weight, of the portfolio to execute trades with.
* **Realistic Trade Execution** - Orders are scheduled after one bar's close and filled at the next bar's open, with configurable commission and slippage rate, rounding to the whole share, and only allowing execution of trades if there is enough cash in the portfolio.
* **7 Built-In Strategies** - Run the backtest with 7 different strategies, and compare the results against a buy-and-hold strategy as a baseline. The built-in strategies include Simple Moving Average Crossover, Trend Following, Momentum Rotation, Relative Strength Index Mean Reversion, Breakout, Inverse Volatility, and Equal Weight Rebalancing.
* **Interactive Command-Line Interface** - Allows the user to pass a text file containing the tickers to be held in the portfolio, and choose the strategy to run along with the amount of cash the portfolio starts with.
* **Performance Report** - After running a strategy, the backtest will display performance metrics including total return, compound annual growth rate, max drawdown, trade counts, time-in-market per ticker, and a chart comparing the equity curve against an equal-weight buy-and-hold benchmark.
* **Round-Trip Trade Statistics** - After running a strategy, the backtest will display metrics such as win rate, average win and loss, and profit factor per ticker.
* **Unit Testing** - Using pytest, test for fill timing, price and transaction cost handling, multi-asset handling, look-ahead bias, and round-trip trades.

## How it Works
On every bar, the backtesting engine runs these three steps in order:
1. **Fill**: Any order that the strategy placed after the close of the previous bar is executed and filled at the current bar's open price (the day in the date range is skipped).
2. **Mark-to-Market**: The current value of the portfolio (cash plus every position at the current closing price) is recorded.
3. **Decide**: The strategy can see all of the data up to and including the current bar and returns the position weights, which will be used to fill the order at the next day's open.

*NOTE: The one-bar delay prevents the strategy from producing look-ahead bias, meaning a signal computed from today's close cannot be used to execute a trade at the current day's close.*

#### Target Weights
Strategies don't execute orders directly. They return a dictionary of target weights (0.0 to 1.0), or the fraction of total portfolio equity they want in each position.

The broker (broker.py) then attempts to produce the trades needed to reflect the target weights. The weights are clamped within a range of 0.0 to 1.0, and if the weights add up to more than 1.0, they are scaled down proportionally. Sells, signaled by a weight of 0.0, are executed before buys, so selling one asset can fund the buy of another on the same bar.

## Getting Started
**Requirements**: Python 3.10 or newer

**1. Install Project Dependencies**
```
pip install -r requirements.txt
```
**2. Create a file with the desired stock tickers**

A plain text file with one or more ticker symbols per line. Blank lines, comments using #, and commas and/or spaces between tickers are fine.
```
# tickers.txt
# US Stocks
SPY
QQQ
# Bonds & Gold
TLT, GLD
```

**3. Run it**
```
bash
python run.py tickers.txt
```
**4. Answer prompts**
```
Select a strategy:
  1. Simple-Moving-Average Crossover
  2. Trend Following
  3. Momentum Rotation
  4. Relative Strength Index Mean Reversion
  5. Breakout
  6. Inverse Volatility
  7. Equal Weight Rebalancing
Enter a number (1-7): 3
Starting cash: [100,000]
```
* The strategy prompt repeats until you enter a valid number.
* The cash prompt accepts a variety of formats: 50000, 50,000, or $50,000. Press enter to accept the default ($100,000)

## Included Strategies
All strategies use the same interface and run using either a single ticker or multiple. Parameters are constructors with the following defaults:
| # | Strategy | Description | Defaults |
|---|----------|-------------|----------|
| 1 | Simple-Moving-Average Crossover | Buy when the short-term moving average crosses above the long-term moving average. Sell when the short-term moving average crosses below the long-term moving average. | short_window = 20, long_window = 50 |
| 2 | Trend Following | Buy when current price > 200 day average, otherwise sell shares. This strategy produces a smaller drawdown during a crash | window = 200 |
| 3 | Momentum Rotation | Calculates winning positions over the last year, disregarding the last month due to bounceback trends, and splits investment weight over top_n tickers with the largest gains over that period | lookback = 252, skip = 21, top_n = 2 |
| 4 | Relative Strength Index Mean Reversion | Buy when a stock has a short-term drop and a long-term uptrend, expecting a bounceback (low 2-day RSI and price above the 200-day average). Sell when the price recovers from the drop and is above the short-term average. | rsi_window = 2, entry = 10, exit_window = 5, trend_window = 200 |
| 5 | Breakout (Donchian) Strategy | Buy when the price rises above the highest price of entry_window days (55 by default). Sell when the price falls below the lowest price of exit_window days (20 by default). Invests in strong moves and sells quickly when price fades. | entry_window = 55, exit_window = 20 |
| 6 | Inverse Volatility | Invest more cash in less volatile positions, so each asset holds a similar amount of risk. | window = 60 |
| 7 | Equal Weight Rebalancing | Splits portfolio equally across all tickers, and trades back into equal weights monthly. | None |



