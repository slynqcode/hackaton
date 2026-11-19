"""RemoteEnv: same reset/step API as AuditEnv, but the evaluator runs in a separate process."""
from __future__ import annotations

import json
import os
import subprocess
import sys


class RemoteEnv:
    def __init__(self, mode: str = "train", limits: dict | None = None, secret: str | None = None):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        child_env = {k: v for k, v in os.environ.items() if k != "AUDITFORGE_SECRET"}
        child_env["PYTHONPATH"] = root
        secret = secret if secret is not None else os.environ.get("AUDITFORGE_SECRET")
        if secret:
            child_env["AUDITFORGE_SECRET"] = secret
        self._p = subprocess.Popen([sys.executable, "-m", "auditforge.server"], cwd=root, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1,
                                   env=child_env)
        self.mode, self.limits = mode, limits or {}

    def _call(self, msg: dict) -> dict:
        try:
            self._p.stdin.write(json.dumps(msg) + "\n")
            self._p.stdin.flush()
            line = self._p.stdout.readline()
        except (BrokenPipeError, OSError):
            self._discard_pipes()
            raise RuntimeError("evaluator_process_died")
        if not line:
            self._discard_pipes()
            raise RuntimeError("evaluator_process_died")
        out = json.loads(line)
        if "fatal" in out:
            raise RuntimeError(out["fatal"])
        return out

    def reset(self, seed: int, config: dict | None = None):
        o = self._call({"op": "reset", "seed": seed, "config": config, "mode": self.mode, "limits": self.limits})
        return o["obs"], o["info"]

    def step(self, action):
        o = self._call({"op": "step", "action": action})
        return o["obs"], o["reward"], o["terminated"], o["truncated"], o["info"]

    def _discard_pipes(self):
        for f in (self._p.stdin, self._p.stdout):
            try:
                f.close()
            except Exception:
                pass

    def evaluation(self) -> dict:
        return self._call({"op": "evaluation"})["evaluation"]

    def close(self):
        if self._p.stdin.closed:
            return
        try:
            self._p.stdin.write(json.dumps({"op": "close"}) + "\n"); self._p.stdin.flush()
        except Exception:
            pass
        try:
            self._p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._p.kill()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
