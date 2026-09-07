import { fetchApi } from "@/lib/api";
import ModelInsightsView from "@/components/ModelInsightsView";

export const dynamic = "force-dynamic";

export default async function ModelsPage() {
  let data = null;
  try {
    data = await fetchApi<any>("/api/models");
  } catch (err) {
    console.error("Failed to load model insights:", err);
  }

  if (!data) {
    return (
      <div className="p-6 rounded-lg bg-red-900/20 border border-red-500/40 text-red-200 font-mono text-sm">
        ⚠️ Unable to fetch model insights from backend API.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold font-serif text-white mb-1">
          Model Insights & Benchmark Evaluation
        </h2>
        <div className="text-xs text-[#94A3B8]">
          Inspection of unsupervised anomaly detectors, cross-model agreement, and PyOD baseline benchmark.
        </div>
      </div>

      <ModelInsightsView data={data} />
    </div>
  );
}
