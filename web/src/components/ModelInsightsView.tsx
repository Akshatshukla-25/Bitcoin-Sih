"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  CartesianGrid,
  ZAxis,
  Legend,
} from "recharts";

interface ModelInsightsProps {
  data: {
    comparison_benchmark: Array<{
      Algorithm: string;
      Type: string;
      ROC_AUC: number;
      PR_AUC: number;
      F1_Score: number;
    }>;
    distributions: Array<{
      model_key: string;
      model_name: string;
      color: string;
      min: number;
      q1: number;
      median: number;
      q3: number;
      max: number;
      mean: number;
      std: number;
    }>;
    agreement_scatter: Array<{
      wallet: string;
      iforest: number;
      mahalanobis: number;
      label: string;
    }>;
  };
}

export default function ModelInsightsView({ data }: ModelInsightsProps) {
  const { comparison_benchmark, distributions, agreement_scatter } = data;

  const getLabelColor = (label: string) => {
    switch (label) {
      case "mixer":
        return "#8B2E2E";
      case "peel_chain":
        return "#C8973B";
      case "rapid_cashout":
        return "#B8562E";
      default:
        return "#5B7A6B";
    }
  };

  const scatterByLabel = {
    normal: agreement_scatter.filter((d) => d.label === "normal"),
    peel_chain: agreement_scatter.filter((d) => d.label === "peel_chain"),
    mixer: agreement_scatter.filter((d) => d.label === "mixer"),
    rapid_cashout: agreement_scatter.filter((d) => d.label === "rapid_cashout"),
  };

  return (
    <div className="space-y-8">
      {/* 2 Columns: Distributions & Scatter */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Model Score Quantiles */}
        <div className="bg-[#131B2E] border border-[#1F2A44] rounded-lg p-5">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-white font-sans">
              Individual Model Anomaly Distributions
            </h3>
            <span className="text-[10px] font-mono text-[#C8973B] bg-[#C8973B]/10 border border-[#C8973B]/30 px-2 py-0.5 rounded">
              QUANTILES
            </span>
          </div>
          <div className="text-[11px] text-[#94A3B8] mb-4">
            Normalized anomaly score spreads [0, 1] across unsupervised detection algorithms.
          </div>

          <div className="space-y-4">
            {distributions.map((d, i) => (
              <div key={i} className="bg-[#0B1220] border border-[#1F2A44] rounded p-3">
                <div className="flex justify-between items-center mb-1 text-xs">
                  <span className="font-bold text-white flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                    {d.model_name}
                  </span>
                  <span className="font-mono text-[11px] text-[#94A3B8]">
                    Median: <b className="text-[#C8973B]">{d.median}</b> | Mean: {d.mean}
                  </span>
                </div>
                <div className="relative h-4 bg-[#1A2438] rounded-full overflow-hidden mt-2">
                  <div
                    className="absolute h-full opacity-40"
                    style={{
                      left: `${d.min * 100}%`,
                      width: `${(d.max - d.min) * 100}%`,
                      backgroundColor: d.color,
                    }}
                  />
                  <div
                    className="absolute h-full opacity-90"
                    style={{
                      left: `${d.q1 * 100}%`,
                      width: `${(d.q3 - d.q1) * 100}%`,
                      backgroundColor: d.color,
                    }}
                  />
                  <div
                    className="absolute h-full w-1 bg-white"
                    style={{ left: `${d.median * 100}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] font-mono text-[#64748B] mt-1">
                  <span>Min: {d.min}</span>
                  <span>Q1: {d.q1}</span>
                  <span>Q3: {d.q3}</span>
                  <span>Max: {d.max}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Isolation Forest vs Mahalanobis Scatter */}
        <div className="bg-[#131B2E] border border-[#1F2A44] rounded-lg p-5">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-white font-sans">
              Isolation Forest vs Mahalanobis Score Agreement
            </h3>
            <span className="text-[10px] font-mono text-[#E8A3A3] bg-[#8B2E2E]/15 border border-[#8B2E2E]/30 px-2 py-0.5 rounded">
              CORRELATION
            </span>
          </div>
          <div className="text-[11px] text-[#94A3B8] mb-4">
            Cross-model score alignment colored by ground truth laundering pattern.
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 10, bottom: 20, left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2A44" />
                <XAxis
                  type="number"
                  dataKey="iforest"
                  name="Isolation Forest"
                  stroke="#64748B"
                  tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }}
                  label={{ value: "Isolation Forest Score", position: "insideBottom", offset: -10, fill: "#94A3B8", fontSize: 10 }}
                />
                <YAxis
                  type="number"
                  dataKey="mahalanobis"
                  name="Robust Mahalanobis"
                  stroke="#64748B"
                  tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }}
                  label={{ value: "Mahalanobis Score", angle: -90, position: "insideLeft", offset: 15, fill: "#94A3B8", fontSize: 10 }}
                />
                <Tooltip
                  content={({ payload }) => {
                    if (payload && payload.length) {
                      const pt = payload[0].payload;
                      return (
                        <div className="bg-[#0B1220] border border-[#1F2A44] p-2 rounded text-xs font-mono">
                          <div className="text-[#C8973B] font-bold">{pt.label.toUpperCase()}</div>
                          <div>IF: {pt.iforest}</div>
                          <div>Mahalanobis: {pt.mahalanobis}</div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Scatter name="Normal" data={scatterByLabel.normal} fill="#5B7A6B" opacity={0.6} />
                <Scatter name="Peel Chain" data={scatterByLabel.peel_chain} fill="#C8973B" opacity={0.8} />
                <Scatter name="Mixer" data={scatterByLabel.mixer} fill="#8B2E2E" opacity={0.8} />
                <Scatter name="Rapid Cashout" data={scatterByLabel.rapid_cashout} fill="#B8562E" opacity={0.8} />
                <Legend wrapperStyle={{ fontSize: "11px", fontFamily: "monospace", paddingTop: "10px" }} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Benchmark Table vs PyOD Baselines */}
      <div className="bg-[#131B2E] border border-[#1F2A44] rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white font-sans">
              Model Comparison Benchmark vs PyOD Baselines
            </h3>
            <div className="text-xs text-[#94A3B8]">
              Empirical evaluation across standard unsupervised anomaly detection baselines.
            </div>
          </div>
          <span className="text-xs font-mono text-[#64748B]">reports/model_comparison.csv</span>
        </div>

        <div className="border border-[#1F2A44] rounded overflow-x-auto">
          <table className="w-full text-left font-mono text-xs text-[#E8E6DE]">
            <thead className="bg-[#1A2438] text-[11px] uppercase text-[#94A3B8] border-b border-[#1F2A44]">
              <tr>
                <th className="p-3">Algorithm</th>
                <th className="p-3">Paradigm</th>
                <th className="p-3">ROC-AUC</th>
                <th className="p-3">PR-AUC</th>
                <th className="p-3">F1-Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F2A44]">
              {comparison_benchmark.map((row, i) => (
                <tr
                  key={i}
                  className={`hover:bg-[#1A2438]/50 ${
                    row.Algorithm.includes("Blended Ensemble") ? "bg-[#C8973B]/10 font-bold" : ""
                  }`}
                >
                  <td className="p-3 text-white flex items-center gap-2">
                    {row.Algorithm}
                    {row.Algorithm.includes("Blended Ensemble") && (
                      <span className="text-[9px] bg-[#C8973B] text-[#05070B] px-1.5 py-0.2 rounded font-bold">
                        OUR SYSTEM
                      </span>
                    )}
                  </td>
                  <td className="p-3 text-[#94A3B8]">{row.Type}</td>
                  <td className="p-3 font-bold text-[#C8973B]">
                    {Number(row.ROC_AUC).toFixed(4)}
                  </td>
                  <td className="p-3">{Number(row.PR_AUC).toFixed(4)}</td>
                  <td className="p-3">{Number(row.F1_Score).toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Bar chart comparing ROC_AUC */}
        <div className="h-56 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={comparison_benchmark}
              margin={{ top: 10, right: 10, left: -10, bottom: 25 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2A44" vertical={false} />
              <XAxis
                dataKey="Algorithm"
                stroke="#64748B"
                tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }}
                angle={-15}
                textAnchor="end"
              />
              <YAxis
                domain={[0, 1]}
                stroke="#64748B"
                tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }}
              />
              <Tooltip
                contentStyle={{ backgroundColor: "#0B1220", borderColor: "#1F2A44", color: "#E8E6DE", fontSize: "11px", fontFamily: "monospace" }}
              />
              <Bar dataKey="ROC_AUC" fill="#C8973B" radius={[4, 4, 0, 0]} name="ROC-AUC Score" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
