"""
network_graph.py — SIH26146
Generates a self-contained vis.js Network HTML for the Streamlit dashboard.
Replaces PyVis with direct vis.js for full control over physics, styling,
interactivity (search, path-highlight, click-to-inspect, node filter, legend toggle).
"""
import json
import networkx as nx
import pandas as pd
from typing import Optional

BAND_COLOR = {
    "CRITICAL": "#8B2E2E",
    "HIGH":     "#B8562E",
    "MEDIUM":   "#C8973B",
    "LOW":      "#5B7A6B",
}

def _band_size(band: str) -> int:
    return {"CRITICAL": 24, "HIGH": 20, "MEDIUM": 15, "LOW": 11}.get(band, 11)

def _build_graph_data(
    G: nx.MultiDiGraph,
    scored_map: dict, band_map: dict, label_map: dict,
    reason_map: dict, cluster_map: dict,
    scope: str, selected_wallet: Optional[str] = None, df: Optional[pd.DataFrame] = None
):
    if scope == "ego" and selected_wallet and selected_wallet in G:
        sub_nodes = {selected_wallet}
        for n1 in G.neighbors(selected_wallet):
            sub_nodes.add(n1)
            for n2 in G.neighbors(n1):
                sub_nodes.add(n2)
        sub_G = G.subgraph(sub_nodes)
    else:
        top_wallets = set(df.sort_values("composite_risk_score", ascending=False).head(30)["wallet_address"]) if df is not None else set()
        sub_nodes = set(top_wallets)
        for w in top_wallets:
            if w in G:
                for n1 in list(G.neighbors(w))[:5]:
                    sub_nodes.add(n1)
                    for n2 in list(G.neighbors(n1))[:2]:
                        sub_nodes.add(n2)
        sub_G = G.subgraph(sub_nodes)

    edge_colors = {
        "pays":       "rgba(200,151,59,0.55)",
        "funds":      "rgba(91,122,107,0.6)",
        "relays_to":  "rgba(56,189,248,0.35)",
        "broadcasts": "rgba(56,189,248,0.35)",
    }

    vis_nodes = []
    vis_edges = []

    for node, data in sub_G.nodes(data=True):
        ntype = data.get("node_type", "wallet")
        if ntype == "wallet":
            score   = float(scored_map.get(node, 0.0))
            band    = band_map.get(node, "LOW")
            label   = label_map.get(node, "normal")
            reasons = str(reason_map.get(node, "—"))
            cluster = str(cluster_map.get(node, "—"))
            color   = BAND_COLOR.get(band, "#5B7A6B")
            vis_nodes.append({
                "id": node, "label": node[:8] + "…",
                "title": f"<b style='color:#E8E6DE'>Wallet</b><br><span style='color:#94A3B8;font-family:monospace;font-size:10px'>{node}</span><br><b>Risk:</b> {score:.1f} ({band})<br><b>Pattern:</b> {label}<br><b>Reasons:</b> {reasons}<br><b>Cluster:</b> {cluster}",
                "color": {"background": color, "border": "#1F2A44", "highlight": {"background": "#DDAE55", "border": "#fff"}, "hover": {"background": "#DDAE55", "border": "#fff"}},
                "shape": "dot", "size": _band_size(band),
                "font": {"color": "#E8E6DE", "size": 10, "face": "IBM Plex Mono,monospace"},
                "group": "wallet", "band": band, "score": score, "pattern": label,
                "shadow": {"enabled": band in ("CRITICAL", "HIGH"), "color": color, "size": 12, "x": 0, "y": 0},
            })
        elif ntype == "transaction":
            ts     = str(data.get("timestamp", ""))[:16]
            fee    = data.get("fee", 0)
            script = data.get("script_type", "")
            lbl    = data.get("label", "normal")
            color  = "#7A6B8F" if lbl != "normal" else "#2E4057"
            vis_nodes.append({
                "id": node, "label": "tx:" + node[:6] + "…",
                "title": f"<b style='color:#E8E6DE'>Transaction</b><br><span style='color:#94A3B8;font-family:monospace;font-size:10px'>{node}</span><br><b>Time:</b> {ts}<br><b>Fee:</b> {fee:.6f} BTC<br><b>Script:</b> {script}<br><b>Pattern:</b> {lbl}",
                "color": {"background": color, "border": "#64748B", "highlight": {"background": "#A89EC0", "border": "#fff"}, "hover": {"background": "#A89EC0", "border": "#fff"}},
                "shape": "square", "size": 9,
                "font": {"color": "#94A3B8", "size": 8, "face": "IBM Plex Mono,monospace"},
                "group": "transaction", "pattern": lbl,
            })
        elif ntype == "ip":
            vis_nodes.append({
                "id": node, "label": node,
                "title": f"<b style='color:#38BDF8'>IP Node</b><br><span style='color:#94A3B8;font-family:monospace'>{node}</span><br>Broadcast / relay endpoint",
                "color": {"background": "#0D2233", "border": "#38BDF8", "highlight": {"background": "#38BDF8", "border": "#fff"}, "hover": {"background": "#38BDF8", "border": "#fff"}},
                "shape": "diamond", "size": 8,
                "font": {"color": "#38BDF8", "size": 8, "face": "IBM Plex Mono,monospace"},
                "group": "ip",
            })

    for i, (u, v, data) in enumerate(sub_G.edges(data=True)):
        etype  = data.get("edge_type", "flow")
        amount = data.get("amount", None)
        tip    = f"<b>{etype}</b>"
        if amount:
            tip += f"<br>{amount:.4f} BTC"
        vis_edges.append({
            "id": i, "from": u, "to": v,
            "title": tip,
            "color": {"color": edge_colors.get(etype, "rgba(232,230,222,0.15)"), "highlight": "#DDAE55", "hover": "#C8973B"},
            "arrows": {"to": {"enabled": True, "scaleFactor": 0.45}},
            "width": 1.8 if etype == "pays" else 1.0,
            "dashes": etype in ("relays_to", "broadcasts"),
            "smooth": {"type": "dynamic"},
            "selectionWidth": 3,
        })

    return vis_nodes, vis_edges


def build_network_html(
    G: nx.MultiDiGraph,
    df: pd.DataFrame,
    scope: str = "top30",
    selected_wallet: Optional[str] = None,
    height: int = 620,
) -> str:
    scored_map  = df.set_index("wallet_address")["composite_risk_score"].to_dict()
    band_map    = df.set_index("wallet_address")["risk_band"].to_dict()
    label_map   = df.set_index("wallet_address")["ground_truth_label"].to_dict()
    reason_map  = df.set_index("wallet_address")["reason_codes"].to_dict()
    cluster_map = df.set_index("wallet_address")["cluster_id"].to_dict()

    nodes, edges = _build_graph_data(
        G, scored_map, band_map, label_map, reason_map, cluster_map,
        scope, selected_wallet, df
    )

    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #05070B; font-family: 'IBM Plex Sans', 'Inter', sans-serif; color: #E8E6DE; overflow: hidden; }}

  #graph-root {{
    position: relative;
    width: 100%;
    height: {height}px;
    background: #05070B;
  }}

  /* ── Controls bar ── */
  #controls {{
    position: absolute;
    top: 12px; left: 12px;
    z-index: 100;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    align-items: center;
  }}
  .ctrl-input {{
    background: rgba(19,27,46,0.92);
    border: 1px solid #1F2A44;
    border-radius: 8px;
    color: #E8E6DE;
    font-size: 12px;
    font-family: 'IBM Plex Mono', monospace;
    padding: 6px 12px;
    outline: none;
    width: 200px;
    backdrop-filter: blur(8px);
  }}
  .ctrl-input::placeholder {{ color: #64748B; }}
  .ctrl-input:focus {{ border-color: #C8973B; }}
  .ctrl-btn {{
    background: rgba(19,27,46,0.92);
    border: 1px solid #1F2A44;
    border-radius: 8px;
    color: #E8E6DE;
    font-size: 11px;
    font-family: 'IBM Plex Sans', sans-serif;
    padding: 6px 12px;
    cursor: pointer;
    backdrop-filter: blur(8px);
    transition: all 0.15s;
    white-space: nowrap;
  }}
  .ctrl-btn:hover {{ border-color: #C8973B; color: #C8973B; }}
  .ctrl-btn.active {{ background: rgba(200,151,59,0.18); border-color: #C8973B; color: #E8CE9E; }}
  .filter-select {{
    background: rgba(19,27,46,0.92);
    border: 1px solid #1F2A44;
    border-radius: 8px;
    color: #E8E6DE;
    font-size: 11px;
    font-family: 'IBM Plex Sans', sans-serif;
    padding: 6px 10px;
    cursor: pointer;
    outline: none;
    backdrop-filter: blur(8px);
  }}
  .filter-select option {{ background: #0B1220; }}

  /* ── Stats bar ── */
  #stats-bar {{
    position: absolute;
    bottom: 52px; left: 12px;
    z-index: 100;
    display: flex;
    gap: 8px;
    align-items: center;
  }}
  .stat-pill {{
    background: rgba(19,27,46,0.88);
    border: 1px solid #1F2A44;
    border-radius: 6px;
    font-size: 10px;
    font-family: 'IBM Plex Mono', monospace;
    padding: 4px 10px;
    color: #94A3B8;
    backdrop-filter: blur(6px);
  }}
  .stat-pill b {{ color: #E8E6DE; }}

  /* ── Legend ── */
  #legend {{
    position: absolute;
    bottom: 52px; right: 12px;
    z-index: 100;
    background: rgba(11,18,32,0.92);
    border: 1px solid #1F2A44;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 10px;
    font-family: 'IBM Plex Sans', sans-serif;
    backdrop-filter: blur(8px);
    display: flex;
    flex-direction: column;
    gap: 5px;
    min-width: 170px;
  }}
  .legend-title {{ font-size: 9px; color: #64748B; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 2px; }}
  .legend-row {{ display: flex; align-items: center; gap: 7px; color: #94A3B8; }}
  .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
  .legend-sq  {{ width: 10px; height: 10px; flex-shrink: 0; }}
  .legend-dm  {{ width: 10px; height: 10px; transform: rotate(45deg); flex-shrink: 0; }}

  /* ── Info panel (click on node) ── */
  #info-panel {{
    position: absolute;
    top: 12px; right: 12px;
    z-index: 100;
    background: rgba(11,18,32,0.96);
    border: 1px solid #1F2A44;
    border-radius: 10px;
    padding: 14px 16px;
    font-size: 11px;
    font-family: 'IBM Plex Sans', sans-serif;
    backdrop-filter: blur(12px);
    display: none;
    max-width: 260px;
    word-break: break-all;
  }}
  #info-panel .ip-title {{ font-size: 12px; font-weight: 600; color: #E8E6DE; margin-bottom: 8px; }}
  #info-panel .ip-row {{ display: flex; gap: 6px; margin-bottom: 4px; color: #94A3B8; }}
  #info-panel .ip-label {{ color: #64748B; min-width: 60px; flex-shrink: 0; }}
  #info-panel .ip-val {{ color: #E8E6DE; font-family: 'IBM Plex Mono', monospace; font-size: 10px; }}
  #info-panel .ip-band {{ display: inline-block; font-size: 9px; font-weight: 700; font-family: 'IBM Plex Mono', monospace; padding: 1px 6px; border-radius: 3px; }}
  #info-close {{ position: absolute; top: 8px; right: 10px; cursor: pointer; color: #64748B; font-size: 14px; }}
  #info-close:hover {{ color: #E8E6DE; }}

  #vis-container {{ width: 100%; height: 100%; }}
  .vis-tooltip {{ background: #0B1220 !important; border: 1px solid #1F2A44 !important; color: #E8E6DE !important; border-radius: 8px !important; font-size: 11px !important; font-family: 'IBM Plex Sans', sans-serif !important; padding: 8px 12px !important; box-shadow: 0 8px 24px rgba(0,0,0,0.6) !important; max-width: 280px !important; }}
</style>

<script>
// ── Inline vis.js (loaded from CDN at demo time; offline fallback is the full lib bundled) ──
// Using cdnjs — already in Streamlit's approved external sources for components
</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css"/>
</head>
<body>
<div id="graph-root">
  <!-- Controls -->
  <div id="controls">
    <input id="search-input" class="ctrl-input" placeholder="🔍 Search wallet / IP…" oninput="onSearch(this.value)"/>
    <select id="filter-group" class="filter-select" onchange="onFilterGroup(this.value)">
      <option value="all">All nodes</option>
      <option value="wallet">Wallets only</option>
      <option value="transaction">Transactions only</option>
      <option value="ip">IPs only</option>
    </select>
    <select id="filter-band" class="filter-select" onchange="onFilterBand(this.value)">
      <option value="all">All risk bands</option>
      <option value="CRITICAL">🔴 Critical</option>
      <option value="HIGH">🟠 High</option>
      <option value="MEDIUM">🟡 Medium</option>
      <option value="LOW">🟢 Low</option>
    </select>
    <button class="ctrl-btn active" id="btn-physics" onclick="togglePhysics()">⚡ Physics ON</button>
    <button class="ctrl-btn" onclick="network.fit()">Fit</button>
    <button class="ctrl-btn" onclick="highlightPaths()">Trace paths</button>
    <button class="ctrl-btn" onclick="clearHighlight()">Clear</button>
  </div>

  <!-- Canvas -->
  <div id="vis-container"></div>

  <!-- Stats -->
  <div id="stats-bar">
    <div class="stat-pill"><b id="stat-nodes">—</b> nodes</div>
    <div class="stat-pill"><b id="stat-edges">—</b> edges</div>
    <div class="stat-pill" id="stat-selected" style="display:none">Selected: <b id="stat-sel-label">—</b></div>
  </div>

  <!-- Legend -->
  <div id="legend">
    <div class="legend-title">Node Types</div>
    <div class="legend-row"><div class="legend-dot" style="background:#8B2E2E"></div> Critical Wallet</div>
    <div class="legend-row"><div class="legend-dot" style="background:#B8562E"></div> High Risk Wallet</div>
    <div class="legend-row"><div class="legend-dot" style="background:#C8973B"></div> Medium Wallet</div>
    <div class="legend-row"><div class="legend-dot" style="background:#5B7A6B"></div> Low Wallet</div>
    <div class="legend-row"><div class="legend-sq"  style="background:#7A6B8F"></div> Anomaly Tx</div>
    <div class="legend-row"><div class="legend-sq"  style="background:#2E4057"></div> Normal Tx</div>
    <div class="legend-row"><div class="legend-dm"  style="background:#38BDF8"></div> IP Node</div>
    <div class="legend-title" style="margin-top:6px">Edge Types</div>
    <div class="legend-row"><span style="color:rgba(200,151,59,0.8);font-size:14px">—</span> pays (BTC flow)</div>
    <div class="legend-row"><span style="color:rgba(91,122,107,0.8);font-size:14px">—</span> funds (input)</div>
    <div class="legend-row"><span style="color:rgba(56,189,248,0.7);font-size:14px">- -</span> relay / broadcast</div>
  </div>

  <!-- Info panel -->
  <div id="info-panel">
    <span id="info-close" onclick="closeInfoPanel()">✕</span>
    <div id="info-content"></div>
  </div>
</div>

<script>
const ALL_NODES = {nodes_json};
const ALL_EDGES = {edges_json};

const BAND_BG = {{
  CRITICAL: 'rgba(139,46,46,0.25)',
  HIGH:     'rgba(184,86,46,0.25)',
  MEDIUM:   'rgba(200,151,59,0.25)',
  LOW:      'rgba(91,122,107,0.25)',
}};
const BAND_TEXT = {{
  CRITICAL: '#E8A3A3', HIGH: '#E8B896', MEDIUM: '#E8CE9E', LOW: '#B3D1C2',
}};

let nodesDS = new vis.DataSet(ALL_NODES);
let edgesDS = new vis.DataSet(ALL_EDGES);
let physicsOn = true;
let selectedNodes = [];

const options = {{
  nodes: {{
    borderWidth: 1.5,
    borderWidthSelected: 3,
    font: {{ color: '#E8E6DE', size: 10, face: 'IBM Plex Mono,monospace' }},
    shadow: false,
  }},
  edges: {{
    width: 1,
    selectionWidth: 3,
    hoverWidth: 2,
    smooth: {{ type: 'dynamic', roundness: 0.3 }},
    font: {{ color: '#94A3B8', size: 9, strokeWidth: 0, align: 'middle' }},
  }},
  physics: {{
    enabled: true,
    forceAtlas2Based: {{
      gravitationalConstant: -55,
      centralGravity: 0.008,
      springLength: 120,
      springConstant: 0.06,
      damping: 0.5,
      avoidOverlap: 0.4,
    }},
    maxVelocity: 60,
    minVelocity: 0.75,
    solver: 'forceAtlas2Based',
    stabilization: {{ iterations: 180, fit: true }},
  }},
  interaction: {{
    hover: true,
    tooltipDelay: 150,
    navigationButtons: false,
    keyboard: {{ enabled: true, bindToWindow: false }},
    zoomView: true,
    dragView: true,
    multiselect: true,
    selectable: true,
  }},
  layout: {{
    randomSeed: 42,
    improvedLayout: true,
  }},
}};

const container = document.getElementById('vis-container');
const network = new vis.Network(container, {{ nodes: nodesDS, edges: edgesDS }}, options);

// Update stats
function updateStats() {{
  document.getElementById('stat-nodes').textContent = nodesDS.length;
  document.getElementById('stat-edges').textContent = edgesDS.length;
}}
updateStats();

// Physics toggle
function togglePhysics() {{
  physicsOn = !physicsOn;
  network.setOptions({{ physics: {{ enabled: physicsOn }} }});
  const btn = document.getElementById('btn-physics');
  btn.textContent = physicsOn ? '⚡ Physics ON' : '⚡ Physics OFF';
  btn.classList.toggle('active', physicsOn);
}}

// Stabilization done → turn off physics for cleaner interaction
network.on('stabilizationIterationsDone', () => {{
  if (physicsOn) togglePhysics();
}});

// Search
function onSearch(q) {{
  q = q.trim().toLowerCase();
  if (!q) {{ clearHighlight(); return; }}
  const matchIds = ALL_NODES
    .filter(n => n.id.toLowerCase().includes(q) || (n.label || '').toLowerCase().includes(q))
    .map(n => n.id);
  if (matchIds.length === 0) return;
  const updates = ALL_NODES.map(n => ({{
    ...n,
    opacity: matchIds.includes(n.id) ? 1.0 : 0.12,
  }}));
  nodesDS.update(updates);
  if (matchIds.length > 0) network.focus(matchIds[0], {{ scale: 1.4, animation: {{ duration: 500, easingFunction: 'easeInOutQuad' }} }});
}}

// Group filter
function onFilterGroup(group) {{
  if (group === 'all') {{ clearHighlight(); return; }}
  const updates = ALL_NODES.map(n => ({{ id: n.id, opacity: n.group === group ? 1.0 : 0.08 }}));
  nodesDS.update(updates);
}}

// Band filter (wallets only)
function onFilterBand(band) {{
  if (band === 'all') {{ clearHighlight(); return; }}
  const updates = ALL_NODES.map(n => {{
    if (n.group !== 'wallet') return {{ id: n.id, opacity: 0.08 }};
    return {{ id: n.id, opacity: n.band === band ? 1.0 : 0.08 }};
  }});
  nodesDS.update(updates);
}}

// Clear all highlights
function clearHighlight() {{
  nodesDS.update(ALL_NODES.map(n => ({{ id: n.id, opacity: 1.0 }})));
  edgesDS.update(ALL_EDGES.map(e => ({{ id: e.id, color: e.color, width: e.width }})));
  selectedNodes = [];
  document.getElementById('stat-selected').style.display = 'none';
}}

// Path highlighting — highlights all edges between selected nodes
function highlightPaths() {{
  if (selectedNodes.length < 2) return;
  const selSet = new Set(selectedNodes);
  const edgeUpdates = ALL_EDGES.map(e => {{
    const isPath = selSet.has(e.from) || selSet.has(e.to);
    return {{ id: e.id, color: {{ color: isPath ? '#DDAE55' : 'rgba(232,230,222,0.05)', highlight: '#DDAE55' }}, width: isPath ? 2.5 : 0.5 }};
  }});
  edgesDS.update(edgeUpdates);
}}

// Click: select node and show info panel
network.on('click', params => {{
  if (params.nodes.length > 0) {{
    const nodeId = params.nodes[0];
    const node   = ALL_NODES.find(n => n.id === nodeId);
    if (!node) return;
    if (!selectedNodes.includes(nodeId)) selectedNodes.push(nodeId);
    document.getElementById('stat-selected').style.display = 'inline';
    document.getElementById('stat-sel-label').textContent  = node.label;
    showInfoPanel(node);
  }} else if (params.edges.length === 0) {{
    selectedNodes = [];
    document.getElementById('stat-selected').style.display = 'none';
    closeInfoPanel();
  }}
}});

// Double-click: focus + 2-hop highlight
network.on('doubleClick', params => {{
  if (params.nodes.length === 0) return;
  const nodeId = params.nodes[0];
  const connected = network.getConnectedNodes(nodeId, 'all');
  const focus = [nodeId, ...connected];
  const updates = ALL_NODES.map(n => ({{ id: n.id, opacity: focus.includes(n.id) ? 1.0 : 0.1 }}));
  nodesDS.update(updates);
  network.focus(nodeId, {{ scale: 1.6, animation: {{ duration: 600, easingFunction: 'easeInOutQuad' }} }});
}});

// Info panel
function showInfoPanel(node) {{
  const panel = document.getElementById('info-panel');
  const content = document.getElementById('info-content');
  if (node.group === 'wallet') {{
    const bandBg   = BAND_BG[node.band]   || 'rgba(91,122,107,0.25)';
    const bandText = BAND_TEXT[node.band] || '#B3D1C2';
    content.innerHTML = `
      <div class="ip-title">🏦 Wallet Entity</div>
      <div class="ip-row"><span class="ip-label">Address</span><span class="ip-val" style="font-size:9px">${{node.id}}</span></div>
      <div class="ip-row"><span class="ip-label">Risk</span><span class="ip-val"><span class="ip-band" style="background:${{bandBg}};color:${{bandText}}">${{node.band}}</span> &nbsp;${{node.score?.toFixed(1)}}/100</span></div>
      <div class="ip-row"><span class="ip-label">Pattern</span><span class="ip-val">${{node.pattern || '—'}}</span></div>
    `;
  }} else if (node.group === 'transaction') {{
    content.innerHTML = `
      <div class="ip-title">📦 Transaction</div>
      <div class="ip-row"><span class="ip-label">TXID</span><span class="ip-val" style="font-size:9px">${{node.id}}</span></div>
      <div class="ip-row"><span class="ip-label">Pattern</span><span class="ip-val">${{node.pattern || 'normal'}}</span></div>
    `;
  }} else {{
    content.innerHTML = `
      <div class="ip-title">🌐 IP Node</div>
      <div class="ip-row"><span class="ip-label">Address</span><span class="ip-val">${{node.id}}</span></div>
      <div class="ip-row"><span class="ip-label">Role</span><span class="ip-val">Broadcast / relay</span></div>
    `;
  }}
  panel.style.display = 'block';
}}

function closeInfoPanel() {{
  document.getElementById('info-panel').style.display = 'none';
}}

// Keyboard: Esc closes info panel
document.addEventListener('keydown', e => {{ if (e.key === 'Escape') {{ clearHighlight(); closeInfoPanel(); }} }});
</script>
</body>
</html>"""
