from fastapi import APIRouter
import pandas as pd
import numpy as np
from api.data_loader import load_data_bundle, clean_nan

router = APIRouter(prefix="/api/overview", tags=["overview"])

@router.get("")
def get_overview():
    data = load_data_bundle()
    scored_df = data["scored_df"]
    transactions = data["transactions"]

    total_wallets = len(scored_df)
    alert_mask = scored_df["risk_band"].isin(["MEDIUM", "HIGH", "CRITICAL"])
    total_alerts = int(alert_mask.sum())
    critical_count = int((scored_df["risk_band"] == "CRITICAL").sum())
    high_count = int((scored_df["risk_band"] == "HIGH").sum())
    medium_count = int((scored_df["risk_band"] == "MEDIUM").sum())
    low_count = int((scored_df["risk_band"] == "LOW").sum())
    total_flagged_btc = float(scored_df.loc[alert_mask, "total_received_amount"].sum())

    # 1. Composite Risk Score Histogram (0-100 binned in 20 bins of size 5)
    bins = list(range(0, 105, 5))
    hist_data = []
    for i in range(len(bins) - 1):
        low, high = bins[i], bins[i+1]
        bin_label = f"{low}-{high}"
        sub = scored_df[(scored_df["composite_risk_score"] >= low) & (
            scored_df["composite_risk_score"] <= high if i == len(bins) - 2 else scored_df["composite_risk_score"] < high
        )]
        hist_data.append({
            "bin": bin_label,
            "min": low,
            "max": high,
            "CRITICAL": int((sub["risk_band"] == "CRITICAL").sum()),
            "HIGH": int((sub["risk_band"] == "HIGH").sum()),
            "MEDIUM": int((sub["risk_band"] == "MEDIUM").sum()),
            "LOW": int((sub["risk_band"] == "LOW").sum()),
            "total": len(sub),
        })

    # 2. Triggered Laundering Reason Codes Frequency
    all_reasons = []
    for rc in scored_df["reason_codes"].dropna():
        for code in str(rc).split(";"):
            c = code.strip()
            if c and c != "None":
                all_reasons.append(c)
    rc_counts = pd.Series(all_reasons).value_counts().reset_index()
    rc_counts.columns = ["reason_code", "count"]
    reason_codes_data = rc_counts.to_dict(orient="records")

    # 3. Top Geographic Jurisdictions (GeoIP Origin)
    valid_countries = scored_df[scored_df["dominant_country"] != "Unknown"]
    country_counts = valid_countries["dominant_country"].value_counts().head(8).reset_index()
    country_counts.columns = ["country", "entities"]
    country_data = country_counts.to_dict(orient="records")

    # 4. Flagged Transaction Volume Over Time (Daily Resample)
    tx_timeline = []
    for tx in transactions:
        tx_timeline.append({
            "timestamp": tx.get("timestamp"),
            "amount": tx.get("total_input_amount", 0.0),
            "label": tx.get("_ground_truth_label", "normal")
        })
    tx_df = pd.DataFrame(tx_timeline)
    volume_timeline = []
    if not tx_df.empty:
        tx_df["datetime"] = pd.to_datetime(tx_df["timestamp"], errors="coerce")
        tx_df = tx_df.dropna(subset=["datetime"])
        tx_agg = tx_df.set_index("datetime").resample("1D").agg(
            total_volume=("amount", "sum"),
            tx_count=("amount", "count")
        ).reset_index()
        for _, r in tx_agg.iterrows():
            volume_timeline.append({
                "date": r["datetime"].strftime("%Y-%m-%d"),
                "display_date": r["datetime"].strftime("%b %d"),
                "volume": round(float(r["total_volume"]), 4),
                "count": int(r["tx_count"])
            })

    return clean_nan({
        "kpis": {
            "total_entities": total_wallets,
            "active_alerts": total_alerts,
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "flagged_volume_btc": round(total_flagged_btc, 4),
            "total_transactions": len(transactions),
        },
        "histogram": hist_data,
        "reason_codes": reason_codes_data,
        "jurisdictions": country_data,
        "volume_timeline": volume_timeline,
    })
