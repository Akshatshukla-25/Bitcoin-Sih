"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { ZoomIn, ZoomOut, RotateCcw, Shield, ArrowRight } from "lucide-react";

interface Node {
  id: string;
  label: string;
  full_label: string;
  type: "wallet" | "transaction" | "ip";
  risk_band?: string;
  risk_score?: number;
  pattern?: string;
  color: string;
  size: number;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

interface LinkItem {
  source: string;
  target: string;
  type: string;
  amount: number;
  color: string;
}

interface NetworkGraphViewProps {
  initialData: {
    scope: string;
    node_count: number;
    edge_count: number;
    nodes: Node[];
    links: LinkItem[];
    legend: Array<{ label: string; color: string; type: string }>;
  };
}

export default function NetworkGraphView({ initialData }: NetworkGraphViewProps) {
  const [scope, setScope] = useState(initialData.scope || "top30");
  const [graphData, setGraphData] = useState(initialData);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Graph interaction state
  const transformRef = useRef({ x: 0, y: 0, k: 1 });
  const isDraggingRef = useRef(false);
  const lastMousePosRef = useRef({ x: 0, y: 0 });

  const fetchScopeData = async (newScope: string) => {
    try {
      setIsLoading(true);
      const res = await fetch(`/api/network?scope=${newScope}`);
      const json = await res.json();
      setGraphData(json);
      setScope(newScope);
    } catch (err) {
      console.error("Error fetching network graph:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Run a lightweight force simulation layout on graphData
  useEffect(() => {
    const nodes = graphData.nodes.map((n, i) => {
      const angle = (i / graphData.nodes.length) * 2 * Math.PI;
      const radius = 180 + (i % 3) * 60;
      return {
        ...n,
        x: 400 + Math.cos(angle) * radius,
        y: 280 + Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
      };
    });

    const nodeMap = new Map(nodes.map((n) => [n.id, n]));
    const links = graphData.links
      .map((l) => ({
        ...l,
        sourceNode: nodeMap.get(l.source),
        targetNode: nodeMap.get(l.target),
      }))
      .filter((l) => l.sourceNode && l.targetNode);

    // Simple spring iterations
    for (let iter = 0; iter < 50; iter++) {
      // Repulsion
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x! - nodes[i].x!;
          const dy = nodes[j].y! - nodes[i].y!;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          if (dist < 200) {
            const force = (200 - dist) / (dist * 10);
            nodes[i].x! -= dx * force;
            nodes[i].y! -= dy * force;
            nodes[j].x! += dx * force;
            nodes[j].y! += dy * force;
          }
        }
      }

      // Attraction along links
      for (const link of links) {
        const s = link.sourceNode!;
        const t = link.targetNode!;
        const dx = t.x! - s.x!;
        const dy = t.y! - s.y!;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (dist - 100) * 0.04;
        s.x! += (dx / dist) * force;
        s.y! += (dy / dist) * force;
        t.x! -= (dx / dist) * force;
        t.y! -= (dy / dist) * force;
      }
    }

    // Render loop
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      const { x, y, k } = transformRef.current;
      ctx.translate(x, y);
      ctx.scale(k, k);

      // Draw Edges
      for (const l of links) {
        const s = l.sourceNode!;
        const t = l.targetNode!;
        ctx.beginPath();
        ctx.moveTo(s.x!, s.y!);
        ctx.lineTo(t.x!, t.y!);
        ctx.strokeStyle = "rgba(232, 230, 222, 0.15)";
        ctx.lineWidth = 1.2;
        ctx.stroke();

        // Direction Arrow
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
        ctx.fillStyle = "rgba(200, 151, 59, 0.5)";
        ctx.fill();
      }

      // Draw Nodes
      for (const n of nodes) {
        ctx.save();
        ctx.translate(n.x!, n.y!);

        if (n.type === "wallet") {
          ctx.beginPath();
          ctx.arc(0, 0, n.size, 0, 2 * Math.PI);
          ctx.fillStyle = n.color;
          ctx.fill();
          ctx.strokeStyle = "#FFFFFF";
          ctx.lineWidth = 1;
          ctx.stroke();
        } else if (n.type === "transaction") {
          ctx.fillStyle = n.color;
          ctx.fillRect(-n.size / 2, -n.size / 2, n.size, n.size);
          ctx.strokeStyle = "rgba(255,255,255,0.4)";
          ctx.lineWidth = 1;
          ctx.strokeRect(-n.size / 2, -n.size / 2, n.size, n.size);
        } else if (n.type === "ip") {
          ctx.save();
          ctx.rotate(Math.PI / 4);
          ctx.fillStyle = n.color;
          ctx.fillRect(-n.size / 2, -n.size / 2, n.size, n.size);
          ctx.restore();
        }

        // Label
        ctx.fillStyle = "#E8E6DE";
        ctx.font = "10px monospace";
        ctx.textAlign = "center";
        ctx.fillText(n.label, 0, n.size + 12);

        ctx.restore();
      }

      ctx.restore();
      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [graphData]);

  // Mouse interaction handlers for Pan and Zoom
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    isDraggingRef.current = true;
    lastMousePosRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - lastMousePosRef.current.x;
    const dy = e.clientY - lastMousePosRef.current.y;
    lastMousePosRef.current = { x: e.clientX, y: e.clientY };
    transformRef.current.x += dx;
    transformRef.current.y += dy;
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleZoom = (delta: number) => {
    transformRef.current.k = Math.max(0.3, Math.min(3, transformRef.current.k + delta));
  };

  const handleResetZoom = () => {
    transformRef.current = { x: 0, y: 0, k: 1 };
  };

  return (
    <div className="space-y-4">
      {/* Scope Toggles */}
      <div className="flex flex-wrap items-center justify-between gap-4">
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

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleZoom(0.15)}
            className="p-1.5 rounded bg-[#131B2E] border border-[#1F2A44] hover:border-[#C8973B] text-[#E8E6DE]"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleZoom(-0.15)}
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
            Nodes: <b className="text-white">{graphData.node_count}</b> | Links: <b className="text-white">{graphData.edge_count}</b>
          </span>
        </div>
      </div>

      {/* Graph Canvas Container */}
      <div className="relative border border-[#1F2A44] rounded-lg overflow-hidden bg-[#0B1220] h-[550px] shadow-2xl">
        {isLoading && (
          <div className="absolute inset-0 bg-[#0B1220]/75 flex items-center justify-center font-mono text-xs text-[#C8973B] z-20">
            Recomputing network layout...
          </div>
        )}
        <canvas
          ref={canvasRef}
          width={880}
          height={550}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          className="w-full h-full cursor-grab active:cursor-grabbing"
        />
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
      </div>
    </div>
  );
}
