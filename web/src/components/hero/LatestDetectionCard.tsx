"use client";

import Link from "next/link";
import type { TopAlert } from "./useHeroData";

const BAND_COLOR: Record<string, string> = {
  CRITICAL: "#8B2E2E",
  HIGH: "#B8562E",
  MEDIUM: "#C8973B",
  LOW: "#5B7A6B",
};

export default function LatestDetectionCard({
  topAlert,
  narrative,
}: {
  topAlert: TopAlert | null;
  narrative: string | null;
}) {
  return (
    <Link
      href={topAlert ? `/dashboard/cases/${topAlert.wallet_address}` : "/dashboard/alerts"}
      className="bento-card p-4 flex flex-col gap-2 h-full hover:border-[#C8973B]/40 transition-colors"
    >
      <span className="text-[11px] font-mono text-[#94A3B8] uppercase tracking-wider">Top flagged entity</span>
      {topAlert ? (
        <>
          <div className="flex items-center gap-2">
            <span
              className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded"
              style={{ backgroundColor: `${BAND_COLOR[topAlert.risk_band]}22`, color: BAND_COLOR[topAlert.risk_band] }}
            >
              {topAlert.risk_band} · {topAlert.composite_risk_score}
            </span>
            <span className="text-[10px] text-[#64748B] truncate font-mono">
              {topAlert.wallet_address.slice(0, 14)}…
            </span>
          </div>
          <p className="text-xs text-[#94A3B8] leading-relaxed line-clamp-2">
            {narrative ?? "Loading explanation…"}
          </p>
        </>
      ) : (
        <span className="text-xs text-[#64748B]">Loading…</span>
      )}
    </Link>
  );
}
