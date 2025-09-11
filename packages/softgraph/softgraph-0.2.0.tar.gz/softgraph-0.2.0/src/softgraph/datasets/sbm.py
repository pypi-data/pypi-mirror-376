from __future__ import annotations
import numpy as np, networkx as nx

def sbm(n=600, k=4, p_in=0.09, p_out=0.02, random_state=None):
    rng = np.random.default_rng(random_state)
    sizes = [n // k] * k
    sizes[0] += n - sum(sizes)
    P = np.full((k, k), p_out, dtype=float)
    np.fill_diagonal(P, p_in)
    G = nx.stochastic_block_model(sizes, P, seed=random_state)
    # labels
    y = []
    for b, sz in enumerate(sizes):
        y += [b] * sz
    # relabel nodes to 0..n-1
    mapping = {node: i for i, node in enumerate(G.nodes())}
    G = nx.relabel_nodes(G, mapping, copy=True)
    return G, np.array(y, dtype=int)
