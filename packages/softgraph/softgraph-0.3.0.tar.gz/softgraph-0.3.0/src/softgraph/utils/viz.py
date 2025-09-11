import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, roc_curve, precision_recall_curve, auc
from sklearn.model_selection import learning_curve as sk_learning_curve

def confusion(y_true, y_pred, title="Confusion Matrix"):
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots()
    ConfusionMatrixDisplay(cm).plot(ax=ax, colorbar=False)
    ax.set_title(title)
    plt.tight_layout()
    return fig

def learning_curve(estimator, X, y, cv=5, train_sizes=np.linspace(0.1, 1.0, 5), scoring=None):
    sizes, train_scores, val_scores = sk_learning_curve(estimator, X, y, cv=cv, train_sizes=train_sizes, scoring=scoring, n_jobs=None)
    fig, ax = plt.subplots()
    ax.plot(sizes, train_scores.mean(axis=1), marker="o", label="train")
    ax.plot(sizes, val_scores.mean(axis=1), marker="o", label="cv")
    ax.set_xlabel("Training size"); ax.set_ylabel("Score"); ax.legend(); ax.set_title("Learning Curve")
    plt.tight_layout()
    return fig

def roc_pr(y_true, y_score, title="ROC/PR (binary)"):
    fpr, tpr, _ = roc_curve(y_true, y_score)
    prec, rec, _ = precision_recall_curve(y_true, y_score)
    roc_auc = auc(fpr, tpr); pr_auc = auc(rec, prec)
    fig1, ax1 = plt.subplots()
    ax1.plot(fpr, tpr); ax1.set_xlabel("FPR"); ax1.set_ylabel("TPR"); ax1.set_title(f"ROC AUC={roc_auc:.3f}")
    fig2, ax2 = plt.subplots()
    ax2.plot(rec, prec); ax2.set_xlabel("Recall"); ax2.set_ylabel("Precision"); ax2.set_title(f"PR AUC={pr_auc:.3f}")
    plt.tight_layout()
    return fig1, fig2
