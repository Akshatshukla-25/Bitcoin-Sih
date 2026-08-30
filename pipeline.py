#!/usr/bin/env python3
"""
pipeline.py — SIH26146 (NTRO) End-to-End Master Pipeline Orchestrator

Executes the complete Bitcoin AML monitoring pipeline deterministically:
  1. Part 1: Synthetic Bitcoin transaction dataset generation (data_gen.py)
  2. Part 2: Tripartite IP/Wallet/Tx graph construction (graph_builder.py)
  3. Part 3: Offline GeoIP & ASN database enrichment (geoip.py)
  4. Part 3: Wallet-Entity feature store engineering (features.py)
  5. Part 3: Heuristic & Community Entity Clustering (clustering.py)
  6. Part 3: 3-Model Unsupervised Anomaly Detection Ensemble (models.py)
  7. Part 3: Composite Risk Scoring & Alert Banding (scoring.py)
  8. Part 3: SHAP TreeExplainer & Plain-Language Reasons (explain.py)
  9. Part 3: Law Enforcement SAR/STR Case Narratives (narrative.py)
  10. Part 3: Model Comparison & PyOD Benchmark (model_comparison.py)
  11. Part 3: Evaluation Suite & Confusion/ROC Visualizations (evaluate.py)

Usage:
  python3 pipeline.py [--count 683] [--seed 42] [--outdir data]
"""

import os
os.environ["MPLCONFIGDIR"] = "/tmp/mpl_config"

import argparse
import sys
import time

def run_step(step_name: str, func, *args, **kwargs):
    print(f"\n>>> [STEP] {step_name}...")
    t0 = time.perf_counter()
    res = func(*args, **kwargs)
    dt = time.perf_counter() - t0
    print(f"    [COMPLETED] in {dt:.2f}s")
    return res

def main():
    parser = argparse.ArgumentParser(description="SIH26146 Master Pipeline Orchestrator")
    parser.add_argument("--count", type=int, default=683, help="total transaction count")
    parser.add_argument("--seed", type=int, default=42, help="random seed for determinism")
    parser.add_argument("--data-dir", type=str, default="data", help="data output directory")
    parser.add_argument("--reports-dir", type=str, default="reports", help="reports output directory")
    args = parser.parse_args()

    os.makedirs(args.data_dir, exist_ok=True)
    os.makedirs(args.reports_dir, exist_ok=True)

    print("=" * 75)
    print("SIH26146 — NTRO BITCOIN LAUNDERING DETECTION & MONITORING PIPELINE")
    print("Runtime: 100% Pure Python, Fully Offline Air-Gapped Operation")
    print(f"Seed: {args.seed} | Transactions: {args.count}")
    print("=" * 75)

    # 1. Data Generation
    import data_gen
    def step_data_gen():
        txs, counts = data_gen.generate_dataset(args.count, args.seed)
        data_gen.write_outputs(txs, ".")
        return len(txs)
    run_step("1/11 Generating synthetic Bitcoin blockchain + network transactions", step_data_gen)

    # 2. Graph Builder
    import graph_builder
    def step_graph_builder():
        txs = graph_builder.load_transactions("transactions.csv")
        G = graph_builder.build_graph(txs)
        import networkx as nx
        from networkx.readwrite import json_graph
        import json
        nx.write_gml(G, "graph.gml")
        data = json_graph.node_link_data(G, edges="edges")
        with open("graph.json", "w") as f:
            json.dump(data, f, indent=2)
        return G.number_of_nodes(), G.number_of_edges()
    run_step("2/11 Building Tripartite IP-Wallet-Tx Network Graph", step_graph_builder)

    # 3. GeoIP Database
    import geoip
    run_step("3/11 Verifying Offline GeoIP & ASN Database", geoip.ensure_geoip_database)

    # 4. Feature Store
    import features
    def step_features():
        df = features.build_feature_table("transactions.csv", "graph.gml")
        df.to_csv(os.path.join(args.data_dir, "features.csv"), index=False)
        return len(df)
    run_step("4/11 Engineering Wallet-Entity Feature Store", step_features)

    # 5. Entity Clustering
    import clustering
    def step_clustering():
        return clustering.cluster_wallets("transactions.csv", os.path.join(args.data_dir, "features.csv"), args.data_dir)
    run_step("5/11 Running Multi-Input + Change Heuristics & Louvain Community Clustering", step_clustering)

    # 6. ML Anomaly Ensemble
    import models
    def step_models():
        return models.run_models_pipeline(os.path.join(args.data_dir, "features.csv"), args.data_dir)
    run_step("6/11 Training 3-Model Unsupervised Anomaly Detection Ensemble (IForest, LOF, Mahalanobis)", step_models)

    # 7. Composite Risk Scoring
    import scoring
    def step_scoring():
        return scoring.calculate_composite_scores(
            os.path.join(args.data_dir, "anomaly_scores.csv"),
            os.path.join(args.data_dir, "wallet_clusters.csv"),
            os.path.join(args.data_dir, "clusters.json"),
            args.data_dir
        )
    run_step("7/11 Computing Composite Risk Scores, Banding & Reason Codes", step_scoring)

    # 8. SHAP Explainability
    import explain
    def step_explain():
        return explain.generate_shap_explanations(
            os.path.join(args.data_dir, "scored_entities.csv"),
            os.path.join(args.data_dir, "model_artifacts.joblib"),
            args.data_dir
        )
    run_step("8/11 Generating SHAP TreeExplainer Attributions & Plain-Language Reason Summaries", step_explain)

    # 9. SAR Case Narratives
    import narrative
    def step_narrative():
        return narrative.cache_top_narratives(
            os.path.join(args.data_dir, "scored_entities.csv"),
            os.path.join(args.data_dir, "explanations.json"),
            args.data_dir,
            top_n=50
        )
    run_step("9/11 Generating FIU/NTRO Forensic Case Narratives & SAR Export Packages", step_narrative)

    # 10. Model Comparison Benchmark
    import model_comparison
    def step_model_comparison():
        return model_comparison.run_comparison(os.path.join(args.data_dir, "features.csv"), args.reports_dir)
    run_step("10/11 Benchmarking Models vs PyOD Baselines against Synthetic Ground Truth", step_model_comparison)

    # 11. Evaluation Suite
    import evaluate
    def step_evaluate():
        return evaluate.evaluate_pipeline(os.path.join(args.data_dir, "scored_entities.csv"), args.reports_dir)
    run_step("11/11 Running Performance Evaluation & Generating Visualizations", step_evaluate)

    print("\n" + "=" * 75)
    print("[SUCCESS] SIH26146 Full Pipeline Execution Complete!")
    print(f"All precomputed artifacts ready in '{args.data_dir}/' and '{args.reports_dir}/'.")
    print("Launch dashboard: streamlit run app.py")
    print("=" * 75)

if __name__ == "__main__":
    main()
