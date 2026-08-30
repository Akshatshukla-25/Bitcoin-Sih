#!/usr/bin/env python3
"""
model_comparison.py — SIH26146 (NTRO) Anomaly Detection Algorithm Benchmark

Compares Isolation Forest, LOF, and Mahalanobis against PyOD anomaly baselines:
  - HBOS (Histogram-based Outlier Score)
  - CBLOF (Cluster-based Local Outlier Factor)
  - PCA (Reconstruction Error)
  - KNN (K-Nearest Neighbors Outlier Detector)
  - 3-Model Blended Ensemble

Evaluates Precision, Recall, F1, ROC-AUC, PR-AUC, and Latency against synthetic ground truth.
Outputs: reports/model_comparison.csv
"""

import argparse
import os
import time
import warnings
import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.covariance import LedoitWolf
from scipy.spatial.distance import mahalanobis

warnings.filterwarnings('ignore')

from models import FEATURE_COLS

def evaluate_detector(y_true, scores, contamination=0.15):
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

def run_comparison(features_path: str = "data/features.csv", outdir: str = "reports"):
    os.makedirs(outdir, exist_ok=True)
    df = pd.read_csv(features_path)
    
    y_true = df["is_planted_anomaly"].values
    X_raw = df[FEATURE_COLS].fillna(0.0).values
    
    scaler = RobustScaler()
    X = scaler.fit_transform(X_raw)

    contamination = float(np.mean(y_true)) if np.mean(y_true) > 0 else 0.15
    results = []

    # 1. Isolation Forest
    t0 = time.perf_counter()
    iforest = IsolationForest(n_estimators=150, contamination=contamination, random_state=42)
    iforest.fit(X)
    scores_iforest = -iforest.decision_function(X)
    lat_iforest = (time.perf_counter() - t0) * 1000
    res = evaluate_detector(y_true, scores_iforest, contamination)
    res["Algorithm"] = "Isolation Forest"
    res["Type"] = "Tree Partitioning"
    res["Latency_ms"] = round(lat_iforest, 2)
    results.append(res)

    # 2. Local Outlier Factor
    t0 = time.perf_counter()
    lof = LocalOutlierFactor(n_neighbors=150, contamination=contamination, novelty=True)
    lof.fit(X)
    scores_lof = -lof.decision_function(X)
    lat_lof = (time.perf_counter() - t0) * 1000
    res = evaluate_detector(y_true, scores_lof, contamination)
    res["Algorithm"] = "Local Outlier Factor (LOF)"
    res["Type"] = "Density Estimation"
    res["Latency_ms"] = round(lat_lof, 2)
    results.append(res)

    # 3. Robust Mahalanobis
    t0 = time.perf_counter()
    lw = LedoitWolf(assume_centered=False)
    lw.fit(X)
    cov_inv = lw.get_precision()
    mean_vec = lw.location_
    scores_mahal = np.array([mahalanobis(x, mean_vec, cov_inv) for x in X])
    lat_mahal = (time.perf_counter() - t0) * 1000
    res = evaluate_detector(y_true, scores_mahal, contamination)
    res["Algorithm"] = "Robust Mahalanobis"
    res["Type"] = "Ellipsoidal Distance"
    res["Latency_ms"] = round(lat_mahal, 2)
    results.append(res)

    # PyOD Baselines
    try:
        from pyod.models.hbos import HBOS
        from pyod.models.cblof import CBLOF
        from pyod.models.pca import PCA as PyODPCA
        from pyod.models.knn import KNN

        # 4. HBOS
        t0 = time.perf_counter()
        hbos = HBOS(contamination=contamination)
        hbos.fit(X)
        scores_hbos = hbos.decision_scores_
        lat_hbos = (time.perf_counter() - t0) * 1000
        res = evaluate_detector(y_true, scores_hbos, contamination)
        res["Algorithm"] = "HBOS"
        res["Type"] = "Histogram / Fast Density"
        res["Latency_ms"] = round(lat_hbos, 2)
        results.append(res)

        # 5. CBLOF
        t0 = time.perf_counter()
        cblof = CBLOF(contamination=contamination, random_state=42, n_clusters=8)
        cblof.fit(X)
        scores_cblof = cblof.decision_scores_
        lat_cblof = (time.perf_counter() - t0) * 1000
        res = evaluate_detector(y_true, scores_cblof, contamination)
        res["Algorithm"] = "CBLOF"
        res["Type"] = "Clustering Outlier"
        res["Latency_ms"] = round(lat_cblof, 2)
        results.append(res)

        # 6. PCA Reconstruction Error
        t0 = time.perf_counter()
        pca_model = PyODPCA(contamination=contamination, random_state=42)
        pca_model.fit(X)
        scores_pca = pca_model.decision_scores_
        lat_pca = (time.perf_counter() - t0) * 1000
        res = evaluate_detector(y_true, scores_pca, contamination)
        res["Algorithm"] = "PCA"
        res["Type"] = "Linear Subspace Projection"
        res["Latency_ms"] = round(lat_pca, 2)
        results.append(res)

        # 7. KNN
        t0 = time.perf_counter()
        knn_model = KNN(contamination=contamination, n_neighbors=15)
        knn_model.fit(X)
        scores_knn = knn_model.decision_scores_
        lat_knn = (time.perf_counter() - t0) * 1000
        res = evaluate_detector(y_true, scores_knn, contamination)
        res["Algorithm"] = "k-NN"
        res["Type"] = "Distance to k-th Neighbor"
        res["Latency_ms"] = round(lat_knn, 2)
        results.append(res)

    except Exception as e:
        print(f"Note: PyOD extra models skipped due to {e}")

    # 8. Blended Ensemble
    t0 = time.perf_counter()
    z_if = (scores_iforest - np.mean(scores_iforest)) / np.std(scores_iforest)
    z_lof = (scores_lof - np.mean(scores_lof)) / np.std(scores_lof)
    z_mah = (scores_mahal - np.mean(scores_mahal)) / np.std(scores_mahal)
    scores_ensemble = (z_if + z_lof + z_mah) / 3.0
    lat_ens = lat_iforest + lat_lof + lat_mahal
    res = evaluate_detector(y_true, scores_ensemble, contamination)
    res["Algorithm"] = "3-Model Ensemble (Proposed)"
    res["Type"] = "Blended Meta-Ensemble"
    res["Latency_ms"] = round(lat_ens, 2)
    results.append(res)

    out_df = pd.DataFrame(results)
    # Order columns
    cols = ["Algorithm", "Type", "ROC_AUC", "PR_AUC", "F1_Score", "Precision", "Recall", "Latency_ms"]
    out_df = out_df[cols].sort_values("ROC_AUC", ascending=False).reset_index(drop=True)
    
    out_csv = os.path.join(outdir, "model_comparison.csv")
    out_df.to_csv(out_csv, index=False)
    return out_df

def main():
    parser = argparse.ArgumentParser(description="SIH26146 — Model Comparison Benchmark")
    parser.add_argument("--features", type=str, default="data/features.csv", help="path to features.csv")
    parser.add_argument("--outdir", type=str, default="reports", help="output directory")
    args = parser.parse_args()

    res_df = run_comparison(args.features, args.outdir)

    print("=" * 80)
    print("SIH26146 — Anomaly Detection Model Benchmark Table (Ground Truth Evaluation)")
    print("=" * 80)
    print(res_df.to_string(index=False))
    print("=" * 80)
    print(f"Saved benchmark table to {os.path.join(args.outdir, 'model_comparison.csv')}")

if __name__ == "__main__":
    main()
