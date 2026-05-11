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


def get_industry_peers(industry: str, exclude_symbol: str) -> pd.DataFrame:
    if not industry:
        return pd.DataFrame()
    try:
        from yfinance import EquityQuery, screen
        # ticker.info uses ' - ' but the screener expects an em dash
        screener_industry = industry.replace(" - ", "—")
        q = EquityQuery("and", [
            EquityQuery("eq", ["industry", screener_industry]),
            EquityQuery("is-in", ["exchange", "NMS", "NYQ"]),
        ])
        result = screen(q, sortField="intradaymarketcap", sortAsc=False, size=11)
        quotes = result.get("quotes", [])
        rows = [
            {
                "Symbol": q["symbol"],
                "Name": q.get("shortName") or q.get("longName", ""),
                "Price": q.get("regularMarketPrice"),
                "Market Cap": q.get("marketCap"),
                "P/E": q.get("trailingPE"),
            }
            for q in quotes
            if q["symbol"].upper() != exclude_symbol.upper()
            and "-" not in q["symbol"]  # exclude preferred shares / depositary units
        ]
        df = pd.DataFrame(rows).head(10)
        df["Price"] = df["Price"].apply(lambda v: f"${v:,.2f}" if pd.notna(v) else "N/A")
        df["Market Cap"] = df["Market Cap"].apply(_fmt_cap)
        df["P/E"] = df["P/E"].apply(lambda v: f"{v:.1f}x" if pd.notna(v) else "N/A")
        return df
    except Exception:
        return pd.DataFrame()


def _fmt_cap(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "N/A"
    if value >= 1e12:
        return f"${value / 1e12:.2f}T"
    if value >= 1e9:
        return f"${value / 1e9:.2f}B"
    return f"${value / 1e6:.0f}M"
