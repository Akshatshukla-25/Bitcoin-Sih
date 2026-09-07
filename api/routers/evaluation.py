from fastapi import APIRouter
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.metrics import roc_curve, precision_recall_curve, confusion_matrix, auc
from api.data_loader import load_data_bundle, clean_nan

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])

@router.get("")
def get_evaluation():
    data = load_data_bundle()
    scored_df = data["scored_df"]
    eval_metrics_df = data["eval_metrics_df"]

    # 1. Performance metrics table from CSV
    metrics_records = eval_metrics_df.to_dict(orient="records") if not eval_metrics_df.empty else []

    # 2. Ground truth and score arrays
    y_true = (scored_df["ground_truth_label"] != "normal").astype(int).values
    y_scores = (scored_df["composite_risk_score"] / 100.0).values

    # 3. Numeric Confusion Matrices for the three triage levels
    bands_config = [
        ("CRITICAL", 60.0, "Immediate Action (Score ≥ 60)"),
        ("HIGH", 50.0, "Priority Escalation (Score ≥ 50)"),
        ("MEDIUM", 35.0, "Surveillance Watch (Score ≥ 35)")
    ]

    confusion_matrices = []
    for band_name, threshold, desc in bands_config:
        y_pred = (scored_df["composite_risk_score"] >= threshold).astype(int).values
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        confusion_matrices.append({
            "band": band_name,
            "threshold": threshold,
            "description": desc,
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
            "flagged": int(tp + fp),
            "precision": round(float(prec * 100), 2),
            "recall": round(float(rec * 100), 2),
            "specificity": round(float(spec * 100), 2),
            "f1_score": round(float(f1), 4)
        })

    # 4. Numeric ROC Curve Points
    fpr, tpr, _ = roc_curve(y_true, y_scores)
    roc_auc_val = float(auc(fpr, tpr))
    # Downsample curve points for fast, smooth client-side charting
    step = max(1, len(fpr) // 40)
    roc_points = [{"fpr": round(float(fpr[i]), 4), "tpr": round(float(tpr[i]), 4)} for i in range(0, len(fpr), step)]
    if roc_points[-1]["fpr"] != 1.0:
        roc_points.append({"fpr": 1.0, "tpr": 1.0})

    # 5. Numeric PR Curve Points
    precision, recall, _ = precision_recall_curve(y_true, y_scores)
    pr_auc_val = float(auc(recall, precision))
    step_pr = max(1, len(precision) // 40)
    pr_points = [{"recall": round(float(recall[i]), 4), "precision": round(float(precision[i]), 4)} for i in range(0, len(precision), step_pr)]

    return clean_nan({
        "metrics_table": metrics_records,
        "confusion_matrices": confusion_matrices,
        "roc_curve": {
            "auc": round(roc_auc_val, 4),
            "points": roc_points
        },
        "pr_curve": {
            "auc": round(pr_auc_val, 4),
            "points": pr_points
        }
    })
