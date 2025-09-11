import softgraph

def main():
    run = softgraph.softgraph(
        task="node_classification",
        dataset="sbm",
        n=600, k=4, p_in=0.10, p_out=0.02,
        features="spectral:16",
        model="mlp",
        plot=True,
        curves=True
    )
    print(run["metrics"])

if __name__ == "__main__":
    main()
