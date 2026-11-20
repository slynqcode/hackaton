"""Evaluator-side process: owns the episode (truth, grader). Speaks JSON lines over stdio.
The policy process never imports this module and never sees truth/provenance/seed.

Hardening (v1.2):
- mode and limits are fixed by whoever STARTS the process (command line), never by messages on the pipe;
  a reset that carries "mode" or "limits" is rejected.
- eval mode: exactly one episode per process (no re-reset of the same seed to probe the reward), and an
  episode secret is always in force: the organisers' secret from --secret-file, otherwise a random one made
  inside this process. So eval episodes can never be regenerated from a public seed.
- the secret is never passed through environment variables (readable from /proc/<pid>/environ).
"""
from __future__ import annotations

import argparse
import json
import secrets
import sys

from .env import MAX_STEPS, TIME_LIMIT_S, AuditEnv

FORBIDDEN_RESET_FIELDS = ("mode", "limits")


def _args(argv=None):
    ap = argparse.ArgumentParser(prog="auditforge.server")
    ap.add_argument("--mode", choices=("train", "eval"), default="train")
    ap.add_argument("--max-steps", type=int, default=MAX_STEPS)
    ap.add_argument("--time-limit", type=float, default=TIME_LIMIT_S)
    ap.add_argument("--secret-file", default=None)
    return ap.parse_args(argv)


def load_secret(mode: str, secret_file: str | None) -> tuple[str | None, str]:
    if secret_file:
        with open(secret_file) as f:
            s = f.read().strip()
        if s:
            return s, "file"
    if mode == "eval":
        return secrets.token_hex(16), "ephemeral"
    return None, "none"


def main(argv=None) -> None:
    a = _args(argv)
    secret, secret_source = load_secret(a.mode, a.secret_file)
    env: AuditEnv | None = None
    resets = 0
    for line in sys.stdin:
        try:
            msg = json.loads(line)
            op = msg.get("op") if isinstance(msg, dict) else None
            if op == "reset":
                if any(k in msg for k in FORBIDDEN_RESET_FIELDS):
                    out = {"fatal": "forbidden_field"}
                elif a.mode == "eval" and resets >= 1:
                    out = {"fatal": "eval_single_episode"}
                elif not isinstance(msg.get("seed"), int) or isinstance(msg.get("seed"), bool):
                    out = {"fatal": "bad_seed"}
                else:
                    env = AuditEnv(mode=a.mode, secret=secret, max_steps=a.max_steps, time_limit_s=a.time_limit)
                    obs, info = env.reset(msg["seed"], msg.get("config"))
                    resets += 1
                    out = {"obs": obs, "info": info}
            elif op == "step":
                if env is None:
                    out = {"fatal": "no_episode"}
                else:
                    obs, r, term, trunc, info = env.step(msg.get("action"))
                    out = {"obs": obs, "reward": r, "terminated": term, "truncated": trunc, "info": info}
            elif op == "evaluation":
                out = {"evaluation": {**env.evaluation(), "secret_source": secret_source}} if env else {"fatal": "no_episode"}
            elif op == "ping":
                out = {"ok": True}
            elif op == "close":
                break
            else:
                out = {"fatal": "bad_op"}
        except Exception:  # never leak tracebacks to the agent side
            out = {"fatal": "internal_error"}
        sys.stdout.write(json.dumps(out) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
