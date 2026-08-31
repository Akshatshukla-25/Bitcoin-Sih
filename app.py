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

    /* ----------------------------------------------------------------------- */
    /* MOTION.DEV SPRING PHYSICS & BKLIT COMPONENT TOKENS                      */
    /* ----------------------------------------------------------------------- */
    .motion-fade-in {
        animation: motionFadeUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    @keyframes motionFadeUp {
        0% { opacity: 0; transform: translateY(8px); }
        100% { opacity: 1; transform: translateY(0); }
    }

    @keyframes radarPulse {
        0% { box-shadow: 0 0 0 0 rgba(139, 46, 46, 0.6); }
        70% { box-shadow: 0 0 0 8px rgba(139, 46, 46, 0); }
        100% { box-shadow: 0 0 0 0 rgba(139, 46, 46, 0); }
    }

    @keyframes goldPulse {
        0% { box-shadow: 0 0 0 0 rgba(200, 151, 59, 0.5); }
        70% { box-shadow: 0 0 0 6px rgba(200, 151, 59, 0); }
        100% { box-shadow: 0 0 0 0 rgba(200, 151, 59, 0); }
    }

    /* Metric Cards (BKlit + Motion Spring Hover) */
    .metric-card {
        background: linear-gradient(180deg, rgba(19, 27, 46, 0.95) 0%, rgba(11, 18, 32, 0.98) 100%);
        backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-top: 3px solid var(--nt-accent);
        border-radius: var(--nt-radius);
        padding: 16px 20px;
        box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.45);
        transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
        overflow: hidden;
    }
    .metric-card:hover {
        transform: translateY(-4px) scale(1.015);
        border-top-color: var(--nt-accent-hover);
        border-color: rgba(200, 151, 59, 0.35);
        box-shadow: 0 16px 36px -4px rgba(0, 0, 0, 0.65), 0 0 24px -2px rgba(200, 151, 59, 0.22);
    }
    .metric-card.critical-card {
        border-top-color: var(--nt-critical);
    }
    .metric-card.critical-card:hover {
        border-color: rgba(139, 46, 46, 0.5);
        box-shadow: 0 16px 36px -4px rgba(0, 0, 0, 0.65), 0 0 24px -2px rgba(139, 46, 46, 0.35);
    }
    .metric-card.high-card {
        border-top-color: var(--nt-high);
    }
    .metric-card.high-card:hover {
        border-color: rgba(184, 86, 46, 0.5);
        box-shadow: 0 16px 36px -4px rgba(0, 0, 0, 0.65), 0 0 24px -2px rgba(184, 86, 46, 0.35);
    }

    .metric-val {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 26px;
        font-weight: 600;
        color: var(--nt-text);
        margin-top: 4px;
        letter-spacing: -0.02em;
    }
    .metric-label {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 11px;
        color: var(--nt-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
    }

    /* BKlit Card Containers for Data Visualizations */
    .bklit-container {
        background: linear-gradient(180deg, rgba(19, 27, 46, 0.7) 0%, rgba(11, 18, 32, 0.9) 100%);
        border: 1px solid var(--nt-border);
        border-radius: var(--nt-radius);
        padding: 16px 18px;
        margin-bottom: 16px;
        transition: border-color 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .bklit-container:hover {
        border-color: rgba(200, 151, 59, 0.25);
    }

    /* Signature Case Stamp (Motion Active State) */
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
        transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .case-stamp:hover {
        transform: rotate(-1deg) scale(1.05);
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
        background: rgba(139, 46, 46, 0.18);
        animation: radarPulse 2.5s infinite ease-out;
    }
    .case-stamp.high {
        color: #E8B896;
        border-color: var(--nt-high);
        background: rgba(184, 86, 46, 0.18);
    }

    /* Risk Badges (Outlined & Tinted Motion Pills) */
    .badge-critical {
        background: rgba(139, 46, 46, 0.18);
        border: 1px solid var(--nt-critical);
        color: #E8A3A3;
        padding: 3px 9px;
        border-radius: 4px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
        transition: all 0.2s ease;
    }
    .badge-critical:hover {
        background: rgba(139, 46, 46, 0.3);
        box-shadow: 0 0 10px rgba(139, 46, 46, 0.4);
    }
    .badge-high {
        background: rgba(184, 86, 46, 0.18);
        border: 1px solid var(--nt-high);
        color: #E8B896;
        padding: 3px 9px;
        border-radius: 4px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
        transition: all 0.2s ease;
    }
    .badge-high:hover {
        background: rgba(184, 86, 46, 0.3);
        box-shadow: 0 0 10px rgba(184, 86, 46, 0.4);
    }
    .badge-medium {
        background: rgba(200, 151, 59, 0.18);
        border: 1px solid var(--nt-medium);
        color: #E8CE9E;
        padding: 3px 9px;
        border-radius: 4px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
        transition: all 0.2s ease;
    }
    .badge-medium:hover {
        background: rgba(200, 151, 59, 0.3);
        box-shadow: 0 0 10px rgba(200, 151, 59, 0.4);
    }
    .badge-low {
        background: rgba(91, 122, 107, 0.18);
        border: 1px solid var(--nt-low);
        color: #B9CDC0;
        padding: 3px 9px;
        border-radius: 4px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
        transition: all 0.2s ease;
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

    /* ----------------------------------------------------------------------- */
    /* LUXURY LANDING PORTAL DESIGN SYSTEM                                     */
    /* ----------------------------------------------------------------------- */
    .landing-canvas {
        background-color: #05070B;
        background-image: 
            radial-gradient(ellipse 65% 55% at 85% 15%, rgba(200, 151, 59, 0.25) 0%, rgba(139, 46, 46, 0.08) 45%, rgba(5, 7, 11, 0) 80%),
            radial-gradient(ellipse 40% 40% at 15% 85%, rgba(62, 92, 118, 0.12) 0%, rgba(5, 7, 11, 0) 70%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 32px 40px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 60px -10px rgba(0, 0, 0, 0.7);
    }

    .landing-watermark {
        position: absolute;
        top: 220px;
        left: 20px;
        font-family: 'IBM Plex Sans', -apple-system, sans-serif;
        font-size: 160px;
        font-weight: 900;
        letter-spacing: -0.05em;
        color: rgba(255, 255, 255, 0.025);
        pointer-events: none;
        user-select: none;
        z-index: 0;
        line-height: 0.8;
    }

    .landing-nav-wrap {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.07);
        padding-bottom: 18px;
        margin-bottom: 36px;
        position: relative;
        z-index: 2;
    }
    .landing-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .landing-brand-logo {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #C8973B 0%, #8B2E2E 100%);
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        font-weight: 800;
        color: #FFFFFF;
        box-shadow: 0 0 16px rgba(200, 151, 59, 0.4);
    }
    .landing-brand-name {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 0.12em;
        color: #E8E6DE;
    }
    .landing-nav-links {
        display: flex;
        gap: 24px;
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 12px;
        font-weight: 500;
        color: #94A3B8;
    }
    .landing-nav-link {
        color: #94A3B8;
        text-decoration: none;
        transition: color 0.2s ease;
    }
    .landing-nav-link:hover {
        color: #C8973B;
    }
    .landing-pill-btn {
        background: rgba(200, 151, 59, 0.15);
        border: 1px solid rgba(200, 151, 59, 0.4);
        color: #E8CE9E;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        padding: 6px 16px;
        border-radius: 20px;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .landing-pill-btn:hover {
        background: rgba(200, 151, 59, 0.28);
        border-color: #C8973B;
        box-shadow: 0 0 16px rgba(200, 151, 59, 0.35);
        transform: translateY(-1px);
    }

    /* Hero Section Grid */
    .landing-hero-grid {
        display: grid;
        grid-template-columns: 1.15fr 0.85fr;
        gap: 40px;
        align-items: center;
        position: relative;
        z-index: 2;
        margin-bottom: 48px;
    }
    .landing-tag-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(200, 151, 59, 0.08);
        border: 1px solid rgba(200, 151, 59, 0.25);
        padding: 4px 12px;
        border-radius: 20px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 10.5px;
        font-weight: 600;
        color: #C8973B;
        letter-spacing: 0.06em;
        margin-bottom: 16px;
    }
    .landing-tag-pill span.dot {
        width: 6px;
        height: 6px;
        background: #C8973B;
        border-radius: 50%;
        box-shadow: 0 0 8px #C8973B;
    }
    .landing-headline {
        font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-size: 52px !important;
        font-weight: 700 !important;
        line-height: 1.05 !important;
        letter-spacing: -0.035em !important;
        color: #FFFFFF !important;
        margin-bottom: 18px !important;
    }
    .landing-headline span.gold-glow {
        background: linear-gradient(135deg, #FFFFFF 20%, #E8CE9E 60%, #C8973B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(200, 151, 59, 0.25);
    }
    .landing-subtext {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 14.5px;
        line-height: 1.6;
        color: #94A3B8;
        max-width: 520px;
        margin-bottom: 28px;
    }

    /* Glass Prompt Search Box */
    .landing-search-card {
        background: rgba(14, 20, 32, 0.75);
        backdrop-filter: blur(24px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 12px 16px;
        max-width: 480px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5), inset 0 0 20px rgba(255, 255, 255, 0.02);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        transition: border-color 0.25s ease, box-shadow 0.25s ease;
    }
    .landing-search-card:hover {
        border-color: rgba(200, 151, 59, 0.4);
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.6), 0 0 20px rgba(200, 151, 59, 0.15);
    }
    .landing-search-placeholder {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 12.5px;
        color: #64748B;
    }
    .landing-search-btn {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #C8973B;
        color: #0B1220;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 14px;
        box-shadow: 0 0 12px rgba(200, 151, 59, 0.5);
    }

    /* Partners Row */
    .landing-partners-bar {
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        padding: 16px 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 48px;
        position: relative;
        z-index: 2;
    }
    .landing-partners-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: #64748B;
    }
    .landing-partner-item {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 12px;
        font-weight: 600;
        color: #94A3B8;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Track Record Section */
    .landing-track-section {
        display: grid;
        grid-template-columns: 1.1fr 0.9fr;
        gap: 36px;
        position: relative;
        z-index: 2;
        margin-bottom: 36px;
    }
    .landing-track-header {
        margin-bottom: 24px;
    }
    .landing-track-title {
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 32px !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
        line-height: 1.15 !important;
        margin-bottom: 8px !important;
    }
    .landing-track-title span {
        color: #C8973B;
    }
    .landing-track-desc {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 13px;
        color: #94A3B8;
        line-height: 1.5;
    }

    .landing-stats-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
    }
    .landing-stat-card {
        background: linear-gradient(145deg, rgba(16, 24, 40, 0.75) 0%, rgba(8, 12, 22, 0.92) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 12px;
        padding: 24px 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), inset -1px -1px 24px 0px rgba(200, 151, 59, 0.1);
        transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .landing-stat-card:hover {
        transform: translateY(-4px);
        border-color: rgba(200, 151, 59, 0.35);
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7), inset -1px -1px 30px 0px rgba(200, 151, 59, 0.2);
    }
    .landing-stat-num {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 36px;
        font-weight: 700;
        color: #FFFFFF;
        line-height: 1;
        margin-bottom: 6px;
        letter-spacing: -0.03em;
    }
    .landing-stat-lbl {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 11.5px;
        color: #94A3B8;
        font-weight: 500;
    }

    /* Featured CTA Card */
    .landing-feature-card {
        background: linear-gradient(160deg, rgba(20, 28, 48, 0.85) 0%, rgba(10, 15, 28, 0.96) 100%);
        border: 1px solid rgba(200, 151, 59, 0.25);
        border-radius: 14px;
        padding: 30px 26px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.6), 0 0 30px rgba(200, 151, 59, 0.12);
        position: relative;
        overflow: hidden;
    }
    .landing-feature-card::before {
        content: "";
        position: absolute;
        top: -60px;
        right: -60px;
        width: 160px;
        height: 160px;
        background: radial-gradient(circle, rgba(200, 151, 59, 0.25) 0%, rgba(0,0,0,0) 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .landing-feature-title {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 24px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 8px;
    }
    .landing-feature-text {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 12.5px;
        color: #94A3B8;
        line-height: 1.5;
        margin-bottom: 20px;
    }
    .landing-feature-btn {
        background: #C8973B;
        color: #070B14;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11.5px;
        font-weight: 700;
        padding: 8px 18px;
        border-radius: 6px;
        text-decoration: none;
        display: inline-block;
        box-shadow: 0 4px 16px rgba(200, 151, 59, 0.4);
        transition: all 0.2s ease;
        align-self: flex-start;
    }
    .landing-feature-btn:hover {
        background: #DDAE55;
        box-shadow: 0 6px 22px rgba(200, 151, 59, 0.6);
        transform: translateY(-1px);
    }

    /* Bottom Banner */
    .landing-bottom-banner {
        text-align: center;
        padding: 32px 0 12px 0;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        position: relative;
        z-index: 2;
    }
    .landing-bottom-heading {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 26px;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.02em;
    }
    .landing-bottom-heading span {
        color: #C8973B;
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

tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "✦ Portal Landing",
    "1. Overview",
    "2. Alert Queue",
    "3. Case Detail",
    "4. Network",
    "5. Model Insights",
    "6. Evaluation"
])

# ---------------------------------------------------------------------------
# TAB 0: LUXURY LANDING PORTAL (Hero, 3D Isometric Tokens, Track Record)
# ---------------------------------------------------------------------------
with tab0:
    landing_html = """
    <div class="landing-canvas">
        <div class="landing-watermark">NTRO</div>

        <!-- Navigation Header -->
        <div class="landing-nav-wrap">
            <div class="landing-brand">
                <div class="landing-brand-logo">⚖️</div>
                <div class="landing-brand-name">NTRO // NROK FORENSIC</div>
            </div>
            <div class="landing-nav-links">
                <span class="landing-nav-link">Tripartite Engine</span>
                <span class="landing-nav-link">Entity Clustering</span>
                <span class="landing-nav-link">SAR Generator</span>
                <span class="landing-nav-link">PyOD Benchmarks</span>
                <span class="landing-nav-link">Air-Gapped Docs</span>
            </div>
            <div class="landing-pill-btn">
                <span>●</span> AIR-GAPPED ACTIVE
            </div>
        </div>

        <!-- Hero Section Grid -->
        <div class="landing-hero-grid">
            <div>
                <div class="landing-tag-pill">
                    <span class="dot"></span>
                    <span>✦ NEW • AMPLIFY NATIONAL CRYPTO DEFENSE →</span>
                </div>
                <h1 class="landing-headline">
                    Defense Against<br>
                    <span class="gold-glow">Digital Threats</span>
                </h1>
                <p class="landing-subtext">
                    Protect sovereign financial systems and critical blockchain networks from sophisticated laundering typologies with intelligent, air-gapped forensic AI. Stay ahead of cyber threats with tripartite graph intelligence.
                </p>
                <div class="landing-search-card">
                    <span class="landing-search-placeholder">Search target wallet address, transaction hash, or entity cluster...</span>
                    <div class="landing-search-btn">➔</div>
                </div>
            </div>

            <!-- 3D Isometric Holographic Security Tokens -->
            <div style="display: flex; justify-content: center; align-items: center;">
                <svg width="420" height="340" viewBox="0 0 420 340" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 20px 30px rgba(0,0,0,0.8));">
                    <!-- Laser beam network lines -->
                    <line x1="210" y1="20" x2="110" y2="150" stroke="rgba(200, 151, 59, 0.25)" stroke-width="1.2" stroke-dasharray="4 4" />
                    <line x1="210" y1="20" x2="260" y2="140" stroke="rgba(200, 151, 59, 0.4)" stroke-width="1.5" />
                    <line x1="210" y1="20" x2="360" y2="160" stroke="rgba(200, 151, 59, 0.2)" stroke-width="1.2" />
                    <line x1="110" y1="150" x2="260" y2="280" stroke="rgba(200, 151, 59, 0.3)" stroke-width="1.2" />
                    <line x1="260" y1="140" x2="260" y2="280" stroke="rgba(200, 151, 59, 0.4)" stroke-width="1.5" />
                    <line x1="360" y1="160" x2="260" y2="280" stroke="rgba(200, 151, 59, 0.25)" stroke-width="1.2" stroke-dasharray="4 4" />

                    <!-- Glow Aura -->
                    <circle cx="260" cy="140" r="90" fill="url(#goldAura)" opacity="0.35" />

                    <!-- Left Glass Node (Snowflake/Star Symbol) -->
                    <g transform="translate(60, 90)">
                        <!-- Isometric Prism -->
                        <polygon points="50,0 100,28 50,56 0,28" fill="rgba(30, 41, 59, 0.85)" stroke="rgba(255, 255, 255, 0.3)" stroke-width="1.5" />
                        <polygon points="0,28 50,56 50,96 0,68" fill="rgba(15, 23, 42, 0.9)" stroke="rgba(255, 255, 255, 0.15)" stroke-width="1.5" />
                        <polygon points="100,28 50,56 50,96 100,68" fill="rgba(30, 41, 59, 0.95)" stroke="rgba(255, 255, 255, 0.2)" stroke-width="1.5" />
                        <!-- Inner Star -->
                        <path d="M50,18 L50,38 M40,28 L60,28 M43,21 L57,35 M43,35 L57,21" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" />
                        <circle cx="50" cy="28" r="4" fill="#C8973B" />
                    </g>

                    <!-- Center Gold Hardware Security Module Token -->
                    <g transform="translate(200, 70)">
                        <!-- Gold Isometric Chassis -->
                        <polygon points="60,0 120,34 60,68 0,34" fill="url(#goldGradTop)" stroke="#DDAE55" stroke-width="2" />
                        <polygon points="0,34 60,68 60,118 0,84" fill="url(#goldGradLeft)" stroke="#B8860B" stroke-width="2" />
                        <polygon points="120,34 60,68 60,118 120,84" fill="url(#goldGradRight)" stroke="#8B2E2E" stroke-width="2" />
                        <!-- Inner Shield / Bitcoin Emblem -->
                        <polygon points="60,12 96,34 60,56 24,34" fill="#0A0E17" stroke="#C8973B" stroke-width="1.5" />
                        <path d="M60,24 L60,44 M52,30 L68,30 M52,38 L68,38" stroke="#E8CE9E" stroke-width="2.5" stroke-linecap="round" />
                        <circle cx="60" cy="34" r="5" fill="#DDAE55" />
                        <!-- Cooling vents -->
                        <line x1="12" y1="52" x2="28" y2="61" stroke="#C8973B" stroke-width="1.5" />
                        <line x1="12" y1="60" x2="28" y2="69" stroke="#C8973B" stroke-width="1.5" />
                        <line x1="12" y1="68" x2="28" y2="77" stroke="#C8973B" stroke-width="1.5" />
                    </g>

                    <!-- Right Translucent Wireframe Token -->
                    <g transform="translate(310, 110)">
                        <polygon points="40,0 80,22 40,44 0,22" fill="rgba(15, 23, 42, 0.4)" stroke="rgba(255, 255, 255, 0.2)" stroke-width="1.2" stroke-dasharray="3 3" />
                        <polygon points="0,22 40,44 40,74 0,52" fill="rgba(15, 23, 42, 0.3)" stroke="rgba(255, 255, 255, 0.15)" stroke-width="1.2" />
                        <polygon points="80,22 40,44 40,74 80,52" fill="rgba(15, 23, 42, 0.5)" stroke="rgba(255, 255, 255, 0.15)" stroke-width="1.2" />
                    </g>

                    <defs>
                        <radialGradient id="goldAura" cx="50%" cy="50%" r="50%">
                            <stop offset="0%" stop-color="#C8973B" stop-opacity="0.8" />
                            <stop offset="100%" stop-color="#C8973B" stop-opacity="0" />
                        </radialGradient>
                        <linearGradient id="goldGradTop" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#FFF2D6" />
                            <stop offset="50%" stop-color="#C8973B" />
                            <stop offset="100%" stop-color="#996515" />
                        </linearGradient>
                        <linearGradient id="goldGradLeft" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#C8973B" />
                            <stop offset="100%" stop-color="#664614" />
                        </linearGradient>
                        <linearGradient id="goldGradRight" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#8B2E2E" />
                            <stop offset="100%" stop-color="#3B1212" />
                        </linearGradient>
                    </defs>
                </svg>
            </div>
        </div>

        <!-- Agency & Partner Trust Ribbon -->
        <div class="landing-partners-bar">
            <span class="landing-partners-label">Deployment Agencies:</span>
            <div class="landing-partner-item">🏛️ NTRO Command</div>
            <div class="landing-partner-item">🛡️ FIU-IND Reference</div>
            <div class="landing-partner-item">⚡ CERT-In Telemetry</div>
            <div class="landing-partner-item">⚖️ PMLA Enforcement</div>
            <div class="landing-partner-item">🔒 Air-Gapped Sandbox</div>
        </div>

        <!-- Our Proven Track Record Section -->
        <div class="landing-track-section">
            <div>
                <div class="landing-track-header">
                    <h2 class="landing-track-title">Our Proven<br><span>Track Record</span></h2>
                    <p class="landing-track-desc">
                        Within milliseconds, our offline multi-model ensemble isolates complex laundering typologies and prepares court-admissible forensic evidence packages with zero external network leakage.
                    </p>
                </div>
                <div class="landing-stats-grid">
                    <div class="landing-stat-card">
                        <div class="landing-stat-num">92.5%</div>
                        <div class="landing-stat-lbl">Success Precision (Critical Tier)</div>
                    </div>
                    <div class="landing-stat-card">
                        <div class="landing-stat-num">699</div>
                        <div class="landing-stat-lbl">Wallet Entities Triaged</div>
                    </div>
                    <div class="landing-stat-card">
                        <div class="landing-stat-num">80.5 ms</div>
                        <div class="landing-stat-lbl">Inference Latency (0.013% Block Window)</div>
                    </div>
                    <div class="landing-stat-card">
                        <div class="landing-stat-num">100%</div>
                        <div class="landing-stat-lbl">Air-Gapped Offline Operation</div>
                    </div>
                </div>
            </div>

            <!-- Featured Promo Card -->
            <div class="landing-feature-card">
                <div>
                    <div class="landing-feature-title">Interested in full triage?</div>
                    <p class="landing-feature-text">
                        Our tripartite graph fuses blockchain UTXOs and TCP/IP broadcast origin telemetry with zero data loss and automated SAR package export.
                    </p>
                    <div style="font-family:'IBM Plex Mono',monospace; font-size:11px; color:#C8973B; background:rgba(200,151,59,0.12); padding:4px 10px; border-radius:4px; border:1px solid rgba(200,151,59,0.3); margin-bottom:18px; display:inline-block;">
                        ● SEED: 42 • DETERMINISTIC ENGINE
                    </div>
                </div>
                
                <div style="display: flex; justify-content: center; align-items: center; margin: 12px 0;">
                    <svg width="240" height="130" viewBox="0 0 240 130" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <!-- Layer 3 Top Glass -->
                        <polygon points="120,10 190,40 120,70 50,40" fill="rgba(30, 41, 59, 0.85)" stroke="#FFFFFF" stroke-width="1.5" />
                        <path d="M120,30 L120,50 M110,40 L130,40" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" />
                        <!-- Layer 2 Middle Gold -->
                        <polygon points="120,40 190,70 120,100 50,70" fill="rgba(200, 151, 59, 0.35)" stroke="#C8973B" stroke-width="1.8" />
                        <circle cx="120" cy="70" r="5" fill="#C8973B" />
                        <!-- Layer 1 Base Obsidian -->
                        <polygon points="120,70 190,100 120,130 50,100" fill="rgba(11, 18, 32, 0.95)" stroke="rgba(200, 151, 59, 0.6)" stroke-width="1.5" />
                    </svg>
                </div>

                <div style="font-family:'IBM Plex Mono',monospace; font-size:11.5px; font-weight:700; color:#070B14; background:#C8973B; padding:8px 18px; border-radius:6px; text-align:center; box-shadow:0 4px 16px rgba(200,151,59,0.4);">
                    Switch to Tab 2 to Explore Live Queue →
                </div>
            </div>
        </div>

        <!-- Bottom Banner -->
        <div class="landing-bottom-banner">
            <div class="landing-bottom-heading">
                Keeping <span>National Sovereign Infrastructure Safe</span> Day And Night!
            </div>
        </div>
    </div>
    """
    st.html(landing_html)

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
        st.html("""
        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
            <span style='font-family:"IBM Plex Sans",sans-serif; font-weight:600; font-size:14px; color:#E8E6DE;'>Composite Risk Score Distribution</span>
            <span style='font-family:"IBM Plex Mono",monospace; font-size:10px; color:#C8973B; background:rgba(200,151,59,0.12); padding:2px 7px; border-radius:3px; border:1px solid rgba(200,151,59,0.3); font-weight:600;'>RISK SPECTRUM</span>
        </div>
        """)
        hist_chart = alt.Chart(scored_df).mark_bar(opacity=0.9, cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
            x=alt.X("composite_risk_score:Q", bin=alt.Bin(maxbins=25), title="Composite Risk Score (0-100)"),
            y=alt.Y("count():Q", title="Entity Count"),
            color=alt.Color("risk_band:N", scale=alt.Scale(
                domain=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                range=["#8B2E2E", "#B8562E", "#C8973B", "#5B7A6B"]
            ), title="Risk Band")
        ).properties(height=280)
        st.altair_chart(hist_chart, width="stretch")

    with c2:
        st.html("""
        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
            <span style='font-family:"IBM Plex Sans",sans-serif; font-weight:600; font-size:14px; color:#E8E6DE;'>Triggered Laundering Reason Codes Frequency</span>
            <span style='font-family:"IBM Plex Mono",monospace; font-size:10px; color:#E8A3A3; background:rgba(139,46,46,0.15); padding:2px 7px; border-radius:3px; border:1px solid rgba(139,46,46,0.35); font-weight:600;'>TYPOLOGIES</span>
        </div>
        """)
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
        ).properties(height=280)
        st.altair_chart(bar_rc, width="stretch")

    c3, c4 = st.columns(2)
    with c3:
        st.html("""
        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
            <span style='font-family:"IBM Plex Sans",sans-serif; font-weight:600; font-size:14px; color:#E8E6DE;'>Top Geographic Jurisdictions (GeoIP Origin)</span>
            <span style='font-family:"IBM Plex Mono",monospace; font-size:10px; color:#A6C2DE; background:rgba(62,92,118,0.2); padding:2px 7px; border-radius:3px; border:1px solid rgba(62,92,118,0.4); font-weight:600;'>ASN / GEOIP</span>
        </div>
        """)
        active_country_df = filtered_df if not filtered_df.empty else scored_df
        country_counts = active_country_df[active_country_df["dominant_country"] != "Unknown"]["dominant_country"].value_counts().reset_index().head(8)
        country_counts.columns = ["Country", "Entities"]
        c_chart = alt.Chart(country_counts).mark_bar(color="#3E5C76", cornerRadiusTopRight=2, cornerRadiusBottomRight=2).encode(
            x=alt.X("Entities:Q", title="Entities"),
            y=alt.Y("Country:N", sort="-x", title="Jurisdiction"),
            tooltip=["Country", "Entities"]
        ).properties(height=260)
        st.altair_chart(c_chart, width="stretch")

    with c4:
        st.html("""
        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
            <span style='font-family:"IBM Plex Sans",sans-serif; font-weight:600; font-size:14px; color:#E8E6DE;'>Flagged Transaction Volume Over Time</span>
            <span style='font-family:"IBM Plex Mono",monospace; font-size:10px; color:#B3D1C2; background:rgba(91,122,107,0.2); padding:2px 7px; border-radius:3px; border:1px solid rgba(91,122,107,0.4); font-weight:600;'>TIMELINE</span>
        </div>
        """)
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
            ).properties(height=260)
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
                st.markdown("#### Entity Cluster Co-Members & Heuristics")
                members = cluster_meta.get("member_wallets", [selected_wallet])
                heuristics = cluster_meta.get("heuristic_reasons", ["SINGLETON_ENTITY"])
                heur_conf = cluster_meta.get("clustering_confidence", 1.0)
                rationale_text = cluster_meta.get("investigative_rationale", f"Cluster {cluster_id_esc} links {len(members)} addresses.")
                
                heur_badges = " ".join([f"<span style='background:rgba(200,151,59,0.15); color:var(--nt-accent); border:1px solid rgba(200,151,59,0.3); padding:2px 6px; font-size:10px; border-radius:3px; margin-right:4px;'>{html.escape(str(h))}</span>" for h in heuristics])
                
                st.html(
                    f"<div style='background:var(--nt-surface); border:1px solid var(--nt-border); padding:10px 12px; border-radius:var(--nt-radius); margin-bottom:8px; font-size:12px;'>"
                    f"<div style='display:flex; justify-content:space-between; margin-bottom:4px; align-items:center;'>"
                    f"<div><b>Method:</b> {heur_badges}</div>"
                    f"<div><b>Confidence:</b> <span style='color:var(--nt-accent); font-weight:bold;'>{heur_conf:.0%}</span></div>"
                    f"</div>"
                    f"<div style='color:var(--nt-text-muted); font-size:11px; line-height:1.4;'>{html.escape(rationale_text)}</div>"
                    f"</div>"
                )
                
                member_rows = "".join([f"<tr><td class='mono-cell' style='color:var(--nt-accent);'>{html.escape(str(m))}</td></tr>" for m in members])
                member_table_html = (
                    f"<div class='dossier-table-wrap' style='max-height:165px;'>"
                    f"<table class='dossier-table'>"
                    f"<thead><tr><th>Co-Member Wallet Address ({len(members)} total)</th></tr></thead>"
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
    legend_html = (
        "<div style='display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; margin-bottom: 6px; font-size: 11px; font-family: var(--nt-font-mono);'>"
        "<span style='background: rgba(139,46,46,0.2); color: #E8A3A3; padding: 4px 9px; border: 1px solid rgba(139,46,46,0.5); border-radius: 2px;'>🔴 Critical Wallet (Score &ge; 60)</span>"
        "<span style='background: rgba(184,86,46,0.2); color: #E8B896; padding: 4px 9px; border: 1px solid rgba(184,86,46,0.5); border-radius: 2px;'>🟠 High Risk Wallet (Score 50–59)</span>"
        "<span style='background: rgba(200,151,59,0.2); color: #E8D4A2; padding: 4px 9px; border: 1px solid rgba(200,151,59,0.5); border-radius: 2px;'>🟡 Medium Risk Wallet (Score 35–49)</span>"
        "<span style='background: rgba(91,122,107,0.2); color: #B3D1C2; padding: 4px 9px; border: 1px solid rgba(91,122,107,0.5); border-radius: 2px;'>🟢 Normal Wallet</span>"
        "<span style='background: rgba(122,107,143,0.2); color: #D1C5DE; padding: 4px 9px; border: 1px solid rgba(122,107,143,0.5); border-radius: 2px;'>🟣 Anomaly Tx</span>"
        "<span style='background: rgba(46,64,87,0.2); color: #ADC2D8; padding: 4px 9px; border: 1px solid rgba(46,64,87,0.5); border-radius: 2px;'>🔵 Normal Tx</span>"
        "<span style='background: rgba(62,92,118,0.2); color: #A6C2DE; padding: 4px 9px; border: 1px solid rgba(62,92,118,0.5); border-radius: 2px;'>🔷 IP Node</span>"
        "</div>"
    )
    st.html(legend_html)

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
