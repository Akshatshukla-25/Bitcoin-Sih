from fastapi import APIRouter, HTTPException, Query
from typing import Literal, Optional

from api.data_loader import load_data_bundle, clean_nan

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

@router.get("")
def get_alerts(
    bands: Optional[str] = Query("CRITICAL,HIGH,MEDIUM", description="Comma-separated risk bands"),
    min_score: float = Query(35.0, ge=0.0, le=100.0, description="Minimum composite risk score (0-100)"),
    country: Optional[str] = Query("ALL", description="Geographic jurisdiction filter"),
    search: Optional[str] = Query("", description="Search term for wallet or cluster ID"),
    limit: int = Query(100, ge=1, le=1000, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    sort_by: Literal["composite_risk_score", "wallet_address", "risk_band", "confidence_score", "total_received_amount", "tx_count"] = Query("composite_risk_score", description="Sort column"),
    sort_dir: Literal["asc", "desc"] = Query("desc", description="Sort direction")
):
    data = load_data_bundle()
    df = data["scored_df"].copy()

    # Filter by risk bands
    if bands:
        selected_bands = [b.strip().upper() for b in bands.split(",") if b.strip()]
        invalid_bands = sorted(set(selected_bands).difference({"CRITICAL", "HIGH", "MEDIUM", "LOW"}))
        if invalid_bands:
            raise HTTPException(status_code=422, detail=f"Unsupported risk bands: {', '.join(invalid_bands)}")
        if selected_bands:
            df = df[df["risk_band"].isin(selected_bands)]

    # Filter by min score
    df = df[df["composite_risk_score"] >= min_score]

    # Filter by country
    if country and country.upper() != "ALL":
        df = df[df["dominant_country"].str.lower() == country.lower()]

    # Filter by search
    if search and search.strip():
        q = search.strip()
        df = df[
            df["wallet_address"].str.contains(q, case=False, na=False, regex=False) |
            df["cluster_id"].str.contains(q, case=False, na=False, regex=False)
        ]

    total_matching = len(df)

    # Sorting
    ascending = sort_dir == "asc"
    if sort_by == "wallet_address":
        df = df.sort_values(by="wallet_address", ascending=ascending, kind="mergesort")
    else:
        df = df.sort_values(
            by=[sort_by, "wallet_address"], ascending=[ascending, True], kind="mergesort"
        )

    # Pagination
    paged = df.iloc[offset : offset + limit]

    entities = []
    for _, r in paged.iterrows():
        entities.append({
            "wallet_address": str(r["wallet_address"]),
            "composite_risk_score": round(float(r["composite_risk_score"]), 1),
            "risk_band": str(r.get("risk_band", "LOW")),
            "confidence_score": round(float(r.get("confidence_score", 0.0)), 2),
            "cluster_id": str(r.get("cluster_id", "N/A")),
            "dominant_country": str(r.get("dominant_country", "Unknown")),
            "dominant_asn": str(r.get("dominant_asn", "Unknown")),
            "dominant_ip": str(r.get("dominant_ip", "Unknown")),
            "total_received_amount": round(float(r.get("total_received_amount", 0.0)), 4),
            "total_sent_amount": round(float(r.get("total_sent_amount", 0.0)), 4),
            "tx_count": int(r.get("tx_count", 0)),
            "reason_codes": str(r.get("reason_codes", "None")),
            "ground_truth_label": str(r.get("ground_truth_label", "normal"))
        })

    all_countries = sorted([
        c for c in data["scored_df"]["dominant_country"].dropna().unique()
        if c and c != "Unknown"
    ])

    return clean_nan({
        "total_matching": total_matching,
        "limit": limit,
        "offset": offset,
        "entities": entities,
        "available_countries": ["ALL"] + all_countries,
        "available_bands": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    })
