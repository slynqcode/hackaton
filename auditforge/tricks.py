"""Shortcut rules ("tricks") that skip the real accounting logic, measured against the truth.

Each rule reads only public tables. A good environment makes every trick pay with false accusations (FP) or misses
(FN); the real rule (period of the document vs period of the posting, line-item comparison, memo + refs) does not.
Used by `python -m auditforge.cli analysis` -> reports/failure_analysis.md.
"""
from __future__ import annotations

from collections import defaultdict

from .checks import Book
from .timeutil import parse_iso


def _minutes(a: str, b: str) -> float:
    return (parse_iso(a) - parse_iso(b)).total_seconds() / 60


def cutoff_delay(t, b, lo=0, hi=240):
    """period_cutoff = posting delay outside [lo, hi] minutes (no period / time-zone logic)."""
    out = set()
    for iid, inv in b.inv.items():
        if any(not lo <= _minutes(r["timestamp"], inv["issued_at"]) <= hi for r in b.rows_by_inv[iid]):
            out.add(iid)
    for pid, p in b.pay.items():
        if any(not lo <= _minutes(r["timestamp"], p["timestamp"]) <= hi for r in b.rows_by_pay[pid] if r["account"] == "CASH"):
            out.add(pid)
    return out


def cutoff_delay_window(t, b):
    """period_cutoff = posting before the document or 4-24 h after it."""
    out = set()
    for iid, inv in b.inv.items():
        if any((m < 0 or 240 < m <= 1440) for m in (_minutes(r["timestamp"], inv["issued_at"]) for r in b.rows_by_inv[iid])):
            out.add(iid)
    for pid, p in b.pay.items():
        if any((m < 0 or 240 < m <= 1440) for m in (_minutes(r["timestamp"], p["timestamp"]) for r in b.rows_by_pay[pid] if r["account"] == "CASH")):
            out.add(pid)
    return out


def _pairs(groups):
    out = set()
    for lst in groups.values():
        if len(lst) > 1:
            lst.sort(key=lambda x: parse_iso(x["issued_at"]))
            for extra in lst[1:]:
                out.add(frozenset([lst[0]["invoice_id"], extra["invoice_id"]]))
    return out


def dup_same_po(t, b):
    """duplicate_invoice = same entity and po_ref (no line comparison)."""
    g = defaultdict(list)
    for inv in b.inv.values():
        g[(inv["entity_id"], tuple(sorted({l["po_ref"] for l in inv["line_items"]})))].append(inv)
    return _pairs(g)


def dup_same_po_amount(t, b):
    """duplicate_invoice = same entity, po_ref, currency and total (no line comparison)."""
    g = defaultdict(list)
    for inv in b.inv.values():
        g[(inv["entity_id"], tuple(sorted({l["po_ref"] for l in inv["line_items"]})), inv["currency"], inv["total_minor"])].append(inv)
    return _pairs(g)


def alloc_refs(t, b):
    """payment_allocation = invoice_refs null, or sum(refs) != amount (memo not read)."""
    out = set()
    for pid, p in b.pay.items():
        refs = p["invoice_refs"]
        if refs is None or sum(r["allocated_minor"] for r in refs) != p["amount_minor"]:
            out.add(pid)
    return out


def alloc_refs_nonempty(t, b):
    """payment_allocation = invoice_refs null, or non-empty refs whose sum != amount (memo not read)."""
    out = set()
    for pid, p in b.pay.items():
        refs = p["invoice_refs"]
        if refs is None or (refs and sum(r["allocated_minor"] for r in refs) != p["amount_minor"]):
            out.add(pid)
    return out


TRICKS = [
    ("period_cutoff", "posting delay outside 0-4 h", cutoff_delay),
    ("period_cutoff", "posting before the document or 4-24 h after it", cutoff_delay_window),
    ("duplicate_invoice", "same entity + po_ref", dup_same_po),
    ("duplicate_invoice", "same entity + po_ref + currency + total", dup_same_po_amount),
    ("payment_allocation", "refs null or sum(refs) != amount", alloc_refs),
    ("payment_allocation", "refs null or non-empty refs with sum != amount", alloc_refs_nonempty),
]


def _truth_keys(ep, ftype, b):
    keys = set()
    for i in ep.truth["issues"]:
        if i["type"] != ftype:
            continue
        ids = i["affected_ids"]
        if ftype == "duplicate_invoice":
            keys.add(frozenset(ids))
        elif ftype == "payment_allocation":
            keys.add(next(x for x in ids if x in b.pay))
        else:
            keys.add(ids[0])
    return keys


def measure(episodes) -> list:
    """-> [{type, rule, tp, fp, fn}] summed over the episodes."""
    rows = []
    for ftype, name, fn in TRICKS:
        tp = fp = fnn = 0
        for ep in episodes:
            b = Book(ep.tables, ep.manifest, ep.policy)
            got, want = fn(ep.tables, b), _truth_keys(ep, ftype, b)
            tp += len(got & want); fp += len(got - want); fnn += len(want - got)
        rows.append({"type": ftype, "rule": name, "tp": tp, "fp": fp, "fn": fnn})
    return rows
