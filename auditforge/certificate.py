"""Per-episode certificate: machine-checked evidence that an episode is *correct* (not that it is easy)."""
from __future__ import annotations

import json
import re

from .checks import Book, check_clean, detect, fx_record_id, make_view, solve_from_evidence, truth_tuples
from .generator import Episode, apply_inverse, diff_tables
from .timeutil import parse_iso

FORBIDDEN_WORDS = ("truth", "provenance", "inject", "fault", "mutation", "ISS-", "oracle", "seed")


def _record_ids(tables: dict) -> set:
    s = {r["row_id"] for r in tables["ledger"]} | {r["doc_id"] for t in ("invoices", "payments") for r in tables[t]}
    s |= {fx_record_id(r) for r in tables["fx"]}
    return s


def certify(ep: Episode) -> dict:
    checks = []

    def add(name, ok, detail=""):
        checks.append({"name": name, "passed": bool(ok), "detail": detail if not ok else ""})

    changes = ep.provenance.get("changes")
    # 1. accounting equalities hold BEFORE the errors (clean books reconstructed from provenance)
    if changes is not None:
        clean = apply_inverse(ep.tables, changes)
        v = check_clean(clean, ep.manifest, ep.policy)
        add("clean_books_satisfy_invariants", not v, "; ".join(v[:5]))
        rt = diff_tables(clean, ep.tables)
        strip = lambda ch: [{k: x for k, x in c.items() if k not in ("doc_key", "issue_ids")} for c in ch]
        add("provenance_diff_roundtrip", strip(rt) == strip(changes), "diff(clean, faulted) != recorded changes")
        if ep.clean_tables is not None:
            norm = lambda t: {k: sorted(json.dumps(r, sort_keys=True) for r in t[k]) for k in ("ledger", "invoices", "payments")}
            add("reconstructed_clean_equals_generated_clean", norm(clean) == norm(ep.clean_tables))
        touched = {i for c in changes for i in c.get("issue_ids", [])}
        add("every_issue_has_recorded_causal_change", all(i["issue_id"] in touched for i in ep.truth["issues"]),
            "issue without provenance change")
    # 2. declared discrepancy == the only discrepancy present in the data
    det, tru = detect(ep.tables, ep.manifest, ep.policy), truth_tuples(ep.truth)
    add("declared_discrepancies_are_exactly_those_present", det == tru, f"detector-only={sorted(set(det)-set(tru))} truth-only={sorted(set(tru)-set(det))}")
    # 3. evidence: ids exist, and each acceptable set independently proves the finding
    ids = _record_ids(ep.tables)
    ex_ok = all(set(s) <= ids for i in ep.truth["issues"] for s in i["acceptable_evidence_sets"])
    add("evidence_ids_exist", ex_ok)
    suff = True; bad = ""
    for i in ep.truth["issues"]:
        for s in i["acceptable_evidence_sets"]:
            r = solve_from_evidence(make_view(ep.tables, s), ep.manifest, ep.policy, i["type"])
            if r != (tuple(sorted(i["affected_ids"])), i["expected_amount_minor"], i["currency"]):
                suff, bad = False, f"{i['type']} {s} -> {r}"
    add("evidence_sets_independently_sufficient", suff, bad)
    # 4. nothing unavailable is required: affected ids exist
    inv_ids = {r["invoice_id"] for r in ep.tables["invoices"]}; pay_ids = {r["payment_id"] for r in ep.tables["payments"]}
    add("affected_ids_exist", all(a in inv_ids | pay_ids for i in ep.truth["issues"] for a in i["affected_ids"]))
    # 5. no leakage into public artefacts
    pub = json.dumps({"t": ep.tables, "m": ep.manifest, "p": ep.policy})
    hits = [w for w in FORBIDDEN_WORDS if w.lower() in pub.lower()]
    add("public_files_contain_no_evaluator_vocabulary", not hits, str(hits))
    add("issue_ids_not_in_public_files", all(i["issue_id"] not in pub for i in ep.truth["issues"]))
    # 6. formats
    ts_ok = all(re.search(r"[+-]\d\d:\d\d$", s) for s in
                [r["timestamp"] for r in ep.tables["ledger"]] + [r["issued_at"] for r in ep.tables["invoices"]] +
                [r["timestamp"] for r in ep.tables["payments"]] + [ep.manifest["period_start"], ep.manifest["period_end"]])
    money_ok = all(isinstance(r["debit_minor"], int) and isinstance(r["credit_minor"], int) for r in ep.tables["ledger"]) and \
        all(isinstance(r["total_minor"], int) for r in ep.tables["invoices"]) and \
        all(isinstance(r["amount_minor"], int) for r in ep.tables["payments"])
    fx_ok = all(isinstance(r["rate"], str) and re.fullmatch(r"\d+\.\d+", r["rate"]) for r in ep.tables["fx"])
    add("formats_iso_offset_integer_minor_decimal_fx", ts_ok and money_ok and fx_ok)
    c = ep.manifest["counts"]
    add("manifest_counts_match", c["ledger_rows"] == len(ep.tables["ledger"]) and c["invoices"] == len(ep.tables["invoices"]) and
        c["payments"] == len(ep.tables["payments"]) and c["fx_rates"] == len(ep.tables["fx"]))
    lo = 100   # the task's 200-2000 is a *proposed* size; all shipped configs meet 200 (tests/test_generator.py)
    add("size_within_bounds", len(ep.truth["issues"]) <= 12 and 20 <= c["documents"] <= 200 and lo <= c["ledger_rows"] <= 2000,
        f"{c}")
    return {"episode_id": ep.episode_id, "passed": all(x["passed"] for x in checks), "checks": checks}
