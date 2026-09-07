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
  const [sortField, setSortField] = useState<keyof Entity>("composite_risk_score");
  const [sortAsc, setSortAsc] = useState(false);
  const pageSize = 25;

  if (entities.length === 0) {
    return (
      <div className="p-6 rounded-lg bg-[#131B2E] border border-[#1F2A44] text-[#94A3B8] font-mono text-xs flex items-center gap-2">
        <span className="text-[#C8973B]">ℹ️</span> No entities match these filters. Widen the risk band or lower the minimum score.
      </div>
    );
  }

  const handleSort = (field: keyof Entity) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(field === "wallet_address" || field === "dominant_country" ? true : false);
    }
    setCurrentPage(1);
  };

  const sortedEntities = [...entities].sort((a, b) => {
    const valA = a[sortField];
    const valB = b[sortField];
    if (typeof valA === "number" && typeof valB === "number") {
      return sortAsc ? valA - valB : valB - valA;
    }
    const strA = String(valA ?? "").toLowerCase();
    const strB = String(valB ?? "").toLowerCase();
    return sortAsc ? strA.localeCompare(strB) : strB.localeCompare(strA);
  });

  const exportCSV = () => {
    const headers: Array<keyof Entity> = [
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
    const escapeCsv = (value: unknown) => `"${String(value ?? "").replace(/"/g, '""')}"`;
    const rows = sortedEntities.map((entity) => headers.map((header) => escapeCsv(entity[header])).join(","));
    const csvContent = [`\uFEFF${headers.join(",")}`, ...rows].join("\r\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `ntro_filtered_alert_queue_${Date.now()}.csv`);
    try {
      document.body.appendChild(link);
      link.click();
    } finally {
      link.remove();
      URL.revokeObjectURL(url);
    }
  };

  const totalPages = Math.ceil(sortedEntities.length / pageSize);
  const startIdx = (currentPage - 1) * pageSize;
  const pageItems = sortedEntities.slice(startIdx, startIdx + pageSize);

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

  const renderSortIndicator = (field: keyof Entity) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-3 h-3 opacity-30 group-hover:opacity-70 inline ml-1" />;
    }
    return (
      <span className="text-[#C8973B] font-bold ml-1">
        {sortAsc ? "▲" : "▼"}
      </span>
    );
  };

  return (
    <div className="space-y-4">
      {/* Evidence-Grade Table Container */}
      <div className="border border-[#1F2A44] rounded-lg overflow-x-auto bg-[#131B2E] shadow-xl">
        <table className="w-full text-left font-mono text-xs text-[#E8E6DE] border-collapse">
          <thead>
            <tr className="bg-[#1A2438] text-[11px] font-semibold uppercase tracking-wider text-[#94A3B8] border-b border-[#1F2A44] select-none">
              <th
                onClick={() => handleSort("wallet_address")}
                className="p-3 pl-4 cursor-pointer hover:text-white group transition-colors"
              >
                <span>Wallet Address</span>
                {renderSortIndicator("wallet_address")}
              </th>
              <th
                onClick={() => handleSort("composite_risk_score")}
                className="p-3 cursor-pointer hover:text-white group transition-colors"
              >
                <span>Risk Score</span>
                {renderSortIndicator("composite_risk_score")}
              </th>
              <th
                onClick={() => handleSort("risk_band")}
                className="p-3 cursor-pointer hover:text-white group transition-colors"
              >
                <span>Band</span>
                {renderSortIndicator("risk_band")}
              </th>
              <th
                onClick={() => handleSort("confidence_score")}
                className="p-3 cursor-pointer hover:text-white group transition-colors"
              >
                <span>Confidence</span>
                {renderSortIndicator("confidence_score")}
              </th>
              <th
                onClick={() => handleSort("cluster_id")}
                className="p-3 cursor-pointer hover:text-white group transition-colors"
              >
                <span>Cluster ID</span>
                {renderSortIndicator("cluster_id")}
              </th>
              <th
                onClick={() => handleSort("dominant_country")}
                className="p-3 cursor-pointer hover:text-white group transition-colors"
              >
                <span>Jurisdiction</span>
                {renderSortIndicator("dominant_country")}
              </th>
              <th
                onClick={() => handleSort("dominant_asn")}
                className="p-3 cursor-pointer hover:text-white group transition-colors"
              >
                <span>ASN</span>
                {renderSortIndicator("dominant_asn")}
              </th>
              <th
                onClick={() => handleSort("total_received_amount")}
                className="p-3 cursor-pointer hover:text-white group transition-colors"
              >
                <span>Volume (₿)</span>
                {renderSortIndicator("total_received_amount")}
              </th>
              <th className="p-3 pr-4">Triggered Reason Codes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1F2A44]/60">
            {pageItems.map((r, i) => (
              <tr key={r.wallet_address} className="hover:bg-[#1A2438]/80 transition-colors">
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
        <span className="text-xs font-mono text-[#94A3B8]">{totalMatching} matching entities</span>
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
