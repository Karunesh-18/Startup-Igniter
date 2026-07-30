/* AgentListPage — Directory of all 72 AI Agents */

import { useState } from 'react';
import {
  Lightbulb, Globe, FlaskConical, Cpu, Briefcase, Boxes, Scale, Sparkles,
  Banknote, TrendingUp, Users, FileText, ArrowRight, Bot, Search, ChevronRight,
} from 'lucide-react';
import NeuralBackground from './NeuralBackground';
import { CREWS, ALL_AGENTS } from '@/data/crews';
import type { Crew, Agent } from '@/data/crews';

const CREW_ICONS: Record<string, any> = {
  Lightbulb, Globe, FlaskConical, Cpu, Briefcase, Boxes, Scale, Sparkles,
  Banknote, TrendingUp, Users, FileText,
};

interface Props {
  onBack: () => void;
  onSelectAgent: (agentId: number) => void;
  onPhases: () => void;
}

export default function AgentListPage({ onBack, onSelectAgent, onPhases }: Props) {
  const [selectedCrew, setSelectedCrew] = useState<number | 'all'>('all');
  const [query, setQuery] = useState('');

  const filteredAgents = ALL_AGENTS.filter((a: Agent) => {
    const matchesCrew = selectedCrew === 'all' || a.crew === selectedCrew;
    const q = query.toLowerCase();
    const matchesQuery = !q || a.name.toLowerCase().includes(q) || a.role.toLowerCase().includes(q);
    return matchesCrew && matchesQuery;
  });

  const getCrewForAgent = (a: Agent): Crew =>
    CREWS.find((c: Crew) => c.id === a.crew)!;

  return (
    <div className="relative min-h-screen overflow-hidden bg-void">
      {/* Background */}
      <div className="absolute inset-0 opacity-25">
        <NeuralBackground density={0.4} />
      </div>
      <div className="absolute inset-0 radial-spotlight" />
      <div className="absolute inset-0 grid-bg opacity-20" />

      <div className="relative z-10 mx-auto max-w-7xl px-6 py-12">
        {/* Back */}
        <button
          onClick={onBack}
          className="mb-10 flex items-center gap-2 text-sm text-white/40 transition-colors hover:text-white"
        >
          <ArrowRight className="h-4 w-4 rotate-180" />
          Back
        </button>

        {/* Header */}
        <div className="mb-10 animate-fade-up flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5">
              <Bot className="h-3.5 w-3.5 text-violet" />
              <span className="text-xs text-white/60">Agent Directory</span>
            </div>
            <h1 className="text-4xl font-light leading-tight text-white sm:text-5xl">
              72 Specialized <span className="font-serif italic text-gradient">Agents</span>
            </h1>
            <p className="mt-3 max-w-xl text-white/45">
              Every agent is purpose-built for a distinct analysis task within its crew phase.
            </p>
          </div>
          <button
            onClick={onPhases}
            className="btn-ghost flex shrink-0 items-center gap-2 rounded-full px-5 py-2 text-sm text-white/70"
          >
            <FileText className="h-4 w-4" />
            View all phases
          </button>
        </div>

        {/* Search + Crew Filter */}
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search agents by name or role…"
              className="w-full rounded-full border border-white/10 bg-white/[0.04] py-2.5 pl-10 pr-4 text-sm text-white placeholder-white/25 focus:border-white/20 focus:outline-none"
            />
          </div>

          {/* Crew filter scrollable */}
          <div className="flex gap-1.5 overflow-x-auto pb-1">
            <button
              onClick={() => setSelectedCrew('all')}
              className="shrink-0 rounded-full border px-3 py-1.5 text-[11px] font-medium uppercase tracking-wider transition-all"
              style={
                selectedCrew === 'all'
                  ? { background: 'rgba(45,127,249,0.2)', color: '#2d7ff9', borderColor: '#2d7ff940' }
                  : { color: 'rgba(255,255,255,0.45)', borderColor: 'rgba(255,255,255,0.08)' }
              }
            >
              All
            </button>
            {CREWS.map((c: Crew) => {
              const Icon = CREW_ICONS[c.icon] ?? Bot;
              return (
                <button
                  key={c.id}
                  onClick={() => setSelectedCrew(c.id)}
                  className="shrink-0 flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[11px] font-medium uppercase tracking-wider transition-all"
                  style={
                    selectedCrew === c.id
                      ? { background: `${c.color}20`, color: c.color, borderColor: `${c.color}40` }
                      : { color: 'rgba(255,255,255,0.45)', borderColor: 'rgba(255,255,255,0.08)' }
                  }
                >
                  <Icon className="h-3 w-3" />
                  {c.short}
                </button>
              );
            })}
          </div>
        </div>

        {/* Count */}
        <div className="mb-5 text-sm text-white/35">
          {filteredAgents.length} agent{filteredAgents.length !== 1 ? 's' : ''}
          {selectedCrew !== 'all' && ` · ${CREWS.find(c => c.id === selectedCrew)?.name}`}
          {query && ` matching "${query}"`}
        </div>

        {/* Agent Grid */}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredAgents.map((agent: Agent, idx) => {
            const crew = getCrewForAgent(agent);
            const Icon = CREW_ICONS[crew.icon] ?? Bot;
            return (
              <button
                key={agent.id}
                onClick={() => onSelectAgent(agent.id)}
                className="group relative overflow-hidden rounded-2xl border border-white/[0.06] bg-charcoal/50 p-4 text-left backdrop-blur-sm transition-all duration-300 hover:border-white/20"
                style={{ animationDelay: `${Math.min(idx * 0.02, 0.6)}s` }}
              >
                <div
                  className="pointer-events-none absolute inset-0 rounded-2xl opacity-0 transition-opacity duration-300 group-hover:opacity-100"
                  style={{ background: `radial-gradient(ellipse 80% 50% at 20% 20%, ${crew.color}06, transparent)` }}
                />
                <div className="mb-3 flex items-center justify-between">
                  <div
                    className="flex h-7 w-7 items-center justify-center rounded-lg"
                    style={{ background: `${crew.color}15`, border: `1px solid ${crew.color}25` }}
                  >
                    <Icon className="h-3.5 w-3.5" style={{ color: crew.color }} />
                  </div>
                  <span className="font-mono text-[9px] text-white/25">#{String(agent.id).padStart(2, '0')}</span>
                </div>
                <div className="text-sm font-medium text-white leading-tight">{agent.name}</div>
                <div className="mt-0.5 text-[10px] uppercase tracking-wider text-white/40">{agent.role}</div>
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
            );
          })}
        </div>

        {filteredAgents.length === 0 && (
          <div className="py-20 text-center">
            <Bot className="mx-auto h-12 w-12 text-white/10" />
            <div className="mt-4 text-white/30">No agents match your search</div>
          </div>
        )}
      </div>
    </div>
  );
}
