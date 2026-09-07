from fastapi import APIRouter
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from api.data_loader import load_data_bundle, clean_nan

router = APIRouter(prefix="/api/models", tags=["models"])

@router.get("")
def get_model_insights():
    data = load_data_bundle()
    scored_df = data["scored_df"]
    comparison_df = data["comparison_df"]

    # 1. Model comparison benchmark table
    comparison_records = comparison_df.to_dict(orient="records") if not comparison_df.empty else []

    # 2. Score distributions for algorithms (quantiles for boxplot)
    algorithms = [
        ("score_iforest", "Isolation Forest", "#5B7A6B"),
        ("score_lof", "Local Outlier Factor", "#C8973B"),
        ("score_mahalanobis", "Robust Mahalanobis", "#B8562E"),
        ("ensemble_anomaly_score", "Blended Ensemble", "#3E5C76")
    ]

    distributions = []
    for col, name, color in algorithms:
        if col in scored_df.columns:
            s = scored_df[col].dropna()
            distributions.append({
                "model_key": col,
                "model_name": name,
                "color": color,
                "min": round(float(s.min()), 4),
                "q1": round(float(s.quantile(0.25)), 4),
                "median": round(float(s.median()), 4),
                "q3": round(float(s.quantile(0.75)), 4),
                "max": round(float(s.max()), 4),
                "mean": round(float(s.mean()), 4),
                "std": round(float(s.std()), 4)
            })

    # 3. IF vs Mahalanobis agreement scatter points (sampled 200 points for light payload)
    scatter_sample = scored_df[["wallet_address", "score_iforest", "score_mahalanobis", "ground_truth_label"]].dropna()
    if len(scatter_sample) > 300:
        scatter_sample = scatter_sample.sample(n=300, random_state=42)
    
    scatter_points = []
    for _, r in scatter_sample.iterrows():
        scatter_points.append({
            "wallet": str(r["wallet_address"]),
            "iforest": round(float(r["score_iforest"]), 4),
            "mahalanobis": round(float(r["score_mahalanobis"]), 4),
            "label": str(r["ground_truth_label"])
        })

    return clean_nan({
        "comparison_benchmark": comparison_records,
        "distributions": distributions,
        "agreement_scatter": scatter_points
    })
