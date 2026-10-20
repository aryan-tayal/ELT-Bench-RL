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

def score_stage2(wh, schema, get_dir, sort_keys):
    