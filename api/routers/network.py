from fastapi import APIRouter, Query
from typing import Optional, Dict, Any, List
import os
import networkx as nx
import pandas as pd
from api.data_loader import load_data_bundle, clean_nan

import geoip

router = APIRouter(prefix="/api/network", tags=["network"])

_G_CACHE = None

def get_graph():
    global _G_CACHE
    if _G_CACHE is not None:
        return _G_CACHE
    if os.path.exists("graph.gml"):
        _G_CACHE = nx.read_gml("graph.gml")
    else:
        _G_CACHE = nx.MultiDiGraph()
    return _G_CACHE

@router.get("")
def get_network(
    wallet: Optional[str] = Query(None, description="Center wallet for ego network"),
    scope: str = Query("top30", description="Network scope: 'ego' or 'top30'")
):
    data = load_data_bundle()
    scored_df = data["scored_df"]
    G = get_graph()

    # Pre-build lookup maps for fast node annotation
    scored_records = scored_df.set_index("wallet_address").to_dict(orient="index")
    tx_map = {t["txid"]: t for t in data.get("transactions", [])}

    top_wallet_options = [
        {
            "wallet": str(r["wallet_address"]),
            "score": round(float(r["composite_risk_score"]), 1),
            "band": str(r["risk_band"])
        }
        for _, r in scored_df.head(50).iterrows()
    ]

    G_undir = G.to_undirected()
    sub_nodes = set()

    active_wallet = wallet
    if scope == "ego":
        if not active_wallet or active_wallet not in G:
            active_wallet = scored_df.iloc[0]["wallet_address"]
        
        if active_wallet in G:
            sub_nodes.add(active_wallet)
            for tx in G_undir.neighbors(active_wallet):
                sub_nodes.add(tx)
                for n in list(G_undir.neighbors(tx))[:12]:
                    sub_nodes.add(n)
        sub_G = G.subgraph(sub_nodes)
    else:
        top_wallets = list(scored_df.head(25)["wallet_address"])
        sub_nodes = set(top_wallets)
        for w in top_wallets:
            if w in G:
                for tx in list(G_undir.neighbors(w))[:2]:
                    sub_nodes.add(tx)
                    ips = [n for n in G_undir.neighbors(tx) if G.nodes[n].get("node_type") == "ip"][:2]
                    wallets = [n for n in G_undir.neighbors(tx) if G.nodes[n].get("node_type") == "wallet"][:2]
                    sub_nodes.update(ips)
                    sub_nodes.update(wallets)
        sub_G = G.subgraph(sub_nodes)

    nodes = []
    for node, ndata in sub_G.nodes(data=True):
        ntype = ndata.get("node_type", "wallet")
        if ntype == "wallet":
            info = scored_records.get(node, {})
            score = float(info.get("composite_risk_score", 0.0))
            band = info.get("risk_band", "LOW")
            color = (
                "#8B2E2E" if band == "CRITICAL"
                else ("#B8562E" if band == "HIGH"
                else ("#C8973B" if band == "MEDIUM" else "#5B7A6B"))
            )
            size = 20 if band == "CRITICAL" else (16 if band == "HIGH" else 12)
            nodes.append({
                "id": str(node),
                "label": f"{node[:6]}...",
                "full_label": str(node),
                "type": "wallet",
                "risk_band": band,
                "risk_score": round(score, 1),
                "cluster_id": str(info.get("cluster_id", "N/A")),
                "dominant_country": str(info.get("dominant_country", "Unknown")),
                "dominant_asn": str(info.get("dominant_asn", "Unknown")),
                "total_volume": round(float(info.get("total_received_amount", 0.0)), 4),
                "color": color,
                "size": size
            })
        elif ntype == "transaction":
            tx_info = tx_map.get(node, {})
            lbl = tx_info.get("_ground_truth_label", "normal")
            amt = float(tx_info.get("total_input_amount", 0.0))
            fee = float(tx_info.get("fee", 0.0))
            script = str(tx_info.get("script_type", "P2PKH"))
            color = "#7A6B8F" if lbl != "normal" else "#2E4057"
            nodes.append({
                "id": str(node),
                "label": f"tx:{node[:4]}",
                "full_label": str(node),
                "type": "transaction",
                "pattern": lbl,
                "amount": round(amt, 4),
                "fee": round(fee, 6),
                "script_type": script,
                "color": color,
                "size": 12 if lbl != "normal" else 10
            })
        elif ntype == "ip":
            geo = geoip.resolve_ip(str(node)) or {}
            nodes.append({
                "id": str(node),
                "label": str(node),
                "full_label": str(node),
                "type": "ip",
                "country": geo.get("country", "Unknown"),
                "country_code": geo.get("country_code", "XX"),
                "asn": geo.get("asn", "Unknown"),
                "as_org": geo.get("as_org", "Unknown"),
                "city": geo.get("city", "Unknown"),
                "color": "#3E5C76",
                "size": 9
            })

    links = []
    for u, v, edata in sub_G.edges(data=True):
        etype = edata.get("edge_type", "flow")
        amt = edata.get("amount", 0.0)
        port = edata.get("port", None)
        links.append({
            "source": str(u),
            "target": str(v),
            "type": etype,
            "port": port,
            "amount": round(float(amt), 4) if amt else 0.0,
            "color": "rgba(232, 230, 222, 0.22)"
        })

    legend = [
        {"label": "Critical Wallet (≥60)", "color": "#8B2E2E", "type": "wallet"},
        {"label": "High Risk Wallet (50-59)", "color": "#B8562E", "type": "wallet"},
        {"label": "Medium Risk Wallet (35-49)", "color": "#C8973B", "type": "wallet"},
        {"label": "Normal Wallet", "color": "#5B7A6B", "type": "wallet"},
        {"label": "Anomaly Tx", "color": "#7A6B8F", "type": "transaction"},
        {"label": "Normal Tx", "color": "#2E4057", "type": "transaction"},
        {"label": "IP Node", "color": "#3E5C76", "type": "ip"}
    ]

    return clean_nan({
        "scope": scope,
        "selected_wallet": active_wallet,
        "wallet_options": top_wallet_options,
        "node_count": len(nodes),
        "edge_count": len(links),
        "nodes": nodes,
        "links": links,
        "legend": legend
    })
