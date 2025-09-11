def show(run):
    print("="*len(run["task"]))
    print(run["task"])
    print("="*len(run["task"]))
    for k, v in run["metrics"].items():
        if isinstance(v, float):
            print(f"{k:>14}: {v:.4f}")
        else:
            print(f"{k:>14}: {v}")
