#!/usr/bin/env python3
"""
explain.py — SIH26146 (NTRO) SHAP Explainability & Reason Generation Engine

Computes local feature attributions using SHAP TreeExplainer on Isolation Forest,
translating numeric contributions and active reason codes into human-readable,
investigator-ready alert explanations.
"""

import os
os.environ["MPLCONFIGDIR"] = "/tmp/mpl_config"

import argparse
import json
import warnings
import joblib
import numpy as np
import pandas as pd
import shap

warnings.filterwarnings('ignore')

from models import FEATURE_COLS

FEATURE_DESCRIPTIONS = {
    "forwarded_pct_10m": ("rapid forward ratio (10m)", lambda v: f"{v:.1%} forwarded in <10m"),
    "forwarded_pct_30m": ("rapid forward ratio (30m)", lambda v: f"{v:.1%} forwarded in <30m"),
    "forwarded_pct_60m": ("rapid forward ratio (60m)", lambda v: f"{v:.1%} forwarded in <60m"),
    "forwarded_pct_120m": ("rapid forward ratio (120m)", lambda v: f"{v:.1%} forwarded in <120m"),
    "peel_signal": ("peel chain skim percentage", lambda v: f"{v:.2f}% skim per hop"),
    "peel_skim_ratio": ("peel chain skim ratio", lambda v: f"{v:.2%} skim"),
    "transient_velocity": ("transient fund velocity", lambda v: f"{v:.2f} velocity index"),
    "velocity_drain_score": ("rapid drain velocity score", lambda v: f"{v:.2f} drain score"),
    "fanout_burst_signal": ("mixer fan-out burst rate", lambda v: f"{v:.2f} destinations/hr"),
    "fanin_burst_signal": ("mixer consolidation burst rate", lambda v: f"{v:.2f} sources/hr"),
    "turnover_ratio": ("velocity turnover ratio", lambda v: f"{v:.1%} drained"),
    "is_peel_chain_node": ("peel chain layering pattern", lambda v: "sequential hop structure"),
    "is_mixer_hub": ("mixer hub node", lambda v: "fan-out/fan-in consolidation hub"),
    "is_rapid_cashout_node": ("rapid cash-out signature", lambda v: "lump sum quick extraction"),
    "unique_counterparties": ("counterparty network breadth", lambda v: f"{int(v)} distinct counterparties"),
    "unique_ips_count": ("associated IP count", lambda v: f"{int(v)} distinct IP addresses"),
    "unique_countries_count": ("geographic jurisdiction span", lambda v: f"{int(v)} countries"),
    "unique_asns_count": ("autonomous system diversity", lambda v: f"{int(v)} ASNs"),
    "tx_count": ("transaction frequency", lambda v: f"{int(v)} transactions"),
    "wallet_age_hours": ("wallet entity lifespan", lambda v: f"created {v:.2f} hours before last tx"),
}

def generate_plain_language_narrative(top_features: List[Dict[str, Any]], reason_codes: List[str], row: pd.Series) -> str:
    """Constructs a readable plain-language explanation sentence for investigators."""
    parts = []
    
    # Mention active reason codes first if any
    if "MIXER_FANOUT" in reason_codes:
        parts.append(f"mixer-style fanout/consolidation behavior ({int(row.get('fanout_count', 0))} out-hubs)")
    if "RAPID_CASHOUT" in reason_codes:
        parts.append(f"rapid balance extraction ({row.get('forwarded_pct_10m', 0):.0%} forwarded within 10 min)")
    if "PEEL_CHAIN" in reason_codes:
        parts.append(f"peel chain layering structure ({row.get('peel_skim_ratio', 0):.1%} skim per hop)")
    if "NEW_WALLET_HIGH_VOLUME" in reason_codes:
        parts.append(f"abnormal new wallet volume ({row.get('total_received_amount', 0):.2f} BTC in <{row.get('wallet_age_hours', 0):.1f}h)")
    if "CROSS_BORDER_HOP" in reason_codes:
        c_count = int(row.get("unique_countries_count", 1))
        dom_c = row.get("dominant_country", "Unknown")
        parts.append(f"cross-border IP routing ({c_count} jurisdictions including {dom_c})")

    # Add top SHAP feature contributions
    for feat in top_features[:2]:
        fname = feat["feature"]
        fval = feat["value"]
        fdesc, ffmt = FEATURE_DESCRIPTIONS.get(fname, (fname, str))
        formatted_val = ffmt(fval)
        desc_str = f"{fdesc} ({formatted_val})"
        if not any(fdesc in p for p in parts):
            parts.append(desc_str)

    if parts:
        return "Flagged primarily due to: " + "; ".join(parts) + "."
    else:
        return "Flagged due to statistically abnormal combination of graph centrality and transaction velocity."

def generate_shap_explanations(
    scored_csv: str = "data/scored_entities.csv",
    artifacts_joblib: str = "data/model_artifacts.joblib",
    outdir: str = "data"
) -> Dict[str, Any]:
    os.makedirs(outdir, exist_ok=True)
    df = pd.read_csv(scored_csv)
    models_bundle = joblib.load(artifacts_joblib)
    
    scaler = models_bundle["scaler"]
    iso_forest = models_bundle["iso_forest"]
    feature_cols = models_bundle["feature_cols"]

    X_raw = df[feature_cols].fillna(0.0).values
    X_scaled = scaler.transform(X_raw)

    # Compute SHAP values with TreeExplainer
    try:
        explainer = shap.TreeExplainer(iso_forest)
        raw_shap = explainer.shap_values(X_scaled)
        # Invert SHAP values so positive = pushes toward anomaly (red)
        shap_values = -raw_shap
    except Exception as e:
        print(f"Warning: TreeExplainer fallback triggered: {e}")
        # Deterministic fallback: scaled absolute deviation from mean
        shap_values = np.abs(X_scaled)

    explanations = {}
    global_importance = np.mean(np.abs(shap_values), axis=0)
    top_global_indices = np.argsort(global_importance)[::-1]
    
    global_top_features = [
        {"feature": feature_cols[i], "importance": round(float(global_importance[i]), 4)}
        for i in top_global_indices[:10]
    ]

    for idx, row in df.iterrows():
        wallet = row["wallet_address"]
        row_shap = shap_values[idx]
        
        # Sort features by signed contribution (most anomalous first)
        sorted_indices = np.argsort(row_shap)[::-1]
        
        top_local_features = []
        for i in sorted_indices[:5]:
            feat_name = feature_cols[i]
            feat_val = float(row[feat_name])
            shap_val = float(row_shap[i])
            top_local_features.append({
                "feature": feat_name,
                "display_name": FEATURE_DESCRIPTIONS.get(feat_name, (feat_name, None))[0],
                "value": round(feat_val, 4),
                "shap_value": round(shap_val, 4),
            })

        reason_codes = str(row.get("reason_codes", "")).split(";") if pd.notna(row.get("reason_codes")) else []
        reason_codes = [r for r in reason_codes if r]
        
        explanation_text = generate_plain_language_narrative(top_local_features, reason_codes, row)

        explanations[wallet] = {
            "wallet_address": wallet,
            "composite_risk_score": row["composite_risk_score"],
            "risk_band": row["risk_band"],
            "confidence_score": row["confidence_score"],
            "reason_codes": reason_codes,
            "top_features": top_local_features,
            "plain_language_explanation": explanation_text,
        }

    out_json = os.path.join(outdir, "explanations.json")
    with open(out_json, "w") as f:
        json.dump({
            "global_importance": global_top_features,
            "entities": explanations
        }, f, indent=2)

    return explanations, global_top_features

def main():
    parser = argparse.ArgumentParser(description="SIH26146 Part 3 — SHAP Explainability Engine")
    parser.add_argument("--scored", type=str, default="data/scored_entities.csv", help="path to scored_entities.csv")
    parser.add_argument("--artifacts", type=str, default="data/model_artifacts.joblib", help="path to model_artifacts.joblib")
    parser.add_argument("--outdir", type=str, default="data", help="output directory")
    args = parser.parse_args()

    explanations, global_top = generate_shap_explanations(args.scored, args.artifacts, args.outdir)

    print("=" * 60)
    print("SIH26146 Part 3 — explain.py summary")
    print("=" * 60)
    print(f"Total entities explained: {len(explanations)}")
    print("Top Global SHAP Contributing Features:")
    for g in global_top[:5]:
        print(f"  - {g['feature']:25}: {g['importance']:.4f}")
    
    print("Sample Top Flagged Plain Language Explanation:")
    sample_wallet = list(explanations.keys())[0]
    sample = explanations[sample_wallet]
    print(f"Wallet: {sample_wallet} (Risk: {sample['composite_risk_score']} - {sample['risk_band']})")
    print(f"Text:   {sample['plain_language_explanation']}")
    print(f"Wrote:  {os.path.join(args.outdir, 'explanations.json')}")

if __name__ == "__main__":
    main()
