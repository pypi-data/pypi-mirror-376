# softauto/guards.py
from __future__ import annotations
from typing import Dict, Any, List, Optional
import re
import numpy as np
import pandas as pd

ID_PATTERNS = re.compile(r"(?:^|_)(id|uuid|guid|hash|token)(?:$|_)", re.I)
DATE_PATTERNS = re.compile(r"(date|time|timestamp|ts)$", re.I)

def _safe_nunique(s: pd.Series) -> int:
    try:
        return int(s.nunique(dropna=True))
    except Exception:
        return len(pd.Series(s).astype(str).unique())

def detect_constant_columns(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if _safe_nunique(df[c]) <= 1]

def detect_id_like_columns(df: pd.DataFrame, max_ratio: float = 0.98) -> List[str]:
    # ID-like = (almost) all unique OR name looks like '...id'
    n = len(df)
    out = []
    for c in df.columns:
        if ID_PATTERNS.search(c):
            out.append(c)
            continue
        u = _safe_nunique(df[c])
        if n > 0 and (u / max(1, n)) >= max_ratio:
            out.append(c)
    return out

def detect_target_duplicates(X: pd.DataFrame, y: pd.Series, match_ratio: float = 0.98) -> List[str]:
    # Feature equals target most of the time → likely leakage/label copy
    out = []
    y_s = pd.Series(y)
    for c in X.columns:
        try:
            eq = (pd.Series(X[c]).astype(str).values == y_s.astype(str).values)
            if np.mean(eq) >= match_ratio:
                out.append(c)
        except Exception:
            continue
    return out

def detect_near_perfect_numeric_corr(X: pd.DataFrame, y: pd.Series, threshold: float = 0.995) -> List[str]:
    out = []
    y_num = pd.to_numeric(pd.Series(y), errors="coerce")
    if y_num.notna().mean() < 0.8:
        return out
    for c in X.select_dtypes(include=np.number).columns:
        try:
            s = X[c]
            corr = float(pd.Series(s).corr(y_num))
            if np.isfinite(corr) and abs(corr) >= threshold:
                out.append(c)
        except Exception:
            continue
    return out

def detect_datetime_features(df: pd.DataFrame) -> List[str]:
    out = []
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]) or DATE_PATTERNS.search(c or ""):
            out.append(c)
    return out

def run_leakage_guard(df: pd.DataFrame, target: str) -> Dict[str, Any]:
    issues: Dict[str, Any] = {"warnings": [], "details": {}}
    if target not in df:
        issues["warnings"].append(f"Target '{target}' not found in df.")
        return issues

    X = df.drop(columns=[target])
    y = df[target]

    consts = detect_constant_columns(X)
    ids    = detect_id_like_columns(X)
    dts    = detect_datetime_features(X)
    dup_t  = detect_target_duplicates(X, y)
    corr_t = detect_near_perfect_numeric_corr(X, y)

    if consts: issues["warnings"].append(f"{len(consts)} constant column(s) detected.")
    if ids:    issues["warnings"].append(f"{len(ids)} ID-like column(s) detected.")
    if dts:    issues["warnings"].append(f"{len(dts)} datetime-like column(s) found (check for leakage).")
    if dup_t:  issues["warnings"].append(f"{len(dup_t)} feature(s) almost duplicate the target.")
    if corr_t: issues["warnings"].append(f"{len(corr_t)} numeric feature(s) with near-perfect correlation to target.")

    issues["details"] = {
        "constant_columns": consts,
        "id_like_columns": ids,
        "datetime_like_columns": dts,
        "target_duplicate_like": dup_t,
        "near_perfect_corr_to_target": corr_t,
    }
    return issues
