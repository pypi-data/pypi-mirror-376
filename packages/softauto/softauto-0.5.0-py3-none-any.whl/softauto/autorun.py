# softauto/autorun.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import json
import os
import warnings
import hashlib

import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import (
    train_test_split,
    cross_val_score,
    StratifiedKFold,
    KFold,
    RandomizedSearchCV,
)
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    roc_auc_score,
    r2_score,
    mean_squared_error,
    mean_absolute_error,
)

from .model_zoo import classifiers, regressors, default_shortlist
from .preprocess import build_preprocessor, clip_outliers
from .feature_select import select_features_mutual_info, select_features_rfecv
from .report import (
    plot_target_distribution,
    plot_missingness,
    plot_corr,
    plot_feature_importance,
    write_simple_html,
)
from .guards import run_leakage_guard

# Optional imbalanced-learn
try:
    from imblearn.pipeline import Pipeline as ImbPipeline
    from imblearn.over_sampling import SMOTE

    HAS_IMB = True
except Exception:
    HAS_IMB = False


# -------------------- Helpers --------------------
def _lite_eda(df: pd.DataFrame, target: str) -> Dict[str, Any]:
    eda = {"shape": df.shape, "dtypes": df.dtypes.astype(str).to_dict()}
    miss = df.isna().mean().sort_values(ascending=False)
    eda["missing_rate_top"] = miss.head(15).round(3).to_dict()
    if target in df:
        if pd.api.types.is_numeric_dtype(df[target]):
            eda["target_summary"] = {
                "mean": float(df[target].mean()),
                "std": float(df[target].std()),
                "min": float(df[target].min()),
                "max": float(df[target].max()),
            }
        else:
            eda["target_counts"] = df[target].value_counts(dropna=False).to_dict()
    return eda


def _compute_metrics(
    task: str,
    y_true,
    y_pred,
    y_proba=None,
    wanted: Optional[List[str]] = None,
) -> Dict[str, float]:
    wanted = wanted or (
        ["accuracy", "f1", "roc_auc"] if task == "classification" else ["r2", "rmse", "mae"]
    )
    out: Dict[str, float] = {}
    if task == "classification":
        if "accuracy" in wanted:
            out["accuracy"] = float(accuracy_score(y_true, y_pred))
        if "f1" in wanted:
            out["f1"] = float(f1_score(y_true, y_pred, average="macro"))
        if "roc_auc" in wanted and y_proba is not None:
            try:
                if getattr(y_proba, "ndim", 1) == 1 or getattr(y_proba, "shape", (0,))[1] == 2:
                    probs = y_proba if y_proba.ndim == 1 else y_proba[:, 1]
                    out["roc_auc"] = float(roc_auc_score(y_true, probs))
                else:
                    out["roc_auc_ovr"] = float(roc_auc_score(y_true, y_proba, multi_class="ovr"))
            except Exception:
                pass
    else:
        if "r2" in wanted:
            out["r2"] = float(r2_score(y_true, y_pred))
        if "rmse" in wanted:
            out["rmse"] = float(mean_squared_error(y_true, y_pred, squared=False))
        if "mae" in wanted:
            out["mae"] = float(mean_absolute_error(y_true, y_pred))
    return out


def _cv(task: str, k: int, shuffle: bool, seed: int):
    return (
        StratifiedKFold(n_splits=k, shuffle=shuffle, random_state=seed)
        if task == "classification"
        else KFold(n_splits=k, shuffle=shuffle, random_state=seed)
    )


def _param_space(task: str, model_name: str) -> Dict[str, List[Any]]:
    # Hyperparameter grids (trimmed for readability)
    grids: Dict[str, List[Any]] = {
        "random_forest": {
            "model__n_estimators": [200, 400, 600],
            "model__max_depth": [None, 6, 10, 16],
        },
        "logreg": {"model__C": [0.1, 0.5, 1.0, 2.0], "model__penalty": ["l2"]},
        "gb": {
            "model__n_estimators": [200, 400],
            "model__learning_rate": [0.03, 0.06, 0.1],
            "model__max_depth": [2, 3],
        },
        "svm_rbf": {"model__C": [0.5, 1, 2, 4], "model__gamma": ["scale", 0.1, 0.01]},
        "knn": {"model__n_neighbors": [3, 5, 7, 9]},
        "mlp": {
            "model__hidden_layer_sizes": [(64,), (128,), (64, 64)],
            "model__alpha": [1e-4, 1e-3, 1e-2],
        },
    }
    return grids.get(model_name, {})


def _hash_dataframe(df: pd.DataFrame) -> str:
    try:
        m = hashlib.md5()
        m.update(pd.util.hash_pandas_object(df, index=True).values.tobytes())
        return m.hexdigest()
    except Exception:
        return hex(hash(tuple(df.columns)) & 0xFFFFFFFFFFFFF)


# -------------------- Core API --------------------
@dataclass
class AutoRun:
    df: pd.DataFrame
    target: str
    task: str = "classification"
    model: str = "auto"
    params: Dict[str, Any] = field(default_factory=dict)

    test_size: float = 0.2
    random_state: int = 42
    numeric_impute: str = "median"
    categorical_impute: str = "most_frequent"
    scale: Optional[str] = "standard"
    one_hot: bool = True

    cv: Optional[int] = 5
    metrics: Optional[List[str]] = None
    report_dir: str = "softauto_artifacts"

    imbalance: str = "auto"
    smote_k_neighbors: int = 5

    cat_min_freq: Optional[float] = 0.01
    num_clip_quantiles: Optional[Tuple[float, float]] = (0.01, 0.99)

    tune: Optional[str] = None
    n_iter: int = 15

    feature_selection: Optional[str] = None
    top_k_features: Optional[int] = 20
    plots: bool = True

    advisor_threshold: Optional[float] = 0.75
    advisor_auto_fix: bool = True

    # internals omitted for brevity...
    # (keep the full fit() method as you already have)

    # NOTE: keep your existing .fit() code intact


# -------------------- Wrapper --------------------
def autorun(X_train, y_train, task="classification", **kwargs):
    """
    Convenience wrapper for AutoRun.
    Allows passing X_train/y_train directly.
    """
    import pandas as pd
    df = pd.DataFrame(X_train).copy()
    df["_y"] = y_train
    runner = AutoRun(df=df, target="_y", task=task, **kwargs)
    results = runner.fit()
    results["best_estimator_"] = runner.__dict__.get("pipeline")
    return results
