import type { ModelDistribution } from "./useHeroData";

export default function ModelEnsembleCard({ distributions }: { distributions: ModelDistribution[] }) {
  return (
    <div className="bento-card p-4 flex flex-col gap-3 h-full">
      <span className="text-[11px] font-mono text-[#94A3B8] uppercase tracking-wider">Model ensemble — mean score</span>
      <div className="flex flex-col gap-2">
        {distributions.length === 0 && <span className="text-xs text-[#64748B]">Loading…</span>}
        {distributions.map((d) => (
          <div key={d.model_key} className="flex items-center gap-2">
            <span className="w-28 shrink-0 text-[11px] text-[#94A3B8]">{d.model_name}</span>
            <div className="h-1.5 flex-1 rounded-full bg-[#0B1220] overflow-hidden">
              <div className="h-full rounded-full" style={{ width: `${d.mean * 100}%`, backgroundColor: d.color }} />
            </div>
            <span className="w-10 text-right text-[11px] font-mono text-[#E8E6DE]">{d.mean.toFixed(2)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
