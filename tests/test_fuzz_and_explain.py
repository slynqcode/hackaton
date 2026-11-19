from auditforge import fuzz
from auditforge.explain import explain
from auditforge.generator import FAULT_TYPES, generate_episode
from auditforge.policies import ZeroAgent
from auditforge.runner import run_episode


def test_fuzzer_finds_no_unsound_reward():
    s = fuzz.soundness(n_episodes=4, per_episode=150, seed=5)
    assert s["n_violations"] == 0 and s["tp_awarded"] > 0


def test_blind_guessing_from_public_records_stays_at_minus_one():
    assert fuzz.blind_search(n_episodes=4, tries=80)["max_best_reward"] < 0.0


def test_secret_blocks_seed_regeneration():
    r = fuzz.regeneration_attack(seed_range=60)
    assert r["recovered_without_secret"] and not r["recovered_with_secret"]


def test_zero_agent_diagnostic():
    assert run_episode(ZeroAgent(), 11, {"faults": {k: 0 for k in FAULT_TYPES}})["evaluation"]["reward"] == 1.0
    assert run_episode(ZeroAgent(), 11, None)["evaluation"]["reward"] == -1.0


def test_explain_report_lists_every_issue_and_draws_causal_links():
    ep = generate_episode(4242, {"interactions": ["partial_fx", "cutoff_fx"]})
    md = explain(ep)
    assert "```mermaid" in md and md.count("==>|") == 2
    for i in ep.truth["issues"]:
        assert i["affected_ids"][0] in md
    assert "Clean company" in explain(generate_episode(3, {"faults": {k: 0 for k in FAULT_TYPES}}))
