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
import json
import os

import networkx as nx
from networkx.readwrite import json_graph

from transaction_schema import load_transactions_csv, validate_transactions


def load_transactions(path):
    return load_transactions_csv(path)


def build_graph(transactions):
    transactions = validate_transactions(transactions)
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

    validate_graph(G, expected_transaction_count=len(transactions))
    return G


def validate_graph(G, expected_transaction_count=None):
    """Reject graph artifacts that violate the documented tripartite convention."""
    if not isinstance(G, nx.MultiDiGraph):
        raise ValueError(f"Expected networkx.MultiDiGraph, got {type(G).__name__}")

    valid_node_types = {"wallet", "transaction", "ip"}
    for node, data in G.nodes(data=True):
        node_type = data.get("node_type")
        if node_type not in valid_node_types:
            raise ValueError(f"Node {node!r} has invalid node_type {node_type!r}")

    edge_conventions = {
        "funds": ("wallet", "transaction"),
        "pays": ("transaction", "wallet"),
        "broadcasts": ("ip", "transaction"),
        "relays_to": ("transaction", "ip"),
    }
    for source, target, key, data in G.edges(keys=True, data=True):
        edge_type = data.get("edge_type")
        if edge_type not in edge_conventions:
            raise ValueError(f"Edge {(source, target, key)!r} has invalid edge_type {edge_type!r}")
        actual = (G.nodes[source]["node_type"], G.nodes[target]["node_type"])
        if actual != edge_conventions[edge_type]:
            raise ValueError(
                f"Edge {(source, target, key)!r} violates {edge_type!r} convention: {actual}"
            )

    transaction_nodes = [node for node, data in G.nodes(data=True) if data["node_type"] == "transaction"]
    if expected_transaction_count is not None and len(transaction_nodes) != expected_transaction_count:
        raise ValueError(
            f"Expected {expected_transaction_count} transaction nodes, found {len(transaction_nodes)}"
        )
    for txid in transaction_nodes:
        incoming_types = {data.get("edge_type") for _, _, data in G.in_edges(txid, data=True)}
        outgoing_types = {data.get("edge_type") for _, _, data in G.out_edges(txid, data=True)}
        if not {"funds", "broadcasts"}.issubset(incoming_types):
            raise ValueError(f"Transaction {txid!r} is missing funds or broadcasts input edges")
        if not {"pays", "relays_to"}.issubset(outgoing_types):
            raise ValueError(f"Transaction {txid!r} is missing pays or relays_to output edges")

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
