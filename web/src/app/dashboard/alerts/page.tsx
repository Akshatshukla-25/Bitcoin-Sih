import React from "react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import AlertQueueTable from "@/components/AlertQueueTable";

interface AlertsData {
  total_matching: number;
  limit: number;
  offset: number;
  entities: Array<{
    wallet_address: string;
    composite_risk_score: number;
    risk_band: string;
    confidence_score: number;
    cluster_id: string;
    dominant_country: string;
    dominant_asn: string;
    total_received_amount: number;
    reason_codes: string;
  }>;
}

export default async function AlertsPage({
  searchParams,
}: {
  searchParams: { [key: string]: string | string[] | undefined };
}) {
  const bands = typeof searchParams.bands === "string" ? searchParams.bands : "CRITICAL,HIGH,MEDIUM";
  const minScore = typeof searchParams.min_score === "string" ? searchParams.min_score : "35";
  const country = typeof searchParams.country === "string" ? searchParams.country : "ALL";
  const search = typeof searchParams.search === "string" ? searchParams.search : "";

  const queryParams = new URLSearchParams();
  if (bands) queryParams.set("bands", bands);
  if (minScore) queryParams.set("min_score", minScore);
  if (country && country !== "ALL") queryParams.set("country", country);
  if (search) queryParams.set("search", search);
  queryParams.set("limit", "200");

  let data: AlertsData | null = null;
  let errorMsg = "";

  try {
    data = await fetchApi<AlertsData>(`/api/alerts?${queryParams.toString()}`);
  } catch (err: any) {
    errorMsg = err.message || "Failed to load alerts";
  }

  if (!data) {
    return (
      <div className="p-6 rounded-lg bg-red-900/20 border border-red-500/40 text-red-200 font-mono text-sm">
        ⚠️ {errorMsg || "Unable to fetch alert queue"}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold font-serif text-white mb-1">
          Alert Queue
        </h2>
        <div className="text-xs text-[#94A3B8]">
          Showing <b className="text-[#C8973B] font-mono">{data.total_matching}</b> suspicious entities matching active filters.
        </div>
      </div>

      <AlertQueueTable entities={data.entities} totalMatching={data.total_matching} />
    </div>
  );
}
