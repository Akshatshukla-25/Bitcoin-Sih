import { fetchApi } from "@/lib/api";
import EvaluationView from "@/components/EvaluationView";

export const dynamic = "force-dynamic";

export default async function EvaluationPage() {
  let data = null;
  try {
    data = await fetchApi<any>("/api/evaluation");
  } catch (err) {
    console.error("Failed to load evaluation data:", err);
  }

  if (!data) {
    return (
      <div className="p-6 rounded-lg bg-red-900/20 border border-red-500/40 text-red-200 font-mono text-sm">
        ⚠️ Unable to fetch evaluation metrics from backend API.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold font-serif text-white mb-1">
          Forensic Model Evaluation & Operational Scorecard
        </h2>
        <div className="text-xs text-[#94A3B8]">
          Empirical scorecard against synthetic ground truth across operational triage policies.
        </div>
      </div>

      <EvaluationView data={data} />
    </div>
  );
}
