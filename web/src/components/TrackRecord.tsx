"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, CheckCircle2 } from "lucide-react";

export default function TrackRecord() {
  const stats = [
    { value: "92.5%", label: "Success Precision Rate", detail: "Critical Triage Tier (Score ≥ 60)" },
    { value: "699", label: "Wallet Entities Triaged", detail: "Multi-model anomaly evaluation" },
    { value: "80.5 ms", label: "Sub-Second Latency", detail: "0.013% of Bitcoin 10m block time" },
    { value: "100%", label: "Air-Gapped Operation", detail: "Zero external network calls" },
  ];

  return (
    <section className="relative z-10 py-12 px-6 sm:px-12 lg:px-20 max-w-7xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
        {/* Left Column: Track Record & 2x2 Grid */}
        <div className="lg:col-span-7">
          <div className="mb-8">
            <h2 className="text-3xl sm:text-4xl font-bold font-sans tracking-tight text-white mb-3">
              Our Proven <br />
              <span className="text-[#C8973B]">Track Record</span>
            </h2>
            <p className="text-sm text-[#94A3B8] leading-relaxed max-w-lg">
              Within milliseconds, our offline multi-model ensemble isolates complex laundering typologies and prepares court-admissible forensic evidence packages with zero external data leakage.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {stats.map((st, idx) => (
              <div
                key={idx}
                className="relative bg-gradient-to-br from-[#101828]/80 to-[#080C16]/95 backdrop-blur-xl border border-white/[0.08] rounded-xl p-6 shadow-[0_10px_30px_rgba(0,0,0,0.5),inset_-1px_-1px_24px_rgba(200,151,59,0.1)] hover:border-[#C8973B]/40 hover:-translate-y-1 transition-all group"
              >
                <div className="font-mono text-3xl sm:text-4xl font-bold text-white tracking-tight mb-2 group-hover:text-[#E8CE9E] transition-colors">
                  {st.value}
                </div>
                <div className="text-xs font-semibold text-[#E8E6DE] mb-1">
                  {st.label}
                </div>
                <div className="text-[11px] text-[#94A3B8]">
                  {st.detail}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Featured Promo Card */}
        <div className="lg:col-span-5">
          <div className="relative bg-gradient-to-br from-[#141C30]/90 to-[#0A0F1C]/98 border border-[#C8973B]/30 rounded-2xl p-8 shadow-[0_16px_48px_rgba(0,0,0,0.6),0_0_30px_rgba(200,151,59,0.12)] overflow-hidden">
            <div className="absolute -top-16 -right-16 w-44 h-44 bg-[radial-gradient(circle,rgba(200,151,59,0.25)_0%,transparent_70%)] pointer-events-none" />

            <div className="relative z-10">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#C8973B]/15 text-[#C8973B] font-mono text-[10.5px] font-bold tracking-wider mb-4 border border-[#C8973B]/30">
                <CheckCircle2 className="w-3.5 h-3.5" /> READY FOR TRIAGE
              </div>

              <h3 className="text-2xl font-bold text-white mb-2 font-sans">
                Interested in full triage?
              </h3>

              <p className="text-xs text-[#94A3B8] leading-relaxed mb-6">
                Our tripartite graph fuses blockchain UTXOs and TCP/IP broadcast origin telemetry with zero data loss and automated FIU-IND SAR export.
              </p>

              {/* 3D Isometric Chip Stack Graphic */}
              <div className="flex justify-center my-6">
                <svg width="220" height="120" viewBox="0 0 240 130" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <polygon points="120,10 190,40 120,70 50,40" fill="rgba(30, 41, 59, 0.85)" stroke="#FFFFFF" strokeWidth="1.5" />
                  <path d="M120,30 L120,50 M110,40 L130,40" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" />
                  <polygon points="120,40 190,70 120,100 50,70" fill="rgba(200, 151, 59, 0.35)" stroke="#C8973B" strokeWidth="1.8" />
                  <circle cx="120" cy="70" r="5" fill="#C8973B" />
                  <polygon points="120,70 190,100 120,130 50,100" fill="rgba(11, 18, 32, 0.95)" stroke="rgba(200, 151, 59, 0.6)" strokeWidth="1.5" />
                </svg>
              </div>

              <Link
                href="/dashboard"
                className="w-full inline-flex items-center justify-center gap-2 py-3 px-5 rounded-lg bg-[#C8973B] hover:bg-[#DDAE55] text-[#05070B] font-mono text-xs font-bold tracking-wider transition-all shadow-[0_4px_20px_rgba(200,151,59,0.4)]"
              >
                LAUNCH FORENSIC MONITOR
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Anchor Banner */}
      <div className="mt-16 pt-8 border-t border-white/[0.08] text-center">
        <h4 className="text-xl sm:text-2xl font-bold text-white font-sans">
          Keeping <span className="text-[#C8973B]">National Sovereign Infrastructure Safe</span> Day And Night!
        </h4>
        <p className="text-xs text-[#64748B] mt-2 font-mono">
          SIH26146 • National Technical Research Organisation (NTRO) • Pure Offline Instrument
        </p>
      </div>
    </section>
  );
}
