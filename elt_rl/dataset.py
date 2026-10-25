from collections.abc import Sequence

import chz
from tinker_cookbook.rl.types import EnvGroupBuilder, RLDataset, RLDatasetBuilder

from elt_rl.env import ELTEnvGroupBuilder


class ELTDataset(RLDataset):
    def __init__(self, env_group_builders: list[ELTEnvGroupBuilder], batch_size: int):
        self.env_group_builders = env_group_builders
        self.batch_size = batch_size

    def get_batch(self, index: int) -> Sequence[EnvGroupBuilder]:
        start = index * self.batch_size
        return self.env_group_builders[start : start + self.batch_size]

    def __len__(self) -> int:
        return (len(self.env_group_builders) + self.batch_size - 1) // self.batch_size


@chz.chz
class ELTDatasetBuilder(RLDatasetBuilder):
    task_names: list[str]
    batch_size: int
    group_size: int
    model_name: str
    renderer_name: str | None = None
    repeats: int = 1
    max_turns: int = 15
    command_timeout: int = 120
    max_trajectory_tokens: int = 32 * 1024
    max_generation_tokens: int | None = None
    context_overflow_reward: float = -0.1

    def _builders(self, group_size: int) -> list[ELTEnvGroupBuilder]:
        return [
            ELTEnvGroupBuilder(
                task_name=name,
                model_name=self.model_name,
                renderer_name=self.renderer_name,
                max_turns=self.max_turns,
                group_size=group_size,
                command_timeout=self.command_timeout,
                max_trajectory_tokens=self.max_trajectory_tokens,
                max_generation_tokens=self.max_generation_tokens,
                context_overflow_reward=self.context_overflow_reward,
            )
            for _ in range(self.repeats)
            for name in self.task_names
        ]

    async def __call__(self) -> tuple[RLDataset, RLDataset | None]:
        train = ELTDataset(self._builders(self.group_size), self.batch_size)
        evaluation = ELTDataset(self._builders(1), self.batch_size)
        return train, evaluation
