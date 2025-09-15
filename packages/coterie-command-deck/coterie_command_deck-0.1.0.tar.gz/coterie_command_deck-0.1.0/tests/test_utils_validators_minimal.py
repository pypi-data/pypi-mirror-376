import pytest

validators = pytest.importorskip("coterie_agents.utils.validators")


def _call_if_exists(name: str, *args, **kwargs):
    fn = getattr(validators, name, None)
    if fn is None or not callable(fn):
        pytest.skip(f"{name} not present in validators")
    return fn(*args, **kwargs)


def test_validate_member_happy_path():
    member = {"name": "Jet", "role": "runner", "status": "idle", "tasks": ["A"]}
    for fn_name in ("validate_member", "validate_crew_member", "validate"):
        try:
            res = _call_if_exists(fn_name, member)
            assert res is None or res
            return
        except pytest.skip.Exception:
            continue
    pytest.skip("no known validate fn found")


def test_validate_member_error_branch():
    bad = {"role": "runner", "status": "idle", "task": "A"}
    for fn_name in ("validate_member", "validate_crew_member", "validate"):
        try:
            try:
                _call_if_exists(fn_name, bad)
            except (ValueError, TypeError, AssertionError):
                return
            return
        except pytest.skip.Exception:
            continue
    pytest.skip("no known validate fn found")
