from __future__ import annotations
from typing import Dict, Any
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor

def classifiers() -> Dict[str, Any]:
    return {
        "logreg": LogisticRegression(max_iter=1000),
        "random_forest": RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1),
        "gb": GradientBoostingClassifier(),
        "svm_rbf": SVC(kernel="rbf", probability=True),
        "knn": KNeighborsClassifier(),
        "mlp": MLPClassifier(hidden_layer_sizes=(128, ), max_iter=400),
    }

def regressors() -> Dict[str, Any]:
    return {
        "linear": LinearRegression(),
        "ridge": Ridge(alpha=1.0),
        "lasso": Lasso(alpha=0.001, max_iter=10000),
        "random_forest": RandomForestRegressor(n_estimators=400, random_state=42, n_jobs=-1),
        "gb": GradientBoostingRegressor(),
        "svr_rbf": SVR(kernel="rbf"),
        "knn": KNeighborsRegressor(),
        "mlp": MLPRegressor(hidden_layer_sizes=(128, ), max_iter=500),
    }

def default_shortlist(task: str):
    return (["random_forest", "logreg", "gb", "svm_rbf", "knn", "mlp"]
            if task=="classification" else
            ["random_forest", "linear", "ridge", "gb", "svr_rbf", "knn", "mlp"])