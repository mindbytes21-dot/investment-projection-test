"""
Pure calculation and validation logic for the Investment Projection tool.

Nothing in here touches the UI, the network or the file system, so it is
easy to unit test.
"""

import math
import re
from dataclasses import dataclass

COMPOUNDING = {"Annually": 1, "Semi-annually": 2, "Quarterly": 4, "Monthly": 12}

EXCHANGE_ASX = "Australia (ASX)"
EXCHANGE_AS_TYPED = "US / exactly as typed"
EXCHANGES = [EXCHANGE_ASX, EXCHANGE_AS_TYPED]

# Sensible limits. They stop absurd inputs and floating-point overflow.
MAX_YEARS = 100
MAX_PRICE = 1e9
MAX_AMOUNT = 1e12
MIN_RATE = -99.0
MAX_RATE = 1000.0
MAX_PROJECTED_VALUE = 1e15

# 1-10 letters/digits, optionally followed by . or - and a short suffix
# (e.g. ATOM, CBA.AX, BRK-B, 0700.HK, BTC-USD). Must start with a letter or digit,
# which also keeps spreadsheet-formula characters (= + - @) out of the workbook.
_TICKER_RE = re.compile(r"^[A-Z0-9]{1,10}([.\-][A-Z0-9]{1,6})?$")


@dataclass(frozen=True)
class ProjectionInputs:
    ticker: str
    price: float
    amount: float
    years: int
    rate_pct: float
    comp_per_year: int


def normalize_ticker(raw):
    """Return the cleaned, upper-case ticker or raise ValueError."""
    symbol = (raw or "").strip().upper()
    if not _TICKER_RE.match(symbol):
        raise ValueError("Enter a valid ticker (e.g. ATOM, AAPL, CBA.AX).")
    return symbol


def yahoo_symbol(symbol, exchange):
    """Map a ticker to the symbol Yahoo Finance expects."""
    if exchange == EXCHANGE_ASX and "." not in symbol:
        return f"{symbol}.AX"
    return symbol


def projected_value(amount, years, rate_pct, comp_per_year):
    """Compound growth: amount * (1 + r/m) ** (m * years).

    Raises ValueError instead of OverflowError when the result is unreasonably large.
    """
    periodic = 1 + rate_pct / 100.0 / comp_per_year
    if periodic <= 0:
        raise ValueError("Expected return must be above -100%.")
    periods = comp_per_year * years
    if amount > 0 and periods > 0:
        log_value = math.log(amount) + periods * math.log(periodic)
        if log_value > math.log(MAX_PROJECTED_VALUE):
            raise ValueError("That return and time horizon give an unrealistically large "
                             "result. Please lower the return or the number of years.")
    return amount * periodic ** periods


def _is_number(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def validate_inputs(ticker, price, amount, years, rate_pct, comp_label):
    """Validate raw form values.

    Returns (ProjectionInputs, []) when valid, or (None, [messages...]) listing every problem.
    """
    problems = []

    clean_ticker = None
    try:
        clean_ticker = normalize_ticker(ticker)
    except ValueError as err:
        problems.append(str(err))

    if not _is_number(price) or price <= 0:
        problems.append("Current price must be a number greater than 0.")
    elif price > MAX_PRICE:
        problems.append("Current price is unrealistically large.")

    if not _is_number(amount) or amount <= 0:
        problems.append("Amount to invest must be a number greater than 0.")
    elif amount > MAX_AMOUNT:
        problems.append("Amount to invest is unrealistically large.")

    if (not _is_number(years) or years != int(years) or not 1 <= years <= MAX_YEARS):
        problems.append(f"Time horizon must be a whole number from 1 to {MAX_YEARS} years.")

    if not _is_number(rate_pct):
        problems.append("Enter an expected annual return (for example 8).")
    elif not MIN_RATE <= rate_pct <= MAX_RATE:
        problems.append(f"Expected return must be between {MIN_RATE:g}% and {MAX_RATE:g}%.")

    if comp_label not in COMPOUNDING:
        problems.append("Choose how often returns compound.")

    if problems:
        return None, problems

    inputs = ProjectionInputs(
        ticker=clean_ticker,
        price=float(price),
        amount=float(amount),
        years=int(years),
        rate_pct=float(rate_pct),
        comp_per_year=COMPOUNDING[comp_label],
    )
    try:
        projected_value(inputs.amount, inputs.years, inputs.rate_pct, inputs.comp_per_year)
    except ValueError as err:
        return None, [str(err)]
    return inputs, []
