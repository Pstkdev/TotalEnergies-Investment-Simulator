import yfinance as yf
import pandas as pd


def fetch_prices(ticker: str, start: str, end: str | None = None) -> pd.Series:

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


def annual_last_price(series: pd.Series) -> pd.Series:
    return series.resample("YE").last()


def build_annual_df(tte: pd.Series, brent: pd.Series) -> pd.DataFrame:
    tte_y = annual_last_price(tte)
    brent_y = annual_last_price(brent)

    df = pd.DataFrame(
        {
            "tte_price": tte_y,
            "brent_price": brent_y,
        }
    ).dropna()

    return df
