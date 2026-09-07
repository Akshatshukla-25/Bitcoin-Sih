#!/usr/bin/env python3
"""
model_comparison.py — SIH26146 (NTRO) Anomaly Detection Algorithm Benchmark

Compares Isolation Forest, LOF, and Mahalanobis against PyOD anomaly baselines:
  - HBOS (Histogram-based Outlier Score)
  - CBLOF (Cluster-based Local Outlier Factor)
  - PCA (Reconstruction Error)
  - KNN (K-Nearest Neighbors Outlier Detector)
  - 3-Model Blended Ensemble

Evaluates Precision, Recall, F1, ROC-AUC, and PR-AUC against synthetic ground truth.
Outputs: reports/model_comparison.csv
"""

import argparse
import os

import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.covariance import LedoitWolf
from scipy.spatial.distance import mahalanobis

from models import FEATURE_COLS

REQUIRED_COLUMNS = ["is_planted_anomaly", *FEATURE_COLS]

def evaluate_detector(y_true, scores, contamination=0.15):
    scores = np.asarray(scores, dtype=float)
    if not np.isfinite(scores).all():
        raise ValueError("Detector produced non-finite anomaly scores")

    # Determine binary threshold at contamination quantile
    threshold = np.quantile(scores, 1.0 - contamination)
    y_pred = (scores >= threshold).astype(int)

    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_true, scores)
    pr_auc = average_precision_score(y_true, scores)

    return {
        "Precision": round(precision, 4),
        "Recall": round(recall, 4),
        "F1_Score": round(f1, 4),
        "ROC_AUC": round(roc_auc, 4),
        "PR_AUC": round(pr_auc, 4),
    }

def run_comparison(
    features_path: str = "data/features.csv",
    outdir: str = "reports",
    random_state: int = 42,
):
    os.makedirs(outdir, exist_ok=True)
    df = pd.read_csv(features_path)
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Feature data is missing required columns: {', '.join(missing)}")
    if len(df) < 2:
        raise ValueError("Model comparison requires at least 2 feature rows")

    y_true = pd.to_numeric(df["is_planted_anomaly"], errors="raise").to_numpy()
    if not np.isin(y_true, [0, 1]).all():
        raise ValueError("is_planted_anomaly must contain only binary values 0 and 1")
    if np.unique(y_true).size != 2:
        raise ValueError("Model comparison requires both normal and anomalous ground-truth rows")

    X_raw = df[FEATURE_COLS].apply(pd.to_numeric, errors="raise").fillna(0.0).to_numpy(dtype=float)
    if not np.isfinite(X_raw).all():
        raise ValueError("Model comparison features must contain only finite numeric values")

    scaler = RobustScaler()
    X = scaler.fit_transform(X_raw)

    contamination = float(np.mean(y_true))
    results = []

    # 1. Isolation Forest
    iforest = IsolationForest(n_estimators=150, contamination=contamination, random_state=random_state)
    iforest.fit(X)
    scores_iforest = -iforest.decision_function(X)
    res = evaluate_detector(y_true, scores_iforest, contamination)
    res["Algorithm"] = "Isolation Forest"
    res["Type"] = "Tree Partitioning"

    results.append(res)

    # 2. Local Outlier Factor
    lof = LocalOutlierFactor(n_neighbors=min(150, len(df) - 1), contamination=contamination, novelty=True)
    lof.fit(X)
    scores_lof = -lof.decision_function(X)
    res = evaluate_detector(y_true, scores_lof, contamination)
    res["Algorithm"] = "Local Outlier Factor (LOF)"
    res["Type"] = "Density Estimation"

    results.append(res)

    # 3. Robust Mahalanobis
    lw = LedoitWolf(assume_centered=False)
    lw.fit(X)
    cov_inv = lw.get_precision()
    mean_vec = lw.location_
    scores_mahal = np.array([mahalanobis(x, mean_vec, cov_inv) for x in X])
    res = evaluate_detector(y_true, scores_mahal, contamination)
    res["Algorithm"] = "Robust Mahalanobis"
    res["Type"] = "Ellipsoidal Distance"

    results.append(res)

    # PyOD baselines are optional. Run independently so one incompatible model
    # cannot hide the results of other installed baselines.
    try:
        from pyod.models.hbos import HBOS
        from pyod.models.cblof import CBLOF
        from pyod.models.pca import PCA as PyODPCA
        from pyod.models.knn import KNN
    except ImportError as exc:
        print(f"Note: PyOD baselines unavailable: {exc}")
    else:
        pyod_detectors = [
            ("HBOS", "Histogram / Fast Density", lambda: HBOS(contamination=contamination)),
            (
                "CBLOF",
                "Clustering Outlier",
                lambda: CBLOF(
                    contamination=contamination,
                    random_state=random_state,
                    n_clusters=min(8, len(df)),
                ),
            ),
            (
                "PCA",
                "Linear Subspace Projection",
                lambda: PyODPCA(contamination=contamination, random_state=random_state),
            ),
            (
                "k-NN",
                "Distance to k-th Neighbor",
                lambda: KNN(contamination=contamination, n_neighbors=min(15, len(df) - 1)),
            ),
        ]
        for algorithm, detector_type, make_detector in pyod_detectors:
            try:
                detector = make_detector()
                detector.fit(X)
                res = evaluate_detector(y_true, detector.decision_scores_, contamination)
                res["Algorithm"] = algorithm
                res["Type"] = detector_type
                results.append(res)
            except (ValueError, TypeError, RuntimeError) as exc:
                print(f"Note: {algorithm} baseline skipped: {exc}")

    # 8. Blended Ensemble (Variance-standardized meta-ensemble matching production models.py)
    z_if = (scores_iforest - np.mean(scores_iforest)) / (np.std(scores_iforest) if np.std(scores_iforest) > 1e-8 else 1.0)
    z_lof = (scores_lof - np.mean(scores_lof)) / (np.std(scores_lof) if np.std(scores_lof) > 1e-8 else 1.0)
    z_mah = (scores_mahal - np.mean(scores_mahal)) / (np.std(scores_mahal) if np.std(scores_mahal) > 1e-8 else 1.0)
    blended_z = (z_if + z_lof + z_mah) / 3.0
    mn, mx = np.min(blended_z), np.max(blended_z)
    scores_ensemble = (blended_z - mn) / (mx - mn if mx > mn else 1.0)
    res = evaluate_detector(y_true, scores_ensemble, contamination)
    res["Algorithm"] = "3-Model Ensemble (Proposed)"
    res["Type"] = "Blended Meta-Ensemble"

    results.append(res)

    out_df = pd.DataFrame(results)
    # Order columns
    cols = ["Algorithm", "Type", "ROC_AUC", "PR_AUC", "F1_Score", "Precision", "Recall"]
    out_df = out_df[cols].sort_values("ROC_AUC", ascending=False).reset_index(drop=True)
    
    out_csv = os.path.join(outdir, "model_comparison.csv")
    out_df.to_csv(out_csv, index=False)
    return out_df

def main():
    parser = argparse.ArgumentParser(description="SIH26146 — Model Comparison Benchmark")
    parser.add_argument("--features", type=str, default="data/features.csv", help="path to features.csv")
    parser.add_argument("--outdir", type=str, default="reports", help="output directory")
    parser.add_argument("--seed", type=int, default=42, help="random seed")
    args = parser.parse_args()

    res_df = run_comparison(args.features, args.outdir, args.seed)

    print("=" * 80)
    print("SIH26146 — Anomaly Detection Model Benchmark Table (Ground Truth Evaluation)")
    print("=" * 80)
    print(res_df.to_string(index=False))
    print("=" * 80)
    print(f"Saved benchmark table to {os.path.join(args.outdir, 'model_comparison.csv')}")

if __name__ == "__main__":
    main()
