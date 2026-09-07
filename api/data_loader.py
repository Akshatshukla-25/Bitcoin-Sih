import json
import math
import threading
from pathlib import Path
from typing import Any, Dict, Iterable

import numpy as np
import pandas as pd


class ArtifactLoadError(RuntimeError):
    """Raised when required pipeline artifacts are missing or invalid."""


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
ARTIFACT_PATHS = {
    "scored_entities": DATA_DIR / "scored_entities.csv",
    "features": DATA_DIR / "features.csv",
    "clusters": DATA_DIR / "clusters.json",
    "explanations": DATA_DIR / "explanations.json",
    "narratives": DATA_DIR / "cached_narratives.json",
    "model_comparison": REPORTS_DIR / "model_comparison.csv",
    "evaluation_metrics": REPORTS_DIR / "evaluation_metrics.csv",
    "transactions": DATA_DIR / "transactions.json",
    "graph": DATA_DIR / "graph.gml",
}

_DATA_CACHE: Dict[str, Any] | None = None
_CACHE_SIGNATURE: tuple[tuple[str, int, int], ...] | None = None
_CACHE_LOCK = threading.RLock()


def clean_nan(obj: Any) -> Any:
    """Recursively convert NumPy values and replace non-finite floats for JSON."""
    if isinstance(obj, np.ndarray):
        return clean_nan(obj.tolist())
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        value = float(obj)
        return value if math.isfinite(value) else None
    if isinstance(obj, dict):
        return {str(key): clean_nan(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [clean_nan(value) for value in obj]
    return obj


def _artifact_signature() -> tuple[tuple[str, int, int], ...]:
    missing = [str(path) for path in ARTIFACT_PATHS.values() if not path.is_file()]
    if missing:
        raise ArtifactLoadError(
            "Required pipeline artifacts are missing: "
            + ", ".join(missing)
            + ". Run 'python3 pipeline.py' from the project root."
        )
    return tuple(
        (name, path.stat().st_mtime_ns, path.stat().st_size)
        for name, path in sorted(ARTIFACT_PATHS.items())
    )


def _require_columns(df: pd.DataFrame, columns: Iterable[str], artifact: Path) -> None:
    missing = sorted(set(columns).difference(df.columns))
    if missing:
        raise ArtifactLoadError(
            f"Artifact '{artifact}' is missing required columns: {', '.join(missing)}. "
            "Re-run 'python3 pipeline.py'."
        )


def _read_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactLoadError(f"Could not read required JSON artifact '{path}': {exc}") from exc


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise ArtifactLoadError(f"Could not read required CSV artifact '{path}': {exc}") from exc


def _load_uncached() -> Dict[str, Any]:
    scored_df = _read_csv(ARTIFACT_PATHS["scored_entities"])
    features_df = _read_csv(ARTIFACT_PATHS["features"])
    comparison_df = _read_csv(ARTIFACT_PATHS["model_comparison"])
    eval_metrics_df = _read_csv(ARTIFACT_PATHS["evaluation_metrics"])
    _require_columns(
        scored_df,
        ["wallet_address", "composite_risk_score", "risk_band", "is_planted_anomaly"],
        ARTIFACT_PATHS["scored_entities"],
    )
    _require_columns(features_df, ["wallet_address"], ARTIFACT_PATHS["features"])
    _require_columns(comparison_df, ["Algorithm", "ROC_AUC", "PR_AUC"], ARTIFACT_PATHS["model_comparison"])
    _require_columns(eval_metrics_df, ["Alert Policy Level", "Precision"], ARTIFACT_PATHS["evaluation_metrics"])
    if scored_df.empty:
        raise ArtifactLoadError("scored_entities.csv contains no entities; re-run the pipeline with --count >= 2")

    clusters = _read_json(ARTIFACT_PATHS["clusters"])
    explanations = _read_json(ARTIFACT_PATHS["explanations"])
    narratives = _read_json(ARTIFACT_PATHS["narratives"])
    transactions = _read_json(ARTIFACT_PATHS["transactions"])
    if not isinstance(clusters, dict):
        raise ArtifactLoadError("clusters.json must contain a JSON object")
    if not isinstance(explanations, dict) or not isinstance(explanations.get("entities", {}), dict):
        raise ArtifactLoadError("explanations.json must contain an object-valued 'entities' field")
    if not isinstance(narratives, dict):
        raise ArtifactLoadError("cached_narratives.json must contain a JSON object")
    if not isinstance(transactions, list):
        raise ArtifactLoadError("transactions.json must contain a JSON array")

    # Reuse the shared transaction validator so API responses cannot expose a
    # stale or malformed transaction artifact.
    from transaction_schema import validate_transactions

    validate_transactions(transactions)
    return {
        "scored_df": scored_df,
        "features_df": features_df,
        "clusters": clusters,
        "explanations": explanations,
        "narratives": narratives,
        "comparison_df": comparison_df,
        "eval_metrics_df": eval_metrics_df,
        "transactions": transactions,
        "graph_path": str(ARTIFACT_PATHS["graph"]),
    }


def load_data_bundle() -> Dict[str, Any]:
    """Load and validate authoritative artifacts, refreshing when files change."""
    global _DATA_CACHE, _CACHE_SIGNATURE
    with _CACHE_LOCK:
        signature = _artifact_signature()
        if _DATA_CACHE is None or signature != _CACHE_SIGNATURE:
            _DATA_CACHE = _load_uncached()
            _CACHE_SIGNATURE = signature
        return _DATA_CACHE


def invalidate_data_cache() -> None:
    """Clear cached artifacts so the next request performs a validated reload."""
    global _DATA_CACHE, _CACHE_SIGNATURE
    with _CACHE_LOCK:
        _DATA_CACHE = None
        _CACHE_SIGNATURE = None
