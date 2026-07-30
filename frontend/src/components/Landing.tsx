import { useEffect, useRef, useState } from 'react';
import {
  Lightbulb, Globe, FlaskConical, Cpu, Briefcase, Boxes, Scale, Sparkles,
  Banknote, TrendingUp, Users, FileText, ArrowRight, Zap, Activity,
  Network, Layers, ShieldCheck, Rocket, ChevronRight, Quote, Star,
} from 'lucide-react';
import NeuralBackground from './NeuralBackground';
import CrewNetwork from './CrewNetwork';
import ExecutionPipeline from './ExecutionPipeline';
import { CREWS, PIPELINE } from '@/data/crews';
import { Counter, CircularProgress, RadarChart, AreaChart, GradientBar } from './charts';
import { useScrollReveal } from '@/hooks/useScrollReveal';

const CREW_ICONS: Record<string, any> = {
  Lightbulb, Globe, FlaskConical, Cpu, Briefcase, Boxes, Scale, Sparkles,
  Banknote, TrendingUp, Users, FileText,
};

export default function Landing({ onLaunch, onDashboard }: { onLaunch: () => void; onDashboard: () => void }) {
  useScrollReveal();
  const [netActive, setNetActive] = useState(false);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineDone, setPipelineDone] = useState(false);
  const netRef = useRef<HTMLDivElement>(null);
  const pipelineRef = useRef<HTMLDivElement>(null);

  // Auto-start pipeline when scrolled into view
  useEffect(() => {
    const el = pipelineRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !pipelineRunning && !pipelineDone) {
            setPipelineRunning(true);
          }
        });
      },
      { threshold: 0.25 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [pipelineRunning, pipelineDone]);

  return (
    <div className="relative min-h-screen overflow-hidden bg-void">
      {/* ===== HERO ===== */}
      <section className="relative min-h-screen overflow-hidden">
        <div className="absolute inset-0">
          <NeuralBackground density={0.8} />
        </div>
        <div className="absolute inset-0 radial-spotlight" />
        <div className="absolute inset-0 grid-bg opacity-40" />

        <div className="relative z-10 mx-auto flex min-h-screen max-w-7xl flex-col justify-center px-6 pt-24">
          {/* Badge */}
          <div className="mb-8 flex justify-center animate-fade-up">
            <div className="glass flex items-center gap-2 rounded-full px-4 py-1.5">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald" />
              </span>
              <span className="text-xs text-white/70">12 AI Crews · 72 Specialized Agents · Now in Beta</span>
            </div>
          </div>

          {/* Headline */}
          <h1 className="text-center text-5xl font-light leading-[1.05] tracking-tight text-white sm:text-7xl lg:text-8xl animate-fade-up" style={{ animationDelay: '0.1s' }}>
            Transform Startup Ideas
            <br />
            <span className="font-serif italic text-gradient">Into Real Companies</span>
          </h1>

          <p className="mx-auto mt-8 max-w-2xl text-center text-lg leading-relaxed text-white/50 animate-fade-up" style={{ animationDelay: '0.2s' }}>
            The AI Operating System that takes a single idea and orchestrates 12 specialized crews
            through 72 agents — from validation to investor-ready, end to end.
          </p>

          {/* CTAs */}
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row animate-fade-up" style={{ animationDelay: '0.3s' }}>
            <button onClick={onLaunch} className="btn-primary group flex items-center gap-2 rounded-full px-7 py-3.5 text-base font-medium">
              Ignite Your Startup
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </button>
            <button onClick={onDashboard} className="btn-ghost flex items-center gap-2 rounded-full px-7 py-3.5 text-base text-white/80">
              <Activity className="h-4 w-4" />
              View Mission Control
            </button>
          </div>

          {/* Stats strip */}
          <div className="mt-16 grid grid-cols-2 gap-6 sm:grid-cols-4 animate-fade-up" style={{ animationDelay: '0.4s' }}>
            {[
              { v: 12, l: 'AI Crews', c: '#2d7ff9' },
              { v: 72, l: 'Specialized Agents', c: '#8b5cf6' },
              { v: 340, l: 'Startups Ignited', c: '#10b981' },
              { v: 94, l: 'Investor-Ready %', c: '#fb923c' },
            ].map((s) => (
              <div key={s.l} className="text-center">
                <div className="text-4xl font-light text-white">
                  <Counter to={s.v} suffix={s.l.includes('%') ? '%' : ''} />
                </div>
                <div className="mt-1 text-xs uppercase tracking-wider text-white/40">{s.l}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Scroll cue */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-float">
          <div className="flex h-10 w-6 items-start justify-center rounded-full border border-white/20 p-1.5">
            <div className="h-2 w-1 rounded-full bg-white/40" />
          </div>
        </div>
      </section>

      {/* ===== PLATFORM OVERVIEW ===== */}
      <section id="platform" className="relative py-32">
        <div className="absolute inset-0 bg-gradient-to-b from-void via-charcoal to-void" />
        <div className="relative mx-auto max-w-7xl px-6">
          <div className="reveal mx-auto max-w-3xl text-center">
            <span className="font-mono text-xs uppercase tracking-[0.3em] text-electric">The Operating System</span>
            <h2 className="mt-4 text-4xl font-light leading-tight text-white sm:text-6xl">
              Not another AI tool.
              <br />
              <span className="font-serif italic text-gradient-cool">An entire crew.</span>
            </h2>
            <p className="mt-6 text-lg text-white/50">
              Most platforms give you a single chat window. Startup Igniter deploys a coordinated
              team of 72 AI agents across 12 crews — each an expert in its domain — working in
              parallel with shared memory to build your company while you watch.
            </p>
          </div>

          {/* Feature trio - asymmetric */}
          <div className="mt-20 grid gap-6 lg:grid-cols-12">
            {/* Large card */}
            <div className="reveal gradient-border noise group relative overflow-hidden rounded-3xl bg-charcoal/50 p-8 backdrop-blur-sm lg:col-span-7 lg:row-span-2">
              <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-electric/10 blur-3xl transition-all duration-700 group-hover:bg-electric/20" />
              <Network className="h-8 w-8 text-electric" />
              <h3 className="mt-6 text-2xl font-light text-white">Coordinated Crew Intelligence</h3>
              <p className="mt-3 max-w-md text-white/50">
                Crews don't work in isolation. They share a living memory layer — every insight from
                Market Research flows into Business Planning, every patent finding informs Technical
                Feasibility. The system thinks as one.
              </p>
              <div className="mt-8 grid grid-cols-3 gap-3">
                {['Shared Memory', 'Live Sync', 'Cross-Crew'].map((t, i) => (
                  <div key={t} className="rounded-xl border border-white/5 bg-white/[0.02] p-3 text-center">
                    <div className="font-mono text-xs text-white/70">{t}</div>
                  </div>
                ))}
              </div>
              {/* Mini network viz — enlarged so nodes aren't cramped */}
              <div className="mt-8 h-72 rounded-2xl border border-white/5 bg-void/40 p-2">
                <CrewNetwork compact active />
              </div>
            </div>

            {/* Top right */}
            <div className="reveal gradient-border noise group relative overflow-hidden rounded-3xl bg-charcoal/50 p-8 backdrop-blur-sm lg:col-span-5">
              <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-violet/10 blur-3xl" />
              <Layers className="h-8 w-8 text-violet" />
              <h3 className="mt-6 text-2xl font-light text-white">12-Stage Pipeline</h3>
              <p className="mt-3 text-white/50">
                From raw idea to investor-ready report, every stage is executed, validated, and
                documented automatically.
              </p>
              <div className="mt-6 space-y-2">
                {PIPELINE.slice(0, 4).map((s, i) => (
                  <div key={s.id} className="flex items-center gap-2 text-xs">
                    <span className="font-mono text-white/30">{String(s.id).padStart(2, '0')}</span>
                    <span className="text-white/70">{s.name}</span>
                    {i < 3 && <ChevronRight className="h-3 w-3 text-white/20" />}
                  </div>
                ))}
                <div className="text-xs text-white/30">+ 8 more stages</div>
              </div>
            </div>

            {/* Bottom right */}
            <div className="reveal gradient-border noise group relative overflow-hidden rounded-3xl bg-charcoal/50 p-8 backdrop-blur-sm lg:col-span-5">
              <div className="absolute -right-10 -bottom-10 h-40 w-40 rounded-full bg-emerald/10 blur-3xl" />
              <ShieldCheck className="h-8 w-8 text-emerald" />
              <h3 className="mt-6 text-2xl font-light text-white">Investor-Ready Output</h3>
              <p className="mt-3 text-white/50">
                Every mission ends with a complete pack — deck, financials, IP strategy, and a
                64-page report your investors will actually read.
              </p>
              <div className="mt-6 flex items-center gap-3">
                <div className="flex -space-x-2">
                  {['#2d7ff9', '#8b5cf6', '#10b981', '#fb923c'].map((c) => (
                    <div key={c} className="h-8 w-8 rounded-full border-2 border-charcoal" style={{ background: c }} />
                  ))}
                </div>
                <span className="text-xs text-white/40">Deck · Financials · IP · Report</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== CREW NETWORK ===== */}
      <section id="crews" className="relative py-32">
        <div className="absolute inset-0 bg-gradient-to-b from-void via-midnight to-void" />
        <div className="relative mx-auto max-w-7xl px-6">
          <div className="reveal grid items-center gap-12 lg:grid-cols-2">
            <div>
              <span className="font-mono text-xs uppercase tracking-[0.3em] text-violet">The Crew Network</span>
              <h2 className="mt-4 text-4xl font-light leading-tight text-white sm:text-5xl">
                72 agents.
                <br />
                <span className="font-serif italic text-gradient">One mission.</span>
              </h2>
              <p className="mt-6 text-lg text-white/50">
                Each crew is a cluster of six specialized agents. Hover the network to meet them.
                When a mission runs, nodes light up, data flows between crews, and memory syncs
                across the entire system in real time.
              </p>
              <button
                onClick={() => setNetActive((v) => !v)}
                className="mt-8 btn-primary flex items-center gap-2 rounded-full px-6 py-3 text-sm font-medium"
              >
                <Zap className="h-4 w-4" />
                {netActive ? 'Pause Sync' : 'Activate Network'}
              </button>

              {/* Crew legend */}
              <div className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-3">
                {CREWS.slice(0, 6).map((c) => {
                  const Icon = CREW_ICONS[c.icon];
                  return (
                    <div key={c.id} className="flex items-center gap-2.5 rounded-xl border border-white/5 bg-white/[0.02] p-2.5">
                      <div className="flex h-7 w-7 items-center justify-center rounded-lg" style={{ background: `${c.color}22` }}>
                        {Icon && <Icon className="h-3.5 w-3.5" style={{ color: c.color }} />}
                      </div>
                      <span className="text-xs text-white/70">{c.name}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div ref={netRef} className="reveal relative aspect-square w-full">
              <div className="absolute inset-0 rounded-3xl border border-white/5 bg-gradient-to-br from-charcoal/40 to-void/40 backdrop-blur-sm">
                <CrewNetwork active={netActive} />
              </div>
            </div>
          </div>

          {/* Full crew grid */}
          <div className="mt-24 reveal">
            <h3 className="text-center text-2xl font-light text-white">All 12 Crews</h3>
            <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {CREWS.map((crew, i) => {
                const Icon = CREW_ICONS[crew.icon];
                return (
                  <div
                    key={crew.id}
                    className="gradient-border-hover noise group relative overflow-hidden rounded-2xl bg-charcoal/40 p-5 backdrop-blur-sm transition-all duration-500 hover:-translate-y-1"
                    style={{ animationDelay: `${i * 50}ms` }}
                  >
                    <div
                      className="absolute -right-8 -top-8 h-24 w-24 rounded-full opacity-20 blur-2xl transition-opacity duration-500 group-hover:opacity-40"
                      style={{ background: crew.color }}
                    />
                    <div className="relative flex items-center justify-between">
                      <div
                        className="flex h-10 w-10 items-center justify-center rounded-xl transition-transform duration-500 group-hover:scale-110"
                        style={{ background: `linear-gradient(135deg, ${crew.color}33, ${crew.color2}11)`, border: `1px solid ${crew.color}44` }}
                      >
                        {Icon && <Icon className="h-5 w-5" style={{ color: crew.color }} />}
                      </div>
                      <span className="font-mono text-[10px] text-white/30">{crew.short}</span>
                    </div>
                    <h4 className="relative mt-4 text-base font-medium text-white">{crew.name}</h4>
                    <p className="relative mt-1 text-xs text-white/40">{crew.domain}</p>
                    <div className="relative mt-4 space-y-1.5">
                      {crew.agents.slice(0, 3).map((a) => (
                        <div key={a.id} className="flex items-center gap-2 text-[11px] text-white/50">
                          <span className="h-1 w-1 rounded-full" style={{ background: crew.color }} />
                          {a.name}
                        </div>
                      ))}
                      <div className="text-[10px] text-white/30">+ {crew.agents.length - 3} more agents</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* ===== PIPELINE ===== */}
      <section id="pipeline" className="relative py-32">
        <div className="absolute inset-0 bg-gradient-to-b from-void via-charcoal to-void" />
        <div className="relative mx-auto max-w-5xl px-6">
          <div className="reveal text-center">
            <span className="font-mono text-xs uppercase tracking-[0.3em] text-orange">Execution Pipeline</span>
            <h2 className="mt-4 text-4xl font-light leading-tight text-white sm:text-5xl">
              From spark to <span className="font-serif italic text-gradient-warm">investor-ready</span>
            </h2>
            <p className="mx-auto mt-6 max-w-2xl text-lg text-white/50">
              Twelve stages, executed in sequence. Each crew owns its stage, hands off to the next,
              and leaves a fully documented trail behind.
            </p>
            {/* Replay button shown after pipeline finishes */}
            {pipelineDone && (
              <button
                onClick={() => { setPipelineDone(false); setPipelineRunning(false); setTimeout(() => setPipelineRunning(true), 80); }}
                className="mt-8 btn-primary inline-flex items-center gap-2 rounded-full px-6 py-3 text-sm font-medium"
              >
                <Rocket className="h-4 w-4" />
                Replay Pipeline
              </button>
            )}
            {!pipelineDone && pipelineRunning && (
              <div className="mt-8 inline-flex items-center gap-2 rounded-full border border-orange/30 bg-orange/10 px-5 py-2.5 text-sm text-orange">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-orange opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-orange" />
                </span>
                Pipeline Running…
              </div>
            )}
            {!pipelineDone && !pipelineRunning && (
              <div className="mt-8 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-5 py-2.5 text-sm text-white/40">
                Scroll to auto-launch pipeline
              </div>
            )}
          </div>

          <div ref={pipelineRef} className="mt-16">
            <ExecutionPipeline
              running={pipelineRunning}
              onComplete={() => { setPipelineDone(true); setPipelineRunning(false); }}
            />
          </div>
        </div>
      </section>

      {/* ===== DASHBOARD PREVIEW ===== */}
      <section id="dashboard" className="relative py-32">
        <div className="absolute inset-0 bg-gradient-to-b from-void via-midnight to-void" />
        <div className="relative mx-auto max-w-7xl px-6">
          <div className="reveal text-center">
            <span className="font-mono text-xs uppercase tracking-[0.3em] text-teal">Mission Control</span>
            <h2 className="mt-4 text-4xl font-light leading-tight text-white sm:text-5xl">
              Your startup, <span className="font-serif italic text-gradient-cool">at a glance</span>
            </h2>
            <p className="mx-auto mt-6 max-w-2xl text-lg text-white/50">
              An immersive workspace — not a boring sidebar layout. Every metric, every crew, every
              signal in one living view.
            </p>
          </div>

          {/* Preview mockup */}
          <div className="reveal mt-16 gradient-border noise relative overflow-hidden rounded-3xl bg-charcoal/40 p-1 backdrop-blur-sm">
            <div className="rounded-[22px] bg-void/60 p-6">
              <div className="grid gap-4 lg:grid-cols-12">
                {/* Health meter */}
                <div className="lg:col-span-3">
                  <div className="gradient-border noise rounded-2xl bg-charcoal/50 p-5">
                    <div className="text-xs uppercase tracking-wider text-white/40">Startup Health</div>
                    <div className="mt-4 flex justify-center">
                      <CircularProgress value={87} size={130} color="#10b981" color2="#14b8a6" sublabel="Health" />
                    </div>
                    <div className="mt-4 space-y-2">
                      {[
                        { l: 'Team', v: 92, c: '#2d7ff9' },
                        { l: 'Product', v: 78, c: '#8b5cf6' },
                        { l: 'Market', v: 85, c: '#10b981' },
                      ].map((r) => (
                        <div key={r.l}>
                          <div className="mb-1 flex justify-between text-[10px] text-white/40">
                            <span>{r.l}</span><span>{r.v}%</span>
                          </div>
                          <GradientBar value={r.v} color={r.c} color2={r.c} />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Radar + area */}
                <div className="lg:col-span-5">
                  <div className="gradient-border noise h-full rounded-2xl bg-charcoal/50 p-5">
                    <div className="flex items-center justify-between">
                      <div className="text-xs uppercase tracking-wider text-white/40">Competitor Radar</div>
                      <span className="font-mono text-[10px] text-emerald">● LIVE</span>
                    </div>
                    <div className="mt-2 flex justify-center">
                      <RadarChart
                        data={[
                          { label: 'Tech', value: 82 },
                          { label: 'Brand', value: 64 },
                          { label: 'Price', value: 90 },
                          { label: 'Reach', value: 71 },
                          { label: 'Team', value: 88 },
                          { label: 'IP', value: 55 },
                        ]}
                        size={240}
                        color="#ec4899"
                        color2="#8b5cf6"
                      />
                    </div>
                  </div>
                </div>

                {/* Funding probability */}
                <div className="lg:col-span-4">
                  <div className="gradient-border noise h-full rounded-2xl bg-charcoal/50 p-5">
                    <div className="text-xs uppercase tracking-wider text-white/40">Funding Probability</div>
                    <div className="mt-4 flex items-center gap-4">
                      <CircularProgress value={73} size={90} stroke={7} color="#fb923c" color2="#ec4899" sublabel="Seed" />
                      <div className="flex-1 space-y-2">
                        {[
                          { l: 'Pre-Seed', v: 95 },
                          { l: 'Seed', v: 73 },
                          { l: 'Series A', v: 41 },
                        ].map((r) => (
                          <div key={r.l}>
                            <div className="mb-1 flex justify-between text-[10px] text-white/40">
                              <span>{r.l}</span><span>{r.v}%</span>
                            </div>
                            <GradientBar value={r.v} color="#fb923c" color2="#ec4899" height={4} />
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="mt-4">
                      <div className="mb-1 text-[10px] text-white/40">Valuation Trend</div>
                      <AreaChart data={[12, 18, 15, 24, 30, 28, 38, 42, 48]} color="#fb923c" color2="#ec4899" height={50} />
                    </div>
                  </div>
                </div>

                {/* Timeline */}
                <div className="lg:col-span-8">
                  <div className="gradient-border noise rounded-2xl bg-charcoal/50 p-5">
                    <div className="flex items-center justify-between">
                      <div className="text-xs uppercase tracking-wider text-white/40">Mission Timeline</div>
                      <span className="font-mono text-[10px] text-white/30">Week 1 — 12</span>
                    </div>
                    <div className="mt-5 flex items-center gap-1">
                      {PIPELINE.map((s, i) => (
                        <div key={s.id} className="flex-1">
                          <div
                            className="h-10 rounded-md transition-all duration-500"
                            style={{
                              background: i < 7
                                ? `linear-gradient(180deg, ${CREWS[s.crew - 1].color}, ${CREWS[s.crew - 1].color2})`
                                : 'rgba(255,255,255,0.04)',
                              boxShadow: i < 7 ? `0 0 12px -2px ${CREWS[s.crew - 1].color}66` : 'none',
                            }}
                          />
                          <div className="mt-1.5 text-[8px] text-white/30">{s.short}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* TRL */}
                <div className="lg:col-span-4">
                  <div className="gradient-border noise h-full rounded-2xl bg-charcoal/50 p-5">
                    <div className="text-xs uppercase tracking-wider text-white/40">TRL Indicator</div>
                    <div className="mt-3 flex items-end gap-1">
                      {Array.from({ length: 9 }).map((_, i) => (
                        <div
                          key={i}
                          className="flex-1 rounded-t transition-all duration-700"
                          style={{
                            height: `${20 + i * 8}px`,
                            background: i < 6 ? `linear-gradient(180deg, #2d7ff9, #14b8a6)` : 'rgba(255,255,255,0.06)',
                            boxShadow: i < 6 ? `0 0 8px -2px #2d7ff966` : 'none',
                          }}
                        />
                      ))}
                    </div>
                    <div className="mt-2 flex justify-between text-[9px] text-white/30">
                      <span>TRL 1</span><span className="text-teal">TRL 6</span><span>TRL 9</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-12 text-center">
            <button onClick={onDashboard} className="btn-primary inline-flex items-center gap-2 rounded-full px-7 py-3.5 text-base font-medium">
              Open Full Dashboard
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </section>

      {/* ===== TESTIMONIALS ===== */}
      <section className="relative py-32">
        <div className="absolute inset-0 bg-gradient-to-b from-void via-charcoal to-void" />
        <div className="relative mx-auto max-w-7xl px-6">
          <div className="reveal text-center">
            <span className="font-mono text-xs uppercase tracking-[0.3em] text-pink">Founders</span>
            <h2 className="mt-4 text-4xl font-light text-white sm:text-5xl">
              They shipped in <span className="font-serif italic text-gradient">weeks, not years</span>
            </h2>
          </div>
          <div className="mt-16 grid gap-6 md:grid-cols-3">
            {[
              { q: 'I had an idea on Monday. By Friday I had a validated market, a tech stack, and a pitch deck that closed our pre-seed.', n: 'Maya Chen', r: 'Founder, Lumen Health', c: '#2d7ff9' },
              { q: 'The crew network is unreal. It felt like having a full team of 72 experts working in parallel — because it was.', n: 'Dev Patel', r: 'CEO, Orbit Labs', c: '#8b5cf6' },
              { q: 'We walked into our seed round with a 64-page report no other pre-seed company had. Investors were stunned.', n: 'Sofia Reyes', r: 'Founder, Nuvora', c: '#10b981' },
            ].map((t, i) => (
              <div key={i} className="reveal gradient-border noise rounded-2xl bg-charcoal/40 p-6 backdrop-blur-sm">
                <Quote className="h-6 w-6" style={{ color: t.c }} />
                <p className="mt-4 text-sm leading-relaxed text-white/70">{t.q}</p>
                <div className="mt-6 flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full" style={{ background: `linear-gradient(135deg, ${t.c}, ${t.c}88)` }}>
                    <span className="text-sm font-medium text-white">{t.n[0]}</span>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">{t.n}</div>
                    <div className="text-xs text-white/40">{t.r}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== CTA ===== */}
      <section className="relative py-32">
        <div className="absolute inset-0">
          <NeuralBackground density={0.5} />
        </div>
        <div className="absolute inset-0 radial-spotlight" />
        <div className="relative mx-auto max-w-3xl px-6 text-center">
          <div className="reveal">
            <Rocket className="mx-auto h-10 w-10 text-electric animate-float" />
            <h2 className="mt-8 text-5xl font-light leading-tight text-white sm:text-6xl">
              Your startup is
              <br />
              <span className="font-serif italic text-gradient">one idea away</span>
            </h2>
            <p className="mx-auto mt-6 max-w-xl text-lg text-white/50">
              Launch a mission today. Watch 72 agents build your company in real time.
            </p>
            <button onClick={onLaunch} className="mt-10 btn-primary inline-flex items-center gap-2 rounded-full px-8 py-4 text-lg font-medium">
              Ignite Your Startup
              <ArrowRight className="h-5 w-5" />
            </button>
          </div>
        </div>
      </section>

      {/* ===== FOOTER ===== */}
      <footer className="relative border-t border-white/5 bg-void py-12">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex flex-col items-center justify-between gap-6 md:flex-row">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-electric to-violet">
                <Rocket className="h-4 w-4 text-white" />
              </div>
              <span className="text-sm font-medium text-white">Startup Igniter AI</span>
            </div>
            <div className="flex gap-6 text-xs text-white/40">
              <a href="#" className="hover:text-white">Platform</a>
              <a href="#" className="hover:text-white">Crews</a>
              <a href="#" className="hover:text-white">Pricing</a>
              <a href="#" className="hover:text-white">Docs</a>
            </div>
            <div className="text-xs text-white/30">© 2026 Startup Igniter AI — Built for founders</div>
          </div>
        </div>
      </footer>
    </div>
  );
}
