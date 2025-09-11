from __future__ import annotations
import pandas as pd, numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from ..utils.metrics import node_cls
from ..utils.viz import learning_curve as plot_learning_curve

def run(X: pd.DataFrame, y, model="logreg", test_size=0.2, random_state=42, curves=False, hidden=(128,64), **kwargs):
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
    if model == "logreg":
        clf = LogisticRegression(max_iter=300)
    elif model == "rf":
        clf = RandomForestClassifier(n_estimators=300, random_state=random_state)
    elif model == "mlp":
        clf = MLPClassifier(hidden_layer_sizes=hidden, activation="relu", solver="adam", max_iter=400, random_state=random_state)
    else:
        raise ValueError("model must be 'logreg', 'rf', or 'mlp'")
    clf.fit(Xtr, ytr)
    yhat = clf.predict(Xte)
    metrics = node_cls(yte, yhat)
    artifacts = {}
    if curves:
        try:
            fig = plot_learning_curve(clf, X, y)
            artifacts["learning_curve"] = fig
        except Exception:
            pass
    return {"task":"node_classification", "model":clf, "X_test":Xte, "y_test":yte, "y_pred":yhat, "metrics":metrics, "artifacts":artifacts}
