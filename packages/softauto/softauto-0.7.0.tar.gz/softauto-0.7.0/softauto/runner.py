from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import os, json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, KFold, cross_val_score
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
import joblib

from .advisor import advise
from .model_zoo import classifiers, regressors
from .preprocess import build_preprocessor, clip_outliers
from .feature_select import select_features_mutual_info, select_features_rfecv
from .metrics import classification_metrics, regression_metrics
from . import plots as P

@dataclass
class Runner:
    df: Optional[pd.DataFrame] = None
    target: Optional[str] = None
    task: Optional[str] = None
    report_dir: str = "softauto_artifacts"
    random_state: int = 42
    test_size: float = 0.2
    stratify: bool = True

    model: Union[str, List[str], None] = None
    scale: Optional[str] = None
    one_hot: Optional[bool] = None
    cat_min_freq: Optional[float] = None
    numeric_impute: Optional[str] = None
    categorical_impute: Optional[str] = None
    use_smote: bool = False

    feature_selection: Optional[str] = None
    top_k_features: Optional[int] = 30
    pca_components: Optional[int] = None

    cv: int = 5

    pipeline: Any = field(default=None, init=False)
    best_name: Optional[str] = field(default=None, init=False)
    leaderboard_: Optional[pd.DataFrame] = field(default=None, init=False)
    X_test_: Optional[pd.DataFrame] = field(default=None, init=False)
    y_test_: Optional[pd.Series] = field(default=None, init=False)

    def fit(self, df: Optional[pd.DataFrame] = None, target: Optional[str] = None, task: Optional[str] = None) -> Dict[str, Any]:
        if df is None: df = self.df
        if target is None: target = self.target
        assert df is not None and target is not None, "Provide df and target."

        hint = advise(df, target, task or self.task)
        task = hint["task"]
        os.makedirs(self.report_dir, exist_ok=True)

        pre_kwargs = hint["preprocess"].copy()
        if self.scale is not None: pre_kwargs["scale"] = self.scale
        if self.one_hot is not None: pre_kwargs["one_hot"] = self.one_hot
        if self.cat_min_freq is not None: pre_kwargs["cat_min_freq"] = self.cat_min_freq
        if self.numeric_impute is not None: pre_kwargs["numeric_impute"] = self.numeric_impute
        if self.categorical_impute is not None: pre_kwargs["categorical_impute"] = self.categorical_impute

        X = df.drop(columns=[target]); y = df[target]
        X_tr, X_te, y_tr, y_te = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state,
            stratify=y if (task=="classification" and self.stratify) else None
        )
        self.X_test_, self.y_test_ = X_te, y_te

        X_tr = clip_outliers(X_tr, X_tr.select_dtypes(include=np.number).columns.tolist())
        pre, num_cols, cat_cols, X_tr_mod = build_preprocessor(X_tr, **pre_kwargs)

        select_cols = X_tr_mod.columns.tolist()
        if self.feature_selection or hint["selection"]["feature_selection"]:
            mode = self.feature_selection or hint["selection"]["feature_selection"]
            if mode == "mutual_info":
                select_cols = select_features_mutual_info(X_tr_mod, y_tr, task, top_k=self.top_k_features or 30)
            elif mode == "rfecv":
                from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
                base = RandomForestClassifier(n_estimators=200, random_state=42) if task=="classification" else RandomForestRegressor(n_estimators=200, random_state=42)
                select_cols = select_features_rfecv(X_tr_mod, y_tr, base, task, cv=min(5, self.cv))
            X_tr = X_tr[select_cols]; X_te = X_te[select_cols]
            pre, _, _, _ = build_preprocessor(X_tr, **pre_kwargs)

        steps = [("pre", pre)]
        if self.pca_components or (hint["selection"]["pca"] and self.pca_components is None):
            k = self.pca_components or 50
            steps.append(("pca", PCA(n_components=min(k, max(1, len(select_cols)-1)))))

        zoo = classifiers() if task=="classification" else regressors()

        shortlist = hint["shortlist"] if (self.model in [None, "auto"]) else (
            [self.model] if isinstance(self.model, str) else list(self.model)
        )
        models = {name: zoo[name] for name in shortlist if name in zoo}

        cvobj = StratifiedKFold(self.cv, shuffle=True, random_state=self.random_state) if task=="classification" else KFold(self.cv, shuffle=True, random_state=self.random_state)

        rows = []
        best_name, best_score, best_pipe = None, -1e18, None
        for name, est in models.items():
            pipe = Pipeline(steps + [("model", est)])
            scoring = "accuracy" if task=="classification" else "r2"
            try:
                scores = cross_val_score(pipe, X_tr, y_tr, cv=cvobj, scoring=scoring, n_jobs=-1)
                mean_score = float(np.mean(scores))
            except Exception:
                pipe.fit(X_tr, y_tr)
                mean_score = float(pipe.score(X_tr, y_tr))
            rows.append({"model": name, "cv_score": mean_score})
            if mean_score > best_score:
                best_name, best_score, best_pipe = name, mean_score, pipe

        best_pipe.fit(X_tr, y_tr)
        self.pipeline = best_pipe
        self.best_name = best_name
        self.leaderboard_ = pd.DataFrame(rows).sort_values("cv_score", ascending=False).reset_index(drop=True)

        y_hat = best_pipe.predict(X_te)
        y_proba = None
        if task=="classification" and hasattr(best_pipe.named_steps["model"], "predict_proba"):
            try: y_proba = best_pipe.predict_proba(X_te)
            except Exception: y_proba = None

        metrics = classification_metrics(y_te, y_hat, y_proba) if task=="classification" else regression_metrics(y_te, y_hat)

        art = {}
        art["target_distribution"] = P.target_distribution(y, self.report_dir)
        art["missingness"] = P.missingness(df, self.report_dir)
        cm_path = P.corr_matrix(df, target, self.report_dir)
        if cm_path: art["corr_matrix"] = cm_path

        model_path = os.path.join(self.report_dir, f"best_{best_name}.joblib")
        joblib.dump(best_pipe, model_path)

        summary = {
            "task": task,
            "best_model": best_name,
            "cv_leaderboard": self.leaderboard_.to_dict(orient="records"),
            "test_metrics": metrics,
            "artifacts": art,
            "model_path": model_path,
            "advisor_notes": advise(df, target, task)["notes"],
            "selected_features": select_cols,
        }
        with open(os.path.join(self.report_dir, "summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        return summary

    def predict(self, X: pd.DataFrame):
        assert self.pipeline is not None, "Call fit() first."
        return self.pipeline.predict(X)

def autorun(df: pd.DataFrame, target: str, task: Optional[str] = None, **kwargs):
    return Runner(df=df, target=target, task=task, **kwargs).fit()
