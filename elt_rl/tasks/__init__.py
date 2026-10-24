def get_task(name: str):
    if name == "synthetic_shop":
        from elt_rl.tasks.synthetic_shop import load_task

        return load_task()
    raise ValueError(f"unknown task: {name!r}")
