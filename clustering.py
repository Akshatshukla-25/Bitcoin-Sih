#!/usr/bin/env python3
"""
clustering.py — SIH26146 (NTRO) Wallet Entity Clustering Engine

Implements a two-layer entity identification architecture:
  1. Primary — Heuristic Clustering:
     - Multi-Input Clustering Heuristic (Common Spending Ownership)
     - Change-Address Heuristic (Single-use fresh change output mapping)
  2. Secondary — Community Detection:
     - Louvain modularity optimization on the wallet interaction graph
  3. Disagreement Analysis:
     - Detects structural obfuscation where heuristic grouping diverges from community structure.

Outputs:
  - data/wallet_clusters.csv (wallet -> cluster_id mapping and attributes)
  - data/clusters.json (cluster metadata and entity grouping)
"""

import argparse
import csv
import json
import os
from collections import defaultdict
from typing import Dict, Any, List, Set, Tuple
import networkx as nx
import pandas as pd

class UnionFind:
    """Disjoint Set Union (DSU) with path compression and union by rank."""
    def __init__(self):
        self.parent = {}
        self.rank = {}

    def find(self, x: str) -> str:
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
            return x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str):
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x == root_y:
            return
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1

def perform_heuristic_clustering(transactions: List[Dict[str, Any]]) -> Tuple[UnionFind, Dict[Tuple[str, str], str]]:
    """
    Applies:
      1. Common-Input-Ownership Heuristic (CIOH) — Reid & Harrigan 2011, Meiklejohn et al. 2013 (95% confidence)
      2. Chronological Change-Address Detection (CADH) — Evaluated strictly prior to tx time, 0 data leakage (85% confidence)
      3. Peel-Chain Continuation Heuristic (PCCH) — Forward residual chaining across sequential peel hops (90% confidence)
    """
    uf = UnionFind()
    link_reasons = {}
    
    # Sort chronologically to prevent temporal lookahead data leakage
    sorted_txs = sorted(transactions, key=lambda x: x.get("timestamp", ""))

    # 1. Common-Input-Ownership Heuristic (CIOH)
    for tx in sorted_txs:
        inputs = tx.get("input_wallet_addresses", [])
        if len(inputs) > 1:
            first_addr = inputs[0]["address"]
            for inp in inputs[1:]:
                other_addr = inp["address"]
                if first_addr != other_addr:
                    uf.union(first_addr, other_addr)
                    pair = tuple(sorted([first_addr, other_addr]))
                    link_reasons[pair] = "COMMON_INPUT_OWNERSHIP"

    # 2. Chronological Change-Address & Peel-Chain Continuation Heuristic
    seen_addresses = set()
    for tx in sorted_txs:
        inputs = tx.get("input_wallet_addresses", [])
        outputs = tx.get("output_wallet_addresses", [])
        
        if len(inputs) >= 1 and len(outputs) == 2:
            sender = inputs[0]["address"]
            out_addrs = [o["address"] for o in outputs]
            out_amts = [float(o.get("amount", 0.0)) for o in outputs]
            
            # Freshness evaluated strictly prior to current transaction timestamp (no lookahead)
            fresh_indices = [idx for idx, addr in enumerate(out_addrs) if addr not in seen_addresses and addr != sender]
            
            # Case A: Standard Change Address (exactly 1 fresh output, other output is existing counterparty)
            if len(fresh_indices) == 1:
                change_addr = out_addrs[fresh_indices[0]]
                uf.union(sender, change_addr)
                pair = tuple(sorted([sender, change_addr]))
                if pair not in link_reasons:
                    link_reasons[pair] = "CHANGE_ADDRESS_DETECTION"
                    
            # Case B: Peel-Chain Continuation (2 fresh outputs, but asymmetric forward vs skim structure)
            elif len(fresh_indices) == 2 and sum(out_amts) > 0:
                tot = sum(out_amts)
                ratios = [a / tot for a in out_amts]
                for idx, r in enumerate(ratios):
                    if 0.85 <= r <= 0.995:
                        forward_addr = out_addrs[idx]
                        uf.union(sender, forward_addr)
                        pair = tuple(sorted([sender, forward_addr]))
                        if pair not in link_reasons:
                            link_reasons[pair] = "PEEL_CHAIN_CONTINUATION"

        # Update chronologically seen addresses
        for inp in inputs:
            seen_addresses.add(inp["address"])
        for out in outputs:
            seen_addresses.add(out["address"])

    return uf, link_reasons

def perform_community_detection(transactions: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Constructs undirected co-spending & direct interaction graph and applies Louvain.
    """
    G = nx.Graph()
    for tx in transactions:
        inputs = [i["address"] for i in tx.get("input_wallet_addresses", [])]
        outputs = [o["address"] for o in tx.get("output_wallet_addresses", [])]
        
        # Connect co-inputs
        for i in range(len(inputs)):
            G.add_node(inputs[i])
            for j in range(i + 1, len(inputs)):
                G.add_edge(inputs[i], inputs[j], weight=2.0)
        
        # Connect input to output
        for inp in inputs:
            for out in outputs:
                G.add_node(out)
                if inp != out:
                    if G.has_edge(inp, out):
                        G[inp][out]["weight"] += 1.0
                    else:
                        G.add_edge(inp, out, weight=1.0)

    try:
        communities = nx.community.louvain_communities(G, seed=42)
        community_map = {}
        for comm_id, comm in enumerate(communities):
            for node in comm:
                community_map[node] = comm_id
        return community_map
    except Exception as e:
        import warnings
        warnings.warn(f"Louvain community detection failed ({e}); falling back to connected components.")
        # Fallback to connected components
        components = list(nx.connected_components(G))
        community_map = {}
        for comp_id, comp in enumerate(components):
            for node in comp:
                community_map[node] = comp_id
        return community_map

def cluster_wallets(transactions_path: str = "transactions.csv", features_path: str = "data/features.csv", outdir: str = "data"):
    os.makedirs(outdir, exist_ok=True)
    
    # Load transactions
    with open(transactions_path, newline="") as f:
        reader = csv.DictReader(f)
        transactions = []
        for row in reader:
            row["input_wallet_addresses"] = json.loads(row["input_wallet_addresses"])
            row["output_wallet_addresses"] = json.loads(row["output_wallet_addresses"])
            transactions.append(row)

    # Heuristic Clustering with Link Tracking
    uf, link_reasons = perform_heuristic_clustering(transactions)
    
    # Community Detection
    community_map = perform_community_detection(transactions)

    # Load all known wallets
    if os.path.exists(features_path):
        features_df = pd.read_csv(features_path)
        all_wallets = set(features_df["wallet_address"])
    else:
        all_wallets = set()
        for tx in transactions:
            for i in tx["input_wallet_addresses"]:
                all_wallets.add(i["address"])
            for o in tx["output_wallet_addresses"]:
                all_wallets.add(o["address"])

    # Group into heuristic clusters
    root_to_cluster_id = {}
    cluster_counter = 1
    
    wallet_cluster_records = []
    cluster_groups = defaultdict(list)

    # Map each wallet
    for wallet in sorted(list(all_wallets)):
        root = uf.find(wallet)
        if root not in root_to_cluster_id:
            root_to_cluster_id[root] = f"CLUSTER_{cluster_counter:04d}"
            cluster_counter += 1
        
        cid = root_to_cluster_id[root]
        louvain_id = community_map.get(wallet, -1)
        cluster_groups[cid].append(wallet)

        wallet_cluster_records.append({
            "wallet_address": wallet,
            "cluster_id": cid,
            "root_address": root,
            "louvain_community_id": louvain_id,
        })

    cluster_df = pd.DataFrame(wallet_cluster_records)
    
    # Calculate cluster stats, heuristic rationales, and confidence
    cluster_metadata = {}
    for cid, members in cluster_groups.items():
        sub_df = cluster_df[cluster_df["cluster_id"] == cid]
        unique_louvain = sub_df["louvain_community_id"].nunique()
        has_disagreement = bool(unique_louvain > 1 and len(members) > 2)
        
        # Determine heuristics active for this cluster
        active_heuristics = set()
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                pair = tuple(sorted([members[i], members[j]]))
                if pair in link_reasons:
                    active_heuristics.add(link_reasons[pair])

        if not active_heuristics:
            if len(members) == 1:
                heuristics_list = ["SINGLETON_ENTITY"]
                confidence = 1.0
                rationale = "Singleton entity (no co-spending or change address links observed)."
            else:
                heuristics_list = ["LOUVAIN_COMMUNITY"]
                confidence = 0.65
                rationale = f"Community modularity cluster linking {len(members)} interacting wallets."
        else:
            heuristics_list = sorted(list(active_heuristics))
            if "COMMON_INPUT_OWNERSHIP" in active_heuristics and ("CHANGE_ADDRESS_DETECTION" in active_heuristics or "PEEL_CHAIN_CONTINUATION" in active_heuristics):
                confidence = 0.92
                rationale = f"Multi-heuristic linkage: Common-Input-Ownership (CIOH) + Change/Peel Chaining across {len(members)} addresses."
            elif "COMMON_INPUT_OWNERSHIP" in active_heuristics:
                confidence = 0.95
                rationale = f"Common-Input-Ownership Heuristic (CIOH): {len(members)} addresses co-spent private keys within shared transaction inputs."
            elif "PEEL_CHAIN_CONTINUATION" in active_heuristics:
                confidence = 0.90
                rationale = f"Peel-Chain Continuation Heuristic (PCCH): {len(members)} addresses linked across sequential forward-peeling hops."
            else:
                confidence = 0.85
                rationale = f"Change-Address Detection Heuristic (CADH): {len(members)} addresses linked via chronological single-use change generation."

        cluster_metadata[cid] = {
            "cluster_id": cid,
            "wallet_count": len(members),
            "member_wallets": members,
            "primary_root": uf.find(members[0]),
            "heuristic_reasons": heuristics_list,
            "clustering_confidence": confidence,
            "investigative_rationale": rationale,
            "has_disagreement": has_disagreement,
        }

    cluster_df["obfuscation_disagreement"] = cluster_df["cluster_id"].map(
        lambda cid: cluster_metadata[cid]["has_disagreement"]
    )
    cluster_df["clustering_confidence"] = cluster_df["cluster_id"].map(
        lambda cid: cluster_metadata[cid]["clustering_confidence"]
    )

    csv_out = os.path.join(outdir, "wallet_clusters.csv")
    json_out = os.path.join(outdir, "clusters.json")

    cluster_df.to_csv(csv_out, index=False)
    with open(json_out, "w") as f:
        json.dump(cluster_metadata, f, indent=2)

    return cluster_df, cluster_metadata

def main():
    parser = argparse.ArgumentParser(description="SIH26146 Part 3 — Wallet Clustering Engine")
    parser.add_argument("--input", type=str, default="transactions.csv", help="path to transactions.csv")
    parser.add_argument("--features", type=str, default="data/features.csv", help="path to features.csv")
    parser.add_argument("--outdir", type=str, default="data", help="output directory")
    args = parser.parse_args()

    cluster_df, metadata = cluster_wallets(args.input, args.features, args.outdir)

    multi_wallet_clusters = [c for c in metadata.values() if c["wallet_count"] > 1]
    disagreements = [c for c in metadata.values() if c["has_disagreement"]]

    print("=" * 60)
    print("SIH26146 Part 3 — clustering.py summary")
    print("=" * 60)
    print(f"Total wallets clustered: {len(cluster_df)}")
    print(f"Total unique entity clusters: {len(metadata)}")
    print(f"Multi-wallet clusters: {len(multi_wallet_clusters)}")
    print(f"Max cluster size: {max(c['wallet_count'] for c in metadata.values())}")
    print(f"Clusters with obfuscation disagreement: {len(disagreements)}")
    print(f"Wrote: {os.path.join(args.outdir, 'wallet_clusters.csv')}")
    print(f"Wrote: {os.path.join(args.outdir, 'clusters.json')}")

if __name__ == "__main__":
    main()
