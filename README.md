# Backtesting Engine
An event-driven backtesting engine written in Python for testing stock trading strategies on historical data provided by the yfincance package and the Yahoo Finance API. Give it a list of stock tickers, choose a strategy, and it replays the historical market data one day at a time, simulates realistic fills with slippage at commission rates, and reports the strategy's performance compared to a buy-and-hold strategy as a benchmark.

$\color{red}{\textbf{DISCLAIMER:}}$ This project is for educational and research purposes ONLY. Results of the backtest do not guarantee future stock performance and should not be taken as financial advice.

## Features
* Event-Driven Design - The engine steps through historical data day-by-day, or bar-by-bar, to simulate the behavior of live trading in real life, so strategies can't look into the future.
* Portfolios with Multiple Assets - Trade one or more tickers at once, and a chosen strategy will assign each stock a portion, or weight, of the portfolio to execute trades with.
* Realistic Trade Execution - Orders are scheduled after one bar's close and filled at the next bar's open, with configurable commission and slippage rate, rounding to the whole share, and only allowing execution of trades if there is enough cash in the portfolio.
* 7 Built-In Strategies - Run the backtest with 7 different strategies, and compare the results against a buy-and-hold strategy as a baseline. The built-in strategies include Simple Moving Average Crossover, Trend Following, Momentum Rotation, Relative Strength Index Mean Reversion, Breakout, Inverse Volatility, and Equal Weight Rebalancing.
* Interactive Command-Line Interface - Allows the user to pass a text file containing the tickers to be held in the portfolio, and choose the strategy to run along with the amount of cash the portfolio starts with.
* Performance Report - After running a strategy, the backtest will display performance metrics including total return, compound annual growth rate, max drawdown, trade counts, time-in-market per ticker, and a chart comparing the equity curve against an equal-weight buy-and-hold benchmark.
* Round-Trip Trade Statistics - After running a strategy, the backtest will display metrics such as win rate, average win and loss, and profit factor per ticker.
* Unit Testing - Using pytest, test for fill timing, price and transaction cost handling, multi-asset handling, look-ahead bias, and round-trip trades.

