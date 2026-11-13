import math
from portfolio import Portfolio, Trade

class Broker:
    def __init__(self, commision_rate: float = 0.001, slippage: float = 0.0005, fractional: bool = False):
        self.commission_rate = commision_rate
        self.slippage = slippage
        self.fractional = fractional

    # Execute a trade in the portfolio based on percentage of total account value to invest in a stock at a given price
    def execute_trade(self, portfolio: Portfolio, target_weights: dict, bars: dict, timestamp) -> None:
        # Prices at open for each ticker of current bar
        reference_prices = {t: float(bar['Open']) for t, bar in bars.items()}

        # Calculate total equity of the portfolio at the reference price for each ticker
        equity = portfolio.equity(reference_prices)

        # Calculate target_weights to prevent short selling and leverage positions
        target_weights = {t: min(max(w, 0.0), 1.0) for t, w in target_weights.items()}
        total_weight = sum(target_weights.values())
        
        # Scale weights of each position, so total equity is greater than shares being purchased
        if total_weight > 1.0:
            target_weights = {t: w / total_weight for t, w in target_weights.items()}

        # Calculate shares to buy/sell for each ticker
        deltas = {}
        for ticker, weight in target_weights.items():
            target = equity * weight / reference_prices[ticker]
            if not self.fractional:
                target = math.floor(target)

            deltas[ticker] = target - portfolio.shares[ticker]

        # For each ticker in the portfolio, sell shares if delta < 0 to free up equity to purchase other shares
        for ticker, delta in deltas.items():
            if delta < 1e-9:
                self._sell(portfolio, ticker, -delta, reference_prices[ticker], timestamp)

        # For each ticker in the portfolio, buy shares if delta > 0
        for ticker, delta in deltas.items():
            if delta > 1e-9:
                self._buy(portfolio, ticker, delta, reference_prices[ticker], timestamp)
        

    def _buy(self, portfolio, ticker, shares, reference_price, timestamp):
        # Calculate price to buy shares, including slippage to account for market volatility
        fill_price = reference_price * (1 + self.slippage)

        # Calculate if portfolio has enough cash to buy one or more shares, return if not
        affordable_shares = portfolio.cash / (fill_price * (1 + self.commission_rate))
        if not self.fractional:
            affordable_shares = math.floor(affordable_shares)
        shares = min(shares, affordable_shares)
        if shares <= 0:
            return

        # Record trade details and update portfolio cash and shares
        cost = shares * fill_price
        commission = cost * self.commission_rate
        portfolio.cash -= cost + commission
        portfolio.shares[ticker] += shares
        trade_type = 'BUY'

        # Record trade in portfolio
        portfolio.trades.append(Trade(timestamp, trade_type, ticker, shares, fill_price, commission))
        
    def _sell(self, portfolio, ticker, shares, reference_price, timestamp):
        # Never sell more shares than currently held in the portfolio, return if not enough shares
        shares = min(shares, portfolio.shares[ticker])
        if shares <= 0:
            return

        # Calculate price to sell shares, including slippage
        fill_price = reference_price * (1 - self.slippage)

        # Record trade details and update portfolio cash and shares
        proceeds = shares * fill_price
        commission = proceeds * self.commission_rate
        portfolio.cash += proceeds - commission
        portfolio.shares[ticker] -= shares
        trade_type = 'SELL'

        # Record trade in portfolio
        portfolio.trades.append(Trade(timestamp, trade_type, ticker, shares, fill_price, commission))