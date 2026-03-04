import pandas as pd


class TTESimulation:

    def __init__(
        self,
        initial_share_price: float,
        initial_shares: int,
        initial_dividend: float,
        dividend_growth_rate: float,
        years: int,
        start_year: int,
        reinvest_dividends: bool,
        loyalty_bonus: bool,
        monthly_investment: float,
        mean_price_high: float,
        mean_price_low: float,
        reversion_speed: float,
        vol_high: float,
        vol_low: float,
        regime_scenario: str,
    ) -> None:
        a = 1
