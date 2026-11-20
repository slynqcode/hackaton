"""Regression guard: every shortcut rule that skips the accounting logic must pay with false accusations,
while the full-information detector (the real rules) stays exact."""
import json
import os

from auditforge.checks import detect, truth_tuples
from auditforge.generator import generate_episode
from auditforge.tricks import TRICKS, measure

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _episodes(split="train"):
    return [generate_episode(e["seed"], e["config"]) for e in json.load(open(os.path.join(ROOT, "configs", f"{split}.json")))["episodes"]]


def test_every_shortcut_rule_makes_false_accusations():
    rows = measure(_episodes("train") + _episodes("dev"))
    assert len(rows) == len(TRICKS)
    for r in rows:
        assert r["fp"] >= 10, r


def test_real_rules_stay_exact_with_new_distractors():
    for ep in _episodes("dev"):
        assert sorted(detect(ep.tables, ep.manifest, ep.policy)) == truth_tuples(ep.truth)
