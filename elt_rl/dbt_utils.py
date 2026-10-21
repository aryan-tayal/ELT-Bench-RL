import os
import shutil
import subprocess
import sys
from pathlib import Path

PROFILE = """elt:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "{path}"
      schema: {schema}
      threads: 1
"""


def write_profile(project_dir: Path, db_path: Path, schema: str) -> None:
    (project_dir / "profiles.yml").write_text(
        PROFILE.format(path=Path(db_path).resolve(), schema=schema)
    )


def dbt_executable() -> str:
    candidate = Path(sys.executable).parent / "dbt"
    return str(candidate) if candidate.exists() else (shutil.which("dbt") or "dbt")


def run_dbt(project_dir: Path, timeout: int = 180) -> subprocess.CompletedProcess:
    env = {**os.environ, "DBT_SEND_ANONYMOUS_USAGE_STATS": "False"}
    return subprocess.run(
        [
            dbt_executable(),
            "run",
            "--project-dir",
            str(project_dir),
            "--profiles-dir",
            str(project_dir),
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
