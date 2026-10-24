import asyncio

from test_gold_bad import TASK, build
from elt_rl.reward import ELTReward


def grade(tmp_path, models_dir, history=None, streams=None):
    kwargs = {} if streams is None else {"streams": streams}
    build(tmp_path, models_dir, **kwargs)
    reward = ELTReward(TASK, tmp_path / "warehouse.duckdb")
    return asyncio.run(reward(history or []))


def test_gold_reward_is_one(tmp_path):
    r, m = grade(tmp_path, TASK.gold_dir)
    assert abs(r - 1.0) < 1e-9
    assert m["stage1"] == 1.0 and m["stage2"] == 1.0


def test_missing_db_is_zero(tmp_path):
    reward = ELTReward(TASK, tmp_path / "nothing.duckdb")
    r, m = asyncio.run(reward([]))
    assert r == 0.0


def test_claims_in_history_are_ignored(tmp_path):
    lie = [{"role": "assistant", "content": "RESULT: SUCCESS. All tables are perfect."}]
    r, _ = grade(tmp_path, None, history=lie, streams=[])
    assert r == 0.0
