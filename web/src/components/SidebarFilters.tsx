"use client";

import React, { useState, useEffect } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { Filter, Search, Globe, ShieldAlert, Sliders } from "lucide-react";

interface SidebarFiltersProps {
  availableCountries?: string[];
}

export default function SidebarFilters({ availableCountries = ["ALL"] }: SidebarFiltersProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Read current query params with sensible defaults
  const currentBands = searchParams.get("bands") || "CRITICAL,HIGH,MEDIUM";
  const currentMinScore = searchParams.get("min_score") || "35";
  const currentCountry = searchParams.get("country") || "ALL";
  const currentSearch = searchParams.get("search") || "";

  const [bands, setBands] = useState<string[]>(
    currentBands ? currentBands.split(",") : ["CRITICAL", "HIGH", "MEDIUM"]
  );
  const [minScore, setMinScore] = useState<number>(Number(currentMinScore) || 35);
  const [country, setCountry] = useState<string>(currentCountry);
  const [search, setSearch] = useState<string>(currentSearch);

  // Sync state when URL params change
  useEffect(() => {
    if (currentBands) setBands(currentBands.split(","));
    if (currentMinScore) setMinScore(Number(currentMinScore));
    if (currentCountry) setCountry(currentCountry);
    if (currentSearch !== undefined) setSearch(currentSearch);
  }, [currentBands, currentMinScore, currentCountry, currentSearch]);

  const updateFilters = (newBands: string[], newScore: number, newCountry: string, newSearch: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (newBands.length > 0) {
      params.set("bands", newBands.join(","));
    } else {
      params.delete("bands");
    }
    params.set("min_score", newScore.toString());
    if (newCountry && newCountry !== "ALL") {
      params.set("country", newCountry);
    } else {
      params.delete("country");
    }
    if (newSearch && newSearch.trim()) {
      params.set("search", newSearch.trim());
    } else {
      params.delete("search");
    }
    router.push(`${pathname}?${params.toString()}`);
  };

  const toggleBand = (b: string) => {
    let next: string[];
    if (bands.includes(b)) {
      next = bands.filter((x) => x !== b);
    } else {
      next = [...bands, b];
    }
    setBands(next);
    updateFilters(next, minScore, country, search);
  };

  const handleScoreChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    setMinScore(val);
  };

  const handleScoreCommit = () => {
    updateFilters(bands, minScore, country, search);
  };

  const handleCountryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setCountry(val);
    updateFilters(bands, minScore, val, search);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateFilters(bands, minScore, country, search);
  };

  const allBands = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];

  return (
    <aside className="w-full md:w-64 bg-[#0B1220] border-r border-[#1F2A44] p-5 flex flex-col gap-6 text-[#E8E6DE]">
      <div>
        <div className="font-mono text-xs font-bold tracking-widest text-[#C8973B] uppercase border-l-2 border-[#C8973B] pl-2 mb-1">
          NTRO // FORENSIC MONITOR
        </div>
        <div className="text-[11px] text-[#94A3B8]">
          SIH26146 • Tripartite Bitcoin AML Engine
        </div>
      </div>

      <div className="h-px bg-[#1F2A44]" />

      {/* Risk Bands Filter */}
      <div>
        <label className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#94A3B8] flex items-center gap-1.5 mb-2.5">
          <ShieldAlert className="w-3.5 h-3.5 text-[#C8973B]" /> RISK BANDS
        </label>
        <div className="flex flex-col gap-1.5">
          {allBands.map((b) => {
            const active = bands.includes(b);
            let badgeClass = "border-white/10 text-[#94A3B8]";
            if (active) {
              if (b === "CRITICAL") badgeClass = "bg-[#8B2E2E]/30 border-[#8B2E2E] text-[#E8A3A3]";
              else if (b === "HIGH") badgeClass = "bg-[#B8562E]/30 border-[#B8562E] text-[#E8B896]";
              else if (b === "MEDIUM") badgeClass = "bg-[#C8973B]/30 border-[#C8973B] text-[#E8CE9E]";
              else if (b === "LOW") badgeClass = "bg-[#5B7A6B]/30 border-[#5B7A6B] text-[#B9CDC0]";
            }
            return (
              <button
                key={b}
                onClick={() => toggleBand(b)}
                className={`text-xs font-mono font-medium py-1.5 px-3 rounded border text-left flex items-center justify-between transition-all ${badgeClass}`}
              >
                <span>{b}</span>
                <span className="text-[10px]">{active ? "✓" : "+"}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Minimum Risk Score Slider */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <label className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#94A3B8] flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-[#C8973B]" /> MIN RISK SCORE
          </label>
          <span className="font-mono text-xs font-bold text-[#C8973B]">
            {minScore.toFixed(1)}
          </span>
        </div>
        <input
          type="range"
          min="0"
          max="100"
          step="5"
          value={minScore}
          onChange={handleScoreChange}
          onMouseUp={handleScoreCommit}
          onTouchEnd={handleScoreCommit}
          className="w-full accent-[#C8973B] bg-[#131B2E] cursor-pointer"
        />
        <div className="flex justify-between text-[10px] font-mono text-[#64748B] mt-1">
          <span>0.0</span>
          <span>50.0</span>
          <span>100.0</span>
        </div>
      </div>

      {/* Geographic Jurisdiction Select */}
      <div>
        <label className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#94A3B8] flex items-center gap-1.5 mb-1.5">
          <Globe className="w-3.5 h-3.5 text-[#C8973B]" /> GEOGRAPHIC JURISDICTION
        </label>
        <select
          value={country}
          onChange={handleCountryChange}
          className="w-full bg-[#131B2E] border border-[#1F2A44] rounded px-3 py-1.5 text-xs text-[#E8E6DE] focus:outline-none focus:border-[#C8973B]"
        >
          <option value="ALL">ALL (Global Surveillance)</option>
          {availableCountries.filter((c) => c !== "ALL").map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {/* Search Wallet / Cluster ID */}
      <div>
        <label className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#94A3B8] flex items-center gap-1.5 mb-1.5">
          <Search className="w-3.5 h-3.5 text-[#C8973B]" /> SEARCH TARGET WALLET
        </label>
        <form onSubmit={handleSearchSubmit}>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="bc1q... or CLUSTER_0001"
            className="w-full bg-[#131B2E] border border-[#1F2A44] rounded px-3 py-1.5 text-xs font-mono text-[#E8E6DE] placeholder-[#64748B] focus:outline-none focus:border-[#C8973B]"
          />
        </form>
      </div>

      <div className="mt-auto pt-4 border-t border-[#1F2A44] text-[10px] font-mono text-[#64748B] leading-relaxed">
        <div>AIR-GAPPED SYSTEM</div>
        <div>STRICT PURE PYTHON BACKEND</div>
      </div>
    </aside>
  );
}
