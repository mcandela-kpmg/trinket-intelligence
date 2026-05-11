import yfinance as yf


def get_top_headlines(symbol: str, count: int = 3) -> list[dict]:
    try:
        results = yf.Search(symbol.upper(), news_count=count).news
        return results[:count] if results else []
    except Exception:
        return []
