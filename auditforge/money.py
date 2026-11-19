"""Money helpers. Money is always integer minor units; rates are Decimal strings."""
from __future__ import annotations

from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal, localcontext

EXPONENTS = {"USD": 2, "EUR": 2, "GBP": 2, "CHF": 2, "KZT": 2, "JPY": 0, "KWD": 3}

_MODES = {"half_up": ROUND_HALF_UP, "half_even": ROUND_HALF_EVEN}


def exponent(ccy: str) -> int:
    return EXPONENTS[ccy]


def rounding_mode(name: str):
    return _MODES[name]


def convert_minor(amount_minor: int, src: str, dst: str, rate: Decimal, rounding: str) -> int:
    """Convert integer minor units src->dst. rate = dst units per 1 src unit (major units)."""
    with localcontext() as ctx:
        ctx.prec = 50
        major = Decimal(amount_minor) / (Decimal(10) ** EXPONENTS[src])
        target_minor = major * rate * (Decimal(10) ** EXPONENTS[dst])
        return int(target_minor.quantize(Decimal(1), rounding=_MODES[rounding]))


def fmt_major(amount_minor: int, ccy: str) -> str:
    e = EXPONENTS[ccy]
    sign = "-" if amount_minor < 0 else ""
    a = abs(amount_minor)
    if e == 0:
        return f"{sign}{a}"
    return f"{sign}{a // 10**e}.{a % 10**e:0{e}d}"
