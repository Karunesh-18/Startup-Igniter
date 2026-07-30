import { useEffect, useState } from 'react';
import {
  Rocket, ArrowLeft, Activity, Zap, Brain, Network, TrendingUp,
  ShieldCheck, FileText, Users, Lightbulb, Cpu, Boxes, Banknote,
  Globe, FlaskConical, Briefcase, Scale, Sparkles, ChevronRight,
  Clock, Target, AlertTriangle, CheckCircle2, Cpu as CpuIcon,
} from 'lucide-react';
import NeuralBackground from './NeuralBackground';
import CrewNetwork from './CrewNetwork';
import { CREWS, PIPELINE } from '@/data/crews';
import { Counter, CircularProgress, RadarChart, AreaChart, GradientBar, Heatmap } from './charts';
import { useScrollReveal } from '@/hooks/useScrollReveal';

const CREW_ICONS: Record<string, any> = {
  Lightbulb, Globe, FlaskConical, Cpu, Briefcase, Boxes, Scale, Sparkles,
  Banknote, TrendingUp, Users, FileText,
};

export default function Dashboard({ onBack, onLaunch }: { onBack: () => void; onLaunch: () => void }) {
  useScrollReveal();
  const [activeCrew, setActiveCrew] = useState<number | null>(1);
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const activeCrewData = CREWS.find((c) => c.id === activeCrew);

  return (
    <div className="relative min-h-screen overflow-hidden bg-void">
      <div className="absolute inset-0 opacity-30">
        <NeuralBackground density={0.3} />
      </div>

      {/* Top bar */}
      <div className="sticky top-0 z-40 border-b border-white/5 bg-void/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between px-6 py-3">
          <div className="flex items-center gap-4">
            <button onClick={onBack} className="flex items-center gap-2 text-sm text-white/50 transition-colors hover:text-white">
              <ArrowLeft className="h-4 w-4" />
              <span className="hidden sm:inline">Back to site</span>
            </button>
            <div className="h-5 w-px bg-white/10" />
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-electric to-violet">
                <Rocket className="h-4 w-4 text-white" />
              </div>
              <div className="leading-none">
                <div className="text-sm font-semibold text-white">Mission Control</div>
                <div className="font-mono text-[9px] uppercase tracking-wider text-white/40">Project · Lumen Health</div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden items-center gap-2 rounded-full border border-emerald/30 bg-emerald/10 px-3 py-1.5 sm:flex">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald" />
              </span>
              <span className="text-xs text-emerald">All systems nominal</span>
            </div>
            <div className="font-mono text-xs text-white/40 tabular-nums">
              {time.toLocaleTimeString('en-US', { hour12: false })}
            </div>
            <button onClick={onLaunch} className="btn-primary flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium">
              <Zap className="h-3.5 w-3.5" />
              New Mission
            </button>
          </div>
        </div>
      </div>

      {/* Main grid */}
      <div className="relative z-10 mx-auto max-w-[1600px] px-6 py-6">
        {/* Row 1: Hero metrics */}
        <div className="grid gap-4 lg:grid-cols-12">
          {/* Startup Health Meter */}
          <div className="gradient-border noise relative overflow-hidden rounded-3xl bg-charcoal/50 p-6 backdrop-blur-sm lg:col-span-4">
            <div className="absolute -right-12 -top-12 h-40 w-40 rounded-full bg-emerald/10 blur-3xl" />
            <div className="relative flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-wider text-white/40">Startup Health</div>
                <div className="mt-1 text-3xl font-light text-white">
                  <Counter to={87} /> <span className="text-lg text-white/40">/ 100</span>
                </div>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald to-teal glow-emerald">
                <Activity className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="relative mt-5 space-y-3">
              {[
                { l: 'Team Strength', v: 92, c: '#2d7ff9' },
                { l: 'Product Maturity', v: 78, c: '#8b5cf6' },
                { l: 'Market Fit', v: 85, c: '#10b981' },
                { l: 'Capital Runway', v: 64, c: '#fb923c' },
              ].map((r) => (
                <div key={r.l}>
                  <div className="mb-1.5 flex justify-between text-[11px]">
                    <span className="text-white/50">{r.l}</span>
                    <span className="font-mono text-white/70">{r.v}%</span>
                  </div>
                  <GradientBar value={r.v} color={r.c} color2={r.c} />
                </div>
              ))}
            </div>
          </div>

          {/* Innovation Gauge */}
          <div className="gradient-border noise relative overflow-hidden rounded-3xl bg-charcoal/50 p-6 backdrop-blur-sm lg:col-span-4">
            <div className="absolute -right-12 -top-12 h-40 w-40 rounded-full bg-violet/10 blur-3xl" />
            <div className="relative flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-wider text-white/40">Innovation Gauge</div>
                <div className="mt-1 text-3xl font-light text-white">
                  <Counter to={91} /> <span className="text-lg text-white/40">/ 100</span>
                </div>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet to-indigo glow-violet">
                <Brain className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="relative mt-5 flex items-center gap-4">
              <CircularProgress value={91} size={90} stroke={7} color="#8b5cf6" color2="#6366f1" sublabel="Score" />
              <div className="flex-1 space-y-2 text-xs">
                <div className="flex justify-between"><span className="text-white/50">Novelty</span><span className="font-mono text-white/70">94</span></div>
                <div className="flex justify-between"><span className="text-white/50">Defensibility</span><span className="font-mono text-white/70">88</span></div>
                <div className="flex justify-between"><span className="text-white/50">Timing</span><span className="font-mono text-white/70">90</span></div>
              </div>
            </div>
          </div>

          {/* Funding Probability */}
          <div className="gradient-border noise relative overflow-hidden rounded-3xl bg-charcoal/50 p-6 backdrop-blur-sm lg:col-span-4">
            <div className="absolute -right-12 -top-12 h-40 w-40 rounded-full bg-orange/10 blur-3xl" />
            <div className="relative flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-wider text-white/40">Funding Probability</div>
                <div className="mt-1 text-3xl font-light text-white">
                  <Counter to={73} suffix="%" />
                </div>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-orange to-pink glow-pink">
                <Banknote className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="relative mt-5 space-y-2.5">
              {[
                { l: 'Pre-Seed', v: 95, c: '#10b981' },
                { l: 'Seed', v: 73, c: '#fb923c' },
                { l: 'Series A', v: 41, c: '#ec4899' },
              ].map((r) => (
                <div key={r.l}>
                  <div className="mb-1 flex justify-between text-[11px]">
                    <span className="text-white/50">{r.l}</span>
                    <span className="font-mono text-white/70">{r.v}%</span>
                  </div>
                  <GradientBar value={r.v} color={r.c} color2={r.c} height={5} />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Row 2: Crew Network + side panel */}
        <div className="mt-4 grid gap-4 lg:grid-cols-12">
          {/* Crew Network - large */}
          <div className="gradient-border noise relative overflow-hidden rounded-3xl bg-charcoal/40 backdrop-blur-sm lg:col-span-8">
            <div className="flex items-center justify-between border-b border-white/5 px-6 py-4">
              <div className="flex items-center gap-2">
                <Network className="h-4 w-4 text-electric" />
                <span className="text-sm font-medium text-white">AI Crew Network</span>
                <span className="font-mono text-[10px] text-white/30">72 agents · 12 crews</span>
              </div>
              <span className="font-mono text-[10px] text-emerald">● SYNCING</span>
            </div>
            <div className="aspect-[16/10] w-full p-4">
              <CrewNetwork active />
            </div>
          </div>

          {/* Active crew detail */}
          <div className="gradient-border noise relative overflow-hidden rounded-3xl bg-charcoal/50 p-6 backdrop-blur-sm lg:col-span-4">
            <div className="text-xs uppercase tracking-wider text-white/40">Active Crew</div>
            {activeCrewData && (
              <>
                <div className="mt-3 flex items-center gap-3">
                  <div
                    className="flex h-12 w-12 items-center justify-center rounded-2xl"
                    style={{ background: `linear-gradient(135deg, ${activeCrewData.color}33, ${activeCrewData.color2}11)`, border: `1px solid ${activeCrewData.color}44` }}
                  >
                    {(() => { const I = CREW_ICONS[activeCrewData.icon]; return I ? <I className="h-6 w-6" style={{ color: activeCrewData.color }} /> : null; })()}
                  </div>
                  <div>
                    <div className="text-base font-medium text-white">{activeCrewData.name}</div>
                    <div className="text-xs text-white/40">{activeCrewData.domain}</div>
                  </div>
                </div>
                <div className="mt-5 space-y-2">
                  {activeCrewData.agents.map((a) => (
                    <div key={a.id} className="flex items-center justify-between rounded-xl border border-white/5 bg-white/[0.02] p-2.5">
                      <div className="flex items-center gap-2">
                        <span className="h-1.5 w-1.5 rounded-full animate-pulse-glow" style={{ background: activeCrewData.color }} />
                        <span className="text-xs text-white/70">{a.name}</span>
                      </div>
                      <span className="font-mono text-[9px] text-white/30">{a.role}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
            <div className="mt-5 flex flex-wrap gap-1.5">
              {CREWS.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setActiveCrew(c.id)}
                  className={`h-7 w-7 rounded-lg border transition-all ${activeCrew === c.id ? 'scale-110' : 'opacity-50 hover:opacity-100'}`}
                  style={{ borderColor: activeCrew === c.id ? c.color : 'rgba(255,255,255,0.1)', background: activeCrew === c.id ? `${c.color}22` : 'transparent' }}
                  title={c.name}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Row 3: Asymmetric widgets */}
        <div className="mt-4 grid gap-4 lg:grid-cols-12">
          {/* Competitor Radar */}
          <div className="gradient-border noise relative overflow-hidden rounded-3xl bg-charcoal/50 p-6 backdrop-blur-sm lg:col-span-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4 text-pink" />
                <span className="text-sm font-medium text-white">Competitor Radar</span>
              </div>
              <span className="font-mono text-[10px] text-white/30">6 dimensions</span>
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
                size={260}
                color="#ec4899"
                color2="#8b5cf6"
              />
            </div>
          </div>

          {/* Mission Timeline */}
          <div className="gradient-border noise relative overflow-hidden rounded-3xl bg-charcoal/50 p-6 backdrop-blur-sm lg:col-span-7">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-electric" />
                <span className="text-sm font-medium text-white">Mission Timeline</span>
              </div>
              <span className="font-mono text-[10px] text-white/30">Week 1 — 12</span>
            </div>
            <div className="mt-6 space-y-3">
              {PIPELINE.map((s, i) => {
                const crew = CREWS[s.crew - 1];
                const status = i < 7 ? 'done' : i === 7 ? 'running' : 'pending';
                return (
                  <div key={s.id} className="flex items-center gap-3">
                    <div
                      className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-[10px] font-mono transition-all"
                      style={{
                        background: status === 'done' ? `linear-gradient(135deg, ${crew.color}, ${crew.color2})` : status === 'running' ? `${crew.color}22` : 'rgba(255,255,255,0.03)',
                        border: `1px solid ${status !== 'pending' ? crew.color + '44' : 'rgba(255,255,255,0.06)'}`,
                        boxShadow: status === 'running' ? `0 0 12px -2px ${crew.color}` : 'none',
                      }}
                    >
                      {status === 'done' ? <CheckCircle2 className="h-4 w-4 text-white" /> : status === 'running' ? <span className="h-2 w-2 rounded-full bg-white animate-pulse" /> : <span className="text-white/30">{i + 1}</span>}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className={`text-sm ${status === 'pending' ? 'text-white/40' : 'text-white'}`}>{s.name}</span>
                        <span className="font-mono text-[10px]" style={{ color: status === 'done' ? '#10b981' : status === 'running' ? crew.color : 'rgba(255,255,255,0.3)' }}>
                          {status === 'done' ? 'COMPLETE' : status === 'running' ? 'RUNNING' : 'QUEUED'}
                        </span>
                      </div>
                      {status === 'running' && (
                        <div className="mt-1.5">
                          <GradientBar value={68} color={crew.color} color2={crew.color2} height={3} />
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Row 4: Three widgets */}
        <div className="mt-4 grid gap-4 lg:grid-cols-12">
          {/* TRL Indicator */}
          <div className="gradient-border noise relative overflow-hidden rounded-3xl bg-charcoal/50 p-6 backdrop-blur-sm lg:col-span-3">
            <div className="flex items-center gap-2">
              <CpuIcon className="h-4 w-4 text-teal" />
              <span className="text-sm font-medium text-white">TRL Indicator</span>
            </div>
            <div className="mt-6 flex items-end gap-1.5">
              {Array.from({ length: 9 }).map((_, i) => (
                <div
                  key={i}
                  className="flex-1 rounded-t transition-all duration-700"
                  style={{
                    height: `${24 + i * 10}px`,
                    background: i < 6 ? `linear-gradient(180deg, #2d7ff9, #14b8a6)` : 'rgba(255,255,255,0.06)',
                    boxShadow: i < 6 ? `0 0 10px -2px #2d7ff966` : 'none',
                  }}
                />
              ))}
            </div>
            <div className="mt-2 flex justify-between text-[9px] text-white/30">
              <span>TRL 1</span><span className="font-medium text-teal">TRL 6 ●</span><span>TRL 9</span>
            </div>
            <div className="mt-4 text-xs text-white/50">
              Technology Readiness Level — currently at <span className="font-mono text-teal">6 / 9</span>
            </div>
          </div>

          {/* Research Timeline / Heatmap */}
          <div className="gradient-border noise relative overflow-hidden rounded-3xl bg-charcoal/50 p-6 backdrop-blur-sm lg:col-span-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FlaskConical className="h-4 w-4 text-violet" />
                <span className="text-sm font-medium text-white">Research Activity</span>
              </div>
              <span className="font-mono text-[10px] text-white/30">12 weeks · daily</span>
            </div>
            <div className="mt-6">
              <Heatmap rows={7} cols={12} color="#8b5cf6" />
            </div>
            <div className="mt-4 flex items-center gap-4 text-[10px] text-white/40">
              <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-white/5" />Idle</span>
              <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-violet/40" />Active</span>
              <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-sm bg-violet" />Intense</span>
            </div>
          </div>

          {/* Patent Map */}
          <div className="gradient-border noise relative overflow-hidden rounded-3xl bg-charcoal/50 p-6 backdrop-blur-sm lg:col-span-4">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-emerald" />
              <span className="text-sm font-medium text-white">Patent Landscape</span>
            </div>
            <div className="mt-4 space-y-3">
              {[
                { l: 'Prior Art Found', v: 47, c: '#10b981' },
                { l: 'White Space', v: 7, c: '#2d7ff9' },
                { l: 'Filings Drafted', v: 3, c: '#8b5cf6' },
                { l: 'Citations Tracked', v: 128, c: '#fb923c' },
              ].map((r) => (
                <div key={r.l} className="flex items-center justify-between">
                  <span className="text-xs text-white/50">{r.l}</span>
                  <span className="font-mono text-lg font-light" style={{ color: r.c }}>
                    <Counter to={r.v} />
                  </span>
                </div>
              ))}
            </div>
            <div className="mt-5 rounded-xl border border-emerald/20 bg-emerald/5 p-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald" />
                <span className="text-xs text-emerald">IP strategy secured</span>
              </div>
              <p className="mt-1 text-[11px] text-white/40">3 provisional patents filed. Freedom-to-operate confirmed.</p>
            </div>
          </div>
        </div>

        {/* Row 5: Memory Explorer + Growth */}
        <div className="mt-4 grid gap-4 lg:grid-cols-12">
          {/* Memory Explorer */}
          <div className="gradient-border noise relative overflow-hidden rounded-3xl bg-charcoal/50 p-6 backdrop-blur-sm lg:col-span-7">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="h-4 w-4 text-indigo" />
                <span className="text-sm font-medium text-white">Memory Explorer</span>
              </div>
              <span className="font-mono text-[10px] text-white/30">Shared context · all crews</span>
            </div>
            <div className="mt-5 space-y-2.5">
              {[
                { crew: 'Idea Validation', msg: 'Validated 11/14 hypotheses. Core risk: distribution channel.', t: '2m ago', c: '#2d7ff9' },
                { crew: 'Market Research', msg: 'TAM revised to $4.2B. ICP narrowed to mid-market clinics.', t: '5m ago', c: '#14b8a6' },
                { crew: 'Research & Patent', msg: '3 white-space patents identified. Prior art cleared.', t: '12m ago', c: '#8b5cf6' },
                { crew: 'Technical Feasibility', msg: 'Stack finalized. Estimated 42ms p99 latency at scale.', t: '18m ago', c: '#6366f1' },
                { crew: 'Business Planning', msg: 'SaaS model selected. 78% gross margin projected.', t: '24m ago', c: '#fb923c' },
              ].map((m, i) => (
                <div key={i} className="flex gap-3 rounded-xl border border-white/5 bg-white/[0.02] p-3 transition-all hover:border-white/10">
                  <div className="mt-1 h-2 w-2 flex-shrink-0 rounded-full animate-pulse-glow" style={{ background: m.c }} />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium" style={{ color: m.c }}>{m.crew}</span>
                      <span className="font-mono text-[9px] text-white/30">{m.t}</span>
                    </div>
                    <p className="mt-0.5 text-xs text-white/50">{m.msg}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Growth chart + alerts */}
          <div className="space-y-4 lg:col-span-5">
            {/* Growth */}
            <div className="gradient-border noise relative overflow-hidden rounded-3xl bg-charcoal/50 p-6 backdrop-blur-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-emerald" />
                  <span className="text-sm font-medium text-white">Growth Trajectory</span>
                </div>
                <span className="font-mono text-[10px] text-emerald">+24% MoM</span>
              </div>
              <div className="mt-4">
                <AreaChart data={[8, 12, 10, 18, 24, 22, 32, 38, 42, 48, 56, 64]} color="#10b981" color2="#14b8a6" height={90} />
              </div>
              <div className="mt-3 grid grid-cols-3 gap-3">
                <div>
                  <div className="text-[9px] uppercase tracking-wider text-white/30">Waitlist</div>
                  <div className="font-mono text-sm text-white"><Counter to={2400} suffix="+" /></div>
                </div>
                <div>
                  <div className="text-[9px] uppercase tracking-wider text-white/30">CAC</div>
                  <div className="font-mono text-sm text-white">$<Counter to={34} /></div>
                </div>
                <div>
                  <div className="text-[9px] uppercase tracking-wider text-white/30">LTV</div>
                  <div className="font-mono text-sm text-white">$<Counter to={1200} /></div>
                </div>
              </div>
            </div>

            {/* Alerts */}
            <div className="gradient-border noise relative overflow-hidden rounded-3xl bg-charcoal/50 p-6 backdrop-blur-sm">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-orange" />
                <span className="text-sm font-medium text-white">Risk Register</span>
              </div>
              <div className="mt-4 space-y-2">
                {[
                  { l: 'Distribution risk — no channel PMF yet', s: 'High', c: '#ec4899' },
                  { l: 'Runway at 6.4 months — raise needed', s: 'Med', c: '#fb923c' },
                  { l: 'Key hire gap — senior engineer', s: 'Low', c: '#2d7ff9' },
                ].map((r, i) => (
                  <div key={i} className="flex items-center justify-between rounded-lg border border-white/5 bg-white/[0.02] p-2.5">
                    <span className="text-xs text-white/60">{r.l}</span>
                    <span className="rounded-full px-2 py-0.5 text-[9px] font-medium" style={{ background: `${r.c}22`, color: r.c }}>{r.s}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Row 6: Crew status grid */}
        <div className="mt-4 gradient-border noise relative overflow-hidden rounded-3xl bg-charcoal/40 p-6 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-electric" />
              <span className="text-sm font-medium text-white">Crew Status Board</span>
            </div>
            <span className="font-mono text-[10px] text-white/30">12 crews · real-time</span>
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {CREWS.map((c, i) => {
              const Icon = CREW_ICONS[c.icon];
              const status = i < 7 ? 'complete' : i === 7 ? 'active' : 'queued';
              return (
                <div
                  key={c.id}
                  className="group relative overflow-hidden rounded-2xl border border-white/5 bg-white/[0.02] p-4 transition-all hover:-translate-y-0.5 hover:border-white/10"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ background: `${c.color}22` }}>
                        {Icon && <Icon className="h-4 w-4" style={{ color: c.color }} />}
                      </div>
                      <span className="text-xs font-medium text-white">{c.name}</span>
                    </div>
                    <span
                      className="h-2 w-2 rounded-full"
                      style={{
                        background: status === 'complete' ? '#10b981' : status === 'active' ? c.color : 'rgba(255,255,255,0.2)',
                        boxShadow: status === 'active' ? `0 0 8px ${c.color}` : 'none',
                      }}
                    />
                  </div>
                  <div className="mt-3 flex items-center justify-between text-[10px]">
                    <span className="text-white/40">{c.agents.length} agents</span>
                    <span style={{ color: status === 'complete' ? '#10b981' : status === 'active' ? c.color : 'rgba(255,255,255,0.3)' }}>
                      {status === 'complete' ? 'COMPLETE' : status === 'active' ? 'RUNNING' : 'QUEUED'}
                    </span>
                  </div>
                  {status === 'active' && (
                    <div className="mt-2">
                      <GradientBar value={68} color={c.color} color2={c.color2} height={3} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Footer spacer */}
      <div className="h-12" />
    </div>
  );
}
