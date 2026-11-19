import pytest

from auditforge.calc import CalcError, evaluate
from auditforge.generator import generate_episode
from auditforge.policies import FlagAll, Oracle, RandomExplorer, ReferenceSolver, SimpleReconciler
from auditforge.runner import run_episode


@pytest.mark.parametrize("expr,val", [("1+1", "2"), ("2*(3+4)", "14"), ("6/3", "2"), ("-(2+3)*2", "-10"), ("123456789*987654321", "121932631112635269"), ("5/8", "0.625")])
def test_calc_ok(expr, val):
    assert evaluate(expr) == val


@pytest.mark.parametrize("expr", ["", "1+", "(1", "1)", "2**2", "abs(1)", "__import__('os')", "1e3", "1,5", "x", "1 1", "1//2", "1%2", "5/0", "9" * 61])
def test_calc_rejects(expr):
    with pytest.raises(CalcError):
        evaluate(expr)


def test_baseline_ordering_on_mixed_episodes():
    totals = {"oracle": [], "reference": [], "simple": [], "flag": [], "random": []}
    for s in range(9600, 9610):
        cfg = {"interactions": ["partial_fx", "cutoff_fx"]} if s % 2 else {}
        ep = generate_episode(s, cfg)
        for k, pol in (("oracle", Oracle(ep.truth)), ("reference", ReferenceSolver()), ("simple", SimpleReconciler()), ("flag", FlagAll()), ("random", RandomExplorer(s))):
            totals[k].append(run_episode(pol, s, cfg, episode=ep)["evaluation"]["reward"])
    m = {k: sum(v) / len(v) for k, v in totals.items()}
    assert m["oracle"] == 1.0 and m["oracle"] > m["reference"] > m["simple"] > m["flag"]
    assert m["flag"] == -1.0 and m["random"] < 0.0


def test_random_explorer_is_seed_deterministic():
    a = run_episode(RandomExplorer(5), 9610, None)["evaluation"]
    b = run_episode(RandomExplorer(5), 9610, None)["evaluation"]
    assert a == b


def test_policy_without_submit_is_closed_with_empty_answer():
    class Lazy:
        name = "lazy"
        def run(self, obs, info):
            yield {"action": "calculator", "expression": "1"}
    r = run_episode(Lazy(), 9611, None)["evaluation"]
    assert r["tp"] == 0 and r["reward"] <= -0.9
