"use client";

import Link from "next/link";
import type { OverviewData } from "./useHeroData";

export default function FlaggedVolumeCard({ overview }: { overview: OverviewData | null }) {
  const kpis = overview?.kpis;
  const bandCounts = kpis
    ? [
        { band: "CRITICAL", count: kpis.critical_count, color: "#8B2E2E" },
        { band: "HIGH", count: kpis.high_count, color: "#B8562E" },
        { band: "MEDIUM", count: kpis.medium_count, color: "#C8973B" },
      ]
    : [];
  const bandTotal = bandCounts.reduce((s, b) => s + b.count, 0) || 1;

  return (
    <div className="bento-card p-5 flex flex-col gap-4 h-full sm:col-span-2">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-mono text-[#94A3B8] uppercase tracking-wider">Flagged volume</span>
        <Link href="/dashboard/alerts" className="text-[10px] font-mono text-[#C8973B] hover:underline">
          View Alert Queue →
        </Link>
      </div>
      <span className="text-3xl font-bold text-[#E8E6DE]">
        {kpis ? `${kpis.flagged_volume_btc.toLocaleString()} ₿` : "—"}
      </span>
      <div className="flex h-2 w-full overflow-hidden rounded-full bg-[#0B1220]">
        {bandCounts.map((b) => (
          <div key={b.band} style={{ width: `${(b.count / bandTotal) * 100}%`, backgroundColor: b.color }} />
        ))}
      </div>
      <div className="flex gap-4 text-[10px] font-mono text-[#94A3B8]">
        {bandCounts.map((b) => (
          <span key={b.band} className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: b.color }} />
            {b.band} · {b.count}
          </span>
        ))}
      </div>
    </div>
  );
}
