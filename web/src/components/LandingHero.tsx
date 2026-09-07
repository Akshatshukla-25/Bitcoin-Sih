"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Shield, Terminal, Cpu, Database } from "lucide-react";

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
    <section className="relative overflow-hidden pt-8 pb-16 px-6 sm:px-12 lg:px-20 max-w-7xl mx-auto">
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

      {/* Hero Body Grid */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        {/* Left Column: Headlines & Search */}
        <div className="lg:col-span-7">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#C8973B]/10 border border-[#C8973B]/25 text-[#C8973B] font-mono text-[11px] font-semibold tracking-wider mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-[#C8973B]" />
            ✦ NEW • AMPLIFY NATIONAL CRYPTO DEFENSE →
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold font-sans tracking-tight leading-[1.08] mb-6">
            Defense Against <br />
            <span className="bg-gradient-to-r from-white via-[#E8CE9E] to-[#C8973B] bg-clip-text text-transparent">
              Digital Threats
            </span>
          </h1>

          <p className="text-base text-[#94A3B8] leading-relaxed max-w-xl mb-8">
            Protect sovereign financial infrastructure and trace adversarial Bitcoin laundering flows with air-gapped, offline AI. Fusing blockchain UTXOs and network broadcast telemetry into court-admissible evidence.
          </p>

          {/* Interactive Search Bar */}
          <form onSubmit={handleSearch} className="max-w-lg mb-4">
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
          <div className="text-[11px] font-mono text-[#64748B] flex items-center gap-4">
            <span>● 100% Offline Air-Gapped</span>
            <span>● Zero Network Calls</span>
            <span>● Seed 42 Deterministic</span>
          </div>
        </div>

        {/* Right Column: 3D Isometric Holographic Security Tokens */}
        <div className="lg:col-span-5 flex justify-center items-center">
          <div className="relative w-full max-w-md aspect-square flex items-center justify-center">
            <svg
              viewBox="0 0 420 340"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="w-full h-auto drop-shadow-[0_20px_40px_rgba(0,0,0,0.9)]"
            >
              {/* Circuit Projection Rays */}
              <line x1="210" y1="20" x2="110" y2="150" stroke="rgba(200, 151, 59, 0.25)" strokeWidth="1.2" strokeDasharray="4 4" />
              <line x1="210" y1="20" x2="260" y2="140" stroke="rgba(200, 151, 59, 0.4)" strokeWidth="1.5" />
              <line x1="210" y1="20" x2="360" y2="160" stroke="rgba(200, 151, 59, 0.2)" strokeWidth="1.2" />
              <line x1="110" y1="150" x2="260" y2="280" stroke="rgba(200, 151, 59, 0.3)" strokeWidth="1.2" />
              <line x1="260" y1="140" x2="260" y2="280" stroke="rgba(200, 151, 59, 0.4)" strokeWidth="1.5" />
              <line x1="360" y1="160" x2="260" y2="280" stroke="rgba(200, 151, 59, 0.25)" strokeWidth="1.2" strokeDasharray="4 4" />

              {/* Ambient Golden Core */}
              <circle cx="260" cy="140" r="90" fill="url(#heroGoldAura)" opacity="0.4" />

              {/* Left Translucent Glass Node */}
              <g transform="translate(60, 90)">
                <polygon points="50,0 100,28 50,56 0,28" fill="rgba(30, 41, 59, 0.85)" stroke="rgba(255, 255, 255, 0.3)" strokeWidth="1.5" />
                <polygon points="0,28 50,56 50,96 0,68" fill="rgba(15, 23, 42, 0.9)" stroke="rgba(255, 255, 255, 0.15)" strokeWidth="1.5" />
                <polygon points="100,28 50,56 50,96 100,68" fill="rgba(30, 41, 59, 0.95)" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="1.5" />
                <path d="M50,18 L50,38 M40,28 L60,28 M43,21 L57,35 M43,35 L57,21" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round" />
                <circle cx="50" cy="28" r="4" fill="#C8973B" />
              </g>

              {/* Center Gold Hardware Security Module */}
              <g transform="translate(200, 70)">
                <polygon points="60,0 120,34 60,68 0,34" fill="url(#goldGradTop)" stroke="#DDAE55" strokeWidth="2" />
                <polygon points="0,34 60,68 60,118 0,84" fill="url(#goldGradLeft)" stroke="#B8860B" strokeWidth="2" />
                <polygon points="120,34 60,68 60,118 120,84" fill="url(#goldGradRight)" stroke="#8B2E2E" strokeWidth="2" />
                <polygon points="60,12 96,34 60,56 24,34" fill="#0A0E17" stroke="#C8973B" strokeWidth="1.5" />
                <path d="M60,24 L60,44 M52,30 L68,30 M52,38 L68,38" stroke="#E8CE9E" strokeWidth="2.5" strokeLinecap="round" />
                <circle cx="60" cy="34" r="5" fill="#DDAE55" />
                <line x1="12" y1="52" x2="28" y2="61" stroke="#C8973B" strokeWidth="1.5" />
                <line x1="12" y1="60" x2="28" y2="69" stroke="#C8973B" strokeWidth="1.5" />
                <line x1="12" y1="68" x2="28" y2="77" stroke="#C8973B" strokeWidth="1.5" />
              </g>

              {/* Right Translucent Wireframe Node */}
              <g transform="translate(310, 110)">
                <polygon points="40,0 80,22 40,44 0,22" fill="rgba(15, 23, 42, 0.4)" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="1.2" strokeDasharray="3 3" />
                <polygon points="0,22 40,44 40,74 0,52" fill="rgba(15, 23, 42, 0.3)" stroke="rgba(255, 255, 255, 0.15)" strokeWidth="1.2" />
                <polygon points="80,22 40,44 40,74 80,52" fill="rgba(15, 23, 42, 0.5)" stroke="rgba(255, 255, 255, 0.15)" strokeWidth="1.2" />
              </g>

              <defs>
                <radialGradient id="heroGoldAura" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#C8973B" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#C8973B" stopOpacity="0" />
                </radialGradient>
                <linearGradient id="goldGradTop" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#FFF2D6" />
                  <stop offset="50%" stopColor="#C8973B" />
                  <stop offset="100%" stopColor="#996515" />
                </linearGradient>
                <linearGradient id="goldGradLeft" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#C8973B" />
                  <stop offset="100%" stopColor="#664614" />
                </linearGradient>
                <linearGradient id="goldGradRight" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#8B2E2E" />
                  <stop offset="100%" stopColor="#3B1212" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>
      </div>

      {/* Agency Partner Trust Ribbon */}
      <div className="relative z-10 mt-16 pt-6 pb-6 border-t border-b border-white/[0.08] flex flex-wrap items-center justify-between gap-6 text-xs text-[#94A3B8]">
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
