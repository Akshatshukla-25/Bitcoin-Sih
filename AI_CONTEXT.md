# SIH26146 — AI Architecture & Technical Reference Manual
**System Name: NTRO Bitcoin Laundering Detection & Monitoring System**  
**Repository: `Bitcoin-Sih` • Sponsoring Agency: National Technical Research Organisation (NTRO)**  
**Target Audience: Coding Agents & Autonomous LLMs (Context Compression Document)**

> [!IMPORTANT]
> **Instructions for AI Agents**:  
> Read this document first. Do not scan all raw Python or TypeScript files unless modifying specific lines. This document contains the verified system architecture, file manifests, data contracts, schemas, API endpoints, and invariants.

---

## 1. System Invariants & Non-Negotiables

1. **100% Offline Air-Gapped Operation**:
   - Zero runtime HTTP/DNS/socket network requests.
   - All GeoIP lookups resolve against the local offline CIDR database in `data/geoip/`.
   - Python dependencies must be standard, offline-installable packages in `requirements.txt`.
   - Frontend is Next.js 14 with all static fonts and packages bundled locally (zero CDN dependencies).
2. **Deterministic Reproducibility**:
   - Any script utilizing pseudo-randomness must explicitly seed both `random.seed(42)` and `numpy.random.seed(42)`.
   - All community clustering (Louvain) and dataframe sorting operations use canonical lexical tie-breaking (`mergesort` with secondary keys).
   - Re-running `python3 pipeline.py` must produce byte-identical files in `data/` and `reports/` (verified via `git status -s`).
3. **Tripartite Graph Schema & Edge Direction Invariant**:
   - Graph type: `networkx.MultiDiGraph`.
   - Node classes (`node_type`):
     - `wallet`: Bitcoin address (Base58 or Bech32).
     - `transaction`: 64-char transaction hash (`txid`).
     - `ip`: IPv4 address string.
   - Directed Edge Semantics (Strictly enforced by `graph_builder.validate_graph`):
     - `wallet -> tx` (`funds`): Amount in BTC contributed by the input wallet UTXO.
     - `tx -> wallet` (`pays`): Amount in BTC disbursed to the output wallet UTXO.
     - `ip -> tx` (`broadcasts`): Source IP broadcasting the transaction to the P2P gossip network.
     - `tx -> ip` (`relays_to`): Peer node receiving the transaction relay.
   - **Never invert or modify these edge directions** — downstream feature extraction (`graph_signals.py`) and visualization rely directly on this convention.
4. **Data Isolation**:
   - Production artifacts reside in `data/` and `reports/`.
   - The FastAPI backend serves these static artifacts via `api/data_loader.py` with thread-safe file signature caching (`_CACHE_LOCK`).

---

## 2. Codebase Manifest & Component Directory

```
.
├── transaction_schema.py   # Shared transaction CSV/JSON validation & parsing
├── data_gen.py             # Deterministic synthetic Bitcoin transaction generator
├── graph_builder.py        # Tripartite MultiDiGraph constructor & schema validator
├── geoip.py                # Pure offline CIDR routing table & GeoIP resolver
├── features.py             # Wallet-level feature store extractor (45 features)
├── graph_signals.py        # Network topology & transaction velocity signals
├── clustering.py           # Multi-heuristic address clustering (CIOH + CADH + PCCH)
├── models.py               # 3-Model unsupervised anomaly ensemble (IForest, LOF, Mahalanobis)
├── scoring.py              # Composite risk scoring, risk banding & reason codes
├── explain.py              # SHAP TreeExplainer feature attributions & reason summaries
├── narrative.py            # FIU/NTRO case briefs & standardized SAR/STR JSON export
├── model_comparison.py     # Benchmark vs PyOD baselines under contamination calibration
├── evaluate.py             # Ground-truth evaluation metrics, ROC/PR curves, confusion matrices
├── pipeline.py             # Master pipeline runner orchestrating all 11 stages
├── app.py                  # Legacy Streamlit dashboard (retained as working fallback)
├── api/                    # Thin offline FastAPI backend
│   ├── main.py             # FastAPI entrypoint, CORS, and route registration
│   ├── data_loader.py      # Authoritative thread-safe artifact loader with signature caching
│   └── routers/
│       ├── overview.py     # /api/overview (KPIs, histograms, timelines, jurisdictions)
│       ├── alerts.py       # /api/alerts (Paginated, filtered, deterministic alert queue)
│       ├── cases.py        # /api/cases/{wallet} & /api/cases/{wallet}/sar
│       ├── network.py      # /api/network (Top 30 subgraph & 2-hop ego subgraphs)
│       ├── models.py       # /api/models (Feature importances, score distributions)
│       └── evaluation.py   # /api/evaluation (Benchmark tables, ROC/PR points, confusion matrices)
├── web/                    # Luxury Next.js 14 Frontend Dashboard
│   ├── src/app/
│   │   ├── layout.tsx      # Global root layout with luxury dark theme
│   │   ├── page.tsx        # Public landing hero with direct link to dashboard
│   │   └── dashboard/
│   │       ├── layout.tsx  # Dashboard frame with sidebar filters & tab navigation
│   │       ├── page.tsx    # Tab 1: Overview & National Telemetry
│   │       ├── alerts/     # Tab 2: Alert Queue Table
│   │       ├── cases/      # Tab 3: Case Dossier & Intelligence Package
│   │       ├── network/    # Tab 4: Tripartite Graph Studio
│   │       ├── models/     # Tab 5: ML Models & Anomaly Insights
│   │       └── evaluation/ # Tab 6: Regulatory Evaluation & ROC Analysis
│   └── src/components/     # Modular React client components (Recharts, Canvas Graph, Filters)
├── data/                   # Precomputed pipeline artifacts (JSON, CSV, GML, joblib)
└── reports/                # Evaluation reports (metrics CSV, comparison CSV, PNG curves)
```

---

## 3. Pipeline Stages & Execution Specifications

The master pipeline is orchestrated via `python3 pipeline.py` with standard flags `--count 683 --seed 42`:

| Step | Script | Execution Responsibility | Key Inputs | Output Artifacts |
| :---: | :--- | :--- | :--- | :--- |
| **1/11** | `data_gen.py` | Generates synthetic Bitcoin transactions with planted laundering typologies. | `--count`, `--seed` | `data/transactions.csv`, `data/transactions.json` |
| **2/11** | `graph_builder.py` | Builds and validates the tripartite `networkx.MultiDiGraph`. | `data/transactions.csv` | `data/graph.gml`, `data/graph.json` |
| **3/11** | `geoip.py` | Verifies offline CIDR routing database integrity. | `data/geoip/` | Pre-parsed in-memory routing table |
| **4/11** | `features.py` | Extracts 45 graph, temporal, flow, and network features per wallet. | `transactions`, `graph` | `data/features.csv` |
| **5/11** | `clustering.py` | Union-Find DSU clustering (CIOH, CADH, PCCH) + Louvain communities. | `transactions`, `features` | `data/wallet_clusters.csv`, `data/clusters.json` |
| **6/11** | `models.py` | Trains 3 unsupervised models, variance-normalizes and blends anomaly scores. | `data/features.csv` | `data/anomaly_scores.csv`, `data/model_artifacts.joblib` |
| **7/11** | `scoring.py` | Blends ML score (50%), graph structural risk (30%), community risk (20%). | `anomaly_scores`, `clusters` | `data/scored_entities.csv`, `data/alerts.json` |
| **8/11** | `explain.py` | Computes TreeExplainer SHAP attribution vectors for Isolation Forest. | `features`, `model_artifacts` | `data/explanations.json` |
| **9/11** | `narrative.py` | Generates plain-language forensic briefs and pre-caches SAR JSON documents. | `scored_entities`, `explanations` | `data/cached_narratives.json` |
| **10/11**| `model_comparison.py`| Benchmarks ensemble against PyOD baselines (CBLOF, PCA, LOF, kNN, HBOS). | `data/features.csv` | `reports/model_comparison.csv` |
| **11/11**| `evaluate.py` | Computes policy confusion matrices, Precision/Recall, and ROC/PR points. | `data/scored_entities.csv` | `reports/evaluation_metrics.csv`, PNG charts |

---

## 4. Data Schemas & Column Dictionaries

### A. `transactions.csv` / `transactions.json`
- `timestamp`: ISO-8601 string (`2025-01-01T...`).
- `txid`: 64-character SHA-256 transaction hash.
- `input_wallet_addresses`: JSON list of `{"address": str, "amount": float}`.
- `output_wallet_addresses`: JSON list of `{"address": str, "amount": float}`.
- `total_input_amount`: Float satoshi balance in BTC.
- `fee`: Float miner fee in BTC.
- `script_type`: Script standard (`P2PKH`, `P2SH`, `P2WPKH`, `P2WSH`).
- `src_ip`, `src_port`: Originating broadcast node IP and port.
- `dst_ip`, `dst_port`: First-hop peer relay node IP and port.
- `_ground_truth_label`: Class label (`normal`, `peel_chain`, `mixer`, `rapid_cashout`).

### B. `features.csv` (45 Total Columns)
1. **Identifiers & Counts**: `wallet_address`, `tx_count`, `in_degree`, `out_degree`, `degree_ratio`, `fanin_count`, `fanout_count`.
2. **Financial Volumes & Turnover**: `total_received_amount`, `total_sent_amount`, `net_balance`, `turnover_ratio` ($\frac{\text{sent}}{\text{received}}$).
3. **Temporal Dynamics**: `avg_hop_interval_mins`, `median_hop_interval_mins`, `min_hop_interval_mins`, `max_hop_interval_mins`, `min_drain_minutes`, `wallet_age_hours`.
4. **Extraction Velocity**: `forwarded_pct_10m`, `forwarded_pct_30m`, `forwarded_pct_60m`, `forwarded_pct_120m`, `transient_velocity`, `velocity_drain_score`.
5. **Typology Signals**: `peel_skim_ratio`, `peel_signal`, `fanout_burst_signal`, `fanin_burst_signal`, `is_peel_chain_node`, `is_mixer_hub`, `is_mixer_intermediate`, `is_rapid_cashout_node`.
6. **Network & Graph Topology**: `unique_counterparties`, `unique_ips_count`, `unique_src_ips_count`, `unique_countries_count`, `unique_src_countries_count`, `unique_asns_count`, `unique_src_asns_count`, `dominant_country`, `dominant_asn`, `timestamp_entropy`, `betweenness_centrality`, `pagerank`.
7. **Evaluation Labels**: `ground_truth_label`, `is_planted_anomaly` (Binary: 1 for illicit, 0 for normal).

### C. `scored_entities.csv`
Contains all feature columns merged with:
- `ensemble_anomaly_score`: Continuous raw ML anomaly score $[0.0, 1.0]$.
- `composite_risk_score`: Scaled composite score $[0.0, 100.0]$:
  $$\text{Composite} = 0.50 \cdot (\text{ML} \cdot 100) + 0.30 \cdot (\text{GraphStructural} \cdot 100) + 0.20 \cdot (\text{CommunityRisk} \cdot 100)$$
- `risk_band`: Categorical risk tier:
  - `CRITICAL`: Score $\ge 60.0$
  - `HIGH`: $50.0 \le \text{Score} < 60.0$
  - `MEDIUM`: $35.0 \le \text{Score} < 50.0$
  - `LOW`: $\text{Score} < 35.0$
- `confidence_score`: Forensic confidence $[0.0, 1.0]$ based on feature coverage and cluster cohesion.
- `reason_codes`: Semicolon-delimited triggered indicators (`PEEL_CHAIN`, `MIXER_FANOUT`, `RAPID_CASHOUT`, `CROSS_BORDER_HOP`, `NEW_WALLET_HIGH_VOLUME`).

### D. `cached_narratives.json` & SAR Export Structure
Keyed by `wallet_address`:
```json
{
  "report_type": "SUSPICIOUS_ACTIVITY_REPORT_STR_SAR",
  "report_id": "SAR-NTRO-2025-BC1QF44P",
  "timestamp_utc": "2025-01-16T23:53:34.549824+00:00",
  "agency": "National Technical Research Organisation (NTRO) / FIU-IND Reference",
  "investigation_case": "SIH26146-BITCOIN-TRAFFIC-MONITOR",
  "subject_entity": {
    "primary_wallet_address": "bc1q...",
    "composite_risk_score": 98.8,
    "risk_band": "CRITICAL",
    "cluster_id": "CLUSTER_0441",
    "cluster_confidence": 0.94,
    "dominant_jurisdiction": "Australia",
    "origin_asn": "AS13335 Cloudflare Inc"
  },
  "detected_typologies": ["RAPID_CASHOUT", "CROSS_BORDER_HOP"],
  "financial_summary": {
    "total_received_btc": 5.4,
    "total_sent_btc": 5.2,
    "turnover_ratio": 0.96,
    "drain_velocity_10m": 0.96
  },
  "explainability": {
    "top_shap_features": [
      {"feature": "forwarded_pct_10m", "shap_value": 0.142},
      {"feature": "unique_countries_count", "shap_value": 0.089}
    ]
  },
  "forensic_investigator_narrative": "...",
  "recommended_action": "Analyst review and corroboration; consider STR/SAR filing if warranted",
  "disclaimer": "Draft investigative aid generated from synthetic/offline analytical data; not a legal conclusion or automatic enforcement directive."
}
```

---

## 5. FastAPI Backend API Contract

All endpoints are hosted at `http://127.0.0.1:8000` and documented at `/docs`:

### 1. `GET /api/overview`
- **Purpose**: System KPIs, score histogram, reason code frequency, daily volume timeline.
- **Response**:
  ```json
  {
    "kpis": {
      "total_entities": 699,
      "active_alerts": 171,
      "critical_count": 95,
      "high_count": 22,
      "medium_count": 54,
      "low_count": 528,
      "flagged_volume_btc": 693.9498,
      "total_transactions": 683
    },
    "histogram": [...],
    "reason_codes": [...],
    "jurisdictions": [...],
    "volume_timeline": [...]
  }
  ```

### 2. `GET /api/alerts`
- **Query Params**:
  - `bands`: Comma-separated (`CRITICAL,HIGH,MEDIUM`)
  - `min_score`: Float ($0.0 - 100.0$, default `35.0`)
  - `country`: String (default `ALL`)
  - `search`: Search query string
  - `limit`: Integer (default `100`)
  - `offset`: Integer (default `0`)
  - `sort_by`: `composite_risk_score` | `wallet_address` | `risk_band` | `confidence_score` | `total_received_amount` | `tx_count`
  - `sort_dir`: `asc` | `desc`
- **Response**: `{"total_matching": int, "limit": int, "offset": int, "entities": [...], "available_countries": [...], "available_bands": [...]}`

### 3. `GET /api/cases/{wallet_address}`
- **Purpose**: Comprehensive forensic case profile, SHAP breakdown, counterparty clusters, directed transaction history.
- **Response**: Profile JSON with `shap_features`, `cluster_details`, `co_spending_wallets`, and `transactions`.

### 4. `GET /api/cases/{wallet_address}/sar`
- **Purpose**: Downloadable official SAR/STR JSON export package.
- **Headers**: `Content-Disposition: attachment; filename="SAR_CASE_<WALLET>.json"`

### 5. `GET /api/network`
- **Query Params**:
  - `scope`: `top30` (default) | `ego`
  - `wallet`: Required when `scope=ego`
- **Response**:
  ```json
  {
    "scope": "ego",
    "selected_wallet": "bc1q...",
    "node_count": 28,
    "edge_count": 34,
    "nodes": [{"id": str, "label": str, "full_label": str, "type": "wallet"|"transaction"|"ip", "is_ego_center": bool, "color": str, "size": int, ...}],
    "links": [{"id": "src|dst|key", "key": str, "source": str, "target": str, "type": str, "amount": float, "port": int, ...}],
    "legend": [...]
  }
  ```

### 6. `GET /api/models`
- **Purpose**: SHAP feature importance rankings, score distribution statistics per model, and IF vs Mahalanobis 2D scatter points.

### 7. `GET /api/evaluation`
- **Purpose**: Algorithm comparison benchmark table, confusion matrices for the 3 triage tiers, and downsampled ROC/PR curve points.

### 8. `GET /api/health`
- **Purpose**: Liveness probe returning system readiness, offline status, and entity counts.

---

## 6. Frontend Architecture (`web/`)

- **Framework**: Next.js 14.2 (App Router, React 18, TypeScript).
- **Styling**: Tailwind CSS + Custom Obsidian Glassmorphism palette:
  - Base: `#05070B` (Canvas), `#0B1220` (Card Base), `#131B2E` (Card Surface), `#1F2A44` (Border).
  - Accents: `#C8973B` (Gold Accent), `#38BDF8` (Cyan Network), `#8B2E2E` (Critical Red), `#5B7A6B` (Normal Green).
- **Core Components**:
  - `NetworkGraphView.tsx`: HTML5 Canvas directed graph visualizer with curved quadratic bezier parallel edges, zoom/pan transforms, node/edge inspector side drawer, and accessible HTML tabular fallback.
  - `CaseDetailView.tsx`: Forensic case dossier with Recharts horizontal SHAP bar chart, counterparty cluster list, embedded ego network, and SAR JSON download.
  - `AlertQueueTable.tsx`: Interactive sorting, search, pagination, and RFC 4180 CSV export with quotation escaping.
  - `TabNavigation.tsx`: Navigation bar with preserved query parameters carrying active wallet selection across tabs.

---

## 7. Developer Runbook & Execution Guide

### A. Run Full Offline Pipeline
```bash
# Deterministic execution with fixed seed 42 (~3.4 seconds)
python3 pipeline.py
```

### B. Launch FastAPI Backend
```bash
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

### C. Launch Next.js Dashboard
```bash
cd web
npm run build    # Verify 0 build errors across all routes
npm run start    # Production server on http://localhost:3000
```

### D. Verify Determinism
```bash
python3 pipeline.py
git status -s data/ reports/
# Must return zero diffs
```
