"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";

export default function SearchCard() {
  const [query, setQuery] = useState("");
  const router = useRouter();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    router.push(query.trim() ? `/dashboard/alerts?search=${encodeURIComponent(query.trim())}` : "/dashboard/alerts");
  }

  return (
    <form onSubmit={handleSubmit} className="bento-card p-4 flex flex-col gap-3 h-full">
      <span className="text-[11px] font-mono text-[#94A3B8] uppercase tracking-wider">Search entities</span>
      <div className="flex items-center gap-2 bg-[#0B1220] border border-[#1F2A44] rounded-lg px-3 py-2">
        <Search className="w-3.5 h-3.5 text-[#64748B] shrink-0" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Wallet or cluster ID…"
          className="w-full bg-transparent text-xs text-[#E8E6DE] placeholder-[#64748B] focus:outline-none"
        />
      </div>
    </form>
  );
}
