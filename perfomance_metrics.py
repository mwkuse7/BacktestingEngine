import numpy as np
import pandas as pd

from portfolio import Trade

# Compute money gained/lost on a round-trip trade
def round_trips(trades: list[Trade]):
    results = []

    # Track when a position is opened, realized gains, cost of shares, and share count
    shares, cost, opened, proceeds = {}, {}, {}, {}

    for trade in trades:
        ticker = trade.ticker

        if trade.trade_type == 'BUY':
            # Check if a position for the current ticker is currently open, if not initialize the values for current ticker
            if shares.get(ticker, 0.0) < 1e-9:
                shares[ticker], cost[ticker], proceeds[ticker] = 0.0, 0.0, 0.0
                opened[ticker] = trade.timestamp
            
            # Record # of shares purchased and cost
            shares[ticker] += trade.quantity
            cost[ticker] += trade.quantity * trade.price + trade.commission
        else:
            # When selling shares, calculate profit/loss on a trade
            # Average cost per share of current ticker
            avg_cost = cost[ticker] / shares[ticker]

            # Subtract price payed for the shares being sold to keep average cost per share the same
            cost[ticker] -= trade.quantity * avg_cost

            # Calculate money gained for shares sold
            proceeds[ticker] = trade.quantity * trade.price - trade.commission - avg_cost * trade.quantity

            # Subtract shares sold from total
            shares[ticker] -= trade.quantity

            # If all shares of the ticker are sold, add a dict with timestamps and profit/loss for round-trip trade
            if shares[ticker] < 1e-9:
                results.append({'ticker': ticker, 'opened': opened[ticker], 'closed': trade.timestamp, 'pnl': proceeds[ticker]})

    # Return results of round-trip trades as a DataFrame
    return pd.DataFrame(results)

# Function to return a Series with overall profit-and-loss for each ticker in the portfolio
def summarize_pnl(pnl):
    wins, losses = pnl[pnl > 0], pnl[pnl <= 0]

    return pd.Series({
        'Round-Trips:': len(pnl),
        'Win Rate:': len(wins) / len(pnl),
        'Average Win': wins.mean(),
        'Average Loss': losses.mean(), 
        'Profit Factor': (wins.sum() / abs(losses.sum()) if len(losses) and losses.sum() != 0 else float('nan')), 
    })



# risk_free_rate is the annual return rate of a zero-risk investment such as treasury bills
def compute_metrics(equity: pd.Series, periods_per_year: int = 252, risk_free_rate: float = 0.0) -> dict:
    # Compute each bar's change in equity from the previous bar ((today - yesterday) / yesterday)
    returns = equity.pct_change().dropna()

    # Number of years in testing period
    years = len(returns) / periods_per_year

    # Total return expressed as percentage
    total_return = equity.iloc[-1] / equity.iloc[0] - 1

    # Compute Compound Annual Growth Rate (CAGR) (GROWTHFACTOR ^ (1/NUMYEARS) - 1)
    cagr = (1 + total_return) ** (1 / years) - 1

    # Portfolio yearly volatility, by taking daily standard deviation and express as an annualized figure
    volatility = returns.std() * np.sqrt(periods_per_year)

    # Calculate Sharpe ratio (return per unit of risk) (Sharpe ratio > 1 decent | Sharpe ratio > 2 excellent)
    # Excess: How much more the investment returned than a safe investment as daily share
    excess = returns - risk_free_rate / periods_per_year
    sharpe = (excess.mean() / returns.std() * np.sqrt(periods_per_year) if returns.std() > 0 else float('nan'))

    # Calculate Drawdown (How far below peak price your equity is, expressed as a fraction)
    drawdown = equity / equity.cummax() - 1

    # Return metrics as a dictionary
    # CAGR: Annualized growth rate
    # Volatility: Annualized standard deviation of daily returns
    # Sharpe Ratio: How much you earned above a safe investment per unit of risk taken
    # Max Drawdown: Largest drop in value from highest peak to lowest trough before a new peak is reached
    return {
        'Total Return': total_return,
        'CAGR': cagr,
        'Volatility': volatility,
        'Sharpe Ratio': sharpe,
        'Max Drawdown': drawdown.min(), 
    }


