#!/usr/bin/env python3
"""
scoring.py — SIH26146 (NTRO) Composite Risk Scoring & Alert Generation Engine

Blends three independent risk signal pillars into a unified 0-100 risk score:
  1. ML Ensemble Anomaly Score (Isolation Forest + LOF + Mahalanobis)
  2. Structural / Behavioral Reason Codes (Peel Chain, Mixer, Rapid Cashout, GeoIP hops)
  3. Entity-Cluster Aggregate Network Risk (Graph entity co-membership risk)

Outputs:
  - data/scored_entities.csv (complete scored wallet dataset)
  - data/alerts.json (actionable alerts with confidence & reason codes)
"""

import argparse
import json
import os
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configurable Scoring Weights (Config constants — adjustable per policy)
# ---------------------------------------------------------------------------
WEIGHT_ML_ENSEMBLE = 0.40          # 40% ML Unsupervised Ensemble
WEIGHT_STRUCTURAL_REASONS = 0.40    # 40% Structural & Behavioral Reason Codes
WEIGHT_CLUSTER_RISK = 0.20          # 20% Entity Cluster Aggregate Risk

# Thresholds for Alert Risk Bands (Calibrated for high sensitivity & precision)
BAND_CRITICAL_MIN = 65.0
BAND_HIGH_MIN = 50.0
BAND_MEDIUM_MIN = 35.0

# Reason Code Severity Contributions (0 - 100)
REASON_WEIGHTS = {
    "MIXER_FANOUT": 45.0,
    "RAPID_CASHOUT": 45.0,
    "PEEL_CHAIN": 40.0,
    "NEW_WALLET_HIGH_VOLUME": 25.0,
    "CROSS_BORDER_HOP": 20.0,
    "OBFUSCATION_DISAGREEMENT": 15.0,
}

def evaluate_wallet_reason_codes(row: pd.Series, cluster_info: Dict[str, Any]) -> Tuple[List[str], float]:
    """Evaluates which named reason codes fire for a given wallet-entity."""
    reasons = []

    # 1. Mixer Fan-out / Fan-in Hub
    if row.get("is_mixer_hub", 0) == 1 or row.get("fanout_count", 0) >= 4 or row.get("fanin_count", 0) >= 4:
        reasons.append("MIXER_FANOUT")
    elif row.get("is_mixer_intermediate", 0) == 1 and row.get("wallet_age_hours", 99) <= 2.5:
        reasons.append("MIXER_FANOUT")

    # 2. Rapid Cash-out
    if row.get("is_rapid_cashout_node", 0) == 1:
        reasons.append("RAPID_CASHOUT")
    elif (row.get("forwarded_pct_10m", 0) >= 0.85 and row.get("total_received_amount", 0) >= 0.5) or (
        row.get("forwarded_pct_30m", 0) >= 0.90 and row.get("min_drain_minutes", 99) <= 15.0 and row.get("wallet_age_hours", 99) <= 0.75
    ):
        reasons.append("RAPID_CASHOUT")

    # 3. Peel Chain Layering
    if row.get("is_peel_chain_node", 0) == 1:
        reasons.append("PEEL_CHAIN")
    elif (row.get("peel_skim_ratio", 0) >= 0.015 and row.get("in_degree", 0) <= 1 and row.get("out_degree", 0) <= 1 and row.get("wallet_age_hours", 99) <= 1.5) or \
         (row.get("forwarded_pct_30m", 0) >= 0.85 and row.get("min_drain_minutes", 99) <= 30.0 and row.get("in_degree", 0) == 1 and row.get("out_degree", 0) == 1 and row.get("wallet_age_hours", 99) <= 1.0):
        reasons.append("PEEL_CHAIN")

    # 4. New Wallet High Volume
    if row.get("wallet_age_hours", 99) <= 2.0 and row.get("total_received_amount", 0) >= 2.5:
        reasons.append("NEW_WALLET_HIGH_VOLUME")

    # 5. Cross-Border / Diverse ASN Hopping
    if row.get("unique_countries_count", 0) >= 2 or row.get("unique_asns_count", 0) >= 2:
        reasons.append("CROSS_BORDER_HOP")

    # 6. Obfuscation Disagreement
    if cluster_info.get("has_disagreement", False):
        reasons.append("OBFUSCATION_DISAGREEMENT")

    # Deduplicate while preserving order
    reasons = list(dict.fromkeys(reasons))
    
    # Calculate aggregate structural score
    raw_structural_score = sum(REASON_WEIGHTS.get(r, 10.0) for r in reasons)
    structural_score = min(100.0, raw_structural_score)
    
    return reasons, structural_score

def compute_risk_band(score: float) -> str:
    if score >= BAND_CRITICAL_MIN:
        return "CRITICAL"
    elif score >= BAND_HIGH_MIN:
        return "HIGH"
    elif score >= BAND_MEDIUM_MIN:
        return "MEDIUM"
    else:
        return "LOW"

def calculate_composite_scores(
    anomaly_csv: str = "data/anomaly_scores.csv",
    wallet_clusters_csv: str = "data/wallet_clusters.csv",
    clusters_json: str = "data/clusters.json",
    outdir: str = "data"
) -> pd.DataFrame:
    os.makedirs(outdir, exist_ok=True)

    df = pd.read_csv(anomaly_csv)
    clusters_df = pd.read_csv(wallet_clusters_csv)
    with open(clusters_json) as f:
        clusters_meta = json.load(f)

    # Merge cluster ID into scored dataframe
    df = df.merge(clusters_df[["wallet_address", "cluster_id"]], on="wallet_address", how="left")

    # Calculate cluster-level risk (mean ML anomaly score per cluster)
    cluster_ml_means = df.groupby("cluster_id")["ensemble_anomaly_score"].mean().to_dict()

    scored_records = []
    alerts = []

    for _, row in df.iterrows():
        wallet = row["wallet_address"]
        cid = row.get("cluster_id", "CLUSTER_0000")
        c_meta = clusters_meta.get(cid, {})

        # Pillar 1: ML Score (0-100)
        ml_score_100 = float(row["ensemble_anomaly_score"]) * 100.0

        # Pillar 2: Structural Reason Codes (0-100)
        reasons, struct_score_100 = evaluate_wallet_reason_codes(row, c_meta)

        # Pillar 3: Cluster Aggregate Risk (0-100)
        clust_ml = cluster_ml_means.get(cid, row["ensemble_anomaly_score"])
        cluster_score_100 = float(clust_ml) * 100.0

        # Composite Risk Calculation
        composite_risk = (
            (WEIGHT_ML_ENSEMBLE * ml_score_100) +
            (WEIGHT_STRUCTURAL_REASONS * struct_score_100) +
            (WEIGHT_CLUSTER_RISK * cluster_score_100)
        )
        composite_risk = round(min(100.0, max(0.0, composite_risk)), 2)
        band = compute_risk_band(composite_risk)

        # Confidence Score: Higher when ML and Structural Signals agree
        signal_agreement = 1.0 - (abs(ml_score_100 - struct_score_100) / 100.0)
        base_conf = 0.65 if band in ("HIGH", "CRITICAL") else (0.50 if band == "MEDIUM" else 0.35)
        confidence = round(min(0.99, max(0.40, base_conf + 0.30 * signal_agreement)), 2)

        rec = dict(row)
        rec["ml_risk_score"] = round(ml_score_100, 2)
        rec["structural_risk_score"] = round(struct_score_100, 2)
        rec["cluster_risk_score"] = round(cluster_score_100, 2)
        rec["composite_risk_score"] = composite_risk
        rec["risk_band"] = band
        rec["confidence_score"] = confidence
        rec["reason_codes"] = ";".join(reasons)
        rec["reason_count"] = len(reasons)
        scored_records.append(rec)

        if band in ("MEDIUM", "HIGH", "CRITICAL"):
            alerts.append({
                "wallet_address": wallet,
                "risk_score": composite_risk,
                "risk_band": band,
                "confidence": confidence,
                "reason_codes": reasons,
                "cluster_id": cid,
                "cluster_size": c_meta.get("wallet_count", 1),
                "dominant_country": row.get("dominant_country", "Unknown"),
                "dominant_asn": row.get("dominant_asn", "Unknown"),
                "total_volume": row.get("total_received_amount", 0.0),
                "ground_truth_label": row.get("ground_truth_label", "normal"),
            })

    result_df = pd.DataFrame(scored_records)
    # Sort by risk score descending
    result_df = result_df.sort_values("composite_risk_score", ascending=False).reset_index(drop=True)

    csv_out = os.path.join(outdir, "scored_entities.csv")
    alerts_out = os.path.join(outdir, "alerts.json")

    result_df.to_csv(csv_out, index=False)
    with open(alerts_out, "w") as f:
        json.dump(alerts, f, indent=2)

    return result_df, alerts

def main():
    parser = argparse.ArgumentParser(description="SIH26146 Part 3 — Composite Risk Scoring & Alert Engine")
    parser.add_argument("--anomaly", type=str, default="data/anomaly_scores.csv", help="path to anomaly_scores.csv")
    parser.add_argument("--clusters", type=str, default="data/wallet_clusters.csv", help="path to wallet_clusters.csv")
    parser.add_argument("--meta", type=str, default="data/clusters.json", help="path to clusters.json")
    parser.add_argument("--outdir", type=str, default="data", help="output directory")
    args = parser.parse_args()

    result_df, alerts = calculate_composite_scores(args.anomaly, args.clusters, args.meta, args.outdir)

    print("=" * 60)
    print("SIH26146 Part 3 — scoring.py summary")
    print("=" * 60)
    print(f"Total entities scored: {len(result_df)}")
    print("Risk Band Breakdown:")
    print(result_df["risk_band"].value_counts().to_string())
    print(f"Total Alerts (MEDIUM / HIGH / CRITICAL): {len(alerts)}")
    print(f"Top 5 Flagged Entities:")
    print(result_df[["wallet_address", "composite_risk_score", "risk_band", "confidence_score", "reason_codes", "ground_truth_label"]].head(5).to_string(index=False))
    print(f"Wrote: {os.path.join(args.outdir, 'scored_entities.csv')}")
    print(f"Wrote: {os.path.join(args.outdir, 'alerts.json')}")

if __name__ == "__main__":
    main()
