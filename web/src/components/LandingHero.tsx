"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Shield, Terminal, Cpu, Database, ChevronDown } from "lucide-react";
import BentoGrid from "./hero/BentoGrid";

export default function LandingHero() {
  const [query, setQuery] = useState("");
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/dashboard/alerts?search=${encodeURIComponent(query.trim())}`);
    } else {
      router.push("/dashboard/alerts");
    }
  };

  return (
    <section className="hero-gradient-frame relative overflow-hidden pt-8 pb-16 px-6 sm:px-12 lg:px-20 max-w-7xl mx-auto rounded-2xl">
      {/* Background Anamorphic Flare & Grid */}
      <div className="absolute top-0 right-0 w-[600px] h-[500px] bg-[radial-gradient(ellipse_60%_50%_at_80%_20%,rgba(200,151,59,0.22),rgba(139,46,46,0.06)_50%,transparent_80%)] pointer-events-none" />
      <div className="absolute top-48 left-10 text-[180px] font-black text-white/[0.02] select-none pointer-events-none font-sans leading-none">
        NTRO
      </div>

      {/* Top Navigation */}
      <nav className="relative z-10 flex items-center justify-between pb-8 mb-12 border-b border-white/[0.08]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-gradient-to-br from-[#C8973B] to-[#8B2E2E] flex items-center justify-center text-white font-bold text-sm shadow-[0_0_16px_rgba(200,151,59,0.4)]">
            ⚖️
          </div>
          <span className="font-mono text-sm font-bold tracking-widest text-[#E8E6DE]">
            NTRO // NROK FORENSIC
          </span>
        </div>

        <div className="hidden md:flex items-center gap-8 text-xs font-medium text-[#94A3B8]">
          <Link href="/dashboard" className="hover:text-[#C8973B] transition-colors">
            Tripartite Engine
          </Link>
          <Link href="/dashboard/network" className="hover:text-[#C8973B] transition-colors">
            Entity Clustering
          </Link>
          <Link href="/dashboard/alerts" className="hover:text-[#C8973B] transition-colors">
            SAR Generator
          </Link>
          <Link href="/dashboard/models" className="hover:text-[#C8973B] transition-colors">
            PyOD Benchmarks
          </Link>
        </div>

        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#C8973B]/15 border border-[#C8973B]/40 text-[#E8CE9E] font-mono text-xs font-semibold hover:bg-[#C8973B]/25 hover:border-[#C8973B] transition-all shadow-[0_0_12px_rgba(200,151,59,0.2)]"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#C8973B] animate-ping" />
          ENTER TERMINAL
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </nav>

      {/* Centered hero copy — matches the reference's stacked composition */}
      <div className="relative z-10 flex flex-col items-center text-center max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-3 mb-6">
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#C8973B]/10 border border-[#C8973B]/25 text-[#C8973B] font-mono text-[11px] font-semibold tracking-wider">
            <span className="w-1.5 h-1.5 rounded-full bg-[#C8973B]" />
            ✦ NEW • PEEL-CHAIN DETECTION LIVE
          </span>
          <Link
            href="/dashboard/evaluation"
            className="inline-flex items-center gap-1 px-3 py-1 rounded-full border border-white/10 text-[#94A3B8] font-mono text-[11px] hover:text-[#E8E6DE] transition-colors"
          >
            Explore Evaluation <ChevronDown className="w-3 h-3" />
          </Link>
        </div>

        <h1 className="font-sans tracking-tight leading-[1.08] mb-6">
          <span className="block text-3xl sm:text-4xl lg:text-5xl font-light text-[#E8E6DE]">
            Trace the money.
          </span>
          <span className="block text-3xl sm:text-4xl lg:text-5xl font-light text-[#E8E6DE]">
            Expose the
          </span>
          <span className="block text-4xl sm:text-5xl lg:text-6xl font-bold bg-gradient-to-r from-[#C8973B] to-[#E8A34A] bg-clip-text text-transparent">
            pattern.
          </span>
        </h1>

        <p className="text-base text-[#94A3B8] leading-relaxed max-w-xl mb-8">
          Protect sovereign financial infrastructure and trace adversarial Bitcoin laundering flows
          with air-gapped, offline AI — fusing blockchain UTXOs and network broadcast telemetry into
          court-admissible evidence.
        </p>

        <div className="flex items-center gap-3 mb-6">
          <Link
            href="/dashboard"
            className="px-6 py-2.5 rounded-full border border-white/15 text-sm font-semibold text-[#E8E6DE] hover:bg-white/5 transition-colors"
          >
            Learn More
          </Link>
          <Link
            href="/dashboard/alerts"
            className="px-6 py-2.5 rounded-full bg-gradient-to-r from-[#C8973B] to-[#DDAE55] text-[#05070B] text-sm font-bold shadow-[0_0_20px_rgba(200,151,59,0.4)] hover:shadow-[0_0_28px_rgba(200,151,59,0.6)] transition-shadow"
          >
            Get Started
          </Link>
        </div>

        {/* Interactive Search Bar */}
        <form onSubmit={handleSearch} className="w-full max-w-lg mb-4">
          <div className="relative flex items-center bg-[#0E1420]/80 backdrop-blur-xl border border-white/10 rounded-xl p-2 pl-4 shadow-[0_12px_32px_rgba(0,0,0,0.6)] focus-within:border-[#C8973B]/50 focus-within:shadow-[0_0_20px_rgba(200,151,59,0.2)] transition-all">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search target wallet, transaction ID, or entity cluster..."
              className="w-full bg-transparent text-sm text-[#E8E6DE] placeholder-[#64748B] focus:outline-none"
            />
            <button
              type="submit"
              className="w-9 h-9 rounded-lg bg-[#C8973B] text-[#05070B] flex items-center justify-center font-bold hover:bg-[#DDAE55] transition-all shadow-[0_0_12px_rgba(200,151,59,0.4)] ml-2 flex-shrink-0"
            >
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </form>
        <div className="text-[11px] font-mono text-[#64748B] flex items-center gap-4 flex-wrap justify-center">
          <span>● 100% Offline Air-Gapped</span>
          <span>● Zero Network Calls</span>
          <span>● Seed 42 Deterministic</span>
        </div>
      </div>

      {/* Live bento grid — every card fetches real data from the FastAPI backend */}
      <BentoGrid />

      {/* Agency Partner Trust Ribbon */}
      <div className="relative z-10 mt-4 pt-6 pb-6 border-t border-b border-white/[0.08] flex flex-wrap items-center justify-between gap-6 text-xs text-[#94A3B8]">
        <span className="font-mono uppercase text-[10px] tracking-widest text-[#64748B]">
          Deployment Agencies:
        </span>
        <div className="flex items-center gap-2 font-medium">
          <Shield className="w-4 h-4 text-[#C8973B]" /> NTRO Command
        </div>
        <div className="flex items-center gap-2 font-medium">
          <Terminal className="w-4 h-4 text-[#5B7A6B]" /> FIU-IND Reference
        </div>
        <div className="flex items-center gap-2 font-medium">
          <Cpu className="w-4 h-4 text-[#3E5C76]" /> CERT-In Telemetry
        </div>
        <div className="flex items-center gap-2 font-medium">
          <Database className="w-4 h-4 text-[#B8562E]" /> PMLA Enforcement
        </div>
        <div className="flex items-center gap-2 font-medium">
          <span>🔒</span> Air-Gapped AirDrop
        </div>
      </div>
    </section>
  );
}
