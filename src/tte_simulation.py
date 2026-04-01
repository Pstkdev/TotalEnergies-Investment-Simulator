import pandas as pd
import random


class TTESimulation:
    def __init__(
        self,
        initial_share_price: float,
        initial_shares: int,
        monthly_investment: float,
        reinvest_dividends: bool,
        initial_dividend: float,
        dividend_growth_rate: float,
        years: int,
        start_year: int,
        long_run_price: float,
        reversion_speed: float,
        vol_annual: float,
        seed: int | None = None,
    ) -> None:
        if initial_share_price <= 0:
            raise ValueError("initial_share_price must be > 0.")
        if not isinstance(initial_shares, int):
            raise TypeError("initial_shares must be an int (no fractional shares).")
        if initial_shares < 0:
            raise ValueError("initial_shares must be >= 0.")
        if monthly_investment < 0:
            raise ValueError("monthly_investment must be >= 0.")
        if initial_dividend < 0:
            raise ValueError("initial_dividend must be >= 0.")
        if dividend_growth_rate < -1:
            raise ValueError("dividend_growth_rate must be >= -1.")
        if years <= 0:
            raise ValueError("years must be >= 1.")
        if long_run_price <= 0:
            raise ValueError("long_run_price must be > 0.")
        if reversion_speed < 0:
            raise ValueError("reversion_speed must be >= 0.")
        if vol_annual < 0:
            raise ValueError("vol_annual must be >= 0.")

        self.initial_share_price = float(initial_share_price)
        self.initial_shares = int(initial_shares)
        self.monthly_investment = float(monthly_investment)
        self.reinvest_dividends = bool(reinvest_dividends)

        self.initial_dividend = float(initial_dividend)
        self.dividend_growth_rate = float(dividend_growth_rate)

        self.years = int(years)
        self.start_year = int(start_year)

        self.long_run_price = float(long_run_price)
        self.reversion_speed = float(reversion_speed)
        self.vol_annual = float(vol_annual)

        self.seed = seed

        self.total_shares = 0
        self.cash_dividends = 0.0
        self.cash_contrib = 0.0
        self.results: pd.DataFrame | None = None

    # --- helpers --- #
    def _next_price(self, current_price: float, rng: random.Random) -> float:
        """
        One-step yearly price update:
        - pull towards long_run_price (mean reversion)
        - add noise using annual volatility
        """
        base = current_price + self.reversion_speed * (self.long_run_price - current_price)
        noise = current_price * self.vol_annual * rng.gauss(0.0, 1.0)
        next_price = base + noise
        return max(0.01, next_price)

    def _quarter_prices(self, p_start: float, p_end: float) -> list[float]:
        """
        Simple linear interpolation over 4 quarters.
        Used only to estimate the price at each quarterly buy/reinvest event.
        """
        q1 = p_start * 0.875 + p_end * 0.125
        q2 = p_start * 0.625 + p_end * 0.375
        q3 = p_start * 0.375 + p_end * 0.625
        q4 = p_start * 0.125 + p_end * 0.875
        return [q1, q2, q3, q4]

    def _buy_shares_with_amount(self, share_price: float, amount: float) -> float:

        if share_price <= 0:
            raise ValueError("Share price must be > 0.")
        if amount < share_price:
            return amount

        shares_bought = int(amount // share_price)
        spent = shares_bought * share_price
        remaining = amount - spent

        if shares_bought > 0:
            self.total_shares += shares_bought

        return remaining

    def run_simulation(self) -> pd.DataFrame:
        """
        Run the simulation and return a yearly results DataFrame.

        For each year, the model simulates an end-of-year share price, pays dividends
        quarterly (with optional reinvestment), invests monthly contributions (grouped
        by quarter) and tracks total shares, cash, portfolio value, dividends, and
        invested capital.
        """
        self.total_shares = self.initial_shares
        self.cash_dividends = 0.0
        self.cash_contrib = 0.0

        rng = random.Random(self.seed)

        share_price = self.initial_share_price
        dividend_per_share = self.initial_dividend

        total_invested = self.initial_shares * self.initial_share_price
        total_div_received = 0.0

        rows = [
            {
                "Year": 0,
                "Calendar year": self.start_year,
                "Share price": share_price,
                "Total shares": self.total_shares,
                "Cash": 0.0,
                "Portfolio value": self.total_shares * share_price,
                "Dividends received": 0.0,
                "Total dividends received": 0.0,
                "Total invested": total_invested,
            }
        ]

        for year in range(1, self.years + 1):
            calendar_year = self.start_year + year

            # yearly price update + quarterly prices
            p_end = self._next_price(share_price, rng)
            q_prices = self._quarter_prices(share_price, p_end)

            # dividends
            dividend_per_share *= 1 + self.dividend_growth_rate
            dps_quarter = dividend_per_share / 4.0
            annual_div_received = 0.0

            for qp in q_prices:
                # contributions
                q_contrib = self.monthly_investment * 3.0
                total_invested += q_contrib
                self.cash_contrib += q_contrib
                self.cash_contrib = self._buy_shares_with_amount(qp, self.cash_contrib)

                # dividends received
                q_div = self.total_shares * dps_quarter
                annual_div_received += q_div
                total_div_received += q_div
                self.cash_dividends += q_div

                # reinvest dividends
                if self.reinvest_dividends:
                    self.cash_dividends = self._buy_shares_with_amount(qp, self.cash_dividends)

            total_cash = self.cash_dividends + self.cash_contrib
            portfolio_value = total_cash + self.total_shares * p_end

            rows.append(
                {
                    "Year": year,
                    "Calendar year": calendar_year,
                    "Share price": p_end,
                    "Total shares": self.total_shares,
                    "Cash": total_cash,
                    "Portfolio value": portfolio_value,
                    "Dividends received": annual_div_received,
                    "Total dividends received": total_div_received,
                    "Total invested": total_invested,
                }
            )

            share_price = p_end

        self.results = pd.DataFrame(rows)
        return self.results
