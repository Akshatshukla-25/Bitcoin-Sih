#!/usr/bin/env python3
"""
features.py — SIH26146 (NTRO) Wallet-Entity Feature Store Generator

Aggregates one comprehensive feature row per unique wallet-entity combining:
  - Blockchain transaction stats (in/out volume, turnover, counts)
  - Graph structural metrics (centrality, PageRank, hop intervals, skim ratios)
  - Behavioral laundering metrics (rapid drain % within 10m/30m/60m/120m, fanout bursts)
  - Network-layer metadata (unique IPs, ASNs, countries, GeoIP entropy)
  - Ground truth labels for supervised evaluation/benchmarking
"""

import argparse
import csv
import json
import os
import networkx as nx
import pandas as pd
import numpy as np

from geoip import resolve_ips
from graph_signals import extract_wallet_structural_signals

def load_transactions_data(path: str):
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            row["input_wallet_addresses"] = json.loads(row["input_wallet_addresses"])
            row["output_wallet_addresses"] = json.loads(row["output_wallet_addresses"])
            row["total_input_amount"] = float(row["total_input_amount"])
            row["fee"] = float(row["fee"])
            row["src_port"] = int(row["src_port"])
            row["dst_port"] = int(row["dst_port"])
            rows.append(row)
    return rows

def build_feature_table(transactions_path: str = "transactions.csv", graph_path: str = "graph.gml") -> pd.DataFrame:
    transactions = load_transactions_data(transactions_path)
    
    if os.path.exists(graph_path):
        try:
            G = nx.read_gml(graph_path)
        except Exception:
            G = nx.MultiDiGraph()
    else:
        G = nx.MultiDiGraph()

    # Extract graph and behavioral signals
    signals = extract_wallet_structural_signals(transactions, G)

    # Collect all unique IPs across all wallets for batch GeoIP resolution
    all_ips = set()
    for s in signals.values():
        all_ips.update(s.get("associated_ips", []))
    
    geo_map = resolve_ips(list(all_ips))

    rows = []
    for wallet, sig in signals.items():
        ips = sig.get("associated_ips", [])
        countries = set()
        asns = set()
        country_counts = {}

        for ip in ips:
            g = geo_map.get(ip, {})
            c = g.get("country", "Unknown")
            a = g.get("asn", "Unknown")
            if c != "Unknown":
                countries.add(c)
                country_counts[c] = country_counts.get(c, 0) + 1
            if a != "Unknown":
                asns.add(a)

        dominant_country = sorted(country_counts.items(), key=lambda x: (-x[1], x[0]))[0][0] if country_counts else "Unknown"
        dominant_asn = sorted(list(asns))[0] if asns else "Unknown"

        row = {
            "wallet_address": wallet,
            "tx_count": sig["tx_count"],
            "in_degree": sig["in_degree"],
            "out_degree": sig["out_degree"],
            "degree_ratio": sig["degree_ratio"],
            "fanin_count": sig["fanin_count"],
            "fanout_count": sig["fanout_count"],
            "total_received_amount": sig["total_received_amount"],
            "total_sent_amount": sig["total_sent_amount"],
            "net_balance": sig["net_balance"],
            "turnover_ratio": sig["turnover_ratio"],
            "avg_hop_interval_mins": sig["avg_hop_interval_mins"],
            "median_hop_interval_mins": sig["median_hop_interval_mins"],
            "min_hop_interval_mins": sig["min_hop_interval_mins"],
            "max_hop_interval_mins": sig["max_hop_interval_mins"],
            "min_drain_minutes": sig["min_drain_minutes"],
            "wallet_age_hours": sig["wallet_age_hours"],
            "forwarded_pct_10m": sig["forwarded_pct_10m"],
            "forwarded_pct_30m": sig["forwarded_pct_30m"],
            "forwarded_pct_60m": sig["forwarded_pct_60m"],
            "forwarded_pct_120m": sig["forwarded_pct_120m"],
            "peel_skim_ratio": sig["peel_skim_ratio"],
            "peel_signal": round(sig["peel_skim_ratio"] * 100.0, 4),
            "transient_velocity": round(sig["turnover_ratio"] / (sig["wallet_age_hours"] + 0.05), 4),
            "velocity_drain_score": round(sig["forwarded_pct_30m"] * 10.0 / (sig["min_drain_minutes"] + 1.0), 4),
            "fanout_burst_signal": round(sig["fanout_count"] / (sig["wallet_age_hours"] + 0.1), 4),
            "fanin_burst_signal": round(sig["fanin_count"] / (sig["wallet_age_hours"] + 0.1), 4),
            "is_peel_chain_node": sig["is_peel_chain_node"],
            "is_mixer_hub": sig["is_mixer_hub"],
            "is_mixer_intermediate": sig["is_mixer_intermediate"],
            "is_rapid_cashout_node": sig["is_rapid_cashout_node"],
            "unique_counterparties": sig["unique_counterparties"],
            "unique_ips_count": sig["unique_ips_count"],
            "unique_countries_count": len(countries),
            "unique_asns_count": len(asns),
            "dominant_country": dominant_country,
            "dominant_asn": dominant_asn,
            "timestamp_entropy": sig["timestamp_entropy"],
            "betweenness_centrality": sig["betweenness_centrality"],
            "pagerank": sig["pagerank"],
            "ground_truth_label": sig["primary_label"],
            "is_planted_anomaly": sig["is_planted_anomaly"],
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.sort_values("wallet_address").reset_index(drop=True)
    return df

def main():
    parser = argparse.ArgumentParser(description="SIH26146 Part 3 — Wallet Feature Store Builder")
    parser.add_argument("--input", type=str, default="transactions.csv", help="path to transactions.csv")
    parser.add_argument("--graph", type=str, default="graph.gml", help="path to graph.gml")
    parser.add_argument("--outdir", type=str, default="data", help="output directory")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    df = build_feature_table(args.input, args.graph)
    out_csv = os.path.join(args.outdir, "features.csv")
    df.to_csv(out_csv, index=False)

    print("=" * 60)
    print("SIH26146 Part 3 — features.py summary")
    print("=" * 60)
    print(f"Total wallet entities: {len(df)}")
    print(f"Planted anomalies: {df['is_planted_anomaly'].sum()}")
    print(f"Normal entities: {len(df) - df['is_planted_anomaly'].sum()}")
    print(f"Wrote: {out_csv}")

if __name__ == "__main__":
    main()
