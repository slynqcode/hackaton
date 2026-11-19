"""Independent verification code: accounting invariants, a full-information 'perfect detector',
and a blind evidence solver.  None of this is used to *build* episodes; it re-derives everything
from the public records + policy, so a bug in the generator cannot silently agree with itself."""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from .money import EXPONENTS, convert_minor
from .timeutil import local_date, parse_iso, parse_offset_label, side_of_period


# ------------------------------------------------------------------ shared helpers

class Book:
    """Indexed read-only view over the public tables."""

    def __init__(self, tables: dict, manifest: dict, policy: dict):
        self.t, self.m, self.p = tables, manifest, policy
        self.off = parse_offset_label(manifest["timezone"])
        self.start, self.end = parse_iso(manifest["period_start"]), parse_iso(manifest["period_end"])
        self.rounding = manifest["rounding"]["mode"]
        self.tol = policy["amount_tolerance_minor"]
        self.inv = {r["invoice_id"]: r for r in tables["invoices"]}
        self.pay = {r["payment_id"]: r for r in tables["payments"]}
        self.rows_by_inv = defaultdict(list)   # invoice posting rows (payment_id null)
        self.rows_by_pay = defaultdict(list)
        for r in tables["ledger"]:
            if r["payment_id"] is not None:
                self.rows_by_pay[r["payment_id"]].append(r)
            elif r["invoice_id"] is not None:
                self.rows_by_inv[r["invoice_id"]].append(r)
        self.fx = {(r["date"], r["source_currency"], r["target_currency"]): Decimal(r["rate"]) for r in tables["fx"]}

    def side(self, iso: str) -> str:
        return side_of_period(parse_iso(iso), self.start, self.end)

    def rate(self, d, s, t):
        return Decimal(1) if s == t else self.fx.get((d.isoformat(), s, t))

    def convert(self, amt, s, t, d):
        r = self.rate(d, s, t)
        return None if r is None else convert_minor(amt, s, t, r, self.rounding)

    def ldate(self, iso: str):
        return local_date(parse_iso(iso), self.off)


def norm_lines(inv: dict) -> tuple:
    return tuple(sorted((l["description"], l["quantity"], l["unit_price_minor"], l["amount_minor"]) for l in inv["line_items"]))


def inv_key(inv: dict) -> tuple:
    return (inv["entity_id"], tuple(sorted({l["po_ref"] for l in inv["line_items"]})), norm_lines(inv))


def memo_invoice_ids(b: Book, memo: str) -> list:
    return sorted(i for i in b.inv if i in memo)


def is_advance(b: Book, p: dict) -> bool:
    """Legitimate prepayment on account: no references and the memo names no invoice."""
    return p["invoice_refs"] == [] and not memo_invoice_ids(b, p["memo"]) and p["amount_minor"] > 0


# ------------------------------------------------------------------ accounting invariants (clean books)

def check_clean(tables: dict, manifest: dict, policy: dict) -> list:
    """Return violation strings. Empty list == all equalities hold (the 'before faults' state)."""
    b = Book(tables, manifest, policy)
    v: list = []
    for name, key in (("ledger", "row_id"), ("invoices", "doc_id"), ("payments", "doc_id")):
        ids = [r[key] for r in tables[name]]
        if len(ids) != len(set(ids)):
            v.append(f"duplicate {key} in {name}")
    if len(b.inv) != len(tables["invoices"]) or len(b.pay) != len(tables["payments"]):
        v.append("duplicate invoice_id/payment_id")
    ccys = set(manifest["currencies"])
    groups = defaultdict(lambda: [0, 0])
    for r in tables["ledger"]:
        if r["currency"] not in ccys or r["debit_minor"] < 0 or r["credit_minor"] < 0 or bool(r["debit_minor"]) == bool(r["credit_minor"]):
            v.append(f"bad ledger row {r['row_id']}")
        g = groups[(r["payment_id"] or r["invoice_id"], r["currency"])]
        g[0] += r["debit_minor"]; g[1] += r["credit_minor"]
    for k, (d, c) in groups.items():
        if d != c:
            v.append(f"unbalanced group {k}: Dr {d} != Cr {c}")
    # invoices
    for iid, inv in b.inv.items():
        if sum(l["amount_minor"] for l in inv["line_items"]) != inv["total_minor"]:
            v.append(f"{iid}: lines != total")
        for l in inv["line_items"]:
            if l["quantity"] * l["unit_price_minor"] != l["amount_minor"]:
                v.append(f"{iid}: line math")
        rows = b.rows_by_inv[iid]
        ar = [r for r in rows if r["account"] == "AR"]
        rev = [r for r in rows if r["account"] == "REVENUE"]
        if len(ar) != 1 or len(rev) != 1 or ar[0]["debit_minor"] != inv["total_minor"] or rev[0]["credit_minor"] != inv["total_minor"]:
            v.append(f"{iid}: posting != total")
        if any(r["currency"] != inv["currency"] or r["entity_id"] != inv["entity_id"] for r in rows):
            v.append(f"{iid}: posting ccy/entity mismatch")
        for r in rows:
            if b.side(r["timestamp"]) != b.side(inv["issued_at"]):
                v.append(f"{iid}: period side mismatch")
    # duplicates
    seen = defaultdict(list)
    for iid, inv in b.inv.items():
        seen[inv_key(inv)].append(iid)
    for k, lst in seen.items():
        if len(lst) > 1:
            v.append(f"duplicate invoices {lst}")
    # payments
    for pid, p in b.pay.items():
        refs = p["invoice_refs"]
        if refs is None:
            v.append(f"{pid}: null refs in clean books")
            continue
        if sum(r["allocated_minor"] for r in refs) != p["amount_minor"] and not is_advance(b, p):
            v.append(f"{pid}: not fully allocated")
        if memo_invoice_ids(b, p["memo"]) != sorted(r["invoice_id"] for r in refs):
            v.append(f"{pid}: memo/refs mismatch")
        rows = b.rows_by_pay[pid]
        un = sum(r["credit_minor"] for r in rows if r["account"] == "UNAPPLIED")
        if un and not (is_advance(b, p) and un == p["amount_minor"]):
            v.append(f"{pid}: unapplied in clean books")
        cash = [r for r in rows if r["account"] == "CASH"]
        if len(cash) != 1 or cash[0]["debit_minor"] + cash[0]["credit_minor"] != abs(p["amount_minor"]) or cash[0]["currency"] != p["currency"]:
            v.append(f"{pid}: cash row")
        d = b.ldate(p["timestamp"])
        for ref in refs:
            inv = b.inv.get(ref["invoice_id"])
            if inv is None:
                v.append(f"{pid}: dangling invoice ref"); continue
            ar = [r for r in rows if r["account"] == "AR" and r["invoice_id"] == ref["invoice_id"]]
            exp = b.convert(abs(ref["allocated_minor"]), p["currency"], inv["currency"], d)
            if exp is None:
                v.append(f"{pid}: missing fx rate"); continue
            if len(ar) != 1 or ar[0]["debit_minor"] + ar[0]["credit_minor"] != exp:
                v.append(f"{pid}: AR amount != conversion at policy date")
        for r in rows:
            if b.side(r["timestamp"]) != b.side(p["timestamp"]):
                v.append(f"{pid}: period side mismatch")
    for r in b.fx.values():
        if r <= 0:
            v.append("non-positive fx rate")
    return v


# ------------------------------------------------------------------ perfect detector (full information)

def detect(tables: dict, manifest: dict, policy: dict) -> list:
    """Re-derive every discrepancy from public data only. Used to prove that the declared
    discrepancies are exactly the ones present (no accidental extra inconsistencies)."""
    b = Book(tables, manifest, policy)
    out = []
    groups = defaultdict(list)
    for iid, inv in b.inv.items():
        groups[inv_key(inv)].append(inv)
    for lst in groups.values():
        if len(lst) > 1:
            lst.sort(key=lambda x: parse_iso(x["issued_at"]))
            for extra in lst[1:]:
                out.append(("duplicate_invoice", tuple(sorted([lst[0]["invoice_id"], extra["invoice_id"]])),
                            extra["total_minor"], extra["currency"]))
    for pid, p in b.pay.items():
        refs = p["invoice_refs"] or []
        un = p["amount_minor"] - sum(r["allocated_minor"] for r in refs)
        if un != 0 and not is_advance(b, p):
            out.append(("payment_allocation", tuple(sorted([pid] + memo_invoice_ids(b, p["memo"]))), abs(un), p["currency"]))
        d = b.ldate(p["timestamp"])
        for ref in refs:
            inv = b.inv[ref["invoice_id"]]
            if inv["currency"] == p["currency"]:
                continue
            exp = b.convert(abs(ref["allocated_minor"]), p["currency"], inv["currency"], d)
            ar = [r for r in b.rows_by_pay[pid] if r["account"] == "AR" and r["invoice_id"] == ref["invoice_id"]]
            for r in ar:
                booked = r["debit_minor"] + r["credit_minor"]
                if abs(booked - exp) > b.tol:
                    out.append(("fx_error", (pid,), abs(booked - exp), inv["currency"]))
    for iid, inv in b.inv.items():
        s = b.side(inv["issued_at"])
        if any(b.side(r["timestamp"]) != s for r in b.rows_by_inv[iid]):
            out.append(("period_cutoff", (iid,), inv["total_minor"], inv["currency"]))
    for pid, p in b.pay.items():
        s = b.side(p["timestamp"])
        if any(b.side(r["timestamp"]) != s for r in b.rows_by_pay[pid]):
            out.append(("period_cutoff", (pid,), abs(p["amount_minor"]), p["currency"]))
    return sorted(out)


def truth_tuples(truth: dict) -> list:
    return sorted((i["type"], tuple(sorted(i["affected_ids"])), i["expected_amount_minor"], i["currency"]) for i in truth["issues"])


# ------------------------------------------------------------------ blind evidence solver

def fx_record_id(r: dict) -> str:
    return f"fx:{r['date']}:{r['source_currency']}:{r['target_currency']}"


def make_view(tables: dict, ids) -> dict:
    """Restricted view: only the named records (ledger rows, docs, fx rows)."""
    want = set(ids)
    view = {}
    for r in tables["ledger"]:
        if r["row_id"] in want:
            view[r["row_id"]] = ("ledger", r)
    for name in ("invoices", "payments"):
        for r in tables[name]:
            if r["doc_id"] in want:
                view[r["doc_id"]] = (name, r)
    for r in tables["fx"]:
        if fx_record_id(r) in want:
            view[fx_record_id(r)] = ("fx", r)
    return view


def solve_from_evidence(view: dict, manifest: dict, policy: dict, ftype: str):
    """Derive (affected_ids, amount, currency) from ONLY the records in `view` + public manifest/policy.
    Returns None when the evidence is insufficient to establish the discrepancy."""
    off = parse_offset_label(manifest["timezone"])
    start, end = parse_iso(manifest["period_start"]), parse_iso(manifest["period_end"])
    rounding, tol = manifest["rounding"]["mode"], policy["amount_tolerance_minor"]
    by = lambda tbl: [r for t, r in view.values() if t == tbl]
    side = lambda iso: side_of_period(parse_iso(iso), start, end)
    invs, pays, rows, fxs = by("invoices"), by("payments"), by("ledger"), by("fx")
    if ftype == "duplicate_invoice":
        if len(invs) != 2:
            return None
        a, b = invs
        if a["invoice_id"] == b["invoice_id"] or inv_key(a) != inv_key(b) or a["currency"] != b["currency"] or a["total_minor"] != b["total_minor"]:
            return None
        return (tuple(sorted([a["invoice_id"], b["invoice_id"]])), a["total_minor"], a["currency"])
    if ftype == "payment_allocation":
        if len(pays) != 1:
            return None
        p = pays[0]
        un = [r for r in rows if r["account"] == "UNAPPLIED" and r["payment_id"] == p["payment_id"]]
        if len(un) != 1:
            return None
        refs = p["invoice_refs"] or []
        gap = p["amount_minor"] - sum(r["allocated_minor"] for r in refs)
        if gap != un[0]["credit_minor"] + un[0]["debit_minor"] or gap <= 0:
            return None
        memo_ids = sorted(set(re.findall(r"[A-Za-z]+[-/_][0-9]+", p["memo"])))
        if not memo_ids:   # an advance on account: unapplied by design, not a discrepancy
            return None
        return (tuple(sorted([p["payment_id"]] + memo_ids)), gap, p["currency"])
    if ftype == "fx_error":
        if len(pays) != 1 or len(fxs) != 1:
            return None
        p, fx = pays[0], fxs[0]
        cand = [r for r in rows if r["payment_id"] == p["payment_id"] and r["account"] in ("AR", "FX_CLEARING") and r["currency"] != p["currency"]]
        if not cand or not p["invoice_refs"]:
            return None
        r = cand[0]
        ref = next((x for x in p["invoice_refs"] if x["invoice_id"] == r["invoice_id"]), None)
        d = local_date(parse_iso(p["timestamp"]), off)
        if ref is None or fx["date"] != d.isoformat() or fx["source_currency"] != p["currency"] or fx["target_currency"] != r["currency"]:
            return None
        right = convert_minor(abs(ref["allocated_minor"]), p["currency"], r["currency"], Decimal(fx["rate"]), rounding)
        booked = r["debit_minor"] + r["credit_minor"]
        if abs(booked - right) <= tol:
            return None
        return ((p["payment_id"],), abs(booked - right), r["currency"])
    if ftype == "period_cutoff":
        if len(rows) < 1 or len(invs) + len(pays) != 1:
            return None
        if invs:
            doc, did, ts, amt = invs[0], invs[0]["invoice_id"], invs[0]["issued_at"], invs[0]["total_minor"]
            mine = [r for r in rows if r["invoice_id"] == did and r["payment_id"] is None]
        else:
            doc, did, ts, amt = pays[0], pays[0]["payment_id"], pays[0]["timestamp"], abs(pays[0]["amount_minor"])
            mine = [r for r in rows if r["payment_id"] == did]
        if not any(side(r["timestamp"]) != side(ts) for r in mine):
            return None
        return ((did,), amt, doc["currency"])
    return None
