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
        regime_scenario: str,
        mean_price_high: float,
        mean_price_low: float,
        reversion_speed: float,
        vol_high: float,
        vol_low: float,
        p_high: float,
        seed: int | None,
    ) -> None:

        self.initial_share_price = initial_share_price
        if initial_share_price <= 0:
            raise ValueError("initial_share_price must be > 0.")

        self.initial_shares = initial_shares

        if not isinstance(initial_shares, int):
            raise TypeError("initial_shares must be an int (no fractional shares).")
        if initial_shares < 0:
            raise ValueError("initial_shares must be >= 0.")

        self.monthly_investment = monthly_investment
        self.reinvest_dividends = reinvest_dividends

        if monthly_investment < 0:
            raise ValueError("monthly_investment must be >= 0.")

        self.initial_dividend = initial_dividend
        self.dividend_growth_rate = dividend_growth_rate

        if initial_dividend < 0:
            raise ValueError("initial_dividend must be >= 0.")
        if dividend_growth_rate < -1:
            raise ValueError("dividend_growth_rate must be >= -1.")

        self.years = years
        if years <= 0:
            raise ValueError("years must be >= 1.")

        self.start_year = start_year

        self.regime_scenario = regime_scenario

        allowed = {"Always High", "Always Low", "Random"}
        if regime_scenario not in allowed:
            raise ValueError(f"regime_scenario must be one of {allowed}.")

        self.mean_price_high = mean_price_high
        self.mean_price_low = mean_price_low

        if mean_price_low >= mean_price_high:
            raise ValueError("mean price low must be strictly lower than mean price high.")

        self.reversion_speed = reversion_speed

        if reversion_speed < 0:
            raise ValueError("reversion_speed must be >= 0.")

        self.vol_high = vol_high
        self.vol_low = vol_low

        if vol_high < 0 or vol_low < 0:
            raise ValueError("Volatility must be >= 0.")

        self.p_high = p_high
        if not (0.0 <= p_high <= 1.0):
            raise ValueError("p_high must be between 0 and 1.")

        self.seed = seed
        self._regime_by_year = {}
        self.total_shares = 0
        self.cash_dividends = 0.0
        self.cash_contrib = 0.0

        self.results: pd.DataFrame | None = None

    # --- helpers --- #
    def _get_regime(self, year: int) -> str:

        if self.regime_scenario == "Always High":
            return "HIGH"

        if self.regime_scenario == "Always Low":
            return "LOW"

        if self.regime_scenario == "Random":

            if year in self._regime_by_year:
                return self._regime_by_year[year]

            base_seed = 0 if self.seed is None else int(self.seed)
            rng = random.Random(base_seed + year * 10000)
            regime = "HIGH" if rng.random() < self.p_high else "LOW"
            self._regime_by_year[year] = regime
            return regime

        raise ValueError("Unknown regime.")

    def _target_price(self, regime: str) -> float:

        if regime == "HIGH":
            return self.mean_price_high

        if regime == "LOW":
            return self.mean_price_low

        raise ValueError("Unknown regime.")

    def _regime_vol(self, regime: str) -> float:
        if regime == "HIGH":
            return self.vol_high

        if regime == "LOW":
            return self.vol_low

        raise ValueError("Unknown regime.")

    def _next_price(self, current_price: float, target: float, vol: float, rng) -> float:

        base = current_price + self.reversion_speed * (target - current_price)  # mean reverting
        noise = current_price * vol * rng.gauss(0, 1)

        next_price = base + noise

        return max(1.0, next_price)

    def _quarter_prices(self, p_start, p_end) -> list[float]:
        q1 = p_start * 0.875 + p_end * 0.125
        q2 = p_start * 0.625 + p_end * 0.375
        q3 = p_start * 0.375 + p_end * 0.625
        q4 = p_start * 0.125 + p_end * 0.875

        return [q1, q2, q3, q4]

    def _buy_shares_with_amount(self, share_price: float, amount: float) -> float:

        if share_price <= 0:
            raise ValueError("Share price must be > 0")

        if amount < share_price:
            return amount

        shares_bought = int(amount // share_price)
        spent = shares_bought * share_price
        remaining = amount - spent

        if shares_bought > 0:
            self.total_shares += shares_bought

        return remaining

    def run_simulation(self) -> pd.DataFrame:

        self.total_shares = self.initial_shares
        self.cash_dividends = 0.0
        self.cash_contrib = 0.0
        self._regime_by_year = {}

        rng = random.Random(self.seed)

        share_price = self.initial_share_price
        dividend_per_share = self.initial_dividend

        total_invested = self.initial_shares * self.initial_share_price
        total_div_received = 0.0

        rows = []
        # Year 0
        rows.append(
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
        )

        for year in range(1, self.years + 1):

            calendar_year = self.start_year + year

            # market regime and yearly price move
            regime = self._get_regime(year)
            target = self._target_price(regime)
            vol = self._regime_vol(regime)

            p_end = self._next_price(share_price, target, vol, rng)
            q_prices = self._quarter_prices(share_price, p_end)

            # Update dividend
            dividend_per_share *= 1 + self.dividend_growth_rate
            dps_quarter = dividend_per_share / 4.0
            annual_dividend_received = 0.0

            # Quarters logic
            for qp in q_prices:
                # contributions
                q_contrib = self.monthly_investment * 3
                total_invested += q_contrib
                self.cash_contrib += q_contrib
                self.cash_contrib = self._buy_shares_with_amount(qp, self.cash_contrib)

                # dividends received
                q_div = self.total_shares * dps_quarter
                annual_dividend_received += q_div
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
                    "Regime": regime,
                    "Share price": p_end,
                    "Total shares": self.total_shares,
                    "Cash": total_cash,
                    "Portfolio value": portfolio_value,
                    "Dividends received": annual_dividend_received,
                    "Total dividends received": total_div_received,
                    "Total invested": total_invested,
                }
            )
            # next year price
            share_price = p_end

        self.results = pd.DataFrame(rows)
        return self.results
