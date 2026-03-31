import math
import pandas as pd
import yfinance as yf


def fetch_adj_close(ticker: str, start: str, end: str | None = None) -> pd.Series:
    """Fetch daily Adjusted Close prices from Yahoo Finance."""
    df = yf.download(
        ticker,
        start=start,
        end=end,
        interval="1d",
        auto_adjust=False,
        progress=False,
        group_by="column",
    )
    if df.empty:
        raise ValueError(f"No data fetched for {ticker}.")

    adj = df["Adj Close"]
    if isinstance(adj, pd.DataFrame):
        if ticker in adj.columns:
            adj = adj[ticker]
        else:
            adj = adj.iloc[:, 0]

    s = adj.dropna()
    s.index = pd.to_datetime(s.index)
    s.name = ticker
    return s


def monthly_mean_price(series: pd.Series) -> pd.Series:
    """Convert daily prices to monthly mean prices."""
    return series.resample("ME").mean().dropna()


def tte_vol_annual_last_20y(ticker: str = "TTE.PA") -> dict:
    """
    Compute annualised volatility over the last 20 years:
    - Build monthly mean prices
    - Compute monthly returns
    - Annualise: std(monthly_returns) * sqrt(12)
    """
    daily = fetch_adj_close(ticker, start="2000-01-01")
    monthly = monthly_mean_price(daily)

    if monthly.empty:
        raise ValueError("No monthly data after resampling.")

    end_date = monthly.index.max()
    start_cut = end_date - pd.DateOffset(years=20)
    monthly_20y = monthly[monthly.index >= start_cut].dropna()

    if monthly_20y.shape[0] < 24:
        raise ValueError("Not enough data to compute volatility (need at least ~24 months).")

    r_m = monthly_20y.pct_change().dropna()

    vol_monthly = float(r_m.std())
    vol_annual = vol_monthly * math.sqrt(12)

    return {
        "ticker": ticker,
        "start": str(monthly_20y.index.min().date()),
        "end": str(monthly_20y.index.max().date()),
        "n_months": int(monthly_20y.shape[0]),
        "vol_monthly": vol_monthly,
        "vol_annual": vol_annual,
    }
