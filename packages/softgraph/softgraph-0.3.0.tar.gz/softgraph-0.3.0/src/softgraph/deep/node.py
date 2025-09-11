from __future__ import annotations
import numpy as np, torch

def _require_torch_geometric():
    try:
        import torch_geometric  # noqa: F401
        from torch_geometric.nn import GCNConv, SAGEConv
        return True
    except Exception:
        return False

def _nx_to_pyg(G, X, y):
    import torch, numpy as np, networkx as nx
    nodes = sorted(G.nodes())
    idx = {u:i for i,u in enumerate(nodes)}
    edges = [(idx[u], idx[v]) for u,v in G.edges()]
    if len(edges) == 0:
        edge_index = torch.zeros((2,0), dtype=torch.long)
    else:
        src = [u for u,v in edges] + [v for u,v in edges]
        dst = [v for u,v in edges] + [u for u,v in edges]
        edge_index = torch.tensor([src, dst], dtype=torch.long)
    X = torch.tensor(X.sort_index().values, dtype=torch.float32)
    y = torch.tensor(np.asarray(y)[np.argsort(nodes)], dtype=torch.long)
    return X, y, edge_index

class _GCN(torch.nn.Module):
    def __init__(self, in_dim, hidden=64, out_dim=None, layers=2, dropout=0.5):
        super().__init__()
        from torch_geometric.nn import GCNConv
        self.convs = torch.nn.ModuleList([GCNConv(in_dim, hidden)] + [GCNConv(hidden, hidden) for _ in range(layers-2)] + [GCNConv(hidden, out_dim)])
        self.dropout = torch.nn.Dropout(dropout); self.act = torch.nn.ReLU()
    def forward(self, x, edge_index):
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            if i < len(self.convs)-1: x = self.act(x); x = self.dropout(x)
        return x

class _SAGE(torch.nn.Module):
    def __init__(self, in_dim, hidden=64, out_dim=None, layers=2, dropout=0.5):
        super().__init__()
        from torch_geometric.nn import SAGEConv
        self.convs = torch.nn.ModuleList([SAGEConv(in_dim, hidden)] + [SAGEConv(hidden, hidden) for _ in range(layers-2)] + [SAGEConv(hidden, out_dim)])
        self.dropout = torch.nn.Dropout(dropout); self.act = torch.nn.ReLU()
    def forward(self, x, edge_index):
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            if i < len(self.convs)-1: x = self.act(x); x = self.dropout(x)
        return x

def train_node(G, X, y, kind="gcn", epochs=100, lr=0.01, hidden=64, layers=2, dropout=0.5, random_state=42):
    if not _require_torch_geometric():
        raise ImportError("GCN/SAGE require torch-geometric. Install torch + torch-geometric and retry.")
    import torch
    torch.manual_seed(random_state)
    X_t, y_t, edge_index = _nx_to_pyg(G, X, y)
    n_classes = int(y_t.max().item() + 1)
    model = _GCN(X_t.size(1), hidden=hidden, out_dim=n_classes, layers=layers, dropout=dropout) if kind=="gcn" else _SAGE(X_t.size(1), hidden=hidden, out_dim=n_classes, layers=layers, dropout=dropout)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=5e-4)
    loss_fn = torch.nn.CrossEntropyLoss()
    n = X_t.size(0); idx = torch.randperm(n); n_tr = int(0.8 * n)
    train_idx, test_idx = idx[:n_tr], idx[n_tr:]
    for _ in range(epochs):
        model.train(); opt.zero_grad()
        out = model(X_t, edge_index)
        loss = loss_fn(out[train_idx], y_t[train_idx])
        loss.backward(); opt.step()
    model.eval()
    with torch.no_grad():
        logits = model(X_t, edge_index)
        yhat = logits[test_idx].argmax(dim=1).cpu().numpy()
        ytrue = y_t[test_idx].cpu().numpy()
    return ytrue, yhat, model
