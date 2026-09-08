import type { OverviewData } from "./useHeroData";

function computeMeanScore(histogram: OverviewData["histogram"]): number | null {
  let weightedSum = 0;
  let totalCount = 0;
  for (const bin of histogram) {
    const midpoint = (bin.min + bin.max) / 2;
    weightedSum += midpoint * bin.total;
    totalCount += bin.total;
  }
  return totalCount > 0 ? weightedSum / totalCount : null;
}

export default function RiskGaugeCard({ overview }: { overview: OverviewData | null }) {
  const mean = overview ? computeMeanScore(overview.histogram) : null;
  const pct = mean !== null ? Math.min(100, Math.max(0, mean)) : 0;
  // semicircle gauge: 180deg sweep, needle angle from -90deg (left/0) to +90deg (right/100)
  const rad = ((-90 + (pct / 100) * 180) * Math.PI) / 180;
  const x2 = 60 + 40 * Math.sin(rad);
  const y2 = 60 - 40 * Math.cos(rad);

  return (
    <div className="bento-card p-4 flex flex-col items-center gap-1 h-full justify-center">
      <span className="text-[11px] font-mono text-[#94A3B8] uppercase tracking-wider self-start">
        System risk index
      </span>
      <svg viewBox="0 0 120 70" className="w-28">
        <path d="M 10 60 A 50 50 0 0 1 110 60" fill="none" stroke="#1F2A44" strokeWidth="8" strokeLinecap="round" />
        <path
          d="M 10 60 A 50 50 0 0 1 110 60"
          fill="none"
          stroke="#C8973B"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${(pct / 100) * 157} 157`}
        />
        <line
          x1="60"
          y1="60"
          x2={x2}
          y2={y2}
          stroke="#E8E6DE"
          strokeWidth="2"
        />
      </svg>
      <span className="text-lg font-semibold text-[#E8E6DE]">
        {mean !== null ? mean.toFixed(1) : "—"}
      </span>
      <span className="text-[10px] text-[#64748B]">mean composite score, live</span>
    </div>
  );
}
