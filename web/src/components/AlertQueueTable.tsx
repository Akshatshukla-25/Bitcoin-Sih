"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Download, ExternalLink, ArrowUpDown } from "lucide-react";

interface Entity {
  wallet_address: string;
  composite_risk_score: number;
  risk_band: string;
  confidence_score: number;
  cluster_id: string;
  dominant_country: string;
  dominant_asn: string;
  total_received_amount: number;
  reason_codes: string;
}

interface AlertQueueTableProps {
  entities: Entity[];
  totalMatching: number;
}

export default function AlertQueueTable({ entities, totalMatching }: AlertQueueTableProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 25;

  if (entities.length === 0) {
    return (
      <div className="p-6 rounded-lg bg-[#131B2E] border border-[#1F2A44] text-[#94A3B8] font-mono text-xs flex items-center gap-2">
        <span className="text-[#C8973B]">ℹ️</span> No entities match these filters. Widen the risk band or lower the minimum score.
      </div>
    );
  }

  const exportCSV = () => {
    const headers = [
      "wallet_address",
      "composite_risk_score",
      "risk_band",
      "confidence_score",
      "cluster_id",
      "dominant_country",
      "dominant_asn",
      "total_received_amount",
      "reason_codes",
    ];
    const rows = entities.map((e) =>
      headers.map((h) => `"${(e as any)[h] ?? ""}"`).join(",")
    );
    const csvContent = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `ntro_filtered_alert_queue_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const totalPages = Math.ceil(entities.length / pageSize);
  const startIdx = (currentPage - 1) * pageSize;
  const pageItems = entities.slice(startIdx, startIdx + pageSize);

  const getBadgeClass = (band: string) => {
    switch (band) {
      case "CRITICAL":
        return "badge-critical";
      case "HIGH":
        return "badge-high";
      case "MEDIUM":
        return "badge-medium";
      default:
        return "badge-low";
    }
  };

  return (
    <div className="space-y-4">
      {/* Evidence-Grade Table Container */}
      <div className="border border-[#1F2A44] rounded-lg overflow-x-auto bg-[#131B2E] shadow-xl">
        <table className="w-full text-left font-mono text-xs text-[#E8E6DE] border-collapse">
          <thead>
            <tr className="bg-[#1A2438] text-[11px] font-semibold uppercase tracking-wider text-[#94A3B8] border-b border-[#1F2A44]">
              <th className="p-3 pl-4">Wallet Address</th>
              <th className="p-3">Risk Score</th>
              <th className="p-3">Band</th>
              <th className="p-3">Confidence</th>
              <th className="p-3">Cluster ID</th>
              <th className="p-3">Jurisdiction</th>
              <th className="p-3">ASN</th>
              <th className="p-3">Volume (₿)</th>
              <th className="p-3 pr-4">Triggered Reason Codes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1F2A44]/60">
            {pageItems.map((r, i) => (
              <tr key={i} className="hover:bg-[#1A2438]/80 transition-colors">
                <td className="p-3 pl-4">
                  <Link
                    href={`/dashboard/cases/${encodeURIComponent(r.wallet_address)}`}
                    className="text-[#C8973B] hover:text-[#DDAE55] hover:underline flex items-center gap-1.5"
                  >
                    <span>{r.wallet_address}</span>
                    <ExternalLink className="w-3 h-3 opacity-60" />
                  </Link>
                </td>
                <td className="p-3 font-bold">{r.composite_risk_score.toFixed(1)}</td>
                <td className="p-3">
                  <span className={getBadgeClass(r.risk_band)}>{r.risk_band}</span>
                </td>
                <td className="p-3">{Math.round(r.confidence_score * 100)}%</td>
                <td className="p-3 text-[#94A3B8]">{r.cluster_id}</td>
                <td className="p-3">{r.dominant_country}</td>
                <td className="p-3 text-[#94A3B8]">{r.dominant_asn}</td>
                <td className="p-3">{r.total_received_amount.toFixed(4)}</td>
                <td className="p-3 pr-4 text-[11px] text-[#94A3B8] max-w-xs truncate">
                  {r.reason_codes}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination & Export Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
        <button
          onClick={exportCSV}
          className="inline-flex items-center gap-2 px-4 py-2 rounded bg-[#131B2E] hover:bg-[#1A2438] border border-[#1F2A44] hover:border-[#C8973B]/50 text-xs font-mono text-[#E8E6DE] transition-all"
        >
          <Download className="w-3.5 h-3.5 text-[#C8973B]" />
          Export Filtered Alert Queue to CSV
        </button>

        {totalPages > 1 && (
          <div className="flex items-center gap-2 text-xs font-mono text-[#94A3B8]">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-2.5 py-1 rounded bg-[#131B2E] border border-[#1F2A44] disabled:opacity-30 hover:border-[#C8973B]"
            >
              Prev
            </button>
            <span>
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-2.5 py-1 rounded bg-[#131B2E] border border-[#1F2A44] disabled:opacity-30 hover:border-[#C8973B]"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
