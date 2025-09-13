from __future__ import annotations
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from .model_zoo import default_shortlist

def _class_balance(y: pd.Series) -> float:
    vc = pd.Series(y).value_counts(normalize=True, dropna=False)
    return float(vc.min()) if len(vc) > 1 else 1.0

def advise(df: pd.DataFrame, target: str, task: Optional[str] = None) -> Dict[str, Any]:
    assert target in df.columns, f"target '{target}' not in df"
    y = df[target]
    X = df.drop(columns=[target])

    if task is None:
        task = "regression" if pd.api.types.is_numeric_dtype(y) and y.nunique() > 10 else "classification"

    n, p = X.shape
    num_cols = X.select_dtypes(include=np.number).columns.tolist()
    cat_cols = [c for c in X.columns if c not in num_cols]
    frac_cat = len(cat_cols) / max(1, p)
    min_class = _class_balance(y) if task == "classification" else None
    miss_rate = float(X.isna().mean().mean())

    shortlist = default_shortlist(task)
    reasons: List[str] = []

    if task == "classification":
        if min_class is not None and min_class < 0.15:
            reasons.append("Class imbalance detected; consider SMOTE or tree-based models.")
        if frac_cat > 0.5:
            reasons.append("Many categorical features; consider CatBoost/RandomForest/GB.")
        if p > 200:
            reasons.append("High dimensionality; prefer linear/regularized models (logreg) or tree ensembles.")
    else:
        if p > 200: reasons.append("High dimensionality; consider Ridge/Lasso/GB/RandomForest.")
        if miss_rate > 0.2: reasons.append("High missingness; tree ensembles are robust.")

    preprocess = {
        "numeric_impute": "median",
        "categorical_impute": "most_frequent",
        "scale": "standard" if task == "classification" else "robust",
        "one_hot": True,
        "cat_min_freq": 0.01 if len(cat_cols) else None
    }
    selection = {"feature_selection": "mutual_info" if p > 20 else None, "pca": True if p > 100 else False}

    return {
        "task": task,
        "shortlist": shortlist,
        "preprocess": preprocess,
        "selection": selection,
        "notes": reasons,
        "shape": (n, p),
        "frac_categorical": frac_cat,
        "class_balance_min": min_class,
        "missing_rate": miss_rate
    }

class Advisor:
    def __call__(self, df: pd.DataFrame, target: str, task: Optional[str] = None) -> Dict[str, Any]:
        return advise(df, target, task)
