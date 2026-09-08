import type { OverviewData } from "./useHeroData";

export default function CriticalAlertsCard({ overview }: { overview: OverviewData | null }) {
  const count = overview?.kpis.critical_count ?? null;
  return (
    <div
      className="bento-card p-5 flex flex-col justify-between h-full row-span-2"
      style={{ boxShadow: count && count > 0 ? "0 0 40px -12px rgba(139,46,46,0.5)" : undefined, borderColor: "#8B2E2E55" }}
    >
      <span className="text-[11px] font-mono text-[#94A3B8] uppercase tracking-wider">Critical alerts</span>
      <div className="flex flex-col gap-1">
        <span className="text-5xl font-bold" style={{ color: "#E8A3A3" }}>
          {count !== null ? count : "—"}
        </span>
        <span className="text-xs text-[#64748B]">entities at immediate-review threshold</span>
      </div>
      <div className="flex items-center gap-1 text-[10px] font-mono text-[#8B2E2E]">
        <span className="w-1.5 h-1.5 rounded-full bg-[#8B2E2E] animate-pulse" />
        LIVE — /api/overview
      </div>
    </div>
  );
}
