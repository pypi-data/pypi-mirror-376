import pandas as pd
from softauto import AutoRun

df = pd.DataFrame({
    "age": [22,35,44,52,30,27,41,19,26,38,21,33,29,48,36,40],
    "city": ["Pune","Mumbai","Delhi","Pune","Delhi","Mumbai","Pune","Delhi","Pune","Mumbai","Delhi","Pune","Pune","Mumbai","Delhi","Pune"],
    "income": [35000,72000,54000,120000,41000,52000,60000,33000,48000,90000,36000,70000,62000,83000,45000,68000],
    "label": [0,1,1,1,0,0,1,0,0,1,0,1,1,1,0,1],
})

run = AutoRun(
  df, target="label", task="classification",
  model="logreg", cv=5, tune="random", n_iter=10,
  feature_selection="mutual_info", top_k_features=10,
  cat_min_freq=0.05, num_clip_quantiles=(0.02, 0.98),
  plots=True, advisor_threshold=0.75, advisor_auto_fix=True,
  imbalance="auto", smote_k_neighbors=2
)
res = run.fit()
print("Best:", res["best_model_name"], "CV:", res["cv_best_score"])
print("Holdout:", res["metrics"])
print("Advisor:", res.get("advisor"))
print("Artifacts:", res["artifacts_dir"])