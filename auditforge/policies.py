"""Four organiser-style baseline policies (+ a reference solver). Each policy is a generator:
    action = yield ...   receives the next observation via send().
Policies only see observations (except Oracle, which is evaluator-side by definition)."""
from __future__ import annotations

import random
from collections import defaultdict
from datetime import timedelta

from .checks import Book, detect, fx_record_id, memo_invoice_ids
from .timeutil import parse_iso, side_of_period


def _fetch_all(table, pages_out):
    cursor = None
    while True:
        obs = yield {"action": "list_records", "table": table, "cursor": cursor, "limit": 50}
        if not obs.get("ok"):
            return
        res = obs["result"]
        pages_out.extend(res["records"])
        cursor = res["next_cursor"]
        if cursor is None:
            return


def _submit(eid, findings):
    return {"action": "submit", "findings": {"episode_id": eid, "findings": findings}}


class RandomExplorer:
    name = "random_explorer"

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)

    def run(self, obs, info):
        rng, eid, seen = self.rng, info["episode_id"], {"ids": [], "docs": [], "amounts": []}
        for _ in range(rng.randint(8, 25)):
            t = rng.choice(["ledger", "invoices", "payments", "fx"])
            o = yield {"action": "list_records", "table": t, "limit": rng.randint(5, 50)}
            if o.get("ok"):
                for r in o["result"]["records"]:
                    for k in ("invoice_id", "payment_id"):
                        if r.get(k):
                            seen["ids"].append(r[k])
                    if r.get("doc_id"):
                        seen["docs"].append(r["doc_id"])
                    for k in ("total_minor", "amount_minor", "debit_minor"):
                        if r.get(k):
                            seen["amounts"].append(abs(r[k]))
            if rng.random() < 0.3:
                yield {"action": "get_record", "table": "ledger", "id": "unknown"}
        fs = []
        for _ in range(rng.randint(0, 3)):
            if seen["ids"]:
                fs.append({"type": rng.choice(["duplicate_invoice", "payment_allocation", "fx_error", "period_cutoff"]),
                           "affected_ids": [rng.choice(seen["ids"])], "claimed_amount_minor": rng.choice(seen["amounts"] or [0]),
                           "currency": rng.choice(obs["manifest"]["currencies"]),
                           "evidence_ids": [rng.choice(seen["docs"])] if seen["docs"] else [], "explanation": "random guess"})
        yield _submit(eid, fs)


class SimpleReconciler:
    """Naive reconciliation heuristics: same-entity+same-total duplicates, string-date cutoff,
    total-amount FX check at the document's own calendar date. Falls for the distractors."""
    name = "simple_reconciler"

    def __init__(self, tz_aware: bool = False, use_allocated: bool = False):
        self.tz_aware, self.use_allocated = tz_aware, use_allocated   # ablation switches (off = the baseline)

    def run(self, obs, info):
        from .timeutil import local_date, parse_offset_label
        eid, man = info["episode_id"], obs["manifest"]
        off = parse_offset_label(man["timezone"])
        start, end = parse_iso(man["period_start"]), parse_iso(man["period_end"])
        day = (lambda ts: local_date(parse_iso(ts), off).isoformat()) if self.tz_aware else (lambda ts: ts[:10])
        led, invs, pays = [], [], []
        yield from _fetch_all("invoices", invs)
        yield from _fetch_all("payments", pays)
        yield from _fetch_all("ledger", led)
        invd = {i["invoice_id"]: i for i in invs}
        by_pay = defaultdict(list)
        for r in led:
            by_pay[r["payment_id"]].append(r)
        by_inv = defaultdict(list)
        for r in led:
            if r["payment_id"] is None:
                by_inv[r["invoice_id"]].append(r)
        fs = []
        # duplicates: same entity + same total within 7 days
        for a in invs:
            for b in invs:
                if a["invoice_id"] < b["invoice_id"] and a["entity_id"] == b["entity_id"] and a["total_minor"] == b["total_minor"] \
                        and abs((parse_iso(a["issued_at"]) - parse_iso(b["issued_at"])).days) <= 7:
                    fs.append({"type": "duplicate_invoice", "affected_ids": [a["invoice_id"], b["invoice_id"]],
                               "claimed_amount_minor": a["total_minor"], "currency": a["currency"],
                               "evidence_ids": [a["doc_id"], b["doc_id"]], "explanation": "same entity and total within 7 days"})
        # allocation gaps
        for p in pays:
            refs = p["invoice_refs"] or []
            gap = p["amount_minor"] - sum(r["allocated_minor"] for r in refs)
            un = [r for r in by_pay[p["payment_id"]] if r["account"] == "UNAPPLIED"]
            if gap > 0 and un:
                fs.append({"type": "payment_allocation", "affected_ids": [p["payment_id"]] + [i for i in invd if i in p["memo"]],
                           "claimed_amount_minor": gap, "currency": p["currency"],
                           "evidence_ids": [p["doc_id"], un[0]["row_id"]], "explanation": "unapplied cash"})
        # cutoff by calendar-date strings
        ps, pe = man["period_start"][:10], man["period_end"][:10]
        inside = (lambda ts: side_of_period(parse_iso(ts), start, end) == "in") if self.tz_aware else (lambda ts: ps <= ts[:10] < pe)
        for i in invs:
            rows = by_inv[i["invoice_id"]]
            if rows and inside(rows[0]["timestamp"]) != inside(i["issued_at"]):
                fs.append({"type": "period_cutoff", "affected_ids": [i["invoice_id"]], "claimed_amount_minor": i["total_minor"],
                           "currency": i["currency"], "evidence_ids": [i["doc_id"], rows[0]["row_id"]], "explanation": "date differs"})
        for p in pays:
            rows = [r for r in by_pay[p["payment_id"]] if r["account"] == "CASH"]
            if rows and inside(rows[0]["timestamp"]) != inside(p["timestamp"]):
                fs.append({"type": "period_cutoff", "affected_ids": [p["payment_id"]], "claimed_amount_minor": abs(p["amount_minor"]),
                           "currency": p["currency"], "evidence_ids": [p["doc_id"], rows[0]["row_id"]], "explanation": "date differs"})
        # fx: total amount at the document's own calendar date
        for p in pays:
            refs = p["invoice_refs"] or []
            if not refs:
                continue
            inv = invd.get(refs[0]["invoice_id"])
            if not inv or inv["currency"] == p["currency"]:
                continue
            fid = f"fx:{day(p['timestamp'])}:{p['currency']}:{inv['currency']}"
            o = yield {"action": "get_record", "table": "fx", "id": fid}
            if not o.get("ok"):
                continue
            from decimal import Decimal
            from .money import convert_minor
            base_amt = abs(refs[0]["allocated_minor"]) if self.use_allocated else abs(p["amount_minor"])
            exp = convert_minor(base_amt, p["currency"], inv["currency"], Decimal(o["result"]["rate"]),
                                man["rounding"]["mode"])
            ar = [r for r in by_pay[p["payment_id"]] if r["account"] == "AR"]
            if ar and abs(ar[0]["credit_minor"] + ar[0]["debit_minor"] - exp) > 1:
                fs.append({"type": "fx_error", "affected_ids": [p["payment_id"]],
                           "claimed_amount_minor": abs(ar[0]["credit_minor"] + ar[0]["debit_minor"] - exp),
                           "currency": inv["currency"], "evidence_ids": [p["doc_id"], ar[0]["row_id"], fid],
                           "explanation": "rate mismatch"})
        yield _submit(eid, fs[:30])


class FlagAll:
    """Attack: accuse every document of every error type (up to the 30-finding cap)."""
    name = "flag_all"

    def run(self, obs, info):
        invs, pays = [], []
        yield from _fetch_all("invoices", invs)
        yield from _fetch_all("payments", pays)
        fs = []
        types = ["duplicate_invoice", "payment_allocation", "fx_error", "period_cutoff"]
        docs = [(d["invoice_id"], d["total_minor"], d["currency"], d["doc_id"]) for d in invs] + \
               [(d["payment_id"], abs(d["amount_minor"]), d["currency"], d["doc_id"]) for d in pays]
        k = 0
        for did, amt, ccy, doc in docs:
            for t in types:
                fs.append({"type": t, "affected_ids": [did], "claimed_amount_minor": amt, "currency": ccy,
                           "evidence_ids": [doc], "explanation": "flag everything"})
            k += 1
            if len(fs) >= 30:
                break
        yield _submit(info["episode_id"], fs[:30])


class Oracle:
    """Evaluator-side only: submits the true findings with the first acceptable evidence set.
    Measures the maximum attainable reward; says nothing about agent ability."""
    name = "oracle"

    def __init__(self, truth: dict):
        self.truth = truth

    def run(self, obs, info):
        fs = [{"type": i["type"], "affected_ids": list(i["affected_ids"]), "claimed_amount_minor": i["expected_amount_minor"],
               "currency": i["currency"], "evidence_ids": list(i["acceptable_evidence_sets"][0]),
               "explanation": "oracle"} for i in self.truth["issues"]]
        yield _submit(info["episode_id"], fs)


class ReferenceSolver:
    """Not one of the four required baselines: proves episodes are solvable through the public tool API alone.
    Pages every table, rebuilds the books, applies the policy exactly (checks.detect) and cites evidence."""
    name = "reference_solver"

    def run(self, obs, info):
        man = obs["manifest"]
        t = {"ledger": [], "invoices": [], "payments": [], "fx": []}
        for name in ("invoices", "payments", "ledger", "fx"):
            yield from _fetch_all(name, t[name])
        o = yield {"action": "get_record", "table": "policy", "id": "policy"}
        policy = o["result"]
        b = Book(t, man, policy)
        fs = []
        for typ, ids, amt, ccy in detect(t, man, policy):
            if typ == "duplicate_invoice":
                ev = [b.inv[i]["doc_id"] for i in ids]
            elif typ == "payment_allocation":
                p = b.pay[ids[0] if ids[0] in b.pay else ids[1]]
                un = [r for r in b.rows_by_pay[p["payment_id"]] if r["account"] == "UNAPPLIED"]
                ev = [p["doc_id"], un[0]["row_id"]]
            elif typ == "fx_error":
                p = b.pay[ids[0]]
                ar = [r for r in b.rows_by_pay[p["payment_id"]] if r["account"] == "AR"][0]
                inv = b.inv[ar["invoice_id"]]
                ev = [p["doc_id"], ar["row_id"], f"fx:{b.ldate(p['timestamp']).isoformat()}:{p['currency']}:{inv['currency']}"]
            else:
                d = b.inv.get(ids[0]) or b.pay[ids[0]]
                rows = b.rows_by_inv[ids[0]] if ids[0] in b.inv else [r for r in b.rows_by_pay[ids[0]] if r["account"] == "CASH"]
                ev = [d["doc_id"], rows[0]["row_id"]]
            fs.append({"type": typ, "affected_ids": list(ids), "claimed_amount_minor": amt, "currency": ccy,
                       "evidence_ids": ev, "explanation": "reference solver"})
        yield _submit(info["episode_id"], fs)


class ZeroAgent:
    """Diagnostic, not one of the four required baselines: submits an empty answer at step 1.
    Shows what 'always stay silent' earns: +1 on clean books, -1 whenever there is any error."""
    name = "zero_agent"

    def run(self, obs, info):
        yield _submit(info["episode_id"], [])
