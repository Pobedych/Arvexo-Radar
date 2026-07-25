export type BestPracticeStatus =
  | "detected"
  | "under_review"
  | "approved"
  | "rejected"
  | "published"
  | "scaling"
  | "archived";

export interface BestPractice {
  id: string;
  title: string;
  short_description: string;
  department: string;
  department_origin?: string;
  scenario: string;
  scenario_id?: string;
  created_at: string;
  detected_at: string;
  status: BestPracticeStatus;
  confidence_score: number;
  impact_score: number;
  adoption_count: number;
  estimated_time_saved: number;
  estimated_fte_saved: number;
  estimated_money_saved?: number;
  tags: string[];
  recommendation: string;
  user_count: number;
  usage_count: number;
  average_rating: number | null;
  success_rate: number;
  error_rate: number;
  growth_rate: number;
  departments: string[];
  models: string[];
  detection_evidence: Record<string, unknown>;
  published_at: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  recommended_departments?: string[];
  is_estimated?: boolean;
}

export interface BestPracticeTop {
  new: BestPractice[];
  fast_growing: BestPractice[];
  most_effective: BestPractice[];
  by_department: Record<string, BestPractice[]>;
  by_model: Record<string, BestPractice[]>;
}

const now = "2026-07-25T08:00:00Z";

export const demoPractices: BestPractice[] = [
  {
    id: "demo-legal-contracts",
    title: "Проверка договоров по единому чек-листу",
    short_description: "Юристы используют устойчивую цепочку из анализа рисков, проверки реквизитов и финального резюме.",
    department: "Юридический отдел",
    scenario: "Проверка договоров",
    created_at: now,
    detected_at: now,
    status: "approved",
    confidence_score: 94,
    impact_score: 96,
    adoption_count: 28,
    estimated_time_saved: 312,
    estimated_fte_saved: 1.95,
    estimated_money_saved: 780000,
    tags: ["договоры", "юристы", "GigaChat Pro"],
    recommendation: "Используется только юридическим отделом. Рекомендуется внедрение в отдел закупок.",
    user_count: 28,
    usage_count: 486,
    average_rating: 4.8,
    success_rate: 0.96,
    error_rate: 0.04,
    growth_rate: 0.34,
    departments: ["Юридический отдел"],
    models: ["GigaChat Pro"],
    detection_evidence: { classifier: "rule-based-v1" },
    published_at: null,
  },
  {
    id: "demo-reporting",
    title: "Сбор еженедельного отчёта из нескольких источников",
    short_description: "ИИ объединяет данные, проверяет отклонения и формирует управленческое резюме по шаблону.",
    department: "Финансы",
    scenario: "Подготовка отчётов",
    created_at: now,
    detected_at: "2026-07-24T11:20:00Z",
    status: "published",
    confidence_score: 91,
    impact_score: 92,
    adoption_count: 42,
    estimated_time_saved: 428,
    estimated_fte_saved: 2.68,
    estimated_money_saved: 1070000,
    tags: ["отчёты", "финансы", "YandexGPT 5 Pro"],
    recommendation: "Практика уже распространяется между подразделениями. Рекомендуется масштабирование.",
    user_count: 42,
    usage_count: 724,
    average_rating: 4.6,
    success_rate: 0.93,
    error_rate: 0.07,
    growth_rate: 0.28,
    departments: ["Финансы", "Продажи", "Операционный блок"],
    models: ["YandexGPT 5 Pro"],
    detection_evidence: { classifier: "rule-based-v1" },
    published_at: "2026-07-24T13:00:00Z",
  },
  {
    id: "demo-email",
    title: "Подготовка ответов на типовые письма клиентов",
    short_description: "Сотрудники задают контекст, тон и ожидаемое действие, затем проверяют ответ перед отправкой.",
    department: "Поддержка",
    scenario: "Работа с почтой",
    created_at: now,
    detected_at: "2026-07-23T09:15:00Z",
    status: "detected",
    confidence_score: 88,
    impact_score: 87,
    adoption_count: 63,
    estimated_time_saved: 265,
    estimated_fte_saved: 1.66,
    estimated_money_saved: 662500,
    tags: ["почта", "клиенты", "Claude Sonnet"],
    recommendation: "Высокая эффективность. Рекомендуется масштабирование.",
    user_count: 63,
    usage_count: 981,
    average_rating: 4.5,
    success_rate: 0.91,
    error_rate: 0.09,
    growth_rate: 0.61,
    departments: ["Поддержка", "Продажи"],
    models: ["Claude Sonnet"],
    detection_evidence: { classifier: "rule-based-v1" },
    published_at: null,
  },
  {
    id: "demo-presentations",
    title: "Черновик презентации из проектных материалов",
    short_description: "Последовательность превращает протоколы и отчёты в структуру с тезисами и выводами для руководства.",
    department: "Проектный офис",
    scenario: "Подготовка презентаций",
    created_at: now,
    detected_at: "2026-07-22T12:40:00Z",
    status: "under_review",
    confidence_score: 86,
    impact_score: 84,
    adoption_count: 19,
    estimated_time_saved: 146,
    estimated_fte_saved: 0.91,
    estimated_money_saved: 365000,
    tags: ["презентации", "проекты", "GigaChat Pro"],
    recommendation: "Высокая эффективность. Рекомендуется масштабирование.",
    user_count: 19,
    usage_count: 218,
    average_rating: 4.4,
    success_rate: 0.89,
    error_rate: 0.11,
    growth_rate: 0.47,
    departments: ["Проектный офис"],
    models: ["GigaChat Pro"],
    detection_evidence: { classifier: "rule-based-v1" },
    published_at: null,
  },
  {
    id: "demo-code-review",
    title: "Предварительная проверка изменений кода",
    short_description: "Разработчики проверяют риски, тестовые сценарии и документацию до отправки изменений на ревью.",
    department: "Разработка",
    scenario: "Помощь разработчикам",
    created_at: now,
    detected_at: "2026-07-21T16:10:00Z",
    status: "approved",
    confidence_score: 90,
    impact_score: 89,
    adoption_count: 37,
    estimated_time_saved: 238,
    estimated_fte_saved: 1.49,
    estimated_money_saved: 595000,
    tags: ["разработка", "code review", "GPT-5"],
    recommendation: "Высокая эффективность. Рекомендуется масштабирование.",
    user_count: 37,
    usage_count: 552,
    average_rating: 4.7,
    success_rate: 0.94,
    error_rate: 0.06,
    growth_rate: 0.39,
    departments: ["Разработка", "Информационная безопасность"],
    models: ["GPT-5"],
    detection_evidence: { classifier: "rule-based-v1" },
    published_at: null,
  },
  {
    id: "demo-hr-knowledge",
    title: "Ответы сотрудникам по внутренним регламентам",
    short_description: "ИИ находит релевантный пункт регламента и формирует короткий ответ со ссылкой на источник.",
    department: "HR",
    scenario: "Поиск знаний",
    created_at: now,
    detected_at: "2026-07-20T10:30:00Z",
    status: "detected",
    confidence_score: 84,
    impact_score: 81,
    adoption_count: 24,
    estimated_time_saved: 129,
    estimated_fte_saved: 0.81,
    estimated_money_saved: 322500,
    tags: ["HR", "регламенты", "YandexGPT 5 Pro"],
    recommendation: "Используется только подразделением HR. Рекомендуется внедрение в сервисный центр.",
    user_count: 24,
    usage_count: 304,
    average_rating: 4.3,
    success_rate: 0.87,
    error_rate: 0.13,
    growth_rate: 0.52,
    departments: ["HR"],
    models: ["YandexGPT 5 Pro"],
    detection_evidence: { classifier: "rule-based-v1" },
    published_at: null,
  },
];

export function buildDemoTop(items: BestPractice[]): BestPracticeTop {
  const group = (key: "departments" | "models") =>
    items.reduce<Record<string, BestPractice[]>>((acc, item) => {
      item[key].forEach((value) => { (acc[value] ??= []).push(item); });
      return acc;
    }, {});
  return {
    new: [...items].sort((a, b) => b.detected_at.localeCompare(a.detected_at)).slice(0, 5),
    fast_growing: [...items].sort((a, b) => b.growth_rate - a.growth_rate).slice(0, 5),
    most_effective: [...items].sort((a, b) => b.impact_score - a.impact_score).slice(0, 5),
    by_department: group("departments"),
    by_model: group("models"),
  };
}

function apiRoot(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";
  return configured.replace(/\/$/, "").replace(/\/v1$/, "");
}

export async function fetchPractices(): Promise<{ items: BestPractice[]; demo: boolean }> {
  try {
    const response = await fetch(`${apiRoot()}/best-practices`, { signal: AbortSignal.timeout(3500) });
    if (!response.ok) throw new Error(`API ${response.status}`);
    const payload = await response.json();
    return { items: payload.items, demo: false };
  } catch {
    return { items: demoPractices, demo: true };
  }
}

export async function fetchPracticeTop(): Promise<BestPracticeTop> {
  try {
    const response = await fetch(`${apiRoot()}/best-practices/top`, { signal: AbortSignal.timeout(3500) });
    if (!response.ok) throw new Error(`API ${response.status}`);
    return await response.json();
  } catch {
    return buildDemoTop(demoPractices);
  }
}

export async function recommendPractice(practice: BestPractice): Promise<BestPractice> {
  if (practice.id.startsWith("demo-")) {
    return { ...practice, status: "published", published_at: new Date().toISOString() };
  }
  let current = practice;
  if (current.status !== "approved" && current.status !== "published") {
    const approved = await fetch(`${apiRoot()}/best-practices/${practice.id}/approve`, { method: "POST" });
    if (!approved.ok) throw new Error("Не удалось согласовать практику");
    current = await approved.json();
  }
  if (current.status === "published") return current;
  const published = await fetch(`${apiRoot()}/best-practices/${practice.id}/publish`, { method: "POST" });
  if (!published.ok) throw new Error("Не удалось опубликовать практику");
  return await published.json();
}
