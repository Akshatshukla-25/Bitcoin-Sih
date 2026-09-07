#!/usr/bin/env python3
"""
narrative.py — SIH26146 (NTRO) Investigator Case Narrative & SAR/STR Generator

Generates forensic investigative case summaries and Suspicious Activity Reports (SAR / STR)
for flagged entities by fusing:
  - Blockchain on-chain flow dynamics (volumes, turnover, hop velocity)
  - Graph topological position & entity cluster context
  - Cross-layer network metadata (GeoIP origins, ASN spread, IP churn)
  - ML ensemble anomaly score & SHAP feature contributions
  - Triggered reason codes (Peel Chain, Mixer Fan-Out/In, Rapid Cash-Out)

Supports:
  1. High-fidelity offline rule/template forensic narrative engine (100% air-gapped)
  2. Pre-cached narratives for top flagged cases stored in data/cached_narratives.json
"""

import argparse
from collections import defaultdict
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, List
import pandas as pd

NARRATIVES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "cached_narratives.json")

def generate_template_narrative(row: Dict[str, Any], explanation: Dict[str, Any]) -> str:
    """
    Generates a rigorous, professional law enforcement / FIU investigative narrative
    completely offline without external dependencies.
    """
    wallet = row.get("wallet_address", "UNKNOWN")
    risk_score = row.get("composite_risk_score", 0.0)
    band = row.get("risk_band", "UNKNOWN")
    reasons = explanation.get("reason_codes", [])
    cluster_id = row.get("cluster_id", "CLUSTER_UNKNOWN")
    country = row.get("dominant_country", "Unknown jurisdiction")
    asn = row.get("dominant_asn", "Unknown ASN")
    received = row.get("total_received_amount", 0.0)
    sent = row.get("total_sent_amount", 0.0)
    turnover = row.get("turnover_ratio", 0.0)
    fwd_10m = row.get("forwarded_pct_10m", 0.0)
    fwd_30m = row.get("forwarded_pct_30m", 0.0)
    age_h = row.get("wallet_age_hours", 0.0)
    tx_count = row.get("tx_count", 0)
    ips_count = row.get("unique_ips_count", 1)

    narrative_paragraphs = []

    # Opening Summary
    p1 = (
        f"Subject wallet entity {wallet} has been flagged at {band} risk level (Composite Risk Score: {risk_score:.1f}/100, "
        f"Confidence: {row.get('confidence_score', 0.85):.0%}) associated with entity cluster {cluster_id}. "
        f"The entity participated in {tx_count} transactions with aggregate cumulative volume of {received:.4f} BTC received "
        f"and {sent:.4f} BTC disbursed ({turnover:.1%} turnover ratio). Primary broadcast activity originated from "
        f"{country} via autonomous system {asn} across {ips_count} unique IP nodes."
    )
    narrative_paragraphs.append(p1)

    # Typology Specific Analysis
    typologies = []
    if "MIXER_FANOUT" in reasons:
        typologies.append(
            f"Transaction patterns exhibit strong mixer fan-out/fan-in characteristics with {int(row.get('fanout_count', 0))} "
            f"downstream destination hubs and high structural centrality, consistent with commercial mixing services or decentralized tumblers."
        )
    if "RAPID_CASHOUT" in reasons:
        typologies.append(
            f"Rapid fund drain signature observed: {fwd_10m:.1%} of total received balance was forwarded within 10 minutes of receipt "
            f"(rising to {fwd_30m:.1%} within 30 minutes) on a newly generated address active for only {age_h:.2f} hours. "
            f"This velocity profile warrants review for possible automated cash-out or theft-related extraction."
        )
    if "PEEL_CHAIN" in reasons:
        typologies.append(
            f"Flow structure matches a peeling chain layering sequence with an average hop interval of {row.get('avg_hop_interval_mins', 0):.1f} "
            f"minutes and a {row.get('peel_skim_ratio', 0):.1%} skim per hop, a pattern that can complicate provenance tracing."
        )
    if "CROSS_BORDER_HOP" in reasons:
        typologies.append(
            f"Network-layer telemetry detected cross-border IP routing spanning {int(row.get('unique_countries_count', 1))} geographic "
            f"jurisdictions and {int(row.get('unique_asns_count', 1))} ASNs within a condensed transaction window, which may reflect "
            f"multi-relay routing or proxy use and requires corroboration."
        )
    if "NEW_WALLET_HIGH_VOLUME" in reasons:
        typologies.append(
            f"The address received a high-value lump sum ({received:.2f} BTC) with zero prior on-chain history, followed by rapid liquidation."
        )

    if typologies:
        narrative_paragraphs.append(" ".join(typologies))
    else:
        narrative_paragraphs.append(
            "The entity displayed severe anomalous deviations in graph flow betweenness centrality and transaction timing entropy relative to population baselines."
        )

    # These outputs are investigative leads, not legal conclusions or automatic
    # enforcement decisions; a trained analyst must corroborate the evidence.
    p3 = (
        f"RECOMMENDATION: Prioritize entity cluster {cluster_id} for analyst review, corroborate the detected signals against "
        f"authoritative blockchain and network records, and consider an STR/SAR filing under applicable AML procedures if the "
        f"review confirms suspicion. Any preservation request or action involving provider {asn} requires appropriate legal authority."
    )
    narrative_paragraphs.append(p3)

    return "\n\n".join(narrative_paragraphs)

def generate_sar_export_document(
    wallet: str,
    row: Dict[str, Any],
    explanation: Dict[str, Any],
    narrative_text: str,
    generated_at: datetime,
) -> Dict[str, Any]:
    """Build a deterministic draft SAR/STR package for investigative handoff."""
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=timezone.utc)
    generated_at = generated_at.astimezone(timezone.utc)
    return {
        "report_type": "SUSPICIOUS_ACTIVITY_REPORT_STR_SAR",
        "report_id": f"SAR-NTRO-{generated_at.year}-{wallet[:8].upper()}",
        "timestamp_utc": generated_at.isoformat(),
        "agency": "National Technical Research Organisation (NTRO) / FIU-IND Reference",
        "investigation_case": "SIH26146-BITCOIN-TRAFFIC-MONITOR",
        "subject_entity": {
            "wallet_address": str(wallet),
            "cluster_id": str(row.get("cluster_id", "N/A")),
            "risk_band": str(row.get("risk_band", "UNKNOWN")),
            "composite_risk_score": float(row.get("composite_risk_score", 0.0)),
            "confidence": float(row.get("confidence_score", 0.0)),
            "dominant_country": str(row.get("dominant_country", "Unknown")),
            "dominant_asn": str(row.get("dominant_asn", "Unknown")),
            "unique_ips_count": int(row.get("unique_ips_count", 1)),
            "total_received_btc": float(row.get("total_received_amount", 0.0)),
            "total_sent_btc": float(row.get("total_sent_amount", 0.0)),
            "turnover_pct": float(row.get("turnover_ratio", 0.0)) * 100,
        },
        "detection_signals": {
            "ml_ensemble_anomaly_score": float(row.get("ml_risk_score", 0.0)),
            "isolation_forest_score": float(row.get("score_iforest", 0.0)),
            "lof_score": float(row.get("score_lof", 0.0)),
            "mahalanobis_score": float(row.get("score_mahalanobis", 0.0)),
            "triggered_reason_codes": explanation.get("reason_codes", []),
            "top_shap_features": explanation.get("top_features", []),
        },
        "forensic_investigator_narrative": narrative_text,
        "recommended_action": "Analyst review and corroboration; consider STR/SAR filing if warranted",
        "disclaimer": "Draft investigative aid generated from synthetic/offline analytical data; not a legal conclusion or automatic enforcement directive.",
    }

def cache_top_narratives(
    scored_csv: str = "data/scored_entities.csv",
    explanations_json: str = "data/explanations.json",
    outdir: str = "data",
    top_n: int = 50
) -> Dict[str, Any]:
    if top_n < 0:
        raise ValueError("top_n must be zero or greater")
    os.makedirs(outdir, exist_ok=True)
    df = pd.read_csv(scored_csv)
    required_columns = {"wallet_address", "composite_risk_score", "risk_band"}
    missing = sorted(required_columns.difference(df.columns))
    if missing:
        raise ValueError(f"Scored entity data is missing required columns: {', '.join(missing)}")
    with open(explanations_json) as f:
        exp_data = json.load(f)
    
    if not isinstance(exp_data, dict) or not isinstance(exp_data.get("entities", {}), dict):
        raise ValueError("Explanations JSON must contain an object-valued 'entities' field")

    entities_exp = exp_data.get("entities", {})
    cached = {}

    # Source timestamps are deterministic pipeline evidence; resolve authentic transaction timestamps
    # from transactions.json when available instead of falling back to the 1970 Unix epoch.
    transactions_path = os.path.join(outdir, "transactions.json")
    if not os.path.exists(transactions_path):
        transactions_path = os.path.join(os.path.dirname(scored_csv), "transactions.json")

    tx_wallet_timestamps = defaultdict(list)
    dataset_timestamps = []
    if os.path.exists(transactions_path):
        try:
            with open(transactions_path, "r", encoding="utf-8") as handle:
                transactions = json.load(handle)
            for tx in transactions:
                ts = tx.get("timestamp")
                if ts:
                    dataset_timestamps.append(ts)
                    for item in tx.get("input_wallet_addresses", []):
                        tx_wallet_timestamps[item.get("address")].append(ts)
                    for item in tx.get("output_wallet_addresses", []):
                        tx_wallet_timestamps[item.get("address")].append(ts)
        except Exception:
            pass

    if dataset_timestamps:
        default_generated_at = pd.to_datetime(max(dataset_timestamps), utc=True).to_pydatetime()
    elif "last_active" in df.columns and not df.empty:
        default_generated_at = pd.to_datetime(df["last_active"], utc=True, errors="coerce").max().to_pydatetime()
    elif "first_active" in df.columns and not df.empty:
        default_generated_at = pd.to_datetime(df["first_active"], utc=True, errors="coerce").max().to_pydatetime()
    else:
        default_generated_at = datetime(2025, 2, 1, tzinfo=timezone.utc)

    top_df = df.head(top_n)
    for _, row in top_df.iterrows():
        wallet = row["wallet_address"]
        exp = entities_exp.get(wallet, {"reason_codes": [], "top_features": []})
        narrative = generate_template_narrative(dict(row), exp)
        wallet_timestamps = tx_wallet_timestamps.get(wallet, [])
        if wallet_timestamps:
            wallet_generated_at = pd.to_datetime(max(wallet_timestamps), utc=True).to_pydatetime()
        else:
            wallet_generated_at = default_generated_at
        sar_doc = generate_sar_export_document(wallet, dict(row), exp, narrative, wallet_generated_at)
        cached[wallet] = {
            "narrative": narrative,
            "sar_document": sar_doc,
        }

    out_path = os.path.join(outdir, "cached_narratives.json")
    with open(out_path, "w") as f:
        json.dump(cached, f, indent=2)

    return cached

def main():
    parser = argparse.ArgumentParser(description="SIH26146 Part 3 — Case Narrative & SAR Export Engine")
    parser.add_argument("--scored", type=str, default="data/scored_entities.csv", help="path to scored_entities.csv")
    parser.add_argument("--explanations", type=str, default="data/explanations.json", help="path to explanations.json")
    parser.add_argument("--outdir", type=str, default="data", help="output directory")
    parser.add_argument("--top", type=int, default=50, help="number of top entities to pre-cache")
    args = parser.parse_args()

    cached = cache_top_narratives(args.scored, args.explanations, args.outdir, args.top)

    print("=" * 60)
    print("SIH26146 Part 3 — narrative.py summary")
    print("=" * 60)
    print(f"Pre-cached forensic narratives for top {len(cached)} flagged entities.")
    if cached:
        sample_wallet = next(iter(cached))
        print(f"\nSample Forensic Case Narrative for Top Entity ({sample_wallet}):\n")
        print(cached[sample_wallet]["narrative"])
    else:
        print("No narratives generated: no entities were selected.")
    print(f"\nWrote: {os.path.join(args.outdir, 'cached_narratives.json')}")

if __name__ == "__main__":
    main()
