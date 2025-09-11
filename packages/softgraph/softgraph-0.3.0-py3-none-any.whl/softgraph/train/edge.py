from __future__ import annotations
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from ..utils.metrics import edge_cls

def _edge_feats(X_nodes: pd.DataFrame, edges_df: pd.DataFrame, mode="hadamard"):
    feats, labels = [], []
    for _, r in edges_df.iterrows():
        u, v, s = int(r.u), int(r.v), int(r.sign)
        xu, xv = X_nodes.loc[u].values, X_nodes.loc[v].values
        f = xu * xv if mode == "hadamard" else np.concatenate([xu, xv])
        feats.append(f); labels.append(1 if s>0 else 0)
    return np.vstack(feats), np.array(labels)

def run(G, X_nodes: pd.DataFrame, edges_df: pd.DataFrame, model="logreg", test_size=0.2, random_state=42):
    X, y = _edge_feats(X_nodes, edges_df)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
    if model != "logreg":
        raise ValueError("only 'logreg' supported for edge classification in MVP")
    clf = LogisticRegression(max_iter=300)
    clf.fit(Xtr, ytr)
    yhat = clf.predict(Xte)
    metrics = edge_cls(yte, yhat)
    return {"task":"edge_classification", "model":clf, "X_test":pd.DataFrame(Xte), "y_test":yte, "y_pred":yhat, "metrics":metrics, "artifacts":{}}
