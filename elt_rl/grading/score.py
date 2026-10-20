from pathlib import Path
import io
import pandas as pd
from ..warehouse.base import Warehouse
from .compare import check_correctness, sort_by_keys

AIRBYTE_COLS = {"_airbyte_raw_id", "_airbyte_extracted_at"}


def score_stage1(wh, schema, expected_raw):
    detail = {}
    if not wh.schema_exists(schema):
        return 0.0, {t: "schema_missing" for t in expected_raw}
    present = {t.lower() for t in wh.list_tables(schema)}
    ok = 0
    for table, n_rows in expected_raw.items():
        t = table.lower()
        if t not in present:
            detail[table] = "missing"
        elif wh.table_size(schema, t) != n_rows:
            detail[table] = "row_count"
        else:
            detail[table] = "ok"
            ok += 1
    return ok / max(len(expected_raw), 1), detail


def _normalize(df):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return pd.read_csv(buf, dtype=str, keep_default_na=True)


def score_stage2(wh, schema, gt_dir, sort_keys):
    per_table = {}
    gt_files = sorted(Path(gt_dir).glob("*.csv"))
    for gt_path in gt_files:
        table = gt_path.stem
        df_gt = pd.read_csv(gt_path, dtype=str, keep_default_na=True)
        try:
            df = _normalize(wh.fetch_table(schema, table))
            if df.empty and len(df.columns) == 0:
                raise LookupError("table missing or empty")
        except Exception as e:
            per_table[table] = {
                "score": 0.0,
                "status": f"unavailable: {type(e).__name__}",
            }
            continue
        keys = sort_keys.get(table, [])
        res = check_correctness(sort_by_keys(df_gt, keys), sort_by_keys(df, keys))
        score = len(res["matched"]) / max(len(df_gt.columns), 1)
        per_table[table] = {"score": score, "status": "ok", **res}
    scores = [v["score"] for v in per_table.values()]
    return (sum(scores) / len(scores) if scores else 0.0), per_table
