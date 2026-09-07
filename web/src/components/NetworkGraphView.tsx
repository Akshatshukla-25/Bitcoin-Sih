"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { ZoomIn, ZoomOut, RotateCcw, Shield, ExternalLink, X, Info, Activity } from "lucide-react";

interface Node {
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
  vx?: number;
  vy?: number;
  isCenter?: boolean;
}

interface LinkItem {
  source: string;
  target: string;
  type: string;
  port?: number | null;
  amount: number;
  color: string;
}

interface WalletOption {
  wallet: string;
  score: number;
  band: string;
}

interface NetworkGraphViewProps {
  initialData: {
    scope: string;
    selected_wallet?: string;
    wallet_options?: WalletOption[];
    node_count: number;
    edge_count: number;
    nodes: Node[];
    links: LinkItem[];
    legend: Array<{ label: string; color: string; type: string }>;
  };
  embedded?: boolean;
}

export default function NetworkGraphView({ initialData, embedded = false }: NetworkGraphViewProps) {
  const [scope, setScope] = useState(initialData.scope || "top30");
  const [selectedEgoWallet, setSelectedEgoWallet] = useState(
    initialData.selected_wallet || (initialData.wallet_options?.[0]?.wallet ?? "")
  );
  const [graphData, setGraphData] = useState(initialData);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [hoveredNode, setHoveredNode] = useState<Node | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [isLoading, setIsLoading] = useState(false);

  const containerRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const nodesRef = useRef<Node[]>([]);
  const linksRef = useRef<any[]>([]);

  // Pan, Zoom & Drag references
  const transformRef = useRef({ x: 0, y: 0, k: 1 });
  const isPanningRef = useRef(false);
  const draggedNodeRef = useRef<Node | null>(null);
  const lastMousePosRef = useRef({ x: 0, y: 0 });
  const hasMovedRef = useRef(false);

  // Sync state whenever initialData changes from parent
  useEffect(() => {
    if (initialData) {
      setGraphData(initialData);
      setScope(initialData.scope || "top30");
      if (initialData.selected_wallet) {
        setSelectedEgoWallet(initialData.selected_wallet);
      }
      setSelectedNode(null);
    }
  }, [initialData]);

  const fetchScopeData = async (newScope: string, targetWallet?: string) => {
    try {
      setIsLoading(true);
      const walletParam = targetWallet || selectedEgoWallet;
      const url =
        newScope === "ego"
          ? `/api/network?scope=ego&wallet=${encodeURIComponent(walletParam)}`
          : `/api/network?scope=top30`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      if (json && Array.isArray(json.nodes)) {
        setGraphData(json);
        setScope(newScope);
        if (json.selected_wallet) {
          setSelectedEgoWallet(json.selected_wallet);
        } else if (targetWallet) {
          setSelectedEgoWallet(targetWallet);
        }
        setSelectedNode(null);
      }
    } catch (err) {
      console.error("Error fetching network graph:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEgoWalletChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSelectedEgoWallet(val);
    fetchScopeData("ego", val);
  };

  const handleCenterEgoOnNode = (walletId: string) => {
    setSelectedEgoWallet(walletId);
    fetchScopeData("ego", walletId);
  };

  // Main Canvas Rendering Routine
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();

    const { x, y, k } = transformRef.current;
    ctx.translate(x, y);
    ctx.scale(k, k);

    const nodes = nodesRef.current;
    const links = linksRef.current;

    // 1. Draw Edges
    for (const l of links) {
      const s = l.sourceNode!;
      const t = l.targetNode!;

      const isIncident =
        (selectedNode && (l.source === selectedNode.id || l.target === selectedNode.id)) ||
        (hoveredNode && (l.source === hoveredNode.id || l.target === hoveredNode.id));

      const isNetworkEdge = l.type === "broadcasts" || l.type === "relays_to";

      ctx.beginPath();
      ctx.moveTo(s.x!, s.y!);
      ctx.lineTo(t.x!, t.y!);

      if (isNetworkEdge) {
        ctx.setLineDash([4, 4]);
        ctx.strokeStyle = isIncident
          ? "rgba(56, 189, 248, 1.0)"
          : (selectedNode || hoveredNode)
          ? "rgba(56, 189, 248, 0.1)"
          : "rgba(56, 189, 248, 0.45)";
        ctx.lineWidth = isIncident ? 2.5 : 1.2;
      } else {
        ctx.setLineDash([]);
        ctx.strokeStyle = isIncident
          ? "rgba(200, 151, 59, 1.0)"
          : (selectedNode || hoveredNode)
          ? "rgba(232, 230, 222, 0.08)"
          : "rgba(232, 230, 222, 0.25)";
        ctx.lineWidth = isIncident ? 2.5 : 1.3;
      }
      ctx.stroke();
      ctx.setLineDash([]);

      // Directional arrow head
      const angle = Math.atan2(t.y! - s.y!, t.x! - s.x!);
      const midX = (s.x! + t.x!) / 2;
      const midY = (s.y! + t.y!) / 2;
      ctx.beginPath();
      ctx.moveTo(midX, midY);
      ctx.lineTo(
        midX - 7 * Math.cos(angle - Math.PI / 6),
        midY - 7 * Math.sin(angle - Math.PI / 6)
      );
      ctx.lineTo(
        midX - 7 * Math.cos(angle + Math.PI / 6),
        midY - 7 * Math.sin(angle + Math.PI / 6)
      );
      ctx.fillStyle = isIncident
        ? (isNetworkEdge ? "#38BDF8" : "#C8973B")
        : (isNetworkEdge ? "rgba(56, 189, 248, 0.7)" : "rgba(200, 151, 59, 0.6)");
      ctx.fill();
    }

    // 2. Draw Nodes
    for (const n of nodes) {
      ctx.save();
      ctx.translate(n.x!, n.y!);

      const isSelected = selectedNode?.id === n.id;
      const isHovered = hoveredNode?.id === n.id;
      const isTarget = n.is_ego_center || (scope === "ego" && n.id === selectedEgoWallet);

      // Target Halo Ring & Badge
      if (isTarget) {
        ctx.beginPath();
        ctx.arc(0, 0, n.size + 10, 0, 2 * Math.PI);
        ctx.strokeStyle = "rgba(200, 151, 59, 0.9)";
        ctx.lineWidth = 2.5;
        ctx.stroke();

        ctx.fillStyle = "#C8973B";
        ctx.font = "bold 9px monospace";
        ctx.textAlign = "center";
        ctx.fillText("★ TARGET ENTITY", 0, -n.size - 13);
      }

      // Outer Selection / Hover Ring
      if (isSelected || isHovered) {
        ctx.beginPath();
        ctx.arc(0, 0, n.size + 6, 0, 2 * Math.PI);
        ctx.strokeStyle = isSelected ? "#C8973B" : "rgba(255, 255, 255, 0.5)";
        ctx.lineWidth = 2;
        ctx.setLineDash(isSelected ? [] : [4, 4]);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      if (n.type === "wallet") {
        ctx.beginPath();
        ctx.arc(0, 0, n.size, 0, 2 * Math.PI);
        ctx.fillStyle = n.color;
        ctx.fill();
        ctx.strokeStyle = isSelected || isTarget ? "#FFFFFF" : "rgba(255, 255, 255, 0.4)";
        ctx.lineWidth = isSelected || isTarget ? 2.5 : 1;
        ctx.stroke();
      } else if (n.type === "transaction") {
        ctx.fillStyle = n.color;
        ctx.fillRect(-n.size / 2, -n.size / 2, n.size, n.size);
        ctx.strokeStyle = isSelected ? "#FFFFFF" : "rgba(255, 255, 255, 0.45)";
        ctx.lineWidth = isSelected ? 2 : 1;
        ctx.strokeRect(-n.size / 2, -n.size / 2, n.size, n.size);
      } else if (n.type === "ip") {
        ctx.save();
        ctx.rotate(Math.PI / 4);
        ctx.fillStyle = n.color;
        ctx.fillRect(-n.size / 2, -n.size / 2, n.size, n.size);
        ctx.strokeStyle = isSelected ? "#FFFFFF" : "rgba(255, 255, 255, 0.35)";
        ctx.lineWidth = isSelected ? 2 : 1;
        ctx.strokeRect(-n.size / 2, -n.size / 2, n.size, n.size);
        ctx.restore();
      }

      // Label below node
      ctx.fillStyle = isSelected || isTarget ? "#C8973B" : "#E8E6DE";
      ctx.font = `${isSelected || isTarget ? "bold " : ""}10px monospace`;
      ctx.textAlign = "center";
      ctx.fillText(n.label, 0, n.size + 13);

      ctx.restore();
    }

    ctx.restore();
  }, [selectedNode, hoveredNode, scope, selectedEgoWallet]);

  // Layout simulation and physics
  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    const width = container?.clientWidth || 920;
    const height = container?.clientHeight || (embedded ? 460 : 550);
    if (canvas) {
      canvas.width = width;
      canvas.height = height;
    }

    const rawNodes = graphData?.nodes || [];
    const rawLinks = graphData?.links || [];
    const isEgo = scope === "ego";
    const centerWallet = graphData.selected_wallet || selectedEgoWallet;

    const nodes: Node[] = rawNodes.map((n, i) => {
      const isCenter = isEgo && (n.is_ego_center || n.id === centerWallet);
      if (isCenter) {
        return {
          ...n,
          isCenter: true,
          x: width / 2,
          y: height / 2,
          vx: 0,
          vy: 0,
        };
      }
      const angle = (i / Math.max(1, rawNodes.length)) * 2 * Math.PI;
      const radius = n.type === "transaction" ? 110 : (n.type === "ip" ? 210 : 170);
      return {
        ...n,
        isCenter: false,
        x: width / 2 + Math.cos(angle) * radius,
        y: height / 2 + Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
      };
    });

    const nodeMap = new Map(nodes.map((n) => [n.id, n]));
    const links = rawLinks
      .map((l) => ({
        ...l,
        sourceNode: nodeMap.get(l.source),
        targetNode: nodeMap.get(l.target),
      }))
      .filter((l) => l.sourceNode && l.targetNode);

    // Iterative organic force relaxation
    const iterations = 80;
    for (let iter = 0; iter < iterations; iter++) {
      const alpha = 1.0 - iter / iterations;

      // Center gravity (for non-center nodes)
      for (const n of nodes) {
        if (n.isCenter) {
          n.x = width / 2;
          n.y = height / 2;
          continue;
        }
        n.x! += (width / 2 - n.x!) * 0.02 * alpha;
        n.y! += (height / 2 - n.y!) * 0.02 * alpha;
      }

      // Repulsion between nodes
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x! - nodes[i].x!;
          const dy = nodes[j].y! - nodes[i].y!;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const minDist = nodes[i].size + nodes[j].size + 40;
          if (dist < minDist) {
            const force = ((minDist - dist) / dist) * 0.25 * alpha;
            if (!nodes[i].isCenter) {
              nodes[i].x! -= dx * force;
              nodes[i].y! -= dy * force;
            }
            if (!nodes[j].isCenter) {
              nodes[j].x! += dx * force;
              nodes[j].y! += dy * force;
            }
          }
        }
      }

      // Spring attraction along edges
      for (const link of links) {
        const s = link.sourceNode!;
        const t = link.targetNode!;
        const dx = t.x! - s.x!;
        const dy = t.y! - s.y!;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const targetDist = link.type === "broadcasts" || link.type === "relays_to" ? 85 : 70;
        const force = ((dist - targetDist) / dist) * 0.09 * alpha;
        if (!s.isCenter) {
          s.x! += dx * force;
          s.y! += dy * force;
        }
        if (!t.isCenter) {
          t.x! -= dx * force;
          t.y! -= dy * force;
        }
      }
    }

    nodesRef.current = nodes;
    linksRef.current = links;

    // Trigger initial redraw
    draw();

    const handleResize = () => {
      if (container && canvas) {
        canvas.width = container.clientWidth;
        canvas.height = container.clientHeight || (embedded ? 460 : 550);
        draw();
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [graphData, draw, scope, selectedEgoWallet, embedded]);

  // Coordinate projection helper
  const getCanvasCoords = (clientX: number, clientY: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0, rawX: 0, rawY: 0 };
    const rect = canvas.getBoundingClientRect();
    const mouseX = clientX - rect.left;
    const mouseY = clientY - rect.top;
    const { x, y, k } = transformRef.current;
    return {
      x: (mouseX - x) / k,
      y: (mouseY - y) / k,
      rawX: mouseX,
      rawY: mouseY,
    };
  };

  // Find node at coordinate
  const findNodeAt = (graphX: number, graphY: number): Node | null => {
    const nodes = nodesRef.current;
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i];
      const dx = n.x! - graphX;
      const dy = n.y! - graphY;
      if (dx * dx + dy * dy <= (n.size + 4) * (n.size + 4)) {
        return n;
      }
    }
    return null;
  };

  // Mouse Listeners
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const coords = getCanvasCoords(e.clientX, e.clientY);
    const hitNode = findNodeAt(coords.x, coords.y);
    hasMovedRef.current = false;
    lastMousePosRef.current = { x: e.clientX, y: e.clientY };

    if (hitNode) {
      draggedNodeRef.current = hitNode;
    } else {
      isPanningRef.current = true;
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const dx = e.clientX - lastMousePosRef.current.x;
    const dy = e.clientY - lastMousePosRef.current.y;
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) {
      hasMovedRef.current = true;
    }
    lastMousePosRef.current = { x: e.clientX, y: e.clientY };

    if (draggedNodeRef.current) {
      const { k } = transformRef.current;
      draggedNodeRef.current.x! += dx / k;
      draggedNodeRef.current.y! += dy / k;
      draw();
      return;
    }

    if (isPanningRef.current) {
      transformRef.current.x += dx;
      transformRef.current.y += dy;
      draw();
      return;
    }

    // Hover check
    const coords = getCanvasCoords(e.clientX, e.clientY);
    const hit = findNodeAt(coords.x, coords.y);
    if (hit !== hoveredNode) {
      setHoveredNode(hit);
      setTooltipPos({ x: coords.rawX, y: coords.rawY });
      draw();
    }
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!hasMovedRef.current) {
      const coords = getCanvasCoords(e.clientX, e.clientY);
      const hitNode = findNodeAt(coords.x, coords.y);
      setSelectedNode(hitNode);
      draw();
    }
    isPanningRef.current = false;
    draggedNodeRef.current = null;
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
    transformRef.current.k = Math.max(0.3, Math.min(3.5, transformRef.current.k * zoomFactor));
    draw();
  };

  const handleZoomBtn = (delta: number) => {
    transformRef.current.k = Math.max(0.3, Math.min(3.5, transformRef.current.k + delta));
    draw();
  };

  const handleResetZoom = () => {
    transformRef.current = { x: 0, y: 0, k: 1 };
    draw();
  };

  return (
    <div className="space-y-4">
      {/* Scope Toggles & Wallet Selector */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="inline-flex rounded-lg bg-[#131B2E] p-1 border border-[#1F2A44]">
            <button
              onClick={() => fetchScopeData("top30")}
              className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium transition-all ${
                scope === "top30"
                  ? "bg-[#C8973B] text-[#05070B] font-bold"
                  : "text-[#94A3B8] hover:text-white"
              }`}
            >
              Top 30 High-Risk Subgraph
            </button>
            <button
              onClick={() => fetchScopeData("ego")}
              className={`px-3 py-1.5 rounded-md text-xs font-mono font-medium transition-all ${
                scope === "ego"
                  ? "bg-[#C8973B] text-[#05070B] font-bold"
                  : "text-[#94A3B8] hover:text-white"
              }`}
            >
              Ego-Network of Selected Case
            </button>
          </div>

          {scope === "ego" && graphData.wallet_options && (
            <div className="flex items-center gap-2">
              <label className="text-[11px] font-mono text-[#94A3B8] uppercase">Target:</label>
              <select
                value={selectedEgoWallet}
                onChange={handleEgoWalletChange}
                className="bg-[#131B2E] border border-[#1F2A44] rounded px-3 py-1 text-xs font-mono text-[#C8973B] font-bold focus:outline-none focus:border-[#C8973B]"
              >
                {graphData.wallet_options.map((opt) => (
                  <option key={opt.wallet} value={opt.wallet}>
                    {opt.wallet.slice(0, 16)}... ({opt.score} - {opt.band})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleZoomBtn(0.2)}
            className="p-1.5 rounded bg-[#131B2E] border border-[#1F2A44] hover:border-[#C8973B] text-[#E8E6DE]"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleZoomBtn(-0.2)}
            className="p-1.5 rounded bg-[#131B2E] border border-[#1F2A44] hover:border-[#C8973B] text-[#E8E6DE]"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleResetZoom}
            className="p-1.5 rounded bg-[#131B2E] border border-[#1F2A44] hover:border-[#C8973B] text-[#E8E6DE]"
            title="Reset View"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <span className="text-xs font-mono text-[#94A3B8] ml-2">
            Nodes: <b className="text-white">{graphData.node_count}</b> | Links:{" "}
            <b className="text-white">{graphData.edge_count}</b>
          </span>
        </div>
      </div>

      {/* Main Canvas Stage & Node Inspector Panel */}
      <div
        ref={containerRef}
        className={`relative border border-[#1F2A44] rounded-lg overflow-hidden bg-[#0B1220] shadow-2xl ${
          embedded ? "h-[460px]" : "h-[550px]"
        }`}
      >
        {isLoading && (
          <div className="absolute inset-0 bg-[#0B1220]/75 flex items-center justify-center font-mono text-xs text-[#C8973B] z-20">
            Recomputing network layout...
          </div>
        )}

        <canvas
          ref={canvasRef}
          width={920}
          height={embedded ? 460 : 550}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={() => {
            isPanningRef.current = false;
            draggedNodeRef.current = null;
            setHoveredNode(null);
            draw();
          }}
          onWheel={handleWheel}
          className={`w-full h-full ${
            hoveredNode ? "cursor-pointer" : "cursor-grab active:cursor-grabbing"
          }`}
        />

        {/* Hover Tooltip */}
        {hoveredNode && !selectedNode && (
          <div
            className="absolute z-10 pointer-events-none bg-[#0B1220]/95 border border-[#C8973B]/50 p-2.5 rounded shadow-2xl font-mono text-xs text-[#E8E6DE]"
            style={{
              left: `${Math.min(tooltipPos.x + 15, 680)}px`,
              top: `${Math.min(tooltipPos.y + 15, 450)}px`,
            }}
          >
            <div className="font-bold text-[#C8973B] flex items-center gap-1.5">
              <span className="uppercase">{hoveredNode.type}:</span>
              <span>{hoveredNode.label}</span>
            </div>
            {hoveredNode.type === "wallet" && (
              <div className="text-[11px] text-[#94A3B8] mt-1 space-y-0.5">
                <div>Risk Score: <b className="text-white">{hoveredNode.risk_score}</b> ({hoveredNode.risk_band})</div>
                <div>Country: <b className="text-white">{hoveredNode.dominant_country}</b></div>
              </div>
            )}
            {hoveredNode.type === "transaction" && (
              <div className="text-[11px] text-[#94A3B8] mt-1 space-y-0.5">
                <div>Pattern: <b className="text-white">{hoveredNode.pattern}</b></div>
                <div>Amount: <b className="text-white">{hoveredNode.amount?.toFixed(4)} ₿</b></div>
              </div>
            )}
            {hoveredNode.type === "ip" && (
              <div className="text-[11px] text-[#94A3B8] mt-1 space-y-0.5">
                <div>Location: <b className="text-white">{hoveredNode.city}, {hoveredNode.country}</b></div>
                <div>ASN: <b className="text-white">{hoveredNode.asn}</b></div>
              </div>
            )}
          </div>
        )}

        {/* Selected Node Inspector Drawer */}
        {selectedNode && (
          <div className="absolute top-4 right-4 w-80 bg-[#131B2E]/95 backdrop-blur-xl border border-[#C8973B]/40 rounded-xl p-4 shadow-2xl z-20 space-y-3 font-sans text-xs">
            <div className="flex items-center justify-between border-b border-[#1F2A44] pb-2">
              <div className="flex items-center gap-2">
                <span
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: selectedNode.color }}
                />
                <span className="font-mono font-bold uppercase text-[#E8E6DE]">
                  {selectedNode.type} Profile
                </span>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-[#94A3B8] hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2 font-mono text-[11px]">
              <div>
                <span className="text-[#94A3B8] block text-[10px] uppercase">Entity ID:</span>
                <span className="text-[#C8973B] font-bold break-all">{selectedNode.full_label}</span>
              </div>

              {selectedNode.type === "wallet" && (
                <>
                  <div className="grid grid-cols-2 gap-2 pt-1">
                    <div>
                      <span className="text-[#94A3B8] block text-[10px] uppercase">Risk Score:</span>
                      <b className="text-white text-sm">{selectedNode.risk_score} / 100</b>
                    </div>
                    <div>
                      <span className="text-[#94A3B8] block text-[10px] uppercase">Risk Band:</span>
                      <b
                        className={
                          selectedNode.risk_band === "CRITICAL"
                            ? "text-[#E8A3A3]"
                            : selectedNode.risk_band === "HIGH"
                            ? "text-[#E8B896]"
                            : "text-[#E8CE9E]"
                        }
                      >
                        {selectedNode.risk_band}
                      </b>
                    </div>
                  </div>

                  <div className="pt-1">
                    <span className="text-[#94A3B8] block text-[10px] uppercase">Cluster ID:</span>
                    <span className="text-white">{selectedNode.cluster_id}</span>
                  </div>

                  <div className="pt-1">
                    <span className="text-[#94A3B8] block text-[10px] uppercase">Jurisdiction & ASN:</span>
                    <span className="text-white">
                      {selectedNode.dominant_country} ({selectedNode.dominant_asn})
                    </span>
                  </div>

                  <div className="pt-2 border-t border-[#1F2A44] flex flex-col gap-2">
                    <button
                      onClick={() => handleCenterEgoOnNode(selectedNode.full_label)}
                      className="w-full inline-flex items-center justify-center gap-1.5 py-1.5 px-3 rounded bg-[#131B2E] hover:bg-[#1A2438] border border-[#C8973B]/50 hover:border-[#C8973B] text-[#C8973B] font-mono text-xs font-bold transition-all"
                    >
                      <Activity className="w-3.5 h-3.5" />
                      <span>Center Ego-Network</span>
                    </button>
                    <Link
                      href={`/dashboard/cases/${encodeURIComponent(selectedNode.full_label)}`}
                      className="w-full inline-flex items-center justify-center gap-1.5 py-2 px-3 rounded bg-[#C8973B] hover:bg-[#DDAE55] text-[#05070B] font-mono text-xs font-bold transition-all shadow-[0_2px_10px_rgba(200,151,59,0.3)]"
                    >
                      <span>Inspect Case Dossier</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </>
              )}

              {selectedNode.type === "transaction" && (
                <div className="space-y-2 pt-1">
                  <div>
                    <span className="text-[#94A3B8] block text-[10px] uppercase">Transaction Pattern:</span>
                    <span className="text-white font-bold text-sm">{selectedNode.pattern}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <span className="text-[#94A3B8] block text-[10px] uppercase">Input Amount:</span>
                      <span className="text-white font-bold">{selectedNode.amount?.toFixed(4)} ₿</span>
                    </div>
                    <div>
                      <span className="text-[#94A3B8] block text-[10px] uppercase">Network Fee:</span>
                      <span className="text-white">{selectedNode.fee ? `${selectedNode.fee.toFixed(6)} ₿` : "N/A"}</span>
                    </div>
                  </div>
                  <div>
                    <span className="text-[#94A3B8] block text-[10px] uppercase">Script Standard:</span>
                    <span className="text-white">{selectedNode.script_type || "P2PKH"}</span>
                  </div>
                </div>
              )}

              {selectedNode.type === "ip" && (
                <div className="space-y-2 pt-1">
                  <div>
                    <span className="text-[#94A3B8] block text-[10px] uppercase">Node Address:</span>
                    <span className="text-white font-bold text-sm">{selectedNode.full_label}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <span className="text-[#94A3B8] block text-[10px] uppercase">Country:</span>
                      <span className="text-white">{selectedNode.country} ({selectedNode.country_code})</span>
                    </div>
                    <div>
                      <span className="text-[#94A3B8] block text-[10px] uppercase">City:</span>
                      <span className="text-white">{selectedNode.city || "Unknown"}</span>
                    </div>
                  </div>
                  <div>
                    <span className="text-[#94A3B8] block text-[10px] uppercase">Autonomous System (ASN):</span>
                    <span className="text-white">{selectedNode.asn}</span>
                  </div>
                  <div>
                    <span className="text-[#94A3B8] block text-[10px] uppercase">AS Organization:</span>
                    <span className="text-[#94A3B8] text-[10px] break-words">{selectedNode.as_org || "Unknown"}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Badge Chip Legend */}
      <div className="flex flex-wrap gap-2 pt-1 font-mono text-[11px]">
        <span className="bg-[#8B2E2E]/20 text-[#E8A3A3] px-2.5 py-1 border border-[#8B2E2E]/50 rounded">
          🔴 Critical Wallet (Score ≥ 60)
        </span>
        <span className="bg-[#B8562E]/20 text-[#E8B896] px-2.5 py-1 border border-[#B8562E]/50 rounded">
          🟠 High Risk Wallet (Score 50–59)
        </span>
        <span className="bg-[#C8973B]/20 text-[#E8D4A2] px-2.5 py-1 border border-[#C8973B]/50 rounded">
          🟡 Medium Risk Wallet (Score 35–49)
        </span>
        <span className="bg-[#5B7A6B]/20 text-[#B3D1C2] px-2.5 py-1 border border-[#5B7A6B]/50 rounded">
          🟢 Normal Wallet
        </span>
        <span className="bg-[#7A6B8F]/20 text-[#D1C5DE] px-2.5 py-1 border border-[#7A6B8F]/50 rounded">
          🟣 Anomaly Tx
        </span>
        <span className="bg-[#2E4057]/20 text-[#ADC2D8] px-2.5 py-1 border border-[#2E4057]/50 rounded">
          🔵 Normal Tx
        </span>
        <span className="bg-[#3E5C76]/20 text-[#A6C2DE] px-2.5 py-1 border border-[#3E5C76]/50 rounded">
          🔷 IP Node
        </span>
        <span className="bg-[#C8973B]/15 text-[#E8D4A2] px-2.5 py-1 border border-[#C8973B]/40 rounded">
          ── Solid: Bitcoin Funds/Pays
        </span>
        <span className="bg-[#38BDF8]/15 text-[#BAE6FD] px-2.5 py-1 border border-[#38BDF8]/40 rounded">
          - - Dashed: Network IP Signal
        </span>
      </div>
    </div>
  );
}
