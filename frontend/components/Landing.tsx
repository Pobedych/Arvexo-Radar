"use client";

import {
  ArrowLeft, ArrowRight, Bell, Books, ChartBar, Clock, House, MagnifyingGlass,
  ShareNetwork, ShieldCheck, Sparkle, Star, TrendUp, UserCircle, Warning,
} from "@phosphor-icons/react";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

function Brand({ compact = false }: { compact?: boolean }) {
  return <span className={`arvexo-brand ${compact ? "compact" : ""}`}>
    <span className="arvexo-glyph" aria-hidden="true"><i /><i /><i /></span>
    <span><strong>ARVEXO</strong><small>Radar</small></span>
  </span>;
}

const dashboardCards = [
  { icon: ShareNetwork, title: "Карта сценариев", copy: "Кластеры и паттерны запросов" },
  { icon: ChartBar, title: "Эффективность и ROI", copy: "Реальная ценность и экономия" },
  { icon: Books, title: "Лучшие практики", copy: "Проверенные сценарии" },
  { icon: Warning, title: "Проблемные зоны", copy: "Где ИИ даёт сбой" },
];

function MobileDashboard({ onOpen }: { onOpen: (screen: number) => void }) {
  return <div className="mobile-dashboard">
    <header className="mobile-app-head"><Brand compact /><div><Bell size={22} /><span>AK</span></div></header>
    <h1>Обзор</h1><p>Ваши промпты. Больше инсайтов. Большая ценность.</p>
    <label className="mobile-search"><MagnifyingGlass size={20} /><input aria-label="Поиск" placeholder="Поиск по запросам, сценариям, тегам..." /></label>
    <div className="mobile-tabs"><button className="active">Сценарии</button><button>ROI</button><button>Риски</button><button>Практики</button></div>
    <section className="mobile-total"><span>ВСЕГО ПРОМПТОВ ПРОАНАЛИЗИРОВАНО</span><div><strong>12 480</strong><b>↗ +12%</b><i><em /><em /><em /><em /></i></div><dl><div><dt>Автоматизация</dt><dd>68%</dd><small>▲ +5%</small></div><div><dt>Экономия времени</dt><dd>146 ч</dd><small>▲ +28%</small></div><div><dt>Эффективность ИИ</dt><dd>8.7<sup>/10</sup></dd><small>▲ +0.6</small></div></dl></section>
    <div className="mobile-feature-grid">{dashboardCards.map((card, index) => { const Icon = card.icon; return <button key={card.title} onClick={() => onOpen(index === 1 ? 3 : 2)}><span><Icon size={23} weight="duotone" /></span><b>{card.title}</b><small>{card.copy}</small><i><ArrowRight size={16} /></i></button>; })}</div>
    <nav className="mobile-bottom-nav"><button className="active"><House size={21} weight="fill" /><span>Главная</span></button><button><ChartBar size={21} /><span>Аналитика</span></button><button><Books size={21} /><span>Библиотека</span></button><button><Bell size={21} /><span>Уведомления</span></button><button><UserCircle size={21} /><span>Профиль</span></button></nav>
  </div>;
}

function MobileFeature({ kind, onBack }: { kind: "map" | "roi"; onBack: () => void }) {
  const map = kind === "map";
  return <div className="mobile-feature-page">
    <header><button onClick={onBack} aria-label="Назад"><ArrowLeft size={25} /></button><div><Star size={24} /><ShareNetwork size={24} /></div></header>
    <div className="feature-visual"><Image src={map ? "/images/scenario-map.png" : "/images/roi-growth.png"} alt={map ? "Карта связанных сценариев" : "Рост эффективности и ROI"} fill sizes="(max-width: 760px) 100vw, 420px" priority />{!map && <><span className="saving"><Clock size={20} />Экономия<br />времени</span><strong className="growth">+27%</strong><span className="roi-chip"><TrendUp size={20} />ROI<br /><b>↑ Растёт</b></span></>}</div>
    <h1>{map ? "Карта сценариев" : "Эффективность и ROI"}</h1>
    <p>{map ? "Показывает устойчивые пользовательские сценарии и частые запросы, объединяя схожие промпты в понятные кластеры." : "Показывает, где автоматизация экономит время, а где процесс буксует. Помогает приоритизировать сценарии и улучшать результаты."}</p>
    <div className="feature-stats">{map ? <><span><ShareNetwork size={23} /><b>12</b><small>кластеров</small></span><span><ChartBar size={23} /><b>84%</b><small>покрытие</small></span><span><Books size={23} /><b>Топ-запросы</b><small>выявлены</small></span></> : <><span><ChartBar size={23} /><small>ROI</small><b>+27%</b></span><span><Clock size={23} /><small>Экономия</small><b>146 ч</b></span><span><ShieldCheck size={23} /><small>Стабильность</small><b>91%</b></span></>}</div>
    <div className="feature-benefits">{(map ? [[ShareNetwork,"Автоклассификация запросов"],[ChartBar,"Визуализация кластеров"],[Sparkle,"Выявление новых сценариев"]] : [[Clock,"Экономия времени"],[Star,"Качество ответов"],[Warning,"Точки отказа"]]).map(([Icon,label]) => { const C=Icon as typeof Clock; return <span key={label as string}><C size={24} /><small>{label as string}</small></span>; })}</div>
    <Link className="mobile-primary" href="/app">{map ? "Открыть анализ" : "Посмотреть отчёт"}<ArrowRight size={22} /></Link>
  </div>;
}

function MobileExperience() {
  const [screen, setScreen] = useState(0);
  if (screen === 1) return <MobileDashboard onOpen={setScreen} />;
  if (screen === 2) return <MobileFeature kind="map" onBack={() => setScreen(1)} />;
  if (screen === 3) return <MobileFeature kind="roi" onBack={() => setScreen(1)} />;
  return <div className="mobile-onboarding">
    <button className="mobile-skip" onClick={() => setScreen(1)}>Пропустить</button><Brand />
    <h1>Промпт-радар<br />для ИИ-агентов</h1>
    <p>Классифицирует запросы, находит сценарии использования и показывает, где ИИ реально экономит время.</p>
    <div className="mobile-radar-image"><Image src="/images/prompt-radar.png" alt="Промпт-радар с орбитами запросов" fill sizes="100vw" priority /><span>● Запросы</span><span>● Сценарии</span><span>● Инсайты</span></div>
    <div className="mobile-dots"><i className="active" /><i /><i /></div>
    <button className="mobile-primary" onClick={() => setScreen(1)}>Начать <ArrowRight size={23} /></button><small>Больше возможностей с ИИ</small>
  </div>;
}

export function Landing() {
  return <main className="arvexo-landing">
    <div className="desktop-site">
      <header className="desktop-topbar">
        <nav><a href="#top" aria-label="Arvexo Radar — на главную"><Brand compact /></a><div><a href="#product">Product</a><a href="#solutions">Solutions</a><a href="#results">Results</a><a href="#resources">Resources</a></div><div><Link href="/auth/login">Sign in</Link><Link className="dark-button" href="/auth/login">Get Started <ArrowRight size={16} /></Link></div></nav>
      </header>
      <section className="desktop-landing" id="top">
        <div className="desktop-hero-copy"><h1>From monitoring<br />to <span>AI intelligence.</span></h1><p>Observe. Measure. Explain. Recommend. Scale.<br />Arvexo Radar helps teams understand, improve, and scale their AI systems in production.</p><div className="desktop-actions"><Link className="dark-button" href="/auth/login">Get Started <ArrowRight size={16} /></Link><Link className="watch-button" href="/app"><i>▶</i> Watch Demo</Link></div></div>
        <div className="desktop-hero-art"><Image src="/images/arvexo-architecture.png" alt="Перламутровая архитектура Arvexo Radar" fill sizes="60vw" priority /></div>
        <dl className="desktop-proof"><div><dt>10×</dt><dd>Faster issue detection</dd></div><div><dt>−40%</dt><dd>Operational costs</dd></div><div><dt>+Better AI</dt><dd>for real business</dd></div></dl>
        <footer><span>Trusted by forward-thinking teams</span><span>Smarter AI<br />for a brighter future.</span><span>01 / 03</span></footer>
      </section>

      <section className="landing-section landing-intro" id="product">
        <div className="landing-wrap"><span className="landing-index">01 / Product intelligence</span><div className="landing-intro-grid"><h2>See what your AI systems are actually doing.</h2><p>Radar turns prompt telemetry into a clear operating picture: recurring scenarios, model quality, latency, cost and the places where automation creates measurable value.</p></div><div className="landing-signal-row"><span>Prompts classified</span><span>Scenarios clustered</span><span>ROI explained</span><span>Actions recommended</span></div></div>
      </section>

      <section className="landing-section landing-showcase" id="solutions">
        <div className="landing-wrap"><div className="landing-section-head"><span className="landing-index">02 / Solutions</span><h2>From scattered requests<br />to a map your team can use.</h2></div><div className="landing-visual-grid"><article><div className="landing-image-frame"><Image src="/images/scenario-map.png" alt="Карта кластеров пользовательских сценариев" fill sizes="50vw" /></div><div><span>Scenario map</span><h3>Find repeatable patterns</h3><p>Group similar prompts, identify stable use cases and see which workflows deserve investment.</p></div></article><article><div className="landing-image-frame"><Image src="/images/roi-growth.png" alt="График эффективности и возврата инвестиций" fill sizes="50vw" /></div><div><span>Efficiency &amp; ROI</span><h3>Connect usage to value</h3><p>Compare time saved, operating cost and reliability without hiding the assumptions behind the numbers.</p></div></article></div></div>
      </section>

      <section className="landing-section landing-results" id="results">
        <div className="landing-wrap"><span className="landing-index">03 / Measurable results</span><div className="landing-results-grid"><div><strong>98.2%</strong><span>model health</span><p>Track quality shifts before they become business incidents.</p></div><div><strong>1.4M</strong><span>requests analyzed</span><p>Understand demand across models, departments and scenarios.</p></div><div><strong>320 ms</strong><span>average latency</span><p>Spot slow agents and expensive patterns in one view.</p></div></div></div>
      </section>

      <section className="landing-section landing-final" id="resources">
        <div className="landing-wrap"><div><span className="landing-index">04 / Start with your data</span><h2>Make every AI request<br />work harder.</h2></div><div><p>Connect your telemetry or upload a dataset. Radar will classify prompts, reveal scenarios and produce evidence-linked recommendations.</p><Link className="dark-button" href="/auth/login">Open Arvexo Radar <ArrowRight size={17} /></Link></div></div>
      </section>
      <footer className="landing-footer"><Brand compact /><span>© 2026 Arvexo Radar</span><div><a href="https://arvexo.ru">Arvexo ecosystem</a><a href="#top">Back to top ↑</a></div></footer>
    </div>
    <section className="mobile-landing"><MobileExperience /></section>
  </main>;
}
