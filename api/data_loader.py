import os
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

_DATA_CACHE = None

def clean_nan(obj):
    """Recursively replace NaN and inf with None for valid JSON serialization."""
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        return float(obj)
    return obj

def load_data_bundle() -> Dict[str, Any]:
    global _DATA_CACHE
    if _DATA_CACHE is not None:
        return _DATA_CACHE

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    reports_dir = os.path.join(base_dir, "reports")

    scored_path = os.path.join(data_dir, "scored_entities.csv")
    features_path = os.path.join(data_dir, "features.csv")
    clusters_path = os.path.join(data_dir, "clusters.json")
    explanations_path = os.path.join(data_dir, "explanations.json")
    narratives_path = os.path.join(data_dir, "cached_narratives.json")
    comparison_path = os.path.join(reports_dir, "model_comparison.csv")
    eval_metrics_path = os.path.join(reports_dir, "evaluation_metrics.csv")
    tx_path = os.path.join(base_dir, "transactions.json")
    graph_path = os.path.join(base_dir, "graph.gml")

    scored_df = pd.read_csv(scored_path) if os.path.exists(scored_path) else pd.DataFrame()
    features_df = pd.read_csv(features_path) if os.path.exists(features_path) else pd.DataFrame()

    clusters = {}
    if os.path.exists(clusters_path):
        with open(clusters_path, "r", encoding="utf-8") as f:
            clusters = json.load(f)

    explanations = {}
    if os.path.exists(explanations_path):
        with open(explanations_path, "r", encoding="utf-8") as f:
            explanations = json.load(f)

    narratives = {}
    if os.path.exists(narratives_path):
        with open(narratives_path, "r", encoding="utf-8") as f:
            narratives = json.load(f)

    comparison_df = pd.read_csv(comparison_path) if os.path.exists(comparison_path) else pd.DataFrame()
    eval_metrics_df = pd.read_csv(eval_metrics_path) if os.path.exists(eval_metrics_path) else pd.DataFrame()

    transactions = []
    if os.path.exists(tx_path):
        with open(tx_path, "r", encoding="utf-8") as f:
            transactions = json.load(f)

    _DATA_CACHE = {
        "scored_df": scored_df,
        "features_df": features_df,
        "clusters": clusters,
        "explanations": explanations,
        "narratives": narratives,
        "comparison_df": comparison_df,
        "eval_metrics_df": eval_metrics_df,
        "transactions": transactions,
        "graph_path": graph_path,
    }
    return _DATA_CACHE
