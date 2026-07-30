import { useState } from 'react';
import { ArrowLeft, Rocket, Sparkles, Zap, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react';
import NeuralBackground from './NeuralBackground';
import { useScrollReveal } from '@/hooks/useScrollReveal';
import { useAnalysis } from '@/hooks/useAnalysis';
import type { AnalysisResult } from '@/lib/types';

const EXAMPLES = [
  'AI-powered legal contract reviewer for small businesses',
  'Carbon credit marketplace for regenerative agriculture',
  'Mental health companion app for Gen Z using voice AI',
  'Decentralized GPU marketplace for indie AI developers',
  'Autonomous warehouse robots with multi-agent AI for inventory management',
];

// Crew color palette matching crews.ts
const CREW_COLORS: Record<number, { color: string; color2: string; label: string }> = {
  1: { color: '#2d7ff9', color2: '#6366f1', label: 'Idea Validation' },
  2: { color: '#14b8a6', color2: '#2d7ff9', label: 'Market Research' },
  3: { color: '#8b5cf6', color2: '#6366f1', label: 'Research & Patent' },
};

interface Props {
  onBack: () => void;
  onComplete: (result: AnalysisResult) => void;
}

export default function AnalysisPage({ onBack, onComplete }: Props) {
  useScrollReveal();
  const [idea, setIdea] = useState('');
  const { status, steps, activeStep, result, error, submit } = useAnalysis();

  const launch = () => {
    if (!idea.trim()) return;
    submit(idea.trim());
  };

  // Navigate to results when done
  if (status === 'done' && result) {
    // Small delay so user sees final step completion
    setTimeout(() => onComplete(result), 600);
  }

  const isRunning = status === 'running';
  const isError = status === 'error';

  return (
    <div className="relative min-h-screen overflow-hidden bg-void">
      <div className="absolute inset-0 opacity-40">
        <NeuralBackground density={0.4} />
      </div>
      <div className="absolute inset-0 radial-spotlight" />

      <div className="relative z-10 mx-auto max-w-4xl px-6 py-12">
        <button onClick={onBack} className="mb-8 flex items-center gap-2 text-sm text-white/50 transition-colors hover:text-white">
          <ArrowLeft className="h-4 w-4" />
          Back
        </button>

        {/* ── Input Section ── */}
        {!isRunning && status !== 'done' && (
          <div>
            <div className="reveal text-center">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5">
                <Sparkles className="h-3.5 w-3.5 text-violet" />
                <span className="text-xs text-white/60">New Mission</span>
              </div>
              <h1 className="text-4xl font-light leading-tight text-white sm:text-5xl">
                What are we <span className="font-serif italic text-gradient">building</span>?
              </h1>
              <p className="mx-auto mt-4 max-w-xl text-white/50">
                Describe your startup idea. 20 AI agents across 3 specialized crews will analyse it end-to-end.
              </p>
            </div>

            {/* Input */}
            <div className="reveal mt-10 gradient-border noise relative overflow-hidden rounded-3xl bg-charcoal/50 p-2 backdrop-blur-xl">
              <textarea
                value={idea}
                onChange={(e) => setIdea(e.target.value)}
                placeholder="e.g. An AI platform that turns startup ideas into investor-ready companies..."
                rows={3}
                className="w-full resize-none rounded-2xl bg-transparent px-5 py-4 text-lg text-white placeholder-white/25 focus:outline-none"
              />
              <div className="flex items-center justify-between px-4 pb-3">
                <div className="flex items-center gap-2 text-xs text-white/30">
                  <Zap className="h-3.5 w-3.5 text-electric" />
                  {idea.length} chars · 3 crews · 20 agents
                </div>
                <button
                  onClick={launch}
                  disabled={!idea.trim()}
                  className="btn-primary flex items-center gap-2 rounded-full px-6 py-2.5 text-sm font-medium disabled:opacity-40"
                >
                  <Rocket className="h-4 w-4" />
                  Launch Mission
                </button>
              </div>
            </div>

            {/* Examples */}
            <div className="reveal mt-6">
              <div className="text-center text-xs uppercase tracking-wider text-white/30">Or try an example</div>
              <div className="mt-4 flex flex-wrap justify-center gap-2">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex}
                    onClick={() => setIdea(ex)}
                    className="rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-xs text-white/60 transition-all hover:border-white/20 hover:text-white"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>

            {/* Error state */}
            {isError && error && (
              <div className="mt-8 flex items-start gap-3 rounded-2xl border border-red-500/20 bg-red-500/10 p-4">
                <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />
                <div>
                  <div className="text-sm font-medium text-red-300">Analysis failed</div>
                  <div className="mt-1 text-xs text-red-400/80">{error}</div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Execution Pipeline ── */}
        {isRunning && (
          <div className="animate-fade-up">
            {/* Status badge */}
            <div className="mb-8 text-center">
              <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-electric" />
                <span className="text-xs text-white/60">Mission in progress</span>
              </div>
              <h2 className="text-2xl font-light text-white">
                Analysing <span className="text-gradient font-medium">"{idea.length > 60 ? idea.slice(0, 60) + '…' : idea}"</span>
              </h2>
              <p className="mt-2 text-sm text-white/40">
                {steps.filter((s) => s.status === 'done').length} / {steps.length} agents complete
              </p>
            </div>

            {/* Crew sections */}
            {[1, 2, 3].map((crewId) => {
              const crewSteps = steps.filter((s) => s.crew === crewId);
              const crew = CREW_COLORS[crewId];
              const crewDone = crewSteps.every((s) => s.status === 'done');
              const crewActive = crewSteps.some((s) => s.status === 'running');

              return (
                <div key={crewId} className="mb-8">
                  {/* Crew header */}
                  <div className="mb-3 flex items-center gap-3">
                    <div
                      className="h-2 w-2 rounded-full"
                      style={{ background: crewDone ? '#10b981' : crewActive ? crew.color : 'rgba(255,255,255,0.2)' }}
                    />
                    <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                      Crew {crewId} — {crew.label}
                    </span>
                    {crewDone && <CheckCircle2 className="h-3.5 w-3.5 text-emerald" />}
                  </div>

                  {/* Agent cards */}
                  <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                    {crewSteps.map((step) => {
                      const isActive = step.status === 'running';
                      const isDone = step.status === 'done';

                      return (
                        <div
                          key={step.id}
                          className="relative overflow-hidden rounded-2xl border bg-charcoal/60 p-3 backdrop-blur-sm transition-all duration-500"
                          style={{
                            borderColor: isDone
                              ? `${crew.color}44`
                              : isActive
                              ? `${crew.color}66`
                              : 'rgba(255,255,255,0.06)',
                            boxShadow: isActive ? `0 0 20px -8px ${crew.color}` : 'none',
                          }}
                        >
                          {/* Pulsing ring when active */}
                          {isActive && (
                            <span
                              className="pointer-events-none absolute inset-0 rounded-2xl animate-ping"
                              style={{ border: `1px solid ${crew.color}`, animationDuration: '1.5s', opacity: 0.4 }}
                            />
                          )}

                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs font-medium text-white/80 leading-tight">{step.name}</span>
                            <span
                              className="shrink-0 rounded-full px-1.5 py-0.5 text-[8px] font-bold uppercase tracking-wider"
                              style={{
                                background: isDone
                                  ? 'rgba(16,185,129,0.15)'
                                  : isActive
                                  ? `${crew.color}22`
                                  : 'rgba(255,255,255,0.04)',
                                color: isDone ? '#10b981' : isActive ? crew.color : 'rgba(255,255,255,0.3)',
                              }}
                            >
                              {isDone ? '✓' : isActive ? 'Running' : 'Queue'}
                            </span>
                          </div>

                          {/* Progress bar */}
                          <div className="mt-2 h-0.5 overflow-hidden rounded-full bg-white/5">
                            <div
                              className="h-full rounded-full transition-all duration-100"
                              style={{
                                width: `${isDone ? 100 : step.progress * 100}%`,
                                background: `linear-gradient(90deg, ${crew.color}, ${crew.color2})`,
                                boxShadow: isActive ? `0 0 6px ${crew.color}` : 'none',
                              }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ── Completion State ── */}
        {status === 'done' && (
          <div className="flex min-h-[40vh] items-center justify-center animate-scale-in">
            <div className="gradient-border noise mx-auto max-w-md rounded-3xl bg-charcoal/50 p-8 text-center backdrop-blur-xl">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald to-teal">
                <Rocket className="h-7 w-7 text-white" />
              </div>
              <h3 className="mt-6 text-2xl font-light text-white">Analysis Complete</h3>
              <p className="mt-2 text-sm text-white/50">Loading your results…</p>
              <Loader2 className="mx-auto mt-4 h-5 w-5 animate-spin text-emerald" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
