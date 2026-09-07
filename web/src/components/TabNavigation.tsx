"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

export default function TabNavigation() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const queryString = searchParams.toString() ? `?${searchParams.toString()}` : "";

  let activeWallet = searchParams.get("wallet") || "";
  if (!activeWallet && pathname.startsWith("/dashboard/cases/")) {
    const parts = pathname.split("/dashboard/cases/");
    if (parts.length > 1 && parts[1]) {
      activeWallet = decodeURIComponent(parts[1].split("/")[0]);
    }
  }

  const networkHref = activeWallet
    ? `/dashboard/network?scope=ego&wallet=${encodeURIComponent(activeWallet)}`
    : "/dashboard/network";

  const caseDetailHref = activeWallet
    ? `/dashboard/cases/${encodeURIComponent(activeWallet)}`
    : "/dashboard/cases";

  const tabs = [
    { label: "1. Overview", href: "/dashboard" },
    { label: "2. Alert Queue", href: "/dashboard/alerts" },
    { label: "3. Case Detail", href: caseDetailHref, matchPrefix: "/dashboard/cases" },
    { label: "4. Network", href: networkHref, matchPrefix: "/dashboard/network" },
    { label: "5. Model Insights", href: "/dashboard/models" },
    { label: "6. Evaluation", href: "/dashboard/evaluation" },
  ];

  const isTabActive = (item: { href: string; matchPrefix?: string }) => {
    if (item.matchPrefix) {
      return pathname.startsWith(item.matchPrefix);
    }
    if (item.href === "/dashboard") {
      return pathname === "/dashboard";
    }
    return pathname.startsWith(item.href);
  };

  return (
    <div className="flex items-center gap-6 border-b border-[#1F2A44] overflow-x-auto">
      {tabs.map((tab) => {
        const active = isTabActive(tab);
        return (
          <Link
            key={tab.href}
            href={`${tab.href}${queryString}`}
            className={`text-xs font-mono font-medium pb-3 border-b-2 whitespace-nowrap transition-all ${
              active
                ? "border-[#C8973B] text-[#C8973B] font-bold"
                : "border-transparent text-[#94A3B8] hover:text-[#E8E6DE]"
            }`}
          >
            {tab.label}
          </Link>
        );
      })}
    </div>
  );
}
