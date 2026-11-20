"""Evaluator-side process: owns the episode (truth, grader). Speaks JSON lines over stdio.
The policy process never imports this module and never sees truth/provenance/seed.

Hardening:
- mode and limits are fixed by whoever STARTS the process (command line), never by messages on the pipe;
  a reset that carries "mode" or "limits" is rejected (v1.2).
- eval mode: exactly one episode per process, and an episode secret is always in force (v1.2).
- the secret arrives as the FIRST stdin line, before any agent message: no temp file, nothing in
  /proc/<pid>/cmdline or /proc/<pid>/environ (v1.3). Empty -> eval makes a random one, train runs without.
- the final evaluation goes to a separate harness channel (--harness-fd) when the episode ends; in eval mode
  `evaluation` on the agent channel is refused (v1.3).
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import secrets
import sys

from .env import MAX_STEPS, TIME_LIMIT_S, AuditEnv

FORBIDDEN_RESET_FIELDS = ("mode", "limits")


def _args(argv=None):
    ap = argparse.ArgumentParser(prog="auditforge.server")
    ap.add_argument("--mode", choices=("train", "eval"), default="train")
    ap.add_argument("--max-steps", type=int, default=MAX_STEPS)
    ap.add_argument("--time-limit", type=float, default=TIME_LIMIT_S)
    ap.add_argument("--harness-fd", type=int, default=None)
    return ap.parse_args(argv)


def read_secret(mode: str, first_line: str) -> tuple[str | None, str, bool]:
    """-> (secret, source, consumed). The harness handshake is a line {"secret": "..."}; any other first line is
    an ordinary message (consumed=False) and the process runs without a harness secret."""
    try:
        m = json.loads(first_line)
    except ValueError:
        m = None
    consumed = isinstance(m, dict) and set(m) == {"secret"}
    s = m["secret"] if consumed and isinstance(m["secret"], str) else ""
    s = s.strip()
    if s:
        return s, "harness", consumed
    if mode == "eval":
        return secrets.token_hex(16), "ephemeral", consumed
    return None, "none", consumed


def main(argv=None) -> None:
    a = _args(argv)
    first = sys.stdin.readline()
    secret, secret_source, consumed = read_secret(a.mode, first)
    lines = sys.stdin if consumed or not first else itertools.chain([first], sys.stdin)
    harness = os.fdopen(a.harness_fd, "w") if a.harness_fd is not None else None
    env: AuditEnv | None = None
    resets = 0
    reported = False

    def report():
        nonlocal reported
        if harness is not None and not reported:
            harness.write(json.dumps({**env.evaluation(), "secret_source": secret_source}) + "\n")
            harness.flush()
            reported = True

    for line in lines:
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
                    try:
                        obs, info = env.reset(msg["seed"], msg.get("config"))
                    except (ValueError, TypeError, KeyError):
                        env = None
                        out = {"fatal": "bad_config"}
                    else:
                        resets += 1
                        reported = False
                        out = {"obs": obs, "info": info}
            elif op == "step":
                if env is None:
                    out = {"fatal": "no_episode"}
                else:
                    obs, r, term, trunc, info = env.step(msg.get("action"))
                    out = {"obs": obs, "reward": r, "terminated": term, "truncated": trunc, "info": info}
                    if term or trunc:
                        report()
            elif op == "evaluation":
                if a.mode == "eval":
                    out = {"fatal": "harness_only"}
                elif env is None:
                    out = {"fatal": "no_episode"}
                else:
                    out = {"evaluation": {**env.evaluation(), "secret_source": secret_source}}
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
