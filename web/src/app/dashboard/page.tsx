import React from "react";
import { fetchApi } from "@/lib/api";
import OverviewCharts from "@/components/OverviewCharts";

interface OverviewData {
  kpis: {
    total_entities: number;
    active_alerts: number;
    critical_count: number;
    high_count: number;
    medium_count: number;
    low_count: number;
    flagged_volume_btc: number;
    total_transactions: number;
  };
  histogram: Array<{
    bin: string;
    min: number;
    max: number;
    CRITICAL: number;
    HIGH: number;
    MEDIUM: number;
    LOW: number;
    total: number;
  }>;
  reason_codes: Array<{
    reason_code: string;
    count: number;
  }>;
  jurisdictions: Array<{
    country: string;
    entities: number;
  }>;
  volume_timeline: Array<{
    date: string;
    display_date: string;
    volume: number;
    count: number;
  }>;
}

export default async function OverviewPage() {
  let data: OverviewData | null = null;
  let errorMsg = "";

  try {
    data = await fetchApi<OverviewData>("/api/overview");
  } catch (err: any) {
    errorMsg = err.message || "Failed to load overview data from API";
  }

  if (!data) {
    return (
      <div className="p-6 rounded-lg bg-red-900/20 border border-red-500/40 text-red-200 font-mono text-sm">
        ⚠️ {errorMsg || "Unable to reach backend API on http://127.0.0.1:8000"}
      </div>
    );
  }

  const { kpis, histogram, reason_codes, jurisdictions, volume_timeline } = data;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-bold font-serif text-white mb-1">
          Forensic Threat Landscape & Executive Summary
        </h2>
        <div className="text-xs text-[#94A3B8]">
          Real-time aggregated anomaly statistics across 699 Bitcoin wallet entities.
        </div>
      </div>

      {/* 5 KPI Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        <div className="metric-card">
          <div className="text-[11px] font-mono uppercase text-[#94A3B8] tracking-wider mb-1">
            Total Entities
          </div>
          <div className="font-mono text-2xl font-bold text-white">
            {kpis.total_entities.toLocaleString()}
          </div>
        </div>

        <div className="metric-card">
          <div className="text-[11px] font-mono uppercase text-[#94A3B8] tracking-wider mb-1">
            Active Alerts
          </div>
          <div className="font-mono text-2xl font-bold text-[#C8973B]">
            {kpis.active_alerts}
          </div>
        </div>

        <div className="metric-card critical-card">
          <div className="text-[11px] font-mono uppercase text-[#94A3B8] tracking-wider mb-1">
            Critical Threats
          </div>
          <div className="font-mono text-2xl font-bold text-[#E8A3A3]">
            {kpis.critical_count}
          </div>
        </div>

        <div className="metric-card high-card">
          <div className="text-[11px] font-mono uppercase text-[#94A3B8] tracking-wider mb-1">
            High Escalations
          </div>
          <div className="font-mono text-2xl font-bold text-[#E8B896]">
            {kpis.high_count}
          </div>
        </div>

        <div className="metric-card">
          <div className="text-[11px] font-mono uppercase text-[#94A3B8] tracking-wider mb-1">
            Flagged Volume
          </div>
          <div className="font-mono text-2xl font-bold text-white">
            {kpis.flagged_volume_btc.toFixed(2)} ₿
          </div>
        </div>
      </div>

      {/* Overview Charts Component */}
      <OverviewCharts
        histogram={histogram}
        reasonCodes={reason_codes}
        jurisdictions={jurisdictions}
        volumeTimeline={volume_timeline}
      />
    </div>
  );
}
