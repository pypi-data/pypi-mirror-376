from __future__ import annotations
import numpy as np, pandas as pd
from collections import defaultdict

def run(train_events: pd.DataFrame, test_events: pd.DataFrame, topk=50):
    neigh = defaultdict(set)
    for _, r in train_events.iterrows():
        u, v = int(r.u), int(r.v)
        neigh[u].add(v); neigh[v].add(u)
    pairs = test_events[["u","v","t"]].drop_duplicates().reset_index(drop=True)
    scores = []
    for _, r in pairs.iterrows():
        u, v = int(r.u), int(r.v)
        s = len(neigh.get(u,set()) & neigh.get(v,set()))
        scores.append(s)
    df = pairs.assign(score=scores).sort_values("score", ascending=False).reset_index(drop=True)
    recall_at_k = float(df.head(topk).shape[0] / max(1, pairs.shape[0]))
    return {"task":"temporal_link_prediction", "metrics":{"recall_at_k": recall_at_k}, "scores": df.to_dict(orient="list"), "artifacts":{}}
