"""
Investment Projection - web version (Streamlit)

Users open a link, enter their numbers (or fetch a live price), and download an
Excel workbook (table + chart) to their own computer.

Run locally:   streamlit run app.py
Run the tests: pip install -r requirements-dev.txt && python -m pytest
"""

import html
import io

import streamlit as st

from calc import COMPOUNDING, EXCHANGES, projected_value, validate_inputs, normalize_ticker
from excel_builder import build_workbook
from pricing import PriceError, fetch_price
from styles import CSS

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

st.set_page_config(page_title="Investment Projection", page_icon="📈", layout="centered")
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def banner(kind, text):
    """Black-on-light message box. kind: ok | err | warn. Text is HTML-escaped."""
    st.markdown(f'<div class="banner {kind}" role="alert">{html.escape(text)}</div>',
                unsafe_allow_html=True)


@st.cache_data(ttl=60, show_spinner=False)
def cached_quote(symbol, exchange):
    """Cache successful lookups for 60 s so repeated clicks do not hammer Yahoo."""
    return fetch_price(symbol, exchange)


def clear_price_message():
    """Ticker or exchange changed: the old 'price found' message no longer applies."""
    st.session_state.pop("price_msg", None)


def get_live_price():
    """Button callback: look up the price and place it in the price box."""
    exchange = st.session_state.get("exchange", EXCHANGES[0])
    try:
        symbol = normalize_ticker(st.session_state.get("ticker", ""))
        quote = cached_quote(symbol, exchange)
    except (ValueError, PriceError) as err:
        st.session_state["price_msg"] = ("err", str(err))
        return
    price = round(quote.price, 4)
    st.session_state["price"] = price
    st.session_state["fetched"] = {"symbol": symbol, "exchange": exchange, "price": price}
    currency = f" {quote.currency}" if quote.currency else ""
    st.session_state["price_msg"] = (
        "ok", f"{quote.symbol}: {price:,.4f}{currency} (latest available, may be delayed)")


# ----------------------------------------------------------------------
# Page
# ----------------------------------------------------------------------
st.markdown(
    '<div class="hero"><h1>Investment Projection</h1>'
    "<p>See how your money could compound, then download it as an Excel file.</p></div>",
    unsafe_allow_html=True,
)

with st.container(key="lookup"):
    left, right = st.columns([3, 2])
    left.text_input("Stock ticker", placeholder="e.g. ATOM", key="ticker",
                    max_chars=17, on_change=clear_price_message)
    right.selectbox("Exchange", EXCHANGES, key="exchange", on_change=clear_price_message)
    st.button("Get live price", on_click=get_live_price)
    message = st.session_state.get("price_msg")
    if message:
        banner(*message)

with st.form("inputs"):
    c1, c2 = st.columns(2)
    price = c1.number_input("Current price ($)", min_value=0.0, value=None,
                            placeholder="e.g. 23.50", format="%.4f", key="price")
    amount = c2.number_input("Investing today ($)", min_value=0.0, value=None,
                             placeholder="e.g. 10000", format="%.2f")
    c3, c4 = st.columns(2)
    years = c3.number_input("Time horizon (years)", min_value=1, max_value=100,
                            value=None, step=1, placeholder="e.g. 10")
    rate = c4.number_input("Expected return (% / yr)", min_value=-99.0, max_value=1000.0,
                           value=None, placeholder="e.g. 8", format="%.2f")
    comp_label = st.selectbox("Compounding", list(COMPOUNDING.keys()))
    submitted = st.form_submit_button("Generate Excel Report")

if submitted:
    inputs, problems = validate_inputs(
        st.session_state.get("ticker", ""), price, amount, years, rate, comp_label)

    # Guard against a stale price: fetched for one ticker, then the ticker was changed.
    fetched = st.session_state.get("fetched")
    if (inputs and fetched and price == fetched["price"]
            and (inputs.ticker, st.session_state.get("exchange")) !=
            (fetched["symbol"], fetched["exchange"])):
        problems.append(
            f"The price shown was fetched for {fetched['symbol']}, but the ticker is now "
            f"{inputs.ticker}. Click 'Get live price' again or type the price yourself.")

    if problems:
        st.session_state.pop("result", None)
        for problem in problems:
            banner("err", problem)
    else:
        final = projected_value(inputs.amount, inputs.years, inputs.rate_pct,
                                inputs.comp_per_year)
        buffer = io.BytesIO()
        build_workbook(inputs.ticker, inputs.price, inputs.amount, inputs.years,
                       inputs.rate_pct, inputs.comp_per_year, buffer)
        st.session_state["result"] = {
            "final": final,
            "gain_pct": (final - inputs.amount) / inputs.amount * 100,
            "summary": (f"{inputs.ticker} · ${inputs.amount:,.0f} · {inputs.rate_pct:g}% a year · "
                        f"{inputs.years} year{'s' if inputs.years != 1 else ''} · {comp_label.lower()}"),
            "years": inputs.years,
            "filename": f"{inputs.ticker.replace('.', '_')}_projection.xlsx",
            "data": buffer.getvalue(),
        }

# The result lives in session state so it survives the rerun a download click triggers.
result = st.session_state.get("result")
if result:
    plural = "S" if result["years"] != 1 else ""
    st.markdown(
        f"""<div class="glass-pill">
            <div class="small">PROJECTED VALUE IN {result['years']} YEAR{plural}</div>
            <div class="big">${result['final']:,.0f}</div>
            <div>{result['gain_pct']:+,.1f}% gain</div>
            <div class="meta">{html.escape(result['summary'])}</div></div>""",
        unsafe_allow_html=True,
    )
    st.download_button("Download Excel file", data=result["data"],
                       file_name=result["filename"], mime=XLSX_MIME)

st.markdown(
    '<div class="note">What-if illustration only. Assumes a constant return each year, '
    "with no fees, taxes or inflation. Prices may be delayed. Not financial advice.</div>",
    unsafe_allow_html=True,
)
