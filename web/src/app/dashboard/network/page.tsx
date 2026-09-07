import React from "react";
import { fetchApi } from "@/lib/api";
import NetworkGraphView from "@/components/NetworkGraphView";

interface NetworkResponse {
  scope: string;
  selected_wallet: string;
  node_count: number;
  edge_count: number;
  nodes: any[];
  links: any[];
  legend: any[];
}

export default async function NetworkPage() {
  let initialData: NetworkResponse = {
    scope: "top30",
    selected_wallet: "",
    node_count: 0,
    edge_count: 0,
    nodes: [],
    links: [],
    legend: [],
  };

  try {
    initialData = await fetchApi<NetworkResponse>("/api/network?scope=top30");
  } catch (err) {
    console.error("Failed to load initial network graph:", err);
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

      <NetworkGraphView initialData={initialData} />
    </div>
  );
}
