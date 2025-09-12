# example_run.py
import pandas as pd
from sklearn.datasets import make_classification
from softauto.autorun import AutoRun

# ---- Step 1: make a toy dataset ----
X, y = make_classification(
    n_samples=200,
    n_features=10,
    n_informative=5,
    n_redundant=2,
    weights=[0.9, 0.1],  # imbalanced
    random_state=42
)

df = pd.DataFrame(X, columns=[f"feat{i}" for i in range(10)])
df["label"] = y

# Add an ID-like column (to trigger Leakage Guard)
df["id"] = range(len(df))

# ---- Step 2: run AutoRun ----
run = AutoRun(
    df=df,
    target="label",
    task="classification",
    model="auto",            # try multiple models
    tune=None,               # or "random"
    report_dir="demo_artifacts"
)

results = run.fit()

# ---- Step 3: view results ----
print("Best model:", results["best_model_name"])
print("Metrics:", results["metrics"])

# Advisor (if triggered)
if "advisor" in results:
    print("Advisor suggestions:", results["advisor"])

print("\nArtifacts saved to:", results["artifacts_dir"])
print("Open report.html in a browser to view plots + Data Doctor + Leakage Guard.")

# ---- Step 4: check experiment log ----
with open("demo_artifacts/softauto_runs.jsonl") as f:
    lines = f.readlines()
    print("\nExperiment log (last entry):")
    print(lines[-1])
