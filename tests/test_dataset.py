import asyncio

from elt_rl.dataset import ELTDatasetBuilder


def make(repeats=5, batch_size=2):
    return ELTDatasetBuilder(
        task_names=["synthetic_shop"],
        batch_size=batch_size,
        group_size=4,
        model_name="Qwen/Qwen3-8B",
        repeats=repeats,
    )


def test_batches():
    train, ev = asyncio.run(make()())
    assert len(train) == 3  # 5 groups, 2 per batch
    assert len(train.get_batch(0)) == 2
    assert len(train.get_batch(2)) == 1
    assert train.get_batch(0)[0].group_size == 4
    assert ev.get_batch(0)[0].group_size == 1
