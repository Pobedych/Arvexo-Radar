"use client";

import {
  Buildings,
  CaretDown,
  CaretRight,
  ChartBar,
  CheckCircle,
  Database,
  DownloadSimple,
  FileText,
  FunnelSimple,
  GearSix,
  Lightbulb,
  List,
  MagnifyingGlass,
  Robot,
  RocketLaunch,
  SealCheck,
  Sparkle,
  SquaresFour,
  WarningCircle,
  X,
} from "@phosphor-icons/react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import {
  BestPractice,
  BestPracticeStatus,
  fetchPractices,
  fetchPracticeTop,
  recommendPractice,
} from "../lib/best-practices";
import {
  EnterpriseFilters,
  fetchAgents,
  fetchDepartments,
  fetchMethodology,
  fetchOverview,
  fetchTools,
} from "../lib/enterprise";
import {
  AgentsView,
  DepartmentsView,
  EfficiencyView,
  EnterpriseOverview,
  InsightsView,
  MethodologyView,
  SourcesView,
} from "./EnterpriseViews";

type View =
  | "overview"
  | "efficiency"
  | "agents"
  | "departments"
  | "insights"
  | "best-practices"
  | "sources"
  | "reports"
  | "methodology";

const viewTitles: Record<View, string> = {
  overview: "Обзор",
  efficiency: "Эффективность ИИ",
  agents: "AI-агенты",
  departments: "Подразделения",
  insights: "Инсайты",
  "best-practices": "Лучшие практики",
  sources: "Источники данных",
  reports: "Отчёты",
  methodology: "Настройки методики",
};

const navGroups = [
  {
    label: "РАБОЧЕЕ ПРОСТРАНСТВО",
    items: [
      { id: "overview" as View, label: "Обзор", icon: SquaresFour },
      { id: "efficiency" as View, label: "Эффективность ИИ", icon: ChartBar },
      { id: "agents" as View, label: "AI-агенты", icon: Robot },
      { id: "departments" as View, label: "Подразделения", icon: Buildings },
      { id: "best-practices" as View, label: "Лучшие практики", icon: SealCheck },
      { id: "insights" as View, label: "Инсайты", icon: Lightbulb },
    ],
  },
  {
    label: "ДАННЫЕ",
    items: [
      { id: "sources" as View, label: "Источники данных", icon: Database },
      { id: "reports" as View, label: "Отчёты", icon: FileText },
      { id: "methodology" as View, label: "Настройки методики", icon: GearSix },
    ],
  },
];

const statusLabels: Record<BestPracticeStatus, string> = {
  detected: "Обнаружена",
  under_review: "На проверке",
  approved: "Согласована",
  rejected: "Отклонена",
  published: "Опубликована",
  scaling: "Масштабируется",
  archived: "В архиве",
};

function formatHours(value: number) {
  return `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 }).format(value)} ч`;
}

function PracticeCard({
  practice,
  onRecommend,
  pending,
}: {
  practice: BestPractice;
  onRecommend: (practice: BestPractice) => void;
  pending: boolean;
}) {
  return (
    <article className="practice-card">
      <div className="practice-card-top">
        <div>
          <span className={`status status-${practice.status}`}>{statusLabels[practice.status]}</span>
          <h3>{practice.title}</h3>
          <p>{practice.short_description}</p>
        </div>
        <div className="impact-score" aria-label={`Impact Score ${practice.impact_score} из 100`}>
          <strong>{Math.round(practice.impact_score)}</strong>
          <span>Impact</span>
        </div>
      </div>
      <div className="practice-department"><Buildings size={15} />{practice.department}</div>
      <dl className="practice-metrics">
        <div><dt>Пользователи</dt><dd>{practice.user_count}</dd></div>
        <div><dt>Экономия времени</dt><dd>{formatHours(practice.estimated_time_saved)}</dd></div>
        <div><dt>Экономия FTE</dt><dd>{practice.estimated_fte_saved.toFixed(2)}</dd></div>
      </dl>
      <div className="practice-recommendation"><Lightbulb size={16} /><span>{practice.recommendation}</span></div>
      <div className="practice-footer">
        <div className="tag-list">{practice.tags.slice(0, 3).map((tag) => <span key={tag}>{tag}</span>)}</div>
        <button
          className="recommend-button"
          type="button"
          disabled={pending || practice.status === "published"}
          onClick={() => onRecommend(practice)}
        >
          {practice.status === "published" ? <CheckCircle size={16} weight="fill" /> : <RocketLaunch size={16} />}
          {practice.status === "published" ? "Рекомендовано" : pending ? "Публикуем..." : "Рекомендовать другим подразделениям"}
        </button>
      </div>
    </article>
  );
}

function BestPracticesView({ practices, onRecommend, pendingId }: { practices: BestPractice[]; onRecommend: (practice: BestPractice) => void; pendingId: string | null }) {
  const [status, setStatus] = useState<BestPracticeStatus | "all">("all");
  const [search, setSearch] = useState("");
  const filtered = practices.filter((practice) => (status === "all" || practice.status === status) && `${practice.title} ${practice.department} ${practice.scenario}`.toLowerCase().includes(search.toLowerCase()));
  return <section><div className="page-heading"><div><h1>AI Best Practices</h1><p>Успешные сценарии использования ИИ, найденные Radar по фактическим сигналам.</p></div><span className="count-badge">{filtered.length} практик</span></div><div className="toolbar"><label className="search-field"><MagnifyingGlass size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Поиск практик" aria-label="Поиск практик" /></label><label><span>Статус</span><select value={status} onChange={(event) => setStatus(event.target.value as BestPracticeStatus | "all")}><option value="all">Все статусы</option>{Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label></div>{filtered.length ? <div className="practice-grid full">{filtered.map((practice) => <PracticeCard key={practice.id} practice={practice} onRecommend={onRecommend} pending={pendingId === practice.id} />)}</div> : <div className="empty-state"><MagnifyingGlass size={28} /><h2>Практики не найдены</h2><p>Измените поисковый запрос или фильтр статуса.</p></div>}</section>;
}

function RankedPracticeList({ title, items, metric }: { title: string; items: BestPractice[]; metric: "date" | "growth" | "impact" }) {
  return <article className="panel ranking-panel"><h2>{title}</h2><div className="ranking-list">{items.slice(0, 4).map((item, index) => <div key={item.id}><span className="rank-number">{String(index + 1).padStart(2, "0")}</span><span><strong>{item.title}</strong><small>{item.department}</small></span><b>{metric === "growth" ? `+${Math.round(item.growth_rate * 100)}%` : metric === "impact" ? item.impact_score : new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "short" }).format(new Date(item.detected_at))}</b></div>)}</div></article>;
}

function DiscoveryView({ top }: { top: Awaited<ReturnType<typeof fetchPracticeTop>> | undefined }) {
  if (!top) return <LoadingState />;
  const groups = (source: Record<string, BestPractice[]>) => Object.entries(source).sort((a, b) => b[1].length - a[1].length);
  return <section><div className="page-heading discovery-heading"><div><h1>Knowledge Discovery</h1><p>Сигналы о том, где рождаются эффективные способы работы и куда их стоит переносить.</p></div><span className="live-badge"><Sparkle size={14} weight="fill" />Правила MVP</span></div><div className="discovery-rankings"><RankedPracticeList title="ТОП новых практик" items={top.new} metric="date" /><RankedPracticeList title="Быстрорастущие" items={top.fast_growing} metric="growth" /><RankedPracticeList title="Самые эффективные" items={top.most_effective} metric="impact" /></div><div className="discovery-groups"><article className="panel group-panel"><div className="group-heading"><Buildings size={19} /><div><h2>Практики по подразделениям</h2><p>Где сформировались повторяемые сценарии</p></div></div><div className="group-list">{groups(top.by_department).map(([name, items]) => <div key={name}><span>{name}</span><b>{items.length}</b><small>лучший Impact {Math.round(Math.max(...items.map((item) => item.impact_score)))}</small></div>)}</div></article><article className="panel group-panel"><div className="group-heading"><Robot size={19} /><div><h2>Практики по моделям</h2><p>Какие модели используются в успешных сценариях</p></div></div><div className="group-list">{groups(top.by_model).map(([name, items]) => <div key={name}><span>{name}</span><b>{items.length}</b><small>{items.reduce((sum, item) => sum + item.usage_count, 0)} использований</small></div>)}</div></article></div></section>;
}

function SupportingView({ view }: { view: "reports" }) {
  const content = {
    reports: { icon: FileText, title: "Отчёты", description: "Сформированные управленческие отчёты Radar.", rows: [["Сводный анализ за июль", "25 июл. 2026"], ["Эффективность подразделений", "24 июл. 2026"], ["Каталог лучших практик", "24 июл. 2026"], ["Качество AI-агентов", "23 июл. 2026"]] },
  }[view];
  const Icon = content.icon;
  return <section><div className="page-heading"><div><h1>{content.title}</h1><p>{content.description}</p></div></div><article className="panel data-view"><div className="data-view-icon"><Icon size={24} /></div><div>{content.rows.map(([label, value]) => <div className="data-row" key={label}><strong>{label}</strong><span>{value}</span><CaretRight size={15} /></div>)}</div></article></section>;
}

function LoadingState() {
  return <div className="loading-grid" aria-label="Загрузка"><div /><div /><div /></div>;
}

export function RadarDashboard() {
  const [view, setView] = useState<View>("overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [workspaceOpen, setWorkspaceOpen] = useState(false);
  const [publishedIds, setPublishedIds] = useState<Set<string>>(new Set());
  const [toast, setToast] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [filters, setFilters] = useState<EnterpriseFilters>({ date_from: "2026-07-01", date_to: "2026-08-01" });
  const practiceQuery = useQuery({ queryKey: ["best-practices"], queryFn: fetchPractices });
  const topQuery = useQuery({ queryKey: ["best-practices", "top"], queryFn: fetchPracticeTop });
  const overviewQuery = useQuery({ queryKey: ["enterprise-overview", filters], queryFn: () => fetchOverview(filters) });
  const agentsQuery = useQuery({ queryKey: ["enterprise-agents", filters], queryFn: () => fetchAgents(filters) });
  const departmentsQuery = useQuery({ queryKey: ["enterprise-departments", filters], queryFn: () => fetchDepartments(filters) });
  const toolsQuery = useQuery({ queryKey: ["enterprise-tools", filters], queryFn: () => fetchTools(filters) });
  const methodologyQuery = useQuery({ queryKey: ["methodology"], queryFn: fetchMethodology });
  const practiceMutation = useMutation({ mutationFn: recommendPractice });

  const practices = useMemo(() => (practiceQuery.data?.items ?? []).map((practice) => publishedIds.has(practice.id) ? { ...practice, status: "published" as const } : practice), [practiceQuery.data, publishedIds]);
  // Any query silently falling back to fabricated demo data (Radar API
  // unreachable) must stay visible as a real warning, not just a small
  // footer note — see docs/11-dashboard.md degraded-state requirement.
  const isDemoData = [overviewQuery, agentsQuery, departmentsQuery, toolsQuery, methodologyQuery, practiceQuery].some((query) => query.data?.demo);

  const navigate = (next: View) => { setView(next); setSidebarOpen(false); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const handleRecommend = async (practice: BestPractice) => {
    setPendingId(practice.id);
    try {
      await practiceMutation.mutateAsync(practice);
      setPublishedIds((current) => new Set(current).add(practice.id));
      setToast("Практика опубликована для других подразделений");
    } catch (error) {
      setToast(error instanceof Error ? error.message : "Не удалось опубликовать практику");
    } finally {
      setPendingId(null);
      window.setTimeout(() => setToast(null), 3200);
    }
  };
  const exportReport = () => {
    const rows = [["Практика", "Подразделение", "Пользователи", "Часы", "FTE", "Impact", "Статус"], ...practices.map((item) => [item.title, item.department, item.user_count, item.estimated_time_saved, item.estimated_fte_saved, item.impact_score, statusLabels[item.status]])];
    // CSV/formula injection guard (docs/16-security.md SEC-02): a leading
    // =, +, -, @, or tab makes Excel/Sheets treat the cell as a formula.
    // Prefixing a single quote forces it to render as plain text instead.
    const sanitizeCell = (value: string) => (/^[=+\-@\t]/.test(value) ? `'${value}` : value);
    const csv = rows.map((row) => row.map((cell) => `"${sanitizeCell(String(cell)).replaceAll('"', '""')}"`).join(",")).join("\n");
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8" }));
    link.download = "arvexo-best-practices.csv";
    link.click();
    URL.revokeObjectURL(link.href);
  };

  return <div className="app-shell">
    <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
      <div className="brand-row"><button type="button" className="brand" onClick={() => navigate("overview")}><span>R</span>Radar</button><button type="button" className="icon-button mobile-only" onClick={() => setSidebarOpen(false)} aria-label="Закрыть меню"><X size={20} /></button></div>
      <nav className="navigation" aria-label="Основная навигация">{navGroups.map((group) => <div className="nav-group" key={group.label}><p>{group.label}</p>{group.items.map((item) => { const Icon = item.icon; return <button type="button" className={`nav-item ${view === item.id ? "active" : ""}`} onClick={() => navigate(item.id)} key={item.id}><Icon size={18} /><span>{item.label}</span>{item.id === "best-practices" && practices.filter((practice) => practice.status === "detected").length > 0 && <b>{practices.filter((practice) => practice.status === "detected").length}</b>}</button>; })}</div>)}</nav>
      <div className="sidebar-footer"><button type="button" className="workspace-button" onClick={() => setWorkspaceOpen((open) => !open)} aria-expanded={workspaceOpen}><span className="workspace-avatar">RD</span><span><strong>Arvexo Radar</strong><small>Рабочее пространство</small></span><CaretDown size={15} /></button>{workspaceOpen && <div className="workspace-menu"><button type="button"><span className="workspace-avatar small">RD</span>Arvexo Radar<CheckCircle size={15} weight="fill" /></button><button type="button"><span className="workspace-avatar small muted">ПС</span>Песочница</button></div>}</div>
    </aside>
    {sidebarOpen && <button className="scrim" aria-label="Закрыть меню" onClick={() => setSidebarOpen(false)} />}

    <main className="main-content">
      <header className="topbar"><div className="topbar-left"><button type="button" className="icon-button menu-button" onClick={() => setSidebarOpen(true)} aria-label="Открыть меню"><List size={20} /></button><div className="breadcrumb"><span>Рабочее пространство</span><CaretRight size={12} /><span>Июль 2026</span><CaretRight size={12} /><strong>{viewTitles[view]}</strong></div></div><div className="topbar-actions"><button type="button" className="secondary-button" onClick={() => setFiltersOpen((open) => !open)} aria-expanded={filtersOpen}><FunnelSimple size={16} />Фильтры<span>{Object.values(filters).filter(Boolean).length}</span></button><button type="button" className="primary-button" onClick={exportReport}><DownloadSimple size={16} />Экспорт отчёта</button><span className="user-avatar" aria-label="Профиль пользователя">U</span></div></header>
      {filtersOpen && <section className="filter-panel enterprise-filters"><label><span>С</span><input type="date" value={filters.date_from ?? ""} onChange={(event) => setFilters((old) => ({ ...old, date_from: event.target.value }))}/></label><label><span>По</span><input type="date" value={filters.date_to ?? ""} onChange={(event) => setFilters((old) => ({ ...old, date_to: event.target.value }))}/></label><label><span>Подразделение</span><select value={filters.department ?? ""} onChange={(event) => setFilters((old) => ({ ...old, department: event.target.value }))}><option value="">Все</option><option>Юридический отдел</option><option>Финансы</option><option>Продажи</option><option>HR</option><option>ИТ</option></select></label><label><span>Роль</span><select value={filters.role ?? ""} onChange={(event) => setFilters((old) => ({ ...old, role: event.target.value }))}><option value="">Все</option><option>Юрист</option><option>Аналитик</option><option>Менеджер по продажам</option><option>HR-партнёр</option></select></label><label><span>Пользователь (hash)</span><input value={filters.user ?? ""} onChange={(event) => setFilters((old) => ({ ...old, user: event.target.value }))} placeholder="user_id_hash" /></label><label><span>Агент</span><select value={filters.agent ?? ""} onChange={(event) => setFilters((old) => ({ ...old, agent: event.target.value }))}><option value="">Все</option>{agentsQuery.data?.data.items.map((agent) => <option value={agent.id} key={agent.id}>{agent.name}</option>)}</select></label><label><span>Модель</span><select value={filters.model ?? ""} onChange={(event) => setFilters((old) => ({ ...old, model: event.target.value }))}><option value="">Все</option><option>GigaChat Pro</option><option>YandexGPT 5 Pro</option><option>Corporate LLM 70B</option></select></label><label><span>Сценарий</span><select value={filters.scenario ?? ""} onChange={(event) => setFilters((old) => ({ ...old, scenario: event.target.value }))}><option value="">Все</option><option value="contract-review">Проверка договоров</option><option value="management-report">Управленческий отчёт</option><option value="crm-followup">Follow-up в CRM</option></select></label><label><span>Инструмент</span><select value={filters.tool ?? ""} onChange={(event) => setFilters((old) => ({ ...old, tool: event.target.value }))}><option value="">Все</option><option>Корпоративные документы</option><option>CRM</option><option>Почта</option><option>Браузер</option></select></label><button type="button" className="text-button" onClick={() => setFiltersOpen(false)}>Готово</button><button type="button" className="text-button muted" onClick={() => setFilters({ date_from: "2026-07-01", date_to: "2026-08-01" })}>Сбросить</button></section>}
      <div className="page-content">
        {isDemoData && <div className="demo-banner" role="status"><WarningCircle size={18} weight="fill" />Radar API недоступен — показаны demo-данные, они не отражают реальное использование ИИ в организации.</div>}
        {practiceQuery.isLoading || overviewQuery.isLoading || agentsQuery.isLoading ? <LoadingState /> : view === "overview" && overviewQuery.data ? <EnterpriseOverview data={overviewQuery.data.data} practices={practices} onOpenPractices={() => navigate("best-practices")} /> : view === "efficiency" && overviewQuery.data && agentsQuery.data ? <EfficiencyView overview={overviewQuery.data.data} agents={agentsQuery.data.data.items} /> : view === "agents" && agentsQuery.data ? <AgentsView data={agentsQuery.data.data} /> : view === "departments" && departmentsQuery.data ? <DepartmentsView data={departmentsQuery.data.data} /> : view === "best-practices" ? <><BestPracticesView practices={practices} onRecommend={handleRecommend} pendingId={pendingId} />{topQuery.data && <DiscoveryView top={topQuery.data} />}</> : view === "insights" && overviewQuery.data ? <InsightsView overview={overviewQuery.data.data} /> : view === "sources" && toolsQuery.data && overviewQuery.data ? <SourcesView tools={toolsQuery.data.data} overview={overviewQuery.data.data} /> : view === "methodology" && methodologyQuery.data ? <MethodologyView initial={methodologyQuery.data.data} /> : <SupportingView view="reports" />}
        <footer className="page-footer"><span>Период: июль 2026 · методика v1</span><span>{isDemoData ? "Demo/Mock — явно помечено" : "Данные Radar API"} | Подразделений 6 | Сценариев 4 | AI-агентов 4</span></footer>
      </div>
    </main>
    {toast && <div className="toast" role="status"><CheckCircle size={18} weight="fill" />{toast}</div>}
  </div>;
}
