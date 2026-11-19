import json
import os

from auditforge.certificate import certify
from auditforge.env import AuditEnv
from auditforge.generator import generate_episode, read_episode, write_episode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_write_read_roundtrip_and_certificate(tmp_path):
    ep = generate_episode(33, {"interactions": ["partial_fx", "cutoff_fx"]})
    base = write_episode(ep, str(tmp_path))
    back = read_episode(base)
    assert back.tables == ep.tables and back.manifest == ep.manifest and back.policy == ep.policy and back.truth == ep.truth
    assert certify(back)["passed"]


def test_public_dir_contains_only_the_six_open_files(tmp_path):
    ep = generate_episode(34)
    base = write_episode(ep, str(tmp_path))
    assert sorted(os.listdir(os.path.join(base, "public"))) == sorted(["manifest.json", "ledger.csv", "invoices.jsonl", "payments.jsonl", "fx.csv", "policy.json"])
    for f in os.listdir(os.path.join(base, "public")):
        txt = open(os.path.join(base, "public", f)).read()
        assert "ISS-" not in txt and "acceptable_evidence" not in txt


def test_env_loads_from_disk_episode_and_replays_identically(tmp_path):
    ep = generate_episode(35)
    back = read_episode(write_episode(ep, str(tmp_path)))
    a, b = AuditEnv(), AuditEnv()
    assert a.reset(episode=ep) == b.reset(episode=back)
    act = {"action": "list_records", "table": "ledger", "limit": 50}
    assert a.step(act) == b.step(act)


def test_shipped_episodes_are_certified_and_trajectories_clean():
    idx = json.load(open(os.path.join(ROOT, "episodes", "index.json")))
    assert len(idx["episodes"]) == 20 and all(e["certified"] for e in idx["episodes"])
    assert sum(1 for e in idx["episodes"] if e["split"] == "train") == 10 and sum(1 for e in idx["episodes"] if e["split"] == "dev") == 10
    seen = set()
    secrets = []
    for e in idx["episodes"]:
        tr = json.load(open(os.path.join(ROOT, "episodes", e["split"], e["episode_id"], "evaluator", "truth.json")))
        secrets += [i["issue_id"] for i in tr["issues"]]
    with open(os.path.join(ROOT, "trajectories.jsonl")) as f:
        for line in f:
            for s in secrets:
                assert s not in line
            rec = json.loads(line)
            assert {"episode_id", "step", "action", "observation", "reward", "terminated", "truncated"} <= set(rec)
            seen.add(rec["episode_id"])
            assert "acceptable_evidence_sets" not in line and "expected_amount_minor" not in line.replace("claimed_amount_minor", "")
    assert len(seen) == 10


def test_generation_is_identical_across_processes_and_hash_seeds():
    import subprocess, sys
    code = ("import sys,json,hashlib;sys.path.insert(0,%r);from auditforge.generator import generate_episode as g;"
            "ep=g(5,{'interactions':['partial_fx','cutoff_fx']});"
            "print(hashlib.sha256(json.dumps([ep.tables,ep.truth,ep.provenance],sort_keys=True,default=str).encode()).hexdigest())") % ROOT
    outs = {subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env={**os.environ, "PYTHONHASHSEED": h}).stdout for h in ("0", "99")}
    assert len(outs) == 1 and len(next(iter(outs)).strip()) == 64
