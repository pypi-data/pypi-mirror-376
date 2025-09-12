from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import json, os, warnings, numpy as np, pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold, KFold, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, r2_score, mean_squared_error, mean_absolute_error
import joblib

from .model_zoo import classifiers, regressors, default_shortlist
from .preprocess import build_preprocessor, clip_outliers
from .feature_select import select_features_mutual_info, select_features_rfecv
from .report import plot_target_distribution, plot_missingness, plot_corr, plot_feature_importance, write_simple_html

try:
    from imblearn.pipeline import Pipeline as ImbPipeline
    from imblearn.over_sampling import SMOTE
    HAS_IMB = True
except Exception:
    HAS_IMB = False

def _lite_eda(df: pd.DataFrame, target: str) -> Dict[str, Any]:
    eda = {"shape": df.shape, "dtypes": df.dtypes.astype(str).to_dict()}
    miss = df.isna().mean().sort_values(ascending=False)
    eda["missing_rate_top"] = miss.head(15).round(3).to_dict()
    if target in df:
        if pd.api.types.is_numeric_dtype(df[target]):
            eda["target_summary"] = {"mean": float(df[target].mean()), "std": float(df[target].std()),
                                     "min": float(df[target].min()), "max": float(df[target].max())}
        else:
            eda["target_counts"] = df[target].value_counts(dropna=False).to_dict()
    return eda

def _compute_metrics(task: str, y_true, y_pred, y_proba=None, wanted: Optional[List[str]] = None) -> Dict[str, float]:
    wanted = wanted or (["accuracy","f1","roc_auc"] if task=="classification" else ["r2","rmse","mae"])
    out = {}
    if task == "classification":
        if "accuracy" in wanted: out["accuracy"] = float(accuracy_score(y_true, y_pred))
        if "f1" in wanted:       out["f1"] = float(f1_score(y_true, y_pred, average="macro"))
        if "roc_auc" in wanted and y_proba is not None:
            try:
                if y_proba.ndim == 1 or getattr(y_proba, "shape", (0,))[1] == 2:
                    probs = y_proba if y_proba.ndim == 1 else y_proba[:,1]
                    out["roc_auc"] = float(roc_auc_score(y_true, probs))
                else:
                    out["roc_auc_ovr"] = float(roc_auc_score(y_true, y_proba, multi_class="ovr"))
            except Exception:
                pass
    else:
        if "r2" in wanted:   out["r2"] = float(r2_score(y_true, y_pred))
        if "rmse" in wanted: out["rmse"] = float(mean_squared_error(y_true, y_pred, squared=False))
        if "mae" in wanted:  out["mae"] = float(mean_absolute_error(y_true, y_pred))
    return out

def _cv(task: str, k: int, shuffle: bool, seed: int):
    return StratifiedKFold(n_splits=k, shuffle=shuffle, random_state=seed) if task=="classification" else KFold(n_splits=k, shuffle=shuffle, random_state=seed)

def _param_space(task: str, model_name: str) -> Dict[str, List[Any]]:
    grids = {
        "random_forest": {"model__n_estimators": [200, 400, 600], "model__max_depth": [None, 6, 10, 16]},
        "logreg": {"model__C": [0.1, 0.5, 1.0, 2.0], "model__penalty": ["l2"]},
        "gb": {"model__n_estimators": [200, 400], "model__learning_rate": [0.03, 0.06, 0.1], "model__max_depth": [2,3]},
        "svm_rbf": {"model__C": [0.5, 1, 2, 4], "model__gamma": ["scale", 0.1, 0.01]},
        "knn": {"model__n_neighbors": [3,5,7,9]},
        "mlp": {"model__hidden_layer_sizes": [(64,), (128,), (64,64)], "model__alpha": [1e-4, 1e-3, 1e-2]},
        "ridge": {"model__alpha": [0.1, 1.0, 10.0]},
        "lasso": {"model__alpha": [1e-4, 1e-3, 1e-2, 1e-1]},
        "svr_rbf": {"model__C": [0.5, 1, 5], "model__gamma": ["scale", 0.1, 0.01]},
    }
    return grids.get(model_name, {})

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
    imbalance: str = "auto"               # "auto" | "class_weight" | "smote" | None
    smote_k_neighbors: int = 5            # new: user-settable cap
    cat_min_freq: Optional[float] = 0.01
    num_clip_quantiles: Optional[Tuple[float,float]] = (0.01, 0.99)
    tune: Optional[str] = None
    n_iter: int = 15
    feature_selection: Optional[str] = None
    top_k_features: Optional[int] = 20
    plots: bool = True
    advisor_threshold: Optional[float] = 0.75
    advisor_auto_fix: bool = True

    def _build_pipeline(self, estimator, pre, sampler):
        steps = [("prep", pre)]
        if sampler is not None:
            steps.append(("smote", sampler))
        steps.append(("model", estimator))
        return (ImbPipeline if sampler is not None else Pipeline)(steps)

    def _evaluate(self, pipe, X_tr, y_tr, scoring, cv_obj, model_name):
        if self.tune == "random":
            space = _param_space(self.task, model_name)
            if space:
                rs = RandomizedSearchCV(pipe, space, n_iter=min(self.n_iter, sum(len(v) for v in space.values())),
                                        scoring=scoring, cv=cv_obj, random_state=self.random_state,
                                        n_jobs=-1, error_score=0.0)
                rs.fit(X_tr, y_tr)
                return rs.best_score_, rs.best_estimator_
        # fallback CV
        try:
            scores = cross_val_score(pipe, X_tr, y_tr, scoring=scoring, cv=cv_obj, n_jobs=-1)
            pipe.fit(X_tr, y_tr)
            return float(scores.mean()), pipe
        except Exception:
            # if any fold fails (often SMOTE), fit once without CV so pipeline still usable
            pipe.fit(X_tr, y_tr)
            return -1e9, pipe

    def fit(self) -> Dict[str, Any]:
        os.makedirs(self.report_dir, exist_ok=True)
        if self.target not in self.df.columns:
            raise ValueError(f"Target '{self.target}' not in DataFrame.")

        eda = _lite_eda(self.df, self.target)
        with open(os.path.join(self.report_dir, "eda.json"), "w") as f:
            json.dump(eda, f, indent=2)

        X = self.df.drop(columns=[self.target])
        y = self.df[self.target]

        # outlier clipping
        num_cols = X.select_dtypes(include=np.number).columns.tolist()
        if self.num_clip_quantiles is not None and num_cols:
            ql, qh = self.num_clip_quantiles
            X = clip_outliers(X, num_cols, ql, qh)

        # preprocessing
        pre, num_cols, cat_cols, X = build_preprocessor(X, self.numeric_impute, self.categorical_impute, self.scale, self.one_hot, self.cat_min_freq)

        # feature selection
        selected_cols = None
        if self.feature_selection == "mutual_info":
            selected_cols = select_features_mutual_info(X, y, self.task, top_k=self.top_k_features or 20)
            X = X[selected_cols]
            pre, num_cols, cat_cols, X = build_preprocessor(X, self.numeric_impute, self.categorical_impute, self.scale, self.one_hot, self.cat_min_freq)

        elif self.feature_selection == "rfecv":
            selected_cols = select_features_mutual_info(X, y, self.task, top_k=min(50, X.shape[1]))
            X_tmp = X[selected_cols].copy()
            for c in X_tmp.select_dtypes(exclude=np.number).columns:
                X_tmp[c] = X_tmp[c].astype("category").cat.codes
            from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
            base = RandomForestClassifier(n_estimators=200, random_state=42) if self.task=="classification" else RandomForestRegressor(n_estimators=200, random_state=42)
            selected_cols = select_features_rfecv(X_tmp, y, base, self.task, cv=min(self.cv or 5, 5))
            X = X[selected_cols]
            pre, num_cols, cat_cols, X = build_preprocessor(X, self.numeric_impute, self.categorical_impute, self.scale, self.one_hot, self.cat_min_freq)

        # split
        strat = y if self.task=="classification" and len(pd.Series(y).unique())>1 else None
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=self.test_size, random_state=self.random_state, stratify=strat)

        # sampler (SMOTE) with tiny-data protection
        sampler = None
        if self.task=="classification" and self.imbalance:
            if self.imbalance == "smote" or (self.imbalance=="auto" and HAS_IMB and len(y_tr)>=20):
                if HAS_IMB:
                    # compute minority count on the training fold
                    counts = pd.Series(y_tr).value_counts()
                    minority_n = int(counts.min())
                    k = min(self.smote_k_neighbors, max(1, minority_n-1))
                    if k >= 1 and minority_n >= 2:
                        sampler = SMOTE(random_state=self.random_state, k_neighbors=k)
                    else:
                        sampler = None  # too small; skip SMOTE

        zoo = classifiers() if self.task=="classification" else regressors()
        shortlist = default_shortlist(self.task)
        scoring = "accuracy" if self.task=="classification" else "r2"
        cv_obj = _cv(self.task, min(self.cv or 5, max(2, len(np.unique(y_tr))-1)) if self.task=="classification" else (self.cv or 5), True, self.random_state)

        def train_one(name):
            est = zoo[name]
            if self.task=="classification" and hasattr(est, "class_weight") and (self.imbalance in ("auto","class_weight")):
                try: est.set_params(class_weight="balanced")
                except Exception: pass
            # apply user params only to chosen model
            if self.params and (self.model == name):
                try: est.set_params(**self.params)
                except Exception: pass
            pipe = self._build_pipeline(est, pre, sampler)
            score, fitted = self._evaluate(pipe, X_tr, y_tr, scoring, cv_obj, name)
            return score, fitted

        tried = []
        if self.model != "auto":
            score, fitted = train_one(self.model)
            tried.append((self.model, score))
            best_name, best_score, best_pipe = self.model, score, fitted
            suggestions = []
            if self.advisor_threshold is not None and self.task=="classification" and (score < self.advisor_threshold):
                for name in shortlist:
                    if name == self.model: continue
                    s, _ = train_one(name)
                    suggestions.append((name, s))
                suggestions.sort(key=lambda x:x[1], reverse=True)
                advisor = {
                    "triggered": True,
                    "chosen_model_cv": score,
                    "threshold": self.advisor_threshold,
                    "suggestions": suggestions[:5],
                    "tips": [
                        "Reduce CV on tiny datasets (cv=3).",
                        "Turn off SMOTE or lower smote_k_neighbors=2..3.",
                        "Enable tune='random', n_iter=20–40.",
                        "Use feature_selection='mutual_info' (top_k=20–50).",
                        "Increase training data or add informative features.",
                    ]
                }
                if self.advisor_auto_fix and suggestions:
                    best_name, best_score = suggestions[0]
                    _, best_pipe = train_one(best_name)
            else:
                advisor = None
        else:
            advisor = None
            best_name, best_score, best_pipe = None, -1e9, None
            for name in shortlist:
                s, f = train_one(name)
                tried.append((name, s))
                if s > best_score:
                    best_name, best_score, best_pipe = name, s, f

        # holdout evaluation
        y_pred = best_pipe.predict(X_te)
        y_proba = None
        mdl = best_pipe.named_steps.get("model")
        if self.task=="classification" and hasattr(mdl, "predict_proba"):
            try: y_proba = best_pipe.predict_proba(X_te)
            except Exception: y_proba = None
        met = _compute_metrics(self.task, y_te, y_pred, y_proba, self.metrics)

        # plots & html
        plots = {}
        plots["target_distribution"] = plot_target_distribution(y, self.report_dir)
        plots["missingness"] = plot_missingness(self.df, self.report_dir)
        plots["corr_with_target"] = plot_corr(self.df, self.target, self.report_dir)
        try:
            prep = best_pipe.named_steps["prep"]
            feat_names = prep.get_feature_names_out() if hasattr(prep, "get_feature_names_out") else [f"f{i}" for i in range(1, 1+len(best_pipe[:-1].transform(X_te[:1])[0]))]
            plots["feature_importance"] = plot_feature_importance(mdl, feat_names, self.report_dir)
        except Exception:
            pass
        write_simple_html(self.report_dir, plots)

        # persist
        joblib.dump(best_pipe, os.path.join(self.report_dir, "pipeline.joblib"))
        with open(os.path.join(self.report_dir, "metrics.json"), "w") as f: json.dump(met, f, indent=2)
        with open(os.path.join(self.report_dir, "model.txt"), "w") as f: f.write(best_name or "unknown")
        with open(os.path.join(self.report_dir, "tried_models.json"), "w") as f: json.dump({"tried": tried}, f, indent=2)

        out = {"metrics": met, "cv_best_score": best_score, "best_model_name": best_name, "artifacts_dir": self.report_dir, "pipeline": best_pipe, "eda": eda}
        if 'advisor' in locals() and advisor is not None:
            out["advisor"] = advisor
        return out