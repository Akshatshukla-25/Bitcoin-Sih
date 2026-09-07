import os
import threading
from typing import Any, Dict, Literal, Optional

import networkx as nx
from fastapi import APIRouter, HTTPException, Query

import geoip
from api.data_loader import ArtifactLoadError, clean_nan, load_data_bundle
from graph_builder import validate_graph

router = APIRouter(prefix="/api/network", tags=["network"])

_G_CACHE: nx.MultiDiGraph | None = None
_G_SIGNATURE: tuple[int, int] | None = None
_G_LOCK = threading.RLock()


def get_graph(graph_path: str) -> nx.MultiDiGraph:
    """Load the authoritative graph and refresh it when the artifact changes."""
    global _G_CACHE, _G_SIGNATURE
    with _G_LOCK:
        try:
            stat = os.stat(graph_path)
        except OSError as exc:
            raise ArtifactLoadError(
                f"Required graph artifact '{graph_path}' is unavailable: {exc}. Run 'python3 pipeline.py'."
            ) from exc
        signature = (stat.st_mtime_ns, stat.st_size)
        if _G_CACHE is None or signature != _G_SIGNATURE:
            try:
                graph = nx.read_gml(graph_path)
                validate_graph(graph)
            except (OSError, nx.NetworkXError, ValueError) as exc:
                raise ArtifactLoadError(f"Could not load valid graph artifact '{graph_path}': {exc}") from exc
            _G_CACHE = graph
            _G_SIGNATURE = signature
        return _G_CACHE


def _sorted_neighbors(graph: nx.Graph, node: str) -> list[str]:
    return sorted((str(neighbor) for neighbor in graph.neighbors(node)))


@router.get("")
def get_network(
    wallet: Optional[str] = Query(None, description="Center wallet for ego network"),
    scope: Literal["ego", "top30"] = Query("top30", description="Network scope"),
):
    data = load_data_bundle()
    scored_df = data["scored_df"]
    graph = get_graph(data["graph_path"])

    ordered_scored = scored_df.sort_values(
        ["composite_risk_score", "wallet_address"], ascending=[False, True], kind="mergesort"
    )
    scored_records: Dict[str, Dict[str, Any]] = ordered_scored.set_index("wallet_address").to_dict(orient="index")
    tx_map = {transaction["txid"]: transaction for transaction in data["transactions"]}

    active_wallet = str(wallet).strip() if wallet else None
    if scope == "ego":
        if not active_wallet:
            raise HTTPException(status_code=422, detail="wallet is required when scope=ego")
        if active_wallet not in graph or graph.nodes[active_wallet].get("node_type") != "wallet":
            raise HTTPException(status_code=404, detail=f"Wallet {active_wallet} not found in the graph")

    top_wallet_options = [
        {
            "wallet": str(row["wallet_address"]),
            "score": round(float(row["composite_risk_score"]), 1),
            "band": str(row["risk_band"]),
        }
        for _, row in ordered_scored.head(30).iterrows()
    ]
    if active_wallet and active_wallet in scored_records and all(
        option["wallet"] != active_wallet for option in top_wallet_options
    ):
        active_info = scored_records[active_wallet]
        top_wallet_options.insert(
            0,
            {
                "wallet": active_wallet,
                "score": round(float(active_info["composite_risk_score"]), 1),
                "band": str(active_info["risk_band"]),
            },
        )

    undirected = graph.to_undirected()
    sub_nodes: set[str] = set()
    if scope == "ego" and active_wallet:
        sub_nodes.add(active_wallet)
        for transaction in _sorted_neighbors(undirected, active_wallet):
            sub_nodes.add(transaction)
            sub_nodes.update(_sorted_neighbors(undirected, transaction)[:15])
    else:
        top_wallets = [str(wallet_id) for wallet_id in ordered_scored.head(30)["wallet_address"]]
        sub_nodes.update(top_wallets)
        for wallet_id in top_wallets:
            if wallet_id not in graph:
                continue
            for transaction in _sorted_neighbors(undirected, wallet_id)[:2]:
                sub_nodes.add(transaction)
                neighbors = _sorted_neighbors(undirected, transaction)
                sub_nodes.update(
                    node for node in neighbors if graph.nodes[node].get("node_type") == "ip"
                )
                sub_nodes.update(
                    node for node in neighbors if graph.nodes[node].get("node_type") == "wallet"
                )
    subgraph = graph.subgraph(sub_nodes)

    nodes = []
    for node, node_data in sorted(subgraph.nodes(data=True), key=lambda item: str(item[0])):
        node_id = str(node)
        node_type = node_data.get("node_type")
        if node_type == "wallet":
            info = scored_records.get(node_id, {})
            score = float(info.get("composite_risk_score", 0.0))
            band = str(info.get("risk_band", "LOW"))
            is_center = scope == "ego" and node_id == active_wallet
            color = {"CRITICAL": "#8B2E2E", "HIGH": "#B8562E", "MEDIUM": "#C8973B"}.get(band, "#5B7A6B")
            nodes.append({
                "id": node_id,
                "label": f"{node_id[:6]}...",
                "full_label": node_id,
                "type": "wallet",
                "is_ego_center": is_center,
                "risk_band": band,
                "risk_score": round(score, 1),
                "cluster_id": str(info.get("cluster_id", "N/A")),
                "dominant_country": str(info.get("dominant_country", "Unknown")),
                "dominant_asn": str(info.get("dominant_asn", "Unknown")),
                "total_volume": round(float(info.get("total_received_amount", 0.0)), 4),
                "color": color,
                "size": 24 if is_center else (20 if band == "CRITICAL" else (16 if band == "HIGH" else 12)),
            })
        elif node_type == "transaction":
            tx_info = tx_map.get(node_id, {})
            label = str(tx_info.get("_ground_truth_label", "normal"))
            nodes.append({
                "id": node_id,
                "label": f"tx:{node_id[:4]}",
                "full_label": node_id,
                "type": "transaction",
                "pattern": label,
                "amount": round(float(tx_info.get("total_input_amount", 0.0)), 4),
                "fee": round(float(tx_info.get("fee", 0.0)), 6),
                "script_type": str(tx_info.get("script_type", "Not provided")),
                "color": "#7A6B8F" if label != "normal" else "#2E4057",
                "size": 12 if label != "normal" else 10,
            })
        elif node_type == "ip":
            location = geoip.resolve_ip(node_id)
            nodes.append({
                "id": node_id,
                "label": node_id,
                "full_label": node_id,
                "type": "ip",
                "country": location["country"],
                "country_code": location["country_code"],
                "asn": location["asn"],
                "as_org": location["as_org"],
                "city": location["city"],
                "color": "#3E5C76",
                "size": 9,
            })

    links = []
    for source, target, key, edge_data in sorted(
        subgraph.edges(keys=True, data=True), key=lambda item: (str(item[0]), str(item[1]), str(item[2]))
    ):
        amount = edge_data.get("amount")
        links.append({
            "id": f"{source}|{target}|{key}",
            "key": str(key),
            "source": str(source),
            "target": str(target),
            "type": str(edge_data.get("edge_type", "unknown")),
            "port": edge_data.get("port"),
            "amount": round(float(amount), 4) if amount is not None else None,
            "color": "rgba(232, 230, 222, 0.22)",
        })

    legend = [
        {"label": "Critical Wallet (≥60)", "color": "#8B2E2E", "type": "wallet"},
        {"label": "High Risk Wallet (50-59)", "color": "#B8562E", "type": "wallet"},
        {"label": "Medium Risk Wallet (35-49)", "color": "#C8973B", "type": "wallet"},
        {"label": "Low Risk Wallet", "color": "#5B7A6B", "type": "wallet"},
        {"label": "Anomaly Tx", "color": "#7A6B8F", "type": "transaction"},
        {"label": "Normal Tx", "color": "#2E4057", "type": "transaction"},
        {"label": "IP Node", "color": "#3E5C76", "type": "ip"},
    ]
    return clean_nan({
        "scope": scope,
        "selected_wallet": active_wallet,
        "wallet_options": top_wallet_options,
        "node_count": len(nodes),
        "edge_count": len(links),
        "nodes": nodes,
        "links": links,
        "legend": legend,
    })
