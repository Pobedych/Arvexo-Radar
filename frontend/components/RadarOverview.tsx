"use client";

import { ArrowRight, CheckCircle, Clock, Gauge, Robot, Sparkle, TrendDown, TrendUp, WarningCircle } from "@phosphor-icons/react";
import type { OverviewData } from "../lib/enterprise";

const number = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 1 });

export function RadarMark({ small = false }: { small?: boolean }) {
  return <svg className={small ? "radar-mark" : "radar-focus-graphic"} viewBox="0 0 48 48" fill="none" aria-hidden="true"><circle cx="24" cy="24" r="20"/><circle cx="24" cy="24" r="13"/><circle cx="24" cy="24" r="6"/></svg>;
}

function PerformanceChart({ values }: { values: OverviewData["requests_by_day"] }) {
  const points = values.length > 1 ? values.slice(-8) : [{ date: "1", requests: 35 }, { date: "2", requests: 45 }, { date: "3", requests: 40 }, { date: "4", requests: 56 }, { date: "5", requests: 60 }, { date: "6", requests: 53 }, { date: "7", requests: 67 }, { date: "8", requests: 75 }];
  const max = Math.max(...points.map(item => item.requests), 1);
  const path = points.map((item, index) => `${index ? "L" : "M"}${60 + index * (520 / Math.max(points.length - 1, 1))} ${170 - item.requests / max * 125}`).join(" ");
  const soft = points.map((item, index) => `${index ? "L" : "M"}${60 + index * (520 / Math.max(points.length - 1, 1))} ${150 - item.requests / max * 58}`).join(" ");
  return <svg className="reference-chart" viewBox="0 0 620 220" role="img" aria-label="Динамика запросов и эффективности">
    {[45,85,125,165].map(y => <path key={y} d={`M60 ${y}H585`} stroke="var(--border-soft)" />)}
    <path d={soft} fill="none" stroke="#56b7ae" strokeWidth="2" />
    <path d={path} fill="none" stroke="#657cff" strokeWidth="2.4" />
    {points.map((item,index)=><circle key={item.date} cx={60 + index * (520 / Math.max(points.length - 1, 1))} cy={170 - item.requests / max * 125} r="3" fill="#657cff" />)}
    {points.map((item,index)=><text key={`t${item.date}`} x={60 + index * (520 / Math.max(points.length - 1, 1))} y="207" textAnchor="middle">{new Date(item.date).toLocaleDateString("ru-RU",{day:"numeric",month:"short"})}</text>)}
  </svg>;
}

export function RadarOverview({ data, onOpenPractices, onOpenAgents, onOpenMethodology }: { data: OverviewData; onOpenPractices: () => void; onOpenAgents: () => void; onOpenMethodology: () => void; }) {
  const requests = data.top_agents.reduce((sum,agent)=>sum+agent.requests,0);
  const avgLatency = data.top_agents.length ? data.top_agents.reduce((sum,agent)=>sum+agent.latency_ms,0)/data.top_agents.length : 320;
  const accuracy = data.top_agents.length ? data.top_agents.reduce((sum,agent)=>sum+(1-agent.error_rate),0)/data.top_agents.length*100 : 98.2;
  const cards = [
    { label:"Model Health", value:`${number.format(accuracy)}%`, delta:"↑ +0.4%", icon:Gauge },
    { label:"Total Requests", value:requests ? number.format(requests) : "1.4M", delta:"↑ +12%", icon:TrendUp },
    { label:"Incidents", value:String(data.issues_and_recommendations.length || 3), delta:"↓ −50%", icon:WarningCircle },
    { label:"Avg. Latency", value:`${number.format(avgLatency)} ms`, delta:"↓ −18%", icon:Clock },
  ];
  return <section className="reference-overview">
    <header className="reference-heading"><div><h1>Good morning, Alexey</h1><p>Here&apos;s what&apos;s happening with your AI systems today.</p></div><button type="button" onClick={onOpenMethodology}>{data.period.label}</button></header>
    <section className="reference-kpis" aria-label="Ключевые показатели">{cards.map(card=>{const Icon=card.icon;return <article key={card.label}><span>{card.label}</span><div><strong>{card.value}</strong><Icon size={25} weight="duotone" /></div><small>{card.delta}</small></article>;})}</section>
    <section className="reference-grid">
      <article className="reference-performance"><header><h2>Performance Overview</h2><button type="button">Last 7 days⌄</button></header><PerformanceChart values={data.requests_by_day}/><footer><span>● Accuracy</span><span>● Latency</span><span>● Cost</span></footer></article>
      <article className="reference-incidents"><header><h2>Recent Incidents</h2><button type="button" onClick={onOpenAgents}>See all</button></header><ul>
        <li><WarningCircle size={21} weight="fill" /><span><b>Quality drop detected</b><small>{data.top_agents[0]?.name ?? "GPT-4o"} · 12 min ago</small></span></li>
        <li><Clock size={21} weight="fill" /><span><b>Latency spike</b><small>{data.top_agents[1]?.name ?? "Embeddings API"} · 1 hr ago</small></span></li>
        <li><Sparkle size={21} weight="fill" /><span><b>Unusual output pattern</b><small>RAG Service · 3 hr ago</small></span></li>
        <li><CheckCircle size={21} weight="fill" /><span><b>Resolved: High error rate</b><small>Classifier v2 · 5 hr ago</small></span></li>
      </ul></article>
    </section>
    <section className="reference-recommendations"><header><div><h2>Recommendations</h2><p>Actionable insights to improve your AI systems.</p></div><button onClick={onOpenPractices}><Sparkle size={16}/>Generate New Insights</button></header><div>
      {[[TrendUp,"Optimize prompt structure","Simplify system prompts to reduce token usage and improve quality.","+8%"],[Robot,"Switch to cached embeddings","Enable embedding cache for repeated queries to reduce costs.","−35%"],[WarningCircle,"Add guardrails for sensitive outputs","Detect and block potentially sensitive content in real time.","−60%"]].map(([Icon,title,copy,effect])=>{const C=Icon as typeof TrendDown;return <article key={title as string}><C size={24}/><span><b>{title as string}</b><small>{copy as string}</small></span><strong>{effect as string}</strong><button onClick={onOpenPractices}>Apply</button><ArrowRight size={16}/></article>;})}
    </div></section>
    <footer className="reference-foot"><span>Arvexo Radar · {data.provenance.data_mode === "demo" ? "demo data" : "connected sources"}</span><button onClick={onOpenMethodology}>How metrics are calculated →</button></footer>
  </section>;
}
