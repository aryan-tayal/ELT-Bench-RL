import json
from dataclasses import dataclass
from pathlib import Path

TASK_DIR = Path(__file__).parent


@dataclass(frozen=True)
class Task:
    name: str
    schema: str
    source_dir: Path
    gt_dir: Path
    gold_dir: Path
    bad_dir: Path
    expected_raw: dict
    sort_keys: dict


def load_task() -> Task:
    return Task(
        name="synthetic_shop",
        schema="synthetic_shop",
        source_dir=TASK_DIR / "sources",
        gt_dir=TASK_DIR / "ground_truth",
        gold_dir=TASK_DIR / "gold",
        bad_dir=TASK_DIR / "bad",
        expected_raw=json.loads((TASK_DIR / "table.json").read_text())[
            "synthetic_shop"
        ],
        sort_keys=json.loads((TASK_DIR / "sort_key.json").read_text())[
            "synthetic_shop"
        ],
    )
