from __future__ import annotations
from typing import Dict, Any

# Sklearn baselines
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor

# Optional libraries (conditionally available)
_HAS_XGB = False
_HAS_LGBM = False
_HAS_CAT  = False

try:
    from xgboost import XGBClassifier, XGBRegressor  # type: ignore
    _HAS_XGB = True
except Exception:
    pass

try:
    from lightgbm import LGBMClassifier, LGBMRegressor  # type: ignore
    _HAS_LGBM = True
except Exception:
    pass

try:
    from catboost import CatBoostClassifier, CatBoostRegressor  # type: ignore
    _HAS_CAT = True
except Exception:
    pass


def classifiers() -> Dict[str, Any]:
    zoo: Dict[str, Any] = {
        "logreg": LogisticRegression(max_iter=1000),
        "random_forest": RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1),
        "gb": GradientBoostingClassifier(),
        "svm_rbf": SVC(kernel="rbf", probability=True),
        "knn": KNeighborsClassifier(),
        "mlp": MLPClassifier(hidden_layer_sizes=(128,), max_iter=400),
    }
    if _HAS_XGB:
        zoo["xgb"] = XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
            eval_metric="logloss", tree_method="hist", random_state=42, n_jobs=-1
        )
    if _HAS_LGBM:
        zoo["lgbm"] = LGBMClassifier(
            n_estimators=400, learning_rate=0.05, num_leaves=31, subsample=0.8, colsample_bytree=0.8,
            random_state=42, n_jobs=-1
        )
    if _HAS_CAT:
        zoo["catboost"] = CatBoostClassifier(
            depth=6, learning_rate=0.1, iterations=400, loss_function="Logloss",
            verbose=False, allow_writing_files=False, random_seed=42
        )
    return zoo


def regressors() -> Dict[str, Any]:
    zoo: Dict[str, Any] = {
        "linear": LinearRegression(),
        "ridge": Ridge(alpha=1.0),
        "lasso": Lasso(alpha=0.001, max_iter=10000),
        "random_forest": RandomForestRegressor(n_estimators=400, random_state=42, n_jobs=-1),
        "gb": GradientBoostingRegressor(),
        "svr_rbf": SVR(kernel="rbf"),
        "knn": KNeighborsRegressor(),
        "mlp": MLPRegressor(hidden_layer_sizes=(128,), max_iter=500),
    }
    if _HAS_XGB:
        zoo["xgb"] = XGBRegressor(
            n_estimators=500, max_depth=6, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
            tree_method="hist", random_state=42, n_jobs=-1
        )
    if _HAS_LGBM:
        zoo["lgbm"] = LGBMRegressor(
            n_estimators=600, learning_rate=0.05, num_leaves=31, subsample=0.8, colsample_bytree=0.8,
            random_state=42, n_jobs=-1
        )
    if _HAS_CAT:
        zoo["catboost"] = CatBoostRegressor(
            depth=6, learning_rate=0.05, iterations=600, loss_function="RMSE",
            verbose=False, allow_writing_files=False, random_seed=42
        )
    return zoo


def default_shortlist(task: str):
    base_cls = ["random_forest", "logreg", "gb", "svm_rbf", "knn", "mlp", "xgb", "lgbm", "catboost"]
    base_reg = ["random_forest", "linear", "ridge", "gb", "svr_rbf", "knn", "mlp", "xgb", "lgbm", "catboost"]
    return base_cls if task == "classification" else base_reg
