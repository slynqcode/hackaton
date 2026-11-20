"""Demo: scripted policies against the isolated evaluator process (no model, no network).
    python demo.py [seed]
Shows one episode with both interacting scenarios: what the books look like, what each policy does, how it is scored."""
import json
import secrets
import sys

from auditforge.env import AuditEnv
from auditforge.policies import FlagAll, Oracle, ReferenceSolver, SimpleReconciler
from auditforge.remote import RemoteEnv
from auditforge.runner import run_episode

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 4242
cfg = {"interactions": ["partial_fx", "cutoff_fx"]}
# the organiser's secret: the evaluator process gets it, the policies never do. Random by default (the hidden
# episode differs every run); pass your own as the 2nd argument to repeat a printout exactly.
secret = sys.argv[2] if len(sys.argv) > 2 else secrets.token_hex(16)
h = AuditEnv(mode="eval", secret=secret); h.reset(seed, cfg); ep = h._ep   # harness-side copy (oracle + printout)
print(f"episode {ep.episode_id}: {ep.manifest['counts']}  tz={ep.manifest['timezone']}  base={ep.manifest['base_currency']}")
print("hidden truth (evaluator-only):")
for i in ep.truth["issues"]:
    print(f"  {i['type']:20s} {i['affected_ids']}  {i['expected_amount_minor']} {i['currency']}")
print("causal links:", [l["scenario"] + ": " + l["mechanism"] for l in ep.provenance["causal_links"]])
print()
for pol in (SimpleReconciler(), FlagAll(), ReferenceSolver(), Oracle(ep.truth)):
    env = RemoteEnv(mode="eval", secret=secret)
    try:
        r = run_episode(pol, seed, cfg, env=env)["evaluation"]
    finally:
        env.close()
    print(f"{pol.name:18s} steps={r['inspection_steps']:3d} TP={r['tp']} FP={r['fp']} FN={r['fn']}  P={r['precision']:.2f} R={r['recall']:.2f} F1={r['f1']:.2f}  return={r['reward']:+.3f}")
