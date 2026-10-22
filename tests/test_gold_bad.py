import shutil
from pathlib import Path

import pytest
import yaml

from elt_rl.dbt_utils import run_dbt, write_profile
from elt_rl.el.fake_airbyte import load_streams
from elt_rl.grading import score_warehouse
from elt_rl.tasks.synthetic_shop import load_task
from elt_rl.warehouse import DuckDBWarehouse

TASK = load_task()
ALL_STREAMS = [{"name": n, "sync_mode": "full_refresh_append"} for n in TASK.expected_raw]


def build(tmp_path: Path, models_dir: Path | None, streams=ALL_STREAMS, el_runs: int = 1):
    db = tmp_path / "warehouse.duckdb"
    for _ in range(el_runs):
        if streams:
            load_streams(TASK.source_dir, db, TASK.schema, streams)
    if models_dir is not None:
        project = tmp_path / "dbt"
        shutil.copytree(models_dir, project)
        write_profile(project, db, TASK.schema)
        result = run_dbt(project)
        assert result.returncode == 0, result.stdout + result.stderr
    return DuckDBWarehouse(db)


def grade(wh):
    return score_warehouse(wh, TASK.schema, TASK.expected_raw, TASK.gt_dir, TASK.sort_keys)


def test_gold_scores_one(tmp_path):
    r = grade(build(tmp_path, TASK.gold_dir))
    assert r.reward == pytest.approx(1.0), r.details


def test_bad_pipeline_scores_low(tmp_path):
    r = grade(build(tmp_path, TASK.bad_dir))
    assert r.stage1 == 1.0
    assert 0.2 < r.reward < 0.5, r.details


def test_no_pipeline_scores_zero(tmp_path):
    r = grade(build(tmp_path, None, streams=[]))
    assert r.reward == 0.0


def test_el_only_gets_stage1_credit(tmp_path):
    r = grade(build(tmp_path, None))
    assert r.reward == pytest.approx(0.2)


def test_double_sync_breaks_stage1(tmp_path):
    r = grade(build(tmp_path, TASK.gold_dir, el_runs=2))
    assert r.stage1 == 0.0  # append twice doubles row counts, like real Airbyte


def test_fake_tables_without_airbyte_metadata_fail_stage1(tmp_path):
    import duckdb
    db = tmp_path / "warehouse.duckdb"
    con = duckdb.connect(str(db))
    con.execute(f"create schema {TASK.schema}")
    for t, n in TASK.expected_raw.items():
        con.execute(f"create table {TASK.schema}.{t} as select range as x from range({n})")
    con.close()
    r = grade(DuckDBWarehouse(db))
    assert r.stage1 == 0.0