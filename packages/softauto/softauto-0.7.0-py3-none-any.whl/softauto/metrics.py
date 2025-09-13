from __future__ import annotations
from typing import Dict
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    roc_auc_score, r2_score, mean_squared_error, mean_absolute_error
)

def classification_metrics(y_true, y_pred, y_proba=None) -> Dict[str, float]:
    out = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro")),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
    }
    if y_proba is not None:
        try:
            import numpy as np
            if getattr(y_proba, "ndim", 1) == 1 or getattr(y_proba, "shape", (0,))[1] == 2:
                probs = y_proba if getattr(y_proba, "ndim", 1) == 1 else y_proba[:, 1]
                out["roc_auc"] = float(roc_auc_score(y_true, probs))
            else:
                out["roc_auc_ovr"] = float(roc_auc_score(y_true, y_proba, multi_class="ovr"))
        except Exception:
            pass
    return out

def regression_metrics(y_true, y_pred) -> Dict[str, float]:
    # Avoid 'squared=False' for max compatibility
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = mse ** 0.5
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "rmse": rmse,
        "mae": float(mean_absolute_error(y_true, y_pred)),
    }
