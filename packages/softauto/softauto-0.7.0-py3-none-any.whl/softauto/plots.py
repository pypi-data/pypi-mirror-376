from __future__ import annotations
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def target_distribution(y, outdir, name="target_dist.png"):
    os.makedirs(outdir, exist_ok=True)
    plt.figure()
    if pd.api.types.is_numeric_dtype(y):
        plt.hist(pd.Series(y).dropna(), bins=20)
    else:
        c = pd.Series(y).astype(str).value_counts(dropna=False)
        plt.bar(c.index, c.values); plt.xticks(rotation=45, ha="right")
    plt.title("Target distribution"); plt.tight_layout()
    path = os.path.join(outdir, name)
    plt.savefig(path, dpi=140); plt.close()
    return path

def missingness(df, outdir, name="missingness.png"):
    os.makedirs(outdir, exist_ok=True)
    miss = df.isna().mean().sort_values(ascending=False).head(30)
    plt.figure()
    plt.bar(miss.index.astype(str), miss.values)
    plt.xticks(rotation=90); plt.title("Missingness (top 30)"); plt.tight_layout()
    path = os.path.join(outdir, name)
    plt.savefig(path, dpi=140); plt.close()
    return path

def corr_matrix(df, target, outdir, name="corr_matrix.png"):
    os.makedirs(outdir, exist_ok=True)
    num = df.select_dtypes(include=np.number)
    if target not in num.columns:
        return None
    corr = num.corr(numeric_only=True)
    plt.figure(figsize=(6,5))
    plt.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    plt.xticks(range(len(corr.columns)), corr.columns, rotation=90)
    plt.yticks(range(len(corr.index)), corr.index)
    plt.colorbar(); plt.title("Correlation matrix (numeric)"); plt.tight_layout()
    path = os.path.join(outdir, name)
    plt.savefig(path, dpi=140); plt.close()
    return path
