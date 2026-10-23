import asyncio
import sys
import tempfile
from pathlib import Path

# from elt_rl.dbt_utils import write_profile
from elt_rl.grading import score_warehouse
from elt_rl.sandbox.local import LocalSandbox
from elt_rl.tasks.synthetic_shop import load_task
from elt_rl.warehouse import DuckDBWarehouse
from elt_rl.workspace import build_workspace

PROFILE_YML = """elt:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "{path}"
      schema: {schema}
      threads: 1
"""

TASK = load_task()

SOURCES_YAML = """streams:
  - name: customers
    sync_mode: full_refresh_append
  - name: orders
    sync_mode: full_refresh_append
  - name: refunds
    sync_mode: full_refresh_append
"""


async def run_scripted(models_dir: Path) -> dict:
    work = Path(tempfile.mkdtemp(prefix="elt_run_"))
    db_path = work / "warehouse.duckdb"
    sb = LocalSandbox(root=work / "ws")
    try:
        build_workspace(TASK, sb.root, db_path)
        await sb.write_file("elt/sources.yaml", SOURCES_YAML)
        r = await sb.run_command(
            f"{sys.executable} -m elt_rl.el.fake_airbyte "
            "--config config.yaml --streams elt/sources.yaml"
        )
        print("EL:", r.exit_code, r.stdout.strip(), r.stderr.strip()[-200:])
        for f in sorted(Path(models_dir).rglob("*")):
            if f.is_file():
                rel = f.relative_to(models_dir)
                await sb.write_file(f"elt/dbt/{rel}", f.read_text())
        await sb.write_file(
            "elt/dbt/profiles.yml",
            PROFILE_YML.format(path=db_path, schema=TASK.schema),
        )
        r = await sb.run_command(
            f"{Path(sys.executable).parent / 'dbt'} run "
            "--project-dir elt/dbt --profiles-dir elt/dbt"
        )
        print("DBT:", r.exit_code, r.stdout.strip()[-200:])
        result = score_warehouse(
            DuckDBWarehouse(db_path),
            TASK.schema,
            TASK.expected_raw,
            TASK.gt_dir,
            TASK.sort_keys,
        )
        return result.metrics()
    finally:
        await sb.cleanup()


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "gold"
    models = TASK.gold_dir if which == "gold" else TASK.bad_dir
    print(which, asyncio.run(run_scripted(models)))
