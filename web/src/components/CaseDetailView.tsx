"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Download, ShieldAlert, Cpu, Network, FileText, CheckCircle2 } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";

interface CaseDetailProps {
  caseData: {
    wallet_address: string;
    composite_risk_score: number;
    risk_band: string;
    confidence_score: number;
    cluster_id: string;
    dominant_country: string;
    dominant_asn: string;
    dominant_ip: string;
    total_received_amount: number;
    total_sent_amount: number;
    reason_codes: string;
    ground_truth_label: string;
    plain_language_explanation: string;
    top_features: Array<{
      feature: string;
      display_name: string;
      value: number;
      shap_value: number;
    }>;
    cluster_info: {
      cluster_id: string;
      member_wallets: string[];
      heuristic_reasons: string[];
      clustering_confidence: number;
      investigative_rationale: string;
      total_members: number;
    };
    narrative_text: string;
  };
  topWallets: string[];
}

export default function CaseDetailView({ caseData, topWallets }: CaseDetailProps) {
  const router = useRouter();
  const [narrativeText, setNarrativeText] = useState(caseData.narrative_text);
  const [isDownloading, setIsDownloading] = useState(false);

  const handleWalletSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selected = e.target.value;
    router.push(`/dashboard/cases/${encodeURIComponent(selected)}`);
  };

  const handleDownloadSAR = async () => {
    try {
      setIsDownloading(true);
      const res = await fetch(`/api/cases/${encodeURIComponent(caseData.wallet_address)}/sar`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `SAR_CASE_${caseData.wallet_address.slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error("Failed to download SAR dossier:", err);
    } finally {
      setIsDownloading(false);
    }
  };

  const card1Class =
    caseData.risk_band === "CRITICAL"
      ? "critical-card"
      : caseData.risk_band === "HIGH"
      ? "high-card"
      : "";

  return (
    <div className="space-y-8">
      {/* Wallet Selector Dropdown */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-lg bg-[#131B2E] border border-[#1F2A44]">
        <div className="flex items-center gap-2">
          <label className="text-xs font-mono font-semibold text-[#94A3B8] uppercase">
            Target Wallet:
          </label>
          <select
            value={caseData.wallet_address}
            onChange={handleWalletSelect}
            className="bg-[#0B1220] border border-[#1F2A44] rounded px-3 py-1.5 text-xs font-mono text-[#C8973B] font-bold focus:outline-none focus:border-[#C8973B]"
          >
            {topWallets.map((w) => (
              <option key={w} value={w}>
                {w}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-[#94A3B8]">
          <span>IP: <b className="text-white">{caseData.dominant_ip}</b></span>
          <span>•</span>
          <span>ASN: <b className="text-white">{caseData.dominant_asn}</b></span>
        </div>
      </div>

      {/* Top 4 KPI Cards with Conditional Signature Stamp */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className={`metric-card ${card1Class}`}>
          <div className="text-[11px] font-mono uppercase text-[#94A3B8] tracking-wider mb-1">
            Composite Risk Score
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-2xl font-bold text-white">
              {caseData.composite_risk_score.toFixed(1)} / 100
            </span>
            {caseData.risk_band === "CRITICAL" && (
              <div className="case-stamp critical">Flagged — Critical Risk</div>
            )}
            {caseData.risk_band === "HIGH" && (
              <div className="case-stamp high">Flagged — High Risk</div>
            )}
          </div>
        </div>

        <div className="metric-card">
          <div className="text-[11px] font-mono uppercase text-[#94A3B8] tracking-wider mb-1">
            Detection Confidence
          </div>
          <div className="font-mono text-2xl font-bold text-white">
            {Math.round(caseData.confidence_score * 100)}%
          </div>
        </div>

        <div className="metric-card">
          <div className="text-[11px] font-mono uppercase text-[#94A3B8] tracking-wider mb-1">
            Entity Cluster ID
          </div>
          <div className="font-mono text-xl font-bold text-[#C8973B] truncate">
            {caseData.cluster_id}
          </div>
        </div>

        <div className="metric-card">
          <div className="text-[11px] font-mono uppercase text-[#94A3B8] tracking-wider mb-1">
            Geographic Origin
          </div>
          <div className="font-mono text-xl font-bold text-white truncate">
            {caseData.dominant_country}
          </div>
        </div>
      </div>

      {/* Plain-Language Investigator Summary */}
      <div className="bg-[#131B2E] border border-[#1F2A44] border-l-4 border-l-[#C8973B] rounded-lg p-5">
        <div className="flex items-center gap-2 mb-2">
          <FileText className="w-4 h-4 text-[#C8973B]" />
          <h3 className="text-sm font-semibold text-white font-sans">
            Plain-Language Investigator Summary
          </h3>
        </div>
        <p className="text-sm text-[#E8E6DE] leading-relaxed font-sans">
          {caseData.plain_language_explanation}
        </p>
      </div>

      {/* 2 Columns: SHAP Feature Attributions & Cluster Co-Members */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: SHAP TreeExplainer Attributions */}
        <div className="bg-[#131B2E] border border-[#1F2A44] rounded-lg p-5">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-white font-sans flex items-center gap-2">
              <Cpu className="w-4 h-4 text-[#C8973B]" /> Feature Attributions (SHAP TreeExplainer)
            </h3>
            <span className="text-[10px] font-mono text-[#E8A3A3] bg-[#8B2E2E]/15 px-2 py-0.5 rounded border border-[#8B2E2E]/30">
              SIGNALS
            </span>
          </div>
          <div className="text-[11px] text-[#94A3B8] mb-4">
            Positive values (<span className="text-[#E8A3A3]">Red</span>) drive anomaly escalation; negative values (<span className="text-[#B9CDC0]">Green</span>) indicate normal baseline behavior.
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={caseData.top_features}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
              >
                <XAxis
                  type="number"
                  stroke="#64748B"
                  tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }}
                />
                <YAxis
                  type="category"
                  dataKey="display_name"
                  stroke="#64748B"
                  tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }}
                />
                <Tooltip
                  formatter={(val: any) => [Number(val).toFixed(4), "SHAP Value"]}
                  contentStyle={{ backgroundColor: "#0B1220", borderColor: "#1F2A44", color: "#E8E6DE", fontSize: "11px", fontFamily: "monospace" }}
                />
                <ReferenceLine x={0} stroke="#64748B" strokeWidth={1} />
                <Bar dataKey="shap_value" radius={[0, 4, 4, 0]}>
                  {caseData.top_features.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.shap_value > 0 ? "#8B2E2E" : "#5B7A6B"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right: Cluster Co-Members & Heuristics */}
        <div className="bg-[#131B2E] border border-[#1F2A44] rounded-lg p-5 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white font-sans flex items-center gap-2">
              <Network className="w-4 h-4 text-[#C8973B]" /> Entity Cluster Co-Members & Heuristics
            </h3>
            <span className="text-xs font-mono font-bold text-[#C8973B]">
              Confidence: {Math.round(caseData.cluster_info.clustering_confidence * 100)}%
            </span>
          </div>

          <div className="bg-[#0B1220] border border-[#1F2A44] rounded p-3 mb-4 text-xs">
            <div className="flex flex-wrap gap-1.5 mb-2">
              {caseData.cluster_info.heuristic_reasons.map((h, i) => (
                <span
                  key={i}
                  className="px-2 py-0.5 rounded bg-[#C8973B]/15 text-[#C8973B] border border-[#C8973B]/30 font-mono text-[10px]"
                >
                  {h}
                </span>
              ))}
            </div>
            <p className="text-[11px] text-[#94A3B8] leading-relaxed">
              {caseData.cluster_info.investigative_rationale}
            </p>
          </div>

          <div className="flex-1 border border-[#1F2A44] rounded overflow-y-auto max-h-48 bg-[#0B1220]">
            <table className="w-full text-left font-mono text-xs text-[#E8E6DE]">
              <thead className="bg-[#1A2438] text-[10px] uppercase text-[#94A3B8] sticky top-0">
                <tr>
                  <th className="p-2.5 pl-3">
                    Co-Member Addresses ({caseData.cluster_info.total_members} total)
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1F2A44]">
                {caseData.cluster_info.member_wallets.map((m, i) => (
                  <tr key={i} className="hover:bg-[#1A2438]/50">
                    <td className="p-2.5 pl-3 text-[#C8973B] font-mono text-[11px] truncate">
                      {m}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Law Enforcement Case Narrative & SAR Export */}
      <div className="bg-[#131B2E] border border-[#1F2A44] rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white font-sans">
              Law Enforcement Case Narrative (SAR / STR Package)
            </h3>
            <div className="text-xs text-[#94A3B8]">
              Standardized evidence summary ready for submission to Financial Intelligence Unit (FIU-IND).
            </div>
          </div>

          <button
            onClick={handleDownloadSAR}
            disabled={isDownloading}
            className="inline-flex items-center gap-2 px-4 py-2 rounded bg-[#C8973B] hover:bg-[#DDAE55] text-[#05070B] font-mono text-xs font-bold transition-all shadow-[0_4px_16px_rgba(200,151,59,0.3)] disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            {isDownloading ? "Generating..." : "Download Official SAR/STR Case Package (JSON)"}
          </button>
        </div>

        <textarea
          rows={7}
          value={narrativeText}
          onChange={(e) => setNarrativeText(e.target.value)}
          className="w-full bg-[#0B1220] border border-[#1F2A44] rounded p-4 font-mono text-xs text-[#E8E6DE] leading-relaxed focus:outline-none focus:border-[#C8973B]"
        />
      </div>
    </div>
  );
}
