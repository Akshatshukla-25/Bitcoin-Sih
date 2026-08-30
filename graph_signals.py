#!/usr/bin/env python3
"""
graph_signals.py — SIH26146 (NTRO) Graph Structural Signals & Pattern Extractors

Computes structural and behavioral graph metrics over the tripartite
MultiDiGraph (wallets, transactions, IPs) and the wallet-flow projection:
  - Fan-in / Fan-out hub metrics & burst ratios (Mixer detection)
  - Directed chain depth & hop skim / interval analysis (Peel Chain detection)
  - Rapid balance drain ratios across 10m, 30m, 60m, 120m windows (Rapid Cashout detection)
  - Betweenness centrality & PageRank on wallet value flows
  - Cross-layer IP, ASN, and geographic diversity / cross-border metrics
"""

import math
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any, List
import networkx as nx
import numpy as np

def parse_iso(ts_str: str) -> datetime:
    try:
        return datetime.fromisoformat(ts_str)
    except Exception:
        return datetime(2025, 1, 1)

def compute_timestamp_entropy(timestamps: List[datetime]) -> float:
    """Calculates normalized Shannon entropy of transaction hours (0-23)."""
    if not timestamps or len(timestamps) < 2:
        return 0.0
    hour_counts = defaultdict(int)
    for t in timestamps:
        hour_counts[t.hour] += 1
    total = len(timestamps)
    entropy = 0.0
    for count in hour_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy / math.log2(24)

def build_wallet_flow_graph(transactions: List[Dict[str, Any]]) -> nx.DiGraph:
    """Constructs a directed wallet-to-wallet flow graph with aggregated weights."""
    W = nx.DiGraph()
    for tx in transactions:
        inputs = tx.get("input_wallet_addresses", [])
        outputs = tx.get("output_wallet_addresses", [])
        if not inputs or not outputs:
            continue
        total_in = max(sum(float(i["amount"]) for i in inputs), 1e-8)
        for inp in inputs:
            src = inp["address"]
            src_share = float(inp["amount"]) / total_in
            for out in outputs:
                dst = out["address"]
                if src == dst:
                    continue
                flow_val = float(out["amount"]) * src_share
                if W.has_edge(src, dst):
                    W[src][dst]["weight"] += flow_val
                    W[src][dst]["tx_count"] += 1
                else:
                    W.add_edge(src, dst, weight=flow_val, tx_count=1)
    return W

def extract_wallet_structural_signals(transactions: List[Dict[str, Any]], G: nx.MultiDiGraph) -> Dict[str, Dict[str, Any]]:
    """
    Computes comprehensive graph and behavioral signals for every wallet.
    """
    wallet_incoming = defaultdict(list)
    wallet_outgoing = defaultdict(list)
    all_wallets = set()

    for tx in transactions:
        ts = parse_iso(tx["timestamp"])
        txid = tx["txid"]
        src_ip = tx.get("src_ip", "")
        dst_ip = tx.get("dst_ip", "")
        label = tx.get("_ground_truth_label", "normal")

        fee = float(tx.get("fee", 0.0))
        tot_in = max(float(tx.get("total_input_amount", 1.0)), 1e-8)
        fee_ratio = fee / tot_in

        for inp in tx.get("input_wallet_addresses", []):
            addr = inp["address"]
            amt = float(inp["amount"])
            all_wallets.add(addr)
            wallet_outgoing[addr].append({
                "timestamp": ts,
                "amount": amt,
                "txid": txid,
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "label": label,
                "fee_ratio": fee_ratio,
                "outputs": [o["address"] for o in tx.get("output_wallet_addresses", [])],
                "output_amounts": [float(o["amount"]) for o in tx.get("output_wallet_addresses", [])],
            })

        for out in tx.get("output_wallet_addresses", []):
            addr = out["address"]
            amt = float(out["amount"])
            all_wallets.add(addr)
            wallet_incoming[addr].append({
                "timestamp": ts,
                "amount": amt,
                "txid": txid,
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "label": label,
                "fee_ratio": fee_ratio,
                "inputs": [i["address"] for i in tx.get("input_wallet_addresses", [])],
            })

    # Build wallet flow graph for centralities
    W = build_wallet_flow_graph(transactions)
    
    try:
        betweenness = nx.betweenness_centrality(W, weight="weight")
    except Exception:
        betweenness = {w: 0.0 for w in all_wallets}
    
    try:
        pagerank = nx.pagerank(W, weight="weight", alpha=0.85, max_iter=200)
    except Exception:
        pagerank = {w: 1.0 / max(len(all_wallets), 1) for w in all_wallets}

    signals = {}

    for wallet in all_wallets:
        in_events = sorted(wallet_incoming.get(wallet, []), key=lambda x: x["timestamp"])
        out_events = sorted(wallet_outgoing.get(wallet, []), key=lambda x: x["timestamp"])
        
        all_events = sorted(in_events + out_events, key=lambda x: x["timestamp"])
        all_timestamps = [e["timestamp"] for e in all_events]

        total_in_vol = sum(e["amount"] for e in in_events)
        total_out_vol = sum(e["amount"] for e in out_events)
        in_degree = len(in_events)
        out_degree = len(out_events)
        tx_count = in_degree + out_degree

        # Hop intervals & wallet lifespan
        if len(all_timestamps) >= 2:
            intervals = [(all_timestamps[i] - all_timestamps[i-1]).total_seconds() / 60.0 for i in range(1, len(all_timestamps))]
            avg_hop_interval = float(np.mean(intervals))
            min_hop_interval = float(np.min(intervals))
            max_hop_interval = float(np.max(intervals))
            median_hop_interval = float(np.median(intervals))
            wallet_age_hours = (all_timestamps[-1] - all_timestamps[0]).total_seconds() / 3600.0
        else:
            avg_hop_interval = 0.0
            min_hop_interval = 0.0
            max_hop_interval = 0.0
            median_hop_interval = 0.0
            wallet_age_hours = 0.0

        # Rapid drain ratios (10m, 30m, 60m, 120m)
        fwd_10m_vol = 0.0
        fwd_30m_vol = 0.0
        fwd_60m_vol = 0.0
        fwd_120m_vol = 0.0
        drain_durations = []

        for in_e in in_events:
            t_in = in_e["timestamp"]
            amt_in = in_e["amount"]
            for out_e in out_events:
                t_out = out_e["timestamp"]
                if t_out >= t_in:
                    diff_mins = (t_out - t_in).total_seconds() / 60.0
                    drain_durations.append(diff_mins)
                    if diff_mins <= 10:
                        fwd_10m_vol += min(out_e["amount"], amt_in)
                    if diff_mins <= 30:
                        fwd_30m_vol += min(out_e["amount"], amt_in)
                    if diff_mins <= 60:
                        fwd_60m_vol += min(out_e["amount"], amt_in)
                    if diff_mins <= 120:
                        fwd_120m_vol += min(out_e["amount"], amt_in)

        forwarded_pct_10m = min(1.0, fwd_10m_vol / max(total_in_vol, 1e-8)) if total_in_vol > 0 else 0.0
        forwarded_pct_30m = min(1.0, fwd_30m_vol / max(total_in_vol, 1e-8)) if total_in_vol > 0 else 0.0
        forwarded_pct_60m = min(1.0, fwd_60m_vol / max(total_in_vol, 1e-8)) if total_in_vol > 0 else 0.0
        forwarded_pct_120m = min(1.0, fwd_120m_vol / max(total_in_vol, 1e-8)) if total_in_vol > 0 else 0.0

        min_drain_minutes = min(drain_durations) if drain_durations else 9999.0

        # Counterparties and Fan-in / Fan-out
        in_counterparties = set()
        out_counterparties = set()
        for e in in_events:
            for inp_addr in e.get("inputs", []):
                if inp_addr != wallet:
                    in_counterparties.add(inp_addr)
        for e in out_events:
            for out_addr in e.get("outputs", []):
                if out_addr != wallet:
                    out_counterparties.add(out_addr)

        fanin_count = len(in_counterparties)
        fanout_count = len(out_counterparties)
        total_counterparties = len(in_counterparties | out_counterparties)

        # Mixer Hub Detection: High fanout or fanin within tight duration
        is_mixer_fanout_hub = 1.0 if (fanout_count >= 4 and wallet_age_hours <= 1.0) else 0.0
        is_mixer_fanin_hub = 1.0 if (fanin_count >= 4 and wallet_age_hours <= 2.0) else 0.0
        is_mixer_intermediate = 1.0 if (in_degree >= 1 and out_degree >= 1 and wallet_age_hours <= 1.5 and 0.80 <= (total_out_vol / max(total_in_vol, 1e-8)) <= 1.02) else 0.0

        # Peel chain skim & pass-through indicator
        peel_skim_ratio = 0.0
        is_peel_chain_node = 0.0
        if in_degree >= 1 and out_degree >= 1:
            for e in out_events:
                amts = e.get("output_amounts", [])
                if len(amts) == 2:
                    total = sum(amts)
                    if total > 0:
                        small_ratio = min(amts) / total
                        if 0.02 <= small_ratio <= 0.10 and min_drain_minutes <= 30.0:
                            peel_skim_ratio = max(peel_skim_ratio, small_ratio)
                            is_peel_chain_node = 1.0
                elif len(amts) == 1:
                    fee_rat = e.get("fee_ratio", 0.0)
                    if 0.02 <= fee_rat <= 0.10 and min_drain_minutes <= 30.0:
                        peel_skim_ratio = max(peel_skim_ratio, fee_rat)
                        is_peel_chain_node = 1.0

            if (peel_skim_ratio >= 0.015 and in_degree <= 1 and out_degree <= 1 and wallet_age_hours <= 1.5) or \
               (forwarded_pct_30m >= 0.85 and min_drain_minutes <= 30.0 and in_degree == 1 and out_degree == 1 and wallet_age_hours <= 1.0):
                is_peel_chain_node = 1.0

        # Rapid Cashout indicator: fresh wallet receiving lump sum and forwarding >=95% within 15 min
        is_rapid_cashout_node = 0.0
        if in_degree >= 1 and out_degree >= 1 and total_in_vol >= 0.5:
            if forwarded_pct_10m >= 0.85 or (forwarded_pct_30m >= 0.90 and min_drain_minutes <= 15.0):
                is_rapid_cashout_node = 1.0

        unique_ips = set()
        for e in all_events:
            if e.get("src_ip"):
                unique_ips.add(e["src_ip"])
            if e.get("dst_ip"):
                unique_ips.add(e["dst_ip"])

        # Ground truth label extraction
        labels = [e["label"] for e in all_events if "label" in e]
        if labels:
            non_normals = [l for l in labels if l != "normal"]
            primary_label = max(set(non_normals), key=non_normals.count) if non_normals else "normal"
        else:
            primary_label = "normal"

        signals[wallet] = {
            "wallet_address": wallet,
            "tx_count": tx_count,
            "in_degree": in_degree,
            "out_degree": out_degree,
            "degree_ratio": float(out_degree) / max(in_degree, 1),
            "fanin_count": fanin_count,
            "fanout_count": fanout_count,
            "total_received_amount": round(total_in_vol, 8),
            "total_sent_amount": round(total_out_vol, 8),
            "net_balance": round(total_in_vol - total_out_vol, 8),
            "turnover_ratio": round(min(total_in_vol, total_out_vol) / max(max(total_in_vol, total_out_vol), 1e-8), 4),
            "avg_hop_interval_mins": round(avg_hop_interval, 2),
            "median_hop_interval_mins": round(median_hop_interval, 2),
            "min_hop_interval_mins": round(min_hop_interval, 2),
            "max_hop_interval_mins": round(max_hop_interval, 2),
            "min_drain_minutes": round(min_drain_minutes if min_drain_minutes < 9000 else 0.0, 2),
            "wallet_age_hours": round(wallet_age_hours, 2),
            "forwarded_pct_10m": round(forwarded_pct_10m, 4),
            "forwarded_pct_30m": round(forwarded_pct_30m, 4),
            "forwarded_pct_60m": round(forwarded_pct_60m, 4),
            "forwarded_pct_120m": round(forwarded_pct_120m, 4),
            "peel_skim_ratio": round(peel_skim_ratio, 4),
            "is_peel_chain_node": is_peel_chain_node,
            "is_mixer_hub": max(is_mixer_fanout_hub, is_mixer_fanin_hub),
            "is_mixer_intermediate": is_mixer_intermediate,
            "is_rapid_cashout_node": is_rapid_cashout_node,
            "unique_counterparties": total_counterparties,
            "unique_ips_count": len(unique_ips),
            "associated_ips": sorted(list(unique_ips)),
            "timestamp_entropy": round(compute_timestamp_entropy(all_timestamps), 4),
            "betweenness_centrality": round(float(betweenness.get(wallet, 0.0)), 6),
            "pagerank": round(float(pagerank.get(wallet, 0.0)), 6),
            "primary_label": primary_label,
            "is_planted_anomaly": 0 if primary_label == "normal" else 1,
        }

    return signals
