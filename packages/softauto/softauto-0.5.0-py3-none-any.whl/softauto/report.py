from __future__ import annotations
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import (
    confusion_matrix, roc_curve, auc, precision_recall_curve,
    average_precision_score
)
from sklearn.preprocessing import label_binarize

def plot_target_distribution(y, outdir, title="target_distribution"):
    try:
        plt.figure()
        if pd.api.types.is_numeric_dtype(y):
            plt.hist(y.dropna(), bins=20)
        else:
            counts = pd.Series(y).value_counts(dropna=False)
            plt.bar(counts.index.astype(str), counts.values)
            plt.xticks(rotation=45, ha='right')
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
        plt.bar(miss.index.astype(str), miss.values)
        plt.xticks(rotation=90)
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
        if target not in num.columns:
            return None
        corr = num.corr(numeric_only=True)[target].drop(target).sort_values(key=lambda s: s.abs(), ascending=False).head(30)
        plt.figure()
        plt.bar(corr.index.astype(str), corr.values)
        plt.xticks(rotation=90)
        plt.title("Correlation with target (numeric)")
        plt.tight_layout()
        path = os.path.join(outdir, f"{title}.png")
        plt.savefig(path, dpi=140)
        plt.close()
        return path
    except Exception:
        pass
    return None

def plot_feature_importance(model, feature_names, outdir, title="feature_importance"):
    try:
        import numpy as _np
        import matplotlib.pyplot as _plt
        importances = None
        if hasattr(model, "feature_importances_"):
            importances = getattr(model, "feature_importances_")
        elif hasattr(model, "coef_"):
            importances = getattr(model, "coef_")
            if getattr(importances, "ndim", 1) != 1:
                importances = _np.mean(_np.abs(importances), axis=0)
        if importances is None:
            return None
        order = _np.argsort(_np.abs(importances))[::-1][:30]
        names = _np.array(feature_names)[order]
        vals = _np.array(importances)[order]
        _plt.figure(figsize=(max(6, len(order)*0.25), 4))
        _plt.bar(range(len(order)), vals)
        _plt.xticks(range(len(order)), names, rotation=90)
        _plt.title("Top feature importance")
        _plt.tight_layout()
        path = os.path.join(outdir, f"{title}.png")
        _plt.savefig(path, dpi=140)
        _plt.close()
        return path
    except Exception:
        return None

def plot_confusion_matrix(y_true, y_pred, outdir, title="confusion_matrix"):
    try:
        labels = np.unique(np.concatenate([pd.Series(y_true).dropna().astype(str).unique(), pd.Series(y_pred).dropna().astype(str).unique()]))
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        plt.figure(figsize=(6,6))
        plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
        plt.title("Confusion matrix")
        plt.colorbar()
        tick_marks = np.arange(len(labels))
        plt.xticks(tick_marks, labels, rotation=45, ha='right')
        plt.yticks(tick_marks, labels)
        thresh = cm.max() / 2.
        for i, j in np.ndindex(cm.shape):
            plt.text(j, i, format(int(cm[i, j]), 'd'),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")
        plt.ylabel('True label')
        plt.xlabel('Predicted label')
        plt.tight_layout()
        path = os.path.join(outdir, f"{title}.png")
        plt.savefig(path, dpi=140)
        plt.close()
        return path
    except Exception:
        return None

def plot_roc_pr_curve(y_true, y_proba, outdir, title_prefix="roc_pr"):
    try:
        y_true = np.array(y_true)
        y_proba = np.array(y_proba)
        n_classes = 1 if y_proba.ndim == 1 else y_proba.shape[1]

        results = {}
        if n_classes == 1 or (y_proba.ndim == 2 and y_proba.shape[1] == 2):
            if y_proba.ndim == 2:
                probs = y_proba[:, 1]
            else:
                probs = y_proba
            fpr, tpr, _ = roc_curve(y_true, probs)
            roc_auc = auc(fpr, tpr)
            plt.figure()
            plt.plot(fpr, tpr, lw=2, label=f'ROC (AUC = {roc_auc:.3f})')
            plt.plot([0,1],[0,1],'k--', lw=1)
            plt.xlabel('False Positive Rate')
            plt.ylabel('True Positive Rate')
            plt.title('ROC Curve')
            plt.legend(loc='lower right')
            plt.tight_layout()
            roc_path = os.path.join(outdir, f"{title_prefix}_roc.png")
            plt.savefig(roc_path, dpi=140)
            plt.close()
            results['roc'] = roc_path

            precision, recall, _ = precision_recall_curve(y_true, probs)
            ap = average_precision_score(y_true, probs)
            plt.figure()
            plt.plot(recall, precision, lw=2, label=f'PR (AP = {ap:.3f})')
            plt.xlabel('Recall')
            plt.ylabel('Precision')
            plt.title('Precision-Recall Curve')
            plt.legend(loc='lower left')
            plt.tight_layout()
            pr_path = os.path.join(outdir, f"{title_prefix}_pr.png")
            plt.savefig(pr_path, dpi=140)
            plt.close()
            results['pr'] = pr_path
            return results

        else:
            classes = np.arange(y_proba.shape[1])
            try:
                Y = label_binarize(y_true, classes=classes)
            except Exception:
                Y = label_binarize(y_true, classes=np.unique(y_true))
            plt.figure(figsize=(6,4))
            for i in classes[:6]:
                fpr, tpr, _ = roc_curve(Y[:, i], y_proba[:, i])
                roc_auc = auc(fpr, tpr)
                plt.plot(fpr, tpr, lw=1.5, label=f'class {i} (AUC={roc_auc:.2f})')
            plt.plot([0,1],[0,1],'k--', lw=1)
            plt.xlabel('FPR'); plt.ylabel('TPR'); plt.title('ROC Curve (per-class)')
            plt.legend(loc='lower right', fontsize='small')
            plt.tight_layout()
            roc_path = os.path.join(outdir, f"{title_prefix}_roc_multiclass.png")
            plt.savefig(roc_path, dpi=140)
            plt.close()
            results['roc'] = roc_path

            plt.figure(figsize=(6,4))
            for i in classes[:6]:
                precision, recall, _ = precision_recall_curve(Y[:, i], y_proba[:, i])
                ap = average_precision_score(Y[:, i], y_proba[:, i])
                plt.plot(recall, precision, lw=1.5, label=f'class {i} (AP={ap:.2f})')
            plt.xlabel('Recall'); plt.ylabel('Precision'); plt.title('Precision-Recall (per-class)')
            plt.legend(loc='lower left', fontsize='small')
            plt.tight_layout()
            pr_path = os.path.join(outdir, f"{title_prefix}_pr_multiclass.png")
            plt.savefig(pr_path, dpi=140)
            plt.close()
            results['pr'] = pr_path
            return results
    except Exception:
        return {'roc': None, 'pr': None}

def plot_residuals(y_true, y_pred, outdir, title="residuals"):
    try:
        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        resid = y_true - y_pred
        plt.figure(figsize=(6,4))
        plt.scatter(y_pred, resid, alpha=0.6, s=10)
        plt.axhline(0, color='k', linestyle='--', linewidth=1)
        plt.xlabel('Predicted')
        plt.ylabel('Residual (true - pred)')
        plt.title('Residuals vs Predicted')
        plt.tight_layout()
        scatter_path = os.path.join(outdir, f"{title}.png")
        plt.savefig(scatter_path, dpi=140)
        plt.close()
        return scatter_path
    except Exception:
        return None

def plot_feature_selection_mi(X, y, task, outdir, top_k=30, title="mutual_info"):
    try:
        from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
        X_enc = X.copy()
        num_cols = X_enc.select_dtypes(include=np.number).columns.tolist()
        cat_cols = [c for c in X_enc.columns if c not in num_cols]
        for c in cat_cols:
            X_enc[c] = X_enc[c].astype('category').cat.codes
        if task == 'classification':
            scores = mutual_info_classif(X_enc, y, discrete_features=[c not in num_cols for c in X_enc.columns], random_state=42)
        else:
            scores = mutual_info_regression(X_enc, y, discrete_features=[c not in num_cols for c in X_enc.columns], random_state=42)
        mi = pd.Series(scores, index=X_enc.columns).sort_values(ascending=False)
        top = mi.head(min(top_k, len(mi)))
        plt.figure(figsize=(max(6, len(top)*0.25), 4))
        plt.bar(top.index.astype(str), top.values)
        plt.xticks(rotation=90)
        plt.title('Mutual information (top features)')
        plt.tight_layout()
        path = os.path.join(outdir, f"{title}.png")
        plt.savefig(path, dpi=140)
        plt.close()
        return path
    except Exception:
        return None

# report.py: replace write_simple_html()
def write_simple_html(outdir, artifacts: dict):
    path = os.path.join(outdir, "report.html")
    html = [
        "<html><head><meta charset='utf-8'><title>softauto report</title>",
        "<style>body{font-family:system-ui,Segoe UI,Roboto,Arial;margin:16px;}"
        "h1{margin:0 0 8px} h2{margin-top:24px}"
        "details{border:1px solid #ddd;border-radius:8px;padding:10px;margin:8px 0;}"
        "summary{font-weight:600;cursor:pointer}"
        "img{max-width:100%} pre{white-space:pre-wrap;word-break:break-word}</style>",
        "</head><body>",
        "<h1>softauto report</h1>"
    ]
    for k, v in artifacts.items():
        if isinstance(v, str) and v.endswith(".png") and os.path.exists(v):
            html.append(f"<h2>{k}</h2><img src='{os.path.basename(v)}'/>")
        elif isinstance(v, dict):
            import json
            html.append(f"<details open><summary>{k}</summary><pre>{json.dumps(v, indent=2)}</pre></details>")
        else:
            # fallback
            html.append(f"<details><summary>{k}</summary><pre>{str(v)}</pre></details>")
    html.append("</body></html>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    return path

