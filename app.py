"""
Investment Projection - web version (Streamlit)

Users open a link, enter their numbers, and download an Excel workbook
(table + chart) to their own computer.

Run locally:   streamlit run app.py
"""

import io
import math

import streamlit as st
import yfinance as yf

from excel_builder import build_workbook

COMPOUNDING = {"Annually": 1, "Semi-annually": 2, "Quarterly": 4, "Monthly": 12}
EXCHANGES = ["Australia (ASX)", "US / exactly as typed"]


@st.cache_data(ttl=60, show_spinner=False)
def lookup_price(symbol, exchange):
    """Fetch the latest price from Yahoo Finance.

    Returns (yahoo_symbol, price, currency). Raises ValueError if nothing is found.
    ASX tickers need a '.AX' suffix on Yahoo, so it is added automatically when
    the Australia option is chosen. Prices can be delayed by ~15 minutes.
    """
    yahoo_symbol = symbol
    if exchange == EXCHANGES[0] and "." not in symbol:
        yahoo_symbol = f"{symbol}.AX"

    try:
        ticker = yf.Ticker(yahoo_symbol)
        price, currency = None, None
        try:
            info = ticker.fast_info
            price = info.get("last_price")
            currency = info.get("currency")
        except Exception:
            pass
        if price is None or (isinstance(price, float) and math.isnan(price)) or price <= 0:
            history = ticker.history(period="5d")
            closes = history["Close"].dropna() if not history.empty else []
            price = float(closes.iloc[-1]) if len(closes) else None
    except Exception as err:
        raise ValueError("Could not reach the price service. Please enter the price manually.") from err

    if price is None or price <= 0:
        raise ValueError(f"No price found for {yahoo_symbol}. Check the ticker and exchange, "
                         "or enter the price manually.")
    return yahoo_symbol, float(price), currency or ""


def fetch_price():
    """Button callback: look up the price and place it in the price box."""
    symbol = st.session_state.get("ticker", "").strip().upper()
    if not symbol or not symbol.replace(".", "").replace("-", "").isalnum():
        st.session_state["price_msg"] = ("err", "Enter a valid ticker first (e.g. ATOM).")
        return
    try:
        yahoo_symbol, price, currency = lookup_price(symbol, st.session_state.get("exchange", EXCHANGES[0]))
    except ValueError as err:
        st.session_state["price_msg"] = ("err", str(err))
        return
    st.session_state["price"] = round(price, 4)
    st.session_state["price_msg"] = (
        "ok", f"{yahoo_symbol}: {price:,.4f} {currency}".strip() + " (latest available, may be delayed)")

st.set_page_config(page_title="Investment Projection", page_icon="📈", layout="centered")

# ----------------------------------------------------------------------
# Glass styling (real backdrop blur, since this runs in a browser)
# ----------------------------------------------------------------------
st.markdown(
    """
<style>
.stApp {
    background:
        radial-gradient(circle at 15% 12%, rgba(60,200,255,.70) 0, transparent 38%),
        radial-gradient(circle at 88% 38%, rgba(255,120,190,.65) 0, transparent 40%),
        radial-gradient(circle at 20% 90%, rgba(140,110,255,.75) 0, transparent 42%),
        radial-gradient(circle at 85% 95%, rgba(255,190,90,.55) 0, transparent 35%),
        linear-gradient(135deg, #2446be 0%, #6e46c8 50%, #e15a96 100%);
    background-attachment: fixed;
}
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 560px; padding-top: 2.5rem; }

h1, h2, h3, p, label, span, div, li { color: #fff; }
h1 { font-weight: 700; letter-spacing: -0.5px; }

/* glass card */
[data-testid="stForm"] {
    background: rgba(255,255,255,.16);
    border: 1px solid rgba(255,255,255,.38);
    border-radius: 26px;
    padding: 1.4rem 1.4rem 1rem;
    backdrop-filter: blur(24px) saturate(160%);
    -webkit-backdrop-filter: blur(24px) saturate(160%);
    box-shadow: 0 10px 40px rgba(10,15,60,.35), inset 0 1px 0 rgba(255,255,255,.45);
}

/* inputs */
div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] > div {
    background: rgba(255,255,255,.62) !important;
    border: 1px solid rgba(255,255,255,.75) !important;
    border-radius: 14px !important;
}
/* typed text in black */
input, textarea {
    color: #000 !important;
    -webkit-text-fill-color: #000 !important;
    caret-color: #000 !important;
}
input::placeholder, textarea::placeholder {
    color: rgba(0,0,0,.45) !important;
    -webkit-text-fill-color: rgba(0,0,0,.45) !important;
}
/* number-input +/- buttons */
div[data-baseweb="input"] button { background: transparent !important; }
div[data-baseweb="input"] button svg { fill: #000 !important; color: #000 !important; }
/* dropdown (selected value, arrow, and the opened menu) */
div[data-baseweb="select"] * { color: #000 !important; -webkit-text-fill-color: #000 !important; }
div[data-baseweb="select"] svg { fill: #000 !important; }
[data-baseweb="popover"] ul, [data-baseweb="popover"] li {
    background: #fff !important; color: #000 !important;
}
[data-baseweb="popover"] li:hover { background: #e8f1ff !important; }
label p { font-size: .78rem; letter-spacing: .08em; text-transform: uppercase;
          color: rgba(255,255,255,.9) !important; }

/* buttons */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
    width: 100%;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,.55);
    background: linear-gradient(180deg, rgba(90,175,255,.95), rgba(10,110,235,.95));
    color: #fff; font-weight: 600; padding: .65rem 1rem;
    box-shadow: 0 6px 20px rgba(10,80,200,.35);
}
.stButton > button:hover, .stDownloadButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    border-color: #fff; color: #fff; filter: brightness(1.08);
}

/* result pill */
.glass-pill {
    margin: 1rem 0; padding: 1rem; text-align: center;
    background: rgba(255,255,255,.16);
    border: 1px solid rgba(255,255,255,.38);
    border-radius: 20px;
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
}
.glass-pill .small { font-size: .75rem; letter-spacing: .08em; opacity: .8; }
.glass-pill .big { font-size: 2rem; font-weight: 700; }
.fine { font-size: .75rem; opacity: .75; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("Investment Projection")
st.write("See how your money could compound, then download it as an Excel file.")

# ----------------------------------------------------------------------
# Form
# ----------------------------------------------------------------------
t1, t2 = st.columns([3, 2])
t1.text_input("Stock ticker", placeholder="e.g. ATOM", key="ticker")
t2.selectbox("Exchange", EXCHANGES, key="exchange")
st.button("Get live price", on_click=fetch_price)

msg = st.session_state.get("price_msg")
if msg:
    (st.success if msg[0] == "ok" else st.error)(msg[1])

with st.form("inputs"):
    c1, c2 = st.columns(2)
    price = c1.number_input("Current price ($)", min_value=0.0, value=None,
                            placeholder="Current price (or tap Get live price)",
                            format="%.4f", key="price")
    amount = c2.number_input("Investing today ($)", min_value=0.0, value=None,
                             placeholder="Amount to invest", format="%.2f")
    c3, c4 = st.columns(2)
    years = c3.number_input("Time horizon (years)", min_value=1, max_value=100,
                            value=None, step=1, placeholder="Years")
    rate = c4.number_input("Expected return (% / yr)", min_value=-99.0, max_value=1000.0,
                           value=None, placeholder="Return % per year", format="%.2f")
    comp_label = st.selectbox("Compounding", list(COMPOUNDING.keys()))
    submitted = st.form_submit_button("Generate Excel Report")

if submitted:
    clean = st.session_state.get("ticker", "").strip().upper()
    problems = []
    if not clean or not clean.replace(".", "").replace("-", "").isalnum():
        problems.append("Enter a valid ticker (e.g. ATOM, AAPL, CBA.AX).")
    if not price or price <= 0:
        problems.append("Current price must be greater than 0.")
    if not amount or amount <= 0:
        problems.append("Amount must be greater than 0.")
    if not years:
        problems.append("Enter a time horizon in whole years.")
    if rate is None:
        problems.append("Enter an expected annual return.")

    if problems:
        for p in problems:
            st.error(p)
    else:
        comp = COMPOUNDING[comp_label]
        years = int(years)
        final = amount * (1 + rate / 100 / comp) ** (comp * years)
        gain_pct = (final - amount) / amount * 100

        buffer = io.BytesIO()
        build_workbook(clean, price, amount, years, rate, comp, buffer)

        st.markdown(
            f"""<div class="glass-pill">
                <div class="small">PROJECTED VALUE IN {years} YEAR{'S' if years != 1 else ''}</div>
                <div class="big">${final:,.0f}</div>
                <div>{gain_pct:+,.1f}% on ${amount:,.0f}</div></div>""",
            unsafe_allow_html=True,
        )
        st.download_button(
            "Download Excel file",
            data=buffer.getvalue(),
            file_name=f"{clean.replace('.', '_')}_projection.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

st.markdown(
    "<p class='fine'>What-if illustration only. Assumes a constant return each year, "
    "with no fees, taxes or inflation. Not financial advice.</p>",
    unsafe_allow_html=True,
)
