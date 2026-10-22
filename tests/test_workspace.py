from pathlib import Path

import yaml

from elt_rl.tasks.synthetic_shop import load_task
from elt_rl.workspace import build_workspace

TASK = load_task()


def make(tmp_path: Path):
    root = tmp_path / "ws"
    build_workspace(TASK, root, tmp_path / "warehouse.duckdb")
    return root


def test_files_exist(tmp_path):
    root = make(tmp_path)
    assert (root / "config.yaml").is_file()
    assert (root / "data_model.yaml").is_file()
    assert (root / "schemas" / "customers.csv").is_file()
    assert (root / "elt").is_dir()


def test_config_contents(tmp_path):
    root = make(tmp_path)
    cfg = yaml.safe_load((root / "config.yaml").read_text())
    assert cfg["destination"]["schema"] == "synthetic_shop"
    assert cfg["streams_available"] == ["customers", "orders", "refunds"]


def test_no_ground_truth_leak(tmp_path):
    root = make(tmp_path)
    gt_dir = str(Path(TASK.gt_dir).resolve())
    gt_values = ["125.5", "Chen,2"]
    for f in root.rglob("*"):
        if f.is_file():
            text = f.read_text()
            assert gt_dir not in text, f
            for v in gt_values:
                assert v not in text, (f, v)
