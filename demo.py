"""Demo: scripted policies against the isolated evaluator process (no model, no network).
    python demo.py [seed]
Shows one episode with both interacting scenarios: what the books look like, what each policy does, how it is scored."""
import json
import sys

from auditforge.generator import generate_episode
from auditforge.policies import FlagAll, Oracle, ReferenceSolver, SimpleReconciler
from auditforge.remote import RemoteEnv
from auditforge.runner import run_episode

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 4242
cfg = {"interactions": ["partial_fx", "cutoff_fx"]}
ep = generate_episode(seed, cfg)   # harness-side copy (needed only by the oracle and for this printout)
print(f"episode {ep.episode_id}: {ep.manifest['counts']}  tz={ep.manifest['timezone']}  base={ep.manifest['base_currency']}")
print("hidden truth (evaluator-only):")
for i in ep.truth["issues"]:
    print(f"  {i['type']:20s} {i['affected_ids']}  {i['expected_amount_minor']} {i['currency']}")
print("causal links:", [l["scenario"] + ": " + l["mechanism"] for l in ep.provenance["causal_links"]])
print()
for pol in (SimpleReconciler(), FlagAll(), ReferenceSolver(), Oracle(ep.truth)):
    env = RemoteEnv(mode="eval")
    try:
        r = run_episode(pol, seed, cfg, env=env)["evaluation"]
    finally:
        env.close()
    print(f"{pol.name:18s} steps={r['inspection_steps']:3d} TP={r['tp']} FP={r['fp']} FN={r['fn']}  P={r['precision']:.2f} R={r['recall']:.2f} F1={r['f1']:.2f}  return={r['reward']:+.3f}")
