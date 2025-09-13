from __future__ import annotations
from typing import List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, MinMaxScaler, RobustScaler
from sklearn.impute import SimpleImputer
import sklearn

def rare_category_binner(series: pd.Series, min_freq: float = 0.01, other_label: str = "__RARE__") -> pd.Series:
    if series.dtype.kind in "OUS":
        freq = series.value_counts(normalize=True, dropna=False)
        keep = freq[freq >= min_freq].index
        return series.where(series.isin(keep), other_label)
    return series

def clip_outliers(df: pd.DataFrame, num_cols: List[str], q_low: float = 0.01, q_high: float = 0.99) -> pd.DataFrame:
    if not num_cols:
        return df
    low = df[num_cols].quantile(q_low)
    high = df[num_cols].quantile(q_high)
    out = df.assign(**{c: df[c].clip(lower=low[c], upper=high[c]) for c in num_cols})
    return out.infer_objects(copy=False)

def _onehot_kwargs():
    major, minor, *_ = map(int, sklearn.__version__.split("."))
    return {"sparse_output": False} if (major > 1 or (major == 1 and minor >= 2)) else {"sparse": False}

def build_preprocessor(
    X: pd.DataFrame,
    numeric_impute: str = "median",
    categorical_impute: str = "most_frequent",
    scale: Optional[str] = "standard",
    one_hot: bool = True,
    cat_min_freq: Optional[float] = None
) -> Tuple[ColumnTransformer, List[str], List[str], pd.DataFrame]:
    num_cols = X.select_dtypes(include=np.number).columns.tolist()
    cat_cols = X.select_dtypes(exclude=np.number).columns.tolist()

    X_mod = X.copy()
    if cat_min_freq is not None and cat_cols:
        for c in cat_cols:
            X_mod[c] = rare_category_binner(X_mod[c], min_freq=cat_min_freq)

    num_steps = [("impute", SimpleImputer(strategy=numeric_impute))]
    if scale == "standard": num_steps.append(("scale", StandardScaler()))
    elif scale == "minmax": num_steps.append(("scale", MinMaxScaler()))
    elif scale == "robust": num_steps.append(("scale", RobustScaler()))

    cat_steps = [("impute", SimpleImputer(strategy=categorical_impute))]
    if one_hot:
        cat_steps.append(("onehot", OneHotEncoder(handle_unknown="ignore", **_onehot_kwargs())))

    pre = ColumnTransformer(
        transformers=[
            ("num", Pipeline(num_steps), num_cols),
            ("cat", Pipeline(cat_steps), cat_cols),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return pre, num_cols, cat_cols, X_mod
