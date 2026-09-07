"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  Legend,
} from "recharts";

interface OverviewChartsProps {
  histogram: Array<{
    bin: string;
    CRITICAL: number;
    HIGH: number;
    MEDIUM: number;
    LOW: number;
    total: number;
  }>;
  reasonCodes: Array<{
    reason_code: string;
    count: number;
  }>;
  jurisdictions: Array<{
    country: string;
    entities: number;
  }>;
  volumeTimeline: Array<{
    display_date: string;
    volume: number;
    count: number;
  }>;
}

export default function OverviewCharts({
  histogram,
  reasonCodes,
  jurisdictions,
  volumeTimeline,
}: OverviewChartsProps) {
  const customTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#0B1220] border border-[#1F2A44] p-2.5 rounded shadow-xl font-mono text-xs text-[#E8E6DE]">
          <div className="font-bold text-[#C8973B] mb-1">{label}</div>
          {payload.map((p: any, idx: number) => (
            <div key={idx} className="flex justify-between gap-4">
              <span style={{ color: p.color }}>{p.name}:</span>
              <span className="font-bold">{p.value}</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* 1. Composite Risk Score Distribution */}
      <div className="bg-[#131B2E] border border-[#1F2A44] rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-[#E8E6DE] font-sans">
            Composite Risk Score Distribution
          </h3>
          <span className="text-[10px] font-mono text-[#C8973B] bg-[#C8973B]/10 border border-[#C8973B]/30 px-2 py-0.5 rounded">
            RISK SPECTRUM
          </span>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={histogram} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2A44" vertical={false} />
              <XAxis dataKey="bin" stroke="#64748B" tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }} />
              <YAxis stroke="#64748B" tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }} />
              <Tooltip content={customTooltip} />
              <Legend wrapperStyle={{ fontSize: "11px", fontFamily: "monospace" }} />
              <Bar dataKey="CRITICAL" fill="#8B2E2E" stackId="a" name="Critical" />
              <Bar dataKey="HIGH" fill="#B8562E" stackId="a" name="High" />
              <Bar dataKey="MEDIUM" fill="#C8973B" stackId="a" name="Medium" />
              <Bar dataKey="LOW" fill="#5B7A6B" stackId="a" name="Low" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 2. Triggered Laundering Reason Codes Frequency */}
      <div className="bg-[#131B2E] border border-[#1F2A44] rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-[#E8E6DE] font-sans">
            Triggered Laundering Reason Codes Frequency
          </h3>
          <span className="text-[10px] font-mono text-[#E8A3A3] bg-[#8B2E2E]/15 border border-[#8B2E2E]/30 px-2 py-0.5 rounded">
            TYPOLOGIES
          </span>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={reasonCodes.slice(0, 7)}
              layout="vertical"
              margin={{ top: 5, right: 20, left: 60, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2A44" horizontal={false} />
              <XAxis type="number" stroke="#64748B" tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }} />
              <YAxis
                type="category"
                dataKey="reason_code"
                stroke="#64748B"
                tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }}
              />
              <Tooltip content={customTooltip} />
              <Bar dataKey="count" fill="#C8973B" radius={[0, 4, 4, 0]} name="Triggers" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 3. Top Geographic Jurisdictions (GeoIP Origin) */}
      <div className="bg-[#131B2E] border border-[#1F2A44] rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-[#E8E6DE] font-sans">
            Top Geographic Jurisdictions (GeoIP Origin)
          </h3>
          <span className="text-[10px] font-mono text-[#A6C2DE] bg-[#3E5C76]/20 border border-[#3E5C76]/40 px-2 py-0.5 rounded">
            ASN / GEOIP
          </span>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={jurisdictions}
              layout="vertical"
              margin={{ top: 5, right: 20, left: 40, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2A44" horizontal={false} />
              <XAxis type="number" stroke="#64748B" tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }} />
              <YAxis
                type="category"
                dataKey="country"
                stroke="#64748B"
                tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }}
              />
              <Tooltip content={customTooltip} />
              <Bar dataKey="entities" fill="#3E5C76" radius={[0, 4, 4, 0]} name="Entities" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 4. Flagged Transaction Volume Over Time */}
      <div className="bg-[#131B2E] border border-[#1F2A44] rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-[#E8E6DE] font-sans">
            Flagged Transaction Volume Over Time
          </h3>
          <span className="text-[10px] font-mono text-[#B9CDC0] bg-[#5B7A6B]/20 border border-[#5B7A6B]/40 px-2 py-0.5 rounded">
            TIMELINE
          </span>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={volumeTimeline} margin={{ top: 10, right: 10, left: -10, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2A44" vertical={false} />
              <XAxis
                dataKey="display_date"
                stroke="#64748B"
                tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }}
              />
              <YAxis
                stroke="#64748B"
                tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }}
                unit=" ₿"
              />
              <Tooltip content={customTooltip} />
              <Line
                type="monotone"
                dataKey="volume"
                stroke="#C8973B"
                strokeWidth={2}
                dot={{ fill: "#C8973B", r: 3 }}
                name="Volume (BTC)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
