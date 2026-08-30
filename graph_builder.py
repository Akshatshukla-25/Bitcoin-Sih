#!/usr/bin/env python3
"""
graph_builder.py — SIH26146 (NTRO) tripartite transaction graph builder — Part 2

Reads transactions.csv (produced by data_gen.py) and builds a tripartite
networkx.MultiDiGraph with three node types: {ip, wallet, transaction}.

Edge direction convention (documented here per spec 3.3 — do not change
without updating this comment, downstream code depends on it):

    wallet      -> transaction   "funds"    : wallet is an input, weight=amount contributed
    transaction -> wallet        "pays"     : wallet is an output, weight=amount received
    ip          -> transaction   "broadcasts": src_ip is the node that broadcast the tx
    transaction -> ip            "relays_to" : dst_ip is the peer the tx propagated toward

This gives every transaction node at least one wallet edge in each direction
and at least one ip edge in each direction, so wallet/ip/transaction nodes are
never left disconnected from one another.

Output: graph.gml and graph.json (node-link format) in --outdir, plus a
printed summary (node counts by type, edge count, tripartite linkage spot check).

Usage:
    python3 graph_builder.py [--input transactions.csv] [--outdir DIR]
"""

import argparse
import csv
import json
import os

import networkx as nx
from networkx.readwrite import json_graph


def load_transactions(path):
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


def build_graph(transactions):
    G = nx.MultiDiGraph()

    for tx in transactions:
        txid = tx["txid"]
        G.add_node(
            txid,
            node_type="transaction",
            timestamp=tx["timestamp"],
            fee=tx["fee"],
            script_type=tx["script_type"],
            label=tx.get("_ground_truth_label", ""),
        )

        for inp in tx["input_wallet_addresses"]:
            addr, amt = inp["address"], float(inp["amount"])
            if addr not in G:
                G.add_node(addr, node_type="wallet")
            G.add_edge(addr, txid, amount=amt, edge_type="funds")

        for out in tx["output_wallet_addresses"]:
            addr, amt = out["address"], float(out["amount"])
            if addr not in G:
                G.add_node(addr, node_type="wallet")
            G.add_edge(txid, addr, amount=amt, edge_type="pays")

        src_ip, dst_ip = tx["src_ip"], tx["dst_ip"]
        if src_ip not in G:
            G.add_node(src_ip, node_type="ip")
        G.add_edge(src_ip, txid, port=tx["src_port"], edge_type="broadcasts")

        if dst_ip not in G:
            G.add_node(dst_ip, node_type="ip")
        G.add_edge(txid, dst_ip, port=tx["dst_port"], edge_type="relays_to")

    return G


def summarize(G):
    counts = {"transaction": 0, "wallet": 0, "ip": 0}
    for _, data in G.nodes(data=True):
        nt = data.get("node_type", "?")
        counts[nt] = counts.get(nt, 0) + 1

    print(f"Total nodes: {G.number_of_nodes()}")
    for k in ["transaction", "wallet", "ip"]:
        print(f"  {k}: {counts.get(k, 0)}")
    print(f"Total edges: {G.number_of_edges()}")

    # Tripartite linkage spot check: find a wallet -> tx -> ip path, preferring
    # a wallet touched by a planted (non-normal) pattern if one is available.
    found = None
    preferred = None
    for n, data in G.nodes(data=True):
        if data.get("node_type") != "wallet":
            continue
        for _, tx_node in G.out_edges(n):
            if G.nodes[tx_node].get("node_type") != "transaction":
                continue
            for _, ip_node in G.out_edges(tx_node):
                if G.nodes[ip_node].get("node_type") == "ip":
                    candidate = (n, tx_node, ip_node)
                    if found is None:
                        found = candidate
                    if G.nodes[tx_node].get("label") not in ("", "normal") and preferred is None:
                        preferred = candidate
    chosen = preferred or found
    if chosen:
        w, t, i = chosen
        label = G.nodes[t].get("label")
        print(f"Tripartite linkage spot check: wallet '{w}' -> tx '{t}' (label={label}) -> ip '{i}'  [OK]")
    else:
        print("WARNING: could not confirm a wallet -> tx -> ip path in spot check!")

    return counts


def main():
    parser = argparse.ArgumentParser(description="SIH26146 Part 2 — tripartite transaction graph builder")
    parser.add_argument("--input", type=str, default="transactions.csv", help="path to transactions.csv from Part 1")
    parser.add_argument("--outdir", type=str, default=".", help="output directory")
    args = parser.parse_args()

    transactions = load_transactions(args.input)
    G = build_graph(transactions)

    print("=" * 60)
    print("SIH26146 Part 2 — graph_builder.py summary")
    print("=" * 60)
    print(f"Input rows: {len(transactions)}")
    counts = summarize(G)

    os.makedirs(args.outdir, exist_ok=True)
    gml_path = os.path.join(args.outdir, "graph.gml")
    json_path = os.path.join(args.outdir, "graph.json")

    nx.write_gml(G, gml_path)
    data = json_graph.node_link_data(G, edges="edges")
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Wrote: {gml_path}")
    print(f"Wrote: {json_path}")


if __name__ == "__main__":
    main()
