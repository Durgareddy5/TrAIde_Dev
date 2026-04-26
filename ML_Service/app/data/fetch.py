import yfinance as yf

def fetch_multi(symbols, period="20y", interval="1d"):
    return yf.download(
        symbols,
        period=period,
        interval=interval,
        group_by="ticker",
        auto_adjust=True,
        threads=True
    )

def fetch_recent(symbols, days=3):
    return yf.download(
        symbols,
        period=f"{days}d",
        interval="5m",
        group_by="ticker",
        threads=True
    )