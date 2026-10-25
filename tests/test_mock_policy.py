import asyncio
import json
import sys
import tempfile
from pathlib import Path

from tinker_cookbook.renderers.base import ToolCall
from tinker_cookbook.tool_use.agent_tool_message_env import AgentToolMessageEnv

from elt_rl.reward import ELTReward
from elt_rl.sandbox.local import LocalSandbox
from elt_rl.tasks.synthetic_shop import load_task
from elt_rl.tools import ELTTools
from elt_rl.workspace import build_workspace

TASK = load_task()
SOURCES = "streams:\n" + "".join(
    f"  - name: {n}\n    sync_mode: full_refresh_append\n" for n in TASK.expected_raw
)


def call(name, **args):
    return ToolCall(
        id=f"call_{name}",
        function=ToolCall.FunctionBody(name=name, arguments=json.dumps(args)),
    )


def message(*calls):
    return {"role": "assistant", "content": "", "tool_calls": list(calls)}


def make_env(tmp: Path, max_turns: int = 20):
    db_path = tmp / "warehouse.duckdb"
    sandbox = LocalSandbox(root=tmp / "ws")
    build_workspace(TASK, sandbox.root, db_path)
    tools = ELTTools(sandbox)
    env = AgentToolMessageEnv(
        tools=[tools.bash, tools.read_file, tools.write_file, tools.submit],
        initial_messages=[{"role": "user", "content": "build the pipeline"}],
        max_turns=max_turns,
        reward_fn=ELTReward(TASK, db_path),
    )
    return env, db_path


def gold_turns(db_path: Path):
    profile = (
        f"elt:\n  target: dev\n  outputs:\n    dev:\n      type: duckdb\n"
        f'      path: "{db_path}"\n      schema: {TASK.schema}\n      threads: 1\n'
    )
    turns = [
        message(call("write_file", path="elt/sources.yaml", content=SOURCES)),
        message(
            call(
                "bash",
                command=(
                    f"{sys.executable} -m elt_rl.el.fake_airbyte "
                    "--config config.yaml --streams elt/sources.yaml"
                ),
            )
        ),
        message(call("write_file", path="elt/dbt/profiles.yml", content=profile)),
    ]
    for f in sorted(TASK.gold_dir.rglob("*")):
        if f.is_file():
            rel = f.relative_to(TASK.gold_dir)
            turns.append(
                message(
                    call("write_file", path=f"elt/dbt/{rel}", content=f.read_text())
                )
            )
    dbt = Path(sys.executable).parent / "dbt"
    turns.append(
        message(
            call(
                "bash",
                command=f"{dbt} run --project-dir elt/dbt --profiles-dir elt/dbt",
            )
        )
    )
    turns.append(message(call("submit")))
    return turns


def run_policy(turns, tmp):
    async def go():
        env, db_path = make_env(tmp)
        await env.initial_observation()
        result = None
        for t in turns(db_path):
            result = await env.step(t)
            if result.episode_done:
                break
        return result

    return asyncio.run(go())


def test_gold_policy_gets_full_reward(tmp_path):
    result = run_policy(gold_turns, tmp_path)
    assert result.episode_done
    assert abs(result.reward - 1.0) < 1e-9, result


def test_submit_without_work_gets_zero(tmp_path):
    result = run_policy(lambda db: [message(call("submit"))], tmp_path)
    assert result.episode_done
    assert result.reward == 0.0, result


def test_no_tool_call_ends_episode_with_zero(tmp_path):
    result = run_policy(
        lambda db: [{"role": "assistant", "content": "RESULT: SUCCESS"}], tmp_path
    )
    assert result.episode_done
    assert result.reward == 0.0, result
