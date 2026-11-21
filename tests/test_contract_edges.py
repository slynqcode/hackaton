import pytest

from auditforge.env import AuditEnv


def test_step_before_reset_returns_not_reset():
    obs, reward, terminated, truncated, info = AuditEnv().step({"action": "list_records", "table": "ledger"})
    assert obs["ok"] is False and obs["error"]["code"] == "not_reset"
    assert reward == 0.0 and terminated is True and truncated is False


@pytest.mark.parametrize("config", [
    {"faults": None}, {"faults": []}, {"distractors": 3}, {"interactions": None}, {"interactions": "partial_fx"},
    {"interactions": ["partial_fx", "partial_fx"]}, {"interactions": [1]}, {"company_offset_minutes": "x"},
    {"company_offset_minutes": True}, {"id_style": 99}, {"id_style": -1}, {"id_style": "0"}, {"id_salt": 5},
    {"period_months": True}, {"currencies": "USD"}, {"currencies": [1, 2]}, {"n_invoices": True},
])
def test_bad_config_types_raise_value_error(config):
    with pytest.raises(ValueError):
        AuditEnv().reset(seed=1, config=config)


def test_step_after_truncation_is_not_also_terminated():
    env = AuditEnv(max_steps=1)
    env.reset(seed=3)
    _, _, terminated, truncated, _ = env.step({"action": "calculator", "expression": "1+1"})
    assert truncated is True and terminated is False
    _, _, terminated, truncated, _ = env.step({"action": "calculator", "expression": "1+1"})
    assert truncated is True and terminated is False
