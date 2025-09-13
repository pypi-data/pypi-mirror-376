from __future__ import annotations
from typing import Optional, Tuple, List
import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression, RFECV
from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold, KFold

def select_features_mutual_info(X: pd.DataFrame, y: pd.Series, task: str, top_k: int = 20) -> List[str]:
    num_cols = X.select_dtypes(include=np.number).columns.tolist()
    cat_cols = [c for c in X.columns if c not in num_cols]
    X_enc = X.copy()
    for c in cat_cols:
        X_enc[c] = X_enc[c].astype("category").cat.codes
    disc_mask = [c not in num_cols for c in X.columns]
    if task == "classification":
        scores = mutual_info_classif(X_enc, y, discrete_features=disc_mask, random_state=42)
    else:
        scores = mutual_info_regression(X_enc, y, discrete_features=disc_mask, random_state=42)
    mi = pd.Series(scores, index=X.columns).sort_values(ascending=False)
    return mi.head(min(top_k, len(mi))).index.tolist()

def select_features_rfecv(X, y, estimator, task: str, cv: int = 5):
    cvobj = StratifiedKFold(cv, shuffle=True, random_state=42) if task=="classification" else KFold(cv, shuffle=True, random_state=42)
    rfecv = RFECV(clone(estimator), step=1, cv=cvobj, scoring=("accuracy" if task=="classification" else "r2"), n_jobs=-1)
    rfecv.fit(X, y)
    support = getattr(rfecv, "support_", None)
    return list(X.columns[support]) if support is not None else X.columns.tolist()
