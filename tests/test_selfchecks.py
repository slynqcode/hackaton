"""The published fixed checks, one pytest case each (same code `make verify` scores)."""
import pytest

from auditforge import selfchecks as S

GROUPS = {"contract": S.contract_checks(), "reward": S.reward_checks(), "paired": S.paired_checks(), "repeat": S.repeat_checks()}
CASES = [(g, n) for g, d in GROUPS.items() for n in d]


@pytest.mark.parametrize("group,name", CASES, ids=[f"{g}::{n}" for g, n in CASES])
def test_selfcheck(group, name):
    GROUPS[group][name]()
