"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";

export default function QuickLookupCard() {
  const [wallet, setWallet] = useState("");
  const router = useRouter();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (wallet.trim()) router.push(`/dashboard/cases/${encodeURIComponent(wallet.trim())}`);
  }

  return (
    <form onSubmit={handleSubmit} className="bento-card p-4 flex flex-col gap-2 h-full">
      <span className="text-[11px] font-mono text-[#94A3B8] uppercase tracking-wider">Quick lookup</span>
      <input
        value={wallet}
        onChange={(e) => setWallet(e.target.value)}
        placeholder="Paste a wallet address…"
        className="bg-[#0B1220] border border-[#1F2A44] rounded-lg px-3 py-2 text-xs text-[#E8E6DE] placeholder-[#64748B] focus:outline-none focus:border-[#C8973B]/50"
      />
      <button
        type="submit"
        className="mt-auto flex items-center justify-center gap-1 rounded-lg bg-[#C8973B]/15 border border-[#C8973B]/40 text-[#E8CE9E] text-xs font-semibold py-2 hover:bg-[#C8973B]/25 transition-colors"
      >
        View Case <ArrowRight className="w-3 h-3" />
      </button>
    </form>
  );
}
