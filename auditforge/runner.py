"""Drive a policy against an env; optionally write trajectories.jsonl lines."""
from __future__ import annotations

import json
import time

from .env import AuditEnv
from .generator import generate_episode


def run_episode(policy, seed: int, config: dict | None = None, mode: str = "train", env=None,
                traj=None, episode=None) -> dict:
    """`traj` is an open text file. Returns {'evaluation', 'wall_s', ...}. `env` may be AuditEnv or RemoteEnv."""
    env = env or AuditEnv(mode=mode)
    t0 = time.perf_counter()
    if episode is not None and isinstance(env, AuditEnv):
        obs, info = env.reset(episode=episode)
    else:
        obs, info = env.reset(seed, config)
    eid = info["episode_id"]

    def log(step, action, o, r, te, tr):
        if traj is not None:
            traj.write(json.dumps({"episode_id": eid, "step": step, "action": action, "observation": o, "reward": r,
                                   "terminated": te, "truncated": tr, "policy": policy.name}) + "\n")
    log(0, None, obs, 0.0, False, False)
    gen = policy.run(obs, info)
    step, done = 0, False
    try:
        action = next(gen)
        while True:
            step += 1
            o, r, te, tr, _ = env.step(action)
            log(step, action, o, r, te, tr)
            if te or tr:
                done = True
                break
            action = gen.send(o)
    except StopIteration:
        pass
    if not done:  # policy ended without submitting -> run to truncation is wasteful; submit empty
        step += 1
        o, r, te, tr, _ = env.step({"action": "submit", "findings": {"episode_id": eid, "findings": []}})
        log(step, {"action": "submit", "findings": {"episode_id": eid, "findings": []}}, o, r, te, tr)
    return {"policy": policy.name, "episode_id": eid, "wall_s": time.perf_counter() - t0, "evaluation": env.evaluation()}
