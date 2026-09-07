import { notFound } from "next/navigation";
import { fetchApi } from "@/lib/api";
import CaseDetailView from "@/components/CaseDetailView";
import type { NetworkData } from "@/components/NetworkGraphView";

export const dynamic = "force-dynamic";

interface CaseDetailResponse {
  wallet_address: string;
  composite_risk_score: number;
  risk_band: string;
  confidence_score: number;
  cluster_id: string;
  dominant_country: string;
  dominant_asn: string;
  dominant_ip: string;
  total_received_amount: number;
  total_sent_amount: number;
  reason_codes: string;
  ground_truth_label: string;
  plain_language_explanation: string;
  top_features: Array<{
    feature: string;
    display_name: string;
    value: number;
    shap_value: number;
  }>;
  cluster_info: {
    cluster_id: string;
    member_wallets: string[];
    heuristic_reasons: string[];
    clustering_confidence: number;
    investigative_rationale: string;
    total_members: number;
  };
  narrative_text: string;
}

interface AlertsResponse {
  entities: Array<{ wallet_address: string }>;
}

export default async function CaseDetailPage({
  params,
}: {
  params: { wallet: string };
}) {
  const walletAddress = decodeURIComponent(params.wallet);

  let caseData: CaseDetailResponse | null = null;
  let networkData: NetworkData | null = null;
  let topWallets: string[] = [];

  try {
    const [caseRes, alertsRes, netRes] = await Promise.all([
      fetchApi<CaseDetailResponse>(`/api/cases/${encodeURIComponent(walletAddress)}`),
      fetchApi<AlertsResponse>("/api/alerts?limit=50"),
      fetchApi<NetworkData>(`/api/network?scope=ego&wallet=${encodeURIComponent(walletAddress)}`).catch(() => null),
    ]);
    caseData = caseRes;
    networkData = netRes;
    topWallets = alertsRes.entities.map((e) => e.wallet_address);
    if (!topWallets.includes(walletAddress)) {
      topWallets = [walletAddress, ...topWallets];
    }
  } catch (err) {
    console.error("Error fetching case detail:", err);
  }

  if (!caseData) {
    notFound();
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold font-serif text-white mb-1">
          Forensic Case Detail & Investigative Evidence Dossier
        </h2>
        <div className="text-xs text-[#94A3B8] font-mono">
          Target Entity: <span className="text-[#C8973B] font-bold">{caseData.wallet_address}</span>
        </div>
      </div>

      <CaseDetailView caseData={caseData} topWallets={topWallets} networkData={networkData} />
    </div>
  );
}
