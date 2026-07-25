export type DataStatus = "actual" | "estimate" | "mixed" | "demo";

export interface KpiValue {
  key: string;
  label: string;
  value: number;
  unit: string;
  change_percent: number | null;
  data_status: DataStatus;
  formula: string;
  source: string;
  assumption?: string | null;
}

export interface AgentAnalytics {
  id: string;
  name: string;
  purpose: string;
  departments: string[];
  roles: string[];
  model: string;
  tools: string[];
  mau: number;
  requests: number;
  tool_calls: number;
  total_tokens: number;
  cost: number;
  error_rate: number;
  latency_ms: number;
  time_saved_hours: number;
  fte_saved: number;
  money_saved: number;
  net_benefit: number;
  roi: number | null;
  payback_ratio: number | null;
  period: string;
  status: "profitable" | "needs_review" | "loss_making" | "insufficient_data";
  data_status: DataStatus;
  confidence: number;
}

export interface OverviewData {
  period: { date_from: string; date_to: string; label: string };
  provenance: { data_mode: "live" | "demo" | "mixed"; estimated_share: number; source: string; limitations: string[] };
  usage_and_cost: KpiValue[];
  business_effect: KpiValue[];
  is_profitable: boolean;
  executive_conclusion: string;
  requests_by_day: { date: string; requests: number }[];
  cost_and_savings_by_month: { month: string; cost: number; money_saved: number }[];
  top_agents: AgentAnalytics[];
  top_scenarios: Array<Record<string, string | number | boolean>>;
  issues_and_recommendations: Array<Record<string, string | boolean>>;
  best_practices: Array<Record<string, unknown>>;
  applied_filters: Record<string, string>;
}

export interface AnalyticsEnvelope<T> {
  period: OverviewData["period"];
  provenance: OverviewData["provenance"];
  items: T[];
  summary: Record<string, unknown>;
  applied_filters: Record<string, string>;
}

export interface MethodologyData {
  average_monthly_fte_cost: number;
  monthly_work_hours_per_fte: number;
  monthly_work_minutes_per_fte: number;
  include_development_team: boolean;
  electricity_price_per_kwh: number;
  hardware_depreciation_months: number;
  currency: string;
  calculation_period: "month" | "quarter" | "year";
  profitability_thresholds: Record<string, number>;
  best_practice_rules: Record<string, number>;
  model_tariffs: Array<Record<string, string | number | boolean | null>>;
  scenario_benchmarks: Array<Record<string, string | number | boolean | null>>;
  data_status: DataStatus;
}

const fallbackAgents: AgentAnalytics[] = [
  { id: "legal-agent", name: "Агент договоров", purpose: "Проверка рисков и реквизитов договоров", departments: ["Юридический отдел", "Закупки"], roles: ["Юрист"], model: "GigaChat Pro", tools: ["Корпоративные документы", "Система согласования"], mau: 124, requests: 7900, tool_calls: 11840, total_tokens: 100000000, cost: 270000, error_rate: 0.027, latency_ms: 1840, time_saved_hours: 434, fte_saved: 2.7125, money_saved: 1085000, net_benefit: 815000, roi: 301.85, payback_ratio: 4.02, period: "2026-07", status: "profitable", data_status: "actual", confidence: 0.92 },
  { id: "report-copilot", name: "Report Copilot", purpose: "Сбор и проверка управленческой отчётности", departments: ["Финансы", "Операционный блок"], roles: ["Аналитик"], model: "YandexGPT 5 Pro", tools: ["Корпоративные документы", "BI-платформа"], mau: 186, requests: 9600, tool_calls: 15420, total_tokens: 115000000, cost: 360000, error_rate: 0.041, latency_ms: 2120, time_saved_hours: 410.67, fte_saved: 2.5667, money_saved: 1026666.67, net_benefit: 666666.67, roi: 185.19, payback_ratio: 2.85, period: "2026-07", status: "profitable", data_status: "actual", confidence: 0.88 },
  { id: "crm-assistant", name: "CRM-ассистент", purpose: "Follow-up и обновление карточек клиентов", departments: ["Продажи", "Поддержка"], roles: ["Менеджер по продажам"], model: "Corporate LLM 70B", tools: ["CRM", "Почта", "Браузер"], mau: 241, requests: 10200, tool_calls: 20760, total_tokens: 153000000, cost: 320000, error_rate: 0.146, latency_ms: 2980, time_saved_hours: 52, fte_saved: 0.325, money_saved: 130000, net_benefit: -190000, roi: -59.38, payback_ratio: 0.41, period: "2026-07", status: "loss_making", data_status: "estimate", confidence: 0.64 },
  { id: "knowledge-guide", name: "Навигатор знаний", purpose: "Поиск ответов по внутренним регламентам", departments: ["HR", "ИТ"], roles: ["HR-партнёр"], model: "Corporate LLM 70B", tools: ["Корпоративные документы", "HR-система"], mau: 91, requests: 700, tool_calls: 1060, total_tokens: 11000000, cost: 220000, error_rate: 0.083, latency_ms: 1660, time_saved_hours: 11, fte_saved: 0.0688, money_saved: 27500, net_benefit: -192500, roi: -87.5, payback_ratio: 0.13, period: "2026-07", status: "insufficient_data", data_status: "estimate", confidence: 0.35 },
];

const requests = Array.from({ length: 31 }, (_, index) => ({
  date: `2026-07-${String(index + 1).padStart(2, "0")}`,
  requests: 760 + ((index * 79) % 320),
}));
requests[30].requests += 28400 - requests.reduce((sum, item) => sum + item.requests, 0);

export const fallbackOverview: OverviewData = {
  period: { date_from: "2026-07-01T00:00:00Z", date_to: "2026-08-01T00:00:00Z", label: "Июль 2026" },
  provenance: { data_mode: "demo", estimated_share: 0.34, source: "Связный синтетический набор Radar Enterprise MVP", limitations: ["Фактическая экономия требует утверждённого бизнес-бенчмарка."] },
  usage_and_cost: [
    { key: "mau", label: "MAU", value: 642, unit: "польз.", change_percent: 8.4, data_status: "actual", formula: "count(distinct user_id_hash) за 30 дней", source: "LLM gateway telemetry" },
    { key: "requests", label: "AI-запросы", value: 28400, unit: "запр.", change_percent: 12.6, data_status: "actual", formula: "count(request_id)", source: "LLM gateway telemetry" },
    { key: "active_agents", label: "Активные AI-агенты", value: 4, unit: "агента", change_percent: null, data_status: "actual", formula: "count(distinct agent_id)", source: "LLM gateway telemetry" },
    { key: "total_ai_cost", label: "Затраты на AI (A)", value: 1170000, unit: "₽", change_percent: 8.3, data_status: "mixed", formula: "Σ включённых Cost Component", source: "Тарифы + FinOps" },
  ],
  business_effect: [
    { key: "time_saved", label: "Экономия времени", value: 907.67, unit: "ч", change_percent: 16.9, data_status: "mixed", formula: "Σ(tasks × minutes_saved_per_task) / 60", source: "Scenario Benchmark + usage" },
    { key: "fte_saved", label: "Высвобожденный FTE", value: 5.673, unit: "FTE", change_percent: 16.9, data_status: "mixed", formula: "time_saved_minutes / 9600", source: "Методика Radar", assumption: "Эквивалент времени, не сокращение штата" },
    { key: "money_saved", label: "Денежная экономия (B)", value: 2269166.67, unit: "₽", change_percent: 17, data_status: "mixed", formula: "fte_saved × 400 000 ₽", source: "Scenario Benchmark + методика" },
    { key: "roi", label: "ROI", value: 93.95, unit: "%", change_percent: 12.1, data_status: "mixed", formula: "(B − A) / A × 100%", source: "Расчёт Radar" },
    { key: "net_benefit", label: "Чистый эффект", value: 1099166.67, unit: "₽", change_percent: 29.4, data_status: "mixed", formula: "B − A", source: "Расчёт Radar" },
  ],
  is_profitable: true,
  executive_conclusion: "B > A: AI окупается. Чистый эффект 1 099 167 ₽ за месяц.",
  requests_by_day: requests,
  cost_and_savings_by_month: [{ month: "2026-05", cost: 980000, money_saved: 1610000 }, { month: "2026-06", cost: 1080000, money_saved: 1940000 }, { month: "2026-07", cost: 1170000, money_saved: 2269166.67 }],
  top_agents: fallbackAgents,
  top_scenarios: [
    { name: "Проверка договоров", department: "Юридический отдел", completed_tasks: 620, time_saved_hours: 434, money_saved: 1085000, is_estimated: false },
    { name: "Сбор управленческого отчёта", department: "Финансы", completed_tasks: 880, time_saved_hours: 410.67, money_saved: 1026666.67, is_estimated: false },
    { name: "Follow-up в CRM", department: "Продажи", completed_tasks: 520, time_saved_hours: 52, money_saved: 130000, is_estimated: true },
  ],
  issues_and_recommendations: [
    { severity: "critical", title: "CRM-ассистент имеет отрицательный Net Benefit −190 000 ₽", recommendation: "Снизить ошибки интеграции CRM и пересмотреть инференс.", is_estimated: true },
    { severity: "warning", title: "В HR только 34% экономии подтверждено benchmark", recommendation: "Провести A/B-замер поиска по регламентам.", is_estimated: true },
    { severity: "positive", title: "Практика отчётности добавила 320 часов экономии", recommendation: "Продолжить внедрение в операционном блоке.", is_estimated: false },
  ],
  best_practices: [],
  applied_filters: {},
};

const fallbackDepartments = [
  { department: "Юридический отдел", mau: 105, requests: 5300, cost: 230000, money_saved: 730000, net_benefit: 500000, roi: 217.4, adoption_rate: 0.81, confirmed_saving_share: 0.91 },
  { department: "Финансы", mau: 92, requests: 5100, cost: 250000, money_saved: 565000, net_benefit: 315000, roi: 126, adoption_rate: 0.74, confirmed_saving_share: 0.86 },
  { department: "Продажи", mau: 88, requests: 4300, cost: 210000, money_saved: 300000, net_benefit: 90000, roi: 42.9, adoption_rate: 0.68, confirmed_saving_share: 0.58 },
  { department: "Поддержка", mau: 124, requests: 4900, cost: 185000, money_saved: 260000, net_benefit: 75000, roi: 40.5, adoption_rate: 0.79, confirmed_saving_share: 0.63 },
  { department: "HR", mau: 61, requests: 3300, cost: 125000, money_saved: 150000, net_benefit: 25000, roi: 20, adoption_rate: 0.52, confirmed_saving_share: 0.34 },
  { department: "ИТ", mau: 172, requests: 5500, cost: 170000, money_saved: 264000, net_benefit: 94000, roi: 55.3, adoption_rate: 0.87, confirmed_saving_share: 0.71 },
];

const fallbackTools = [
  { tool_name: "Корпоративные документы", category: "documents", usages: 13240, success_rate: 0.978, error_rate: 0.022, avg_latency_ms: 640, top_scenario: "Проверка договоров", money_saved: 910000 },
  { tool_name: "CRM", category: "crm", usages: 7680, success_rate: 0.846, error_rate: 0.154, avg_latency_ms: 1420, top_scenario: "Follow-up клиенту", money_saved: 94000 },
  { tool_name: "Браузер", category: "browser", usages: 5220, success_rate: 0.912, error_rate: 0.088, avg_latency_ms: 1180, top_scenario: "Проверка компании", money_saved: 128000 },
  { tool_name: "Почта", category: "email", usages: 4860, success_rate: 0.903, error_rate: 0.097, avg_latency_ms: 930, top_scenario: "Подготовка ответа", money_saved: 176000 },
];

export const fallbackMethodology: MethodologyData = {
  average_monthly_fte_cost: 400000,
  monthly_work_hours_per_fte: 160,
  monthly_work_minutes_per_fte: 9600,
  include_development_team: false,
  electricity_price_per_kwh: 8.7,
  hardware_depreciation_months: 36,
  currency: "RUB",
  calculation_period: "month",
  profitability_thresholds: { profitable_roi_percent: 20, needs_review_roi_percent: 0 },
  best_practice_rules: { min_impact_score: 70, min_usage_count: 8, min_user_count: 3, min_success_rate: 0.8, max_error_rate: 0.2 },
  model_tariffs: [],
  scenario_benchmarks: [],
  data_status: "demo",
};

function apiRoot(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";
  return configured.replace(/\/$/, "").replace(/\/v1$/, "");
}

export type EnterpriseFilters = Partial<Record<"department" | "role" | "user" | "agent" | "model" | "scenario" | "tool" | "date_from" | "date_to", string>>;

function withFilters(path: string, filters: EnterpriseFilters = {}): string {
  const parameters = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => { if (value) parameters.set(key, value); });
  const query = parameters.toString();
  return query ? `${path}?${query}` : path;
}

async function request<T>(path: string, fallback: T, init?: RequestInit): Promise<{ data: T; demo: boolean }> {
  try {
    const response = await fetch(`${apiRoot()}${path}`, { ...init, signal: AbortSignal.timeout(4000), headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) } });
    if (!response.ok) throw new Error(`Radar API ${response.status}`);
    return { data: await response.json() as T, demo: false };
  } catch {
    return { data: fallback, demo: true };
  }
}

export const fetchOverview = (filters: EnterpriseFilters = {}) => request<OverviewData>(withFilters("/analytics/overview", filters), fallbackOverview);
export const fetchAgents = (filters: EnterpriseFilters = {}) => request<AnalyticsEnvelope<AgentAnalytics>>(withFilters("/analytics/agents", filters), { period: fallbackOverview.period, provenance: fallbackOverview.provenance, items: fallbackAgents, summary: {}, applied_filters: {} });
export const fetchDepartments = (filters: EnterpriseFilters = {}) => request<AnalyticsEnvelope<Record<string, number | string>>>(withFilters("/analytics/departments", filters), { period: fallbackOverview.period, provenance: fallbackOverview.provenance, items: fallbackDepartments, summary: {}, applied_filters: {} });
export const fetchTools = (filters: EnterpriseFilters = {}) => request<AnalyticsEnvelope<Record<string, number | string>>>(withFilters("/analytics/tools", filters), { period: fallbackOverview.period, provenance: fallbackOverview.provenance, items: fallbackTools, summary: {}, applied_filters: {} });
export const fetchMethodology = () => request<MethodologyData>("/methodology", fallbackMethodology);

export async function saveMethodology(value: MethodologyData): Promise<MethodologyData> {
  const payload = {
    average_monthly_fte_cost: value.average_monthly_fte_cost,
    monthly_work_hours_per_fte: value.monthly_work_hours_per_fte,
    include_development_team: value.include_development_team,
    electricity_price_per_kwh: value.electricity_price_per_kwh,
    hardware_depreciation_months: value.hardware_depreciation_months,
    currency: value.currency,
    calculation_period: value.calculation_period,
    profitability_thresholds: value.profitability_thresholds,
    best_practice_rules: value.best_practice_rules,
  };
  const result = await request<MethodologyData>("/methodology", { ...value, monthly_work_minutes_per_fte: value.monthly_work_hours_per_fte * 60 }, { method: "PUT", body: JSON.stringify(payload) });
  return result.data;
}
