import yfinance as yf
import pandas as pd


def fetch_prices(ticker: str, start: str, end: str | None = None) -> pd.Series:
    """retrieve stock data"""
    df = yf.download(ticker, start=start, end=end, interval="1d", auto_adjust=False, progress=False)

    if df.empty:
        raise ValueError("Impossible to fetch data.")

    adj = df["Adj Close"]

    if isinstance(adj, pd.DataFrame):
        if ticker in adj.columns:
            adj = adj[ticker]
        else:
            adj = adj.iloc[:, 0]

    s = adj.dropna()
    s.name = ticker
    return s


def annual_mean_price(series: pd.Series) -> pd.Series:
    return series.resample("YE").mean()


def build_annual_df(tte: pd.Series, brent: pd.Series) -> pd.DataFrame:
    tte_y = annual_mean_price(tte)
    brent_y = annual_mean_price(brent)

    df = pd.DataFrame(
        {
            "tte_price": tte_y,
            "brent_price": brent_y,
        }
    ).dropna()

    # get tte share price variation over the year
    df["tte_return"] = df["tte_price"].pct_change()
    df = df.dropna()

    # define adapted regime with oil price using median threshold
    threshold = df["brent_price"].median()
    df["regime"] = df["brent_price"].apply(lambda x: "HIGH" if x > threshold else "LOW")

    return df


def smoke_test():
    tte = fetch_prices("TTE.PA", start="2000-01-01")
    brent = fetch_prices("CL=F", start="2000-01-01")

    df = build_annual_df(tte, brent)
    print(df.head())
    print(df.tail())

    threshold = df["brent_price"].median()
    print("\nBrent threshold (median):", threshold)

    print("\nRegime counts:")
    print(df["regime"].value_counts(normalize=False))
    print("\nRegime proportions:")
    print(df["regime"].value_counts(normalize=True))

    print("\nTTE price medians by regime:")
    print(df.groupby("regime")["tte_price"].median())

    print("\nTTE return volatility (std) by regime:")
    print(df.groupby("regime")["tte_return"].std())


smoke_test()
