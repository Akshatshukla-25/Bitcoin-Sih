import React, { Suspense } from "react";
import SidebarFilters from "@/components/SidebarFilters";
import TabNavigation from "@/components/TabNavigation";
import { fetchApi } from "@/lib/api";

export const dynamic = "force-dynamic";

interface AlertsResponse {
  available_countries: string[];
}

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  let countries = ["ALL"];
  try {
    const alertsData = await fetchApi<AlertsResponse>("/api/alerts?limit=1");
    if (alertsData && alertsData.available_countries) {
      countries = alertsData.available_countries;
    }
  } catch (err) {
    console.error("Failed to load initial filter countries:", err);
  }

  return (
    <div className="flex flex-col md:flex-row min-h-screen bg-[#05070B] text-[#E8E6DE]">
      {/* Sidebar Filters */}
      <Suspense fallback={<div className="w-64 bg-[#0B1220] p-5">Loading filters...</div>}>
        <SidebarFilters availableCountries={countries} />
      </Suspense>

      {/* Main Forensic Dossier Stage */}
      <main className="flex-1 p-6 md:p-8 lg:p-10 overflow-y-auto max-w-7xl">
        {/* Classification Header */}
        <div className="mb-6">
          <div className="inline-block px-2.5 py-1 rounded bg-[#C8973B]/10 border border-[#C8973B]/30 text-[#C8973B] font-mono text-[11px] font-bold tracking-widest uppercase mb-2">
            NTRO INTERNAL — SIH26146 CASE FILE
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold font-serif tracking-tight text-white mb-1">
            Bitcoin Transaction Traffic & Laundering Detection System
          </h1>
          <div className="text-xs text-[#94A3B8] font-sans">
            National Technical Research Organisation (NTRO) • Problem Statement SIH26146 • Air-Gapped Forensic Instrument
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8">
          <Suspense fallback={<div className="h-8 border-b border-[#1F2A44]" />}>
            <TabNavigation />
          </Suspense>
        </div>

        {/* Tab View Content */}
        {children}
      </main>
    </div>
  );
}
