import yfinance as yf
import pandas as pd
import math


def fetch_adj_close(ticker: str, start: str, end: str | None = None) -> pd.Series:
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
    s.name = ticker
    return s


def monthly_mean_price(series: pd.Series) -> pd.Series:
    return series.resample("ME").mean()


def tte_monthly_stats(tte_daily: pd.Series) -> dict:
    tte_m = monthly_mean_price(tte_daily).dropna()

    # monthly returns based on monthly mean prices
    r_m = tte_m.pct_change().dropna()

    vol_monthly = float(r_m.std())
    vol_annual = vol_monthly * math.sqrt(12)

    q = tte_m.quantile([0.10, 0.25, 0.50, 0.75, 0.90])
    return {
        "n_months": int(tte_m.shape[0]),
        "price_q10": float(q.loc[0.10]),
        "price_q25": float(q.loc[0.25]),
        "price_q50": float(q.loc[0.50]),
        "price_q75": float(q.loc[0.75]),
        "price_q90": float(q.loc[0.90]),
        "vol_monthly": vol_monthly,
        "vol_annual": vol_annual,
    }


def smoke_test():
    tte = fetch_adj_close("TTE.PA", start="2006-01-01")
    stats = tte_monthly_stats(tte)

    print("Months:", stats["n_months"])
    print("Price quantiles (monthly mean):")
    print("  Q10:", stats["price_q10"])
    print("  Q25:", stats["price_q25"])
    print("  Q50 (recommended long_run_price):", stats["price_q50"])
    print("  Q75:", stats["price_q75"])
    print("  Q90:", stats["price_q90"])
    print("Volatility:")
    print("  monthly std:", stats["vol_monthly"])
    print("  annualised (std*sqrt(12)):", stats["vol_annual"])


if __name__ == "__main__":
    smoke_test()
