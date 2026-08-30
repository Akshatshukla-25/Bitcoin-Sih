#!/usr/bin/env python3
"""
evaluate.py — SIH26146 (NTRO) Pipeline Evaluation & Performance Suite

Evaluates composite detection engine against synthetic ground truth:
  - Precision, Recall, Specificity, F1-Score, ROC-AUC, PR-AUC across alert bands (MEDIUM+, HIGH+, CRITICAL)
  - Generates confusion matrix visualization: reports/confusion_matrix.png
  - Generates ROC & Precision-Recall curves: reports/roc_curve.png
  - Outputs executive terminal scorecard for live demo defense
"""

import argparse
import os
import warnings
import numpy as np
import pandas as pd

# Set matplotlib cache directory for headless environments
os.environ["MPLCONFIGDIR"] = "/tmp/mpl_config"
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    average_precision_score, confusion_matrix, roc_curve, precision_recall_curve
)

warnings.filterwarnings("ignore")

def evaluate_pipeline(
    scored_csv: str = "data/scored_entities.csv",
    outdir: str = "reports"
):
    os.makedirs(outdir, exist_ok=True)
    df = pd.read_csv(scored_csv)

    y_true = df["is_planted_anomaly"].values
    scores = df["composite_risk_score"].values

    bands = [
        ("MEDIUM+ (Triage Policy >= 35)", 35.0),
        ("HIGH+ (Escalation Policy >= 50)", 50.0),
        ("CRITICAL (Immediate Freeze >= 65)", 65.0),
    ]

    metrics_list = []
    cm_dict = {}

    roc_auc = roc_auc_score(y_true, scores)
    pr_auc = average_precision_score(y_true, scores)

    for band_name, threshold in bands:
        y_pred = (scores >= threshold).astype(int)
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        spec = tn / max(tn + fp, 1)

        metrics_list.append({
            "Alert Policy Level": band_name,
            "Threshold": f">= {threshold:.0f}",
            "Flagged Count": int(np.sum(y_pred)),
            "True Positives (TP)": int(tp),
            "False Positives (FP)": int(fp),
            "Precision": round(prec, 4),
            "Recall (Sensitivity)": round(rec, 4),
            "Specificity": round(spec, 4),
            "F1-Score": round(f1, 4),
            "ROC-AUC": round(roc_auc, 4),
            "PR-AUC": round(pr_auc, 4),
        })
        cm_dict[band_name] = cm

    metrics_df = pd.DataFrame(metrics_list)
    report_csv = os.path.join(outdir, "evaluation_metrics.csv")
    metrics_df.to_csv(report_csv, index=False)

    # Apply NTRO Dark Theme to Matplotlib
    from matplotlib.colors import LinearSegmentedColormap
    plt.rcParams.update({
        "figure.facecolor": "#0B1220",
        "axes.facecolor": "#131B2E",
        "axes.edgecolor": "#1F2A44",
        "axes.labelcolor": "#E8E6DE",
        "text.color": "#E8E6DE",
        "xtick.color": "#94A3B8",
        "ytick.color": "#94A3B8",
        "font.family": "monospace",
        "grid.color": "#1F2A44",
        "grid.alpha": 0.4,
    })

    ntro_cmap = LinearSegmentedColormap.from_list("ntro_heat", ["#131B2E", "#2A364F", "#C8973B", "#8B2E2E"])

    # 1. Plot Confusion Matrices
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), facecolor="#0B1220")
    for ax, (band_name, cm) in zip(axes, cm_dict.items()):
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap=ntro_cmap,
            cbar=False,
            ax=ax,
            xticklabels=["Normal (0)", "Suspicious (1)"],
            yticklabels=["Normal (0)", "Suspicious (1)"],
            annot_kws={"size": 13, "weight": "bold", "color": "#E8E6DE"}
        )
        ax.set_title(band_name, fontsize=12, pad=10, weight="bold", color="#E8E6DE")
        ax.set_ylabel("Ground Truth", fontsize=10, color="#94A3B8")
        ax.set_xlabel("Predicted Alert", fontsize=10, color="#94A3B8")

    plt.tight_layout()
    cm_png = os.path.join(outdir, "confusion_matrix.png")
    plt.savefig(cm_png, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()

    # 2. Plot ROC and PR Curves
    fpr, tpr, _ = roc_curve(y_true, scores)
    precisions, recalls, _ = precision_recall_curve(y_true, scores)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), facecolor="#0B1220")

    # ROC Curve
    ax1.plot(fpr, tpr, color="#C8973B", lw=2.5, label=f"Composite Detector (AUC = {roc_auc:.3f})")
    ax1.plot([0, 1], [0, 1], color="#94A3B8", lw=1.5, linestyle="--", label="Random Chance (AUC = 0.500)")
    ax1.set_xlim([0.0, 1.0])
    ax1.set_ylim([0.0, 1.05])
    ax1.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11, color="#94A3B8")
    ax1.set_ylabel("True Positive Rate (Recall)", fontsize=11, color="#94A3B8")
    ax1.set_title("Receiver Operating Characteristic (ROC) Curve", fontsize=13, weight="bold", color="#E8E6DE")
    leg1 = ax1.legend(loc="lower right", facecolor="#131B2E", edgecolor="#1F2A44")
    for text in leg1.get_texts():
        text.set_color("#E8E6DE")
    ax1.grid(True, alpha=0.3, color="#1F2A44")

    # PR Curve
    baseline = np.mean(y_true)
    ax2.plot(recalls, precisions, color="#C8973B", lw=2.5, label=f"Precision-Recall (PR-AUC = {pr_auc:.3f})")
    ax2.axhline(y=baseline, color="#94A3B8", linestyle="--", lw=1.5, label=f"Baseline (Prevalence = {baseline:.3f})")
    ax2.set_xlim([0.0, 1.0])
    ax2.set_ylim([0.0, 1.05])
    ax2.set_xlabel("Recall (Coverage)", fontsize=11, color="#94A3B8")
    ax2.set_ylabel("Precision (Accuracy)", fontsize=11, color="#94A3B8")
    ax2.set_title("Precision-Recall Curve (Imbalanced Benchmark)", fontsize=13, weight="bold", color="#E8E6DE")
    leg2 = ax2.legend(loc="lower left", facecolor="#131B2E", edgecolor="#1F2A44")
    for text in leg2.get_texts():
        text.set_color("#E8E6DE")
    ax2.grid(True, alpha=0.3, color="#1F2A44")

    plt.tight_layout()
    roc_png = os.path.join(outdir, "roc_curve.png")
    plt.savefig(roc_png, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()

    return metrics_df, cm_png, roc_png

def main():
    parser = argparse.ArgumentParser(description="SIH26146 Part 3 — Evaluation Harness")
    parser.add_argument("--scored", type=str, default="data/scored_entities.csv", help="path to scored_entities.csv")
    parser.add_argument("--outdir", type=str, default="reports", help="output directory")
    args = parser.parse_args()

    metrics_df, cm_png, roc_png = evaluate_pipeline(args.scored, args.outdir)

    print("=" * 95)
    print("SIH26146 — AI Detection Engine Benchmark Scorecard (NTRO Ground Truth)")
    print("=" * 95)
    print(metrics_df.to_string(index=False))
    print("=" * 95)
    print(f"Saved Confusion Matrix: {cm_png}")
    print(f"Saved ROC & PR Curves:  {roc_png}")

if __name__ == "__main__":
    main()
