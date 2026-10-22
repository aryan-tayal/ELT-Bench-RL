import asyncio
import pytest
from elt_rl.sandbox.local import LocalSandbox


def run(coro):
    return asyncio.run(coro)


def test_echo():
    async def go():
        sb = LocalSandbox()
        r = await sb.run_command("echo hi")
        await sb.cleanup()
        return r
    r = run(go())
    assert r.stdout.strip() == "hi" and r.exit_code == 0


def test_timeout():
    async def go():
        sb = LocalSandbox()
        r = await sb.run_command("sleep 5", timeout=1)
        await sb.cleanup()
        return r
    assert run(go()).exit_code == 124


def test_write_read_roundtrip():
    async def go():
        sb = LocalSandbox()
        await sb.write_file("elt/a.txt", "hello")
        r = await sb.read_file("elt/a.txt")
        await sb.cleanup()
        return r
    assert run(go()).stdout == "hello"


def test_escape_rejected():
    async def go():
        sb = LocalSandbox()
        try:
            await sb.write_file("../escape.txt", "x")
        finally:
            await sb.cleanup()
    with pytest.raises(ValueError):
        run(go())


def test_cleanup_removes_root():
    async def go():
        sb = LocalSandbox()
        root = sb.root
        await sb.cleanup()
        return root
    assert not run(go()).exists()