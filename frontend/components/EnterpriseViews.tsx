"use client";

import {
  ArrowRight,
  CheckCircle,
  Clock,
  Coins,
  Info,
  Robot,
  SlidersHorizontal,
  TrendDown,
  TrendUp,
  UsersThree,
  WarningCircle,
  Wrench,
} from "@phosphor-icons/react";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import {
  AgentAnalytics,
  AnalyticsEnvelope,
  KpiValue,
  MethodologyData,
  OverviewData,
  saveMethodology,
} from "../lib/enterprise";

const number = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 1 });
const compact = new Intl.NumberFormat("ru-RU", {
  notation: "compact",
  maximumFractionDigits: 1,
});
const rubles = new Intl.NumberFormat("ru-RU", {
  style: "currency",
  currency: "RUB",
  maximumFractionDigits: 0,
});

function formatMetric(metric: KpiValue) {
  if (metric.unit === "₽") return rubles.format(metric.value);
  if (metric.unit === "%") return `${number.format(metric.value)}%`;
  if (metric.unit === "FTE") return number.format(metric.value);
  return `${compact.format(metric.value)} ${metric.unit}`;
}

function DataBadge({
  status,
}: {
  status: KpiValue["data_status"] | "actual" | "estimate";
}) {
  if (status === "demo")
    return <span className="data-badge demo">Demo / mock данные</span>;
  const estimated = status === "estimate" || status === "mixed";
  return (
    <span className={`data-badge ${estimated ? "estimated" : "actual"}`}>
      {estimated ? "Оценка" : "Фактические данные"}
    </span>
  );
}

function MetricCard({
  metric,
  primary = false,
}: {
  metric: KpiValue;
  primary?: boolean;
}) {
  const details = `${metric.formula}. Источник: ${metric.source}${metric.assumption ? `. Допущение: ${metric.assumption}` : ""}`;
  return (
    <article className={`metric-card ${primary ? "primary-metric" : ""}`}>
      <div className="metric-label">
        <span>{metric.label}</span>
        <button
          type="button"
          className="info-button"
          title={details}
          aria-label={`Пояснение: ${details}`}
        >
          <Info size={14} />
        </button>
      </div>
      <strong>{formatMetric(metric)}</strong>
      <div className="metric-meta">
        <DataBadge status={metric.data_status} />
        {metric.change_percent !== null && (
          <span
            className={metric.change_percent >= 0 ? "metric-up" : "metric-down"}
          >
            {metric.change_percent >= 0 ? (
              <TrendUp size={13} />
            ) : (
              <TrendDown size={13} />
            )}
            {number.format(Math.abs(metric.change_percent))}%
          </span>
        )}
      </div>
    </article>
  );
}

function RequestTrend({ values }: { values: OverviewData["requests_by_day"] }) {
  const width = 620;
  const height = 156;
  const max = Math.max(...values.map((item) => item.requests), 1);
  const min = Math.min(...values.map((item) => item.requests), 0);
  const points = values.map((item, index) => ({
    x: values.length === 1 ? 0 : (index / (values.length - 1)) * width,
    y:
      height -
      14 -
      ((item.requests - min) / Math.max(max - min, 1)) * (height - 30),
  }));
  const line = points
    .map(
      (point, index) =>
        `${index ? "L" : "M"}${point.x.toFixed(1)} ${point.y.toFixed(1)}`,
    )
    .join(" ");
  return (
    <svg
      className="request-chart"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Динамика AI-запросов по дням"
    >
      <defs>
        <linearGradient id="requestArea" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#315bbd" stopOpacity=".18" />
          <stop offset="1" stopColor="#315bbd" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path
        d={`${line} L${width} ${height} L0 ${height}Z`}
        fill="url(#requestArea)"
      />
      <path
        d={line}
        fill="none"
        stroke="#315bbd"
        strokeWidth="2"
        vectorEffect="non-scaling-stroke"
      />
      <circle
        cx={points.at(-1)?.x}
        cy={points.at(-1)?.y}
        r="4"
        fill="#315bbd"
      />
    </svg>
  );
}

function CostSavingBars({
  values,
}: {
  values: OverviewData["cost_and_savings_by_month"];
}) {
  const maximum = Math.max(
    ...values.flatMap((item) => [item.cost, item.money_saved]),
    1,
  );
  return (
    <div className="comparison-chart">
      {values.map((item) => (
        <div className="comparison-month" key={item.month}>
          <div className="bar-pair">
            <span
              className="cost-bar"
              style={{ height: `${Math.max((item.cost / maximum) * 100, 5)}%` }}
              title={`Затраты ${rubles.format(item.cost)}`}
            />
            <span
              className="saving-bar"
              style={{
                height: `${Math.max((item.money_saved / maximum) * 100, 5)}%`,
              }}
              title={`Экономия ${rubles.format(item.money_saved)}`}
            />
          </div>
          <strong>
            {new Intl.DateTimeFormat("ru-RU", { month: "short" }).format(
              new Date(`${item.month}-01`),
            )}
          </strong>
        </div>
      ))}
    </div>
  );
}

const agentStatus: Record<AgentAnalytics["status"], string> = {
  profitable: "Окупается",
  needs_review: "Нужна проверка",
  loss_making: "Убыточный",
  insufficient_data: "Недостаточно данных",
};

function AgentRow({ agent }: { agent: AgentAnalytics }) {
  return (
    <div className="agent-row">
      <div className="agent-identity">
        <span className="agent-icon">
          <Robot size={18} />
        </span>
        <span>
          <strong>{agent.name}</strong>
          <small>{agent.purpose}</small>
        </span>
      </div>
      <span>{compact.format(agent.requests)}</span>
      <span>{rubles.format(agent.cost)}</span>
      <span>{rubles.format(agent.money_saved)}</span>
      <span
        className={agent.net_benefit >= 0 ? "positive-value" : "negative-value"}
      >
        {rubles.format(agent.net_benefit)}
      </span>
      <span>{agent.roi === null ? "—" : `${number.format(agent.roi)}%`}</span>
      <span className={`effect-status effect-${agent.status}`}>
        {agentStatus[agent.status]}
      </span>
    </div>
  );
}

export function EnterpriseOverview({
  data,
  practices,
  onOpenPractices,
}: {
  data: OverviewData;
  practices: Array<{
    id: string;
    title: string;
    department: string;
    impact_score: number;
    status: string;
    estimated_money_saved?: number;
  }>;
  onOpenPractices: () => void;
}) {
  const topScenario = data.top_scenarios[0];
  return (
    <>
      <section
        className={`executive-banner ${data.is_profitable ? "profitable" : "optimize"}`}
      >
        <div>
          <span className="executive-kicker">
            Главный вывод · {data.period.label}
          </span>
          {data.provenance.data_mode === "demo" && (
            <DataBadge status="demo" />
          )}
          <h1>{data.executive_conclusion}</h1>
          <p>
            Radar сопоставил полную стоимость AI (A) с денежным эквивалентом
            экономии (B).
          </p>
        </div>
        <div className="equation">
          <span>B</span>
          <b>{data.is_profitable ? ">" : "≤"}</b>
          <span>A</span>
        </div>
      </section>

      <section className="kpi-section" aria-labelledby="usage-kpi-title">
        <div className="section-mini-heading">
          <div>
            <h2 id="usage-kpi-title">Использование и расходы</h2>
            <p>Наблюдаемая активность и полная стоимость AI</p>
          </div>
          <DataBadge status="actual" />
        </div>
        <div className="metric-grid usage-grid">
          {data.usage_and_cost.map((metric) => (
            <MetricCard key={metric.key} metric={metric} />
          ))}
        </div>
      </section>
      <section className="kpi-section" aria-labelledby="effect-kpi-title">
        <div className="section-mini-heading">
          <div>
            <h2 id="effect-kpi-title">Бизнес-эффект</h2>
            <p>Экономия по утверждённым и оценочным benchmark</p>
          </div>
          <span className="assumption-share">
            {Math.round(data.provenance.estimated_share * 100)}% данных
            оценочные
          </span>
        </div>
        <div className="metric-grid effect-grid">
          {data.business_effect.map((metric) => (
            <MetricCard
              key={metric.key}
              metric={metric}
              primary={metric.key === "net_benefit"}
            />
          ))}
        </div>
      </section>

      <section className="analytics-grid">
        <article className="panel chart-panel">
          <div className="panel-heading">
            <div>
              <h2>AI-запросы по дням</h2>
              <p>
                {compact.format(
                  data.requests_by_day.reduce(
                    (sum, item) => sum + item.requests,
                    0,
                  ),
                )}{" "}
                запросов за период
              </p>
            </div>
            <span className="live-dot">Телеметрия</span>
          </div>
          <RequestTrend values={data.requests_by_day} />
        </article>
        <article className="panel comparison-panel">
          <div className="panel-heading">
            <div>
              <h2>Расходы A и экономия B</h2>
              <p>Сравнение по месяцам, ₽</p>
            </div>
            <div className="chart-legend">
              <span>
                <i className="legend-cost" />A
              </span>
              <span>
                <i className="legend-saving" />B
              </span>
            </div>
          </div>
          <CostSavingBars values={data.cost_and_savings_by_month} />
        </article>
      </section>

      <section className="panel agent-performance">
        <div className="panel-heading">
          <div>
            <h2>AI-агенты: использование и окупаемость</h2>
            <p>Техническая успешность отделена от бизнес-эффекта</p>
          </div>
          <button type="button" className="text-link">
            Сравнить агентов <ArrowRight size={14} />
          </button>
        </div>
        <div className="agent-table">
          <div className="agent-row agent-table-head">
            <span>Агент</span>
            <span>Запросы</span>
            <span>Затраты</span>
            <span>Экономия</span>
            <span>Net Benefit</span>
            <span>ROI</span>
            <span>Статус</span>
          </div>
          {data.top_agents.map((agent) => (
            <AgentRow agent={agent} key={agent.id} />
          ))}
        </div>
      </section>

      <section className="overview-grid enterprise-bottom-grid">
        <article className="panel compact-list-panel">
          <div className="panel-heading">
            <div>
              <h2>Эффективные сценарии</h2>
              <p>Подтверждённая экономия и потенциал</p>
            </div>
          </div>
          <div className="scenario-rank-list">
            {data.top_scenarios.slice(0, 4).map((scenario, index) => (
              <div key={String(scenario.name)}>
                <span className="rank-number">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span>
                  <strong>{String(scenario.name)}</strong>
                  <small>
                    {String(scenario.department)} ·{" "}
                    {number.format(Number(scenario.time_saved_hours))} ч
                  </small>
                </span>
                <span className="scenario-value">
                  {rubles.format(Number(scenario.money_saved))}
                  <DataBadge
                    status={scenario.is_estimated ? "estimate" : "actual"}
                  />
                </span>
              </div>
            ))}
          </div>
          {topScenario && (
            <p className="panel-note">
              <CheckCircle size={14} weight="fill" />
              Лидер: {String(topScenario.name)}
            </p>
          )}
        </article>
        <article className="panel compact-list-panel">
          <div className="panel-heading">
            <div>
              <h2>Проблемы и рекомендации</h2>
              <p>Rule-based управленческие сигналы</p>
            </div>
          </div>
          <div className="management-insights">
            {data.issues_and_recommendations.slice(0, 4).map((item) => (
              <div key={String(item.title)}>
                <span className={`insight-symbol insight-${item.severity}`}>
                  {item.severity === "critical" ? (
                    <WarningCircle size={17} />
                  ) : item.severity === "positive" ? (
                    <TrendUp size={17} />
                  ) : (
                    <Info size={17} />
                  )}
                </span>
                <span>
                  <strong>{String(item.title)}</strong>
                  <small>{String(item.recommendation)}</small>
                </span>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="best-practice-preview">
        <div className="section-heading-row">
          <div>
            <h2>Новые лучшие практики</h2>
            <p>Обезличенные сценарии, готовые к проверке и масштабированию</p>
          </div>
          <button type="button" className="text-link" onClick={onOpenPractices}>
            Открыть каталог <ArrowRight size={15} />
          </button>
        </div>
        <div className="practice-strip">
          {practices.slice(0, 3).map((practice) => (
            <article key={practice.id}>
              <span className="practice-number">
                Impact {Math.round(practice.impact_score)}
              </span>
              <h3>{practice.title}</h3>
              <p>{practice.department}</p>
              <strong>
                {rubles.format(practice.estimated_money_saved ?? 0)}
              </strong>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

export function AgentsView({
  data,
}: {
  data: AnalyticsEnvelope<AgentAnalytics>;
}) {
  const [first, setFirst] = useState(data.items[0]?.id ?? "");
  const [second, setSecond] = useState(data.items[1]?.id ?? "");
  const compared = [
    data.items.find((item) => item.id === first),
    data.items.find((item) => item.id === second),
  ].filter(Boolean) as AgentAnalytics[];
  return (
    <section>
      <div className="page-heading">
        <div>
          <h1>AI-агенты</h1>
          <p>
            Стоимость, стабильность и подтверждённый бизнес-эффект каждого
            агента.
          </p>
        </div>
        <span className="count-badge">{data.items.length} активных</span>
      </div>
      <article className="comparison-selector panel">
        <div>
          <strong>Сравнение агентов</strong>
          <small>Одинаковый период и методика</small>
        </div>
        <select
          value={first}
          onChange={(event) => setFirst(event.target.value)}
        >
          {data.items.map((agent) => (
            <option value={agent.id} key={agent.id}>
              {agent.name}
            </option>
          ))}
        </select>
        <span>и</span>
        <select
          value={second}
          onChange={(event) => setSecond(event.target.value)}
        >
          {data.items.map((agent) => (
            <option value={agent.id} key={agent.id}>
              {agent.name}
            </option>
          ))}
        </select>
      </article>
      <div className="agent-comparison">
        {compared.map((agent) => (
          <article className="panel agent-detail" key={agent.id}>
            <div className="agent-detail-heading">
              <span className="agent-icon large">
                <Robot size={24} />
              </span>
              <div>
                <h2>{agent.name}</h2>
                <p>{agent.purpose}</p>
              </div>
              <span className={`effect-status effect-${agent.status}`}>
                {agentStatus[agent.status]}
              </span>
            </div>
            <dl>
              <div>
                <dt>MAU</dt>
                <dd>{agent.mau}</dd>
              </div>
              <div>
                <dt>Запросы</dt>
                <dd>{compact.format(agent.requests)}</dd>
              </div>
              <div>
                <dt>Tool calls</dt>
                <dd>{compact.format(agent.tool_calls)}</dd>
              </div>
              <div>
                <dt>Токены</dt>
                <dd>{compact.format(agent.total_tokens)}</dd>
              </div>
              <div>
                <dt>Затраты</dt>
                <dd>{rubles.format(agent.cost)}</dd>
              </div>
              <div>
                <dt>Error rate</dt>
                <dd>{number.format(agent.error_rate * 100)}%</dd>
              </div>
              <div>
                <dt>Latency</dt>
                <dd>{number.format(agent.latency_ms)} мс</dd>
              </div>
              <div>
                <dt>Экономия времени</dt>
                <dd>{number.format(agent.time_saved_hours)} ч</dd>
              </div>
              <div title="Эквивалент высвобождённого рабочего времени">
                <dt>FTE Saved</dt>
                <dd>{number.format(agent.fte_saved)}</dd>
              </div>
              <div>
                <dt>Money Saved</dt>
                <dd>{rubles.format(agent.money_saved)}</dd>
              </div>
              <div>
                <dt>Net Benefit</dt>
                <dd
                  className={
                    agent.net_benefit >= 0 ? "positive-value" : "negative-value"
                  }
                >
                  {rubles.format(agent.net_benefit)}
                </dd>
              </div>
              <div>
                <dt>ROI</dt>
                <dd>
                  {agent.roi === null ? "—" : `${number.format(agent.roi)}%`}
                </dd>
              </div>
            </dl>
            <div className="agent-tags">
              {agent.tools.map((tool) => (
                <span key={tool}>
                  <Wrench size={12} />
                  {tool}
                </span>
              ))}
            </div>
            <DataBadge status={agent.data_status} />
          </article>
        ))}
      </div>
      <article className="panel all-agents">
        <div className="agent-row agent-table-head">
          <span>Агент</span>
          <span>Запросы</span>
          <span>Затраты</span>
          <span>Экономия</span>
          <span>Net Benefit</span>
          <span>ROI</span>
          <span>Статус</span>
        </div>
        {data.items.map((agent) => (
          <AgentRow key={agent.id} agent={agent} />
        ))}
      </article>
    </section>
  );
}

export function DepartmentsView({
  data,
}: {
  data: AnalyticsEnvelope<Record<string, number | string>>;
}) {
  return (
    <section>
      <div className="page-heading">
        <div>
          <h1>Подразделения</h1>
          <p>
            Внедрение, затраты и денежный эффект по организационным единицам.
          </p>
        </div>
      </div>
      <div className="department-grid">
        {data.items.map((item) => (
          <article
            className="panel department-card"
            key={String(item.department)}
          >
            <div>
              <span className="department-avatar">
                {String(item.department).slice(0, 2).toUpperCase()}
              </span>
              <div>
                <h2>{item.department}</h2>
                <p>
                  {item.mau} MAU · {compact.format(Number(item.requests))}{" "}
                  запросов
                </p>
              </div>
            </div>
            <dl>
              <div>
                <dt>Затраты</dt>
                <dd>{rubles.format(Number(item.cost))}</dd>
              </div>
              <div>
                <dt>Экономия</dt>
                <dd>{rubles.format(Number(item.money_saved))}</dd>
              </div>
              <div>
                <dt>Net Benefit</dt>
                <dd
                  className={
                    Number(item.net_benefit) >= 0
                      ? "positive-value"
                      : "negative-value"
                  }
                >
                  {rubles.format(Number(item.net_benefit))}
                </dd>
              </div>
              <div>
                <dt>ROI</dt>
                <dd>{number.format(Number(item.roi))}%</dd>
              </div>
            </dl>
            <div className="adoption-meter">
              <span>
                <b style={{ width: `${Number(item.adoption_rate) * 100}%` }} />
              </span>
              <small>
                Внедрение {number.format(Number(item.adoption_rate) * 100)}%
              </small>
            </div>
            <DataBadge
              status={
                Number(item.confirmed_saving_share) > 0.7
                  ? "actual"
                  : "estimate"
              }
            />
          </article>
        ))}
      </div>
    </section>
  );
}

export function EfficiencyView({
  overview,
  agents,
}: {
  overview: OverviewData;
  agents: AgentAnalytics[];
}) {
  const cost =
    overview.usage_and_cost.find((metric) => metric.key === "total_ai_cost")
      ?.value ?? 0;
  const saved =
    overview.business_effect.find((metric) => metric.key === "money_saved")
      ?.value ?? 0;
  return (
    <section>
      <div className="page-heading">
        <div>
          <h1>Эффективность ИИ</h1>
          <p>
            От полной стоимости AI до подтверждённого экономического эффекта.
          </p>
        </div>
        <DataBadge status="estimate" />
      </div>
      <section className="economics-hero panel">
        <div>
          <span>Полная стоимость AI · A</span>
          <strong>{rubles.format(cost)}</strong>
          <p>
            Токены, инфраструктура, подписки, оборудование, электроэнергия и
            сопровождение.
          </p>
        </div>
        <span className="economics-operator">{saved > cost ? "<" : "≥"}</span>
        <div>
          <span>Денежная экономия · B</span>
          <strong>{rubles.format(saved)}</strong>
          <p>
            Только сценарии с benchmark; оценочные данные помечены отдельно.
          </p>
        </div>
      </section>
      <div className="formula-grid">
        <article className="panel formula-card">
          <Clock size={20} />
          <h2>Time Saved</h2>
          <code>Σ(tasks × minutes saved)</code>
          <p>{number.format(overview.business_effect[0].value)} ч за период</p>
        </article>
        <article className="panel formula-card">
          <UsersThree size={20} />
          <h2>FTE Saved</h2>
          <code>minutes / monthly work minutes</code>
          <p>
            {number.format(overview.business_effect[1].value)} FTE — эквивалент
            времени
          </p>
        </article>
        <article className="panel formula-card">
          <Coins size={20} />
          <h2>ROI</h2>
          <code>(B − A) / A × 100%</code>
          <p>{number.format(overview.business_effect[3].value)}%</p>
        </article>
      </div>
      <article className="panel scenario-economics">
        <div className="panel-heading">
          <div>
            <h2>Экономика агентов</h2>
            <p>В одной валюте и за единый период</p>
          </div>
        </div>
        {agents.map((agent) => (
          <div key={agent.id}>
            <span>
              <strong>{agent.name}</strong>
              <small>
                {agent.data_status === "actual"
                  ? "Фактический benchmark"
                  : "Оценочный benchmark"}
              </small>
            </span>
            <span>A {rubles.format(agent.cost)}</span>
            <span>B {rubles.format(agent.money_saved)}</span>
            <b
              className={
                agent.net_benefit >= 0 ? "positive-value" : "negative-value"
              }
            >
              {rubles.format(agent.net_benefit)}
            </b>
          </div>
        ))}
      </article>
    </section>
  );
}

export function InsightsView({ overview }: { overview: OverviewData }) {
  return (
    <section>
      <div className="page-heading">
        <div>
          <h1>Инсайты</h1>
          <p>Понятные управленческие выводы на основе прозрачных правил.</p>
        </div>
        <span className="live-badge">Rule-based v1</span>
      </div>
      <div className="insight-card-grid">
        {overview.issues_and_recommendations.map((item) => (
          <article
            className={`panel insight-card insight-card-${item.severity}`}
            key={String(item.title)}
          >
            <span className="insight-rule">
              {item.is_estimated ? "Оценка" : "Фактические данные"}
            </span>
            <h2>{String(item.title)}</h2>
            <p>{String(item.recommendation)}</p>
            <button type="button" className="text-link">
              Открыть обоснование <ArrowRight size={14} />
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}

export function SourcesView({
  tools,
  overview,
}: {
  tools: AnalyticsEnvelope<Record<string, number | string>>;
  overview: OverviewData;
}) {
  const sources = [
    {
      name: "LLM-шлюз",
      status: "Синхронизирован",
      kind: "Факт",
      details: "Запросы, пользователи, модели, токены и задержка",
    },
    {
      name: "FinOps / договоры",
      status: "Синхронизирован",
      kind: "Смешанные",
      details: "Тарифы, инфраструктура, подписки и поддержка",
    },
    {
      name: "Бенчмарки сценариев",
      status: "Требует ревью",
      kind: "Факт + оценка",
      details: "Базовое и фактическое время, выборка и достоверность",
    },
    {
      name: "HR-справочник",
      status: "Demo",
      kind: "Demo",
      details: "Роли, команды, подразделения без открытых ПДн",
    },
  ];
  return (
    <section>
      <div className="page-heading">
        <div>
          <h1>Источники данных</h1>
          <p>Откуда Radar получает фактические и оценочные сигналы.</p>
        </div>
        <span className="count-badge">
          {Math.round(overview.provenance.estimated_share * 100)}% оценки
        </span>
      </div>
      <div className="context-banner" role="note">
        <Info size={18} weight="fill" />
        <span>
          <strong>Корпоративный контекст.</strong> Показатели ниже объединяют фактические, оценочные и демонстрационные источники Radar и не рассчитываются только по текущему загруженному CSV.
        </span>
      </div>
      <div className="source-grid">
        {sources.map((source) => (
          <article className="panel source-card" key={source.name}>
            <span className="source-icon">
              <SlidersHorizontal size={19} />
            </span>
            <div>
              <h2>{source.name}</h2>
              <p>{source.details}</p>
            </div>
            <span className="source-status">{source.status}</span>
            <small>{source.kind}</small>
          </article>
        ))}
      </div>
      <article className="panel tools-table">
        <div className="panel-heading">
          <div>
            <h2>Инструменты агентов</h2>
            <p>Успешность, ошибки и вклад в сценарии</p>
          </div>
        </div>
        <div className="tool-row tool-head">
          <span>Инструмент</span>
          <span>Категория</span>
          <span>Использования</span>
          <span>Успешность</span>
          <span>Ошибки</span>
          <span>Лучший сценарий</span>
          <span>Эффект</span>
        </div>
        {tools.items.map((tool) => (
          <div className="tool-row" key={String(tool.tool_name)}>
            <span>
              <Wrench size={16} />
              <strong>{tool.tool_name}</strong>
            </span>
            <span>{tool.category}</span>
            <span>{compact.format(Number(tool.usages))}</span>
            <span>{number.format(Number(tool.success_rate) * 100)}%</span>
            <span
              className={Number(tool.error_rate) > 0.1 ? "negative-value" : ""}
            >
              {number.format(Number(tool.error_rate) * 100)}%
            </span>
            <span>{tool.top_scenario}</span>
            <span>{rubles.format(Number(tool.money_saved))}</span>
          </div>
        ))}
      </article>
    </section>
  );
}

export function MethodologyView({ initial }: { initial: MethodologyData }) {
  const [form, setForm] = useState(initial);
  const [saved, setSaved] = useState(false);
  const mutation = useMutation({
    mutationFn: saveMethodology,
    onSuccess: (value) => {
      setForm(value);
      setSaved(true);
      window.setTimeout(() => setSaved(false), 2500);
    },
  });
  const updateNumber = (key: keyof MethodologyData, value: string) =>
    setForm((current) => ({ ...current, [key]: Number(value) }));
  return (
    <section>
      <div className="page-heading">
        <div>
          <h1>Настройки методики</h1>
          <p>
            Все параметры расчёта редактируются и версионируются. Значения ниже
            — demo default.
          </p>
        </div>
        <DataBadge status="estimate" />
      </div>
      <form
        className="methodology-layout"
        onSubmit={(event) => {
          event.preventDefault();
          mutation.mutate(form);
        }}
      >
        <article className="panel methodology-form">
          <div className="panel-heading">
            <div>
              <h2>Экономическая модель</h2>
              <p>Базовые допущения для FTE, TCO и ROI</p>
            </div>
          </div>
          <div className="settings-grid">
            <label>
              <span>Средняя стоимость FTE в месяц, ₽</span>
              <input
                type="number"
                min="0"
                value={form.average_monthly_fte_cost}
                onChange={(event) =>
                  updateNumber("average_monthly_fte_cost", event.target.value)
                }
              />
            </label>
            <label>
              <span>Рабочие часы в месяц</span>
              <input
                type="number"
                min="1"
                value={form.monthly_work_hours_per_fte}
                onChange={(event) =>
                  updateNumber("monthly_work_hours_per_fte", event.target.value)
                }
              />
            </label>
            <label>
              <span>Стоимость электроэнергии, ₽/кВт⋅ч</span>
              <input
                type="number"
                min="0"
                step="0.1"
                value={form.electricity_price_per_kwh}
                onChange={(event) =>
                  updateNumber("electricity_price_per_kwh", event.target.value)
                }
              />
            </label>
            <label>
              <span>Амортизация оборудования, мес.</span>
              <input
                type="number"
                min="1"
                value={form.hardware_depreciation_months}
                onChange={(event) =>
                  updateNumber(
                    "hardware_depreciation_months",
                    event.target.value,
                  )
                }
              />
            </label>
            <label>
              <span>Валюта</span>
              <select
                value={form.currency}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    currency: event.target.value,
                  }))
                }
              >
                <option value="RUB">RUB · российский рубль</option>
              </select>
            </label>
            <label>
              <span>Период расчёта</span>
              <select
                value={form.calculation_period}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    calculation_period: event.target
                      .value as MethodologyData["calculation_period"],
                  }))
                }
              >
                <option value="month">Месяц</option>
                <option value="quarter">Квартал</option>
                <option value="year">Год</option>
              </select>
            </label>
          </div>
          <label className="toggle-row">
            <input
              type="checkbox"
              checked={form.include_development_team}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  include_development_team: event.target.checked,
                }))
              }
            />
            <span>
              <strong>Включать стоимость команды разработки в TCO</strong>
              <small>Опциональный компонент; demo default — выключено</small>
            </span>
          </label>
          <div className="methodology-actions">
            <button
              className="primary-button"
              type="submit"
              disabled={mutation.isPending}
            >
              {mutation.isPending ? "Сохраняем..." : "Сохранить методику"}
            </button>
            {saved && (
              <span className="saved-message">
                <CheckCircle size={16} weight="fill" />
                Настройки сохранены
              </span>
            )}
          </div>
        </article>
        <aside className="panel methodology-summary">
          <h2>Как считается результат</h2>
          <ol>
            <li>
              <b>A</b>
              <span>Полная стоимость AI из выбранных Cost Component.</span>
            </li>
            <li>
              <b>B</b>
              <span>Денежный эквивалент времени по Scenario Benchmark.</span>
            </li>
            <li>
              <b>B − A</b>
              <span>Чистый бизнес-эффект.</span>
            </li>
            <li>
              <b>ROI</b>
              <span>(B − A) / A × 100%.</span>
            </li>
          </ol>
          <div className="fte-callout">
            <Info size={17} />
            <p>
              <strong>FTE Saved не равен увольнениям.</strong> Это эквивалент
              высвобождённого рабочего времени.
            </p>
          </div>
        </aside>
      </form>
      <section className="methodology-tables">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <h2>Тарифы моделей</h2>
                <p>Effective-dated, настраиваются через Radar API</p>
            </div>
          </div>
          {form.model_tariffs.length ? (
            form.model_tariffs.map((tariff) => (
              <div className="method-row" key={String(tariff.model_name)}>
                <span>
                  <strong>{String(tariff.model_name)}</strong>
                  <small>с {String(tariff.effective_from).slice(0, 10)}</small>
                </span>
                <span>
                  Input{" "}
                  {rubles.format(Number(tariff.input_price_per_1m_tokens))} / 1M
                </span>
                <span>
                  Output{" "}
                  {rubles.format(Number(tariff.output_price_per_1m_tokens))} /
                  1M
                </span>
              </div>
            ))
          ) : (
            <p className="empty-note">
              Тарифы загрузятся из Radar API после подключения backend.
            </p>
          )}
        </article>
        <article className="panel">
          <div className="panel-heading">
            <div>
              <h2>Нормативы сценариев</h2>
              <p>Baseline, фактическое время и confidence</p>
            </div>
          </div>
          {form.scenario_benchmarks.length ? (
            form.scenario_benchmarks.map((benchmark) => (
              <div className="method-row" key={String(benchmark.scenario_id)}>
                <span>
                  <strong>{String(benchmark.scenario_name)}</strong>
                  <small>{String(benchmark.source_type)}</small>
                </span>
                <span>
                  {benchmark.baseline_minutes_without_ai} →{" "}
                  {benchmark.actual_minutes_with_ai} мин
                </span>
                <span>
                  {number.format(Number(benchmark.confidence_level) * 100)}%
                  confidence
                </span>
              </div>
            ))
          ) : (
            <p className="empty-note">
              Benchmark загрузятся из Radar API после подключения backend.
            </p>
          )}
        </article>
      </section>
    </section>
  );
}
