"""AuditEnv: Gymnasium-style JSON contract (reset/step), no gym dependency.

Isolation model
  * the evaluator (truth, provenance, grader) lives inside this object; in the isolated deployment
    (`remote.RemoteEnv`) it runs in a separate OS process and the agent only sees JSON lines;
  * observations contain ONLY requested records / result / bounded error / steps_remaining;
  * error messages are fixed strings (never echo evaluator state);
  * mode="train": terminal reward is returned to the policy;
    mode="eval" : reward is 0.0 and info has no diagnostics; the harness reads env.evaluation() afterwards.
"""
from __future__ import annotations

import copy
import re
import time
from typing import Any, Callable

from . import ENV_VERSION, SCHEMA_VERSION
from .calc import CalcError, evaluate
from .generator import Episode, generate_episode, policy_summary
from .grader import InvalidSubmission, grade, invalid_result, validate_submission
from .checks import fx_record_id

MAX_STEPS = 100
PAGE_MAX = 50
TIME_LIMIT_S = 60.0
TABLES = ("ledger", "invoices", "payments", "fx")
ACTIONS = ("list_records", "get_record", "get_document", "calculator", "submit")

TASK_TEXT = ("You are auditing one fictional company for one reporting period. The books may contain hidden "
             "errors of four kinds: duplicate_invoice, payment_allocation, fx_error, period_cutoff. Inspect records with "
             "list_records / get_record / get_document / calculator, then call submit once with findings "
             "{episode_id, findings:[{type, affected_ids, claimed_amount_minor, currency, evidence_ids, explanation}]}. "
             "Report only errors you can prove from records; ids you cite as evidence must exist. Each inspection step costs a little.")

ERRORS = {
    "unknown_action": "unknown action", "invalid_argument": "invalid argument", "unknown_table": "unknown table",
    "unknown_id": "unknown id", "invalid_cursor": "invalid cursor", "calc_error": "calculator rejected the expression",
    "episode_finished": "episode already finished", "invalid_submission": "submission rejected: invalid structure",
    "time_limit": "time limit exceeded", "not_reset": "call reset first",
}


class AuditEnv:
    def __init__(self, mode: str = "train", max_steps: int = MAX_STEPS, time_limit_s: float = TIME_LIMIT_S,
                 clock: Callable[[], float] = time.monotonic, secret: str | None = None):
        """secret: evaluator-only string mixed into every generated episode. Without it the generator is public, so
        anyone who knows seed range + config can regenerate an episode and read its truth (measured: ~13 s for 2000
        seeds). RemoteEnv in eval mode always runs with one (organisers' file, or random inside the evaluator)."""
        if mode not in ("train", "eval"):
            raise ValueError("mode must be 'train' or 'eval'")
        self._secret = secret
        self.mode, self.max_steps, self.time_limit_s, self._clock = mode, max_steps, time_limit_s, clock
        self._ep: Episode | None = None
        self._done = False

    # ------------------------------------------------------------------ lifecycle
    def reset(self, seed: int | None = None, config: dict | None = None, episode: Episode | None = None):
        if episode is None:
            if not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed < 2 ** 63:
                raise ValueError("seed must be an int in [0, 2**63)")
            cfg = dict(config or {})
            if self._secret:
                cfg["id_salt"] = f"{self._secret}|{cfg.get('id_salt', '')}"
            episode = generate_episode(int(seed), cfg)
        ep = episode
        self._ep = ep
        self._steps, self._done, self._truncated, self._result, self._reason = 0, False, False, None, None
        self._t0 = self._clock()
        t = ep.tables
        self._idx = {
            "ledger": {r["row_id"]: r for r in t["ledger"]},
            "invoices": {r["invoice_id"]: r for r in t["invoices"]},
            "payments": {r["payment_id"]: r for r in t["payments"]},
            "fx": {fx_record_id(r): r for r in t["fx"]},
        }
        self._docs = {r["doc_id"]: r for r in t["invoices"] + t["payments"]}
        self._known_ids = frozenset(self._idx["ledger"]) | frozenset(self._docs) | frozenset(self._idx["fx"])
        obs = {"task": TASK_TEXT, "manifest": copy.deepcopy(ep.manifest), "policy_summary": policy_summary(ep.policy),
               "steps_remaining": self.max_steps}
        info = {"episode_id": ep.episode_id, "env_version": ENV_VERSION, "schema_version": SCHEMA_VERSION, "mode": self.mode}
        return obs, info

    # ------------------------------------------------------------------ step
    def step(self, action: Any):
        if self._ep is None:
            return self._obs(error="not_reset"), 0.0, True, False, {}
        if self._done:
            return self._obs(error="episode_finished"), 0.0, True, self._truncated, {"step": self._steps}
        self._steps += 1
        if self._clock() - self._t0 > self.time_limit_s:
            return self._finish(truncated=True, reason="truncated_time", obs=self._obs(error="time_limit"))
        res = self._dispatch(action)
        if res.get("terminal"):
            return res["terminal"]
        obs = self._obs(**{k: v for k, v in res.items() if k in ("result", "error")})
        if self._steps >= self.max_steps:
            return self._finish(truncated=True, reason="truncated_steps", obs=obs)
        return obs, 0.0, False, False, {"step": self._steps}

    # ------------------------------------------------------------------ internals
    def _obs(self, result: Any = None, error: str | None = None) -> dict:
        o: dict = {"steps_remaining": max(0, self.max_steps - self._steps)}
        if error is not None:
            o["ok"], o["error"] = False, {"code": error, "message": ERRORS[error]}
        else:
            o["ok"], o["result"] = True, copy.deepcopy(result)
        return o

    def _err(self, code: str) -> dict:
        return {"error": code}

    def _dispatch(self, a: Any) -> dict:
        if not isinstance(a, dict) or not isinstance(a.get("action"), str):
            return self._err("invalid_argument")
        name = a["action"]
        if name not in ACTIONS:
            return self._err("unknown_action")
        if name == "list_records":
            return self._list(a)
        if name == "get_record":
            return self._get(a)
        if name == "get_document":
            d = a.get("doc_id")
            if not isinstance(d, str):
                return self._err("invalid_argument")
            return {"result": self._docs[d]} if d in self._docs else self._err("unknown_id")
        if name == "calculator":
            try:
                return {"result": {"value": evaluate(a.get("expression"))}}
            except CalcError:
                return self._err("calc_error")
        return self._submit(a)

    def _list(self, a: dict) -> dict:
        table, cursor, limit = a.get("table"), a.get("cursor"), a.get("limit")
        if limit is None:
            limit = PAGE_MAX
        if table not in TABLES:
            return self._err("unknown_table" if isinstance(table, str) else "invalid_argument")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            return self._err("invalid_argument")
        limit = min(limit, PAGE_MAX)
        off = 0
        if cursor is not None:
            # ASCII digits only, bounded length: str.isdigit() accepts Unicode digits and int() caps at 4300 digits
            if not (isinstance(cursor, str) and re.fullmatch(r"c[0-9]{1,9}", cursor)):
                return self._err("invalid_cursor")
            off = int(cursor[1:])
        rows = self._ep.tables[table]
        if off > len(rows):
            return self._err("invalid_cursor")
        page = rows[off:off + limit]
        nxt = f"c{off + len(page)}" if off + len(page) < len(rows) else None
        return {"result": {"table": table, "records": page, "next_cursor": nxt, "total": len(rows)}}

    def _get(self, a: dict) -> dict:
        table, rid = a.get("table"), a.get("id")
        if not isinstance(table, str) or not isinstance(rid, str):
            return self._err("invalid_argument")
        if table == "policy":
            return {"result": self._ep.policy} if rid == "policy" else self._err("unknown_id")
        if table == "manifest":
            return {"result": self._ep.manifest} if rid == "manifest" else self._err("unknown_id")
        if table not in TABLES:
            return self._err("unknown_table")
        rec = self._idx[table].get(rid)
        return {"result": rec} if rec is not None else self._err("unknown_id")

    def _submit(self, a: dict) -> dict:
        inspection = self._steps - 1
        try:
            findings = validate_submission(a.get("findings"), self._ep.episode_id)
            self._result = grade(findings, self._ep.truth["issues"], self._ep.policy["amount_tolerance_minor"], inspection,
                                 self._known_ids)
            reason, obs = "submitted", self._obs(result={"status": "submitted"})
        except InvalidSubmission as e:
            self._result = invalid_result(e.code, inspection)
            reason, obs = "invalid_submission", self._obs(error="invalid_submission")
        return {"terminal": self._finish(truncated=False, reason=reason, obs=obs, graded=True)}

    def _finish(self, truncated: bool, reason: str, obs: dict, graded: bool = False):
        if not graded:  # truncation: empty final answer is graded
            self._result = grade([], self._ep.truth["issues"], self._ep.policy["amount_tolerance_minor"], self._steps, self._known_ids)
        self._done, self._truncated, self._reason = True, truncated, reason
        reward, info = 0.0, {"step": self._steps}
        if self.mode == "train":
            reward = float(self._result["reward"])
            info["terminal"] = {k: self._result[k] for k in ("tp", "fp", "fn", "precision", "recall", "f1", "inspection_steps")}
            info["terminal"]["reason"] = reason
        return obs, reward, (not truncated), truncated, info

    # ------------------------------------------------------------------ evaluator-only API (harness, never the policy)
    def evaluation(self) -> dict:
        if not self._done:
            raise RuntimeError("evaluation is available only after the episode ended")
        return {"episode_id": self._ep.episode_id, "reason": self._reason, "steps": self._steps, **copy.deepcopy(self._result)}
