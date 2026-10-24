import asyncio

from tinker_cookbook.tool_use import ToolInput

from elt_rl.sandbox.local import LocalSandbox
from elt_rl.tools import ELTTools


def run(coro):
    return asyncio.run(coro)


def call(tool, **args):
    return run(tool.run(ToolInput(arguments=args)))


def make():
    return ELTTools(LocalSandbox())


def test_write_outside_elt_rejected():
    t = make()
    res = call(t.write_file, path="config.yaml", content="x")
    assert "error" in str(res.messages)


def test_write_traversal_rejected():
    t = make()
    res = call(t.write_file, path="elt/../config.yaml", content="x")
    assert "error" in str(res.messages)


def test_write_then_read():
    t = make()
    call(t.write_file, path="elt/a.txt", content="hello")
    res = call(t.read_file, path="elt/a.txt")
    assert "hello" in str(res.messages)


def test_bash_runs():
    t = make()
    res = call(t.bash, command="echo hi")
    assert "hi" in str(res.messages)


def test_submit_stops_episode():
    t = make()
    res = call(t.submit)
    assert res.should_stop is True
    assert t.submitted is True
