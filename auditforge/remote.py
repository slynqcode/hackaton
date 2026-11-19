"""RemoteEnv: same reset/step API as AuditEnv, but the evaluator runs in a separate process."""
from __future__ import annotations

import json
import os
import subprocess
import sys


class RemoteEnv:
    def __init__(self, mode: str = "train", limits: dict | None = None):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._p = subprocess.Popen([sys.executable, "-m", "auditforge.server"], cwd=root, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1,
                                   env={**os.environ, "PYTHONPATH": root})
        self.mode, self.limits = mode, limits or {}

    def _call(self, msg: dict) -> dict:
        self._p.stdin.write(json.dumps(msg) + "\n")
        self._p.stdin.flush()
        out = json.loads(self._p.stdout.readline())
        if "fatal" in out:
            raise RuntimeError(out["fatal"])
        return out

    def reset(self, seed: int, config: dict | None = None):
        o = self._call({"op": "reset", "seed": seed, "config": config, "mode": self.mode, "limits": self.limits})
        return o["obs"], o["info"]

    def step(self, action):
        o = self._call({"op": "step", "action": action})
        return o["obs"], o["reward"], o["terminated"], o["truncated"], o["info"]

    def evaluation(self) -> dict:
        return self._call({"op": "evaluation"})["evaluation"]

    def close(self):
        try:
            self._p.stdin.write(json.dumps({"op": "close"}) + "\n"); self._p.stdin.flush()
        except Exception:
            pass
        self._p.wait(timeout=5)
