# softauto 0.3.1 – tiny-data safe SMOTE, advisor, plots
# softauto 0.3.2 (Pro+Fix)

**EDA → Clean → Select → Train → Tune → Plot → Advise**  
A lightweight AutoML helper that makes it easy to run an end-to-end experiment with just one call.

---

## ✨ Features
- **Model Zoo** (classification & regression):  
  `logreg`, `linear`, `ridge`, `lasso`, `random_forest`, `gb`, `svm_rbf`, `knn`, `mlp`  
  *(XGBoost / LightGBM available if installed).*

- **Preprocessing**
  - Missing-value imputation (median / most_frequent).
  - Scaling: `standard`, `minmax`, `robust`, or `None`.
  - Rare-category binning (`cat_min_freq=...`).
  - Outlier clipping (`num_clip_quantiles=(low, high)`).

- **Feature Selection**
  - `mutual_info` → keep top-k informative features.
  - `rfecv` → recursive elimination with CV.

- **Imbalance Handling**
  - `imbalance="auto"` → tries SMOTE (safe on small folds) else falls back to class weights.
  - `imbalance="class_weight"` or `"smote"` explicit.
  - New: `smote_k_neighbors` param (default 5, auto-reduced on small datasets).

- **Advisor**
  - If user-chosen model underperforms (e.g., accuracy < 0.75), evaluates a shortlist and:
    - Returns best alternatives.
    - Suggests practical tuning/feature/imbalance tips.
    - Auto-fixes to best alternative if `advisor_auto_fix=True`.

- **Plots & Report**
  - Target distribution, missingness, correlation, feature importance.
  - Auto-generated `report.html` with embedded charts.

- **Tuning**
  - Lightweight `RandomizedSearchCV` with sensible param grids.
  - Safe defaults (`error_score=0.0` → failed folds don’t crash).

---

## 🔧 Install
```bash
pip install -e .
# optional extras:
pip install -e .[boosters]   # xgboost, lightgbm
pip install -e .[imbalance]  # imbalanced-learn for SMOTE
