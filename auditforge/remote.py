"""RemoteEnv: same reset/step API as AuditEnv, but the evaluator runs in a separate process."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile


class RemoteEnv:
    """mode and limits go on the evaluator's command line: the agent side cannot change them over the pipe.
    The secret (argument, AUDITFORGE_SECRET_FILE or AUDITFORGE_SECRET of the harness) reaches the evaluator as a
    0600 temp file that is deleted once the evaluator has started; it is never put in the child's environment.
    In eval mode without any secret the evaluator makes a random one itself."""

    def __init__(self, mode: str = "train", limits: dict | None = None, secret: str | None = None):
        if mode not in ("train", "eval"):
            raise ValueError("mode must be 'train' or 'eval'")
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        child_env = {k: v for k, v in os.environ.items() if not k.startswith("AUDITFORGE_SECRET")}
        child_env["PYTHONPATH"] = root
        limits = limits or {}
        cmd = [sys.executable, "-m", "auditforge.server", "--mode", mode]
        if "max_steps" in limits:
            cmd += ["--max-steps", str(int(limits["max_steps"]))]
        if "time_limit_s" in limits:
            cmd += ["--time-limit", str(float(limits["time_limit_s"]))]
        if secret is None:
            sf = os.environ.get("AUDITFORGE_SECRET_FILE")
            if sf and os.path.exists(sf):
                secret = open(sf).read().strip() or None
            else:
                secret = os.environ.get("AUDITFORGE_SECRET") or None
        tmp = None
        if secret:
            fd, tmp = tempfile.mkstemp(prefix="af-secret-")
            with os.fdopen(fd, "w") as f:
                f.write(secret)
            cmd += ["--secret-file", tmp]
        self._p = subprocess.Popen(cmd, cwd=root, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, text=True, bufsize=1, env=child_env)
        self.mode, self.limits = mode, limits
        if tmp:   # a no-op round trip proves the evaluator has read the file; then remove it
            try:
                self._call({"op": "ping"}, allow_fatal=True)
            finally:
                os.unlink(tmp)

    def _call(self, msg: dict, allow_fatal: bool = False) -> dict:
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
        if "fatal" in out and not allow_fatal:
            raise RuntimeError(out["fatal"])
        return out

    def reset(self, seed: int, config: dict | None = None):
        o = self._call({"op": "reset", "seed": seed, "config": config})
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
