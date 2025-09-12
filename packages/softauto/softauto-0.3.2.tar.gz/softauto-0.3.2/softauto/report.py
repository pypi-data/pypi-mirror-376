from __future__ import annotations
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def plot_target_distribution(y, outdir, title="target_distribution"):
    try:
        plt.figure()
        if pd.api.types.is_numeric_dtype(y):
            y.plot(kind="hist", bins=20)
        else:
            y.value_counts(dropna=False).plot(kind="bar")
        plt.title("Target distribution")
        plt.tight_layout()
        path = os.path.join(outdir, f"{title}.png")
        plt.savefig(path, dpi=140)
        plt.close()
        return path
    except Exception:
        return None

def plot_missingness(df, outdir, title="missingness"):
    try:
        miss = df.isna().mean().sort_values(ascending=False).head(30)
        plt.figure()
        miss.plot(kind="bar")
        plt.title("Missingness (top 30)")
        plt.tight_layout()
        path = os.path.join(outdir, f"{title}.png")
        plt.savefig(path, dpi=140)
        plt.close()
        return path
    except Exception:
        return None

def plot_corr(df, target, outdir, title="correlation_with_target"):
    try:
        num = df.select_dtypes(include=np.number)
        if target in num:
            corr = num.corr(numeric_only=True)[target].drop(target).sort_values(key=lambda s: s.abs(), ascending=False).head(30)
            plt.figure()
            corr.plot(kind="bar")
            plt.title("Correlation with target (numeric)")
            plt.tight_layout()
            path = os.path.join(outdir, f"{title}.png")
            plt.savefig(path, dpi=140)
            plt.close()
            return path
    except Exception:
        return None
    return None

def plot_feature_importance(model, feature_names, outdir, title="feature_importance"):
    try:
        importances = None
        if hasattr(model, "feature_importances_"):
            importances = getattr(model, "feature_importances_")
        elif hasattr(model, "coef_"):
            importances = getattr(model, "coef_")
            import numpy as np
            if getattr(importances, "ndim", 1) != 1:
                importances = np.mean(np.abs(importances), axis=0)
        if importances is None:
            return None
        import numpy as np
        order = np.argsort(np.abs(importances))[::-1][:30]
        names = np.array(feature_names)[order]
        vals = np.array(importances)[order]
        import matplotlib.pyplot as plt
        plt.figure()
        plt.bar(range(len(order)), vals)
        plt.xticks(range(len(order)), names, rotation=90)
        plt.title("Top feature importance")
        plt.tight_layout()
        path = os.path.join(outdir, f"{title}.png")
        plt.savefig(path, dpi=140)
        plt.close()
        return path
    except Exception:
        return None

def write_simple_html(outdir, artifacts: dict):
    path = os.path.join(outdir, "report.html")
    html = ["<html><head><meta charset='utf-8'><title>softauto report</title></head><body>",
            "<h1>softauto report</h1>"]
    for k,v in artifacts.items():
        if isinstance(v, str) and v.endswith(".png") and os.path.exists(v):
            html.append(f"<h2>{k}</h2><img src='{os.path.basename(v)}' style='max-width:100%;'/>")
        elif isinstance(v, dict):
            html.append(f"<h2>{k}</h2><pre>{v}</pre>")
    html.append("</body></html>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    return path