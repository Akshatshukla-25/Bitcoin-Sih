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
import os
import networkx as nx
import pandas as pd

from graph_builder import validate_graph
from graph_signals import extract_wallet_structural_signals
from ofac import OFACScreener
from transaction_schema import load_transactions_csv

_ofac_path = "data/ofac_crypto_addresses.csv"
if not os.path.exists(_ofac_path):
    _repo_root = os.path.dirname(os.path.abspath(__file__))
    _ofac_path = os.path.join(_repo_root, "data", "ofac_crypto_addresses.csv")
_ofac = OFACScreener(csv_path=_ofac_path)

FEATURE_OUTPUT_COLUMNS = [
    # Identity & Basic Graph Stats
    "wallet_address", "tx_count", "in_degree", "out_degree", "degree_ratio",
    "fanin_count", "fanout_count", "total_received_amount", "total_sent_amount",
    "net_balance", "turnover_ratio",
    
    # Hop intervals & Timing
    "avg_hop_interval_mins", "median_hop_interval_mins", "min_hop_interval_mins", "max_hop_interval_mins",
    "min_drain_minutes", "wallet_age_hours", "temporal_burst_score", "timestamp_entropy",
    
    # Rapid Drain Percentiles
    "forwarded_pct_10m", "forwarded_pct_30m", "forwarded_pct_60m", "forwarded_pct_120m",
    
    # Heuristic & Behavioral Signals
    "peel_skim_ratio", "peel_signal", "transient_velocity", "velocity_drain_score",
    "fanout_burst_signal", "fanin_burst_signal",
    "is_peel_chain_node", "is_mixer_hub", "is_mixer_intermediate", "is_rapid_cashout_node",
    
    # On-Chain Fingerprints
    "fee_rate_mean", "fee_rate_std", "fee_rate_zscore",
    "round_output_ratio", "nonzero_locktime_ratio",
    
    # OFAC Sanctions Cross-Reference
    "is_ofac_flagged", "ofac_entity_name", "ofac_program",
    "has_ofac_counterparty", "ofac_counterparty_count",
    
    # Graph Topology
    "unique_counterparties", "betweenness_centrality", "pagerank",
    
    # Evaluation / Labels
    "ground_truth_label", "is_planted_anomaly",
]


def load_transactions_data(path: str):
    return load_transactions_csv(path)

def build_feature_table(transactions_path: str = "transactions.csv", graph_path: str = "graph.gml") -> pd.DataFrame:
    transactions = load_transactions_data(transactions_path)
    
    if not os.path.exists(graph_path):
        raise FileNotFoundError(
            f"Required graph artifact {graph_path!r} does not exist; run graph_builder.py first."
        )
    try:
        G = nx.read_gml(graph_path)
    except (OSError, nx.NetworkXError) as exc:
        raise ValueError(f"Unable to read graph artifact {graph_path!r}: {exc}") from exc
    validate_graph(G, expected_transaction_count=len(transactions))

    # Extract graph, behavioral, and OFAC signals
    signals = extract_wallet_structural_signals(transactions, G)

    rows = []
    for wallet, sig in signals.items():
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
            "temporal_burst_score": sig["temporal_burst_score"],
            "timestamp_entropy": sig["timestamp_entropy"],
            "forwarded_pct_10m": sig["forwarded_pct_10m"],
            "forwarded_pct_30m": sig["forwarded_pct_30m"],
            "forwarded_pct_60m": sig["forwarded_pct_60m"],
            "forwarded_pct_120m": sig["forwarded_pct_120m"],
            "peel_skim_ratio": sig["peel_skim_ratio"],
            "peel_signal": round(sig["peel_skim_ratio"] * 100.0, 4),
            "transient_velocity": round(sig["turnover_ratio"] / (sig["wallet_age_hours"] + 0.05), 4),
            "velocity_drain_score": round(sig["forwarded_pct_30m"] * 10.0 / (sig["min_drain_minutes"] + 1.0), 4) if sig["min_drain_minutes"] >= 0.0 else 0.0,
            "fanout_burst_signal": round(sig["fanout_count"] / (sig["wallet_age_hours"] + 0.1), 4),
            "fanin_burst_signal": round(sig["fanin_count"] / (sig["wallet_age_hours"] + 0.1), 4),
            "is_peel_chain_node": sig["is_peel_chain_node"],
            "is_mixer_hub": sig["is_mixer_hub"],
            "is_mixer_intermediate": sig["is_mixer_intermediate"],
            "is_rapid_cashout_node": sig["is_rapid_cashout_node"],
            "fee_rate_mean": sig["fee_rate_mean"],
            "fee_rate_std": sig["fee_rate_std"],
            "fee_rate_zscore": sig["fee_rate_zscore"],
            "round_output_ratio": sig["round_output_ratio"],
            "nonzero_locktime_ratio": sig["nonzero_locktime_ratio"],
            "is_ofac_flagged": sig["is_ofac_flagged"],
            "ofac_entity_name": sig["ofac_entity_name"],
            "ofac_program": sig["ofac_program"],
            "has_ofac_counterparty": sig["has_ofac_counterparty"],
            "ofac_counterparty_count": sig["ofac_counterparty_count"],
            "unique_counterparties": sig["unique_counterparties"],
            "betweenness_centrality": sig["betweenness_centrality"],
            "pagerank": sig["pagerank"],
            "ground_truth_label": sig["primary_label"],
            "is_planted_anomaly": sig["is_planted_anomaly"],
        }
        rows.append(row)

    df = pd.DataFrame(rows, columns=FEATURE_OUTPUT_COLUMNS)
    if not df.empty:
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
