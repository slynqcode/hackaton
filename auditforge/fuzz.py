"""Reward-hacking fuzzer.

1. soundness   : thousands of random submissions (perturbed true findings + junk built from real public records).
                 Every TP the grader awards is re-checked by an INDEPENDENT predicate written here (not grader code),
                 and no submission may beat the oracle.
2. blind search: best-of-N random structured guessing that only uses public records (doc ids, ledger rows, amounts,
                 currencies). Measures how far an agent gets without analysing the books.
3. regeneration: the public generator lets an agent recover an episode by brute-forcing seeds; with the evaluator
                 secret it must fail.
"""
from __future__ import annotations

import random
import statistics
import time

from . import grader as G
from .checks import fx_record_id
from .generator import FAULT_TYPES, generate_episode

CFGS = [{}, {"interactions": ["partial_fx", "cutoff_fx"]}, {"faults": {k: 0 for k in FAULT_TYPES}},
        {"faults": {k: 2 for k in FAULT_TYPES}}]


def _known(ep):
    t = ep.tables
    return frozenset(r["row_id"] for r in t["ledger"]) | frozenset(r["doc_id"] for r in t["invoices"] + t["payments"]) | \
        frozenset(fx_record_id(r) for r in t["fx"])


def _truth_finding(i):
    return {"type": i["type"], "affected_ids": list(i["affected_ids"]), "claimed_amount_minor": i["expected_amount_minor"],
            "currency": i["currency"], "evidence_ids": list(i["acceptable_evidence_sets"][0]), "explanation": ""}


def _independent_ok(f: dict, t: dict, known, tol: int) -> bool:
    """Written from the task text, deliberately not reusing grader helpers."""
    ev = {e.strip() for e in f["evidence_ids"]}
    return (f["type"] == t["type"]
            and {a.strip() for a in f["affected_ids"]} == set(t["affected_ids"])
            and abs(int(f["claimed_amount_minor"]) - t["expected_amount_minor"]) <= tol
            and f["currency"].strip().upper() == t["currency"]
            and any(set(s) <= ev for s in t["acceptable_evidence_sets"])
            and ev <= known)


def _junk(rng, ep):
    t = ep.tables
    doc = rng.choice(t["invoices"] + t["payments"])
    rows = rng.sample(t["ledger"], rng.randint(0, 3))
    ids = [doc.get("invoice_id") or doc.get("payment_id")]
    if rng.random() < 0.4:
        other = rng.choice(t["invoices"])
        ids.append(other["invoice_id"])
    amt = rng.choice([doc.get("total_minor") or abs(doc.get("amount_minor", 0)), rng.randint(0, 10**7)] +
                     [r["debit_minor"] + r["credit_minor"] for r in rows])
    ev = [doc["doc_id"]] + [r["row_id"] for r in rows]
    if rng.random() < 0.3:
        ev.append(fx_record_id(rng.choice(t["fx"])))
    if rng.random() < 0.1:
        ev.append("FAKE-" + str(rng.randint(0, 999)))
    return {"type": rng.choice(FAULT_TYPES), "affected_ids": ids, "claimed_amount_minor": abs(int(amt)),
            "currency": rng.choice(ep.manifest["currencies"]), "evidence_ids": ev[:10], "explanation": ""}


def _perturb(rng, f, ep):
    g = dict(f, affected_ids=list(f["affected_ids"]), evidence_ids=list(f["evidence_ids"]))
    k = rng.randrange(7)
    if k == 0:
        g["claimed_amount_minor"] = max(0, g["claimed_amount_minor"] + rng.choice([-3, -2, -1, 1, 2, 3, 100]))
    elif k == 1:
        g["currency"] = rng.choice(ep.manifest["currencies"])
    elif k == 2 and g["evidence_ids"]:
        g["evidence_ids"].pop(rng.randrange(len(g["evidence_ids"])))
    elif k == 3:
        g["type"] = rng.choice(FAULT_TYPES)
    elif k == 4 and len(g["affected_ids"]) > 1:
        g["affected_ids"].pop()
    elif k == 5:
        g["evidence_ids"] = (g["evidence_ids"] + [rng.choice(ep.tables["ledger"])["row_id"]])[:10]
    else:
        g["affected_ids"] = g["affected_ids"][::-1] + ([rng.choice(ep.tables["invoices"])["invoice_id"]] if rng.random() < 0.3 else [])
    return g


def soundness(n_episodes=8, per_episode=400, seed=0) -> dict:
    rng = random.Random(seed)
    violations, total, tps = [], 0, 0
    for e in range(n_episodes):
        ep = generate_episode(7000 + e, CFGS[e % len(CFGS)])
        known, issues, tol = _known(ep), ep.truth["issues"], ep.policy["amount_tolerance_minor"]
        oracle = G.grade(G.validate_submission({"episode_id": ep.episode_id, "findings": [_truth_finding(i) for i in issues]},
                                               ep.episode_id), issues, tol, 0, known)["reward"]
        base = [_truth_finding(i) for i in issues]
        for _ in range(per_episode):
            fs = [rng.random() < 0.5 and _perturb(rng, f, ep) or dict(f) for f in base if rng.random() < 0.8]
            fs += [_junk(rng, ep) for _ in range(rng.randint(0, 8))]
            if fs and rng.random() < 0.2:
                fs.append(dict(rng.choice(fs)))         # duplicate
            rng.shuffle(fs)
            fs = fs[:30]
            r = G.grade(G.validate_submission({"episode_id": ep.episode_id, "findings": fs}, ep.episode_id), issues, tol, 0, known)
            total += 1
            tps += r["tp"]
            if r["reward"] > oracle + 1e-12:
                violations.append(("beats_oracle", ep.episode_id))
            for fi, ti in r["matched"]:
                if not _independent_ok(fs[fi], issues[ti], known, tol):
                    violations.append(("unsound_tp", ep.episode_id, fs[fi]["type"]))
            coverable = sum(1 for t in issues if any(_independent_ok(f, t, known, tol) for f in fs))
            if r["tp"] > coverable:
                violations.append(("tp_exceeds_coverable", ep.episode_id))
    return {"submissions": total, "tp_awarded": tps, "violations": violations[:10], "n_violations": len(violations)}


def blind_search(n_episodes=10, tries=300, seed=1) -> dict:
    """Best reward reachable by structured random guessing from public records (no analysis, no truth)."""
    rng = random.Random(seed)
    best = []
    for e in range(n_episodes):
        ep = generate_episode(7100 + e, CFGS[e % 2])          # episodes WITH errors only
        known, issues, tol = _known(ep), ep.truth["issues"], ep.policy["amount_tolerance_minor"]
        b = -1.0
        for _ in range(tries):
            fs = [_junk(rng, ep) for _ in range(rng.randint(1, 30))]
            r = G.grade(G.validate_submission({"episode_id": ep.episode_id, "findings": fs}, ep.episode_id), issues, tol, 0, known)
            b = max(b, r["reward"])
        best.append(b)
    return {"episodes": n_episodes, "tries_per_episode": tries, "mean_best_reward": statistics.mean(best), "max_best_reward": max(best)}


def regeneration_attack(seed_range=400, secret="organiser-secret") -> dict:
    from .env import AuditEnv
    target_seed = seed_range // 2 + 3
    t0 = time.time()
    plain = AuditEnv(mode="eval").reset(target_seed)[0]["manifest"]
    hit_plain = next((s for s in range(seed_range) if generate_episode(s).manifest == plain), None)
    secret_m = AuditEnv(mode="eval", secret=secret).reset(target_seed)[0]["manifest"]
    hit_secret = next((s for s in range(seed_range) if generate_episode(s).manifest == secret_m), None)
    return {"seed_range": seed_range, "recovered_without_secret": hit_plain is not None,
            "recovered_with_secret": hit_secret is not None, "seconds": round(time.time() - t0, 1)}


def run_all(quick=False) -> dict:
    s = soundness(per_episode=150 if quick else 400)
    b = blind_search(tries=100 if quick else 300)
    g = regeneration_attack(seed_range=120 if quick else 400)
    ok = s["n_violations"] == 0 and b["max_best_reward"] < 0.0 and g["recovered_without_secret"] and not g["recovered_with_secret"]
    return {"passed": ok, "soundness": s, "blind_search": b, "regeneration": g}


if __name__ == "__main__":
    import json
    print(json.dumps(run_all(), indent=1))
