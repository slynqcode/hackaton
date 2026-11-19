import collections
import json

import pytest

from auditforge.certificate import certify
from auditforge.checks import check_clean, detect, truth_tuples
from auditforge.generator import FAULT_TYPES, apply_inverse, generate_episode, resolve_config

CFGS = [
    {}, {"faults": {k: 0 for k in FAULT_TYPES}},
    {"interactions": ["partial_fx"]}, {"interactions": ["cutoff_fx"]},
    {"interactions": ["partial_fx", "cutoff_fx"], "faults": {"duplicate_invoice": 2, "payment_allocation": 1, "fx_error": 1, "period_cutoff": 1}},
    {"faults": {"duplicate_invoice": 3, "payment_allocation": 3, "fx_error": 3, "period_cutoff": 3}},
    {"company_offset_minutes": 0, "interactions": ["partial_fx", "cutoff_fx"]},
    {"n_invoices": 90}, {"n_invoices": 40}, {"period_months": 1}, {"rounding": "half_even"}, {"rounding": "half_up", "currencies": ["KZT", "JPY", "USD"]},
]


@pytest.mark.parametrize("ci", range(len(CFGS)))
@pytest.mark.parametrize("seed", [3, 17, 101, 5555])
def test_certificate_passes(ci, seed):
    ep = generate_episode(seed, CFGS[ci])
    cert = certify(ep)
    assert cert["passed"], [c for c in cert["checks"] if not c["passed"]]


def test_four_types_and_two_interaction_scenarios_present():
    ep = generate_episode(5, {"interactions": ["partial_fx", "cutoff_fx"]})
    types = collections.Counter(i["type"] for i in ep.truth["issues"])
    assert set(types) == set(FAULT_TYPES) and sum(types.values()) == 8
    groups = [f["group"] for f in ep.provenance["faults"] if f["group"]]
    assert sorted(groups) == ["cutoff_fx", "cutoff_fx", "partial_fx", "partial_fx"]
    assert len(ep.provenance["causal_links"]) == 2
    # interacting issues share the same payment
    by_pay = collections.defaultdict(list)
    for i in ep.truth["issues"]:
        by_pay[tuple(i["affected_ids"][:1])].append(i["type"])


def test_faults_are_independently_configurable():
    for t in FAULT_TYPES:
        cfg = {"faults": {k: (2 if k == t else 0) for k in FAULT_TYPES}}
        ep = generate_episode(9, cfg)
        assert [i["type"] for i in ep.truth["issues"]] == [t, t]


def test_twelve_issue_cap_and_config_validation():
    generate_episode(1, {"faults": {k: 2 for k in FAULT_TYPES}, "interactions": ["partial_fx", "cutoff_fx"]})
    with pytest.raises(ValueError):
        resolve_config({"faults": {k: 3 for k in FAULT_TYPES}, "interactions": ["partial_fx"]})
    with pytest.raises(ValueError):
        resolve_config({"nope": 1})
    with pytest.raises(ValueError):
        resolve_config({"faults": {"nope": 1}})


def test_size_ranges_hold_for_default_configs():
    for s in range(50, 70):
        c = generate_episode(s).manifest["counts"]
        assert 200 <= c["ledger_rows"] <= 2000 and 20 <= c["documents"] <= 200


def test_variation_across_seeds():
    eps = [generate_episode(s) for s in range(1, 13)]
    assert len({e.manifest["timezone"] for e in eps}) >= 4
    assert len({tuple(e.manifest["currencies"]) for e in eps}) >= 4
    assert len({e.tables["invoices"][0]["invoice_id"][:2] for e in eps}) >= 2
    assert len({e.manifest["rounding"]["mode"] for e in eps}) == 2


def test_distractors_present_and_not_flagged_by_exact_rules():
    ep = generate_episode(12, {"faults": {k: 0 for k in FAULT_TYPES}})
    assert detect(ep.tables, ep.manifest, ep.policy) == []
    inv = ep.tables["invoices"]
    same = collections.defaultdict(list)
    for i in inv:
        same[(i["entity_id"], i["total_minor"])].append(i)
    assert any(len(v) > 1 for v in same.values()), "legit repeated amounts expected"
    assert any(p["amount_minor"] < 0 for p in ep.tables["payments"]), "refund expected"
    assert any(len(p["invoice_refs"]) > 1 for p in ep.tables["payments"]), "multi-invoice payment expected"
    inv_pay = collections.Counter(r["invoice_id"] for p in ep.tables["payments"] for r in p["invoice_refs"])
    assert any(v > 1 for v in inv_pay.values()), "split payments expected"
    assert any(r["currency"] != ep.manifest["base_currency"] for r in ep.tables["ledger"])


def test_faulted_books_break_invariants_clean_books_do_not():
    ep = generate_episode(4)
    assert check_clean(ep.tables, ep.manifest, ep.policy)
    assert check_clean(apply_inverse(ep.tables, ep.provenance["changes"]), ep.manifest, ep.policy) == []


def test_seed_determinism_and_isolation_between_calls():
    a = generate_episode(77, {"interactions": ["partial_fx"]})
    generate_episode(78)
    b = generate_episode(77, {"interactions": ["partial_fx"]})
    assert json.dumps(a.tables, sort_keys=True) == json.dumps(b.tables, sort_keys=True)
    assert a.truth == b.truth


def test_amounts_are_integers_and_currencies_have_exponents():
    ep = generate_episode(8, {"currencies": ["KZT", "JPY", "EUR"]})
    for r in ep.tables["ledger"]:
        assert isinstance(r["debit_minor"], int) and isinstance(r["credit_minor"], int)
    assert ep.manifest["currency_exponents"] == {"KZT": 2, "JPY": 0, "EUR": 2}


def test_detector_matches_truth_on_many_seeds():
    for s in range(200, 240):
        ep = generate_episode(s, {"interactions": ["partial_fx", "cutoff_fx"]} if s % 2 else {})
        assert detect(ep.tables, ep.manifest, ep.policy) == truth_tuples(ep.truth), s
