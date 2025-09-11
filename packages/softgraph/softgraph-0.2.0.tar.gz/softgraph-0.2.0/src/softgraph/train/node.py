from __future__ import annotations
import pandas as pd, numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from ..utils.metrics import node_cls

def run(X: pd.DataFrame, y, model="logreg", test_size=0.2, random_state=42):
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
    if model == "logreg":
        clf = LogisticRegression(max_iter=200)
    elif model == "rf":
        clf = RandomForestClassifier(n_estimators=200, random_state=random_state)
    else:
        raise ValueError("model must be 'logreg' or 'rf'")
    clf.fit(Xtr, ytr)
    yhat = clf.predict(Xte)
    metrics = node_cls(yte, yhat)
    return {"task":"node_classification", "model":clf, "X_test":Xte, "y_test":yte, "y_pred":yhat, "metrics":metrics, "artifacts":{}}
