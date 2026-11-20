"""RemoteEnv: same reset/step API as AuditEnv, but the evaluator runs in a separate process.

Two channels (v1.3):
- agent channel (the child's stdin/stdout): reset / step only. In eval mode `evaluation` is refused on it.
- harness channel (a separate pipe, fd passed with pass_fds): the evaluator writes the final evaluation there
  when the episode ends. Only the object that started the evaluator holds its read end.

Secret (v1.3): sent as the FIRST line on the child's stdin, before any agent message. No temp file, nothing on
the command line or in the environment (/proc/<pid>/cmdline and /proc/<pid>/environ stay clean).
- eval: the `secret` argument, else AUDITFORGE_SECRET_FILE / AUDITFORGE_SECRET of the harness, else the
  evaluator makes a random one itself.
- train: only an explicit `secret` argument; the environment is ignored, so code running next to the harness
  cannot open a train-mode copy of a closed eval episode.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys


def _secret_from_env() -> str | None:
    sf = os.environ.get("AUDITFORGE_SECRET_FILE")
    if sf and os.path.exists(sf):
        with open(sf) as f:
            return f.read().strip() or None
    return os.environ.get("AUDITFORGE_SECRET") or None


class RemoteEnv:
    """mode and limits go on the evaluator's command line: the agent side cannot change them over the pipe."""

    def __init__(self, mode: str = "train", limits: dict | None = None, secret: str | None = None):
        if mode not in ("train", "eval"):
            raise ValueError("mode must be 'train' or 'eval'")
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        child_env = {k: v for k, v in os.environ.items() if not k.startswith("AUDITFORGE_SECRET")}
        child_env["PYTHONPATH"] = root
        limits = limits or {}
        if secret is None and mode == "eval":
            secret = _secret_from_env()
        self._h_read, h_write = os.pipe()
        cmd = [sys.executable, "-m", "auditforge.server", "--mode", mode, "--harness-fd", str(h_write)]
        if "max_steps" in limits:
            cmd += ["--max-steps", str(int(limits["max_steps"]))]
        if "time_limit_s" in limits:
            cmd += ["--time-limit", str(float(limits["time_limit_s"]))]
        self._p = subprocess.Popen(cmd, cwd=root, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, text=True, bufsize=1, env=child_env,
                                   pass_fds=(h_write,))
        os.close(h_write)
        self._harness = os.fdopen(self._h_read, "r")
        self.mode, self.limits = mode, limits
        self._done, self._eval = False, None
        # line 1 of the protocol: the secret (empty line = none given)
        self._p.stdin.write(json.dumps({"secret": secret or ""}) + "\n")
        self._p.stdin.flush()

    def _call(self, msg: dict, allow_fatal: bool = False) -> dict:
        try:
            self._p.stdin.write(json.dumps(msg) + "\n")
            self._p.stdin.flush()
            line = self._p.stdout.readline()
        except (BrokenPipeError, OSError, ValueError):
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
        self._done, self._eval = False, None
        return o["obs"], o["info"]

    def step(self, action):
        o = self._call({"op": "step", "action": action})
        if (o["terminated"] or o["truncated"]) and not self._done:
            self._done = True
            line = self._harness.readline()   # written by the evaluator before it answered on the agent channel
            self._eval = json.loads(line) if line else None
        return o["obs"], o["reward"], o["terminated"], o["truncated"], o["info"]

    def _discard_pipes(self):
        for f in (self._p.stdin, self._p.stdout):
            try:
                f.close()
            except Exception:
                pass

    def evaluation(self) -> dict:
        """Harness-only: read from the separate harness channel (written by the evaluator at episode end)."""
        if not self._done:
            raise RuntimeError("episode_not_finished")
        if self._eval is None:
            raise RuntimeError("evaluator_process_died")
        return dict(self._eval)

    def close(self):
        try:
            self._harness.close()
        except Exception:
            pass
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
