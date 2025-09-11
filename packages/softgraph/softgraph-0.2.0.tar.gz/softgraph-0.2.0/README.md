## softgraph (one-call API)

> Import once, call once, get results.

```python
import softgraph

# Node classification on SBM in one call
run = softgraph.softgraph(
    task="node_classification",
    dataset="sbm",
    n=600, k=4, p_in=0.09, p_out=0.02,
    features="degree+pagerank+cluster",
    model="logreg",
    test_size=0.2,
    random_state=42,
    plot=True
)

print(run["metrics"])
```

**Supported tasks**
- `node_classification` (dataset: `sbm`)
- `edge_classification` (dataset: `signed_sbm`)
- `temporal_link_prediction` (dataset: `temporal_contacts`)

All run objects include:
```python
{
  "task": "...",
  "metrics": {...},
  "artifacts": {...}  # e.g., figures
}
```