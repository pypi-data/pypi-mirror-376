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

def softgraph(task: str,
              dataset: str,
              # common dataset kwargs
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
              # features / models
              features: str = "degree+pagerank+cluster",
              model: str = "logreg",
              test_size: float = 0.2,
              plot: bool = False,
              **kwargs):
    """One-call API. Examples:
    softgraph(task="node_classification", dataset="sbm", n=600, k=4, p_in=0.09, p_out=0.02, features="degree+pagerank", model="logreg", plot=True)
    softgraph(task="edge_classification", dataset="signed_sbm", n=500, k=3)
    softgraph(task="temporal_link_prediction", dataset="temporal_contacts", n=400, horizon=40)
    """

    task = task.lower().strip()
    dataset = dataset.lower().strip()

    if task == "node_classification":
        if dataset != "sbm":
            raise ValueError("node_classification currently supports dataset='sbm'")
        G, y = sbm(n=n, k=k, p_in=p_in, p_out=p_out, random_state=random_state)
        X = node_features(G, mode=features)
        run = train_node.run(X, y, model=model, test_size=test_size, random_state=random_state)
        if plot:
            _plot_conf(run["y_test"], run["y_pred"], title="Node Classification")
        return run

    elif task == "edge_classification":
        if dataset != "signed_sbm":
            raise ValueError("edge_classification currently supports dataset='signed_sbm'")
        G, edges = signed_sbm(n=n, k=k, pos_in=pos_in, neg_out=neg_out, random_state=random_state)
        X = node_features(G, mode=features)
        run = train_edge.run(G, X, edges, model=model, test_size=test_size, random_state=random_state)
        return run

    elif task == "temporal_link_prediction":
        if dataset != "temporal_contacts":
            raise ValueError("temporal_link_prediction currently supports dataset='temporal_contacts'")
        events = temporal_contacts(n=n, horizon=horizon, base_rate=base_rate, homophily=homophily, random_state=random_state)
        # simple 80/20 time split
        t_max = int(events["t"].max())
        t_cut = int(t_max * 0.8)
        tr = events[events["t"] <= t_cut].reset_index(drop=True)
        te = events[events["t"] > t_cut].reset_index(drop=True)
        run = train_temporal.run(tr, te, topk=kwargs.get("topk", 50))
        return run

    else:
        raise ValueError("Unknown task. Use one of: node_classification, edge_classification, temporal_link_prediction")
