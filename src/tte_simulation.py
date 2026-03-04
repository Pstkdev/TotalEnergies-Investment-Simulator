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

    def _next_price(self, current_price, target, vol, rng) -> float:

        base = current_price + self.reversion_speed * (target - current_price)
        noise = current_price * vol * rng.gauss(0, 1)

        next_price = base + noise

        return max(1.0, next_price)
