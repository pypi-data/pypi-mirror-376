import softgraph

def main():
    import softgraph

    run = softgraph.softgraph(
        task="node_classification",
        dataset="sbm",
        n=600, k=4, p_in=0.12, p_out=0.01,     # clearer communities
        features="spectral:16",                 # use spectral only, or mix with +degree
        model="logreg",                         # logreg now works great with spectral
        random_state=42,
        plot=True
    )
    print(run["metrics"])


if __name__ == "__main__":
    main()
