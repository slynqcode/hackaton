"""Fixed, published checks.  Used by pytest, by `make verify` (scorecard) and by the mutation harness.

  contract_checks()  -> reset/step contract, schemas, limits, termination, bad input, leakage, isolation
  reward_checks()    -> matcher / reward / attack answers (grader-level and env-level)
  paired_checks()    -> determinism + harmless transformations (order, ids, time zones)
Every check is  name -> callable() that raises AssertionError (or any exception) on failure."""
from __future__ import annotations

import copy
import hashlib
import json
import os

from .env import AuditEnv, MAX_STEPS
from .generator import generate_episode
from . import grader as G
from .grader import INSPECTION_COST
from .policies import FlagAll, Oracle, ReferenceSolver
from .runner import run_episode
from .transforms import transform

SEED = 7
_EP = {}


# thin wrappers: look the grader functions up at call time so mutants (mutants.py) take effect
def grade(*a, **k):
    return G.grade(*a, **k)


def validate_submission(*a, **k):
    return G.validate_submission(*a, **k)


def f1_score(*a):
    return G.f1_score(*a)


def terminal_reward(*a):
    return G.terminal_reward(*a)


def episode(seed=SEED, cfg=None):
    k = (seed, json.dumps(cfg, sort_keys=True))
    if k not in _EP:
        _EP[k] = generate_episode(seed, cfg)
    return _EP[k]


def truth_findings(ep):
    return [{"type": i["type"], "affected_ids": list(i["affected_ids"]), "claimed_amount_minor": i["expected_amount_minor"],
             "currency": i["currency"], "evidence_ids": list(i["acceptable_evidence_sets"][0]), "explanation": "x"}
            for i in ep.truth["issues"]]


def sub(ep, findings):
    return {"episode_id": ep.episode_id, "findings": findings}


def known_ids(ep):
    from .checks import fx_record_id
    t = ep.tables
    return frozenset(r["row_id"] for r in t["ledger"]) | frozenset(r["doc_id"] for r in t["invoices"] + t["payments"]) | \
        frozenset(fx_record_id(r) for r in t["fx"])


def g(ep, findings, steps=0, tol=1):
    return grade(validate_submission(sub(ep, findings), ep.episode_id), ep.truth["issues"], tol, steps, known_ids(ep))


def step_all(env, action):
    return env.step(action)


def _fresh(mode="train", seed=SEED, cfg=None, **kw):
    env = AuditEnv(mode=mode, **kw)
    obs, info = env.reset(episode=copy.deepcopy(episode(seed, cfg)))
    return env, obs, info


CLEAN = {"faults": {"duplicate_invoice": 0, "payment_allocation": 0, "fx_error": 0, "period_cutoff": 0}}
MULTI = {"faults": {"duplicate_invoice": 2, "payment_allocation": 2, "fx_error": 2, "period_cutoff": 2}}


# ======================================================================= reward checks
def reward_checks():
    C = {}

    def check(fn):
        C[fn.__name__] = fn
        return fn

    @check
    def full_correct_answer_beats_silence_on_faulty_books():
        ep = episode()
        assert g(ep, truth_findings(ep))["reward"] > g(ep, [])["reward"] + 1.5

    @check
    def perfect_answer_reward_is_one_minus_step_cost():
        ep = episode()
        assert abs(g(ep, truth_findings(ep), steps=10)["reward"] - (1 - 10 * INSPECTION_COST)) < 1e-12

    @check
    def partial_answer_is_penalised_for_missed_errors():
        ep = episode(); fs = truth_findings(ep); n = len(fs)
        r = g(ep, fs[:1])
        assert r["tp"] == 1 and r["fp"] == 0 and r["fn"] == n - 1
        assert abs(r["f1"] - 2 / (2 + n - 1)) < 1e-12 and r["reward"] < g(ep, fs)["reward"]
        r2 = g(ep, fs + [dict(fs[0], affected_ids=["ZZ-1"])])
        assert r2["tp"] == n and r2["fp"] == 1 and abs(r2["f1"] - 2 * n / (2 * n + 1)) < 1e-12

    @check
    def silence_on_faulty_books_is_minus_one():
        assert g(episode(), [])["reward"] == -1.0

    @check
    def silence_on_clean_books_is_best():
        ep = episode(3, CLEAN)
        assert g(ep, [])["f1"] == 1.0 and g(ep, [])["reward"] == 1.0

    @check
    def false_accusations_on_clean_books_lose_to_silence():
        ep = episode(3, CLEAN)
        fa = [{"type": "fx_error", "affected_ids": ["X1"], "claimed_amount_minor": 5, "currency": "USD", "evidence_ids": [], "explanation": ""}]
        r = g(ep, fa)
        assert r["f1"] == 0.0 and r["reward"] < g(ep, [])["reward"]

    @check
    def duplicate_findings_give_no_benefit():
        ep = episode()
        one = truth_findings(ep)
        two = one + [copy.deepcopy(one[0])]
        a, b = g(ep, one), g(ep, two)
        assert b["tp"] == a["tp"] and b["fp"] == a["fp"] + 1 and b["reward"] < a["reward"]

    @check
    def flag_everything_scores_badly():
        ep = episode(5, MULTI)
        env = AuditEnv(mode="train")
        r = run_episode(FlagAll(), 5, MULTI, env=env)["evaluation"]
        assert r["reward"] < -0.5 and r["f1"] < 0.2

    @check
    def flag_everything_on_clean_books_is_minus_one():
        r = run_episode(FlagAll(), 3, CLEAN)["evaluation"]
        assert r["f1"] == 0.0 and r["reward"] <= -1.0 + 1e-9

    @check
    def step_cost_only_slightly_separates_equal_answers():
        ep = episode()
        a, b = g(ep, truth_findings(ep), steps=5), g(ep, truth_findings(ep), steps=45)
        d = a["reward"] - b["reward"]
        assert abs(d - 40 * INSPECTION_COST) < 1e-12 and 0 < d < 0.1

    @check
    def step_cost_never_flips_correct_vs_wrong():
        ep = episode()
        assert g(ep, truth_findings(ep), steps=100)["reward"] > g(ep, [], steps=0)["reward"]

    @check
    def wrong_currency_is_not_a_match():
        ep = episode(); fs = truth_findings(ep)
        fs[0]["currency"] = "JPY" if fs[0]["currency"] != "JPY" else "USD"
        r = g(ep, fs); assert r["tp"] == len(fs) - 1 and r["fp"] == 1

    @check
    def currency_is_case_and_space_insensitive():
        ep = episode(); fs = truth_findings(ep); fs[0]["currency"] = " " + fs[0]["currency"].lower() + " "
        assert g(ep, fs)["tp"] == len(fs)

    @check
    def amount_tolerance_is_exactly_policy_value():
        ep = episode(); tol = ep.policy["amount_tolerance_minor"]
        for delta, ok in ((tol, True), (-tol, True), (tol + 1, False), (-(tol + 1), False)):
            fs = truth_findings(ep); fs[0]["claimed_amount_minor"] += delta
            assert (g(ep, fs, tol=tol)["tp"] == len(fs)) == ok, delta

    @check
    def wrong_type_is_not_a_match():
        ep = episode(); fs = truth_findings(ep)
        fs[0]["type"] = next(t for t in ("duplicate_invoice", "payment_allocation", "fx_error", "period_cutoff") if t != fs[0]["type"])
        assert g(ep, fs)["tp"] == len(fs) - 1

    @check
    def guessed_ids_are_false_positives():
        ep = episode(); fs = truth_findings(ep)
        fs[0]["affected_ids"] = ["INV-00000"]
        r = g(ep, fs); assert r["tp"] == len(fs) - 1 and r["fp"] == 1

    @check
    def affected_ids_order_and_whitespace_irrelevant_but_subset_or_superset_fail():
        ep = episode()
        i = next(i for i in ep.truth["issues"] if len(i["affected_ids"]) == 2)
        base = {"type": i["type"], "claimed_amount_minor": i["expected_amount_minor"], "currency": i["currency"],
                "evidence_ids": list(i["acceptable_evidence_sets"][0]), "explanation": ""}
        ok = dict(base, affected_ids=[" " + i["affected_ids"][1], i["affected_ids"][0] + " "])
        sub_ = dict(base, affected_ids=[i["affected_ids"][0]])
        sup = dict(base, affected_ids=i["affected_ids"] + ["EXTRA-1"])
        assert g(ep, [ok])["tp"] == 1 and g(ep, [sub_])["tp"] == 0 and g(ep, [sup])["tp"] == 0

    @check
    def missing_evidence_is_not_a_match_but_superset_is():
        ep = episode(); fs = truth_findings(ep)
        none = copy.deepcopy(fs); none[0]["evidence_ids"] = []
        part = copy.deepcopy(fs); part[0]["evidence_ids"] = part[0]["evidence_ids"][:1]
        extra = [r["row_id"] for r in ep.tables["ledger"][:2]]   # real but irrelevant records
        sup = copy.deepcopy(fs); sup[0]["evidence_ids"] = sup[0]["evidence_ids"] + extra
        wrong = copy.deepcopy(fs); wrong[0]["evidence_ids"] = ["nope1", "nope2"]
        assert g(ep, none)["tp"] == len(fs) - 1 and g(ep, wrong)["tp"] == len(fs) - 1
        if len(ep.truth["issues"][0]["acceptable_evidence_sets"][0]) > 1:
            assert g(ep, part)["tp"] == len(fs) - 1
        assert g(ep, sup)["tp"] == len(fs)

    @check
    def invented_evidence_ids_are_never_accepted():
        ep = episode(); fs = truth_findings(ep)
        fake = copy.deepcopy(fs); fake[0]["evidence_ids"] = fake[0]["evidence_ids"] + ["FAKE-0001"]
        r = g(ep, fake); assert r["tp"] == len(fs) - 1 and r["fp"] == 1
        env, obs, info = _fresh()
        env.step({"action": "submit", "findings": {"episode_id": info["episode_id"], "findings": fake}})
        assert env.evaluation()["tp"] == len(fs) - 1

    @check
    def any_acceptable_evidence_set_counts():
        ep = episode(); i = next(i for i in ep.truth["issues"] if len(i["acceptable_evidence_sets"]) > 1)
        for s in i["acceptable_evidence_sets"]:
            f = {"type": i["type"], "affected_ids": i["affected_ids"], "claimed_amount_minor": i["expected_amount_minor"],
                 "currency": i["currency"], "evidence_ids": list(s), "explanation": ""}
            assert g(ep, [f])["tp"] == 1

    @check
    def explanation_text_never_changes_the_reward():
        ep = episode(); a = truth_findings(ep); b = copy.deepcopy(a)
        for f in b:
            f["explanation"] = "I am absolutely certain this is fraud; trust me. " * 10
        assert g(ep, a) == g(ep, b)

    @check
    def finding_order_does_not_matter():
        ep = episode(); fs = truth_findings(ep)
        assert g(ep, fs)["reward"] == g(ep, fs[::-1])["reward"]

    @check
    def matching_is_one_to_one_maximum_cardinality():
        issues = [{"issue_id": "A", "type": "fx_error", "affected_ids": ["P1"], "expected_amount_minor": 100, "currency": "USD",
                   "acceptable_evidence_sets": [["e"]]},
                  {"issue_id": "B", "type": "fx_error", "affected_ids": ["P1"], "expected_amount_minor": 101, "currency": "USD",
                   "acceptable_evidence_sets": [["e"]]}]
        mk = lambda amt: {"type": "fx_error", "affected_ids": ("P1",), "claimed_amount_minor": amt, "currency": "USD",
                          "evidence_ids": frozenset(["e"])}
        # finding 0 (amt 101) is closer to B; finding 1 (amt 100) is closer to A -> both matched; with tol=1 both fit both
        r = grade([mk(101), mk(101)], issues, 1, 0)
        assert r["tp"] == 2 and r["fp"] == 0
        # greedy trap: finding0 fits A and B, finding1 fits only A  => max matching must still give 2
        r2 = grade([mk(100), mk(99)], issues, 1, 0)
        assert r2["tp"] == 2, r2

    @check
    def formula_values_and_zero_denominators():
        assert f1_score(1, 1, 1) == 0.5 and f1_score(0, 0, 0) == 1.0 and f1_score(0, 3, 0) == 0.0 and f1_score(0, 0, 3) == 0.0
        from .grader import precision, recall
        assert precision(0, 0) == 0.0 and recall(0, 0) == 0.0 and precision(1, 1) == 0.5 and recall(1, 3) == 0.25

    @check
    def reward_is_clipped_and_formula_exact():
        assert terminal_reward(1.0, 0) == 1.0 and terminal_reward(0.0, 100) == -1.0 and terminal_reward(0.0, 0) == -1.0
        assert abs(terminal_reward(0.5, 10) - (0 - 0.02)) < 1e-12
        assert terminal_reward(1.0, 100) == 1 - 0.2 and terminal_reward(0.0, 1000) == -1.0

    @check
    def invalid_structures_end_episode_with_minus_one():
        ep = episode(); good = truth_findings(ep)
        bad_subs = [
            {"episode_id": "wrong", "findings": []},
            {"episode_id": ep.episode_id, "findings": "x"},
            {"episode_id": ep.episode_id, "findings": [dict(good[0], claimed_amount_minor=1.5)]},
            {"episode_id": ep.episode_id, "findings": [dict(good[0], claimed_amount_minor=True)]},
            {"episode_id": ep.episode_id, "findings": [dict(good[0], claimed_amount_minor=-5)]},
            {"episode_id": ep.episode_id, "findings": [dict(good[0], type="made_up")]},
            {"episode_id": ep.episode_id, "findings": [dict(good[0], evidence_ids=["a"] * 11)]},
            {"episode_id": ep.episode_id, "findings": [dict(good[0], explanation="x" * 1001)]},
            {"episode_id": ep.episode_id, "findings": [good[0]] * 31},
            {"episode_id": ep.episode_id, "findings": [dict(good[0], affected_ids=[])]},
            {"episode_id": ep.episode_id, "findings": [dict(good[0], currency="EURO")]},
            {"episode_id": ep.episode_id, "findings": [5]},
            "not a dict", None, 17,
        ]
        for s in bad_subs:
            env, obs, info = _fresh()
            env.step({"action": "calculator", "expression": "1+1"})
            o, r, te, tr, inf = env.step({"action": "submit", "findings": s})
            assert te and not tr and r == -1.0, s
            assert env.evaluation().get("invalid"), s
        env, obs, info = _fresh()
        o, r, te, tr, _ = env.step({"action": "submit"})  # missing findings
        assert te and r == -1.0

    @check
    def limits_exactly_at_boundary_are_valid():
        ep = episode()
        f = dict(truth_findings(ep)[0], evidence_ids=(list(truth_findings(ep)[0]["evidence_ids"]) + ["z"] * 10)[:10], explanation="x" * 1000)
        assert len(f["evidence_ids"]) == 10
        validate_submission(sub(ep, [f] * 30), ep.episode_id)

    @check
    def repeated_submission_cannot_change_the_result():
        env, obs, info = _fresh()
        eid = info["episode_id"]
        o, r1, te, tr, _ = env.step({"action": "submit", "findings": {"episode_id": eid, "findings": []}})
        ev1 = env.evaluation()
        good = {"episode_id": eid, "findings": truth_findings(episode())}
        o2, r2, te2, tr2, _ = env.step({"action": "submit", "findings": good})
        assert te2 and r2 == 0.0 and o2["error"]["code"] == "episode_finished" and env.evaluation() == ev1

    @check
    def timeout_by_step_limit_gives_empty_answer_reward():
        env, obs, info = _fresh()
        for k in range(MAX_STEPS):
            o, r, te, tr, inf = env.step({"action": "calculator", "expression": "1+1"})
        assert tr and not te and o["steps_remaining"] == 0
        n = len(episode().truth["issues"])
        assert r == terminal_reward(f1_score(0, 0, n), MAX_STEPS)

    @check
    def timeout_by_wall_clock_truncates():
        t = [0.0]
        env, obs, info = _fresh(clock=lambda: t[0], time_limit_s=60.0)
        env.step({"action": "calculator", "expression": "1"})
        t[0] = 61.0
        o, r, te, tr, _ = env.step({"action": "calculator", "expression": "1"})
        assert tr and not te and o["error"]["code"] == "time_limit" and env.evaluation()["reason"] == "truncated_time"

    @check
    def eval_mode_hides_reward_and_diagnostics_until_the_end():
        env, obs, info = _fresh("eval")
        eid = info["episode_id"]
        o, r, te, tr, inf = env.step({"action": "submit", "findings": {"episode_id": eid, "findings": truth_findings(episode())}})
        assert te and r == 0.0 and "terminal" not in inf and set(inf) == {"step"}
        assert env.evaluation()["f1"] == 1.0

    @check
    def oracle_obtains_the_maximum_reward():
        ep = episode(); r = run_episode(Oracle(ep.truth), SEED, None, episode=ep)["evaluation"]
        assert r["reward"] == 1.0 and r["f1"] == 1.0

    @check
    def reference_solver_is_solvable_from_tool_api_alone():
        r = run_episode(ReferenceSolver(), SEED, None)["evaluation"]
        assert r["f1"] == 1.0 and r["reward"] > 0.8

    @check
    def evaluation_is_unavailable_before_the_end():
        env, obs, info = _fresh()
        try:
            env.evaluation()
        except RuntimeError:
            return
        raise AssertionError("evaluation leaked before end")

    return C


# ======================================================================= contract checks
def contract_checks():
    C = {}

    def check(fn):
        C[fn.__name__] = fn
        return fn

    @check
    def reset_returns_obs_info_with_required_fields():
        env = AuditEnv(); obs, info = env.reset(SEED)
        assert set(obs) == {"task", "manifest", "policy_summary", "steps_remaining"} and obs["steps_remaining"] == 100
        for k in ("schema_version", "episode_id", "base_currency", "period_start", "period_end", "timezone", "counts", "rounding"):
            assert k in obs["manifest"], k
        assert {"episode_id", "env_version", "mode"} <= set(info)
        json.dumps([obs, info])

    @check
    def reset_does_not_reveal_seed_or_evaluator_data():
        env = AuditEnv(); obs, info = env.reset(SEED)
        txt = json.dumps([obs, info])
        assert "ISS-" not in txt and "truth" not in txt.lower() and "provenance" not in txt.lower() and '"seed"' not in txt

    @check
    def step_returns_five_tuple_json_contract():
        env, obs, info = _fresh()
        out = env.step({"action": "calculator", "expression": "2*3"})
        assert len(out) == 5
        o, r, te, tr, inf = out
        assert isinstance(r, float) and te is False and tr is False and isinstance(inf, dict)
        assert o["ok"] and o["result"]["value"] == "6" and o["steps_remaining"] == 99
        json.dumps(out)

    @check
    def pages_are_at_most_50_and_cursors_are_stable_and_complete():
        env, obs, info = _fresh()
        for table in ("ledger", "invoices", "payments", "fx"):
            seen, cur, pages = [], None, 0
            while True:
                o, *_ = env.step({"action": "list_records", "table": table, "cursor": cur, "limit": 500})
                assert o["ok"] and len(o["result"]["records"]) <= 50
                seen += o["result"]["records"]; cur = o["result"]["next_cursor"]; pages += 1
                if cur is None:
                    break
            assert len(seen) == o["result"]["total"] == len(episode().tables[table])
            o1, *_ = env.step({"action": "list_records", "table": table, "cursor": "c0", "limit": 3})
            o2, *_ = env.step({"action": "list_records", "table": table, "cursor": "c0", "limit": 3})
            assert o1["result"] == o2["result"]

    @check
    def get_record_and_get_document_return_requested_records_only():
        env, obs, info = _fresh(); ep = episode()
        row, inv, pay, fx = ep.tables["ledger"][0], ep.tables["invoices"][0], ep.tables["payments"][0], ep.tables["fx"][0]
        assert env.step({"action": "get_record", "table": "ledger", "id": row["row_id"]})[0]["result"] == row
        assert env.step({"action": "get_record", "table": "invoices", "id": inv["invoice_id"]})[0]["result"] == inv
        assert env.step({"action": "get_record", "table": "payments", "id": pay["payment_id"]})[0]["result"] == pay
        fid = f"fx:{fx['date']}:{fx['source_currency']}:{fx['target_currency']}"
        assert env.step({"action": "get_record", "table": "fx", "id": fid})[0]["result"] == fx
        assert env.step({"action": "get_document", "doc_id": inv["doc_id"]})[0]["result"] == inv
        assert env.step({"action": "get_document", "doc_id": pay["doc_id"]})[0]["result"] == pay
        assert env.step({"action": "get_record", "table": "policy", "id": "policy"})[0]["ok"]

    @check
    def unknown_id_and_unknown_action_return_bounded_errors_and_cost_a_step():
        env, obs, info = _fresh()
        for a, code in (({"action": "get_record", "table": "ledger", "id": "nope"}, "unknown_id"),
                        ({"action": "get_document", "doc_id": "nope"}, "unknown_id"),
                        ({"action": "get_record", "table": "nope", "id": "x"}, "unknown_table"),
                        ({"action": "shell", "cmd": "ls"}, "unknown_action")):
            before = env._steps
            o, r, te, tr, _ = env.step(a)
            assert not o["ok"] and o["error"]["code"] == code and env._steps == before + 1 and not te and r == 0.0
            assert len(json.dumps(o["error"])) < 120

    @check
    def malformed_actions_never_crash():
        env, obs, info = _fresh()
        for a in (None, 5, "list_records", [], {}, {"action": 3}, {"action": "list_records"}, {"action": "list_records", "table": "ledger", "limit": 0},
                  {"action": "list_records", "table": "ledger", "limit": "x"}, {"action": "list_records", "table": "ledger", "cursor": "zzz"},
                  {"action": "list_records", "table": "ledger", "cursor": "c999999"}, {"action": "get_record", "table": 1, "id": 2},
                  {"action": "get_document", "doc_id": 5}, {"action": "calculator"}, {"action": "calculator", "expression": 5}):
            o, r, te, tr, _ = env.step(a)
            assert o["ok"] in (True, False) and not te and r == 0.0, a

    @check
    def calculator_is_arithmetic_only():
        env, obs, info = _fresh()
        ok = {"1+2*3": "7", "(1+2)*3": "9", "10/4": "2.5", "-2.5*4": "-10", "1000000*1000000": "1000000000000", "0.1+0.2": "0.3"}
        for e, v in ok.items():
            assert env.step({"action": "calculator", "expression": e})[0]["result"]["value"] == v, e
        for e in ("__import__('os')", "open('/etc/passwd')", "2**10", "1e3", "a", "1/0", "(", "", "1; 2", "lambda: 1", "1 if 1 else 2", "[1]", "0x10", "1_0", "9" * 70):
            o = env.step({"action": "calculator", "expression": e})[0]
            assert not o["ok"] and o["error"]["code"] == "calc_error", e

    @check
    def submit_terminates_with_terminated_true_not_truncated():
        env, obs, info = _fresh()
        o, r, te, tr, _ = env.step({"action": "submit", "findings": {"episode_id": info["episode_id"], "findings": []}})
        assert te is True and tr is False and o["steps_remaining"] == 99

    @check
    def submit_is_allowed_as_the_hundredth_step():
        env, obs, info = _fresh()
        for _ in range(99):
            env.step({"action": "calculator", "expression": "1"})
        o, r, te, tr, _ = env.step({"action": "submit", "findings": {"episode_id": info["episode_id"], "findings": truth_findings(episode())}})
        assert te and not tr and env.evaluation()["f1"] == 1.0 and env.evaluation()["inspection_steps"] == 99

    @check
    def step_after_end_does_not_change_state():
        env, obs, info = _fresh()
        env.step({"action": "submit", "findings": {"episode_id": info["episode_id"], "findings": []}})
        snap = env.evaluation()
        for _ in range(3):
            o, r, te, tr, _ = env.step({"action": "calculator", "expression": "1"})
            assert te and r == 0.0 and o["error"]["code"] == "episode_finished"
        assert env.evaluation() == snap

    @check
    def reset_isolates_episode_state():
        env = AuditEnv()
        env.reset(SEED); [env.step({"action": "calculator", "expression": "1"}) for _ in range(30)]
        obs, info = env.reset(SEED + 1)
        assert obs["steps_remaining"] == 100 and env._steps == 0 and not env._done
        o, *_ = env.step({"action": "calculator", "expression": "1"})
        assert o["steps_remaining"] == 99

    @check
    def same_seed_config_actions_reproduce_records_transitions_rewards():
        def trace():
            env = AuditEnv(); obs, info = env.reset(11, {"interactions": ["partial_fx"]}); out = [obs, info]
            acts = [{"action": "list_records", "table": "ledger", "limit": 50}, {"action": "calculator", "expression": "3/7"},
                    {"action": "get_record", "table": "ledger", "id": "x"}, {"action": "submit", "findings": {"episode_id": info["episode_id"], "findings": []}}]
            for a in acts:
                out.append(env.step(a))
            return hashlib.sha256(json.dumps(out, sort_keys=True).encode()).hexdigest()
        assert trace() == trace()

    @check
    def different_seeds_differ_and_config_changes_episode_id():
        a, b = generate_episode(1), generate_episode(2)
        assert a.episode_id != b.episode_id and a.tables["ledger"] != b.tables["ledger"]
        assert generate_episode(1, {"id_salt": "x"}).episode_id != a.episode_id

    @check
    def exploration_never_leaks_evaluator_state():
        env, obs, info = _fresh(); ep = episode()
        secrets = [i["issue_id"] for i in ep.truth["issues"]] + ["expected_amount_minor", "acceptable_evidence_sets", "provenance", "truth.json"]
        outs = []
        for t in ("ledger", "invoices", "payments", "fx"):
            cur = None
            while True:
                o = env.step({"action": "list_records", "table": t, "cursor": cur, "limit": 50})[0]; outs.append(o)
                cur = o["result"]["next_cursor"]
                if cur is None:
                    break
        outs.append(env.step({"action": "get_record", "table": "policy", "id": "policy"})[0])
        outs.append(env.step({"action": "get_record", "table": "ledger", "id": "../../etc/passwd"})[0])
        outs.append(env.step({"action": "get_record", "table": "truth", "id": "truth"})[0])
        txt = json.dumps(outs)
        for s in secrets:
            assert s not in txt, s

    @check
    def observation_is_a_copy_agent_cannot_mutate_environment_state():
        env, obs, info = _fresh()
        o = env.step({"action": "list_records", "table": "ledger", "limit": 5})[0]
        o["result"]["records"][0]["debit_minor"] = -1
        o["result"]["records"].clear()
        o2 = env.step({"action": "list_records", "table": "ledger", "limit": 5})[0]
        assert len(o2["result"]["records"]) == 5 and o2["result"]["records"][0]["debit_minor"] != -1

    @check
    def record_schemas_match_the_published_columns():
        ep = episode()
        assert list(ep.tables["ledger"][0]) == ["row_id", "timestamp", "account", "debit_minor", "credit_minor", "currency", "entity_id", "invoice_id", "payment_id"]
        assert {"doc_id", "invoice_id", "entity_id", "issued_at", "due_at", "currency", "total_minor", "line_items"} <= set(ep.tables["invoices"][0])
        assert {"doc_id", "payment_id", "timestamp", "currency", "amount_minor", "invoice_refs"} <= set(ep.tables["payments"][0])
        assert list(ep.tables["fx"][0]) == ["date", "source_currency", "target_currency", "rate"]

    @check
    def missing_references_are_explicit_null():
        ep = episode(7, {"faults": {"duplicate_invoice": 0, "payment_allocation": 1, "fx_error": 0, "period_cutoff": 0}, "interactions": []})
        assert any(r["payment_id"] is None for r in ep.tables["ledger"]) and any(r["invoice_id"] is None for r in ep.tables["ledger"])
        for s in range(20, 40):
            e = generate_episode(s, {"faults": {"duplicate_invoice": 0, "payment_allocation": 3, "fx_error": 0, "period_cutoff": 0}})
            for r in e.tables["payments"]:
                assert "invoice_refs" in r

    @check
    def isolated_process_env_matches_in_process_env_and_holds_no_truth():
        from .remote import RemoteEnv
        r = RemoteEnv(mode="eval", secret="same-secret")
        try:
            obs, info = r.reset(SEED)
            assert not hasattr(r, "_ep") and not hasattr(r, "truth")
            assert r._p.pid != __import__("os").getpid()
            env = AuditEnv(mode="eval", secret="same-secret"); obs2, info2 = env.reset(SEED)
            assert obs == obs2 and info == info2
            a = {"action": "list_records", "table": "payments", "limit": 7}
            assert r.step(a) == env.step(a)
            o, rw, te, tr, inf = r.step({"action": "submit", "findings": {"episode_id": info["episode_id"], "findings": []}})
            assert te and rw == 0.0 and r.evaluation()["f1"] == 0.0
        finally:
            r.close()

    @check
    def evaluator_secret_defeats_seed_regeneration():
        # without a secret the public generator reproduces the episode; with it, no seed in the range matches
        env = AuditEnv(mode="eval", secret="organiser-only-secret")
        obs, info = env.reset(SEED)
        plain = AuditEnv(mode="eval").reset(SEED)[0]
        assert obs["manifest"] != plain["manifest"]
        target = obs["manifest"]
        assert all(generate_episode(s).manifest != target for s in range(0, 60))
        # deterministic for the same secret
        assert AuditEnv(mode="eval", secret="organiser-only-secret").reset(SEED)[0] == obs

    @check
    def remote_secret_stays_inside_evaluator_process():
        from .remote import RemoteEnv
        with RemoteEnv(mode="eval", secret="s3cr3t-xyz") as r:
            obs, info = r.reset(SEED)
            assert "s3cr3t" not in json.dumps([obs, info])
            assert obs == AuditEnv(mode="eval", secret="s3cr3t-xyz").reset(SEED)[0]
            o = r.step({"action": "get_record", "table": "ledger", "id": "s3cr3t-xyz"})[0]
            assert "s3cr3t" not in json.dumps(o)

    @check
    def agent_cannot_change_mode_limits_or_rerun_eval_over_the_pipe():
        from .remote import RemoteEnv
        with RemoteEnv(mode="eval") as r:
            for bad in ({"op": "reset", "seed": SEED, "mode": "train"},
                        {"op": "reset", "seed": SEED, "limits": {"max_steps": 100000}}):
                assert r._call(bad, allow_fatal=True) == {"fatal": "forbidden_field"}
            r.reset(SEED)
            assert r._call({"op": "reset", "seed": SEED}, allow_fatal=True) == {"fatal": "eval_single_episode"}
            o, rw, te, tr, inf = r.step({"action": "submit", "findings": {"episode_id": "x", "findings": []}})
            assert rw == 0.0 and set(inf) == {"step"}

    @check
    def eval_without_organiser_secret_is_still_not_regenerable():
        from .remote import RemoteEnv
        with RemoteEnv(mode="eval") as r:
            obs, info = r.reset(SEED)
            r.step({"action": "submit", "findings": {"episode_id": info["episode_id"], "findings": []}})
            assert r.evaluation()["secret_source"] == "ephemeral"
        assert obs["manifest"] != AuditEnv(mode="eval").reset(SEED)[0]["manifest"]

    @check
    def secret_is_not_in_evaluator_environment():
        from .remote import RemoteEnv
        with RemoteEnv(mode="eval", secret="s3cr3t-env-probe") as r:
            r.reset(SEED)
            path = f"/proc/{r._p.pid}/environ"
            if os.path.exists(path):
                assert b"s3cr3t-env-probe" not in open(path, "rb").read()
        tmp = __import__("tempfile").gettempdir()
        assert not [n for n in os.listdir(tmp) if n.startswith("af-secret-")]   # temp secret file removed

    @check
    def malformed_cursors_and_seeds_are_errors_not_crashes():
        env, obs, info = _fresh()
        for c in ("c\u00b2", "c\u0661\u0660", "c" + "9" * 5000, "c-1", "c 1", "c", 5):
            o = env.step({"action": "list_records", "table": "ledger", "cursor": c})[0]
            assert not o["ok"] and o["error"]["code"] == "invalid_cursor", c
        for bad in (None, "1", 1.5, True, -1):
            try:
                AuditEnv().reset(bad)
            except ValueError:
                pass
            else:
                raise AssertionError(f"seed {bad!r} accepted")

    @check
    def list_records_without_limit_uses_full_page():
        env, obs, info = _fresh()
        o = env.step({"action": "list_records", "table": "ledger", "limit": None})[0]
        assert o["ok"] and len(o["result"]["records"]) == 50
        o = env.step({"action": "list_records", "table": "ledger"})[0]
        assert o["ok"] and len(o["result"]["records"]) == 50

    @check
    def dead_evaluator_process_is_reported_not_hung():
        from .remote import RemoteEnv
        r = RemoteEnv()
        r.reset(SEED)
        r._p.kill(); r._p.wait()
        try:
            r.step({"action": "calculator", "expression": "1"})
        except RuntimeError as e:
            assert "evaluator_process_died" in str(e)
        else:
            raise AssertionError("no error on dead evaluator")

    @check
    def trajectory_lines_have_required_fields_and_no_truth():
        import io
        buf = io.StringIO()
        run_episode(ReferenceSolver(), SEED, None, traj=buf)
        lines = [json.loads(l) for l in buf.getvalue().splitlines()]
        assert lines[0]["step"] == 0 and lines[-1]["terminated"]
        for l in lines:
            assert {"episode_id", "step", "action", "observation", "reward", "terminated", "truncated"} <= set(l)
        txt = buf.getvalue()
        assert "ISS-" not in txt and "acceptable_evidence_sets" not in txt

    return C


# ======================================================================= paired checks
def paired_checks(seeds=(21, 22, 23, 24, 25), cfgs=None):
    """Return {name: callable}. Each = one (episode, transformation) pair: 5 seeds x 4 kinds = 20."""
    cfgs = cfgs or [{"interactions": ["partial_fx", "cutoff_fx"]}, {}, CLEAN, MULTI, {"interactions": ["cutoff_fx"]}]
    C = {}
    for n, seed in enumerate(seeds):
        for kind in ("shuffle", "rename_ids", "tz_shift", "all"):
            def fn(seed=seed, kind=kind, cfg=cfgs[n % len(cfgs)]):
                from .checks import detect, truth_tuples
                ep = episode(seed, cfg)
                ep2 = transform(ep, kind, seed)
                # detector and truth still agree on the transformed books
                assert detect(ep2.tables, ep2.manifest, ep2.policy) == truth_tuples(ep2.truth)
                # oracle: same reward before / after
                r1 = run_episode(Oracle(ep.truth), seed, cfg, episode=ep)["evaluation"]
                r2 = run_episode(Oracle(ep2.truth), seed, cfg, episode=ep2)["evaluation"]
                assert r1["reward"] == r2["reward"] == 1.0 and (r1["tp"], r1["fp"], r1["fn"]) == (r2["tp"], r2["fp"], r2["fn"])
                # a solver that works through the tool API adapts to new ids / order / time zones
                rs = run_episode(ReferenceSolver(), seed, cfg, episode=ep2)["evaluation"]
                assert rs["f1"] == 1.0
                if kind in ("rename_ids", "all") and ep.truth["issues"]:
                    # stale answer written with the OLD ids must not score on the renamed episode
                    env = AuditEnv(); obs, info = env.reset(episode=ep2)
                    old = [{"type": i["type"], "affected_ids": i["affected_ids"], "claimed_amount_minor": i["expected_amount_minor"],
                            "currency": i["currency"], "evidence_ids": i["acceptable_evidence_sets"][0], "explanation": ""} for i in ep.truth["issues"]]
                    env.step({"action": "submit", "findings": {"episode_id": info["episode_id"], "findings": old}})
                    assert env.evaluation()["tp"] == 0
            C[f"pair_{kind}_seed{seed}"] = fn
    return C


def repeat_checks(seeds=(31, 32, 33, 34, 35)):
    """Exact repeatability of generation and of full trajectories (hash equality)."""
    C = {}
    for seed in seeds:
        def fn(seed=seed):
            import io
            cfg = {"interactions": ["partial_fx", "cutoff_fx"]}
            a, b = generate_episode(seed, cfg), generate_episode(seed, cfg)
            assert json.dumps([a.tables, a.truth, a.manifest, a.policy, a.provenance], sort_keys=True, default=str) == \
                   json.dumps([b.tables, b.truth, b.manifest, b.policy, b.provenance], sort_keys=True, default=str)
            h = []
            for _ in range(2):
                buf = io.StringIO(); run_episode(ReferenceSolver(), seed, cfg, traj=buf); h.append(buf.getvalue())
            assert h[0] == h[1]
        C[f"repeat_seed{seed}"] = fn
    return C


def run_checks(checks: dict) -> dict:
    out = {}
    for name, fn in checks.items():
        try:
            fn()
            out[name] = True
        except BaseException as e:  # noqa
            out[name] = f"{type(e).__name__}: {str(e)[:160]}"
    return out
