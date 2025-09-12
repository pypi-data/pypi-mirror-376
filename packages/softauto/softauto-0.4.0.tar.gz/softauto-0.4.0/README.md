# 🪶 softauto — AutoML with seatbelts

> AutoML that **respects small, messy, real-world datasets.**  
> One line in → a trained pipeline, metrics, and a human-readable report out.

---

## ✨ Why softauto?

Most AutoML libraries brute-force models until something sticks.  
**softauto is different:**

- 🧑‍🏫 **Advisor mode** – if your model underperforms, it suggests fixes (or auto-switches).  
- ⚖️ **Safe imbalance handling** – SMOTE applied *only* when statistically valid, else falls back to class weights.  
- 🧹 **Robust preprocessing** – rare category binning, outlier clipping, flexible scalers.  
- 🔍 **Smart feature selection** – Mutual Information & RFECV options.  
- 📊 **Automatic reporting** – HTML + plots (target distribution, missingness, correlations, feature importances).  
- 🎯 **Opinionated model zoo** – Random Forest, GB, SVM, KNN, MLP, Ridge/Lasso, all with tuned search spaces.  

---

## 🚀 Quickstart

```python
import pandas as pd
from softauto.autorun import AutoRun

# load your dataset
df = pd.read_csv("mydata.csv")

# run softauto
run = AutoRun(df=df, target="label", task="classification")
results = run.fit()

print(results["metrics"])        # final holdout metrics
print(results["best_model_name"])# chosen model
print(results["artifacts_dir"])  # directory with reports + plots
```