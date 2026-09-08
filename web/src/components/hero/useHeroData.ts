"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";

export interface OverviewData {
  kpis: {
    total_entities: number;
    active_alerts: number;
    critical_count: number;
    high_count: number;
    medium_count: number;
    low_count: number;
    flagged_volume_btc: number;
    total_transactions: number;
  };
  histogram: { bin: string; min: number; max: number; CRITICAL: number; HIGH: number; MEDIUM: number; LOW: number; total: number }[];
}

export interface TopAlert {
  wallet_address: string;
  composite_risk_score: number;
  risk_band: string;
  reason_codes: string;
  dominant_country: string;
}

export interface ModelDistribution {
  model_key: string;
  model_name: string;
  color: string;
  mean: number;
}

export interface EvaluationData {
  roc_curve: {
    available: boolean;
    auc: number | null;
    points: { fpr: number; tpr: number }[];
  };
}

export interface HeroData {
  overview: OverviewData | null;
  topAlert: TopAlert | null;
  topAlertNarrative: string | null;
  distributions: ModelDistribution[];
  evaluation: EvaluationData | null;
  loading: boolean;
  error: string | null;
}

/**
 * Fetches every real number the hero's bento grid displays, once, from the
 * live FastAPI backend. Nothing in the bento grid should read from a literal
 * — every card consumes fields from this hook.
 */
export function useHeroData(): HeroData {
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [topAlert, setTopAlert] = useState<TopAlert | null>(null);
  const [topAlertNarrative, setTopAlertNarrative] = useState<string | null>(null);
  const [distributions, setDistributions] = useState<ModelDistribution[]>([]);
  const [evaluation, setEvaluation] = useState<EvaluationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [overviewRes, alertsRes, modelsRes, evalRes] = await Promise.all([
          fetchApi<OverviewData>("/api/overview"),
          fetchApi<{ entities: TopAlert[] }>(
            "/api/alerts?bands=CRITICAL,HIGH,MEDIUM,LOW&min_score=0&limit=1&sort_by=composite_risk_score&sort_dir=desc"
          ),
          fetchApi<{ distributions: ModelDistribution[] }>("/api/models"),
          fetchApi<EvaluationData>("/api/evaluation"),
        ]);

        if (cancelled) return;

        setOverview(overviewRes);
        setDistributions(modelsRes.distributions);
        setEvaluation(evalRes);

        const top = alertsRes.entities[0] ?? null;
        setTopAlert(top);

        if (top) {
          const caseDetail = await fetchApi<{ plain_language_explanation: string }>(
            `/api/cases/${top.wallet_address}`
          );
          if (!cancelled) setTopAlertNarrative(caseDetail.plain_language_explanation);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load live data");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return { overview, topAlert, topAlertNarrative, distributions, evaluation, loading, error };
}
