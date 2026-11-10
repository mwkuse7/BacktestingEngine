import numpy as np
import pandas as pd

from portfolio import Trade

# Compute money gained/lost on a round-trip trade
def round_trips(trades: list[Trade]):
    results = []
    shares = 0.0
    cost = 0.0

    for trade in trades:
        if trade.trade_type == 'BUY':
            # When shares were purchased add shares and cost to respective totals
            shares += trade.quantity
            cost += trade.quantity * trade.price
        else:
            # When selling shares, calculate profit/loss on a trade
            # Average cost per share
            avg_cost = cost / shares

            # Subtract price payed for the shares being sold to keep average cost per share the same
            cost -= trade.quantity * avg_cost

            # Calculate money gained for shares sold
            proceeds = trade.quantity * trade.price - trade.commission

            # Add profit/loss for round-trip trade
            results.append(proceeds - avg_cost * trade.quantity)

            # Subtract shares sold from total
            shares -= trade.quantity

    return results

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


