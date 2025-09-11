from __future__ import annotations
import numpy as np, pandas as pd, networkx as nx
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

def _spectral_features(G: nx.Graph, k: int = 8) -> pd.DataFrame:
    nodes = sorted(G.nodes())
    if len(nodes) == 0:
        return pd.DataFrame(index=[])
    A = nx.to_scipy_sparse_array(G, nodelist=nodes, dtype=float, format="csr")
    deg = np.array(A.sum(1)).ravel()
    invsqrt = 1.0 / np.sqrt(np.maximum(deg, 1e-12))
    Dhalf = sp.diags(invsqrt)
    L = sp.eye(A.shape[0]) - Dhalf @ A @ Dhalf
    k_eff = min(max(k + 1, 2), max(2, A.shape[0]))
    vals, vecs = eigsh(L, k=k_eff, which="SM")
    if vecs.shape[1] > 1:
        Xspec = pd.DataFrame(vecs[:, 1:], index=nodes)
        Xspec.columns = [f"spec{i}" for i in range(1, Xspec.shape[1] + 1)]
    else:
        Xspec = pd.DataFrame(index=nodes)
    return Xspec

def node_features(G: nx.Graph, mode: str = "degree+pagerank+cluster", noise: float = 0.0) -> pd.DataFrame:
    nodes = sorted(G.nodes())
    X = pd.DataFrame(index=nodes)
    parts = [m.strip().lower() for m in mode.split("+") if m.strip()]
    if "degree" in parts:
        X["deg"] = pd.Series(dict(G.degree()), dtype=float).reindex(nodes)
    if "pagerank" in parts:
        X["pr"] = pd.Series(nx.pagerank(G), dtype=float).reindex(nodes)
    if "cluster" in parts:
        X["clust"] = pd.Series(nx.clustering(G), dtype=float).reindex(nodes)
    for p in parts:
        if p.startswith("spectral"):
            try:
                k = int(p.split(":", 1)[1])
            except Exception:
                k = 8
            X = X.join(_spectral_features(G, k=k), how="left")
    if X.shape[1] == 0:
        X["deg"] = pd.Series(dict(G.degree()), dtype=float).reindex(nodes)
    if noise > 0.0 and X.shape[1] > 0:
        rng = np.random.default_rng(0)
        X = X + noise * rng.normal(size=X.shape)
    return X.fillna(0.0)
