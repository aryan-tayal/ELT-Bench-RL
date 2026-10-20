# Adapted from ELT-Bench (evaluation/eva_stage2.py), https://github.com/uiuc-kang-lab/ELT-Bench
# Licensed under CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/
# Changes: renamed check_corretness -> check_correctness
# This file is therefore also distributed under CC BY-SA 4.0.

import numpy as np
import pandas as pd


def _to_numeric_if_possible(s: pd.Series) -> pd.Series:
    """Try numeric coercion; return original Series if any non-null fails."""
    coerced = pd.to_numeric(s, errors="coerce")
    # accept only if every original non-null value parsed successfully
    if coerced.isna().sum() == s.isna().sum():
        return coerced
    return s


def _vectors_match(
    v1: pd.Series, v2: pd.Series, rtol: float = 1e-2, atol: float = 1e-9
) -> bool:
    if len(v1) != len(v2):
        return False

    # Best-effort: if BOTH sides parse cleanly as numeric, compare numerically.
    n1 = _to_numeric_if_possible(v1.reset_index(drop=True))
    n2 = _to_numeric_if_possible(v2.reset_index(drop=True))
    both_numeric = pd.api.types.is_numeric_dtype(n1) and pd.api.types.is_numeric_dtype(
        n2
    )

    if both_numeric:
        a = n1.to_numpy(dtype=float)
        b = n2.to_numpy(dtype=float)
        # element-wise: NaN==NaN ok; else within relative + absolute tolerance.
        nan_match = np.isnan(a) & np.isnan(b)
        close = np.isclose(a, b, rtol=rtol, atol=atol, equal_nan=False)
        return bool(np.all(nan_match | close))

    # Mixed / non-numeric: case-insensitive string compare with NaN tolerance.
    for a, b in zip(v1, v2):
        if pd.isna(a) and pd.isna(b):
            continue
        if pd.isna(a) or pd.isna(b):
            return False
        if isinstance(a, str) and isinstance(b, str):
            if a.strip().lower() != b.strip().lower():
                return False
        else:
            if a != b:
                return False
    return True


def check_correctness(df_gt: pd.DataFrame, df: pd.DataFrame) -> dict:
    """Compare each gold column against its (case-insensitively matched)
    actual column. Returns a structured result dict:

        {
          "status": "ok",
          "match": <bool>,          # True iff nothing unmatched/missed
          "matched": [...],
          "unmatched": [...],
          "missed": [...],
        }
    """
    matched_cols, unmatched_cols, missed_cols = [], [], []
    df_cols_lower = {c.lower(): c for c in df.columns}

    for gold_col in df_gt.columns:
        actual_col = df_cols_lower.get(gold_col.lower())
        if actual_col is None:
            missed_cols.append(gold_col)
            continue
        if _vectors_match(df_gt[gold_col], df[actual_col]):
            matched_cols.append(gold_col)
        else:
            unmatched_cols.append(gold_col)

    return {
        "status": "ok",
        "match": not unmatched_cols and not missed_cols,
        "matched": matched_cols,
        "unmatched": unmatched_cols,
        "missed": missed_cols,
    }
