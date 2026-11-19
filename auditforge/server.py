"""Evaluator-side process: owns the episode (truth, grader). Speaks JSON lines over stdio.
The policy process never imports this module and never sees truth/provenance/seed."""
from __future__ import annotations

import json
import os
import sys

from .env import AuditEnv


def main() -> None:
    env: AuditEnv | None = None
    for line in sys.stdin:
        try:
            msg = json.loads(line)
            op = msg.get("op")
            if op == "reset":
                # the secret comes from this process's environment only, never from the agent-facing channel
                env = AuditEnv(mode=msg.get("mode", "train"), secret=os.environ.get("AUDITFORGE_SECRET") or None,
                               **msg.get("limits", {}))
                obs, info = env.reset(msg["seed"], msg.get("config"))
                out = {"obs": obs, "info": info}
            elif op == "step":
                obs, r, term, trunc, info = env.step(msg.get("action"))
                out = {"obs": obs, "reward": r, "terminated": term, "truncated": trunc, "info": info}
            elif op == "evaluation":
                out = {"evaluation": env.evaluation()}
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
