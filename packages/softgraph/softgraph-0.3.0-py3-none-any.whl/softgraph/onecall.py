from __future__ import annotations
from typing import Optional
from .datasets.sbm import sbm
from .datasets.signed import signed_sbm
from .datasets.temporal import temporal_contacts
from .datasets.features import node_features
from .train import node as train_node
from .train import edge as train_edge
from .train import temporal as train_temporal
from .utils.viz import confusion as _plot_conf
from .deep.node import train_node as _deep_node_train
from .utils.metrics import node_cls

def softgraph(task: str,
              dataset: str,
              n: int = 600,
              k: int = 4,
              p_in: float = 0.09,
              p_out: float = 0.02,
              pos_in: float = 0.12,
              neg_out: float = 0.05,
              horizon: int = 40,
              base_rate: float = 0.002,
              homophily: float = 0.7,
              random_state: Optional[int] = None,
              features: str = "degree+pagerank+cluster",
              model: str = "logreg",           # logreg | rf | mlp | gcn | sage
              test_size: float = 0.2,
              plot: bool = False,
              curves: bool = False,
              epochs: int = 100,
              lr: float = 0.01,
              hidden = 64,
              layers: int = 2,
              dropout: float = 0.5,
              **kwargs):
    task = task.lower().strip()
    dataset = dataset.lower().strip()

    if task == "node_classification":
        if dataset != "sbm":
            raise ValueError("node_classification currently supports dataset='sbm'")
        G, y = sbm(n=n, k=k, p_in=p_in, p_out=p_out, random_state=random_state)
        X = node_features(G, mode=features)

        if model in {"logreg", "rf", "mlp"}:
            run = train_node.run(X, y, model=model, test_size=test_size, random_state=random_state, curves=curves, hidden=hidden)
            if plot:
                _plot_conf(run["y_test"], run["y_pred"], title="Node Classification")
            return run
        elif model in {"gcn", "sage"}:
            y_true, y_pred, mdl = _deep_node_train(G, X, y, kind=model, epochs=epochs, lr=lr, hidden=(hidden if isinstance(hidden,int) else 64), layers=layers, dropout=dropout, random_state=random_state or 42)
            run = {"task":"node_classification", "model":mdl, "y_test":y_true, "y_pred":y_pred, "metrics":{}, "artifacts":{}}
            run["metrics"] = node_cls(y_true, y_pred)
            if plot:
                _plot_conf(y_true, y_pred, title=f"Node Classification ({model.upper()})")
            return run
        else:
            raise ValueError("model must be one of: logreg, rf, mlp, gcn, sage")

    elif task == "edge_classification":
        if dataset != "signed_sbm":
            raise ValueError("edge_classification currently supports dataset='signed_sbm'")
        G, edges = signed_sbm(n=n, k=k, pos_in=pos_in, neg_out=neg_out, random_state=random_state)
        X = node_features(G, mode=features)
        run = train_edge.run(G, X, edges, model="logreg", test_size=test_size, random_state=random_state)
        return run

    elif task == "temporal_link_prediction":
        if dataset != "temporal_contacts":
            raise ValueError("temporal_link_prediction currently supports dataset='temporal_contacts'")
        events = temporal_contacts(n=n, horizon=horizon, base_rate=base_rate, homophily=homophily, random_state=random_state)
        t_max = int(events["t"].max()) if len(events) else 0
        t_cut = int(t_max * 0.8)
        tr = events[events["t"] <= t_cut].reset_index(drop=True)
        te = events[events["t"] > t_cut].reset_index(drop=True)
        run = train_temporal.run(tr, te, topk=kwargs.get("topk", 50))
        return run

    else:
        raise ValueError("Unknown task. Use one of: node_classification, edge_classification, temporal_link_prediction")
