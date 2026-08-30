#!/usr/bin/env python3
"""
app.py — SIH26146 (NTRO) AI Bitcoin Transaction Traffic & Laundering Detection Dashboard

Evidence-grade forensic instrument for NTRO investigators.
Case-file / ledger visual identity with block-explorer monospace data discipline.
"""

import os
os.environ["MPLCONFIGDIR"] = "/tmp/mpl_config"

import html
import json
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import altair as alt
import networkx as nx
from pyvis.network import Network
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(
    page_title="NTRO INTERNAL • Bitcoin Forensic Monitor | SIH26146",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# NTRO FORENSIC DOSSIER DESIGN SYSTEM & TOKENS (Offline Air-Gapped Fonts)
# ---------------------------------------------------------------------------
st.html("""
<style>
    :root {
        --nt-bg: #0B1220;
        --nt-surface: #131B2E;
        --nt-surface-raised: #1A2438;
        --nt-border: #1F2A44;
        --nt-text: #E8E6DE;
        --nt-text-muted: #94A3B8;
        --nt-accent: #C8973B;
        --nt-accent-hover: #DDAE55;
        --nt-low: #5B7A6B;
        --nt-medium: #C8973B;
        --nt-high: #B8562E;
        --nt-critical: #8B2E2E;
        --nt-radius: 8px;
        --nt-shadow: 0 4px 24px rgba(0, 0, 0, 0.45);
    }

    .stApp {
        background-color: var(--nt-bg);
        color: var(--nt-text);
        font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }

    /* Display Headers */
    h1, h2, h3, .dossier-title {
        font-family: 'Source Serif 4', Georgia, 'Times New Roman', serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
        color: var(--nt-text) !important;
    }

    h4, h5, h6 {
        font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-weight: 600 !important;
        color: var(--nt-text) !important;
    }

    /* Classification Banners */
    .classification-banner {
        font-family: 'IBM Plex Mono', Menlo, Monaco, Consolas, 'Courier New', monospace;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--nt-accent);
        background: rgba(200, 151, 59, 0.08);
        border: 1px solid rgba(200, 151, 59, 0.25);
        padding: 4px 10px;
        border-radius: 3px;
        display: inline-block;
        margin-bottom: 8px;
    }

    .sidebar-wordmark {
        font-family: 'IBM Plex Mono', Menlo, Monaco, Consolas, 'Courier New', monospace;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: var(--nt-accent);
        border-left: 3px solid var(--nt-accent);
        padding-left: 8px;
        margin-bottom: 4px;
    }

    .sidebar-caption {
        font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 11px;
        color: var(--nt-text-muted);
        margin-bottom: 16px;
    }

    /* Metric Cards */
    .metric-card {
        background: var(--nt-surface);
        border: 1px solid var(--nt-border);
        border-top: 3px solid var(--nt-accent);
        border-radius: var(--nt-radius);
        padding: 16px 20px;
        box-shadow: var(--nt-shadow);
        transition: border-color 0.2s ease, transform 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-top-color: var(--nt-accent-hover);
    }
    .metric-card.critical-card {
        border-top-color: var(--nt-critical);
    }
    .metric-card.high-card {
        border-top-color: var(--nt-high);
    }
    .metric-val {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 26px;
        font-weight: 600;
        color: var(--nt-text);
        margin-top: 4px;
    }
    .metric-label {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 11px;
        color: var(--nt-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 500;
    }

    /* Signature Case Stamp */
    .case-stamp {
        display: inline-block;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 700;
        font-size: 12px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 6px 14px;
        border: 2px solid currentColor;
        border-radius: 2px;
        transform: rotate(-4deg);
        position: relative;
        opacity: 0.92;
        margin-left: 12px;
        vertical-align: middle;
    }
    .case-stamp::before {
        content: "";
        position: absolute;
        inset: 2px;
        border: 1px solid currentColor;
        border-radius: 1px;
        opacity: 0.45;
    }
    .case-stamp.critical {
        color: #E8A3A3;
        border-color: var(--nt-critical);
        background: rgba(139, 46, 46, 0.15);
    }
    .case-stamp.high {
        color: #E8B896;
        border-color: var(--nt-high);
        background: rgba(184, 86, 46, 0.15);
    }

    /* Risk Badges (Outlined & Tinted Pills) */
    .badge-critical {
        background: rgba(139, 46, 46, 0.15);
        border: 1px solid var(--nt-critical);
        color: #E8A3A3;
        padding: 2px 8px;
        border-radius: 4px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-high {
        background: rgba(184, 86, 46, 0.15);
        border: 1px solid var(--nt-high);
        color: #E8B896;
        padding: 2px 8px;
        border-radius: 4px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-medium {
        background: rgba(200, 151, 59, 0.15);
        border: 1px solid var(--nt-medium);
        color: #E8CE9E;
        padding: 2px 8px;
        border-radius: 4px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-low {
        background: rgba(91, 122, 107, 0.15);
        border: 1px solid var(--nt-low);
        color: #B9CDC0;
        padding: 2px 8px;
        border-radius: 4px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }

    /* Tabs Styling */
    [data-baseweb="tab-list"] {
        border-bottom: 1px solid var(--nt-border) !important;
        gap: 20px !important;
        background: transparent !important;
    }
    [data-baseweb="tab"] {
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        color: var(--nt-text-muted) !important;
        background: transparent !important;
        border: none !important;
        padding-bottom: 12px !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        color: var(--nt-accent) !important;
        border-bottom: 2px solid var(--nt-accent) !important;
        font-weight: 600 !important;
    }

    /* Forensic Dossier Table */
    .dossier-table-wrap {
        border: 1px solid var(--nt-border);
        border-radius: var(--nt-radius);
        overflow-x: auto;
        max-height: 480px;
        background: var(--nt-surface);
        box-shadow: var(--nt-shadow);
        margin-bottom: 16px;
    }
    .dossier-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
        color: var(--nt-text);
    }
    .dossier-table th {
        background: var(--nt-surface-raised);
        position: sticky;
        top: 0;
        z-index: 1;
        padding: 10px 14px;
        text-align: left;
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--nt-text-muted);
        border-bottom: 1px solid var(--nt-border);
    }
    .dossier-table td {
        padding: 9px 14px;
        border-bottom: 1px solid var(--nt-border);
        white-space: nowrap;
    }
    .dossier-table tr:hover {
        background: var(--nt-surface-raised);
    }

    /* Monospace elements */
    .mono-cell {
        font-family: 'IBM Plex Mono', monospace !important;
    }

    /* Subtle tab transition */
    @media (prefers-reduced-motion: no-preference) {
        .tab-content {
            animation: fadeIn 0.2s ease-in-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(3px); }
            to { opacity: 1; transform: translateY(0); }
        }
    }
</style>
""")

# Register NTRO Dark Altair Theme
def ntro_theme():
    return {
        "config": {
            "background": "transparent",
            "title": {"font": "IBM Plex Sans", "fontSize": 14, "color": "#E8E6DE", "anchor": "start"},
            "axis": {
                "labelFont": "IBM Plex Mono", "labelColor": "#94A3B8", "labelFontSize": 11,
                "titleFont": "IBM Plex Sans", "titleColor": "#E8E6DE", "titleFontSize": 12,
                "gridColor": "#1F2A44", "domainColor": "#1F2A44",
            },
            "legend": {
                "labelFont": "IBM Plex Sans", "labelColor": "#E8E6DE",
                "titleFont": "IBM Plex Sans", "titleColor": "#E8E6DE"
            },
            "range": {"category": ["#5B7A6B", "#C8973B", "#B8562E", "#8B2E2E", "#3E5C76", "#7A6B8F"]},
        }
    }
alt.themes.register("ntro_dark", ntro_theme)
alt.themes.enable("ntro_dark")

# ---------------------------------------------------------------------------
# ARTIFACT LOADER
# ---------------------------------------------------------------------------
@st.cache_data
def load_all_artifacts():
    data_dir = "data"
    reports_dir = "reports"

    scored_path = os.path.join(data_dir, "scored_entities.csv")
    features_path = os.path.join(data_dir, "features.csv")
    clusters_path = os.path.join(data_dir, "clusters.json")
    explanations_path = os.path.join(data_dir, "explanations.json")
    narratives_path = os.path.join(data_dir, "cached_narratives.json")
    comparison_path = os.path.join(reports_dir, "model_comparison.csv")
    eval_metrics_path = os.path.join(reports_dir, "evaluation_metrics.csv")

    scored_df = pd.read_csv(scored_path) if os.path.exists(scored_path) else pd.DataFrame()
    features_df = pd.read_csv(features_path) if os.path.exists(features_path) else pd.DataFrame()
    
    if os.path.exists(clusters_path):
        with open(clusters_path) as f:
            clusters_json = json.load(f)
    else:
        clusters_json = {}

    if os.path.exists(explanations_path):
        with open(explanations_path) as f:
            explanations_json = json.load(f)
    else:
        explanations_json = {}

    if os.path.exists(narratives_path):
        with open(narratives_path) as f:
            narratives_json = json.load(f)
    else:
        narratives_json = {}

    comparison_df = pd.read_csv(comparison_path) if os.path.exists(comparison_path) else pd.DataFrame()
    eval_metrics_df = pd.read_csv(eval_metrics_path) if os.path.exists(eval_metrics_path) else pd.DataFrame()

    if os.path.exists("transactions.json"):
        with open("transactions.json") as f:
            transactions = json.load(f)
    else:
        transactions = []

    return {
        "scored_df": scored_df,
        "features_df": features_df,
        "clusters": clusters_json,
        "explanations": explanations_json,
        "narratives": narratives_json,
        "comparison_df": comparison_df,
        "eval_metrics_df": eval_metrics_df,
        "transactions": transactions,
    }

data_bundle = load_all_artifacts()
scored_df = data_bundle["scored_df"]
features_df = data_bundle["features_df"]
clusters_json = data_bundle["clusters"]
explanations_json = data_bundle["explanations"]
narratives_json = data_bundle["narratives"]
comparison_df = data_bundle["comparison_df"]
eval_metrics_df = data_bundle["eval_metrics_df"]
transactions = data_bundle["transactions"]

# ---------------------------------------------------------------------------
# SIDEBAR INVESTIGATION FILTERS
# ---------------------------------------------------------------------------
st.sidebar.html("<div class='sidebar-wordmark'>NTRO // FORENSIC MONITOR</div>")
st.sidebar.html("<div class='sidebar-caption'>SIH26146 • Tripartite Bitcoin AML Engine</div>")
st.sidebar.markdown("--- ")

filter_bands = st.sidebar.multiselect(
    "RISK BANDS",
    options=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
    default=["CRITICAL", "HIGH", "MEDIUM"]
)

min_score = st.sidebar.slider("MINIMUM RISK SCORE", min_value=0.0, max_value=100.0, value=35.0, step=5.0)

all_countries = sorted([c for c in scored_df["dominant_country"].unique() if c and c != "Unknown"])
selected_country = st.sidebar.selectbox("GEOGRAPHIC JURISDICTION", options=["ALL"] + all_countries, index=0)

search_query = st.sidebar.text_input("SEARCH WALLET / CLUSTER ID", "").strip()

# Apply Filters
filtered_df = scored_df.copy()
if filter_bands:
    filtered_df = filtered_df[filtered_df["risk_band"].isin(filter_bands)]
filtered_df = filtered_df[filtered_df["composite_risk_score"] >= min_score]
if selected_country != "ALL":
    filtered_df = filtered_df[filtered_df["dominant_country"] == selected_country]
if search_query:
    filtered_df = filtered_df[
        filtered_df["wallet_address"].str.contains(search_query, case=False, na=False, regex=False) |
        filtered_df["cluster_id"].str.contains(search_query, case=False, na=False, regex=False)
    ]

# ---------------------------------------------------------------------------
# MAIN DOSSIER HEADER
# ---------------------------------------------------------------------------
st.html("<div class='classification-banner'>NTRO INTERNAL — SIH26146 CASE FILE</div>")
st.html("<h1 style='margin-top:0px; margin-bottom:4px;'>Bitcoin Transaction Traffic & Laundering Detection System</h1>")
st.html("<div style='color:var(--nt-text-muted); font-size:13px; margin-bottom:16px;'>National Technical Research Organisation (NTRO) • Problem Statement SIH26146 • Air-Gapped Forensic Instrument</div>")
st.markdown("--- ")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1. Overview",
    "2. Alert Queue",
    "3. Case Detail",
    "4. Network",
    "5. Model Insights",
    "6. Evaluation"
])

# ---------------------------------------------------------------------------
# TAB 1: OVERVIEW
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Forensic Threat Landscape & Executive Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    total_wallets = len(scored_df)
    total_alerts = len(scored_df[scored_df["risk_band"].isin(["MEDIUM", "HIGH", "CRITICAL"])])
    critical_count = len(scored_df[scored_df["risk_band"] == "CRITICAL"])
    high_count = len(scored_df[scored_df["risk_band"] == "HIGH"])
    total_flagged_btc = scored_df[scored_df["risk_band"].isin(["MEDIUM", "HIGH", "CRITICAL"])]["total_received_amount"].sum()

    col1.html(f"<div class='metric-card'><div class='metric-label'>Total Entities</div><div class='metric-val'>{total_wallets:,}</div></div>")
    col2.html(f"<div class='metric-card'><div class='metric-label'>Active Alerts</div><div class='metric-val' style='color:var(--nt-medium);'>{total_alerts}</div></div>")
    col3.html(f"<div class='metric-card critical-card'><div class='metric-label'>Critical Threats</div><div class='metric-val' style='color:#E8A3A3;'>{critical_count}</div></div>")
    col4.html(f"<div class='metric-card high-card'><div class='metric-label'>High Escalations</div><div class='metric-val' style='color:#E8B896;'>{high_count}</div></div>")
    col5.html(f"<div class='metric-card'><div class='metric-label'>Flagged Volume</div><div class='metric-val'>{total_flagged_btc:,.2f} ₿</div></div>")

    st.markdown("### ")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Composite Risk Score Distribution")
        hist_chart = alt.Chart(scored_df).mark_bar(opacity=0.9, cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
            x=alt.X("composite_risk_score:Q", bin=alt.Bin(maxbins=25), title="Composite Risk Score (0-100)"),
            y=alt.Y("count():Q", title="Entity Count"),
            color=alt.Color("risk_band:N", scale=alt.Scale(
                domain=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                range=["#8B2E2E", "#B8562E", "#C8973B", "#5B7A6B"]
            ), title="Risk Band")
        ).properties(height=290)
        st.altair_chart(hist_chart, width="stretch")

    with c2:
        st.markdown("#### Triggered Laundering Reason Codes Frequency")
        all_reasons = []
        for rc in scored_df["reason_codes"].dropna():
            for code in str(rc).split(";"):
                if code:
                    all_reasons.append(code)
        rc_df = pd.Series(all_reasons).value_counts().reset_index()
        rc_df.columns = ["Reason Code", "Count"]

        bar_rc = alt.Chart(rc_df).mark_bar(color="#C8973B", cornerRadiusTopRight=2, cornerRadiusBottomRight=2).encode(
            x=alt.X("Count:Q", title="Trigger Count"),
            y=alt.Y("Reason Code:N", sort="-x", title="Typology Reason Code"),
            tooltip=["Reason Code", "Count"]
        ).properties(height=290)
        st.altair_chart(bar_rc, width="stretch")

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("#### Top Geographic Jurisdictions (GeoIP Origin)")
        active_country_df = filtered_df if not filtered_df.empty else scored_df
        country_counts = active_country_df[active_country_df["dominant_country"] != "Unknown"]["dominant_country"].value_counts().reset_index().head(8)
        country_counts.columns = ["Country", "Entities"]
        c_chart = alt.Chart(country_counts).mark_bar(color="#3E5C76", cornerRadiusTopRight=2, cornerRadiusBottomRight=2).encode(
            x=alt.X("Entities:Q", title="Entities"),
            y=alt.Y("Country:N", sort="-x", title="Jurisdiction"),
            tooltip=["Country", "Entities"]
        ).properties(height=270)
        st.altair_chart(c_chart, width="stretch")

    with c4:
        st.markdown("#### Flagged Transaction Volume Over Time")
        tx_timeline = []
        for tx in transactions:
            tx_timeline.append({
                "timestamp": tx["timestamp"],
                "amount": tx["total_input_amount"],
                "label": tx.get("_ground_truth_label", "normal")
            })
        tx_df = pd.DataFrame(tx_timeline)
        if not tx_df.empty:
            tx_df["datetime"] = pd.to_datetime(tx_df["timestamp"])
            tx_agg = tx_df.set_index("datetime").resample("1D").agg({"amount": "sum"}).reset_index()
            t_chart = alt.Chart(tx_agg).mark_line(point=True, color="#C8973B").encode(
                x=alt.X("datetime:T", axis=alt.Axis(format="%b %d", title="Date")),
                y=alt.Y("amount:Q", title="Total Transacted Volume (BTC)"),
                tooltip=[
                    alt.Tooltip("datetime:T", format="%b %d, %Y", title="Date"),
                    alt.Tooltip("amount:Q", format=".2f", title="Volume (BTC)")
                ]
            ).properties(height=270)
            st.altair_chart(t_chart, width="stretch")

# ---------------------------------------------------------------------------
# TAB 2: ALERT QUEUE
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("Alert Queue")
    st.html(f"<div style='color:var(--nt-text-muted); font-size:13px; margin-top:-8px; margin-bottom:16px;'>Showing <b>{len(filtered_df)}</b> suspicious entities matching active filters.</div>")

    if filtered_df.empty:
        st.info("ℹ️ No entities match these filters. Widen the risk band or lower the minimum score.")
    else:
        # Build Evidence-Grade Forensic HTML Table with Monospace styling
        table_rows = []
        for _, r in filtered_df.head(100).iterrows():
            band_raw = str(r.get("risk_band", "LOW")).upper()
            band = html.escape(band_raw)
            badge_class = f"badge-{html.escape(band_raw.lower())}"
            w_addr = html.escape(str(r["wallet_address"]))
            score_val = html.escape(f"{float(r['composite_risk_score']):.1f}")
            conf_val = html.escape(f"{float(r.get('confidence_score', 0)):.0%}")
            vol_val = html.escape(f"{float(r.get('total_received_amount', 0)):.4f}")
            country_val = html.escape(str(r.get("dominant_country", "Unknown")))
            asn_val = html.escape(str(r.get("dominant_asn", "Unknown")))
            reasons_val = html.escape(str(r.get("reason_codes", "None")))
            cluster_val = html.escape(str(r.get("cluster_id", "N/A")))

            table_rows.append(
                f"<tr>"
                f"<td style='color:var(--nt-accent);'>{w_addr}</td>"
                f"<td><b>{score_val}</b></td>"
                f"<td><span class='{badge_class}'>{band}</span></td>"
                f"<td>{conf_val}</td>"
                f"<td>{cluster_val}</td>"
                f"<td>{country_val}</td>"
                f"<td>{asn_val}</td>"
                f"<td>{vol_val}</td>"
                f"<td style='color:var(--nt-text-muted); font-size:11px;'>{reasons_val}</td>"
                f"</tr>"
            )

        rows_html = "".join(table_rows)
        table_html = (
            "<div class='dossier-table-wrap'>"
            "<table class='dossier-table'>"
            "<thead><tr>"
            "<th>Wallet Address</th>"
            "<th>Risk Score</th>"
            "<th>Band</th>"
            "<th>Confidence</th>"
            "<th>Cluster ID</th>"
            "<th>Jurisdiction</th>"
            "<th>ASN</th>"
            "<th>Volume (BTC)</th>"
            "<th>Triggered Reason Codes</th>"
            "</tr></thead>"
            f"<tbody>{rows_html}</tbody>"
            "</table></div>"
        )
        st.html(table_html)

        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Export Filtered Alert Queue to CSV",
            data=csv_data,
            file_name="ntro_filtered_alert_queue.csv",
            mime="text/csv",
        )

# ---------------------------------------------------------------------------
# TAB 3: CASE DETAIL
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("Case Detail")
    
    top_wallets = filtered_df["wallet_address"].tolist() if not filtered_df.empty else scored_df["wallet_address"].tolist()
    
    if not top_wallets:
        st.info("ℹ️ No entities match these filters. Widen the risk band or lower the minimum score.")
    else:
        selected_wallet = st.selectbox("Select Target Wallet to Inspect:", options=top_wallets)

        if selected_wallet:
            row = scored_df[scored_df["wallet_address"] == selected_wallet].iloc[0]
            exp = explanations_json.get("entities", {}).get(selected_wallet, {})
            narrative_obj = narratives_json.get(selected_wallet, {})
            cluster_meta = clusters_json.get(row.get("cluster_id", ""), {})

            # Signature Case Stamp (Conditionally for HIGH / CRITICAL)
            stamp_html = ""
            if row['risk_band'] == "CRITICAL":
                stamp_html = "<div class='case-stamp critical'>Flagged — Critical Risk</div>"
            elif row['risk_band'] == "HIGH":
                stamp_html = "<div class='case-stamp high'>Flagged — High Risk</div>"

            # Top KPI Metric Cards for Target Entity
            k1, k2, k3, k4 = st.columns(4)
            card1_class = "critical-card" if row['risk_band'] == "CRITICAL" else ("high-card" if row['risk_band'] == "HIGH" else "")
            
            cluster_id_esc = html.escape(str(row.get('cluster_id', 'N/A')))
            country_esc = html.escape(str(row.get('dominant_country', 'N/A')))

            k1.html(
                f"<div class='metric-card {card1_class}'>"
                f"<div class='metric-label'>Composite Risk Score</div>"
                f"<div class='metric-val'>{row['composite_risk_score']:.1f} / 100 {stamp_html}</div>"
                f"</div>"
            )

            k2.html(
                f"<div class='metric-card'>"
                f"<div class='metric-label'>Detection Confidence</div>"
                f"<div class='metric-val'>{row['confidence_score']:.0%}</div>"
                f"</div>"
            )

            k3.html(
                f"<div class='metric-card'>"
                f"<div class='metric-label'>Entity Cluster ID</div>"
                f"<div class='metric-val' style='font-size:20px;'>{cluster_id_esc}</div>"
                f"</div>"
            )

            k4.html(
                f"<div class='metric-card'>"
                f"<div class='metric-label'>Geographic Origin</div>"
                f"<div class='metric-val' style='font-size:20px;'>{country_esc}</div>"
                f"</div>"
            )

            st.markdown("--- ")

            # Plain Language Investigator Summary
            st.markdown("#### Plain-Language Investigator Summary")
            plain_text = exp.get("plain_language_explanation", "No explanation generated.")
            plain_text_esc = html.escape(plain_text)
            st.html(
                f"<div style='background:var(--nt-surface); border:1px solid var(--nt-border); border-left:3px solid var(--nt-accent); border-radius:var(--nt-radius); padding:16px 20px; color:var(--nt-text); font-size:13px; line-height:1.6;'>"
                f"{plain_text_esc}"
                f"</div>"
            )

            st.markdown("### ")

            # 2 Columns: SHAP Feature Attributions & Cluster Co-Members
            cd1, cd2 = st.columns(2)
            with cd1:
                st.markdown("#### Feature Attributions (SHAP TreeExplainer)")
                top_feats = exp.get("top_features", [])
                if top_feats:
                    shap_df = pd.DataFrame(top_feats)
                    shap_bar = alt.Chart(shap_df).mark_bar(cornerRadiusTopRight=2, cornerRadiusBottomRight=2).encode(
                        x=alt.X("shap_value:Q", title="SHAP Contribution Value (+ Anomaly / - Normal)"),
                        y=alt.Y("display_name:N", sort="-x", title="Feature Signal"),
                        color=alt.condition(
                            alt.datum.shap_value > 0,
                            alt.value("#8B2E2E"),
                            alt.value("#5B7A6B")
                        ),
                        tooltip=["display_name", "value", "shap_value"]
                    ).properties(height=270)
                    st.altair_chart(shap_bar, width="stretch")

            with cd2:
                st.markdown("#### Entity Cluster Co-Members")
                members = cluster_meta.get("member_wallets", [selected_wallet])
                st.html(f"<div style='color:var(--nt-text-muted); font-size:12px; margin-bottom:8px;'>Cluster <b>{cluster_id_esc}</b> links <b>{len(members)}</b> co-controlled wallets:</div>")
                
                member_rows = "".join([f"<tr><td class='mono-cell' style='color:var(--nt-accent);'>{html.escape(str(m))}</td></tr>" for m in members])
                member_table_html = (
                    f"<div class='dossier-table-wrap' style='max-height:220px;'>"
                    f"<table class='dossier-table'>"
                    f"<thead><tr><th>Co-Member Wallet Address</th></tr></thead>"
                    f"<tbody>{member_rows}</tbody>"
                    f"</table>"
                    f"</div>"
                )
                st.html(member_table_html)

            # Law Enforcement Case Narrative & SAR Export
            st.markdown("#### Law Enforcement Case Narrative (SAR / STR Package)")
            narrative_text = narrative_obj.get("narrative", "")
            if not narrative_text:
                import narrative
                narrative_text = narrative.generate_template_narrative(dict(row), exp)
            
            st.text_area("Forensic Case Dossier Narrative", value=narrative_text, height=180)

            # SAR JSON Export Button
            sar_doc = narrative_obj.get("sar_document", {})
            if not sar_doc:
                import narrative
                sar_doc = narrative.generate_sar_export_document(selected_wallet, dict(row), exp, narrative_text)

            st.download_button(
                label="Download Official SAR/STR Case Package (JSON)",
                data=json.dumps(sar_doc, indent=2, default=lambda o: int(o) if isinstance(o, (np.integer, int)) else (float(o) if isinstance(o, (np.floating, float)) else str(o))),
                file_name=f"SAR_CASE_{selected_wallet[:10]}.json",
                mime="application/json"
            )

# ---------------------------------------------------------------------------
# TAB 4: NETWORK GRAPH
# ---------------------------------------------------------------------------
with tab4:
    st.subheader("Network")
    st.html("<div style='color:var(--nt-text-muted); font-size:13px; margin-top:-8px; margin-bottom:16px;'>Interactive tripartite network graph (Wallets, Transactions, Broadcast/Relay IPs).</div>")

    net_filter = st.radio("Graph Scope:", ["Ego-Network of Selected Case", "Top 30 High-Risk Subgraph"], horizontal=True)
    
    net = Network(height="550px", width="100%", bgcolor="#0B1220", font_color="#E8E6DE", directed=True)
    net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=100, spring_strength=0.08)

    # Load Graph
    if os.path.exists("graph.gml"):
        G = nx.read_gml("graph.gml")
    else:
        G = nx.MultiDiGraph()

    scored_map = scored_df.set_index("wallet_address")["composite_risk_score"].to_dict()
    band_map = scored_df.set_index("wallet_address")["risk_band"].to_dict()

    if net_filter == "Ego-Network of Selected Case" and selected_wallet in G:
        sub_nodes = set([selected_wallet])
        for n1 in G.neighbors(selected_wallet):
            sub_nodes.add(n1)
            for n2 in G.neighbors(n1):
                sub_nodes.add(n2)
        sub_G = G.subgraph(sub_nodes)
    else:
        top_wallets_set = set(scored_df.head(25)["wallet_address"])
        sub_nodes = set(top_wallets_set)
        for w in top_wallets_set:
            if w in G:
                for n in list(G.neighbors(w))[:3]:
                    sub_nodes.add(n)
        sub_G = G.subgraph(sub_nodes)

    for node, data in sub_G.nodes(data=True):
        ntype = data.get("node_type", "wallet")
        if ntype == "wallet":
            score = scored_map.get(node, 0.0)
            band = band_map.get(node, "LOW")
            color = "#8B2E2E" if band == "CRITICAL" else ("#B8562E" if band == "HIGH" else ("#C8973B" if band == "MEDIUM" else "#5B7A6B"))
            net.add_node(node, label=f"{node[:6]}...", title=f"Wallet: {node} | Risk: {score:.1f} ({band})", color=color, shape="dot", size=16)
        elif ntype == "transaction":
            lbl = data.get("label", "")
            color = "#7A6B8F" if lbl != "normal" else "#2E4057"
            net.add_node(node, label=f"tx:{node[:4]}", title=f"TXID: {node} | Pattern: {lbl}", color=color, shape="square", size=10)
        elif ntype == "ip":
            net.add_node(node, label=node, title=f"IP Node: {node}", color="#3E5C76", shape="diamond", size=8)

    for u, v, data in sub_G.edges(data=True):
        etype = data.get("edge_type", "flow")
        net.add_edge(u, v, title=f"{etype}", color="rgba(232, 230, 222, 0.15)", arrows="to")

    html_path = "reports/network_view.html"
    net.save_graph(html_path)
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    components.html(html_content, height=580)
    st.caption("Legend: 🔴 Critical (#8B2E2E) / 🟠 High (#B8562E) / 🟡 Medium (#C8973B) / 🟢 Low (#5B7A6B) Wallets | 🟣 Anomaly Tx (#7A6B8F) | 🔵 Normal Tx (#2E4057) | 🔷 IP Nodes (#3E5C76)")

# ---------------------------------------------------------------------------
# TAB 5: MODEL INSIGHTS
# ---------------------------------------------------------------------------
with tab5:
    st.subheader("Model Insights")
    st.html("<div style='color:var(--nt-text-muted); font-size:13px; margin-top:-8px; margin-bottom:16px;'>Inspection of unsupervised anomaly detectors, cross-model agreement, and PyOD baseline benchmark.</div>")

    m1, m2 = st.columns(2)
    with m1:
        st.markdown("#### Individual Model Anomaly Distributions")
        model_scores_melted = scored_df.melt(
            id_vars=["wallet_address", "ground_truth_label"],
            value_vars=["score_iforest", "score_lof", "score_mahalanobis", "ensemble_anomaly_score"],
            var_name="Model",
            value_name="Normalized Score"
        )
        model_map = {
            "score_iforest": "Isolation Forest",
            "score_lof": "Local Outlier Factor",
            "score_mahalanobis": "Robust Mahalanobis",
            "ensemble_anomaly_score": "Blended Ensemble"
        }
        model_scores_melted["Model Name"] = model_scores_melted["Model"].map(model_map)

        box_plot = alt.Chart(model_scores_melted).mark_boxplot(extent="min-max").encode(
            x=alt.X("Model Name:N", title="Algorithm"),
            y=alt.Y("Normalized Score:Q", title="Normalized Anomaly Score [0, 1]"),
            color=alt.Color("Model Name:N", scale=alt.Scale(range=["#5B7A6B", "#C8973B", "#B8562E", "#3E5C76"]))
        ).properties(height=300)
        st.altair_chart(box_plot, width="stretch")

    with m2:
        st.markdown("#### Isolation Forest vs Mahalanobis Score Agreement")
        scatter = alt.Chart(scored_df).mark_circle(size=60, opacity=0.75).encode(
            x=alt.X("score_iforest:Q", title="Isolation Forest Anomaly Score"),
            y=alt.Y("score_mahalanobis:Q", title="Robust Mahalanobis Score"),
            color=alt.Color("ground_truth_label:N", scale=alt.Scale(
                domain=["normal", "peel_chain", "mixer", "rapid_cashout"],
                range=["#5B7A6B", "#C8973B", "#8B2E2E", "#B8562E"]
            ), title="Ground Truth Typology"),
            tooltip=["wallet_address", "score_iforest", "score_mahalanobis", "ground_truth_label"]
        ).properties(height=300)
        st.altair_chart(scatter, width="stretch")

    st.markdown("--- ")
    st.markdown("#### Model Comparison Benchmark vs PyOD Baselines (from `reports/model_comparison.csv`)")
    if not comparison_df.empty:
        st.dataframe(comparison_df, width="stretch")
        
        comp_bar = alt.Chart(comparison_df).mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
            x=alt.X("Algorithm:N", sort="-y", title="Algorithm"),
            y=alt.Y("ROC_AUC:Q", title="ROC-AUC Score"),
            color=alt.Color("Type:N", scale=alt.Scale(range=["#C8973B", "#5B7A6B", "#B8562E", "#3E5C76", "#7A6B8F", "#8B2E2E"]), title="Paradigm"),
            tooltip=["Algorithm", "Type", "ROC_AUC", "PR_AUC", "F1_Score", "Latency_ms"]
        ).properties(height=280)
        st.altair_chart(comp_bar, width="stretch")

# ---------------------------------------------------------------------------
# TAB 6: EVALUATION
# ---------------------------------------------------------------------------
with tab6:
    st.subheader("Evaluation")
    st.html("<div style='color:var(--nt-text-muted); font-size:13px; margin-top:-8px; margin-bottom:16px;'>Empirical scorecard against synthetic ground truth across operational triage policies.</div>")
    
    st.info("ℹ️ **Evaluation Methodology:** Benchmarked against synthetic ground truth generated with planted peel-chain, mixer, and rapid-cashout patterns. Real-world operational deployment incorporates labeled FIU law-enforcement data.")

    if not eval_metrics_df.empty:
        st.markdown("#### Performance Metrics by Operational Policy Band")
        st.dataframe(eval_metrics_df, width="stretch")

    e1, e2 = st.columns(2)
    with e1:
        st.markdown("#### Confusion Matrices across Alert Triage Levels")
        if os.path.exists("reports/confusion_matrix.png"):
            st.image("reports/confusion_matrix.png", width="stretch")

    with e2:
        st.markdown("#### ROC and Precision-Recall Curves")
        if os.path.exists("reports/roc_curve.png"):
            st.image("reports/roc_curve.png", width="stretch")

st.markdown("--- ")
st.caption("NTRO INTERNAL CASE FILE • Smart India Hackathon (SIH26146) • Offline Forensic Instrument")
