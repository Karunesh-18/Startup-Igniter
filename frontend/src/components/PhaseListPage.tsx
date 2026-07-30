/* PhaseListPage — Mission Control Grid of all 12 Crew Phases */

import { useState } from 'react';
import {
  Lightbulb, Globe, FlaskConical, Cpu, Briefcase, Boxes, Scale, Sparkles,
  Banknote, TrendingUp, Users, FileText, ArrowRight, ChevronRight, Activity,
  Zap, Network,
} from 'lucide-react';
import NeuralBackground from './NeuralBackground';
import { CREWS } from '@/data/crews';
import type { Crew } from '@/data/crews';

const CREW_ICONS: Record<string, any> = {
  Lightbulb, Globe, FlaskConical, Cpu, Briefcase, Boxes, Scale, Sparkles,
  Banknote, TrendingUp, Users, FileText,
};

const CREW_DESCRIPTIONS: Record<number, string> = {
  1: 'Validate your core concept, test assumptions and score originality.',
  2: 'Map the demand landscape, size TAM/SAM/SOM and discover competitors.',
  3: 'Mine prior art, analyse research papers and identify innovation gaps.',
  4: 'Prove the architecture, scalability ceiling and security posture.',
  5: 'Design the revenue model, unit economics and 3-year projections.',
  6: 'Scope the MVP, select tech stack and sequence the sprint roadmap.',
  7: 'Incorporate the entity, draft contracts and map regulatory compliance.',
  8: 'Craft brand narrative, naming candidates and go-to-market channels.',
  9: 'Match investors, model valuation and structure the fundraise round.',
  10: 'Engineer growth loops, referral programmes and retention mechanics.',
  11: 'Cultivate an early community, find mentors and accelerator cohorts.',
  12: 'Synthesise every crew\'s output into an investor-ready master report.',
};

interface Props {
  onBack: () => void;
  onSelectPhase: (crewId: number) => void;
  onAgents: () => void;
}

export default function PhaseListPage({ onBack, onSelectPhase, onAgents }: Props) {
  const [hovered, setHovered] = useState<number | null>(null);

  return (
    <div className="relative min-h-screen overflow-hidden bg-void">
      {/* Background */}
      <div className="absolute inset-0 opacity-30">
        <NeuralBackground density={0.5} />
      </div>
      <div className="absolute inset-0 radial-spotlight" />
      <div className="absolute inset-0 grid-bg opacity-30" />

      <div className="relative z-10 mx-auto max-w-7xl px-6 py-12">
        {/* Header */}
        <div className="mb-12 animate-fade-up">
          <button
            onClick={onBack}
            className="mb-8 flex items-center gap-2 text-sm text-white/40 transition-colors hover:text-white"
          >
            <ArrowRight className="h-4 w-4 rotate-180" />
            Back
          </button>

          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5">
                <Network className="h-3.5 w-3.5 text-electric" />
                <span className="text-xs text-white/60">Mission Control</span>
              </div>
              <h1 className="text-4xl font-light leading-tight text-white sm:text-5xl">
                12 Specialized <span className="font-serif italic text-gradient">Crews</span>
              </h1>
              <p className="mt-3 max-w-xl text-white/45">
                Each crew is a self-contained intelligence unit running multiple AI agents in parallel through a distinct startup phase.
              </p>
            </div>
            <button
              onClick={onAgents}
              className="btn-ghost flex shrink-0 items-center gap-2 rounded-full px-5 py-2 text-sm text-white/70"
            >
              <Users className="h-4 w-4" />
              View all agents
            </button>
          </div>

          {/* Stats strip */}
          <div className="mt-8 flex flex-wrap gap-6 border-t border-white/5 pt-8">
            {[
              { label: 'Phase Crews', value: '12', icon: Network, color: '#2d7ff9' },
              { label: 'AI Agents', value: '72', icon: Activity, color: '#8b5cf6' },
              { label: 'Analysis Domains', value: '12', icon: Zap, color: '#10b981' },
            ].map((s) => (
              <div key={s.label} className="flex items-center gap-3">
                <div
                  className="flex h-8 w-8 items-center justify-center rounded-lg"
                  style={{ background: `${s.color}18`, border: `1px solid ${s.color}30` }}
                >
                  <s.icon className="h-4 w-4" style={{ color: s.color }} />
                </div>
                <div>
                  <div className="text-lg font-semibold leading-none text-white" style={{ color: s.color }}>
                    {s.value}
                  </div>
                  <div className="text-[10px] uppercase tracking-wider text-white/40">{s.label}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Phase Crew Grid */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {CREWS.map((crew: Crew, idx) => {
            const Icon = CREW_ICONS[crew.icon] ?? Zap;
            const isHovered = hovered === crew.id;
            return (
              <button
                key={crew.id}
                onClick={() => onSelectPhase(crew.id)}
                onMouseEnter={() => setHovered(crew.id)}
                onMouseLeave={() => setHovered(null)}
                className="group relative overflow-hidden rounded-2xl border bg-charcoal/50 p-5 text-left backdrop-blur-sm transition-all duration-300"
                style={{
                  borderColor: isHovered ? `${crew.color}55` : 'rgba(255,255,255,0.06)',
                  boxShadow: isHovered ? `0 0 30px -10px ${crew.color}60` : 'none',
                  animationDelay: `${idx * 0.04}s`,
                }}
              >
                {/* Hover glow overlay */}
                <div
                  className="pointer-events-none absolute inset-0 rounded-2xl opacity-0 transition-opacity duration-300 group-hover:opacity-100"
                  style={{
                    background: `radial-gradient(ellipse 80% 60% at 30% 20%, ${crew.color}08, transparent 70%)`,
                  }}
                />

                {/* Icon + index */}
                <div className="mb-4 flex items-start justify-between">
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-xl transition-transform duration-300 group-hover:scale-110"
                    style={{
                      background: `linear-gradient(135deg, ${crew.color}25, ${crew.color2}18)`,
                      border: `1px solid ${crew.color}30`,
                    }}
                  >
                    <Icon className="h-5 w-5" style={{ color: crew.color }} />
                  </div>
                  <span className="font-mono text-[10px] text-white/25">
                    {String(crew.id).padStart(2, '0')}
                  </span>
                </div>

                {/* Content */}
                <div className="mb-3">
                  <div className="text-[9px] uppercase tracking-[0.18em] text-white/35 mb-1">{crew.domain}</div>
                  <h3 className="text-sm font-semibold text-white">{crew.name}</h3>
                  <p className="mt-1.5 text-xs leading-relaxed text-white/45">
                    {CREW_DESCRIPTIONS[crew.id]}
                  </p>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between">
                  <span
                    className="rounded-full px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider"
                    style={{ background: `${crew.color}18`, color: crew.color }}
                  >
                    {crew.agents.length} agents
                  </span>
                  <ChevronRight
                    className="h-4 w-4 text-white/25 transition-all duration-300 group-hover:translate-x-1 group-hover:text-white/60"
                  />
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
