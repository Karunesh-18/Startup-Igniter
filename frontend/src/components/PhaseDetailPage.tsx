/* PhaseDetailPage — Deep-dive into a single Phase Crew */

import { useState } from 'react';
import {
  Lightbulb, Globe, FlaskConical, Cpu, Briefcase, Boxes, Scale, Sparkles,
  Banknote, TrendingUp, Users, FileText, ArrowRight, ChevronRight,
  Activity, CheckCircle2, Clock, Zap, BarChart3, Bot,
} from 'lucide-react';
import NeuralBackground from './NeuralBackground';
import { CREWS, PIPELINE } from '@/data/crews';
import type { Crew, Agent } from '@/data/crews';

const CREW_ICONS: Record<string, any> = {
  Lightbulb, Globe, FlaskConical, Cpu, Briefcase, Boxes, Scale, Sparkles,
  Banknote, TrendingUp, Users, FileText,
};

const CREW_DESCRIPTIONS: Record<number, string> = {
  1: 'Validate your core concept against market reality, test foundational assumptions and score originality. Six agents run in parallel to give you a comprehensive idea audit before you invest resources.',
  2: 'Map the demand landscape, size TAM/SAM/SOM and discover your competitive field. Seven agents analyse market conditions, consumer trends and competitor positioning.',
  3: 'Mine USPTO patent databases, analyse academic research papers and identify innovation white spaces. Six agents give you a full IP and research intelligence brief.',
  4: 'Prove the architecture can scale, identify security gaps and model infrastructure costs. Six agents audit your technical feasibility from every engineering angle.',
  5: 'Design your revenue model, calculate unit economics and build a 3-year financial projection. Six agents formulate the complete business planning framework.',
  6: 'Scope the MVP, select the optimal tech stack and sequence sprint milestones. Six agents turn your idea into an actionable product delivery plan.',
  7: 'Incorporate the entity, draft core legal contracts and map regulatory compliance requirements. Six agents protect your legal foundation.',
  8: 'Craft brand narrative, generate startup naming candidates and plan go-to-market channels. Five agents build your complete brand identity kit.',
  9: 'Match investors by stage and vertical, model pre-money valuation and structure the fundraise. Five agents prepare you for investor conversations.',
  10: 'Engineer growth loops, design referral mechanics and plan international expansion. Four agents map your scaling playbook.',
  11: 'Cultivate early community, connect with mentors and identify accelerator cohorts. Four agents build your ecosystem network.',
  12: 'Synthesise every crew\'s output into an investor-ready master report with 30-60-90 day action plan. Five agents produce your complete startup deliverable.',
};

const AGENT_ROLES_DETAIL: Record<string, string> = {
  'Hypothesis Scanner': 'Tests foundational assumptions against market data',
  'Problem Decoder': 'Identifies root causes and validates pain point severity',
  'Market Fit Analyst': 'Calculates TAM/SAM/SOM and product-market fit signals',
  'Risk Assessor': 'Quantifies technical, market and operational risks',
  'Trend Mapper': 'Maps macro trends to timing and opportunity windows',
  'Uniqueness Probe': 'Evaluates differentiation and competitive moat strength',
};

interface Props {
  crewId: number;
  onBack: () => void;
  onSelectAgent: (agentId: number) => void;
  onLaunch: () => void;
}

export default function PhaseDetailPage({ crewId, onBack, onSelectAgent, onLaunch }: Props) {
  const [activeTab, setActiveTab] = useState<'agents' | 'metrics' | 'related'>('agents');

  const crew = CREWS.find((c: Crew) => c.id === crewId);
  const stage = PIPELINE.find((p) => p.crew === crewId);
  const relatedCrews = CREWS.filter((c: Crew) => c.id !== crewId).slice(0, 3);

  if (!crew) return null;

  const Icon = CREW_ICONS[crew.icon] ?? Zap;

  return (
    <div className="relative min-h-screen overflow-hidden bg-void">
      {/* Background */}
      <div className="absolute inset-0 opacity-25">
        <NeuralBackground density={0.4} />
      </div>
      <div
        className="absolute inset-0"
        style={{
          background: `radial-gradient(ellipse 70% 50% at 50% 0%, ${crew.color}10, transparent 70%)`,
        }}
      />
      <div className="absolute inset-0 grid-bg opacity-20" />

      <div className="relative z-10 mx-auto max-w-6xl px-6 py-12">
        {/* Back */}
        <button
          onClick={onBack}
          className="mb-10 flex items-center gap-2 text-sm text-white/40 transition-colors hover:text-white"
        >
          <ArrowRight className="h-4 w-4 rotate-180" />
          All phases
        </button>

        {/* Hero Header */}
        <div className="mb-10 animate-fade-up">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
            {/* Icon */}
            <div
              className="flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl"
              style={{
                background: `linear-gradient(135deg, ${crew.color}30, ${crew.color2}20)`,
                border: `1px solid ${crew.color}40`,
                boxShadow: `0 0 40px -10px ${crew.color}50`,
              }}
            >
              <Icon className="h-9 w-9" style={{ color: crew.color }} />
            </div>

            {/* Meta */}
            <div className="flex-1">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <span
                  className="rounded-full px-3 py-1 text-[10px] font-medium uppercase tracking-widest"
                  style={{ background: `${crew.color}18`, color: crew.color }}
                >
                  Phase {String(crew.id).padStart(2, '0')}
                </span>
                <span className="text-xs text-white/30">{crew.domain}</span>
              </div>
              <h1 className="text-3xl font-light text-white sm:text-4xl">
                {crew.name}
                <span className="ml-3 font-mono text-base font-normal text-white/30">{crew.short}</span>
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-relaxed text-white/50">
                {CREW_DESCRIPTIONS[crewId]}
              </p>

              {/* Quick stats */}
              <div className="mt-5 flex flex-wrap gap-6">
                {[
                  { label: 'Agents', value: crew.agents.length, color: crew.color },
                  { label: 'Domain', value: crew.domain, color: crew.color2 },
                  { label: 'Status', value: 'Ready', color: '#10b981' },
                ].map((stat) => (
                  <div key={stat.label}>
                    <div className="text-lg font-semibold" style={{ color: stat.color }}>
                      {stat.value}
                    </div>
                    <div className="text-[10px] uppercase tracking-wider text-white/35">{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Launch CTA */}
            <button
              onClick={onLaunch}
              className="btn-primary shrink-0 flex items-center gap-2 rounded-full px-6 py-2.5 text-sm font-medium"
            >
              <Zap className="h-4 w-4" />
              Launch Analysis
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-8 flex gap-1 rounded-2xl border border-white/[0.06] bg-white/[0.02] p-1">
          {(['agents', 'metrics', 'related'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className="flex-1 rounded-xl py-2 text-xs font-medium uppercase tracking-wider transition-all duration-200"
              style={
                activeTab === tab
                  ? {
                      background: `linear-gradient(135deg, ${crew.color}25, ${crew.color2}15)`,
                      color: crew.color,
                      border: `1px solid ${crew.color}30`,
                    }
                  : { color: 'rgba(255,255,255,0.4)' }
              }
            >
              {tab === 'agents' ? `Agents (${crew.agents.length})` : tab === 'metrics' ? 'Metrics' : 'Related'}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'agents' && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {crew.agents.map((agent: Agent, idx) => (
              <button
                key={agent.id}
                onClick={() => onSelectAgent(agent.id)}
                className="group relative overflow-hidden rounded-2xl border border-white/[0.06] bg-charcoal/60 p-4 text-left backdrop-blur-sm transition-all duration-300 hover:border-white/20"
                style={{ animationDelay: `${idx * 0.05}s` }}
              >
                <div className="pointer-events-none absolute inset-0 rounded-2xl opacity-0 transition-opacity duration-300 group-hover:opacity-100"
                  style={{ background: `radial-gradient(ellipse 80% 60% at 30% 20%, ${crew.color}06, transparent)` }}
                />
                <div className="mb-3 flex items-start justify-between">
                  <div
                    className="flex h-8 w-8 items-center justify-center rounded-lg"
                    style={{ background: `${crew.color}15`, border: `1px solid ${crew.color}25` }}
                  >
                    <Bot className="h-4 w-4" style={{ color: crew.color }} />
                  </div>
                  <span className="font-mono text-[9px] text-white/25">
                    {String(agent.id).padStart(2, '0')}
                  </span>
                </div>
                <div className="font-medium text-sm text-white">{agent.name}</div>
                <div className="mt-1 text-[10px] uppercase tracking-wider text-white/40">{agent.role}</div>
                <div className="mt-3 flex items-center justify-between">
                  <span
                    className="rounded-full px-2 py-0.5 text-[8px] font-medium uppercase tracking-wider"
                    style={{ background: `${crew.color}18`, color: crew.color }}
                  >
                    {crew.short}
                  </span>
                  <ChevronRight className="h-3.5 w-3.5 text-white/20 transition-all group-hover:translate-x-0.5 group-hover:text-white/50" />
                </div>
              </button>
            ))}
          </div>
        )}

        {activeTab === 'metrics' && stage && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {stage.metrics.map((m) => (
              <div
                key={m.label}
                className="rounded-2xl border border-white/[0.06] bg-charcoal/60 p-5 backdrop-blur-sm"
              >
                <div className="mb-1 text-[10px] uppercase tracking-wider text-white/40">{m.label}</div>
                <div className="text-2xl font-semibold" style={{ color: crew.color }}>{m.value}</div>
              </div>
            ))}
            {/* Extra descriptive card */}
            <div className="rounded-2xl border border-white/[0.06] bg-charcoal/60 p-5 backdrop-blur-sm sm:col-span-2 lg:col-span-1">
              <div className="mb-1 text-[10px] uppercase tracking-wider text-white/40">Description</div>
              <div className="text-sm leading-relaxed text-white/60">{stage.description}</div>
            </div>
          </div>
        )}

        {activeTab === 'related' && (
          <div className="grid gap-4 sm:grid-cols-3">
            {relatedCrews.map((rc: Crew) => {
              const RIcon = CREW_ICONS[rc.icon] ?? Zap;
              return (
                <button
                  key={rc.id}
                  onClick={onBack}
                  className="group rounded-2xl border border-white/[0.06] bg-charcoal/60 p-5 text-left backdrop-blur-sm transition-all duration-300 hover:border-white/20"
                >
                  <div
                    className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl"
                    style={{ background: `${rc.color}18`, border: `1px solid ${rc.color}28` }}
                  >
                    <RIcon className="h-5 w-5" style={{ color: rc.color }} />
                  </div>
                  <div className="text-sm font-medium text-white">{rc.name}</div>
                  <div className="mt-1 text-[10px] uppercase tracking-wider text-white/40">{rc.domain}</div>
                  <div className="mt-3 flex items-center gap-1 text-[10px] text-white/40 group-hover:text-white/60 transition-colors">
                    View crew <ChevronRight className="h-3 w-3" />
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
