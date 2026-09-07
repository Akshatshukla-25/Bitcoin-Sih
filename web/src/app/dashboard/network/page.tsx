import React from "react";
import { fetchApi } from "@/lib/api";
import NetworkGraphView, { NetworkData } from "@/components/NetworkGraphView";

export const dynamic = "force-dynamic";


interface NetworkPageProps {
  searchParams?: {
    scope?: string;
    wallet?: string;
  };
}

export default async function NetworkPage({ searchParams }: NetworkPageProps) {
  const scope = searchParams?.scope === "ego" ? "ego" : "top30";
  const wallet = searchParams?.wallet || "";

  let initialData: NetworkData = {
    scope,
    selected_wallet: wallet || null,
    node_count: 0,
    edge_count: 0,
    nodes: [],
    links: [],
    legend: [],
  };

  let initialError: string | null = null;
  try {
    const endpoint =
      scope === "ego" && wallet
        ? `/api/network?scope=ego&wallet=${encodeURIComponent(wallet)}`
        : `/api/network?scope=top30`;
    initialData = await fetchApi<NetworkData>(endpoint);
  } catch (err) {
    initialError = err instanceof Error ? err.message : "Unable to load network graph.";
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold font-serif text-white mb-1">
          Tripartite Network Graph
        </h2>
        <div className="text-xs text-[#94A3B8]">
          Interactive graph visualization fusing Wallets, Transactions, and Broadcast/Relay IP Nodes.
        </div>
      </div>

      <NetworkGraphView initialData={initialData} initialError={initialError} />
    </div>
  );
}
