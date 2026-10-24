import shutil
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from tinker_cookbook import model_info, tokenizer_utils
from tinker_cookbook.renderers import get_renderer
from tinker_cookbook.rl.types import Env, EnvGroupBuilder
from tinker_cookbook.tool_use import build_agent_tool_env

from elt_rl.prompt import SYSTEM_PROMPT, build_task_prompt
from elt_rl.reward import ELTReward
from elt_rl.sandbox.local import LocalSandbox
from elt_rl.tools import ELTTools
from elt_rl.workspace import build_workspace


def initial_messages(renderer, tools: ELTTools) -> list:
    dbt = str(Path(sys.executable).parent / "dbt")
    prefix = renderer.create_conversation_prefix_with_tools(
        tools=[
            tools.bash.to_spec(),
            tools.read_file.to_spec(),
            tools.write_file.to_spec(),
            tools.submit.to_spec(),
        ],
        system_prompt=SYSTEM_PROMPT,
    )
    return prefix + [
        {"role": "user", "content": build_task_prompt(sys.executable, dbt)}
    ]


class ELTEnvGroupBuilder(EnvGroupBuilder):
    def __init__(
        self,
        task_name: str,
        model_name: str,
        renderer_name: str | None,
        max_turns: int,
        group_size: int,
        command_timeout: int = 120,
        max_trajectory_tokens: int = 32 * 1024,
        max_generation_tokens: int | None = None,
        context_overflow_reward: float = -0.1,
    ):
        self.task_name = task_name
        self.model_name = model_name
        self.renderer_name = renderer_name
        self.max_turns = max_turns
        self.group_size = group_size
        self.command_timeout = command_timeout
        self.max_trajectory_tokens = max_trajectory_tokens
        self.max_generation_tokens = max_generation_tokens
        self.context_overflow_reward = context_overflow_reward
        self._sandboxes: list[LocalSandbox] = []
        self._work_dirs: list[Path] = []

    async def make_envs(self) -> Sequence[Env]:
        from elt_rl.tasks import get_task

        task = get_task(self.task_name)
        self._sandboxes, self._work_dirs = [], []

        tokenizer = tokenizer_utils.get_tokenizer(self.model_name)
        renderer_name = self.renderer_name or model_info.get_recommended_renderer_name(
            self.model_name
        )
        renderer = get_renderer(renderer_name, tokenizer)

        envs = []
        for _ in range(self.group_size):
            work = Path(tempfile.mkdtemp(prefix="elt_env_"))
            db_path = work / "warehouse.duckdb"
            sandbox = LocalSandbox(root=work / "ws")
            build_workspace(task, sandbox.root, db_path)
            self._work_dirs.append(work)
            self._sandboxes.append(sandbox)

            tools = ELTTools(sandbox, command_timeout=self.command_timeout)
            envs.append(
                build_agent_tool_env(
                    renderer=renderer,
                    tools=[tools.bash, tools.read_file, tools.write_file, tools.submit],
                    initial_messages=initial_messages(renderer, tools),
                    reward_fn=ELTReward(task, db_path),
                    max_turns=self.max_turns,
                    max_trajectory_tokens=self.max_trajectory_tokens,
                    max_generation_tokens=self.max_generation_tokens,
                    context_overflow_reward=self.context_overflow_reward,
                )
            )
        return envs

    async def cleanup(self) -> None:
        for sandbox in self._sandboxes:
            try:
                await sandbox.cleanup()
            except Exception:
                pass
        for work in self._work_dirs:
            shutil.rmtree(work, ignore_errors=True)
        self._sandboxes.clear()
        self._work_dirs.clear()

    def logging_tags(self) -> list[str]:
        return ["elt", self.task_name]
