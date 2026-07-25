import { apiV1Root } from "./datasets";

export interface CategorySummary {
  category_id: string;
  name: string;
  count: number;
  share: number;
  avg_confidence: number;
}

export interface ScenarioSummary {
  scenario_id: string;
  name: string | null;
  description: string | null;
  size: number;
  share: number;
  quality: Record<string, unknown>;
  category_ids: string[];
  generation_status: string;
  is_noise: boolean;
}

export interface FindingSummary {
  rule_id: string;
  type: string;
  severity: string;
  count: number;
  examples: string[];
}

export interface InsightSummary {
  insight_id: string;
  type: string;
  statement: string;
  evidence_refs: string[];
  confidence: number;
  limitations: string[];
}

export interface RecommendationSummary {
  recommendation_id: string;
  action: string;
  rationale: string;
  linked_insight_id: string | null;
  priority_basis: string;
  caveats: string[];
}

export interface RunOverview {
  run_id: string;
  dataset_id: string;
  status: string;
  total_records: number;
  denominator: number;
  top_categories: CategorySummary[];
  top_scenarios: ScenarioSummary[];
  top_findings: FindingSummary[];
  insights: InsightSummary[];
  recommendations: RecommendationSummary[];
  trend: { available: boolean; reason: string | null };
  degradations: { code: string; affected: string[]; details?: Record<string, unknown> }[];
  limitations: string[];
}

export async function fetchRunOverview(runId: string): Promise<RunOverview | null> {
  try {
    const response = await fetch(`${apiV1Root()}/runs/${runId}/overview`);
    if (!response.ok) return null;
    return (await response.json()) as RunOverview;
  } catch {
    return null;
  }
}
