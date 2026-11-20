"""Command line: python -m auditforge.cli {gen|baselines|mutation|analysis|verify}"""
from __future__ import annotations

import argparse
import json
import secrets
import os
import statistics
import sys
import time

from . import ENV_VERSION
from .certificate import certify
from .generator import generate_episode, write_episode
from .mutants import run_mutation_suite
from .policies import FlagAll, Oracle, RandomExplorer, ReferenceSolver, SimpleReconciler, ZeroAgent
from .explain import explain
from . import fuzz
from . import tricks
from .remote import RemoteEnv
from .runner import run_episode
from .env import AuditEnv
from . import selfchecks

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)


def load_split(name: str) -> dict:
    return json.load(open(P("configs", f"{name}.json")))


def make_policies(ep, seed):
    return [RandomExplorer(seed), SimpleReconciler(), FlagAll(), Oracle(ep.truth)]


def _summ(rows):
    """P and R are pooled over all findings/errors of the split (micro average): a per-episode mean would
    count clean episodes (no errors, nothing flagged: 0/0) as P=R=0 while F1=1. None = undefined (0/0)."""
    f = lambda k: statistics.mean(r[k] for r in rows)
    tp, fp, fn = (sum(r[k] for r in rows) for k in ("tp", "fp", "fn"))
    return {"episodes": len(rows), "tp": tp, "fp": fp, "fn": fn,
            "precision": tp / (tp + fp) if tp + fp else None, "recall": tp / (tp + fn) if tp + fn else None,
            "f1": f("f1"), "return": f("reward"),
            "inspection_steps": f("inspection_steps"), "wall_s": statistics.mean(r["wall_s"] for r in rows)}


def run_policies(split: str, mode: str, isolated: bool, traj=None, extra_reference=True):
    spec = load_split(split)
    per = {}
    # isolated eval = the organisers' setting: a secret known to the harness (needed only by the oracle's
    # solvability check) and to the evaluator process, never to the policies. Random per run by default; a fixed
    # value only on explicit request (AUDITFORGE_LOCAL_SECRET), never for a closed run.
    run_secret = (os.environ.get("AUDITFORGE_LOCAL_SECRET") or secrets.token_hex(16)) if isolated and mode == "eval" else None
    for e in spec["episodes"]:
        if run_secret:
            h = AuditEnv(mode="eval", secret=run_secret); h.reset(e["seed"], e["config"]); ep = h._ep
        else:
            ep = generate_episode(e["seed"], e["config"])
        pols = make_policies(ep, e["seed"]) + ([ReferenceSolver(), ZeroAgent()] if extra_reference else [])
        for pol in pols:
            if isolated:
                env = RemoteEnv(mode=mode, secret=run_secret)
                try:
                    r = run_episode(pol, e["seed"], e["config"], env=env, traj=traj)
                finally:
                    env.close()
            else:
                r = run_episode(pol, e["seed"], e["config"], mode=mode, episode=ep, traj=traj)
            ev = r["evaluation"]
            per.setdefault(pol.name, []).append({**{k: ev[k] for k in ("tp", "fp", "fn", "precision", "recall", "f1", "reward", "inspection_steps", "by_type")},
                                                 "wall_s": r["wall_s"], "name": e["name"], "seed": e["seed"],
                                                 "n_issues": ev["tp"] + ev["fn"]})
    return per


def cmd_gen(args):
    out = P("episodes")
    index = []
    for split in ("train", "dev"):
        for e in load_split(split)["episodes"]:
            ep = generate_episode(e["seed"], e["config"])
            base = write_episode(ep, os.path.join(out, split))
            cert = certify(ep)
            json.dump(cert, open(os.path.join(base, "evaluator", "certificate.json"), "w"), indent=1)
            open(os.path.join(base, "evaluator", "explain.md"), "w").write(explain(ep))
            index.append({"split": split, "name": e["name"], "episode_id": ep.episode_id, "seed": e["seed"],
                          "issues": len(ep.truth["issues"]), "certified": cert["passed"], "counts": ep.manifest["counts"]})
    json.dump({"env_version": ENV_VERSION, "episodes": index}, open(os.path.join(out, "index.json"), "w"), indent=1)
    print(f"wrote {len(index)} episodes, certified: {sum(i['certified'] for i in index)}")


def cmd_baselines(args):
    os.makedirs(P("reports"), exist_ok=True)
    result = {}
    with open(P("trajectories.jsonl"), "w") as traj:
        result["train"] = run_policies("train", "train", False, traj=traj)
    result["dev"] = run_policies("dev", "train", False)
    summary = {s: {p: _summ(rows) for p, rows in per.items()} for s, per in result.items()}
    json.dump({"env_version": ENV_VERSION, "summary": summary, "per_episode": result}, open(P("reports", "baselines.json"), "w"), indent=1)
    print(markdown_table(summary))


def markdown_table(summary):
    lines = []
    for split, per in summary.items():
        lines += [f"\n**{split}**\n", "| policy | TP | FP | FN | P (pooled) | R (pooled) | mean F1 | mean return | steps | s/episode |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for p, s in per.items():
            lines.append(f"| {p} | {s['tp']} | {s['fp']} | {s['fn']} | {_fmt(s['precision'])} | {_fmt(s['recall'])} | {s['f1']:.3f} | "
                         f"{s['return']:.3f} | {s['inspection_steps']:.1f} | {s['wall_s']:.2f} |")
    lines.append("\nP and R are pooled over all episodes of the split; mean F1 and mean return are averaged per episode "
                 "(a clean episode answered with no findings has F1 = 1). '—' = nothing flagged, precision undefined.")
    return "\n".join(lines)


def _fmt(x):
    return "—" if x is None else f"{x:.3f}"


def cmd_explain(args):
    ep = generate_episode(args.seed, json.loads(args.config) if args.config else None)
    print(explain(ep))


def cmd_fuzz(args):
    r = fuzz.run_all()
    json.dump(r, open(P("reports", "fuzz_report.json"), "w"), indent=1)
    print(json.dumps(r, indent=1))


def cmd_mutation(args):
    r = run_mutation_suite()
    json.dump(r, open(P("reports", "mutation_report.json"), "w"), indent=1)
    print(f"mutants killed {r['killed']}/{r['mutants']}  survivors={r['survivors']}")
    return r


def cmd_analysis(args):
    """Measured failure analysis: per-type errors of the naive reconciler + distractor ablation."""
    NO_DIS = {"installments": 0, "refunds": 0, "multi_invoice": 0, "recurring": 0, "same_amount_near": 0,
              "boundary_invoices": 0, "boundary_cross_ok": 0, "cross_ccy_ok": 0, "advances": 0, "split_po": 0, "late_postings": 0,
              "early_postings": 0, "on_account": 0}
    NOFAULT = {k: 0 for k in ("duplicate_invoice", "payment_allocation", "fx_error", "period_cutoff")}
    seeds = list(range(9301, 9316))
    variants = {"naive": dict(), "+tz_aware": dict(tz_aware=True), "+tz_aware+allocated_amount": dict(tz_aware=True, use_allocated=True)}

    def f1s(cfg_fn, kw):
        return [run_episode(SimpleReconciler(**kw), s, cfg_fn(s))["evaluation"] for s in seeds]

    md = ["# Failure analysis (measured: `python -m auditforge.cli analysis`)", "",
          f"Policy: `simple_reconciler` (same-entity+total duplicates, string-date cutoff, total-amount FX check). {len(seeds)} episodes per cell, mean F1.", "",
          "| reconciler variant | with distractors | distractors removed |", "|---|---|---|"]
    by = {}
    for name, kw in variants.items():
        a = f1s(lambda s: {}, kw)
        b = f1s(lambda s: {"distractors": NO_DIS}, kw)
        by[name] = a
        md.append(f"| {name} | {statistics.mean(r['f1'] for r in a):.3f} | {statistics.mean(r['f1'] for r in b):.3f} |")
    md += ["", "Per-type counts of the naive variant (sum over episodes, distractors on):", "", "| type | TP | FP | FN |", "|---|---|---|---|"]
    for t in ("duplicate_invoice", "payment_allocation", "fx_error", "period_cutoff"):
        c = {k: sum(r["by_type"][t][k] for r in by["naive"]) for k in ("tp", "fp", "fn")}
        md.append(f"| {t} | {c['tp']} | {c['fp']} | {c['fn']} |")
    clean = [run_episode(SimpleReconciler(), 9400 + i, {"faults": NOFAULT})["evaluation"] for i in range(10)]
    inter_cfg = lambda s: {"faults": NOFAULT, "interactions": ["partial_fx", "cutoff_fx"]}
    inter = {n: [run_episode(SimpleReconciler(**kw), 9500 + i, inter_cfg(0))["evaluation"] for i in range(10)] for n, kw in variants.items()}
    md += ["", f"Clean companies (10 episodes, 0 errors), naive: **{sum(r['fp'] for r in clean)} false accusations**, mean return "
           f"{statistics.mean(r['reward'] for r in clean):.3f} (silence scores about 0.96).", "",
           "Interacting-only episodes (10 episodes, partial_fx + cutoff_fx), mean F1: " +
           ", ".join(f"{n} **{statistics.mean(r['f1'] for r in v):.3f}**" for n, v in inter.items()) + ".", "",
           "How to read it: each ablation row removes one naive shortcut and the F1 gain is the measured cost of that shortcut. "
           "`reference_solver` (same tool API, exact policy) reaches F1 = 1.0 on every episode (see `reports/hidden_like_eval.json`), "
           "so the remaining gap is analytical difficulty, not unsolvable data."]
    # shortcut rules that skip the accounting logic, measured on all train + dev + hidden_like episodes
    eps = [generate_episode(e["seed"], e["config"]) for sp in ("train", "dev", "hidden_like") for e in load_split(sp)["episodes"]]
    md += ["", f"## Shortcut rules (tricks) vs the truth ({len(eps)} episodes: train + dev + hidden_like)", "",
           "Each rule reads public tables only and skips the real logic (period of document vs posting, line items, memo). "
           "Legit distractors make every one of them pay with false accusations.", "",
           "| error type | shortcut rule | TP | FP (false accusations) | FN |", "|---|---|---|---|---|"]
    for r in tricks.measure(eps):
        md.append(f"| {r['type']} | {r['rule']} | {r['tp']} | {r['fp']} | {r['fn']} |")
    open(P("reports", "failure_analysis.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md))


def _pct(d):
    return sum(1 for v in d.values() if v is True), len(d)


def cmd_verify(args):
    t0 = time.time()
    os.makedirs(P("reports"), exist_ok=True)
    sc, fails = {}, []

    def section(name, checks, weight):
        res = selfchecks.run_checks(checks)
        ok, n = _pct(res)
        sc[name] = {"passed": ok, "total": n, "points": round(weight * ok / n, 2), "max": weight}
        fails.extend(f"{name}: {k}: {v}" for k, v in res.items() if v is not True)
        print(f"[{name}] {ok}/{n}")

    section("contract_and_isolation", selfchecks.contract_checks(), 25)
    # data & truth: certify generated episodes (hidden-like + train + dev), independent of the disk copies
    eps = []
    for split in ("hidden_like", "train", "dev"):
        eps += [generate_episode(e["seed"], e["config"]) for e in load_split(split)["episodes"]]
    certs = [certify(e) for e in eps]
    ok = sum(c["passed"] for c in certs)
    sc["data_and_truth"] = {"passed": ok, "total": len(certs), "points": round(25 * ok / len(certs), 2), "max": 25}
    for c in certs:
        fails.extend(f"data: {c['episode_id']}: {x['name']} {x['detail']}" for x in c["checks"] if not x["passed"])
    print(f"[data_and_truth] {ok}/{len(certs)} episodes certified")
    rc = selfchecks.reward_checks()
    res = selfchecks.run_checks(rc)
    mut = cmd_mutation(None)
    fz = fuzz.run_all(quick=True)
    json.dump(fz, open(P("reports", "fuzz_report.json"), "w"), indent=1)
    print(f"[reward fuzzer] {fz['soundness']['submissions']} random submissions, unsound awards: {fz['soundness']['n_violations']}; "
          f"blind best reward {fz['blind_search']['max_best_reward']:+.2f}; seed regeneration: without secret "
          f"{fz['regeneration']['recovered_without_secret']}, with secret {fz['regeneration']['recovered_with_secret']}")
    if not fz["passed"]:
        fails.append("reward fuzzer failed")
    ok_r, n_r = _pct(res)
    total_r = n_r + 2
    ok_total = ok_r + (1 if not mut["survivors"] else 0) + (1 if fz["passed"] else 0)
    sc["reward_reliability"] = {"passed": ok_total, "total": total_r, "points": round(25 * ok_total / total_r, 2), "max": 25,
                                "mutation_score": mut["mutation_score"]}
    fails.extend(f"reward: {k}: {v}" for k, v in res.items() if v is not True)
    if mut["survivors"]:
        fails.append(f"mutation survivors: {mut['survivors']}")
    print(f"[reward_reliability] checks {ok_r}/{n_r}, mutants killed {mut['killed']}/{mut['mutants']}")
    pc = {**selfchecks.paired_checks(), **selfchecks.repeat_checks()}
    section("reproducibility_and_generalisation", pc, 15)
    # hidden-like evaluation: isolated evaluator process, eval mode, all policies
    per = run_policies("hidden_like", "eval", True)
    summ = {p: _summ(rows) for p, rows in per.items()}
    json.dump({"summary": summ, "per_episode": per}, open(P("reports", "hidden_like_eval.json"), "w"), indent=1)
    print("[hidden_like eval, isolated process, 20 episodes]")
    print(markdown_table({"hidden_like": summ}))
    expect = [("oracle return == 1", all(r["reward"] == 1.0 for r in per["oracle"])),
              ("reference_solver F1 == 1", all(r["f1"] == 1.0 for r in per["reference_solver"])),
              ("flag_all mean return < -0.5", summ["flag_all"]["return"] < -0.5),
              ("simple_reconciler worse than reference", summ["simple_reconciler"]["f1"] < summ["reference_solver"]["f1"] - 0.2),
              ("random_explorer F1 < 0.3", summ["random_explorer"]["f1"] < 0.3),
              ("zero_agent: +1 on clean, -1 otherwise", all(r["reward"] == (1.0 if r["n_issues"] == 0 else -1.0) for r in per["zero_agent"]))]
    for n, v in expect:
        print(f"  {'ok ' if v else 'FAIL'} {n}")
        if not v:
            fails.append("baseline expectation: " + n)
    eng = {
        "one_command_run": os.path.exists(P("Makefile")) and "verify" in open(P("Makefile")).read(),
        "versioned_configs": all("config_version" in load_split(s) for s in ("train", "dev", "hidden_like")),
        "trajectory_logs": os.path.exists(P("trajectories.jsonl")),
        "measured_failure_analysis": os.path.exists(P("reports", "failure_analysis.md")),
        "honest_limitations": "## Limitations" in open(P("README.md")).read() if os.path.exists(P("README.md")) else False,
    }
    sc["engineering"] = {"passed": sum(eng.values()), "total": 5, "points": 2 * sum(eng.values()), "max": 10, "detail": eng}
    print(f"[engineering] {eng}")
    fails.extend(f"engineering: {k}" for k, v in eng.items() if not v)
    total = sum(v["points"] for v in sc.values())
    sc_out = {"env_version": ENV_VERSION, "scorecard": sc, "self_assessed_total": round(total, 1), "failures": fails,
              "seconds": round(time.time() - t0, 1)}
    json.dump(sc_out, open(P("reports", "scorecard.json"), "w"), indent=1)
    print("\nSCORECARD (self-assessed; mirrors the published rubric)")
    for k, v in sc.items():
        print(f"  {k:38s} {v['points']:6.2f} / {v['max']}")
    print(f"  {'TOTAL':38s} {total:6.2f} / 100   ({sc_out['seconds']} s)")
    if fails:
        print("\nFAILURES:"); [print("  -", f) for f in fails]
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(prog="auditforge")
    ap.add_argument("cmd", choices=["gen", "baselines", "mutation", "analysis", "verify", "explain", "fuzz"])
    ap.add_argument("--seed", type=int, default=4242, help="explain: episode seed")
    ap.add_argument("--config", default=None, help='explain: JSON config, e.g. \'{"interactions":["partial_fx"]}\'')
    args = ap.parse_args()
    {"gen": cmd_gen, "baselines": cmd_baselines, "mutation": cmd_mutation, "analysis": cmd_analysis, "verify": cmd_verify,
     "explain": cmd_explain, "fuzz": cmd_fuzz}[args.cmd](args)


if __name__ == "__main__":
    main()
