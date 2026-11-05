import math
from portfolio import Portfolio, Trade

class Broker:
    def __init__(self, commision_rate: float = 0.001, slippage: float = 0.0005, fractional: bool = False):
        self.commission_rate = commision_rate
        self.slippage = slippage
        self.fractional = fractional

    # Execute a trade in the portfolio based on percentage of total account value to invest in a stock at a given price
    def execute_trade(self, portfolio: Portfolio, target_weight: float, bar, timestamp) -> None:
        # Calculate target_weight to prevent short selling and leverage positions
        target_weight = min(max(target_weight, 0.0), 1.0)

        # Price at open of current bar
        reference_price = float(bar['Open'])

        # Calculate total equity of the portfolio at the reference price
        equity = portfolio.equity(reference_price)

        # Calculate shares able to buy/sell based on current stock price
        # If fractional shares are not allowed, round down to nearest whole number
        target_shares = equity * target_weight / reference_price
        if not self.fractional:
            target_shares = math.floor(target_shares)

        # Calculate change in shares to buy/sell, return if no transaction is needed
        delta = target_shares - portfolio.shares
        if delta < 1e-6:
            return

        # Buy shares if delta is positive, sell shares if delta is negative
        if delta > 0:
            # Calculate price to buy shares, including slippage to account for market volatility
            fill_price = reference_price * (1 + self.slippage)

            # Calculate if portfolio has enough cash to buy one or more shares, return if not
            affordable_shares = portfolio.cash / (fill_price * (1 + self.commission_rate))
            if not self.fractional:
                affordable_shares = math.floor(affordable_shares)
            shares = min(delta, affordable_shares)
            if shares <= 0:
                return

            # Record trade details and update portfolio cash and shares
            cost = shares * fill_price
            commission = cost * self.commission_rate
            portfolio.cash -= cost + commission
            portfolio.shares += shares
            trade_type = 'BUY'
        else:
            # Never sell more shares than currently held in the portfolio, return if not enough shares
            shares = min(-delta, portfolio.shares)
            if shares <= 0:
                return

            # Calculate price to sell shares, including slippage
            fill_price = reference_price * (1 - self.slippage)

            # Record trade details and update portfolio cash and shares
            proceeds = shares * fill_price
            commission = proceeds * self.commission_rate
            portfolio.cash += proceeds - commission
            portfolio.shares -= shares
            trade_type = 'SELL'

        # Record trade in portfolio
        portfolio.trades.append(Trade(timestamp, trade_type, shares, fill_price, commission))





            

