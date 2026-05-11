import yfinance as yf
import pandas as pd


def get_ticker_market_data(symbol: str) -> dict | None:
    ticker = yf.Ticker(symbol.upper())
    info = ticker.info
    if not info or info.get("trailingPegRatio") is None and info.get("currentPrice") is None and info.get("regularMarketPrice") is None:
        # yfinance returns a minimal dict for invalid tickers; check for a reliable key
        if not info.get("longName") and not info.get("shortName"):
            return None
    return {
        "symbol": info.get("symbol", symbol.upper()),
        "longName": info.get("longName") or info.get("shortName", symbol.upper()),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "industryKey": info.get("industryKey", ""),
        "currentPrice": info.get("currentPrice") or info.get("regularMarketPrice"),
        "marketCap": info.get("marketCap"),
        "trailingPE": info.get("trailingPE"),
        "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
        "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
        "volume": info.get("volume") or info.get("regularMarketVolume"),
        "averageVolume": info.get("averageVolume"),
    }


def get_industry_peers(industry_key: str, exclude_symbol: str) -> pd.DataFrame:
    if not industry_key:
        return pd.DataFrame()
    try:
        industry = yf.Industry(industry_key)
        df = industry.top_performing_companies
        if df is None or df.empty:
            return pd.DataFrame()
        # Drop the searched ticker so it's not listed as its own peer
        df = df[df.index.str.upper() != exclude_symbol.upper()]
        return df.head(10).reset_index()
    except Exception:
        return pd.DataFrame()
