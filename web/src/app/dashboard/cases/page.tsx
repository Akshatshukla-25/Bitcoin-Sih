import { redirect } from "next/navigation";
import { fetchApi } from "@/lib/api";

export const dynamic = "force-dynamic";

interface AlertsResponse {
  entities: Array<{ wallet_address: string }>;
}

export default async function CasesIndexPage() {
  let defaultWallet = "bc1qf44prawa4n3m6eevc28425279y0zme45pv99g5";
  try {
    const res = await fetchApi<AlertsResponse>("/api/alerts?limit=1");
    if (res.entities.length > 0) {
      defaultWallet = res.entities[0].wallet_address;
    }
  } catch (e) {
    console.error("Could not fetch top alert wallet:", e);
  }

  redirect(`/dashboard/cases/${encodeURIComponent(defaultWallet)}`);
}
