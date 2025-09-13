# softauto 0.6.0 — Advising‑first AutoML

**softauto** is a light, zero‑boilerplate AutoML toolkit that starts with **AI advice**: it inspects your dataframe, infers the task, suggests preprocessing & model shortlists, then trains, evaluates, and saves the best pipeline — with plots and a JSON summary.

- ✅ **Advisor**: suggests task, preprocessing, feature selection, PCA, and model shortlists (with reasons)
- ✅ **User‑choice or Auto**: pass a model name or let softauto pick
- ✅ **EDA**: target distribution, missingness, correlation matrix
- ✅ **Preprocessing**: impute, encode, scale, rare‑category binning, outlier clip
- ✅ **Selection/Extraction**: Mutual Info, RFECV, PCA
- ✅ **Training/Testing**: robust CV, leaderboard, hold‑out metrics, artifacts + saved model
- ✅ **Boosters optional**: XGBoost, LightGBM, CatBoost auto‑detected (no hard dependency)
- ✅ **Tiny API**: `autorun(df, target, task=...)` or `Runner(...).fit()`

---

## Installation

**Core (lightweight):**
```bash
pip install softauto
```

**With boosters & imbalance extras:**
```bash
pip install "softauto[all]"
# or pick subsets:
# pip install "softauto[boosters]"
# pip install "softauto[imbalance]"
```

> Boosters are optional; if not present they’re skipped silently.

---

## Quick Start (Classification)

```python
import pandas as pd
from sklearn.datasets import load_breast_cancer
from softauto import autorun

cancer = load_breast_cancer(as_frame=True)
df = cancer.frame.copy()
df.rename(columns={"target":"target"}, inplace=True)

res = autorun(df, target="target", task="classification", report_dir="report_cls", model="auto")
print(res["best_model"], res["test_metrics"])
# Artifacts in report_cls/: target_dist.png, missingness.png, corr_matrix.png, best_<model>.joblib, summary.json
```

## Quick Start (Regression)

```python
from sklearn.datasets import fetch_california_housing
from softauto import autorun
cal = fetch_california_housing(as_frame=True)
df = cal.frame.copy()
df["target"] = df["MedHouseVal"]; df = df.drop(columns=["MedHouseVal"])

res = autorun(df, target="target", task="regression", report_dir="report_reg", model="auto")
print(res["best_model"], res["test_metrics"])
```

---

## API

### `autorun(df, target, task=None, **kwargs) -> dict`
Single‑shot run. Returns a summary dict with:
- `task`, `best_model`, `cv_leaderboard`, `test_metrics`
- `artifacts` (plot paths), `model_path`, `advisor_notes`, `selected_features`

Common kwargs:
- `report_dir="softauto_artifacts"`, `random_state=42`, `test_size=0.2`
- `model="auto"` or list/str of model names (`"random_forest"`, `"logreg"`, `"xgb"`, `"lgbm"`, `"catboost"`, ...)
- Preprocess: `scale`, `one_hot`, `cat_min_freq`, `numeric_impute`, `categorical_impute`
- Selection: `feature_selection=("mutual_info"|"rfecv"|None)`, `top_k_features`, `pca_components`
- CV: `cv=5`

### `Runner`
```python
from softauto import Runner
r = Runner(df, target="target", task="classification", report_dir="report")
summary = r.fit()
y_pred = r.predict(r.X_test_)  # after fit
```

---

## Artifacts

- `target_dist.png` — class/target distribution
- `missingness.png` — top-30 missing rates
- `corr_matrix.png` — numeric correlation heatmap (skips if target not numeric)
- `best_<model>.joblib` — saved sklearn pipeline
- `summary.json` — complete run data

---

## Model Names

Classification: `logreg`, `random_forest`, `gb`, `svm_rbf`, `knn`, `mlp`, (`xgb`, `lgbm`, `catboost` if installed)  
Regression: `linear`, `ridge`, `lasso`, `random_forest`, `gb`, `svr_rbf`, `knn`, `mlp`, (`xgb`, `lgbm`, `catboost`)

---

## License
MIT © Soft Tech Talks
