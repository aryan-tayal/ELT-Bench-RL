import asyncio

from elt_rl.env import ELTEnvGroupBuilder


def test_builder_is_picklable():
    import pickle

    b = ELTEnvGroupBuilder("synthetic_shop", "Qwen/Qwen3-8B", None, 10, 2)
    assert pickle.loads(pickle.dumps(b)).task_name == "synthetic_shop"


def test_cleanup_is_safe_with_no_envs():
    b = ELTEnvGroupBuilder("synthetic_shop", "Qwen/Qwen3-8B", None, 10, 2)
    asyncio.run(b.cleanup())
    asyncio.run(b.cleanup())


def test_logging_tags():
    b = ELTEnvGroupBuilder("synthetic_shop", "Qwen/Qwen3-8B", None, 10, 2)
    assert "elt" in b.logging_tags()
