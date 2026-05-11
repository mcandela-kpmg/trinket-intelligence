import streamlit as st
from datetime import datetime

from market_data import get_ticker_market_data, get_industry_peers
from news import get_top_headlines


def _fmt_market_cap(value) -> str:
    if value is None:
        return "N/A"
    if value >= 1e12:
        return f"${value / 1e12:.2f}T"
    if value >= 1e9:
        return f"${value / 1e9:.2f}B"
    if value >= 1e6:
        return f"${value / 1e6:.2f}M"
    return f"${value:,.0f}"


def _fmt_price(value) -> str:
    return f"${value:,.2f}" if value is not None else "N/A"


def _fmt_pe(value) -> str:
    return f"{value:.1f}x" if value is not None else "N/A"


def _fmt_volume(value) -> str:
    if value is None:
        return "N/A"
    if value >= 1e6:
        return f"{value / 1e6:.2f}M"
    return f"{value:,.0f}"


@st.cache_data(ttl=300)
def _cached_market_data(symbol: str):
    return get_ticker_market_data(symbol)


@st.cache_data(ttl=300)
def _cached_peers(industry_key: str, exclude_symbol: str):
    return get_industry_peers(industry_key, exclude_symbol)


@st.cache_data(ttl=300)
def _cached_headlines(symbol: str):
    return get_top_headlines(symbol, count=3)


st.set_page_config(page_title="Market Intelligence", page_icon="📈", layout="wide")
st.title("📈 Market Intelligence")
st.caption("Powered by Yahoo Finance · Data refreshes every 5 minutes")

col_input, col_btn = st.columns([4, 1])
with col_input:
    ticker_input = st.text_input(
        "Ticker Symbol",
        placeholder="e.g. AAPL, MSFT, JPM",
        label_visibility="collapsed",
    )
with col_btn:
    search_clicked = st.button("Search", use_container_width=True, type="primary")

symbol = ticker_input.strip().upper()

if symbol and (search_clicked or ticker_input):
    with st.spinner(f"Fetching data for {symbol}..."):
        data = _cached_market_data(symbol)

    if data is None:
        st.error(f"Ticker **{symbol}** not found. Please check the symbol and try again.")
        st.stop()

    # ── Company Overview ──────────────────────────────────────────────────────
    st.divider()
    st.subheader(f"{data['longName']} ({data['symbol']})")
    st.caption(f"Sector: **{data['sector']}** · Industry: **{data['industry']}**")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Current Price", _fmt_price(data["currentPrice"]))
    c2.metric("Market Cap", _fmt_market_cap(data["marketCap"]))
    c3.metric("P/E Ratio", _fmt_pe(data["trailingPE"]))
    c4.metric("52W High", _fmt_price(data["fiftyTwoWeekHigh"]))
    c5.metric("52W Low", _fmt_price(data["fiftyTwoWeekLow"]))

    cv1, cv2 = st.columns(2)
    cv1.metric("Volume", _fmt_volume(data["volume"]))
    cv2.metric("Avg Volume", _fmt_volume(data["averageVolume"]))

    # ── Industry Peers ────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Industry Peers")

    if data["industryKey"]:
        with st.spinner("Loading industry peers..."):
            peers_df = _cached_peers(data["industryKey"], symbol)

        if peers_df.empty:
            st.info("No peer data available for this industry.")
        else:
            st.dataframe(peers_df, use_container_width=True, hide_index=True)
    else:
        st.info("Industry key not available — cannot load peers.")

    # ── Top Headlines ─────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Top 3 Headlines")

    with st.spinner("Loading headlines..."):
        headlines = _cached_headlines(symbol)

    if not headlines:
        st.info("No headlines found.")
    else:
        for i, article in enumerate(headlines, 1):
            title = article.get("title", "Untitled")
            link = article.get("link", "#")
            publisher = article.get("publisher", "")
            pub_time = article.get("providerPublishTime")
            date_str = (
                datetime.fromtimestamp(pub_time).strftime("%b %d, %Y")
                if pub_time
                else ""
            )
            st.markdown(
                f"**{i}. [{title}]({link})**  \n"
                f"<sub>{publisher}{' · ' if publisher and date_str else ''}{date_str}</sub>",
                unsafe_allow_html=True,
            )
            if i < len(headlines):
                st.write("")
