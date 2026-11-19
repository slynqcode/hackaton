"""Randomised properties of matcher + reward (no external libs)."""
import random

from auditforge.grader import grade, terminal_reward, validate_submission
from auditforge.selfchecks import episode, truth_findings, sub


def test_reward_always_in_range_and_f1_in_unit_interval():
    rng = random.Random(1)
    ep = episode()
    base = truth_findings(ep)
    for _ in range(300):
        fs = []
        for f in base:
            if rng.random() < 0.7:
                g = dict(f)
                if rng.random() < 0.3:
                    g["claimed_amount_minor"] += rng.randint(-3, 3)
                if rng.random() < 0.2:
                    g["evidence_ids"] = []
                fs.append(g)
        fs += [dict(rng.choice(base), affected_ids=[f"X{rng.randint(0, 5)}"]) for _ in range(rng.randint(0, 6))]
        rng.shuffle(fs)
        r = grade(validate_submission(sub(ep, fs), ep.episode_id), ep.truth["issues"], 1, rng.randint(0, 100))
        assert -1.0 <= r["reward"] <= 1.0 and 0.0 <= r["f1"] <= 1.0
        assert r["tp"] + r["fn"] == len(ep.truth["issues"]) and r["tp"] + r["fp"] == len(fs)
        assert abs(sum(c["tp"] for c in r["by_type"].values()) - r["tp"]) == 0


def test_more_true_findings_never_lower_f1_without_new_fps():
    ep = episode()
    base = truth_findings(ep)
    prev = -1
    for k in range(len(base) + 1):
        r = grade(validate_submission(sub(ep, base[:k]), ep.episode_id), ep.truth["issues"], 1, 0)
        assert r["f1"] >= prev
        prev = r["f1"]


def test_reward_is_monotone_in_steps():
    assert all(terminal_reward(0.6, s) >= terminal_reward(0.6, s + 1) for s in range(0, 100))


def test_adding_any_false_positive_never_helps():
    rng = random.Random(2)
    ep = episode()
    base = truth_findings(ep)
    r0 = grade(validate_submission(sub(ep, base), ep.episode_id), ep.truth["issues"], 1, 0)
    for _ in range(50):
        extra = dict(rng.choice(base), claimed_amount_minor=rng.randint(0, 10**9), affected_ids=[f"Q{rng.randint(0, 10**6)}"])
        r1 = grade(validate_submission(sub(ep, base + [extra]), ep.episode_id), ep.truth["issues"], 1, 0)
        assert r1["reward"] < r0["reward"]
