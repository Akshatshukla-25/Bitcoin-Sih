# SIH26146 • AI-Powered Bitcoin Transaction Monitoring & Analysis System
**Smart India Hackathon (SIH 2026) • National Technical Research Organisation (NTRO)**

An air-gapped, offline AI system that fuses blockchain-layer (wallet/UTXO) and network-layer (TCP/IP broadcast/relay) telemetry into a tripartite graph to detect Bitcoin money laundering typologies (peel chains, mixer fan-out/consolidation, and rapid cash-outs).

---

## Key Capabilities
- **Tripartite Graph Fusion**: Fuses 699 wallets, 683 transactions, and 1,366 IP broadcast/relay nodes.
- **Unsupervised Anomaly Ensemble**: Multi-model detection via Isolation Forest, Local Outlier Factor (LOF), and Robust Mahalanobis Distance (10% AML screening prior).
- **Entity Clustering**: Multi-input common spending ownership (CIOH) + constrained single-use change address (CADH) + Louvain modularity with confidence scoring.
- **Offline GeoIP & ASN Enrichment**: Built-in offline GeoIP & Autonomous System (ASN) lookup engine in `data/geoip/`.
- **SHAP Explainability & SAR Generation**: TreeExplainer attributions + automated FIU/NTRO Suspicious Activity Report (SAR/STR) generator.
- **Interactive Streamlit Dashboard**: 6 tabs (Overview, Alert Queue, Case Detail, PyVis Network, Model Insights, Evaluation).

---

## Setup & Installation

```bash
# 1. Clone repository
cd Bitcoin-Sih

# 2. Install dependencies (standard OSS Python packages)
python3 -m pip install -r requirements.txt
```

---

## Quickstart: Running the System

### 1. Execute Full End-to-End Pipeline
```bash
python3 pipeline.py
```
This orchestrates all 11 pipeline stages deterministically in **~3.4 seconds** (warm step time; **~5.6s** cold Python subprocess) and saves precomputed outputs to `data/` and `reports/`.

### 2. Launch the Streamlit Dashboard
```bash
streamlit run app.py
```
Open `http://localhost:8501` to explore the 6 interactive investigation tabs.

### 3. Run Individual Components
- **Data Generator**: `python3 data_gen.py --count 683 --seed 42`
- **Graph Builder**: `python3 graph_builder.py`
- **Feature Store**: `python3 features.py`
- **Clustering Engine**: `python3 clustering.py`
- **Anomaly Ensemble**: `python3 models.py`
- **Composite Scoring**: `python3 scoring.py`
- **SHAP Explainability**: `python3 explain.py`
- **SAR Case Narratives**: `python3 narrative.py`
- **Model Comparison**: `python3 model_comparison.py`
- **Evaluation Suite**: `python3 evaluate.py`

---

## Verification of Air-Gapped Offline Execution
To verify that the system runs 100% offline without network calls:
1. Disconnect your internet connection or run in an isolated sandbox.
2. Re-run `python3 pipeline.py`
3. Launch `streamlit run app.py`
4. Confirm instant sub-second dashboard loading from local precomputed files.
