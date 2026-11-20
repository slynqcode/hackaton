"""Arithmetic-only calculator: + - * / parentheses, unary signs, decimal literals. No names, calls, exponents."""
from __future__ import annotations

import re
from decimal import Decimal, DivisionByZero, InvalidOperation, localcontext

_TOK = re.compile(r"\s*([0-9]+(?:\.[0-9]+)?|[()+\-*/])", re.ASCII)   # ASCII digits only
MAX_LEN, MAX_DIGITS = 300, 60


class CalcError(Exception):
    pass


def _tokenize(s: str) -> list:
    pos, out = 0, []
    s = s.strip()
    while pos < len(s):
        m = _TOK.match(s, pos)
        if not m:
            raise CalcError("syntax")
        tok = m.group(1)
        if tok[0].isdigit() and len(tok) > MAX_DIGITS:
            raise CalcError("too_long_number")
        out.append(tok)
        pos = m.end()
    if not out:
        raise CalcError("empty")
    return out


def evaluate(expr: str) -> str:
    if not isinstance(expr, str) or len(expr) > MAX_LEN:
        raise CalcError("invalid_expression")
    toks, i = _tokenize(expr), [0]

    def peek():
        return toks[i[0]] if i[0] < len(toks) else None

    def eat():
        t = toks[i[0]]; i[0] += 1; return t

    def expr_():
        v = term()
        while peek() in ("+", "-"):
            op = eat(); r = term()
            v = v + r if op == "+" else v - r
        return v

    def term():
        v = unary()
        while peek() in ("*", "/"):
            op = eat(); r = unary()
            v = v * r if op == "*" else v / r
        return v

    def unary():
        if peek() in ("+", "-"):
            op = eat(); v = unary()
            return -v if op == "-" else v
        return atom()

    def atom():
        t = peek()
        if t is None:
            raise CalcError("syntax")
        if t == "(":
            eat(); v = expr_()
            if peek() != ")":
                raise CalcError("syntax")
            eat(); return v
        if t[0].isdigit():
            eat(); return Decimal(t)
        raise CalcError("syntax")

    try:
        with localcontext() as ctx:
            ctx.prec = 40
            v = expr_()
            if i[0] != len(toks):
                raise CalcError("syntax")
            v = +v
    except (DivisionByZero, InvalidOperation, ZeroDivisionError):
        raise CalcError("arithmetic")
    s = format(v, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s or "0"
