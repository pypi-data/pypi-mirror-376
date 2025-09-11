from __future__ import annotations
import numpy as np, pandas as pd, networkx as nx

def signed_sbm(n=500, k=3, pos_in=0.12, neg_out=0.05, random_state=None):
    sizes = [n // k] * k
    sizes[0] += n - sum(sizes)
    P = np.full((k, k), neg_out, dtype=float)
    np.fill_diagonal(P, pos_in)
    G = nx.stochastic_block_model(sizes, P, seed=random_state)
    block_of = {}
    idx = 0
    for b, sz in enumerate(sizes):
        for _ in range(sz):
            block_of[idx] = b
            idx += 1
    rows = []
    for u, v in G.edges():
        sign = 1 if block_of[u] == block_of[v] else -1
        rows.append((u, v, sign))
    edges = pd.DataFrame(rows, columns=["u","v","sign"])
    return G, edges
