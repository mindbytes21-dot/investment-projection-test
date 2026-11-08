"""
Live price lookup via Yahoo Finance (yfinance).

The data source is injectable (`ticker_factory`) so tests never touch the network.
Prices from Yahoo can be delayed by roughly 15 minutes.
"""

import math
from dataclasses import dataclass

from calc import yahoo_symbol


class PriceError(Exception):
    """Raised with a user-friendly message when a price cannot be obtained."""


@dataclass(frozen=True)
class PriceQuote:
    symbol: str      # the symbol actually queried, e.g. ATOM.AX
    price: float
    currency: str    # e.g. AUD (may be empty if Yahoo does not say)


def _clean_price(value):
    """Return value as a positive finite float, else None."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def _default_factory(symbol):
    import yfinance as yf  # imported lazily so unit tests do not need it
    return yf.Ticker(symbol)


def fetch_price(symbol, exchange, ticker_factory=None):
    """Return a PriceQuote for `symbol` or raise PriceError."""
    factory = ticker_factory or _default_factory
    queried = yahoo_symbol(symbol, exchange)

    try:
        ticker = factory(queried)
    except Exception as err:
        raise PriceError("Could not reach the price service. "
                         "Please enter the price manually.") from err

    price, currency = None, ""
    failures = 0

    # 1) fast path: last traded price
    try:
        info = ticker.fast_info
        price = _clean_price(info.get("last_price"))
        currency = info.get("currency") or ""
    except Exception:
        failures += 1

    # 2) fallback: most recent daily close
    if price is None:
        try:
            history = ticker.history(period="5d")
            if history is not None and not history.empty:
                closes = history["Close"].dropna()
                if len(closes):
                    price = _clean_price(closes.iloc[-1])
        except Exception:
            failures += 1

    if price is None:
        if failures == 2:
            raise PriceError("Could not reach the price service. "
                             "Please enter the price manually.")
        raise PriceError(f"No price found for {queried}. Check the ticker and exchange, "
                         "or enter the price manually.")

    return PriceQuote(symbol=queried, price=price, currency=str(currency))
