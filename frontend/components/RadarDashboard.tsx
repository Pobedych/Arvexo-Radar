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
import { useMemo, useRef, useState } from "react";

import {
  BestPractice,
  BestPracticeStatus,
  fetchPractices,
  fetchPracticeTop,
  recommendPractice,
} from "../lib/best-practices";
import {
  createRun,
  hasAnalysisResults,
  pollRunUntilDone,
  RunSummary,
  uploadDataset,
} from "../lib/datasets";
import {
  EnterpriseFilters,
  fetchAgents,
  fetchDepartments,
  fetchMethodology,
  fetchOverview,
  fetchTools,
} from "../lib/enterprise";
import { createReport, downloadReportPdf, pollReportUntilDone } from "../lib/reports";
import { fetchRunOverview, RunOverview } from "../lib/runs";
import {
  AgentsView,
  DepartmentsView,
  EfficiencyView,
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

const runStatusLabels: Record<string, string> = {
  queued: "в очереди",
  running: "в обработке",
  completed: "завершён",
  degraded: "завершён с ограничениями",
  failed: "завершён с ошибкой",
  cancelled: "отменён",
};

const generationStatusLabels: Record<string, string> = {
  pending: "ожидает обработки",
  generated: "название сформировано",
  completed: "готово",
  degraded: "название требует уточнения",
  failed: "ошибка формирования",
};

const findingLabels: Record<string, string> = {
  SEC_SENSITIVE_DATA: "Возможные чувствительные данные",
  PH_TOO_LONG: "Слишком длинные запросы",
};

const findingTypeLabels: Record<string, string> = {
  security: "Безопасность",
  prompt_health: "Качество запроса",
};

const severityLabels: Record<string, string> = {
  low: "низкий приоритет",
  medium: "средний приоритет",
  high: "высокий приоритет",
  critical: "критический приоритет",
};

const limitationLabels: Record<string, string> = {
  classification_uses_keyword_fallback: "Категории определены по ключевым словам",
  clustering_uses_placeholder_embeddings: "Сценарии сгруппированы по упрощённым признакам",
  run_degraded_llm_wording_partial: "Часть формулировок создана без помощи языковой модели",
};

function formatRunStatus(status: string) {
  return runStatusLabels[status] ?? status;
}

function formatGenerationStatus(status: string) {
  return generationStatusLabels[status] ?? status;
}

function formatFindingLabel(ruleId: string) {
  return findingLabels[ruleId] ?? ruleId.replaceAll("_", " ");
}

function formatFindingMeta(type: string, severity: string) {
  return `${findingTypeLabels[type] ?? type} · ${severityLabels[severity] ?? severity}`;
}

function formatScenarioName(name: string | null | undefined, index: number) {
  if (!name || /^cluster\s*\d+$/i.test(name) || /^кластер\s*\d+$/i.test(name)) return `Сценарий ${index + 1}`;
  return name;
}

function formatInsightStatement(statement: string) {
  return statement.replace(/^(observation|hypothesis|наблюдение|гипотеза):\s*/i, "");
}

function formatLimitation(limitation: string) {
  return limitationLabels[limitation] ?? limitation.replaceAll("_", " ");
}

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
  if (!top) return <DataUnavailable title="Knowledge Discovery недоступен" reason="Radar API не вернул сводку по лучшим практикам." />;
  const groups = (source: Record<string, BestPractice[]>) => Object.entries(source).sort((a, b) => b[1].length - a[1].length);
  return <section><div className="page-heading discovery-heading"><div><h1>Knowledge Discovery</h1><p>Сигналы о том, где рождаются эффективные способы работы и куда их стоит переносить.</p></div><span className="live-badge"><Sparkle size={14} weight="fill" />Правила MVP</span></div><div className="discovery-rankings"><RankedPracticeList title="ТОП новых практик" items={top.new} metric="date" /><RankedPracticeList title="Быстрорастущие" items={top.fast_growing} metric="growth" /><RankedPracticeList title="Самые эффективные" items={top.most_effective} metric="impact" /></div><div className="discovery-groups"><article className="panel group-panel"><div className="group-heading"><Buildings size={19} /><div><h2>Практики по подразделениям</h2><p>Где сформировались повторяемые сценарии</p></div></div><div className="group-list">{groups(top.by_department).map(([name, items]) => <div key={name}><span>{name}</span><b>{items.length}</b><small>лучший Impact {Math.round(Math.max(...items.map((item) => item.impact_score)))}</small></div>)}</div></article><article className="panel group-panel"><div className="group-heading"><Robot size={19} /><div><h2>Практики по моделям</h2><p>Какие модели используются в успешных сценариях</p></div></div><div className="group-list">{groups(top.by_model).map(([name, items]) => <div key={name}><span>{name}</span><b>{items.length}</b><small>{items.reduce((sum, item) => sum + item.usage_count, 0)} использований</small></div>)}</div></article></div></section>;
}

type ReportStage = "idle" | "generating" | "downloading" | "error";

function ReportsView({
  run,
  onRequestUpload,
}: {
  run: RunSummary | null;
  onRequestUpload: () => void;
}) {
  const [stage, setStage] = useState<ReportStage>("idle");
  const [error, setError] = useState<string | null>(null);
  const reportAvailable = Boolean(run && hasAnalysisResults(run.status));
  const staticRows: [string, string][] = [
    ["Сводный анализ за июль", "25 июл. 2026"],
    ["Эффективность подразделений", "24 июл. 2026"],
    ["Каталог лучших практик", "24 июл. 2026"],
    ["Качество AI-агентов", "23 июл. 2026"],
  ];

  const generateAndDownload = async () => {
    if (!run) return;
    setStage("generating");
    setError(null);
    try {
      const report = await createReport(run.run_id);
      const ready = await pollReportUntilDone(report.report_id);
      if (ready.status !== "generated") {
        throw new Error(ready.safe_error ?? "Отчёт не удалось сформировать.");
      }
      setStage("downloading");
      await downloadReportPdf(ready.report_id);
      setStage("idle");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Не удалось сформировать PDF-отчёт.");
      setStage("error");
    }
  };

  return (
    <section>
      <div className="page-heading">
        <div>
          <h1>Отчёты</h1>
          <p>Сформированные управленческие отчёты Radar.</p>
        </div>
      </div>
      <article className="panel data-view">
        <div className="data-view-icon"><FileText size={24} /></div>
        <div>
          {run ? (
            <div className="data-row report-row">
              <strong>PDF-отчёт по текущему прогону анализа</strong>
              <span>
                {reportAvailable
                  ? run.status === "degraded"
                    ? "Готов с ограничениями — часть LLM-блоков недоступна"
                    : "Готов к формированию"
                  : `Статус прогона: ${formatRunStatus(run.status)}`}
              </span>
              <button
                type="button"
                className="secondary-button"
                disabled={!reportAvailable || stage === "generating" || stage === "downloading"}
                onClick={generateAndDownload}
              >
                {stage === "generating" || stage === "downloading" ? (
                  <GearSix size={16} className="spin" />
                ) : (
                  <DownloadSimple size={16} />
                )}
                {stage === "generating" ? "Формируем PDF..." : stage === "downloading" ? "Скачиваем..." : "Скачать PDF"}
              </button>
            </div>
          ) : (
            <div className="data-row">
              <strong>Нет активного прогона анализа</strong>
              <span>Загрузите датасет, чтобы сформировать PDF-отчёт по своим данным.</span>
              <button type="button" className="secondary-button" onClick={onRequestUpload}>
                <Database size={16} />
                Загрузить датасет
              </button>
            </div>
          )}
          {error && <p className="upload-error" role="alert">{error}</p>}
          {staticRows.map(([label, value]) => (
            <div className="data-row" key={label}>
              <strong>{label}</strong>
              <span>{value}</span>
              <CaretRight size={15} />
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}

type UploadStage = "idle" | "uploading" | "validating" | "analyzing" | "error";

function DatasetUploadModal({
  onClose,
  onCompleted,
}: {
  onClose: () => void;
  onCompleted: (run: RunSummary) => void;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [stage, setStage] = useState<UploadStage>("idle");
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  const stageLabel: Record<UploadStage, string> = {
    idle: "Выберите CSV-файл с запросами пользователей к ИИ-агенту.",
    uploading: "Загружаем и валидируем датасет...",
    validating: "Проверяем структуру и данные...",
    analyzing: "Запускаем классификацию и кластеризацию... это может занять несколько минут.",
    error: "Не удалось обработать датасет.",
  };

  const handleFile = async (file: File) => {
    setFileName(file.name);
    setError(null);
    setStage("uploading");
    try {
      const dataset = await uploadDataset(file);
      setStage("analyzing");
      const run = await createRun(dataset.id);
      const finished = await pollRunUntilDone(run.run_id);
      if (!hasAnalysisResults(finished.status)) {
        throw new Error(`Анализ завершился со статусом «${finished.status}».`);
      }
      onCompleted(finished);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Не удалось обработать датасет.");
      setStage("error");
    }
  };

  const busy = stage === "uploading" || stage === "validating" || stage === "analyzing";

  return (
    <div className="modal-overlay" role="presentation" onClick={busy ? undefined : onClose}>
      <div
        className="panel upload-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Загрузка собственного датасета"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="page-heading">
          <div>
            <h1>Загрузить собственный датасет</h1>
            <p>CSV с запросами пользователей к ИИ-агенту — Radar классифицирует их и найдёт сценарии.</p>
          </div>
          {!busy && (
            <button type="button" className="icon-button" onClick={onClose} aria-label="Закрыть">
              <X size={18} />
            </button>
          )}
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,text/csv"
          hidden
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void handleFile(file);
          }}
        />
        <div className="empty-state upload-dropzone">
          {busy ? <GearSix size={28} className="spin" /> : <Database size={28} />}
          <h2>{fileName ?? "Ещё не выбран файл"}</h2>
          <p>{stageLabel[stage]}</p>
          {error && <p className="upload-error" role="alert">{error}</p>}
          {!busy && (
            <button type="button" className="primary-button" onClick={() => fileInputRef.current?.click()}>
              <Database size={16} />
              Выбрать CSV-файл
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function LoadingState() {
  return <div className="loading-grid" aria-label="Загрузка"><div /><div /><div /></div>;
}

function DataUnavailable({ title, reason, onRequestUpload }: { title: string; reason?: string; onRequestUpload?: () => void }) {
  return (
    <div className="empty-state" role="status">
      <WarningCircle size={28} />
      <h2>{title}</h2>
      <p>{reason ?? "Radar API недоступен или для этого раздела ещё нет данных."}</p>
      {onRequestUpload && (
        <button type="button" className="secondary-button" onClick={onRequestUpload}>
          <Database size={16} />
          Загрузить датасет
        </button>
      )}
    </div>
  );
}

function formatPercent(share: number) {
  return `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 1 }).format(share * 100)}%`;
}

function BarRow({
  label,
  sublabel,
  value,
  barShare,
  tone = "default",
}: {
  label: string;
  sublabel?: string;
  value: string;
  barShare: number;
  tone?: "default" | "warning";
}) {
  return (
    <div className="bar-row">
      <div className="bar-row-top">
        <span className="bar-row-label" title={label}>{label}</span>
        <span className="bar-row-value">{value}</span>
      </div>
      <div className="bar-row-track">
        <div
          className={`bar-row-fill ${tone === "warning" ? "bar-row-fill-warning" : ""}`}
          style={{ width: `${Math.max(Math.min(barShare, 1), 0) * 100}%` }}
        />
      </div>
      {sublabel && <div className="bar-row-sublabel">{sublabel}</div>}
    </div>
  );
}

const LLM_DEGRADATION_LABELS: Record<string, string> = {
  LLM_PROVIDER_UNAVAILABLE: "LLM-провайдер недоступен",
  LLM_TIMEOUT: "BotHub не ответил вовремя",
  LLM_TRANSPORT_ERROR: "ошибка соединения с BotHub",
  LLM_HTTP_ERROR: "BotHub вернул HTTP-ошибку",
  LLM_INVALID_RESPONSE: "BotHub вернул неполный ответ",
  LLM_INVALID_JSON: "модель вернула невалидный JSON",
  LLM_SCHEMA_VALIDATION_FAILED: "JSON модели не соответствует ожидаемой схеме",
  LLM_INVALID_EVIDENCE: "для генерации не хватило подтверждающих данных",
};

function formatDegradations(degradations: RunOverview["degradations"]) {
  return [...new Set(degradations.map(({ code, details }) => {
    const label = LLM_DEGRADATION_LABELS[code] ?? code;
    const statusCode = details?.status_code;
    if (typeof statusCode === "number") return `${label} (HTTP ${statusCode})`;
    const issues = details?.issues;
    if (Array.isArray(issues)) {
      const fields = [...new Set(issues
        .map((issue) => typeof issue === "object" && issue !== null && "loc" in issue
          ? String(issue.loc)
          : "")
        .filter(Boolean))];
      if (fields.length > 0) return `${label} (поля: ${fields.join(", ")})`;
    }
    return label;
  }))]
    .join(", ");
}

function DatasetInsightsView({ overview, onRequestUpload }: { overview: RunOverview; onRequestUpload: () => void }) {
  return (
    <section className="dataset-overview">
      <div className="page-heading dataset-page-heading">
        <div>
          <span className="dataset-eyebrow">Анализ загруженного датасета</span>
          <h1>Обзор запросов к ИИ-агенту</h1>
          <p>{overview.total_records} запросов обработано · прогон {formatRunStatus(overview.status)}</p>
        </div>
        <button type="button" className="secondary-button" onClick={onRequestUpload}>
          <Database size={16} />
          Загрузить другой датасет
        </button>
      </div>

      {overview.degradations.length > 0 && (
        <div className="analysis-notice" role="status">
          <span className="analysis-notice-icon"><WarningCircle size={18} weight="fill" /></span>
          <div>
            <strong>Результаты готовы, но требуют проверки</strong>
            <p>Часть анализа выполнена в упрощённом режиме: {formatDegradations(overview.degradations)}.</p>
          </div>
        </div>
      )}

      <section className="kpi-section" aria-label="Ключевые показатели датасета">
        <div className="metric-grid usage-grid">
          <article className="metric-card dataset-metric primary-metric">
            <div className="metric-label"><span>Запросы</span><Database size={17} /></div>
            <strong>{overview.total_records}</strong>
            <span className="metric-footnote">все строки датасета</span>
          </article>
          <article className="metric-card dataset-metric">
            <div className="metric-label"><span>Категории</span><List size={17} /></div>
            <strong>{overview.top_categories.length}</strong>
            <span className="metric-footnote">тематических групп</span>
          </article>
          <article className="metric-card dataset-metric">
            <div className="metric-label"><span>Сценарии</span><Sparkle size={17} /></div>
            <strong>{overview.top_scenarios.filter((s) => !s.is_noise).length}</strong>
            <span className="metric-footnote">повторяющийся паттерн</span>
          </article>
          <article className="metric-card dataset-metric finding-metric">
            <div className="metric-label"><span>Сигналы риска</span><WarningCircle size={17} /></div>
            <strong>{overview.top_findings.reduce((sum, f) => sum + f.count, 0)}</strong>
            <span className="metric-footnote">срабатывания правил могут пересекаться</span>
          </article>
        </div>
      </section>

      <div className="panel-grid dataset-primary-grid">
        <article className="panel dataset-insights-panel dataset-categories-panel">
          <div className="panel-heading"><div><span className="panel-kicker">Структура спроса</span><h2>Категории запросов</h2></div><p>Доля от {overview.denominator} классифицированных запросов</p></div>
          {overview.top_categories.length ? (
            <div className="bar-chart">
              {overview.top_categories.map((category) => (
                <BarRow
                  key={category.category_id}
                  label={category.name}
                  value={`${category.count} · ${formatPercent(category.share)}`}
                  barShare={category.share}
                />
              ))}
            </div>
          ) : <p>Категории ещё не определены.</p>}
        </article>

        <article className="panel dataset-insights-panel dataset-scenarios-panel">
          <div className="panel-heading"><div><span className="panel-kicker">Повторяемость</span><h2>Сценарии использования</h2></div><p>Паттерны, найденные автоматической группировкой</p></div>
          {overview.top_scenarios.length ? (
            <div className="bar-chart">
              {overview.top_scenarios.map((scenario, index) => (
                <BarRow
                  key={scenario.scenario_id}
                  label={formatScenarioName(scenario.name, index)}
                  sublabel={scenario.is_noise ? "шум" : formatGenerationStatus(scenario.generation_status)}
                  value={`${scenario.size} · ${formatPercent(scenario.share)}`}
                  barShare={scenario.share}
                />
              ))}
            </div>
          ) : <p>Сценарии ещё не сгруппированы.</p>}
        </article>
      </div>

      <div className="panel-grid dataset-secondary-grid">
        <article className="panel dataset-insights-panel dataset-findings-panel">
          <div className="panel-heading"><div><span className="panel-kicker">Контроль качества</span><h2>Проблемы и риски</h2></div><p>Сигналы качества запросов и безопасности</p></div>
          {overview.top_findings.length ? (
            <div className="bar-chart">
              {(() => {
                const maxCount = Math.max(...overview.top_findings.map((f) => f.count), 1);
                return overview.top_findings.map((finding) => (
                  <BarRow
                    key={finding.rule_id}
                    label={formatFindingLabel(finding.rule_id)}
                    sublabel={formatFindingMeta(finding.type, finding.severity)}
                    value={String(finding.count)}
                    barShare={finding.count / maxCount}
                    tone={finding.severity === "high" || finding.severity === "critical" ? "warning" : "default"}
                  />
                ));
              })()}
            </div>
          ) : <p>Находок не обнаружено.</p>}
        </article>

        <article className="panel dataset-insights-panel dataset-insights-summary">
          <div className="panel-heading"><div><span className="panel-kicker">Что важно</span><h2>Выводы и рекомендации</h2></div><p>Наблюдения, подтверждённые данными</p></div>
          {overview.insights.length ? (
            <ul className="insight-list">
              {overview.insights.map((insight) => (
                <li className="insight-item" key={insight.insight_id}>
                  <span className="insight-type">{insight.type === "observation" ? "Наблюдение" : "Гипотеза"}</span>
                  <p>{formatInsightStatement(insight.statement)}</p>
                  <small>Уверенность {Math.round(insight.confidence * 100)}% · подтверждений {insight.evidence_refs.length}</small>
                </li>
              ))}
            </ul>
          ) : <p>Инсайтов пока нет.</p>}
          {overview.recommendations.length > 0 && (
            <ul className="insight-list">
              {overview.recommendations.map((recommendation) => (
                <li className="insight-item recommendation-item" key={recommendation.recommendation_id}>
                  <span className="insight-type">Рекомендация</span>
                  <p>{recommendation.action}</p>
                  <small>{recommendation.rationale}</small>
                </li>
              ))}
            </ul>
          )}
        </article>
      </div>

      {overview.limitations.length > 0 && (
        <article className="limitations-panel">
          <div><span className="panel-kicker">Методика</span><h2>Что учитывать при интерпретации</h2></div>
          <ul>{overview.limitations.map((limitation) => <li key={limitation}>{formatLimitation(limitation)}</li>)}</ul>
        </article>
      )}
    </section>
  );
}

function WelcomeScreen({
  onChooseDemo,
  onChooseUpload,
}: {
  onChooseDemo: () => void;
  onChooseUpload: () => void;
}) {
  return (
    <div className="welcome-screen">
      <div className="welcome-card">
        <span className="brand welcome-brand"><span>R</span>Radar</span>
        <h1>Промпт-радар для ИИ-агентов</h1>
        <p>
          Классифицирует запросы пользователей к ИИ-агенту, находит устойчивые сценарии
          использования и показывает, где агент реально экономит время, а где ломается.
        </p>
        <div className="welcome-options">
          <button type="button" className="welcome-option" onClick={onChooseUpload}>
            <span className="welcome-option-icon"><Database size={22} /></span>
            <span className="welcome-option-body">
              <strong>Загрузить свой датасет</strong>
              <span>CSV с запросами к ИИ-агенту — получите категории, сценарии и инсайты по вашим данным</span>
            </span>
            <CaretRight size={18} className="welcome-option-arrow" />
          </button>
          <button type="button" className="welcome-option" onClick={onChooseDemo}>
            <span className="welcome-option-icon welcome-option-icon-demo"><Sparkle size={22} weight="fill" /></span>
            <span className="welcome-option-body">
              <strong>Посмотреть демо</strong>
              <span>Пример дашборда на синтетическом наборе: агенты, подразделения, ROI, лучшие практики</span>
            </span>
            <CaretRight size={18} className="welcome-option-arrow" />
          </button>
        </div>
      </div>
    </div>
  );
}

export function RadarDashboard() {
  const [mode, setMode] = useState<"choose" | "demo" | "real">("choose");
  const [view, setView] = useState<View>("overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [workspaceOpen, setWorkspaceOpen] = useState(false);
  const [publishedIds, setPublishedIds] = useState<Set<string>>(new Set());
  const [toast, setToast] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [currentRun, setCurrentRun] = useState<RunSummary | null>(null);
  const [filters, setFilters] = useState<EnterpriseFilters>({ date_from: "2026-07-01", date_to: "2026-08-01" });
  const practiceQuery = useQuery({ queryKey: ["best-practices"], queryFn: fetchPractices });
  const topQuery = useQuery({ queryKey: ["best-practices", "top"], queryFn: fetchPracticeTop });
  const overviewQuery = useQuery({ queryKey: ["enterprise-overview", filters], queryFn: () => fetchOverview(filters) });
  const agentsQuery = useQuery({ queryKey: ["enterprise-agents", filters], queryFn: () => fetchAgents(filters) });
  const departmentsQuery = useQuery({ queryKey: ["enterprise-departments", filters], queryFn: () => fetchDepartments(filters) });
  const toolsQuery = useQuery({ queryKey: ["enterprise-tools", filters], queryFn: () => fetchTools(filters) });
  const methodologyQuery = useQuery({ queryKey: ["methodology"], queryFn: fetchMethodology });
  const runOverviewQuery = useQuery({
    queryKey: ["run-overview", currentRun?.run_id],
    queryFn: () => fetchRunOverview(currentRun!.run_id),
    enabled: Boolean(currentRun && hasAnalysisResults(currentRun.status)),
  });
  const practiceMutation = useMutation({ mutationFn: recommendPractice });

  const practices = useMemo(() => (practiceQuery.data?.items ?? []).map((practice) => publishedIds.has(practice.id) ? { ...practice, status: "published" as const } : practice), [practiceQuery.data, publishedIds]);
  // No fabricated demo numbers (docs/11-dashboard.md UI-AC-09): the Enterprise
  // Analytics API (agents/departments/tools/methodology) is a separate demo
  // subsystem, not derived from the uploaded dataset. If it's unreachable we
  // say so plainly instead of quietly rendering fake figures as if real.
  const enterpriseApiUnavailable = [overviewQuery, agentsQuery, departmentsQuery, toolsQuery, methodologyQuery].some((query) => query.data && query.data.data === null);

  const navigate = (next: View) => { setView(next); setSidebarOpen(false); window.scrollTo({ top: 0, behavior: "auto" }); };
  const openUpload = () => { setMode("real"); setUploadOpen(true); };
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

  const renderMainView = () => {
    if (view === "overview") {
      if (currentRun) {
        if (runOverviewQuery.isLoading) return <LoadingState />;
        if (runOverviewQuery.data) return <DatasetInsightsView overview={runOverviewQuery.data} onRequestUpload={openUpload} />;
        return <DataUnavailable title="Не удалось получить статистику по прогону" reason="Проверьте, что backend и база данных доступны, и попробуйте загрузить датасет ещё раз." onRequestUpload={openUpload} />;
      }
      return <DataUnavailable title="Пока нет статистики" reason="Загрузите CSV с запросами пользователей к ИИ-агенту, чтобы увидеть реальные категории, сценарии и инсайты." onRequestUpload={openUpload} />;
    }
    if (practiceQuery.isLoading || overviewQuery.isLoading || agentsQuery.isLoading) return <LoadingState />;
    if (view === "efficiency") return overviewQuery.data?.data && agentsQuery.data?.data ? <EfficiencyView overview={overviewQuery.data.data} agents={agentsQuery.data.data.items} /> : <DataUnavailable title="Эффективность ИИ недоступна" reason={overviewQuery.data?.error ?? agentsQuery.data?.error} />;
    if (view === "agents") return agentsQuery.data?.data ? <AgentsView data={agentsQuery.data.data} /> : <DataUnavailable title="Данные по AI-агентам недоступны" reason={agentsQuery.data?.error} />;
    if (view === "departments") return departmentsQuery.data?.data ? <DepartmentsView data={departmentsQuery.data.data} /> : <DataUnavailable title="Данные по подразделениям недоступны" reason={departmentsQuery.data?.error} />;
    if (view === "best-practices") return <><BestPracticesView practices={practices} onRecommend={handleRecommend} pendingId={pendingId} />{topQuery.data && <DiscoveryView top={topQuery.data} />}</>;
    if (view === "insights") return overviewQuery.data?.data ? <InsightsView overview={overviewQuery.data.data} /> : <DataUnavailable title="Инсайты недоступны" reason={overviewQuery.data?.error} />;
    if (view === "sources") return toolsQuery.data?.data && overviewQuery.data?.data ? <SourcesView tools={toolsQuery.data.data} overview={overviewQuery.data.data} /> : <DataUnavailable title="Источники данных недоступны" reason={toolsQuery.data?.error ?? overviewQuery.data?.error} />;
    if (view === "methodology") return methodologyQuery.data?.data ? <MethodologyView initial={methodologyQuery.data.data} /> : <DataUnavailable title="Настройки методики недоступны" reason={methodologyQuery.data?.error} />;
    return <ReportsView run={currentRun} onRequestUpload={openUpload} />;
  };

  if (mode === "choose") {
    return <WelcomeScreen onChooseDemo={() => setMode("demo")} onChooseUpload={openUpload} />;
  }

  return <div className="app-shell">
    {uploadOpen && (
      <DatasetUploadModal
        onClose={() => setUploadOpen(false)}
        onCompleted={(run) => {
          setCurrentRun(run);
          setUploadOpen(false);
          setToast(
            run.status === "degraded"
              ? "Анализ завершён с ограничениями — локальные результаты и PDF доступны"
              : "Датасет загружен и проанализирован — можно сформировать отчёт",
          );
          window.setTimeout(() => setToast(null), 3200);
          navigate("reports");
        }}
      />
    )}
    <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
      <div className="brand-row"><button type="button" className="brand" onClick={() => setMode("choose")}><span>R</span>Radar</button><button type="button" className="icon-button mobile-only" onClick={() => setSidebarOpen(false)} aria-label="Закрыть меню"><X size={20} /></button></div>
      <nav className="navigation" aria-label="Основная навигация">{navGroups.map((group) => <div className="nav-group" key={group.label}><p>{group.label}</p>{group.items.map((item) => { const Icon = item.icon; return <button type="button" className={`nav-item ${view === item.id ? "active" : ""}`} onClick={() => navigate(item.id)} key={item.id}><Icon size={18} /><span>{item.label}</span>{item.id === "best-practices" && practices.filter((practice) => practice.status === "detected").length > 0 && <b>{practices.filter((practice) => practice.status === "detected").length}</b>}</button>; })}</div>)}</nav>
      <div className="sidebar-footer"><button type="button" className="workspace-button" onClick={() => setWorkspaceOpen((open) => !open)} aria-expanded={workspaceOpen}><span className="workspace-avatar">RD</span><span><strong>Arvexo Radar</strong><small>Рабочее пространство</small></span><CaretDown size={15} /></button>{workspaceOpen && <div className="workspace-menu"><button type="button"><span className="workspace-avatar small">RD</span>Arvexo Radar<CheckCircle size={15} weight="fill" /></button><button type="button"><span className="workspace-avatar small muted">ПС</span>Песочница</button></div>}</div>
    </aside>
    {sidebarOpen && <button className="scrim" aria-label="Закрыть меню" onClick={() => setSidebarOpen(false)} />}

    <main className="main-content">
      <header className="topbar"><div className="topbar-left"><button type="button" className="icon-button menu-button" onClick={() => setSidebarOpen(true)} aria-label="Открыть меню"><List size={20} /></button><div className="breadcrumb"><span>Рабочее пространство</span><CaretRight size={12} /><span>Июль 2026</span><CaretRight size={12} /><strong>{viewTitles[view]}</strong></div></div><div className="topbar-actions"><button type="button" className="secondary-button" onClick={() => setFiltersOpen((open) => !open)} aria-expanded={filtersOpen}><FunnelSimple size={16} />Фильтры<span>{Object.values(filters).filter(Boolean).length}</span></button><button type="button" className="secondary-button" onClick={openUpload}><Database size={16} />Загрузить датасет</button><button type="button" className="primary-button" onClick={exportReport}><DownloadSimple size={16} />Экспорт отчёта</button><span className="user-avatar" aria-label="Профиль пользователя">U</span></div></header>
      {filtersOpen && <section className="filter-panel enterprise-filters"><label><span>С</span><input type="date" value={filters.date_from ?? ""} onChange={(event) => setFilters((old) => ({ ...old, date_from: event.target.value }))}/></label><label><span>По</span><input type="date" value={filters.date_to ?? ""} onChange={(event) => setFilters((old) => ({ ...old, date_to: event.target.value }))}/></label><label><span>Подразделение</span><select value={filters.department ?? ""} onChange={(event) => setFilters((old) => ({ ...old, department: event.target.value }))}><option value="">Все</option><option>Юридический отдел</option><option>Финансы</option><option>Продажи</option><option>HR</option><option>ИТ</option></select></label><label><span>Роль</span><select value={filters.role ?? ""} onChange={(event) => setFilters((old) => ({ ...old, role: event.target.value }))}><option value="">Все</option><option>Юрист</option><option>Аналитик</option><option>Менеджер по продажам</option><option>HR-партнёр</option></select></label><label><span>Пользователь (hash)</span><input value={filters.user ?? ""} onChange={(event) => setFilters((old) => ({ ...old, user: event.target.value }))} placeholder="user_id_hash" /></label><label><span>Агент</span><select value={filters.agent ?? ""} onChange={(event) => setFilters((old) => ({ ...old, agent: event.target.value }))}><option value="">Все</option>{agentsQuery.data?.data?.items.map((agent) => <option value={agent.id} key={agent.id}>{agent.name}</option>)}</select></label><label><span>Модель</span><select value={filters.model ?? ""} onChange={(event) => setFilters((old) => ({ ...old, model: event.target.value }))}><option value="">Все</option><option>GigaChat Pro</option><option>YandexGPT 5 Pro</option><option>Corporate LLM 70B</option></select></label><label><span>Сценарий</span><select value={filters.scenario ?? ""} onChange={(event) => setFilters((old) => ({ ...old, scenario: event.target.value }))}><option value="">Все</option><option value="contract-review">Проверка договоров</option><option value="management-report">Управленческий отчёт</option><option value="crm-followup">Follow-up в CRM</option></select></label><label><span>Инструмент</span><select value={filters.tool ?? ""} onChange={(event) => setFilters((old) => ({ ...old, tool: event.target.value }))}><option value="">Все</option><option>Корпоративные документы</option><option>CRM</option><option>Почта</option><option>Браузер</option></select></label><button type="button" className="text-button" onClick={() => setFiltersOpen(false)}>Готово</button><button type="button" className="text-button muted" onClick={() => setFilters({ date_from: "2026-07-01", date_to: "2026-08-01" })}>Сбросить</button></section>}
      <div className="page-content">
        {enterpriseApiUnavailable && view !== "overview" && view !== "reports" && (
          <div className="demo-banner" role="status">
            <WarningCircle size={18} weight="fill" />
            Enterprise Analytics API недоступен для этого раздела — показанные данные могут быть неполными.
          </div>
        )}
        {renderMainView()}
        {currentRun && runOverviewQuery.data && (
          <footer className="page-footer">
            <span>Прогон {currentRun.run_id.slice(0, 8)} · {formatRunStatus(currentRun.status)}</span>
            <span>Записей {runOverviewQuery.data.total_records} · Категорий {runOverviewQuery.data.top_categories.length} · Сценариев {runOverviewQuery.data.top_scenarios.length}</span>
          </footer>
        )}
      </div>
    </main>
    {toast && <div className="toast" role="status"><CheckCircle size={18} weight="fill" />{toast}</div>}
  </div>;
}
