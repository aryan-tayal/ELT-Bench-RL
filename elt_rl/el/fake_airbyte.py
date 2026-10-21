import re
import duckdb
from pathlib import Path

IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_streams(source_dir, db_path, schema, streams):
    if not IDENT.match(schema):
        raise ValueError(f"bad schema name: {schema!r}")
    con = duckdb.connect(str(db_path))
    loaded = []
    try:
        con.execute(f'create schema if not exists "{schema}"')
        for s in streams:
            name, mode = s.get("name"), s.get("sync_mode")
            if not isinstance(name, str) or not IDENT.match(name):
                raise ValueError(f"bad stream name: {name!r}")
            if mode not in ["full_refresh_append", "full_refresh_override"]:
                raise ValueError(
                    f"stream {name}: sync_mode must be one of 'full_refresh_append', 'full_refresh_override'"
                )
            csv = Path(source_dir) / f"{name}.csv"
            if not csv.is_file():
                raise FileNotFoundError(f"no source named {name!r}")
            path = str(csv).replace("'", "''")
            select = (
                "SELECT uuid()::varchar AS _airbyte_raw_id, now() AS _airbyte_extracted_at, * "
                f"FROM read_csv_auto('{path}')"
            )
            target = f'"{schema}"."{name}"'
            exists = (
                con.execute(
                    "SELECT count(*) FROM information_schema.tables "
                    "WHERE table_schema=? and table_name=?",
                    [schema, name],
                ).fetchone()[0]
                > 0
            )
            if mode == "full_refresh_overwrite" or not exists:
                con.execute(f"CREATE OR replace TABLE {target} AS {select}")
            else:
                con.execute(f"INSERT INTO {target} {select}")
            loaded.append(name)
    finally:
        con.close()
    return loaded
