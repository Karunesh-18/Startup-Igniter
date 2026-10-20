/* AgentDetailPage — Deep-dive into a single AI Agent */

import { ArrowRight, Bot, ChevronRight, Zap, Target } from 'lucide-react';
import { CREW_ICONS } from '@/lib/icons';
import { Link, Navigate } from 'react-router-dom';
import NeuralBackground from './NeuralBackground';
import { crewKeyForId, crewMeta } from '@/lib/report';
import { CREWS, ALL_AGENTS } from '@/data/crews';
import type { Crew, Agent } from '@/data/crews';

// Every crews.ts role currently shares this generic description; per-role
// copy belongs in data/crews.ts once it exists.
const DEFAULT_DETAIL = {
  purpose: 'Specialist AI agent performing targeted analysis within its crew phase.',
  outputs: ['Structured analysis report', 'Confidence scores', 'Recommendations'],
  tools: ['Web search (Tavily / Exa / Zyte)', 'Self-hosted LLM gateway', 'Shared project memory'],
};

export default function AgentDetailPage({ agentId }: { agentId: number }) {
  const agent = ALL_AGENTS.find((a: Agent) => a.id === agentId);
  if (!agent) return <Navigate to="/agents" replace />;

  const crew = CREWS.find((c: Crew) => c.id === agent.crew)!;
  const Icon = CREW_ICONS[crew.icon] ?? Bot;
  const detail = DEFAULT_DETAIL;

  // Sibling agents in same crew (excluding self)
  const siblings = crew.agents.filter((a: Agent) => a.id !== agentId);

  // Facts that follow from the crew spec itself (no runtime telemetry exists yet).
  const specs = [
    { label: 'Agent', value: `#${String(agent.id).padStart(2, '0')}` },
    { label: 'Pipeline stage', value: `${crew.id} of ${CREWS.length}` },
    { label: 'Agents in crew', value: String(crew.agents.length) },
    { label: 'Report section', value: crewMeta(crewKeyForId(crew.id)).label },
  ];

  return (
    <div className="relative min-h-screen overflow-hidden bg-void">
      {/* Background */}
      <div className="absolute inset-0 opacity-20">
        <NeuralBackground density={0.35} />
      </div>
      <div
        className="absolute inset-0"
        style={{
          background: `radial-gradient(ellipse 60% 40% at 50% 0%, ${crew.color}0d, transparent 70%)`,
        }}
      />
      <div className="absolute inset-0 grid-bg opacity-20" />

      <div className="relative z-10 mx-auto max-w-5xl px-4 pb-12 pt-28 sm:px-6">
        {/* Back */}
        <Link to="/agents" className="mb-10 flex w-fit items-center gap-2 text-sm text-white/40 transition-colors hover:text-white">
          <ArrowRight className="h-4 w-4 rotate-180" />
          All agents
        </Link>

        {/* Hero */}
        <div className="mb-10 animate-fade-up">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
            {/* Agent icon */}
            <div
              className="relative flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl"
              style={{
                background: `linear-gradient(135deg, ${crew.color}25, ${crew.color2}18)`,
                border: `1px solid ${crew.color}40`,
                boxShadow: `0 0 40px -10px ${crew.color}50`,
              }}
            >
              <Bot className="h-9 w-9" style={{ color: crew.color }} />
              {/* Crew badge overlay */}
              <div
                className="absolute -bottom-2 -right-2 flex h-7 w-7 items-center justify-center rounded-lg"
                style={{ background: crew.color, boxShadow: `0 0 12px ${crew.color}80` }}
              >
                <Icon className="h-3.5 w-3.5 text-white" />
              </div>
            </div>

            {/* Meta */}
            <div className="flex-1">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <span
                  className="rounded-full px-3 py-1 text-[10px] font-medium uppercase tracking-widest"
                  style={{ background: `${crew.color}18`, color: crew.color }}
                >
                  {crew.short} · Agent #{String(agentId).padStart(2, '0')}
                </span>
                <span className="text-xs text-white/30">{agent.role}</span>
              </div>
              <h1 className="text-3xl font-light text-white sm:text-4xl">{agent.name}</h1>
              <p className="mt-3 max-w-2xl text-sm leading-relaxed text-white/50">{detail.purpose}</p>

              <Link
                to={`/phases/${crew.id}`}
                className="mt-4 flex w-fit items-center gap-1.5 text-xs transition-colors"
                style={{ color: crew.color }}
              >
                <Icon className="h-3.5 w-3.5" />
                {crew.name} phase
                <ChevronRight className="h-3 w-3" />
              </Link>
            </div>
          </div>
        </div>

        {/* Spec */}
        <div className="mb-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {specs.map((m) => (
            <div
              key={m.label}
              className="rounded-2xl border border-white/[0.06] bg-charcoal/60 p-4 backdrop-blur-sm"
            >
              <div className="text-xs text-white/45">{m.label}</div>
              <div className="mt-1 text-xl font-semibold" style={{ color: crew.color }}>{m.value}</div>
            </div>
          ))}
        </div>

        {/* Two-column detail */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Outputs */}
          <div className="rounded-2xl border border-white/[0.06] bg-charcoal/60 p-6 backdrop-blur-sm">
            <div className="mb-4 flex items-center gap-2">
              <Target className="h-4 w-4" style={{ color: crew.color }} />
              <h3 className="text-sm font-medium text-white">Outputs</h3>
            </div>
            <div className="flex flex-col gap-2.5">
              {detail.outputs.map((out, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div
                    className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full"
                    style={{ background: crew.color }}
                  />
                  <span className="text-sm text-white/60">{out}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Tools */}
          <div className="rounded-2xl border border-white/[0.06] bg-charcoal/60 p-6 backdrop-blur-sm">
            <div className="mb-4 flex items-center gap-2">
              <Zap className="h-4 w-4" style={{ color: crew.color2 }} />
              <h3 className="text-sm font-medium text-white">Tools & Integrations</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {detail.tools.map((tool, i) => (
                <span
                  key={i}
                  className="rounded-full px-3 py-1 text-xs"
                  style={{
                    background: `${crew.color}12`,
                    color: `${crew.color}cc`,
                    border: `1px solid ${crew.color}25`,
                  }}
                >
                  {tool}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Sibling Agents */}
        {siblings.length > 0 && (
          <div className="mt-8">
            <h3 className="mb-4 text-sm font-medium text-white/60">
              Other agents in <span style={{ color: crew.color }}>{crew.name}</span>
            </h3>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {siblings.map((sib: Agent) => (
                <Link
                  key={sib.id}
                  to={`/agents/${sib.id}`}
                  className="group flex items-center justify-between rounded-xl border border-white/[0.06] bg-charcoal/40 px-4 py-3 text-left transition-all hover:border-white/20"
                >
                  <div>
                    <div className="text-xs font-medium text-white/80">{sib.name}</div>
                    <div className="text-[10px] text-white/35">{sib.role}</div>
                  </div>
                  <ChevronRight className="h-3.5 w-3.5 text-white/20 transition-all group-hover:translate-x-0.5 group-hover:text-white/50" />
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
