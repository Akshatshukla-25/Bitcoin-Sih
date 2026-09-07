import Link from "next/link";
import { redirect } from "next/navigation";
import { fetchApi } from "@/lib/api";

export const dynamic = "force-dynamic";

interface AlertsResponse {
  entities: Array<{ wallet_address: string }>;
}

export default async function CasesIndexPage() {
  try {
    const response = await fetchApi<AlertsResponse>("/api/alerts?limit=1");
    const wallet = response.entities[0]?.wallet_address;
    if (wallet) {
      redirect(`/dashboard/cases/${encodeURIComponent(wallet)}`);
    }
  } catch {
    // Render an actionable state below; do not redirect to fabricated evidence.
  }

  return (
    <div role="alert" className="p-6 rounded-lg bg-[#131B2E] border border-[#1F2A44] text-[#E8E6DE]">
      <h2 className="font-bold mb-2">No case is available</h2>
      <p className="text-sm text-[#94A3B8] mb-4">The alert API returned no wallet that can be opened. Verify pipeline artifacts and API readiness.</p>
      <Link className="text-[#C8973B] underline" href="/dashboard/alerts">Return to the alert queue</Link>
    </div>
  );
}
