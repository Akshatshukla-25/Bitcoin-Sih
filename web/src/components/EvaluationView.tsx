"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from "recharts";

interface EvaluationProps {
  data: {
    metrics_table: Array<{
      Alert_Policy_Level?: string;
      Policy_Level?: string;
      "Alert Policy Level"?: string;
      [key: string]: any;
    }>;
    confusion_matrices: Array<{
      band: string;
      threshold: number;
      description: string;
      tn: number;
      fp: number;
      fn: number;
      tp: number;
      flagged: number;
      precision: number;
      recall: number;
      specificity: number;
      f1_score: number;
    }>;
    roc_curve: {
      auc: number;
      points: Array<{ fpr: number; tpr: number }>;
    };
    pr_curve: {
      auc: number;
      points: Array<{ recall: number; precision: number }>;
    };
  };
}

export default function EvaluationView({ data }: EvaluationProps) {
  const { metrics_table, confusion_matrices, roc_curve, pr_curve } = data;

  return (
    <div className="space-y-8">
      {/* Information Banner */}
      <div className="p-4 rounded-lg bg-[#131B2E] border border-[#1F2A44] text-xs text-[#94A3B8] leading-relaxed">
        <b className="text-[#C8973B]">ℹ️ Evaluation Methodology:</b> Benchmarked against synthetic ground truth generated with planted peel-chain, mixer, and rapid-cashout patterns. Real-world operational deployment incorporates labeled FIU law-enforcement data.
      </div>

      {/* 1. Performance Metrics Table */}
      <div className="bg-[#131B2E] border border-[#1F2A44] rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white font-sans">
            Performance Metrics by Operational Policy Band
          </h3>
          <span className="text-xs font-mono text-[#64748B]">reports/evaluation_metrics.csv</span>
        </div>

        <div className="border border-[#1F2A44] rounded overflow-x-auto">
          <table className="w-full text-left font-mono text-xs text-[#E8E6DE]">
            <thead className="bg-[#1A2438] text-[11px] uppercase text-[#94A3B8] border-b border-[#1F2A44]">
              <tr>
                {metrics_table.length > 0 &&
                  Object.keys(metrics_table[0]).map((h, i) => (
                    <th key={i} className="p-3">
                      {h}
                    </th>
                  ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F2A44]">
              {metrics_table.map((row, i) => (
                <tr
                  key={i}
                  className={`hover:bg-[#1A2438]/50 ${
                    JSON.stringify(row).includes("CRITICAL") ? "bg-[#8B2E2E]/10 font-bold" : ""
                  }`}
                >
                  {Object.values(row).map((val: any, j) => (
                    <td key={j} className="p-3">
                      {typeof val === "number" ? val.toFixed(4) : val}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 2. Interactive Numeric Confusion Matrix Quadrants */}
      <div className="bg-[#131B2E] border border-[#1F2A44] rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white font-sans">
            Diagnostic Confusion Matrices across Alert Triage Levels
          </h3>
          <span className="text-[10px] font-mono text-[#C8973B] bg-[#C8973B]/10 border border-[#C8973B]/30 px-2 py-0.5 rounded">
            QUADRANT DATA
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {confusion_matrices.map((cm, idx) => (
            <div
              key={idx}
              className="bg-[#0B1220] border border-[#1F2A44] rounded-lg p-4 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span
                    className={`font-mono text-xs font-bold ${
                      cm.band === "CRITICAL"
                        ? "text-[#E8A3A3]"
                        : cm.band === "HIGH"
                        ? "text-[#E8B896]"
                        : "text-[#E8CE9E]"
                    }`}
                  >
                    {cm.band} BAND
                  </span>
                  <span className="text-[10px] font-mono text-[#94A3B8]">
                    Score ≥ {cm.threshold}
                  </span>
                </div>
                <div className="text-[11px] text-[#94A3B8] mb-3">{cm.description}</div>
              </div>

              {/* 2x2 Matrix Box */}
              <div className="grid grid-cols-2 gap-1.5 font-mono text-center mb-3">
                <div className="bg-[#131B2E] p-2.5 rounded border border-white/5">
                  <div className="text-[9px] text-[#94A3B8]">TRUE NEG (TN)</div>
                  <div className="text-sm font-bold text-white mt-0.5">{cm.tn}</div>
                </div>
                <div className="bg-[#8B2E2E]/20 p-2.5 rounded border border-[#8B2E2E]/30">
                  <div className="text-[9px] text-[#E8A3A3]">FALSE POS (FP)</div>
                  <div className="text-sm font-bold text-[#E8A3A3] mt-0.5">{cm.fp}</div>
                </div>
                <div className="bg-[#B8562E]/20 p-2.5 rounded border border-[#B8562E]/30">
                  <div className="text-[9px] text-[#E8B896]">FALSE NEG (FN)</div>
                  <div className="text-sm font-bold text-[#E8B896] mt-0.5">{cm.fn}</div>
                </div>
                <div className="bg-[#C8973B]/20 p-2.5 rounded border border-[#C8973B]/30">
                  <div className="text-[9px] text-[#E8CE9E]">TRUE POS (TP)</div>
                  <div className="text-sm font-bold text-[#E8CE9E] mt-0.5">{cm.tp}</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[10px] font-mono border-t border-[#1F2A44] pt-2 text-[#94A3B8]">
                <div>Precision: <b className="text-white">{cm.precision}%</b></div>
                <div>Recall: <b className="text-white">{cm.recall}%</b></div>
                <div>Specificity: <b className="text-white">{cm.specificity}%</b></div>
                <div>F1-Score: <b className="text-white">{cm.f1_score}</b></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 3. Interactive ROC and PR Curves */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: ROC Curve */}
        <div className="bg-[#131B2E] border border-[#1F2A44] rounded-lg p-5">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-white font-sans">
              Receiver Operating Characteristic (ROC)
            </h3>
            <span className="text-xs font-mono font-bold text-[#C8973B]">
              AUC: {roc_curve.auc.toFixed(4)}
            </span>
          </div>
          <div className="text-[11px] text-[#94A3B8] mb-4">
            True Positive Rate vs False Positive Rate across decision thresholds.
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={roc_curve.points} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2A44" />
                <XAxis
                  dataKey="fpr"
                  stroke="#64748B"
                  tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }}
                  label={{ value: "False Positive Rate", position: "insideBottom", offset: -10, fill: "#94A3B8", fontSize: 10 }}
                />
                <YAxis
                  domain={[0, 1]}
                  stroke="#64748B"
                  tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }}
                  label={{ value: "True Positive Rate", angle: -90, position: "insideLeft", offset: 25, fill: "#94A3B8", fontSize: 10 }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0B1220", borderColor: "#1F2A44", color: "#E8E6DE", fontSize: "11px", fontFamily: "monospace" }}
                />
                <Line
                  type="monotone"
                  dataKey="tpr"
                  stroke="#C8973B"
                  strokeWidth={2.5}
                  dot={false}
                  name="Ensemble ROC"
                />
                <ReferenceLine stroke="#64748B" strokeDasharray="3 3" segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right: Precision-Recall Curve */}
        <div className="bg-[#131B2E] border border-[#1F2A44] rounded-lg p-5">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-white font-sans">
              Precision-Recall Curve
            </h3>
            <span className="text-xs font-mono font-bold text-[#5B7A6B]">
              PR-AUC: {pr_curve.auc.toFixed(4)}
            </span>
          </div>
          <div className="text-[11px] text-[#94A3B8] mb-4">
            Trade-off between Precision and Recall for class-imbalanced AML detection.
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={pr_curve.points} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2A44" />
                <XAxis
                  dataKey="recall"
                  stroke="#64748B"
                  tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }}
                  label={{ value: "Recall (True Positive Rate)", position: "insideBottom", offset: -10, fill: "#94A3B8", fontSize: 10 }}
                />
                <YAxis
                  domain={[0, 1]}
                  stroke="#64748B"
                  tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }}
                  label={{ value: "Precision", angle: -90, position: "insideLeft", offset: 25, fill: "#94A3B8", fontSize: 10 }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0B1220", borderColor: "#1F2A44", color: "#E8E6DE", fontSize: "11px", fontFamily: "monospace" }}
                />
                <Line
                  type="monotone"
                  dataKey="precision"
                  stroke="#5B7A6B"
                  strokeWidth={2.5}
                  dot={false}
                  name="Ensemble PR"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
