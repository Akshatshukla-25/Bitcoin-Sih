from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import re
from api.data_loader import load_data_bundle, clean_nan
import narrative

router = APIRouter(prefix="/api/cases", tags=["cases"])

@router.get("/{wallet_address}")
def get_case_detail(wallet_address: str):
    data = load_data_bundle()
    scored_df = data["scored_df"]
    features_df = data["features_df"]
    clusters_json = data["clusters"]
    explanations_json = data["explanations"]
    narratives_json = data["narratives"]
    transactions = data["transactions"]

    match = scored_df[scored_df["wallet_address"] == wallet_address]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Wallet {wallet_address} not found")

    row = match.iloc[0].to_dict()

    # Features for this wallet
    feat_match = features_df[features_df["wallet_address"] == wallet_address]
    features_dict = feat_match.iloc[0].to_dict() if not feat_match.empty else {}

    # Explanations
    exp = explanations_json.get("entities", {}).get(wallet_address, {})
    plain_summary = exp.get("plain_language_explanation", "No automated summary generated.")
    top_features = exp.get("top_features", [])

    # Cluster Info
    cluster_id = str(row.get("cluster_id", "N/A"))
    cluster_meta = clusters_json.get(cluster_id, {})
    cluster_info = {
        "cluster_id": cluster_id,
        "member_wallets": cluster_meta.get("member_wallets", [wallet_address]),
        "heuristic_reasons": cluster_meta.get("heuristic_reasons", ["SINGLETON_ENTITY"]),
        "clustering_confidence": round(float(cluster_meta.get("clustering_confidence", 1.0)), 2),
        "investigative_rationale": cluster_meta.get("investigative_rationale", f"Cluster {cluster_id} links addresses."),
        "total_members": len(cluster_meta.get("member_wallets", [wallet_address]))
    }

    # Narrative
    narrative_obj = narratives_json.get(wallet_address, {})
    narrative_text = narrative_obj.get("narrative", "")
    if not narrative_text:
        narrative_text = narrative.generate_template_narrative(row, exp)

    # Associated Transactions
    wallet_txs = []
    for tx in transactions:
        in_addrs = [inp.get("address") for inp in tx.get("input_wallet_addresses", [])]
        out_addrs = [out.get("address") for out in tx.get("output_wallet_addresses", [])]
        if wallet_address in in_addrs:
            wallet_txs.append({
                "txid": tx.get("txid"),
                "timestamp": tx.get("timestamp"),
                "amount": sum(float(item["amount"]) for item in tx["input_wallet_addresses"] if item["address"] == wallet_address),
                "direction": "OUTGOING",
                "src_ip": tx.get("src_ip"),
                "dst_ip": tx.get("dst_ip"),
                "label": tx.get("_ground_truth_label", "normal")
            })
        if wallet_address in out_addrs:
            wallet_txs.append({
                "txid": tx.get("txid"),
                "timestamp": tx.get("timestamp"),
                "amount": sum(float(item["amount"]) for item in tx["output_wallet_addresses"] if item["address"] == wallet_address),
                "direction": "INCOMING",
                "src_ip": tx.get("src_ip"),
                "dst_ip": tx.get("dst_ip"),
                "label": tx.get("_ground_truth_label", "normal")
            })

    wallet_txs.sort(key=lambda item: (str(item["timestamp"]), str(item["txid"]), item["direction"]), reverse=True)

    return clean_nan({
        "wallet_address": wallet_address,
        "composite_risk_score": round(float(row.get("composite_risk_score", 0.0)), 1),
        "risk_band": str(row.get("risk_band", "LOW")),
        "confidence_score": round(float(row.get("confidence_score", 0.0)), 2),
        "cluster_id": cluster_id,
        "dominant_country": str(row.get("dominant_country", "Unknown")),
        "dominant_asn": str(row.get("dominant_asn", "Unknown")),
        "dominant_ip": str(row.get("dominant_ip", "Unknown")),
        "total_received_amount": round(float(row.get("total_received_amount", 0.0)), 4),
        "total_sent_amount": round(float(row.get("total_sent_amount", 0.0)), 4),
        "reason_codes": str(row.get("reason_codes", "None")),
        "ground_truth_label": str(row.get("ground_truth_label", "normal")),
        "plain_language_explanation": plain_summary,
        "top_features": top_features,
        "cluster_info": cluster_info,
        "narrative_text": narrative_text,
        "features": features_dict,
        "transactions": wallet_txs[:50]
    })

@router.get("/{wallet_address}/sar")
def get_case_sar(wallet_address: str):
    data = load_data_bundle()
    scored_df = data["scored_df"]
    explanations_json = data["explanations"]
    narratives_json = data["narratives"]

    match = scored_df[scored_df["wallet_address"] == wallet_address]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Wallet {wallet_address} not found")

    row = match.iloc[0].to_dict()
    exp = explanations_json.get("entities", {}).get(wallet_address, {})
    narrative_obj = narratives_json.get(wallet_address, {})

    sar_doc = narrative_obj.get("sar_document")
    if not sar_doc or str(sar_doc.get("timestamp_utc", "")).startswith("1970"):
        narrative_text = narrative_obj.get("narrative", "")
        if not narrative_text:
            narrative_text = narrative.generate_template_narrative(row, exp)
        timestamp_column = "last_active" if "last_active" in match.columns else "first_active"
        if timestamp_column in match.columns:
            generated_at = datetime.fromisoformat(str(row[timestamp_column])).replace(tzinfo=timezone.utc)
        else:
            all_transactions = data.get("transactions", [])
            wallet_timestamps = [
                tx["timestamp"]
                for tx in all_transactions
                if tx.get("timestamp") and (
                    any(i.get("address") == wallet_address for i in tx.get("input_wallet_addresses", []))
                    or any(o.get("address") == wallet_address for o in tx.get("output_wallet_addresses", []))
                )
            ]
            if wallet_timestamps:
                generated_at = datetime.fromisoformat(str(max(wallet_timestamps))).replace(tzinfo=timezone.utc)
            elif all_transactions:
                all_ts = [t["timestamp"] for t in all_transactions if t.get("timestamp")]
                generated_at = datetime.fromisoformat(str(max(all_ts))).replace(tzinfo=timezone.utc)
            else:
                generated_at = datetime(2025, 2, 1, tzinfo=timezone.utc)
        sar_doc = narrative.generate_sar_export_document(wallet_address, row, exp, narrative_text, generated_at)

    safe_wallet = re.sub(r"[^A-Za-z0-9_-]", "_", wallet_address)[:32] or "UNKNOWN"
    return JSONResponse(
        content=clean_nan(sar_doc),
        headers={
            "Content-Disposition": f'attachment; filename="SAR_CASE_{safe_wallet}.json"'
        }
    )
