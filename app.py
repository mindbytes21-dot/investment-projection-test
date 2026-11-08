"""
Investment Projection - web version (Streamlit)

Users open a link, enter their numbers, and download an Excel workbook
(table + chart) to their own computer.

Run locally:   streamlit run app.py
"""

import io

import streamlit as st

from excel_builder import build_workbook

COMPOUNDING = {"Annually": 1, "Semi-annually": 2, "Quarterly": 4, "Monthly": 12}

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
with st.form("inputs"):
    ticker = st.text_input("Stock ticker", placeholder="e.g. ATOM")
    c1, c2 = st.columns(2)
    price = c1.number_input("Current price ($)", min_value=0.0, value=None,
                            placeholder="Current price", format="%.4f")
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
    clean = ticker.strip().upper()
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
