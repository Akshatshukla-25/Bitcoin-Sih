import type { EvaluationData } from "./useHeroData";

export default function RocAucCard({ evaluation }: { evaluation: EvaluationData | null }) {
  const roc = evaluation?.roc_curve;
  const points = roc?.points ?? [];

  const path =
    points.length > 1
      ? points
          .map((p, i) => `${i === 0 ? "M" : "L"} ${p.fpr * 100} ${100 - p.tpr * 100}`)
          .join(" ")
      : "";

  return (
    <div className="bento-card p-4 flex flex-col gap-2 h-full">
      <span className="text-[11px] font-mono text-[#94A3B8] uppercase tracking-wider">Ensemble ROC-AUC</span>
      <span className="text-3xl font-bold text-[#E8E6DE]">
        {roc?.auc !== null && roc?.auc !== undefined ? roc.auc.toFixed(3) : "—"}
      </span>
      {path && (
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="w-full h-10">
          <line x1="0" y1="100" x2="100" y2="0" stroke="#1F2A44" strokeWidth="1.5" strokeDasharray="3 3" />
          <path d={path} fill="none" stroke="#C8973B" strokeWidth="2.5" vectorEffect="non-scaling-stroke" />
        </svg>
      )}
      <span className="text-[10px] text-[#64748B]">real ROC curve, /api/evaluation</span>
    </div>
  );
}
