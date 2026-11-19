"""Harmless (semantics-preserving) transformations used for paired / metamorphic checks.

shuffle    : reorder rows in every table
rename_ids : bijectively rename entity / invoice / payment / doc / row ids (incl. memo text, refs, truth)
tz_shift   : re-render every timestamp (and period bounds) with a different UTC offset (same instant)
all        : the three above, in order
"""
from __future__ import annotations

import copy
import hashlib
import random
import re

from .generator import DOC_OFFSETS, ID_STYLES, Episode, Ids
from .timeutil import parse_iso, to_iso

KINDS = ("shuffle", "rename_ids", "tz_shift", "all")


def transform(ep: Episode, kind: str, seed: int = 0) -> Episode:
    if kind == "all":
        e = ep
        for k in ("shuffle", "rename_ids", "tz_shift"):
            e = transform(e, k, seed)
        return e
    rng = random.Random(f"{seed}|{kind}|{ep.episode_id}")
    tables, manifest, truth = copy.deepcopy(ep.tables), copy.deepcopy(ep.manifest), copy.deepcopy(ep.truth)
    if kind == "shuffle":
        for t in ("ledger", "invoices", "payments"):
            rng.shuffle(tables[t])
    elif kind == "tz_shift":
        sh = lambda s: to_iso(parse_iso(s), rng.choice(DOC_OFFSETS))
        for r in tables["ledger"]:
            r["timestamp"] = sh(r["timestamp"])
        for r in tables["invoices"]:
            r["issued_at"], r["due_at"] = sh(r["issued_at"]), sh(r["due_at"])
        for r in tables["payments"]:
            r["timestamp"] = sh(r["timestamp"])
        manifest["period_start"], manifest["period_end"] = sh(manifest["period_start"]), sh(manifest["period_end"])
    elif kind == "rename_ids":
        ids = Ids(f"rename|{seed}|{ep.episode_id}", rng.randrange(len(ID_STYLES)))
        mp: dict = {}
        for r in tables["ledger"]:
            mp[r["row_id"]] = ids.get("row", r["row_id"])
            mp[r["entity_id"]] = ids.get("ent", r["entity_id"])
        for r in tables["invoices"]:
            mp[r["doc_id"]] = ids.get("doc", r["doc_id"]); mp[r["invoice_id"]] = ids.get("inv", r["invoice_id"])
            mp[r["entity_id"]] = ids.get("ent", r["entity_id"])
        for r in tables["payments"]:
            mp[r["doc_id"]] = ids.get("doc", r["doc_id"]); mp[r["payment_id"]] = ids.get("pay", r["payment_id"])
            mp[r["entity_id"]] = ids.get("ent", r["entity_id"])
        m = lambda x: None if x is None else mp.get(x, x)
        pat = re.compile("|".join(re.escape(k) for k in sorted(mp, key=len, reverse=True)))
        for r in tables["ledger"]:
            for k in ("row_id", "entity_id", "invoice_id", "payment_id"):
                r[k] = m(r[k])
        for r in tables["invoices"]:
            for k in ("doc_id", "invoice_id", "entity_id"):
                r[k] = m(r[k])
        for r in tables["payments"]:
            for k in ("doc_id", "payment_id", "entity_id"):
                r[k] = m(r[k])
            if r["invoice_refs"]:
                for ref in r["invoice_refs"]:
                    ref["invoice_id"] = m(ref["invoice_id"])
            r["memo"] = pat.sub(lambda mo: mp[mo.group(0)], r["memo"])
        for i in truth["issues"]:
            i["affected_ids"] = [m(x) for x in i["affected_ids"]]
            i["acceptable_evidence_sets"] = [sorted(m(x) for x in s) for s in i["acceptable_evidence_sets"]]
        new_id = "ep-" + hashlib.sha256((ep.episode_id + "|rename|" + str(seed)).encode()).hexdigest()[:12]
        manifest["episode_id"] = truth["episode_id"] = new_id
        return Episode(new_id, ep.seed, ep.config, manifest, copy.deepcopy(ep.policy), tables, truth, {"transformed": kind})
    else:
        raise ValueError(kind)
    return Episode(ep.episode_id, ep.seed, ep.config, manifest, copy.deepcopy(ep.policy), tables, truth, {"transformed": kind})
