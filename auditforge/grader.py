"""Shared matcher + terminal reward (the 'common reward function' of the task, section 05).

Every check is a small module-level function so the mutation-testing harness (mutants.py) can
replace each one with a deliberately broken version and verify the test-suite notices.

Normalisation
  * affected_ids  : strip() each id, deduplicate, compare as a SET (order irrelevant, case-sensitive)
  * currency      : strip().upper()
  * amount        : exact integer minor units; |claimed - expected| <= policy.amount_tolerance_minor
  * evidence      : finding.evidence_ids must be a SUPERSET of at least one acceptable evidence set, and
                    EVERY cited evidence id must be a real record id of the episode (no invented support)
Ambiguous matches
  * one-to-one maximum-cardinality bipartite matching (Kuhn). Candidate edges per finding are ordered
    by (|amount diff|, issue_id); findings are processed in submission order. A finding that cannot be
    assigned (or repeats an already matched issue) is a FP; an unmatched truth issue is a FN.
"""
from __future__ import annotations

from typing import Any

TYPES = ("duplicate_invoice", "payment_allocation", "fx_error", "period_cutoff")
MAX_FINDINGS, MAX_EVIDENCE, MAX_EXPLANATION, MAX_AFFECTED = 30, 10, 1000, 10
INSPECTION_COST = 0.002


class InvalidSubmission(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


# ---------------------------------------------------------------- structure
def validate_submission(sub: Any, episode_id: str) -> list:
    """Return normalised findings or raise InvalidSubmission(code). Extra keys are ignored."""
    if not isinstance(sub, dict):
        raise InvalidSubmission("not_an_object")
    if sub.get("episode_id") != episode_id:
        raise InvalidSubmission("episode_id_mismatch")
    fs = sub.get("findings")
    if not isinstance(fs, list):
        raise InvalidSubmission("findings_not_list")
    if len(fs) > MAX_FINDINGS:
        raise InvalidSubmission("too_many_findings")
    out = []
    for f in fs:
        if not isinstance(f, dict):
            raise InvalidSubmission("finding_not_object")
        if f.get("type") not in TYPES:
            raise InvalidSubmission("bad_type")
        ids = f.get("affected_ids")
        if not isinstance(ids, list) or not (1 <= len(ids) <= MAX_AFFECTED) or not all(isinstance(i, str) and i.strip() for i in ids):
            raise InvalidSubmission("bad_affected_ids")
        amt = f.get("claimed_amount_minor")
        if isinstance(amt, bool) or not isinstance(amt, int) or amt < 0:
            raise InvalidSubmission("bad_amount")
        ccy = f.get("currency")
        if not isinstance(ccy, str) or len(ccy.strip()) != 3:
            raise InvalidSubmission("bad_currency")
        ev = f.get("evidence_ids")
        if not isinstance(ev, list) or len(ev) > MAX_EVIDENCE or not all(isinstance(i, str) for i in ev):
            raise InvalidSubmission("bad_evidence")
        ex = f.get("explanation")
        if not isinstance(ex, str) or len(ex) > MAX_EXPLANATION:
            raise InvalidSubmission("bad_explanation")
        out.append({"type": f["type"], "affected_ids": normalize_ids(ids), "claimed_amount_minor": amt,
                    "currency": ccy.strip().upper(), "evidence_ids": frozenset(i.strip() for i in ev)})
    return out


def normalize_ids(ids) -> tuple:
    return tuple(sorted({str(i).strip() for i in ids}))


# ---------------------------------------------------------------- field checks (mutation targets)
def _type_ok(f: dict, t: dict) -> bool:
    return f["type"] == t["type"]


def _ids_ok(f: dict, t: dict) -> bool:
    return f["affected_ids"] == normalize_ids(t["affected_ids"])


def _amount_ok(f: dict, t: dict, tol: int) -> bool:
    return abs(f["claimed_amount_minor"] - t["expected_amount_minor"]) <= tol


def _currency_ok(f: dict, t: dict) -> bool:
    return f["currency"] == t["currency"].upper()


def _evidence_ok(f: dict, t: dict) -> bool:
    return any(set(s) <= f["evidence_ids"] for s in t["acceptable_evidence_sets"])


def _evidence_real(f: dict, known_ids) -> bool:
    return known_ids is None or f["evidence_ids"] <= known_ids


def is_match(f: dict, t: dict, tol: int) -> bool:
    return _type_ok(f, t) and _ids_ok(f, t) and _amount_ok(f, t, tol) and _currency_ok(f, t) and _evidence_ok(f, t)


# ---------------------------------------------------------------- matching
def match_findings(findings: list, issues: list, tol: int, known_ids=None) -> dict:
    adj = []
    for f in findings:
        c = [j for j, t in enumerate(issues) if _evidence_real(f, known_ids) and is_match(f, t, tol)]
        c.sort(key=lambda j: (abs(f["claimed_amount_minor"] - issues[j]["expected_amount_minor"]), issues[j]["issue_id"]))
        adj.append(c)
    owner: dict = {}

    def assign(i, seen):
        for j in adj[i]:
            if j in seen:
                continue
            seen.add(j)
            if j not in owner or assign(owner[j], seen):
                owner[j] = i
                return True
        return False

    for i in range(len(findings)):
        assign(i, set())
    return {j: i for j, i in owner.items()}


def f1_score(tp: int, fp: int, fn: int) -> float:
    if tp + fp + fn == 0:
        return 1.0
    return 2 * tp / (2 * tp + fp + fn)


def precision(tp: int, fp: int) -> float:
    return tp / (tp + fp) if tp + fp else 0.0


def recall(tp: int, fn: int) -> float:
    return tp / (tp + fn) if tp + fn else 0.0


def terminal_reward(f1: float, inspection_steps: int) -> float:
    r = 2 * f1 - 1 - INSPECTION_COST * inspection_steps
    return max(-1.0, min(1.0, r))


def grade(findings: list, truth_issues: list, tol: int, inspection_steps: int, known_ids=None) -> dict:
    """known_ids: set of every record id of the episode (row_id, doc_id, fx:..). When given, a finding that cites a
    non-existent evidence id can never be a TP. The environment always passes it."""
    owner = match_findings(findings, truth_issues, tol, known_ids)
    tp = len(owner)
    fp = len(findings) - tp
    fn = len(truth_issues) - tp
    f1 = f1_score(tp, fp, fn)
    by_type = {t: {"tp": 0, "fp": 0, "fn": 0} for t in TYPES}
    matched_f = set(owner.values())
    for i, f in enumerate(findings):
        by_type[f["type"]]["tp" if i in matched_f else "fp"] += 1
    for j, t in enumerate(truth_issues):
        if j not in owner:
            by_type[t["type"]]["fn"] += 1
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision(tp, fp), "recall": recall(tp, fn), "f1": f1,
            "inspection_steps": inspection_steps, "reward": terminal_reward(f1, inspection_steps),
            "matched": sorted((i, j) for j, i in owner.items()), "by_type": by_type}


def invalid_result(code: str, inspection_steps: int) -> dict:
    return {"tp": 0, "fp": 0, "fn": 0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "inspection_steps": inspection_steps,
            "reward": -1.0, "matched": [], "invalid": code}
