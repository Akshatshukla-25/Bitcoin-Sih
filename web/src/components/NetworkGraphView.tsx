"use client";

import Link from "next/link";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ExternalLink, RotateCcw, X, ZoomIn, ZoomOut } from "lucide-react";

interface GraphNode {
  id: string;
  label: string;
  full_label: string;
  type: "wallet" | "transaction" | "ip";
  is_ego_center?: boolean;
  risk_band?: string;
  risk_score?: number;
  pattern?: string;
  cluster_id?: string;
  dominant_country?: string;
  dominant_asn?: string;
  total_volume?: number;
  amount?: number;
  fee?: number;
  script_type?: string;
  country?: string;
  country_code?: string;
  asn?: string;
  as_org?: string;
  city?: string;
  color: string;
  size: number;
  x?: number;
  y?: number;
}

interface GraphLink {
  id: string;
  key: string;
  source: string;
  target: string;
  type: string;
  port?: number | null;
  amount?: number | null;
  color: string;
}

interface PositionedLink extends GraphLink {
  sourceNode: GraphNode;
  targetNode: GraphNode;
  parallelIndex: number;
  parallelCount: number;
}

interface WalletOption {
  wallet: string;
  score: number;
  band: string;
}

export interface NetworkData {
  scope: "ego" | "top30";
  selected_wallet?: string | null;
  wallet_options?: WalletOption[];
  node_count: number;
  edge_count: number;
  nodes: GraphNode[];
  links: GraphLink[];
  legend: Array<{ label: string; color: string; type: string }>;
}

interface NetworkGraphViewProps {
  initialData: NetworkData;
  initialError?: string | null;
  embedded?: boolean;
}

const MIN_ZOOM = 0.35;
const MAX_ZOOM = 3;

function edgeControl(link: PositionedLink) {
  const sourceX = link.sourceNode.x ?? 0;
  const sourceY = link.sourceNode.y ?? 0;
  const targetX = link.targetNode.x ?? 0;
  const targetY = link.targetNode.y ?? 0;
  const dx = targetX - sourceX;
  const dy = targetY - sourceY;
  const distance = Math.hypot(dx, dy) || 1;
  const offset = (link.parallelIndex - (link.parallelCount - 1) / 2) * 18;
  return {
    x: (sourceX + targetX) / 2 - (dy / distance) * offset,
    y: (sourceY + targetY) / 2 + (dx / distance) * offset,
  };
}

export default function NetworkGraphView({ initialData, initialError = null, embedded = false }: NetworkGraphViewProps) {
  const [graphData, setGraphData] = useState(initialData);
  const [scope, setScope] = useState<"ego" | "top30">(initialData.scope || "top30");
  const [selectedWallet, setSelectedWallet] = useState(
    initialData.selected_wallet || initialData.wallet_options?.[0]?.wallet || "",
  );
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphLink | null>(null);
  const [error, setError] = useState<string | null>(initialError);
  const [isLoading, setIsLoading] = useState(false);
  const [viewport, setViewport] = useState({ width: 920, height: embedded ? 460 : 550 });

  const containerRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const requestRef = useRef(0);
  const transformRef = useRef({ x: 0, y: 0, k: 1 });
  const panRef = useRef<{ active: boolean; x: number; y: number }>({ active: false, x: 0, y: 0 });

  useEffect(() => {
    setGraphData(initialData);
    setScope(initialData.scope || "top30");
    if (initialData.selected_wallet) setSelectedWallet(initialData.selected_wallet);
    setSelectedNode(null);
    setSelectedEdge(null);
  }, [initialData]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const update = () => {
      setViewport({
        width: Math.max(320, container.clientWidth),
        height: Math.max(320, container.clientHeight || (embedded ? 460 : 550)),
      });
    };
    update();
    const observer = new ResizeObserver(update);
    observer.observe(container);
    return () => observer.disconnect();
  }, [embedded]);

  const positionedNodes = useMemo(() => {
    const centerX = viewport.width / 2;
    const centerY = viewport.height / 2;
    const radius = Math.max(90, Math.min(viewport.width, viewport.height) * 0.39);
    const ordered = [...graphData.nodes].sort((a, b) => a.id.localeCompare(b.id));
    const centerIndex = ordered.findIndex(
      (node) => node.is_ego_center || (scope === "ego" && node.id === graphData.selected_wallet),
    );
    return ordered.map((node, index) => {
      if (index === centerIndex) return { ...node, x: centerX, y: centerY };
      const ringIndex = index > centerIndex && centerIndex >= 0 ? index - 1 : index;
      const ringCount = Math.max(1, ordered.length - (centerIndex >= 0 ? 1 : 0));
      const angle = (ringIndex / ringCount) * Math.PI * 2 - Math.PI / 2;
      const typeScale = node.type === "ip" ? 1 : node.type === "transaction" ? 0.75 : 0.9;
      return {
        ...node,
        x: centerX + Math.cos(angle) * radius * typeScale,
        y: centerY + Math.sin(angle) * radius * typeScale,
      };
    });
  }, [graphData.nodes, graphData.selected_wallet, scope, viewport]);

  const positionedLinks = useMemo(() => {
    const nodeMap = new Map(positionedNodes.map((node) => [node.id, node]));
    const grouped = new Map<string, GraphLink[]>();
    for (const link of graphData.links) {
      const key = `${link.source}\u0000${link.target}`;
      grouped.set(key, [...(grouped.get(key) || []), link]);
    }
    const links: PositionedLink[] = [];
    grouped.forEach((group) => {
      group.sort((a, b) => a.id.localeCompare(b.id));
      group.forEach((link, index) => {
        const sourceNode = nodeMap.get(link.source);
        const targetNode = nodeMap.get(link.target);
        if (sourceNode && targetNode) {
          links.push({ ...link, sourceNode, targetNode, parallelIndex: index, parallelCount: group.length });
        }
      });
    });
    return links.sort((a, b) => a.id.localeCompare(b.id));
  }, [graphData.links, positionedNodes]);

  const fitGraph = useCallback(() => {
    transformRef.current = { x: 0, y: 0, k: 1 };
  }, []);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.round(viewport.width * ratio);
    canvas.height = Math.round(viewport.height * ratio);
    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;
    const context = canvas.getContext("2d");
    if (!context) return;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.clearRect(0, 0, viewport.width, viewport.height);
    const transform = transformRef.current;
    context.save();
    context.translate(transform.x, transform.y);
    context.scale(transform.k, transform.k);

    for (const link of positionedLinks) {
      const control = edgeControl(link);
      const sourceX = link.sourceNode.x ?? 0;
      const sourceY = link.sourceNode.y ?? 0;
      const targetX = link.targetNode.x ?? 0;
      const targetY = link.targetNode.y ?? 0;
      const highlighted = selectedEdge?.id === link.id || selectedNode?.id === link.source || selectedNode?.id === link.target;
      const networkEdge = link.type === "broadcasts" || link.type === "relays_to";
      context.beginPath();
      context.moveTo(sourceX, sourceY);
      context.quadraticCurveTo(control.x, control.y, targetX, targetY);
      context.setLineDash(networkEdge ? [4, 4] : []);
      context.strokeStyle = highlighted ? (networkEdge ? "#38BDF8" : "#C8973B") : networkEdge ? "rgba(56,189,248,.45)" : "rgba(232,230,222,.24)";
      context.lineWidth = highlighted ? 2.5 : 1.2;
      context.stroke();
      context.setLineDash([]);

      const midX = 0.25 * sourceX + 0.5 * control.x + 0.25 * targetX;
      const midY = 0.25 * sourceY + 0.5 * control.y + 0.25 * targetY;
      const tangentX = targetX - sourceX;
      const tangentY = targetY - sourceY;
      const angle = Math.atan2(tangentY, tangentX);
      context.beginPath();
      context.moveTo(midX, midY);
      context.lineTo(midX - 7 * Math.cos(angle - Math.PI / 6), midY - 7 * Math.sin(angle - Math.PI / 6));
      context.lineTo(midX - 7 * Math.cos(angle + Math.PI / 6), midY - 7 * Math.sin(angle + Math.PI / 6));
      context.closePath();
      context.fillStyle = networkEdge ? "#38BDF8" : "#C8973B";
      context.fill();
    }

    for (const node of positionedNodes) {
      const x = node.x ?? 0;
      const y = node.y ?? 0;
      const active = selectedNode?.id === node.id;
      context.save();
      context.translate(x, y);

      if (node.is_ego_center) {
        context.beginPath();
        context.arc(0, 0, node.size + 8, 0, Math.PI * 2);
        context.strokeStyle = "rgba(200, 151, 59, 0.55)";
        context.lineWidth = 2;
        context.stroke();

        context.beginPath();
        context.arc(0, 0, node.size + 14, 0, Math.PI * 2);
        context.strokeStyle = "rgba(200, 151, 59, 0.25)";
        context.lineWidth = 1;
        context.stroke();
      }

      context.beginPath();
      if (node.type === "wallet") context.arc(0, 0, node.size, 0, Math.PI * 2);
      else if (node.type === "transaction") context.rect(-node.size / 2, -node.size / 2, node.size, node.size);
      else {
        context.rotate(Math.PI / 4);
        context.rect(-node.size / 2, -node.size / 2, node.size, node.size);
      }
      context.fillStyle = node.color;
      context.fill();
      context.strokeStyle = active || node.is_ego_center ? "#FFFFFF" : "rgba(255,255,255,.4)";
      context.lineWidth = active ? 3 : (node.is_ego_center ? 2.5 : 1);
      context.stroke();
      context.restore();
      context.fillStyle = active || node.is_ego_center ? "#C8973B" : "#E8E6DE";
      context.font = `${active || node.is_ego_center ? "bold " : ""}10px ui-monospace, monospace`;
      context.textAlign = "center";
      context.fillText(node.label, x, y + node.size + 13);
    }
    context.restore();
  }, [positionedLinks, positionedNodes, selectedEdge, selectedNode, viewport]);

  useEffect(() => {
    fitGraph();
    draw();
  }, [draw, fitGraph, graphData]);

  const fetchScopeData = async (nextScope: "ego" | "top30", wallet?: string) => {
    const target = wallet || selectedWallet;
    if (nextScope === "ego" && !target) {
      setError("Select a wallet before loading an ego network.");
      return;
    }
    const requestId = ++requestRef.current;
    setIsLoading(true);
    setError(null);
    try {
      const query = nextScope === "ego" ? `scope=ego&wallet=${encodeURIComponent(target)}` : "scope=top30";
      const response = await fetch(`/api/network?${query}`, { cache: "no-store" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : `HTTP ${response.status}`);
      if (!Array.isArray(payload.nodes) || !Array.isArray(payload.links)) throw new Error("Network API returned an invalid payload.");
      if (requestId !== requestRef.current) return;
      setGraphData(payload as NetworkData);
      setScope(nextScope);
      setSelectedWallet(payload.selected_wallet || target);
      setSelectedNode(null);
      setSelectedEdge(null);
    } catch (caught) {
      if (requestId === requestRef.current) setError(caught instanceof Error ? caught.message : "Unable to load graph data.");
    } finally {
      if (requestId === requestRef.current) setIsLoading(false);
    }
  };

  const canvasPoint = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const transform = transformRef.current;
    return { x: (event.clientX - rect.left - transform.x) / transform.k, y: (event.clientY - rect.top - transform.y) / transform.k };
  };

  const selectAt = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const point = canvasPoint(event);
    const node = [...positionedNodes].reverse().find((candidate) => Math.hypot((candidate.x ?? 0) - point.x, (candidate.y ?? 0) - point.y) <= candidate.size + 5);
    setSelectedNode(node || null);
    if (node) setSelectedEdge(null);
  };

  const zoom = useCallback((amount: number) => {
    transformRef.current.k = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, transformRef.current.k + amount));
    draw();
  }, [draw]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const handleWheel = (event: WheelEvent) => {
      event.preventDefault();
      zoom(event.deltaY < 0 ? 0.12 : -0.12);
    };
    canvas.addEventListener("wheel", handleWheel, { passive: false });
    return () => {
      canvas.removeEventListener("wheel", handleWheel);
    };
  }, [zoom]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="inline-flex rounded-lg bg-[#131B2E] p-1 border border-[#1F2A44]" role="group" aria-label="Graph scope">
            <button disabled={isLoading} aria-pressed={scope === "top30"} onClick={() => fetchScopeData("top30")} className={`px-3 py-1.5 rounded-md text-xs font-mono ${scope === "top30" ? "bg-[#C8973B] text-[#05070B] font-bold" : "text-[#94A3B8]"}`}>Top 30 High-Risk Subgraph</button>
            <button disabled={isLoading || !selectedWallet} aria-pressed={scope === "ego"} onClick={() => fetchScopeData("ego")} className={`px-3 py-1.5 rounded-md text-xs font-mono ${scope === "ego" ? "bg-[#C8973B] text-[#05070B] font-bold" : "text-[#94A3B8]"}`}>Selected Wallet Ego Network</button>
          </div>
          <label htmlFor="ego-wallet" className="text-[11px] font-mono text-[#94A3B8] uppercase">Target wallet</label>
          <select id="ego-wallet" disabled={isLoading} value={selectedWallet} onChange={(event) => { setSelectedWallet(event.target.value); void fetchScopeData("ego", event.target.value); }} className="bg-[#131B2E] border border-[#1F2A44] rounded px-3 py-1 text-xs font-mono text-[#C8973B]">
            {(graphData.wallet_options || []).map((option) => <option key={option.wallet} value={option.wallet}>{option.wallet.slice(0, 16)}… ({option.score} - {option.band})</option>)}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <button aria-label="Zoom in" onClick={() => zoom(0.2)} className="p-1.5 rounded bg-[#131B2E] border border-[#1F2A44]"><ZoomIn aria-hidden="true" className="w-4 h-4" /></button>
          <button aria-label="Zoom out" onClick={() => zoom(-0.2)} className="p-1.5 rounded bg-[#131B2E] border border-[#1F2A44]"><ZoomOut aria-hidden="true" className="w-4 h-4" /></button>
          <button aria-label="Fit graph to view" onClick={() => { fitGraph(); draw(); }} className="p-1.5 rounded bg-[#131B2E] border border-[#1F2A44]"><RotateCcw aria-hidden="true" className="w-4 h-4" /></button>
          <span className="text-xs font-mono text-[#94A3B8]">Nodes: <b className="text-white">{graphData.node_count}</b> | Edges: <b className="text-white">{graphData.edge_count}</b></span>
        </div>
      </div>

      {error && <div role="alert" className="border border-[#8B2E2E] bg-[#8B2E2E]/20 text-[#E8A3A3] rounded p-3 text-sm">Graph request failed: {error} <button className="underline ml-2" onClick={() => fetchScopeData(scope)}>Retry</button></div>}
      <div ref={containerRef} className={`relative border border-[#1F2A44] rounded-lg overflow-hidden bg-[#0B1220] ${embedded ? "h-[460px]" : "h-[550px]"}`}>
        {isLoading && <div aria-live="polite" className="absolute inset-0 z-20 bg-[#0B1220]/75 flex items-center justify-center text-[#C8973B]">Loading graph…</div>}
        <canvas ref={canvasRef} aria-label={`Directed tripartite graph containing ${graphData.node_count} nodes and ${graphData.edge_count} edges. Complete tabular data follows.`} onClick={selectAt} onMouseDown={(event) => { panRef.current = { active: true, x: event.clientX, y: event.clientY }; }} onMouseMove={(event) => { if (!panRef.current.active) return; transformRef.current.x += event.clientX - panRef.current.x; transformRef.current.y += event.clientY - panRef.current.y; panRef.current = { active: true, x: event.clientX, y: event.clientY }; draw(); }} onMouseUp={() => { panRef.current.active = false; }} onMouseLeave={() => { panRef.current.active = false; }} className="w-full h-full cursor-grab active:cursor-grabbing" />
        {selectedNode && <aside aria-label="Selected node details" className="absolute top-4 right-4 w-80 max-w-[90%] bg-[#131B2E]/95 border border-[#C8973B]/40 rounded-xl p-4 z-10 text-xs space-y-2">
          <div className="flex justify-between"><strong className="uppercase">{selectedNode.type} profile</strong><button aria-label="Close node details" onClick={() => setSelectedNode(null)}><X aria-hidden="true" className="w-4 h-4" /></button></div>
          <div className="font-mono break-all text-[#C8973B]">{selectedNode.full_label}</div>
          {selectedNode.risk_score !== undefined && <div>Risk: {selectedNode.risk_score} / 100 ({selectedNode.risk_band})</div>}
          {selectedNode.pattern && <div>Pattern: {selectedNode.pattern}; amount: {selectedNode.amount?.toFixed(4) ?? "Not provided"} BTC</div>}
          {selectedNode.country && <div>Location: {selectedNode.city}, {selectedNode.country}; ASN: {selectedNode.asn}</div>}
          {selectedNode.type === "wallet" && <Link href={`/dashboard/cases/${encodeURIComponent(selectedNode.id)}`} className="inline-flex items-center gap-1 text-[#C8973B] underline">Inspect case <ExternalLink aria-hidden="true" className="w-3 h-3" /></Link>}
        </aside>}
      </div>

      <details className="bg-[#131B2E] border border-[#1F2A44] rounded p-3">
        <summary className="cursor-pointer font-semibold">Accessible graph data ({graphData.node_count} nodes, {graphData.edge_count} directed edges)</summary>
        <div className="mt-3 overflow-auto max-h-80 space-y-5">
          <table className="w-full text-xs"><caption className="text-left font-bold mb-2">Nodes</caption><thead><tr><th scope="col" className="text-left">ID</th><th scope="col" className="text-left">Type</th><th scope="col" className="text-left">Risk/pattern/location</th></tr></thead><tbody>{positionedNodes.map((node) => <tr key={node.id}><td><button className="text-[#C8973B] text-left break-all" onClick={() => { setSelectedNode(node); setSelectedEdge(null); }}>{node.id}</button></td><td>{node.type}</td><td>{node.risk_band || node.pattern || node.country || "Not provided"}</td></tr>)}</tbody></table>
          <table className="w-full text-xs"><caption className="text-left font-bold mb-2">Directed edges</caption><thead><tr><th scope="col" className="text-left">Source → target</th><th scope="col" className="text-left">Relationship</th><th scope="col" className="text-left">Amount/port</th></tr></thead><tbody>{positionedLinks.map((edge) => <tr key={edge.id}><td><button className="text-[#C8973B] text-left break-all" onClick={() => { setSelectedEdge(edge); setSelectedNode(null); }}>{edge.source} → {edge.target}</button></td><td>{edge.type} (key {edge.key})</td><td>{edge.amount !== null && edge.amount !== undefined ? `${edge.amount} BTC` : edge.port !== null && edge.port !== undefined ? `port ${edge.port}` : "Not provided"}</td></tr>)}</tbody></table>
        </div>
      </details>
      {selectedEdge && <div role="region" aria-label="Selected edge details" className="bg-[#131B2E] border border-[#C8973B]/40 rounded p-3 text-xs font-mono"><div className="flex justify-between"><strong>{selectedEdge.type}</strong><button aria-label="Close edge details" onClick={() => setSelectedEdge(null)}><X aria-hidden="true" className="w-4 h-4" /></button></div><div className="break-all">{selectedEdge.source} → {selectedEdge.target}</div><div>Key: {selectedEdge.key}; Amount: {selectedEdge.amount ?? "Not provided"}; Port: {selectedEdge.port ?? "Not provided"}</div></div>}
    </div>
  );
}
