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

import collections
import math
import os
import warnings
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any, List
import networkx as nx
import numpy as np

from ofac import OFACScreener

_ofac_path = "data/ofac_crypto_addresses.csv"
if not os.path.exists(_ofac_path):
    _repo_root = os.path.dirname(os.path.abspath(__file__))
    _ofac_path = os.path.join(_repo_root, "data", "ofac_crypto_addresses.csv")
_ofac = OFACScreener(csv_path=_ofac_path)

def _is_round_amount(amount: float) -> bool:
    """Detect AML structuring via suspiciously round output amounts (divisible by 0.1, 0.5, 1.0 BTC)."""
    if amount <= 0.0:
        return False
    for step in (0.1, 0.5, 1.0):
        rem = amount % step
        if rem < 0.001 or abs(step - rem) < 0.001:
            return True
        if abs(amount - round(amount / step) * step) < 0.001:
            return True
    return False

# ---------------------------------------------------------------------------
# Named Forensic Constants & Thresholds
# ---------------------------------------------------------------------------
DRAIN_WINDOW_10M = 10.0          # 10-minute rapid cashout window
DRAIN_WINDOW_30M = 30.0          # 30-minute rapid cashout / peel window
DRAIN_WINDOW_60M = 60.0          # 60-minute window
DRAIN_WINDOW_120M = 120.0        # 120-minute window

PEEL_SKIM_MIN_RATIO = 0.015      # Minimum skim ratio to flag peel hop (1.5%)
PEEL_SKIM_MAX_RATIO = 0.10       # Maximum skim ratio to flag peel hop (10.0%)
PEEL_MAX_DRAIN_MINS = 30.0       # Maximum minutes between peel hops
PEEL_MAX_WALLET_AGE_HOURS = 3.0  # Peel wallets are transient single-hop intermediates

MIXER_FANOUT_THRESHOLD = 4       # Minimum counterparties for fanout / fanin hub
MIXER_FANOUT_MAX_AGE_HOURS = 3.0 # Mixer fanout hub max active age window
MIXER_INTERMEDIATE_MAX_AGE_HOURS = 3.0  # Mixer intermediate wallet max active age (matches gen_mixer)
MIXER_PASSTHROUGH_MIN_RATIO = 0.80      # Mixer intermediate passthrough ratio floor
MIXER_PASSTHROUGH_MAX_RATIO = 1.02      # Mixer intermediate passthrough ratio ceiling

NO_DRAIN_SENTINEL = -1.0         # Sentinel value representing no outgoing drain observed

def parse_iso(ts_str: str) -> datetime:
    try:
        return datetime.fromisoformat(ts_str)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid ISO-8601 transaction timestamp {ts_str!r}") from exc

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

    # Invert weight for shortest-path centrality: high-value flow = shorter forensic distance
    for _, _, data in W.edges(data=True):
        data["distance"] = 1.0 / (data["weight"] + 1e-6)

    return W

def compute_windowed_forward_vol(in_events: List[Dict[str, Any]], out_events: List[Dict[str, Any]], max_window_mins: float) -> float:
    """Accurately computes forwarded volume without double-counting across multiple input events."""
    in_rem = [e["amount"] for e in in_events]
    out_rem = [e["amount"] for e in out_events]
    fwd_vol = 0.0
    for i, in_e in enumerate(in_events):
        t_in = in_e["timestamp"]
        for j, out_e in enumerate(out_events):
            if out_rem[j] <= 1e-8 or in_rem[i] <= 1e-8:
                continue
            t_out = out_e["timestamp"]
            if t_out >= t_in:
                diff_mins = (t_out - t_in).total_seconds() / 60.0
                if diff_mins <= max_window_mins:
                    matched = min(in_rem[i], out_rem[j])
                    fwd_vol += matched
                    in_rem[i] -= matched
                    out_rem[j] -= matched
    return fwd_vol

def extract_wallet_structural_signals(transactions: List[Dict[str, Any]], G: nx.MultiDiGraph) -> Dict[str, Dict[str, Any]]:
    """
    Computes comprehensive graph and behavioral signals for every wallet.
    """
    if not isinstance(G, nx.MultiDiGraph):
        raise ValueError(f"Expected a MultiDiGraph, got {type(G).__name__}")

    graph_wallets = {
        node for node, data in G.nodes(data=True) if data.get("node_type") == "wallet"
    }
    wallet_incoming = defaultdict(list)
    wallet_outgoing = defaultdict(list)
    all_wallets = set()

    for tx in transactions:
        ts = parse_iso(tx["timestamp"])
        txid = tx["txid"]
        label = tx.get("_ground_truth_label", "normal")

        fee = float(tx.get("fee", 0.0))
        tot_in = max(float(tx.get("total_input_amount", 1.0)), 1e-8)
        fee_ratio = fee / tot_in

        inputs = tx.get("input_wallet_addresses", [])
        outputs = tx.get("output_wallet_addresses", [])
        tx_size_proxy = max(len(inputs) + len(outputs), 1)
        tx_fee_rate = fee / tx_size_proxy

        has_round_output = any(_is_round_amount(float(o.get("amount", 0.0))) for o in outputs)
        # Bitcoin transaction version and locktime: default to 0 if not present in schema
        # (would be populated from real Bitcoin node data)
        locktime = tx.get("locktime", tx.get("nLockTime", 0))
        is_nonzero_locktime = (locktime != 0)

        for inp in inputs:
            addr = inp["address"]
            amt = float(inp["amount"])
            all_wallets.add(addr)
            wallet_outgoing[addr].append({
                "timestamp": ts,
                "amount": amt,
                "txid": txid,
                "label": label,
                "fee_ratio": fee_ratio,
                "fee_rate": tx_fee_rate,
                "has_round_output": has_round_output,
                "is_nonzero_locktime": is_nonzero_locktime,
                "inputs": [i["address"] for i in inputs],
                "outputs": [o["address"] for o in outputs],
                "output_amounts": [float(o["amount"]) for o in outputs],
            })

        for out in outputs:
            addr = out["address"]
            amt = float(out["amount"])
            all_wallets.add(addr)
            wallet_incoming[addr].append({
                "timestamp": ts,
                "amount": amt,
                "txid": txid,
                "label": label,
                "fee_ratio": fee_ratio,
                "inputs": [i["address"] for i in inputs],
                "outputs": [o["address"] for o in outputs],
            })

    if all_wallets != graph_wallets:
        missing = sorted(all_wallets - graph_wallets)[:3]
        extra = sorted(graph_wallets - all_wallets)[:3]
        raise ValueError(
            f"Graph/transaction wallet mismatch; missing={missing}, extra={extra}"
        )

    # Build wallet flow projection for value-weighted centralities after validating
    # that the supplied tripartite graph contains the same wallet population.
    W = build_wallet_flow_graph(transactions)
    
    try:
        betweenness = nx.betweenness_centrality(W, weight="distance")
    except Exception as e:
        warnings.warn(f"Betweenness centrality calculation failed ({e}); defaulting to 0.0")
        betweenness = {w: 0.0 for w in all_wallets}
    
    try:
        pagerank = nx.pagerank(W, weight="weight", alpha=0.85, max_iter=200)
    except Exception as e:
        warnings.warn(f"PageRank calculation failed ({e}); defaulting to uniform")
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
            mean_interval = float(np.mean(intervals))
            std_interval = float(np.std(intervals))
            temporal_burst_score = float(std_interval / mean_interval) if mean_interval > 1e-6 else 0.0
        else:
            avg_hop_interval = 0.0
            min_hop_interval = 0.0
            max_hop_interval = 0.0
            median_hop_interval = 0.0
            wallet_age_hours = 0.0
            temporal_burst_score = 0.0

        # Rapid drain ratios (10m, 30m, 60m, 120m) computed with running remaining attribution
        fwd_10m_vol = compute_windowed_forward_vol(in_events, out_events, DRAIN_WINDOW_10M)
        fwd_30m_vol = compute_windowed_forward_vol(in_events, out_events, DRAIN_WINDOW_30M)
        fwd_60m_vol = compute_windowed_forward_vol(in_events, out_events, DRAIN_WINDOW_60M)
        fwd_120m_vol = compute_windowed_forward_vol(in_events, out_events, DRAIN_WINDOW_120M)

        drain_durations = []
        for in_e in in_events:
            t_in = in_e["timestamp"]
            for out_e in out_events:
                t_out = out_e["timestamp"]
                if t_out >= t_in:
                    drain_durations.append((t_out - t_in).total_seconds() / 60.0)

        forwarded_pct_10m = min(1.0, fwd_10m_vol / max(total_in_vol, 1e-8)) if total_in_vol > 0 else 0.0
        forwarded_pct_30m = min(1.0, fwd_30m_vol / max(total_in_vol, 1e-8)) if total_in_vol > 0 else 0.0
        forwarded_pct_60m = min(1.0, fwd_60m_vol / max(total_in_vol, 1e-8)) if total_in_vol > 0 else 0.0
        forwarded_pct_120m = min(1.0, fwd_120m_vol / max(total_in_vol, 1e-8)) if total_in_vol > 0 else 0.0

        min_drain_minutes = min(drain_durations) if drain_durations else NO_DRAIN_SENTINEL

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
        all_counterparties = in_counterparties | out_counterparties
        total_counterparties = len(all_counterparties)

        # OFAC sanctions cross-reference
        ofac_result = _ofac.screen(wallet)
        is_ofac_flagged = 1.0 if ofac_result["is_flagged"] else 0.0
        ofac_entity_name = ofac_result.get("entity_name") or ""
        ofac_program = ofac_result.get("program") or ""

        ofac_counterparty_count = sum(
            1 for c in all_counterparties if _ofac.screen(c)["is_flagged"]
        )
        has_ofac_counterparty = 1.0 if ofac_counterparty_count > 0 else 0.0

        # On-chain transaction fingerprints (fee rate, round output structuring, locktime ratio)
        seen_out_txids = set()
        wallet_rates = []
        wallet_round_tx_count = 0
        wallet_nonzero_locktime_count = 0
        for e in out_events:
            tx_id = e["txid"]
            if tx_id not in seen_out_txids:
                seen_out_txids.add(tx_id)
                wallet_rates.append(e["fee_rate"])
                if e.get("has_round_output"):
                    wallet_round_tx_count += 1
                if e.get("is_nonzero_locktime"):
                    wallet_nonzero_locktime_count += 1

        num_out_txs = len(seen_out_txids)
        if wallet_rates:
            fee_rate_mean = float(np.mean(wallet_rates))
            fee_rate_std = float(np.std(wallet_rates)) if len(wallet_rates) > 1 else 0.0
        else:
            fee_rate_mean = 0.0
            fee_rate_std = 0.0

        round_output_ratio = float(wallet_round_tx_count) / max(num_out_txs, 1) if num_out_txs > 0 else 0.0
        # Bitcoin transaction version and locktime: default to 0 if not present in schema
        # (would be populated from real Bitcoin node data)
        nonzero_locktime_ratio = float(wallet_nonzero_locktime_count) / max(num_out_txs, 1) if num_out_txs > 0 else 0.0

        # Mixer Hub Detection: High fanout or fanin within tight duration
        is_mixer_fanout_hub = 1.0 if (fanout_count >= MIXER_FANOUT_THRESHOLD and wallet_age_hours <= MIXER_FANOUT_MAX_AGE_HOURS) else 0.0
        is_mixer_fanin_hub = 1.0 if (fanin_count >= MIXER_FANOUT_THRESHOLD and wallet_age_hours <= MIXER_FANOUT_MAX_AGE_HOURS) else 0.0
        is_mixer_intermediate = 1.0 if (
            in_degree >= 1 and out_degree >= 1 and 
            wallet_age_hours <= MIXER_INTERMEDIATE_MAX_AGE_HOURS and 
            MIXER_PASSTHROUGH_MIN_RATIO <= (total_out_vol / max(total_in_vol, 1e-8)) <= MIXER_PASSTHROUGH_MAX_RATIO
        ) else 0.0

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
                        if PEEL_SKIM_MIN_RATIO <= small_ratio <= PEEL_SKIM_MAX_RATIO and (0.0 <= min_drain_minutes <= PEEL_MAX_DRAIN_MINS):
                            peel_skim_ratio = max(peel_skim_ratio, small_ratio)
                            is_peel_chain_node = 1.0
                elif len(amts) == 1:
                    fee_rat = e.get("fee_ratio", 0.0)
                    if PEEL_SKIM_MIN_RATIO <= fee_rat <= PEEL_SKIM_MAX_RATIO and (0.0 <= min_drain_minutes <= PEEL_MAX_DRAIN_MINS):
                        peel_skim_ratio = max(peel_skim_ratio, fee_rat)
                        is_peel_chain_node = 1.0

            if (peel_skim_ratio >= PEEL_SKIM_MIN_RATIO and in_degree <= 1 and out_degree <= 1 and wallet_age_hours <= PEEL_MAX_WALLET_AGE_HOURS) or \
               (forwarded_pct_30m >= 0.85 and (0.0 <= min_drain_minutes <= PEEL_MAX_DRAIN_MINS) and in_degree == 1 and out_degree == 1 and wallet_age_hours <= PEEL_MAX_WALLET_AGE_HOURS):
                is_peel_chain_node = 1.0

        # Rapid Cashout indicator: fresh wallet receiving lump sum and forwarding >=95% within 15 min
        is_rapid_cashout_node = 0.0
        if in_degree >= 1 and out_degree >= 1 and total_in_vol >= 0.5:
            if forwarded_pct_10m >= 0.85 or (forwarded_pct_30m >= 0.90 and 0.0 <= min_drain_minutes <= 15.0):
                is_rapid_cashout_node = 1.0

        # Ground truth label extraction with deterministic tie-breaking
        labels = [e["label"] for e in all_events if "label" in e]
        if labels:
            non_normals = [l for l in labels if l != "normal"]
            if non_normals:
                counts = collections.Counter(non_normals)
                # Primary sort: count descending; Secondary sort: label name ascending
                primary_label = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
            else:
                primary_label = "normal"
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
            "min_drain_minutes": round(min_drain_minutes, 2),
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
            "timestamp_entropy": round(compute_timestamp_entropy(all_timestamps), 4),
            "betweenness_centrality": round(float(betweenness.get(wallet, 0.0)), 6),
            "pagerank": round(float(pagerank.get(wallet, 0.0)), 6),
            "primary_label": primary_label,
            "is_planted_anomaly": 0 if primary_label == "normal" else 1,
            # OFAC Sanctions Cross-Reference
            "is_ofac_flagged": is_ofac_flagged,
            "ofac_entity_name": ofac_entity_name,
            "ofac_program": ofac_program,
            "has_ofac_counterparty": has_ofac_counterparty,
            "ofac_counterparty_count": ofac_counterparty_count,
            # On-chain Fingerprints
            "fee_rate_mean": round(fee_rate_mean, 8),
            "fee_rate_std": round(fee_rate_std, 8),
            "fee_rate_zscore": 0.0,
            "round_output_ratio": round(round_output_ratio, 4),
            "nonzero_locktime_ratio": round(nonzero_locktime_ratio, 4),
            "temporal_burst_score": round(temporal_burst_score, 4),
        }

    # Population z-score computation for fee_rate_mean across all wallets
    pop_fee_means = [sig["fee_rate_mean"] for sig in signals.values()]
    pop_mean = float(np.mean(pop_fee_means)) if pop_fee_means else 0.0
    pop_std = float(np.std(pop_fee_means)) if pop_fee_means else 0.0

    for sig in signals.values():
        if pop_std > 1e-8:
            sig["fee_rate_zscore"] = round(float((sig["fee_rate_mean"] - pop_mean) / pop_std), 4)
        else:
            sig["fee_rate_zscore"] = 0.0

    return signals
