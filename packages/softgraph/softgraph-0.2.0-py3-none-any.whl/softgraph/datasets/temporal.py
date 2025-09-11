from __future__ import annotations
import numpy as np, pandas as pd

def temporal_contacts(n=400, horizon=40, base_rate=0.002, homophily=0.7, random_state=None):
    rng = np.random.default_rng(random_state)
    groups = rng.integers(0, 2, size=n)
    rows = []
    for t in range(horizon):
        lam = base_rate * n * np.log1p(n)
        m = rng.poisson(lam)
        for _ in range(m):
            if rng.random() < homophily:
                g = rng.integers(0, 2)
                cand = np.where(groups == g)[0]
                if len(cand) >= 2:
                    u, v = rng.choice(cand, 2, replace=False)
                else:
                    u, v = rng.integers(0, n, 2)
            else:
                u, v = rng.integers(0, n, 2)
            if u == v: 
                continue
            rows.append((int(u), int(v), int(t)))
    return pd.DataFrame(rows, columns=["u","v","t"]).sort_values("t").reset_index(drop=True)
