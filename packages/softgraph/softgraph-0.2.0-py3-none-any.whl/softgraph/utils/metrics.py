from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef

def node_cls(y_true, y_pred):
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro")),
    }

def edge_cls(y_true, y_pred):
    return {
        "balanced_acc": float(accuracy_score(y_true, y_pred)),
        "mcc": float(matthews_corrcoef(y_true, y_pred)),
    }
