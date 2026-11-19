"""Episode generator.

Pipeline (see docs/DESIGN.md):
  1. hidden company HISTORY (entities, invoices, payments, FX walk) -- internally consistent;
  2. CLEAN books rendered from history with no faults (accounting equalities hold);
  3. FAULT PLAN: each error is a recorded causal mutation (operator) applied at render time;
  4. FAULTED books rendered; diff(clean, faulted) is stored as provenance;
  5. truth.json is built from the plan + faulted ledger row ids (evidence).
Everything is a pure function of (seed, config, ENV_VERSION). Only stdlib is used.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from . import ENV_VERSION, SCHEMA_VERSION
from .money import EXPONENTS, convert_minor
from .timeutil import local_date, offset_label, side_of_period, tz_from_minutes, to_iso

FAULT_TYPES = ["duplicate_invoice", "payment_allocation", "fx_error", "period_cutoff"]
INTERACTIONS = ["partial_fx", "cutoff_fx"]
MAX_ISSUES = 12

DEFAULT_CONFIG: dict[str, Any] = {
    "n_invoices": 62,
    "n_entities": 9,
    "faults": {"duplicate_invoice": 1, "payment_allocation": 1, "fx_error": 1, "period_cutoff": 1},
    "interactions": [],
    "distractors": {
        "installments": 3, "refunds": 2, "multi_invoice": 2, "recurring": 2,
        "same_amount_near": 3, "boundary_invoices": 8, "boundary_cross_ok": 4, "cross_ccy_ok": 6, "advances": 2,
    },
    "company_offset_minutes": None,
    "period_months": None,
    "rounding": None,
    "currencies": None,
    "id_style": None,
    "id_salt": "",
}

DOC_OFFSETS = [-480, -300, 0, 60, 120, 180, 300, 330, 480, 540]
COMPANY_OFFSETS = [300, 180, 60, -300, 480, 540, -180, 330, -420, 120, 0]
USD_VALUE = {"USD": "1", "EUR": "1.08", "GBP": "1.27", "CHF": "1.12", "KZT": "0.0020", "JPY": "0.0067", "KWD": "3.25"}
PRICE_RANGES = {"USD": (50, 4000), "EUR": (50, 4000), "GBP": (40, 3500), "CHF": (50, 4000),
                "KZT": (25000, 2000000), "JPY": (5000, 400000), "KWD": (20, 1500)}
CATALOG = ["Consulting services", "Software license", "Support plan", "Implementation fee", "Training session",
           "Hardware lease", "Data processing", "Audit preparation", "Cloud hosting", "Maintenance retainer",
           "Integration work", "Analytics package"]
ID_STYLES = [
    {"inv": "INV-{:05d}", "pay": "PAY-{:05d}", "ent": "CUST-{:03d}", "doc": "DOC-{:07d}", "row": "JE{:08d}"},
    {"inv": "SI/{:06d}", "pay": "RCP/{:06d}", "ent": "E{:04d}", "doc": "D{:08d}", "row": "L{:07d}"},
    {"inv": "F-{:05d}", "pay": "P-{:05d}", "ent": "C{:03d}", "doc": "doc_{:07d}", "row": "r{:08d}"},
]
_DIGITS = {"inv": 5, "pay": 5, "ent": 3, "doc": 7, "row": 8}
FX_DP = Decimal("0.0000000001")


# ----------------------------------------------------------------------------- config

def resolve_config(config: dict | None) -> dict:
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    for k, v in (config or {}).items():
        if k not in cfg:
            raise ValueError(f"unknown config key: {k}")
        if isinstance(cfg[k], dict) and isinstance(v, dict):
            for kk, vv in v.items():
                if kk not in cfg[k] and k == "distractors":
                    raise ValueError(f"unknown distractor key: {kk}")
                if k == "faults" and kk not in FAULT_TYPES:
                    raise ValueError(f"unknown fault type: {kk}")
                cfg[k][kk] = vv
        else:
            cfg[k] = v
    for t in cfg["interactions"]:
        if t not in INTERACTIONS:
            raise ValueError(f"unknown interaction: {t}")
    if not (isinstance(cfg["n_entities"], int) and 3 <= cfg["n_entities"] <= 40):
        raise ValueError("n_entities must be an int in [3, 40]")
    if not (isinstance(cfg["n_invoices"], int) and 30 <= cfg["n_invoices"] <= 80):
        raise ValueError("n_invoices must be an int in [30, 80] (keeps documents <= 200)")
    if cfg["currencies"] is not None:
        if len(set(cfg["currencies"])) < 2 or any(c not in EXPONENTS for c in cfg["currencies"]):
            raise ValueError("currencies: >=2 distinct supported currencies")
    if cfg["rounding"] not in (None, "half_up", "half_even"):
        raise ValueError("rounding must be half_up or half_even")
    if cfg["company_offset_minutes"] is not None and not (-720 <= cfg["company_offset_minutes"] <= 840):
        raise ValueError("company_offset_minutes out of range")
    if cfg["period_months"] not in (None, 1, 2, 3):
        raise ValueError("period_months must be 1, 2 or 3")
    for k, v in list(cfg["faults"].items()) + list(cfg["distractors"].items()):
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise ValueError(f"{k} must be a non-negative int")
    total = sum(cfg["faults"].values()) + 2 * len(cfg["interactions"])
    if total > MAX_ISSUES:
        raise ValueError(f"too many issues: {total} > {MAX_ISSUES}")
    return cfg


def config_hash(cfg: dict) -> str:
    return hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:16]


def make_episode_id(seed: int, cfg: dict) -> str:
    raw = f"{seed}|{config_hash(cfg)}|{ENV_VERSION}|{cfg['id_salt']}|episode"
    return "ep-" + hashlib.sha256(raw.encode()).hexdigest()[:12]


# ----------------------------------------------------------------------------- ids

class Ids:
    """Key-addressed pseudo-random ids: independent of call order (clean/faulted renders agree)."""

    def __init__(self, token: str, style: int):
        self.token, self.style = token, ID_STYLES[style]
        self.used: dict[str, set] = defaultdict(set)
        self.memo: dict[tuple, str] = {}

    def get(self, kind: str, key: str) -> str:
        mk = (kind, key)
        if mk in self.memo:
            return self.memo[mk]
        mod = 10 ** _DIGITS[kind]
        n = int.from_bytes(hashlib.sha256(f"{self.token}|{kind}|{key}".encode()).digest()[:8], "big") % mod
        while n in self.used[kind]:
            n = (n + 1) % mod
        self.used[kind].add(n)
        self.memo[mk] = self.style[kind].format(n)
        return self.memo[mk]


# ----------------------------------------------------------------------------- history model

@dataclass
class Inv:
    key: str
    ent: str
    ccy: str
    issued: datetime
    due: datetime
    lines: list
    po: str
    doc_off: int = 0
    post_off: int = 0
    post_ts: datetime | None = None
    tags: set = field(default_factory=set)

    @property
    def total(self) -> int:
        return sum(l["amount_minor"] for l in self.lines)


@dataclass
class Pay:
    key: str
    ent: str
    ccy: str
    ts: datetime
    amount: int
    allocs: list  # [(inv_key, alloc_minor_in_payment_ccy)]
    doc_off: int = 0
    post_off: int = 0
    post_ts: datetime | None = None
    tags: set = field(default_factory=set)
    refund: bool = False


@dataclass
class Ctx:
    seed: int
    cfg: dict
    off: int
    start: datetime
    end: datetime
    ccys: list
    base: str
    rounding: str
    rates: dict
    ids: Ids
    ents: dict
    invs: dict = field(default_factory=dict)
    pays: dict = field(default_factory=dict)
    wstart: datetime = None
    wend: datetime = None

    def rate(self, d: date, s: str, t: str) -> Decimal:
        return Decimal(1) if s == t else self.rates[(d.isoformat(), s, t)]

    def ldate(self, dt: datetime) -> date:
        return local_date(dt, self.off)

    def side(self, dt: datetime) -> str:
        return side_of_period(dt, self.start, self.end)


def _R(seed: int, ck: str, name: str) -> random.Random:
    return random.Random(f"{seed}|{ck}|{name}")


def _rand_instant(rng, lo: datetime, hi: datetime) -> datetime:
    mins = int((hi - lo).total_seconds() // 60)
    return lo + timedelta(minutes=rng.randrange(mins))


# ----------------------------------------------------------------------------- history builder

def _build_fx(rng, ccys, base, d0: date, d1: date):
    vals = {c: Decimal(USD_VALUE[c]) / Decimal(USD_VALUE[base]) for c in ccys}
    rates = {}
    d = d0
    while d <= d1:
        for c in ccys:
            if c != base:
                bp = rng.randint(30, 120) * rng.choice([-1, 1])
                vals[c] = (vals[c] * (Decimal(10000 + bp) / Decimal(10000))).quantize(Decimal("1e-14"))
        for s in ccys:
            for t in ccys:
                if s != t:
                    rates[(d.isoformat(), s, t)] = (vals[s] / vals[t]).quantize(FX_DP)
        d += timedelta(days=1)
    return rates


def _price(rng, ccy):
    lo, hi = PRICE_RANGES[ccy]
    major = rng.randrange(lo, hi, 5 if hi > 100 else 1)
    return major * 10 ** EXPONENTS[ccy]


def _make_lines(rng, ccy, po, descs=None):
    n = rng.randint(1, 4)
    lines = []
    for i in range(n):
        qty = rng.randint(1, 12)
        unit = _price(rng, ccy)
        lines.append({"line_no": i + 1, "description": (descs[i % len(descs)] if descs else rng.choice(CATALOG)),
                      "quantity": qty, "unit_price_minor": unit, "amount_minor": qty * unit, "po_ref": po})
    return lines


def _boundary_time(rng, ctx: Ctx, which: str, utc_mismatch: bool = False):
    b = ctx.end if which == "end" else ctx.start
    sign = rng.choice([-1, 1])
    if utc_mismatch and ctx.off != 0:
        span = max(12, abs(ctx.off) - 10)
        mins = rng.randint(10, span)
        sign = 1 if ctx.off > 0 else -1   # off>0: just after local midnight (UTC date is previous day)
        return b + timedelta(minutes=sign * mins)
    return b + timedelta(minutes=sign * rng.randint(5, 30 * 60))


def _post_ts(rng, ctx: Ctx, ts: datetime) -> datetime:
    cand = ts + timedelta(minutes=rng.randrange(0, 241))
    return cand if ctx.side(cand) == ctx.side(ts) else ts


def build_context(seed: int, cfg: dict) -> tuple[Ctx, random.Random]:
    ck = config_hash(cfg)
    rs = _R(seed, ck, "setup")
    off = cfg["company_offset_minutes"] if cfg["company_offset_minutes"] is not None else rs.choice(COMPANY_OFFSETS)
    months = cfg["period_months"] or rs.choice([1, 2, 3])
    m0 = rs.randint(1, 9)
    sd, ed = date(2026, m0, 1), date(2026, m0 + months, 1)
    tz = tz_from_minutes(off)
    start = datetime(sd.year, sd.month, sd.day, tzinfo=tz)
    end = datetime(ed.year, ed.month, ed.day, tzinfo=tz)
    ccys = list(cfg["currencies"]) if cfg["currencies"] else rs.sample(["USD", "EUR", "GBP", "KZT", "JPY"], 3)
    base = ccys[0]
    rounding = cfg["rounding"] or rs.choice(["half_up", "half_even"])
    style = cfg["id_style"] if cfg["id_style"] is not None else rs.randrange(len(ID_STYLES))
    ids = Ids(f"{seed}|{ck}|{cfg['id_salt']}", style)
    rates = _build_fx(_R(seed, ck, "fx"), ccys, base, sd - timedelta(days=40), ed + timedelta(days=16))
    ctx = Ctx(seed, cfg, off, start, end, ccys, base, rounding, rates, ids, {})
    ctx.wstart, ctx.wend = start - timedelta(days=10), end + timedelta(days=10)
    return ctx, _R(seed, ck, "history")


def _new_inv(ctx, rng, ent_key, issued, tags=None, descs=None, lines=None, po=None) -> Inv:
    ent = ctx.ents[ent_key]
    key = f"I{len(ctx.invs):04d}"
    po = po or f"PO-{rng.randrange(10**6):06d}"
    due = issued + timedelta(days=rng.choice([14, 30, 45]))
    inv = Inv(key, ent_key, ent["inv_ccy"], issued, due, lines or _make_lines(rng, ent["inv_ccy"], po, descs), po,
              rng.choice(DOC_OFFSETS), rng.choice(DOC_OFFSETS), None, set(tags or ()))
    inv.post_ts = _post_ts(rng, ctx, issued)
    ctx.invs[key] = inv
    return inv


def _receipt_amount(ctx, inv: Inv, pay_ccy: str, ts: datetime, num=1, den=1) -> int:
    part = inv.total * num // den
    if pay_ccy == inv.ccy:
        return part
    return convert_minor(part, inv.ccy, pay_ccy, ctx.rate(ctx.ldate(ts), inv.ccy, pay_ccy), ctx.rounding)


def _new_pay(ctx, rng, inv: Inv, ts, amount, alloc=None, tags=None, refund=False) -> Pay:
    key = f"P{len(ctx.pays):04d}"
    pay = Pay(key, inv.ent, ctx.ents[inv.ent]["pay_ccy"], ts, amount, [(inv.key, amount if alloc is None else alloc)],
              rng.choice(DOC_OFFSETS), rng.choice(DOC_OFFSETS), None, set(tags or ()), refund)
    pay.post_ts = _post_ts(rng, ctx, ts)
    ctx.pays[key] = pay
    return pay


def build_history(ctx: Ctx, rng) -> dict:
    cfg, dis = ctx.cfg, ctx.cfg["distractors"]
    # entities
    for i in range(cfg["n_entities"]):
        ic = rng.choice([ctx.base, ctx.base] + ctx.ccys)
        pc = ic if rng.random() < 0.6 else rng.choice([c for c in ctx.ccys if c != ic])
        ctx.ents[f"E{i:02d}"] = {"inv_ccy": ic, "pay_ccy": pc}
    ek = list(ctx.ents)
    # guarantee >=1 cross-currency entity (E00) and >=2 same-currency entities (E01, E02): FX faults,
    # cutoff receipts and distractors all need them. Previously small n_entities could crash here.
    ctx.ents[ek[0]]["pay_ccy"] = [c for c in ctx.ccys if c != ctx.ents[ek[0]]["inv_ccy"]][0]
    for e in ek[1:3]:
        ctx.ents[e]["pay_ccy"] = ctx.ents[e]["inv_ccy"]
    cross_ents = [e for e in ek if ctx.ents[e]["inv_ccy"] != ctx.ents[e]["pay_ccy"]]
    same_ents = [e for e in ek if e not in cross_ents]

    n_b_inv = max(dis["boundary_invoices"], 2 * cfg["faults"]["period_cutoff"] + 2)
    # generic + boundary invoices
    for i in range(cfg["n_invoices"]):
        e = rng.choice(ek)
        if i < n_b_inv:
            ts = _boundary_time(rng, ctx, rng.choice(["start", "end"]))
            _new_inv(ctx, rng, e, ts, {"boundary"})
        else:
            _new_inv(ctx, rng, e, _rand_instant(rng, ctx.wstart, ctx.wend))
    # recurring (subscription) distractors: same entity & lines & amount, different po_ref and period tag
    for s in range(dis["recurring"]):
        e = rng.choice(ek)
        t0 = _rand_instant(rng, ctx.wstart, ctx.wstart + timedelta(days=30))
        base_lines = _make_lines(rng, ctx.ents[e]["inv_ccy"], "x", ["Subscription"] * 1)
        for j in range(3):
            ts = t0 + timedelta(days=30 * j + rng.randint(0, 2))
            if ts >= ctx.wend:
                continue
            po = f"SUB-{s:02d}{j}-{rng.randrange(10**4):04d}"
            lines = copy.deepcopy(base_lines)
            for l in lines:
                l["po_ref"], l["description"] = po, f"Subscription {ts.date().isoformat()[:7]}"
            _new_inv(ctx, rng, e, ts, {"recurring"}, lines=lines, po=po)
    # same-amount near pairs: identical lines, different po_ref, days apart (legit repeated amounts)
    for s in range(dis["same_amount_near"]):
        e = rng.choice(ek)
        t0 = _rand_instant(rng, ctx.wstart, ctx.wend - timedelta(days=8))
        a = _new_inv(ctx, rng, e, t0, {"pair"})
        po2 = f"PO-{rng.randrange(10**6):06d}"
        lines = copy.deepcopy(a.lines)
        for l in lines:
            l["po_ref"] = po2
        _new_inv(ctx, rng, e, t0 + timedelta(days=rng.randint(1, 6), minutes=rng.randrange(600)), {"pair"},
                 lines=lines, po=po2)

    # payments for invoices ---------------------------------------------------------------
    inv_list = list(ctx.invs.values())
    elig = [i for i in inv_list if ctx.ents[i.ent]["inv_ccy"] == ctx.ents[i.ent]["pay_ccy"] and "boundary" not in i.tags]
    rng.shuffle(elig)
    special: dict[str, str] = {}
    for kind, n in (("installments", dis["installments"]), ("refunds", dis["refunds"])):
        for _ in range(n):
            if elig:
                special[elig.pop().key] = kind
    by_ent = defaultdict(list)
    for i in elig:
        by_ent[i.ent].append(i)
    multi_pairs = []
    for _ in range(dis["multi_invoice"]):
        pool = [v for v in by_ent.values() if len(v) >= 2]
        if not pool:
            break
        v = rng.choice(pool)
        a, b = v.pop(), v.pop()
        multi_pairs.append((a, b))
        special[a.key] = special[b.key] = "multi"

    def pay_ts(inv, lo=1, hi=30):
        ts = inv.issued + timedelta(minutes=rng.randrange(lo * 1440, hi * 1440))
        return ts if ts < ctx.wend else None

    done_multi = set()
    for inv in inv_list:
        kind = special.get(inv.key)
        pc = ctx.ents[inv.ent]["pay_ccy"]
        if kind == "multi":
            continue
        if kind != "installments" and kind != "refunds" and rng.random() > 0.72:
            continue
        ts = pay_ts(inv)
        if ts is None:
            continue
        if kind == "installments":
            first = inv.total * 6 // 10
            p1 = _new_pay(ctx, rng, inv, ts, first, tags={"installment"})
            ts2 = ts + timedelta(minutes=rng.randrange(3 * 1440, 20 * 1440))
            if ts2 < ctx.wend:
                _new_pay(ctx, rng, inv, ts2, inv.total - first, tags={"installment"})
        elif kind == "refunds":
            p = _new_pay(ctx, rng, inv, ts, inv.total)
            ts2 = ts + timedelta(minutes=rng.randrange(2 * 1440, 12 * 1440))
            if ts2 < ctx.wend:
                r = inv.total * rng.randint(10, 35) // 100
                _new_pay(ctx, rng, inv, ts2, -r, tags={"refund"}, refund=True)
        else:
            amt = _receipt_amount(ctx, inv, pc, ts)
            _new_pay(ctx, rng, inv, ts, amt)
    for a, b in multi_pairs:
        ts = max(pay_ts(a) or a.issued + timedelta(days=3), pay_ts(b) or b.issued + timedelta(days=3))
        if ts >= ctx.wend:
            ts = ctx.wend - timedelta(hours=5)
        key = f"P{len(ctx.pays):04d}"
        pay = Pay(key, a.ent, a.ccy, ts, a.total + b.total, [(a.key, a.total), (b.key, b.total)],
                  rng.choice(DOC_OFFSETS), rng.choice(DOC_OFFSETS), None, {"multi"})
        pay.post_ts = _post_ts(rng, ctx, ts)
        ctx.pays[key] = pay

    # boundary cross-currency payments (UTC date != local date where possible) + generic cross payments
    n_b = dis["boundary_cross_ok"] + len(cfg["interactions"]) + cfg["faults"]["fx_error"]
    for _ in range(n_b):
        e = rng.choice(cross_ents)
        ts = _boundary_time(rng, ctx, rng.choice(["start", "end"]), utc_mismatch=True)
        inv = _new_inv(ctx, rng, e, ts - timedelta(days=rng.randint(3, 20)), {"xb"})
        _new_pay(ctx, rng, inv, ts, _receipt_amount(ctx, inv, ctx.ents[e]["pay_ccy"], ts), tags={"boundary_cross"})
    n_cross = sum(1 for p in ctx.pays.values() if ctx.invs[p.allocs[0][0]].ccy != p.ccy and "boundary_cross" not in p.tags)
    need = dis["cross_ccy_ok"] + cfg["faults"]["fx_error"] + 1
    while n_cross < need:
        e = rng.choice(cross_ents)
        ts = _rand_instant(rng, ctx.wstart + timedelta(days=12), ctx.wend - timedelta(days=1))
        inv = _new_inv(ctx, rng, e, ts - timedelta(days=rng.randint(2, 11)))
        _new_pay(ctx, rng, inv, ts, _receipt_amount(ctx, inv, ctx.ents[e]["pay_ccy"], ts))
        n_cross += 1
    # boundary payments for cutoff candidates / distractors (same-currency receipts near boundary)
    for _ in range(max(2, 2 * cfg["faults"]["period_cutoff"] + len(cfg["interactions"]) - 0)):
        e = rng.choice(same_ents)
        ts = _boundary_time(rng, ctx, rng.choice(["start", "end"]))
        inv = _new_inv(ctx, rng, e, ts - timedelta(days=rng.randint(3, 20)))
        _new_pay(ctx, rng, inv, ts, inv.total, tags={"boundary"})
    # legitimate advances (prepayments on account): no invoice, full amount sits in UNAPPLIED.
    # They make "any UNAPPLIED row = allocation error" a losing shortcut; the memo/refs must be read.
    for _ in range(dis["advances"]):
        e = rng.choice(same_ents)
        ccy = ctx.ents[e]["pay_ccy"]
        ts = _rand_instant(rng, ctx.wstart, ctx.wend)
        key = f"P{len(ctx.pays):04d}"
        pay = Pay(key, e, ccy, ts, _price(rng, ccy) * rng.randint(1, 6), [], rng.choice(DOC_OFFSETS),
                  rng.choice(DOC_OFFSETS), None, {"advance"})
        pay.post_ts = _post_ts(rng, ctx, ts)
        ctx.pays[key] = pay
    return {"special_counts": {k: sum(1 for v in special.values() if v == k) for k in ("installments", "refunds", "multi")}}


# ----------------------------------------------------------------------------- rendering

def fx_id(d: str, s: str, t: str) -> str:
    return f"fx:{d}:{s}:{t}"


def _utc_date(dt: datetime) -> date:
    return dt.astimezone(timezone.utc).date()


def _conv(ctx: Ctx, amount: int, src: str, dst: str, d: date, rate_override: Decimal | None = None) -> int:
    rate = rate_override if rate_override is not None else ctx.rate(d, src, dst)
    return convert_minor(amount, src, dst, rate, ctx.rounding)


def render(ctx: Ctx, F: dict) -> dict:
    """Render all public tables from the hidden history, applying fault operators F."""
    ids = ctx.ids
    rows: list = []
    idx: dict = {}
    rowdoc: dict = {}
    inv_docs: list = []
    pay_docs: list = []
    seq = [0]

    def add(ts, off, dockey, role, account, side, amount, ccy, ent, inv_id, pay_id):
        seq[0] += 1
        rid = ids.get("row", f"{dockey}|{role}")
        rows.append((ts, seq[0], {
            "row_id": rid, "timestamp": to_iso(ts, off), "account": account,
            "debit_minor": amount if side == "D" else 0, "credit_minor": amount if side == "C" else 0,
            "currency": ccy, "entity_id": ids.get("ent", ent), "invoice_id": inv_id, "payment_id": pay_id}))
        idx[(dockey, role)] = rid
        rowdoc[rid] = dockey

    def render_inv(inv: Inv, lines_override=None):
        iid = ids.get("inv", inv.key)
        did = ids.get("doc", "inv:" + inv.key)
        lines = lines_override or inv.lines
        total = sum(l["amount_minor"] for l in lines)
        inv_docs.append({"doc_id": did, "invoice_id": iid, "entity_id": ids.get("ent", inv.ent),
                         "issued_at": to_iso(inv.issued, inv.doc_off), "due_at": to_iso(inv.due, inv.doc_off),
                         "currency": inv.ccy, "total_minor": total, "line_items": copy.deepcopy(lines)})
        ts = F["cutoff"].get(("inv", inv.key), inv.post_ts)
        ent = inv.ent
        add(ts, inv.post_off, inv.key, "ar", "AR", "D", total, inv.ccy, ent, iid, None)
        add(ts, inv.post_off, inv.key, "rev", "REVENUE", "C", total, inv.ccy, ent, iid, None)

    for inv in ctx.invs.values():
        render_inv(inv)
    for d in F["dups"]:
        lines = copy.deepcopy(d["src_lines"])
        random.Random(d["shuffle"]).shuffle(lines)
        for i, l in enumerate(lines):
            l["line_no"] = i + 1
        render_inv(d["inv"], lines)

    for p in ctx.pays.values():
        pid = ids.get("pay", p.key)
        did = ids.get("doc", "pay:" + p.key)
        ts = F["cutoff"].get(("pay", p.key), p.post_ts)
        allocs = list(p.allocs)
        refs_null = False
        fa = F["alloc"].get(p.key)
        if fa:
            if fa["mode"] == "missing":
                allocs, refs_null = [], True
            else:
                allocs = [(p.allocs[0][0], fa["alloc_minor"])]
        amt = abs(p.amount)
        rcpt = not p.refund
        flip = (lambda s: s) if rcpt else (lambda s: "C" if s == "D" else "D")
        ent = p.ent
        add(ts, p.post_off, p.key, "cash", "CASH", flip("D"), amt, p.ccy, ent, None, pid)
        fxo = F["fx"].get(p.key)
        for ik, a in allocs:
            inv = ctx.invs[ik]
            iid = ids.get("inv", ik)
            a_abs = abs(a)
            if inv.ccy == p.ccy:
                add(ts, p.post_off, p.key, "ar:" + ik, "AR", flip("C"), a_abs, inv.ccy, ent, iid, pid)
            else:
                d = ctx.ldate(p.ts)
                ro = None
                if fxo:
                    d = fxo["date_override"] or d
                    ro = Decimal(fxo["rate_override"]) if fxo["rate_override"] else None
                conv = _conv(ctx, a_abs, p.ccy, inv.ccy, d, ro)
                add(ts, p.post_off, p.key, "fxc_pay:" + ik, "FX_CLEARING", flip("C"), a_abs, p.ccy, ent, iid, pid)
                add(ts, p.post_off, p.key, "fxc_inv:" + ik, "FX_CLEARING", flip("D"), conv, inv.ccy, ent, iid, pid)
                add(ts, p.post_off, p.key, "ar:" + ik, "AR", flip("C"), conv, inv.ccy, ent, iid, pid)
        rem = amt - sum(abs(a) for _, a in allocs)
        if rem:
            add(ts, p.post_off, p.key, "unapplied", "UNAPPLIED", flip("C"), rem, p.ccy, ent, None, pid)
        orig_ids = [ids.get("inv", ik) for ik, _ in p.allocs]
        pay_docs.append({
            "doc_id": did, "payment_id": pid, "entity_id": ids.get("ent", p.ent),
            "timestamp": to_iso(p.ts, p.doc_off), "currency": p.ccy, "amount_minor": p.amount,
            "invoice_refs": None if refs_null else [{"invoice_id": ids.get("inv", ik), "allocated_minor": a} for ik, a in allocs],
            "memo": "Advance payment on account (no invoice yet)" if "advance" in p.tags else
                    ("Refund against " if p.refund else "Remittance advice: ") + "; ".join(orig_ids)})

    rows.sort(key=lambda r: (r[0], r[1]))
    ledger = [r[2] for r in rows]
    token = ids.token
    order = lambda d: hashlib.sha256((token + d["doc_id"]).encode()).hexdigest()
    inv_docs.sort(key=order)
    pay_docs.sort(key=order)
    fx_rows = [{"date": d, "source_currency": s, "target_currency": t, "rate": format(r, "f")}
               for (d, s, t), r in sorted(ctx.rates.items())]
    return {"tables": {"ledger": ledger, "invoices": inv_docs, "payments": pay_docs, "fx": fx_rows},
            "idx": idx, "rowdoc": rowdoc}


# ----------------------------------------------------------------------------- fault planning

def _cross_ts(rng, ctx: Ctx, doc_ts: datetime) -> datetime:
    b = min([ctx.start, ctx.end], key=lambda x: abs(x - doc_ts))
    delta = timedelta(minutes=rng.randint(5, 600))
    return b - delta if doc_ts >= b else b + delta


def _typo_rate(rate: Decimal) -> Decimal:
    s = format(rate, "f")
    digits = [i for i, ch in enumerate(s) if ch.isdigit()]
    nz = [i for i in digits if s[i] != "0"][:5]
    for a, b in zip(nz, nz[1:]):
        if b == a + 1 and s[a] != s[b] or (b == a + 2 and s[a + 1] == "." and s[a] != s[b]):
            t = list(s); t[a], t[b] = t[b], t[a]
            cand = Decimal("".join(t))
            if abs(cand / rate - 1) > Decimal("0.004"):
                return cand
    return (rate * Decimal("1.02")).quantize(FX_DP)


MIN_FX_GAP_MINOR = 8   # an fx_error must move AR by clearly more than the 1-minor-unit tolerance


def _gap(ctx: Ctx, p: Pay, inv: Inv, alloc: int, d_wrong: date, d_right: date) -> int:
    """Never edits published rates (an edited rate would be a detectable spike = leak)."""
    return abs(_conv(ctx, alloc, p.ccy, inv.ccy, d_wrong) - _conv(ctx, alloc, p.ccy, inv.ccy, d_right))


def plan_faults(ctx: Ctx, rng) -> tuple[dict, list]:
    cfg = ctx.cfg
    F = {"dups": [], "alloc": {}, "fx": {}, "cutoff": {}}
    plan: list = []
    used_pay: set = set()
    used_inv: set = set()
    used_doc: set = set()

    def single_receipts(extra_tag=None, cross=None):
        out = []
        for p in ctx.pays.values():
            if p.refund or len(p.allocs) != 1 or "installment" in p.tags or p.key in used_pay:
                continue
            if p.allocs[0][0] in used_inv or ("pay", p.key) in used_doc:
                continue
            if extra_tag and extra_tag not in p.tags:
                continue
            is_cross = ctx.invs[p.allocs[0][0]].ccy != p.ccy
            if cross is not None and cross != is_cross:
                continue
            out.append(p)
        return out

    def claim_pay(p: Pay):
        used_pay.add(p.key)
        used_inv.update(k for k, _ in p.allocs)
        used_doc.add(("pay", p.key))

    def alloc_plan(p: Pay, mode: str):
        amount = p.amount
        a = amount * rng.randint(30, 80) // 100
        if mode == "partial" and (a < 10 or amount - a < 10):
            a = amount // 2
        if mode == "partial" and (a < 10 or amount - a < 10):
            mode = "missing"
        F["alloc"][p.key] = {"mode": mode, "alloc_minor": a if mode == "partial" else 0}
        return mode

    def fx_plan(p: Pay, variant: str):
        inv = ctx.invs[p.allocs[0][0]]
        alloc = F["alloc"][p.key]["alloc_minor"] if p.key in F["alloc"] else p.allocs[0][1]
        d_right = ctx.ldate(p.ts)
        if variant == "utc_date":
            d_wrong = _utc_date(p.ts)
        elif variant == "prev_day":
            d_wrong = d_right - timedelta(days=1)
        elif variant == "invoice_date":
            d_wrong = ctx.ldate(inv.issued)
        elif variant == "posting_date":
            d_wrong = ctx.ldate(F["cutoff"][("pay", p.key)])
        else:
            d_wrong = None
        if d_wrong is not None and d_wrong != d_right and _gap(ctx, p, inv, alloc, d_wrong, d_right) >= MIN_FX_GAP_MINOR:
            F["fx"][p.key] = {"variant": variant, "date_override": d_wrong, "rate_override": None}
        else:  # rare: the wrong date gives an invisible difference -> keying (typo) error instead
            wr = _typo_rate(ctx.rate(d_right, p.ccy, inv.ccy))
            F["fx"][p.key] = {"variant": "typo", "date_override": None, "rate_override": format(wr, "f")}

    def new_cutoff(p_or_inv, kind: str):
        doc_ts = p_or_inv.ts if kind == "pay" else p_or_inv.issued
        F["cutoff"][(kind, p_or_inv.key)] = _cross_ts(rng, ctx, doc_ts)
        used_doc.add((kind, p_or_inv.key))

    # ---- interactions first (they need boundary cross-currency payments)
    for inter in cfg["interactions"]:
        cands = single_receipts("boundary_cross", cross=True)
        cands = [p for p in cands if ("pay", p.key) not in used_doc]
        if not cands:
            raise RuntimeError("no candidate for interaction " + inter)
        p = rng.choice(cands)
        claim_pay(p)
        if inter == "partial_fx":
            alloc_plan(p, "partial")
            if F["alloc"][p.key]["mode"] != "partial":
                raise RuntimeError("partial allocation infeasible")
            variant = "utc_date" if (ctx.off != 0 and _utc_date(p.ts) != ctx.ldate(p.ts)) else "prev_day"
            fx_plan(p, variant)
            plan.append({"type": "payment_allocation", "pay": p, "group": inter, "role": "primary"})
            plan.append({"type": "fx_error", "pay": p, "group": inter, "role": "dependent"})
        else:
            new_cutoff(p, "pay")
            fx_plan(p, "posting_date")
            plan.append({"type": "period_cutoff", "kind": "pay", "doc": p, "group": inter, "role": "primary"})
            plan.append({"type": "fx_error", "pay": p, "group": inter, "role": "dependent"})

    # ---- independent faults
    for _ in range(cfg["faults"]["duplicate_invoice"]):
        cands = [i for i in ctx.invs.values() if not i.tags and i.key not in used_inv and ("inv", i.key) not in used_doc]
        src = rng.choice(cands)
        used_inv.add(src.key)
        used_doc.add(("inv", src.key))
        delta = rng.randint(60, 4 * 1440)
        issued = src.issued + timedelta(minutes=delta)
        if issued >= ctx.wend - timedelta(hours=1):
            issued = src.issued + timedelta(minutes=60)
        dup = Inv(f"{src.key}#D", src.ent, src.ccy, issued, issued + (src.due - src.issued), [], src.po,
                  rng.choice(DOC_OFFSETS), rng.choice(DOC_OFFSETS), None, {"dup"})
        dup.post_ts = _post_ts(rng, ctx, issued)
        F["dups"].append({"inv": dup, "src_lines": copy.deepcopy(src.lines), "shuffle": rng.randrange(10**9)})
        plan.append({"type": "duplicate_invoice", "src": src, "dup": dup, "group": None})
    for _ in range(cfg["faults"]["payment_allocation"]):
        p = rng.choice(single_receipts())
        claim_pay(p)
        mode = alloc_plan(p, rng.choice(["partial", "partial", "missing"]))
        plan.append({"type": "payment_allocation", "pay": p, "group": None})
    for _ in range(cfg["faults"]["fx_error"]):
        p = rng.choice(single_receipts(cross=True))
        claim_pay(p)
        inv = ctx.invs[p.allocs[0][0]]
        variants = ["prev_day", "typo"]
        if ctx.off != 0 and _utc_date(p.ts) != ctx.ldate(p.ts):
            variants.append("utc_date")
        if ctx.ldate(inv.issued) != ctx.ldate(p.ts):
            variants.append("invoice_date")
        fx_plan(p, rng.choice(variants))
        plan.append({"type": "fx_error", "pay": p, "group": None})
    for _ in range(cfg["faults"]["period_cutoff"]):
        cands = [("inv", i) for i in ctx.invs.values() if "boundary" in i.tags and ("inv", i.key) not in used_doc and i.key not in used_inv]
        cands += [("pay", p) for p in ctx.pays.values() if ({"boundary", "boundary_cross"} & p.tags) and ("pay", p.key) not in used_doc and p.key not in used_pay and p.allocs[0][0] not in used_inv]
        kind, doc = rng.choice(cands)
        new_cutoff(doc, kind)
        if kind == "pay":
            used_pay.add(doc.key)
        used_inv.update([doc.key] if kind == "inv" else [k for k, _ in doc.allocs])
        plan.append({"type": "period_cutoff", "kind": kind, "doc": doc, "group": None})
    return F, plan


# ----------------------------------------------------------------------------- episode assembly

FINDING_SPEC = {
    "duplicate_invoice": {
        "affected_ids": "both invoice_id values (original and repeated invoice), any order",
        "claimed_amount_minor": "total_minor of one of the two invoices", "currency": "invoice currency",
        "evidence_ids": "doc_id of both invoices"},
    "payment_allocation": {
        "affected_ids": "[payment_id, invoice_id named in the payment memo]",
        "claimed_amount_minor": "payment amount_minor minus sum(invoice_refs.allocated_minor) (null refs count as 0), in PAYMENT currency",
        "currency": "payment currency",
        "evidence_ids": "payment doc_id + row_id of the ledger UNAPPLIED row"},
    "fx_error": {
        "affected_ids": "[payment_id]",
        "claimed_amount_minor": "|booked AR credit - correct conversion of the allocated amount| in INVOICE currency",
        "currency": "invoice currency",
        "evidence_ids": "payment doc_id + row_id of the AR credit row (or the FX_CLEARING row in invoice currency) + fx record id of the correct rate"},
    "period_cutoff": {
        "affected_ids": "[invoice_id] or [payment_id] of the document posted on the wrong side of the period boundary",
        "claimed_amount_minor": "total_minor (invoice) or |amount_minor| (payment)", "currency": "document currency",
        "evidence_ids": "document doc_id + a ledger row_id posted for it (invoice: AR or REVENUE row; payment: CASH row)"},
}


@dataclass
class Episode:
    episode_id: str
    seed: int
    config: dict
    manifest: dict
    policy: dict
    tables: dict
    truth: dict
    provenance: dict
    clean_tables: dict | None = None


def build_policy(ctx: Ctx) -> dict:
    return {
        "company_timezone": offset_label(ctx.off),
        "period_semantics": "[period_start, period_end): start inclusive, end exclusive, in company timezone",
        "cutoff_basis": "A document belongs to the period of its own timestamp (invoice issued_at / payment timestamp) "
                        "in company timezone. Every ledger row posted for the document must fall on the same side of "
                        "the period boundaries (before / in / after) as the document. Records outside the period exist.",
        "fx_rate_date": "local date (company timezone) of the payment document timestamp",
        "fx_lookup": "fx.csv row with date = that local date, source_currency = payment currency, target_currency = invoice currency; "
                     "rate = target units per 1 source unit (major units)",
        "fx_booking": "Cross-currency receipt posts: Dr CASH (payment ccy); Cr FX_CLEARING (payment ccy, allocated amount); "
                      "Dr FX_CLEARING + Cr AR (invoice ccy, converted allocated amount); remainder Cr UNAPPLIED (payment ccy)",
        "rounding": {"mode": ctx.rounding, "rule": "converted amount rounded once to the minor unit of the target currency"},
        "amount_tolerance_minor": 1,
        "duplicate_rule": "two invoices with the same entity, the same po_ref and the same set of line items",
        "allocation_rule": "invoice_refs[].allocated_minor is in payment currency. A receipt whose memo names invoices must "
                           "allocate its full amount to them; null = not allocated. An advance payment on account (memo names "
                           "no invoice, invoice_refs = []) legitimately stays in UNAPPLIED and is NOT an error.",
        "null_semantics": "null in a reference field means the link is absent; links are never guessed",
        "accounts": ["AR", "REVENUE", "CASH", "FX_CLEARING", "UNAPPLIED"],
        "record_ids": {"ledger": "row_id", "invoices": "invoice_id (get_record) / doc_id (get_document)",
                       "payments": "payment_id (get_record) / doc_id (get_document)", "fx": "fx:YYYY-MM-DD:SRC:DST",
                       "policy": "policy", "manifest": "manifest"},
        "finding_types": FINDING_SPEC,
    }


def policy_summary(policy: dict) -> dict:
    return {k: policy[k] for k in ("company_timezone", "period_semantics", "fx_rate_date", "rounding",
                                   "amount_tolerance_minor", "duplicate_rule")} | {
        "finding_types": {t: list(v) for t, v in policy["finding_types"].items()},
        "note": "full policy: get_record(table='policy', id='policy')"}


def diff_tables(clean: dict, faulted: dict) -> list:
    changes = []
    for table, idk in (("ledger", "row_id"), ("invoices", "doc_id"), ("payments", "doc_id")):
        c = {r[idk]: r for r in clean[table]}
        f = {r[idk]: r for r in faulted[table]}
        for k in sorted(set(c) | set(f)):
            if k not in c:
                changes.append({"op": "add", "table": table, "id": k, "record": f[k]})
            elif k not in f:
                changes.append({"op": "remove", "table": table, "id": k, "record": c[k]})
            else:
                for fld in sorted(c[k]):
                    if c[k][fld] != f[k].get(fld):
                        changes.append({"op": "modify", "table": table, "id": k, "field": fld,
                                        "before": c[k][fld], "after": f[k][fld]})
    return changes


def apply_inverse(faulted: dict, changes: list) -> dict:
    out = {t: copy.deepcopy(v) for t, v in faulted.items()}
    key = {"ledger": "row_id", "invoices": "doc_id", "payments": "doc_id"}
    for ch in changes:
        t = ch["table"]
        if ch["op"] == "add":
            out[t] = [r for r in out[t] if r[key[t]] != ch["id"]]
        elif ch["op"] == "remove":
            out[t].append(copy.deepcopy(ch["record"]))
        else:
            for r in out[t]:
                if r[key[t]] == ch["id"]:
                    r[ch["field"]] = copy.deepcopy(ch["before"])
    return out


def _jsonable(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, Decimal):
        return format(o, "f")
    raise TypeError(type(o))


def generate_episode(seed: int, config: dict | None = None) -> Episode:
    cfg = resolve_config(config)
    ck = config_hash(cfg)
    ctx, hrng = build_context(seed, cfg)
    meta = build_history(ctx, hrng)
    F, plan = plan_faults(ctx, _R(seed, ck, "faults"))
    empty = {"dups": [], "alloc": {}, "fx": {}, "cutoff": {}}
    clean = render(ctx, empty)
    faulted = render(ctx, F)
    ids, idx = ctx.ids, faulted["idx"]
    tables = faulted["tables"]
    doc_of = lambda kind, key: ids.get("doc", f"{kind}:{key}")
    issues, fault_records = [], []
    for n, pl in enumerate(plan):
        issue_id = "ISS-" + hashlib.sha256(f"{ids.token}|issue|{n}".encode()).hexdigest()[:10]
        t = pl["type"]
        if t == "duplicate_invoice":
            s, d = pl["src"], pl["dup"]
            sid, did = ids.get("inv", s.key), ids.get("inv", d.key)
            iss = {"type": t, "affected_ids": sorted([sid, did]), "expected_amount_minor": s.total, "currency": s.ccy,
                   "acceptable_evidence_sets": [sorted([doc_of("inv", s.key), doc_of("inv", d.key)])]}
            touched, params = {d.key}, {"source_invoice": sid, "duplicate_invoice": did,
                                        "duplicate_issued_at": d.issued, "lines_reordered": True}
        elif t == "payment_allocation":
            p = pl["pay"]; fa = F["alloc"][p.key]
            iid = ids.get("inv", p.allocs[0][0])
            exp = p.amount - fa["alloc_minor"]
            iss = {"type": t, "affected_ids": sorted([ids.get("pay", p.key), iid]), "expected_amount_minor": exp,
                   "currency": p.ccy, "acceptable_evidence_sets": [sorted([doc_of("pay", p.key), idx[(p.key, "unapplied")]])]}
            touched, params = {p.key}, {"mode": fa["mode"], "allocated_minor": fa["alloc_minor"], "payment_amount_minor": p.amount}
        elif t == "fx_error":
            p = pl["pay"]; fxo = F["fx"][p.key]
            ik = p.allocs[0][0]; inv = ctx.invs[ik]
            alloc = F["alloc"][p.key]["alloc_minor"] if p.key in F["alloc"] else p.allocs[0][1]
            d_right = ctx.ldate(p.ts)
            ro = Decimal(fxo["rate_override"]) if fxo["rate_override"] else None
            booked = _conv(ctx, alloc, p.ccy, inv.ccy, fxo["date_override"] or d_right, ro)
            right = _conv(ctx, alloc, p.ccy, inv.ccy, d_right)
            fid = fx_id(d_right.isoformat(), p.ccy, inv.ccy)
            iss = {"type": t, "affected_ids": [ids.get("pay", p.key)], "expected_amount_minor": abs(booked - right),
                   "currency": inv.ccy,
                   "acceptable_evidence_sets": [sorted([doc_of("pay", p.key), idx[(p.key, "ar:" + ik)], fid]),
                                                sorted([doc_of("pay", p.key), idx[(p.key, "fxc_inv:" + ik)], fid])]}
            touched = {p.key}
            params = {"variant": fxo["variant"], "wrong_date": fxo["date_override"], "wrong_rate": fxo["rate_override"],
                      "booked_minor": booked, "correct_minor": right, "allocated_minor": alloc}
        else:
            doc, kind = pl["doc"], pl["kind"]
            if kind == "inv":
                iss = {"type": t, "affected_ids": [ids.get("inv", doc.key)], "expected_amount_minor": doc.total,
                       "currency": doc.ccy, "acceptable_evidence_sets": [
                           sorted([doc_of("inv", doc.key), idx[(doc.key, "ar")]]),
                           sorted([doc_of("inv", doc.key), idx[(doc.key, "rev")]])]}
                doc_ts = doc.issued
            else:
                iss = {"type": t, "affected_ids": [ids.get("pay", doc.key)], "expected_amount_minor": abs(doc.amount),
                       "currency": doc.ccy, "acceptable_evidence_sets": [sorted([doc_of("pay", doc.key), idx[(doc.key, "cash")]])]}
                doc_ts = doc.ts
            touched = {doc.key}
            params = {"document": iss["affected_ids"][0], "document_timestamp": doc_ts,
                      "document_side": ctx.side(doc_ts), "posted_at": F["cutoff"][(kind, doc.key)],
                      "posted_side": ctx.side(F["cutoff"][(kind, doc.key)])}
        iss["issue_id"] = issue_id
        iss["_touched"] = touched
        issues.append(iss)
        fault_records.append({"issue_id": issue_id, "type": t, "operator": t + "_op", "group": pl.get("group"),
                              "role": pl.get("role"), "params": params})
    # causal links for interacting scenarios
    links = []
    by_group = defaultdict(list)
    for fr in fault_records:
        if fr["group"]:
            by_group[fr["group"]].append(fr)
    for g, frs in by_group.items():
        prim = next(f for f in frs if f["role"] == "primary"); dep = next(f for f in frs if f["role"] == "dependent")
        mech = {"partial_fx": "FX conversion applied to the allocated part; wrong rate date taken from the UTC date of the payment",
                "cutoff_fx": "misposted entry converted at the rate of its (wrong) posting date"}[g]
        dep["caused_by"] = prim["issue_id"]
        links.append({"scenario": g, "cause": prim["issue_id"], "effect": dep["issue_id"], "mechanism": mech})
    changes = diff_tables(clean["tables"], tables)
    dockey = {}
    for rid, dk in {**clean["rowdoc"], **faulted["rowdoc"]}.items():
        dockey[rid] = dk
    for (kind, k) in [("inv", k) for k in list(ctx.invs) + [d["inv"].key for d in F["dups"]]] + [("pay", k) for k in ctx.pays]:
        dockey[ids.get("doc", f"{kind}:{k}")] = k
    for ch in changes:
        dk = dockey.get(ch["id"])
        ch["doc_key"] = dk
        ch["issue_ids"] = [i["issue_id"] for i in issues if dk in i["_touched"]]
    for i in issues:
        i.pop("_touched")
    ep_id = make_episode_id(seed, cfg)
    manifest = {
        "schema_version": SCHEMA_VERSION, "episode_id": ep_id, "env_version": ENV_VERSION,
        "base_currency": ctx.base, "currencies": ctx.ccys,
        "currency_exponents": {c: EXPONENTS[c] for c in ctx.ccys},
        "period_start": to_iso(ctx.start, ctx.off), "period_end": to_iso(ctx.end, ctx.off),
        "timezone": offset_label(ctx.off),
        "counts": {"ledger_rows": len(tables["ledger"]), "invoices": len(tables["invoices"]),
                   "payments": len(tables["payments"]), "documents": len(tables["invoices"]) + len(tables["payments"]),
                   "fx_rates": len(tables["fx"])},
        "rounding": {"mode": ctx.rounding, "fx_rate_format": "decimal string, 10 dp"},
        "formats": {"time": "ISO-8601 with UTC offset", "money": "integer minor units; exponent per currency in currency_exponents",
                    "fx": "decimal strings", "null": "explicit null (ledger.csv uses the literal null)"},
        "files": ["manifest.json", "ledger.csv", "invoices.jsonl", "payments.jsonl", "fx.csv", "policy.json"],
    }
    provenance = {
        "schema_version": SCHEMA_VERSION, "env_version": ENV_VERSION, "seed": seed, "config": cfg,
        "setup": {"company_offset_minutes": ctx.off, "currencies": ctx.ccys, "rounding": ctx.rounding,
                  "history": meta, "n_issues": len(issues)},
        "faults": fault_records, "causal_links": links, "changes": changes,
    }
    provenance = json.loads(json.dumps(provenance, default=_jsonable))
    truth = {"episode_id": ep_id, "issues": issues}
    return Episode(ep_id, seed, cfg, manifest, build_policy(ctx), tables, truth, provenance, clean["tables"])


# ----------------------------------------------------------------------------- disk I/O

LEDGER_COLS = ["row_id", "timestamp", "account", "debit_minor", "credit_minor", "currency", "entity_id", "invoice_id", "payment_id"]


def write_episode(ep: Episode, root: str, evaluator: bool = True) -> str:
    import csv, os
    base = os.path.join(root, ep.episode_id)
    pub = os.path.join(base, "public")
    os.makedirs(pub, exist_ok=True)
    with open(os.path.join(pub, "manifest.json"), "w") as f:
        json.dump(ep.manifest, f, indent=1)
    with open(os.path.join(pub, "policy.json"), "w") as f:
        json.dump(ep.policy, f, indent=1)
    with open(os.path.join(pub, "ledger.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(LEDGER_COLS)
        for r in ep.tables["ledger"]:
            w.writerow(["null" if r[c] is None else r[c] for c in LEDGER_COLS])
    for name in ("invoices", "payments"):
        with open(os.path.join(pub, name + ".jsonl"), "w") as f:
            for r in ep.tables[name]:
                f.write(json.dumps(r, sort_keys=False) + "\n")
    with open(os.path.join(pub, "fx.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "source_currency", "target_currency", "rate"])
        for r in ep.tables["fx"]:
            w.writerow([r["date"], r["source_currency"], r["target_currency"], r["rate"]])
    if evaluator:
        ev = os.path.join(base, "evaluator")
        os.makedirs(ev, exist_ok=True)
        with open(os.path.join(ev, "truth.json"), "w") as f:
            json.dump(ep.truth, f, indent=1)
        with open(os.path.join(ev, "provenance.json"), "w") as f:
            json.dump(ep.provenance, f, indent=1)
    return base


def read_episode(base: str) -> Episode:
    import csv, os
    pub = os.path.join(base, "public")
    manifest = json.load(open(os.path.join(pub, "manifest.json")))
    policy = json.load(open(os.path.join(pub, "policy.json")))
    ledger = []
    with open(os.path.join(pub, "ledger.csv"), newline="") as f:
        for r in csv.DictReader(f):
            for c in ("debit_minor", "credit_minor"):
                r[c] = int(r[c])
            for c in ("invoice_id", "payment_id"):
                r[c] = None if r[c] == "null" else r[c]
            ledger.append(r)
    tables = {"ledger": ledger}
    for name in ("invoices", "payments"):
        tables[name] = [json.loads(l) for l in open(os.path.join(pub, name + ".jsonl")) if l.strip()]
    with open(os.path.join(pub, "fx.csv"), newline="") as f:
        tables["fx"] = list(csv.DictReader(f))
    ev = os.path.join(base, "evaluator")
    truth = json.load(open(os.path.join(ev, "truth.json"))) if os.path.exists(os.path.join(ev, "truth.json")) else {"episode_id": manifest["episode_id"], "issues": []}
    prov = json.load(open(os.path.join(ev, "provenance.json"))) if os.path.exists(os.path.join(ev, "provenance.json")) else {}
    return Episode(manifest["episode_id"], prov.get("seed", -1), prov.get("config", {}), manifest, policy, tables, truth, prov)
