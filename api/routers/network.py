from fastapi import APIRouter, Query
from typing import Optional, Dict, Any, List
import os
import networkx as nx
import pandas as pd
from api.data_loader import load_data_bundle, clean_nan

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

    scored_map = scored_df.set_index("wallet_address")["composite_risk_score"].to_dict()
    band_map = scored_df.set_index("wallet_address")["risk_band"].to_dict()

    G_undir = G.to_undirected()
    sub_nodes = set()
    if scope == "ego" and wallet and wallet in G:
        sub_nodes.add(wallet)
        for n1 in list(G_undir.neighbors(wallet)):
            sub_nodes.add(n1)
            for n2 in list(G_undir.neighbors(n1))[:3]:
                sub_nodes.add(n2)
        sub_G = G.subgraph(sub_nodes)
    else:
        top_wallets = list(scored_df.head(25)["wallet_address"])
        sub_nodes = set(top_wallets)
        for w in top_wallets:
            if w in G:
                for n in list(G_undir.neighbors(w))[:2]:
                    sub_nodes.add(n)
                    for ip_n in list(G_undir.neighbors(n))[:2]:
                        sub_nodes.add(ip_n)
        sub_G = G.subgraph(sub_nodes)

    nodes = []
    for node, ndata in sub_G.nodes(data=True):
        ntype = ndata.get("node_type", "wallet")
        if ntype == "wallet":
            score = float(scored_map.get(node, 0.0))
            band = band_map.get(node, "LOW")
            color = (
                "#8B2E2E" if band == "CRITICAL"
                else ("#B8562E" if band == "HIGH"
                else ("#C8973B" if band == "MEDIUM" else "#5B7A6B"))
            )
            size = 18 if band == "CRITICAL" else (14 if band == "HIGH" else 10)
            nodes.append({
                "id": str(node),
                "label": f"{node[:6]}...",
                "full_label": str(node),
                "type": "wallet",
                "risk_band": band,
                "risk_score": round(score, 1),
                "color": color,
                "size": size
            })
        elif ntype == "transaction":
            lbl = ndata.get("label", "normal")
            color = "#7A6B8F" if lbl != "normal" else "#2E4057"
            nodes.append({
                "id": str(node),
                "label": f"tx:{node[:4]}",
                "full_label": str(node),
                "type": "transaction",
                "pattern": lbl,
                "color": color,
                "size": 8
            })
        elif ntype == "ip":
            nodes.append({
                "id": str(node),
                "label": str(node),
                "full_label": str(node),
                "type": "ip",
                "color": "#3E5C76",
                "size": 6
            })

    links = []
    for u, v, edata in sub_G.edges(data=True):
        etype = edata.get("edge_type", "flow")
        amt = edata.get("amount", 0.0)
        links.append({
            "source": str(u),
            "target": str(v),
            "type": etype,
            "amount": float(amt) if amt else 0.0,
            "color": "rgba(232, 230, 222, 0.18)"
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
        "selected_wallet": wallet,
        "node_count": len(nodes),
        "edge_count": len(links),
        "nodes": nodes,
        "links": links,
        "legend": legend
    })
