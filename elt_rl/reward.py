import asyncio
from dataclasses import dataclass
from pathlib import Path

from elt_rl.grading import score_warehouse
from elt_rl.warehouse import DuckDBWarehouse


@dataclass
class ELTReward:
    task: object
    db_path: Path

    async def __call__(self, history) -> tuple[float, dict[str, float]]:
        try:
            result = await asyncio.to_thread(self._grade)
        except Exception:
            return 0.0, {
                "reward": 0.0,
                "stage1": 0.0,
                "stage2": 0.0,
                "grading_error": 1.0,
            }
        return result.reward, result.metrics()

    def _grade(self):
        wh = DuckDBWarehouse(self.db_path)
        try:
            return score_warehouse(
                wh,
                self.task.schema,
                self.task.expected_raw,
                self.task.gt_dir,
                self.task.sort_keys,
            )
        finally:
            wh.close()
