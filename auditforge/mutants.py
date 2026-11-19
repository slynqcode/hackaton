"""Mutation testing of the EVALUATOR.  We break the matcher / reward in ~35 plausible ways and require that the
published reward checks (selfchecks.reward_checks) fail for every mutant ("killed").  A surviving mutant means
the test-suite would not notice that bug in a real grader."""
from __future__ import annotations

import contextlib

from . import env as envmod
from . import grader as G
from .selfchecks import reward_checks, run_checks


@contextlib.contextmanager
def patched(patches):
    saved = [(m, a, getattr(m, a)) for m, a, _ in patches]
    try:
        for m, a, v in patches:
            setattr(m, a, v)
        yield
    finally:
        for m, a, v in reversed(saved):
            setattr(m, a, v)


_orig_validate, _orig_invalid = G.validate_submission, G.invalid_result
_orig_match = G.match_findings


def _greedy(findings, issues, tol):
    owner, used = {}, set()
    for i, f in enumerate(findings):
        c = sorted((j for j, t in enumerate(issues) if G.is_match(f, t, tol) and j not in used),
                   key=lambda j: issues[j]["issue_id"])
        if c:
            owner[c[0]] = i; used.add(c[0])
    return owner


def _many_to_one(findings, issues, tol):
    return {i: next(j for j, t in enumerate(issues) if G.is_match(f, t, tol))
            for i, f in enumerate(findings) if any(G.is_match(f, t, tol) for t in issues)}


def _skip_episode_check(s, eid):
    return _orig_validate(dict(s, episode_id=eid) if isinstance(s, dict) else s, eid)


def _invalid_zero(code, steps):
    r = _orig_invalid(code, steps); r["reward"] = 0.0; return r


MUTANTS = {
    "currency_check_removed": [(G, "_currency_ok", lambda f, t: True)],
    "evidence_check_removed": [(G, "_evidence_ok", lambda f, t: True)],
    "evidence_any_overlap_suffices": [(G, "_evidence_ok", lambda f, t: any(set(s) & f["evidence_ids"] for s in t["acceptable_evidence_sets"]))],
    "evidence_nonempty_suffices": [(G, "_evidence_ok", lambda f, t: bool(f["evidence_ids"]))],
    "evidence_only_first_set": [(G, "_evidence_ok", lambda f, t: set(t["acceptable_evidence_sets"][0]) <= f["evidence_ids"])],
    "evidence_must_equal_set": [(G, "_evidence_ok", lambda f, t: any(set(s) == f["evidence_ids"] for s in t["acceptable_evidence_sets"]))],
    "evidence_existence_not_checked": [(G, "_evidence_real", lambda f, known: True)],
    "amount_check_removed": [(G, "_amount_ok", lambda f, t, tol: True)],
    "amount_tolerance_1000": [(G, "_amount_ok", lambda f, t, tol: abs(f["claimed_amount_minor"] - t["expected_amount_minor"]) <= 1000)],
    "amount_exact_only": [(G, "_amount_ok", lambda f, t, tol: f["claimed_amount_minor"] == t["expected_amount_minor"])],
    "amount_tolerance_exclusive": [(G, "_amount_ok", lambda f, t, tol: abs(f["claimed_amount_minor"] - t["expected_amount_minor"]) < tol)],
    "amount_relative_10pct": [(G, "_amount_ok", lambda f, t, tol: abs(f["claimed_amount_minor"] - t["expected_amount_minor"]) <= 0.1 * t["expected_amount_minor"])],
    "ids_check_removed": [(G, "_ids_ok", lambda f, t: True)],
    "ids_subset_accepted": [(G, "_ids_ok", lambda f, t: set(f["affected_ids"]) <= set(t["affected_ids"]))],
    "ids_superset_accepted": [(G, "_ids_ok", lambda f, t: set(f["affected_ids"]) >= set(t["affected_ids"]))],
    "ids_any_overlap": [(G, "_ids_ok", lambda f, t: bool(set(f["affected_ids"]) & set(t["affected_ids"])))],
    "ids_order_sensitive": [(G, "normalize_ids", lambda ids: tuple(str(i).strip() for i in ids))],
    "ids_not_stripped": [(G, "normalize_ids", lambda ids: tuple(sorted({str(i) for i in ids})))],
    "type_check_removed": [(G, "_type_ok", lambda f, t: True)],
    "greedy_matching": [(G, "match_findings", _greedy)],
    "many_to_one_matching": [(G, "match_findings", _many_to_one)],
    "f1_empty_empty_is_zero": [(G, "f1_score", lambda tp, fp, fn: 0.0 if tp + fp + fn == 0 else 2 * tp / (2 * tp + fp + fn))],
    "f1_is_precision_only": [(G, "f1_score", lambda tp, fp, fn: (tp / (tp + fp)) if tp + fp else (1.0 if fn == 0 else 0.0))],
    "f1_is_recall_only": [(G, "f1_score", lambda tp, fp, fn: (tp / (tp + fn)) if tp + fn else 1.0)],
    "f1_ignores_false_negatives": [(G, "f1_score", lambda tp, fp, fn: 1.0 if tp + fp == 0 else 2 * tp / (2 * tp + fp))],
    "f1_ignores_false_positives": [(G, "f1_score", lambda tp, fp, fn: 1.0 if tp + fn == 0 else 2 * tp / (2 * tp + fn))],
    "precision_zero_div_is_one": [(G, "precision", lambda tp, fp: tp / (tp + fp) if tp + fp else 1.0)],
    "recall_zero_div_is_one": [(G, "recall", lambda tp, fn: tp / (tp + fn) if tp + fn else 1.0)],
    "reward_not_clipped": [(G, "terminal_reward", lambda f1, s: 2 * f1 - 1 - G.INSPECTION_COST * s)],
    "reward_not_rescaled": [(G, "terminal_reward", lambda f1, s: max(-1.0, min(1.0, f1 - G.INSPECTION_COST * s)))],
    "step_cost_10x": [(G, "INSPECTION_COST", 0.02)],
    "step_cost_removed": [(G, "INSPECTION_COST", 0.0)],
    "step_cost_rewards_steps": [(G, "terminal_reward", lambda f1, s: max(-1.0, min(1.0, 2 * f1 - 1 + G.INSPECTION_COST * s)))],
    "invalid_submission_reward_zero": [(G, "invalid_result", _invalid_zero), (envmod, "invalid_result", _invalid_zero)],
    "episode_id_not_checked": [(G, "validate_submission", _skip_episode_check), (envmod, "validate_submission", _skip_episode_check)],
    "max_findings_31": [(G, "MAX_FINDINGS", 31)],
    "max_evidence_11": [(G, "MAX_EVIDENCE", 11)],
    "max_explanation_2000": [(G, "MAX_EXPLANATION", 2000)],
}


def run_mutation_suite() -> dict:
    checks = reward_checks()
    base = run_checks(checks)
    assert all(v is True for v in base.values()), {k: v for k, v in base.items() if v is not True}
    results = {}
    for name, patches in MUTANTS.items():
        with patched(patches):
            res = run_checks(checks)
        killers = [k for k, v in res.items() if v is not True]
        results[name] = {"killed": bool(killers), "killed_by": killers[:3]}
    killed = sum(1 for r in results.values() if r["killed"])
    return {"mutants": len(results), "killed": killed, "mutation_score": killed / len(results),
            "survivors": [k for k, r in results.items() if not r["killed"]], "details": results}


if __name__ == "__main__":
    r = run_mutation_suite()
    print(r["killed"], "/", r["mutants"], "survivors:", r["survivors"])
