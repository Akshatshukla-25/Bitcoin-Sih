#!/usr/bin/env python3
"""
models.py — SIH26146 (NTRO) Unsupervised Multi-Model Anomaly Ensemble

Trains a tripartite ensemble of unsupervised detectors on wallet-entity features:
  1. Isolation Forest (Tree-based subspace isolation)
  2. Local Outlier Factor (Density-based local reachability distance)
  3. Robust Mahalanobis Distance (Regularized Ledoit-Wolf / Empirical Covariance)

Normalizes each model's score via z-scoring & min-max scaling to prevent dominance,
and blends into a unified ensemble anomaly score per wallet-entity.
"""

import argparse
import os
import warnings
import joblib
import numpy as np
import pandas as pd
from scipy.spatial.distance import mahalanobis
from sklearn.covariance import LedoitWolf, EmpiricalCovariance
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import RobustScaler

warnings.filterwarnings('ignore')

FEATURE_COLS = [
    "forwarded_pct_10m",
    "forwarded_pct_30m",
    "forwarded_pct_60m",
    "forwarded_pct_120m",
    "peel_signal",
    "transient_velocity",
    "velocity_drain_score",
    "fanout_burst_signal",
    "fanin_burst_signal",
    "turnover_ratio",
    "unique_countries_count",
    "unique_asns_count",
    "is_peel_chain_node",
    "is_mixer_hub",
    "is_rapid_cashout_node",
]

def train_ensemble(df: pd.DataFrame, random_state: int = 42):
    np.random.seed(random_state)
    
    X_raw = df[FEATURE_COLS].fillna(0.0).values
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X_raw)

    # 1. Isolation Forest
    iso_forest = IsolationForest(
        n_estimators=150,
        contamination=0.35,
        random_state=random_state,
        n_jobs=-1,
    )
    iso_forest.fit(X_scaled)
    scores_iforest = -iso_forest.decision_function(X_scaled)

    # 2. Local Outlier Factor
    lof = LocalOutlierFactor(
        n_neighbors=150,
        contamination=0.35,
        novelty=True,
        n_jobs=-1,
    )
    lof.fit(X_scaled)
    scores_lof = -lof.decision_function(X_scaled)

    # 3. Robust Mahalanobis with Ledoit-Wolf shrinkage
    try:
        lw = LedoitWolf(assume_centered=False)
        lw.fit(X_scaled)
        cov_inv = lw.get_precision()
        mean_vec = lw.location_
    except Exception as e:
        warnings.warn(f"Ledoit-Wolf shrinkage failed ({e}); falling back to EmpiricalCovariance.")
        emp = EmpiricalCovariance()
        emp.fit(X_scaled)
        cov_inv = np.linalg.pinv(emp.covariance_)
        mean_vec = emp.location_

    scores_mahal = np.array([
        mahalanobis(x, mean_vec, cov_inv) for x in X_scaled
    ])

    # Equalize score variances via standard Z-normalization before blending
    def z_normalize(arr: np.ndarray) -> np.ndarray:
        std = np.std(arr)
        return (arr - np.mean(arr)) / (std if std > 1e-8 else 1.0)

    def min_max_scale(arr: np.ndarray) -> np.ndarray:
        mn, mx = np.min(arr), np.max(arr)
        return (arr - mn) / (mx - mn if mx > mn else 1.0)

    # Standardize individual model score distributions
    z_iforest = z_normalize(scores_iforest)
    z_lof = z_normalize(scores_lof)
    z_mahal = z_normalize(scores_mahal)

    # Equal-weight variance-standardized ensemble blend
    blended_z = (z_iforest + z_lof + z_mahal) / 3.0
    blended_score = min_max_scale(blended_z)

    result_df = df.copy()
    result_df["score_iforest"] = np.round(min_max_scale(scores_iforest), 4)
    result_df["score_lof"] = np.round(min_max_scale(scores_lof), 4)
    result_df["score_mahalanobis"] = np.round(min_max_scale(scores_mahal), 4)
    result_df["ensemble_anomaly_score"] = np.round(blended_score, 4)

    models_bundle = {
        "scaler": scaler,
        "iso_forest": iso_forest,
        "lof": lof,
        "mean_vec": mean_vec,
        "cov_inv": cov_inv,
        "feature_cols": FEATURE_COLS,
    }

    return result_df, models_bundle

def run_models_pipeline(features_path: str = "data/features.csv", outdir: str = "data"):
    os.makedirs(outdir, exist_ok=True)
    df = pd.read_csv(features_path)
    scored_df, models_bundle = train_ensemble(df, random_state=42)
    
    out_csv = os.path.join(outdir, "anomaly_scores.csv")
    scored_df.to_csv(out_csv, index=False)
    
    bundle_path = os.path.join(outdir, "model_artifacts.joblib")
    joblib.dump(models_bundle, bundle_path)

    return scored_df, models_bundle

def main():
    parser = argparse.ArgumentParser(description="SIH26146 Part 3 — Multi-Model Anomaly Ensemble")
    parser.add_argument("--features", type=str, default="data/features.csv", help="path to features.csv")
    parser.add_argument("--outdir", type=str, default="data", help="output directory")
    args = parser.parse_args()

    scored_df, _ = run_models_pipeline(args.features, args.outdir)

    print("=" * 60)
    print("SIH26146 Part 3 — models.py summary")
    print("=" * 60)
    print(f"Total entities scored: {len(scored_df)}")
    print(f"Top 5 Anomaly Scores:")
    top5 = scored_df.sort_values("ensemble_anomaly_score", ascending=False)[
        ["wallet_address", "ensemble_anomaly_score", "score_iforest", "score_lof", "score_mahalanobis", "ground_truth_label"]
    ].head(5)
    print(top5.to_string(index=False))
    print(f"Wrote: {os.path.join(args.outdir, 'anomaly_scores.csv')}")

if __name__ == "__main__":
    main()
