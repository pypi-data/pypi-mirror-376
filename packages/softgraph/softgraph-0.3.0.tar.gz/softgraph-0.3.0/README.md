# softgraph (one-call API) — v0.3.0

**One call** to generate data → extract features → train a model → evaluate and plot.

## Install (editable dev)
```bash
pip install -e .
```

Optional deep:
```bash
pip install "softgraph[deep]"
# Then install torch-geometric from wheels if you want GCN/SAGE.
```

## Usage
```python
import softgraph

run = softgraph.softgraph(
    task="node_classification",
    dataset="sbm",
    n=800, k=4, p_in=0.10, p_out=0.02,
    features="spectral:16",
    model="mlp",
    plot=True,      # confusion matrix
    curves=True     # learning curve
)
print(run["metrics"])
```
