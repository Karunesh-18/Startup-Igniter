import { useState } from 'react';
import {
  ArrowLeft, Rocket, Sparkles, Zap, AlertTriangle, Loader2,
  CheckCircle2, Brain, Network, Lightbulb,
} from 'lucide-react';
import NeuralBackground from './NeuralBackground';
import { useScrollReveal } from '@/hooks/useScrollReveal';
import { runAnalysis } from '@/lib/api';
import type { AnalysisResult } from '@/lib/types';

const EXAMPLES = [
  'AI-powered legal contract reviewer for small businesses',
  'Carbon credit marketplace for regenerative agriculture',
  'Mental health companion app for Gen Z using voice AI',
  'Decentralized GPU marketplace for indie AI developers',
  'Autonomous warehouse robots with multi-agent AI for inventory management',
];

// Rotating status messages during API call
const LOADING_MESSAGES = [
  'Running Idea Validation agents…',
  'Researching market landscape…',
  'Mining patent databases…',
  'Assessing technical feasibility…',
  'Designing revenue model…',
  'Scoping the MVP roadmap…',
  'Auditing legal & compliance…',
  'Crafting brand identity…',
  'Matching investors…',
  'Modelling growth loops…',
  'Building final report…',
  'Synthesising all 66 agents…',
];

type Status = 'idle' | 'running' | 'done' | 'error';

interface Props {
  onBack: () => void;
  onComplete: (result: AnalysisResult) => void;
}

export default function AnalysisPage({ onBack, onComplete }: Props) {
  useScrollReveal();
  const [idea, setIdea] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState<string | null>(null);
  const [msgIdx, setMsgIdx] = useState(0);

  const launch = async () => {
    if (!idea.trim()) return;
    setStatus('running');
    setError(null);

    // Cycle through status messages
    const interval = setInterval(() => {
      setMsgIdx((i) => (i + 1) % LOADING_MESSAGES.length);
    }, 3500);

    try {
      const result = await runAnalysis({ idea_text: idea.trim(), mock_mode: false });
      clearInterval(interval);
      setStatus('done');
      setTimeout(() => onComplete(result), 800);
    } catch (err: any) {
      clearInterval(interval);
      setError(err?.message ?? 'Analysis failed. Please try again.');
      setStatus('error');
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-void">
      <div className="absolute inset-0 opacity-40">
        <NeuralBackground density={0.4} />
      </div>
      <div className="absolute inset-0 radial-spotlight" />

      <div className="relative z-10 mx-auto max-w-4xl px-6 py-12">
        <button
          onClick={onBack}
          disabled={status === 'running'}
          className="mb-8 flex items-center gap-2 text-sm text-white/50 transition-colors hover:text-white disabled:pointer-events-none disabled:opacity-30"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </button>

        {/* ── Idle / Error Input ── */}
        {status !== 'running' && status !== 'done' && (
          <div>
            <div className="reveal text-center">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5">
                <Sparkles className="h-3.5 w-3.5 text-violet" />
                <span className="text-xs text-white/60">New Mission · 12 Crews · 66 Agents</span>
              </div>
              <h1 className="text-4xl font-light leading-tight text-white sm:text-5xl">
                What are we <span className="font-serif italic text-gradient">building</span>?
              </h1>
              <p className="mx-auto mt-4 max-w-xl text-white/50">
                Describe your startup idea in 1–3 sentences. Our 66 AI agents across 12 specialized crews will analyse it end-to-end and generate an investor-ready report.
              </p>
            </div>

            {/* Input */}
            <div className="reveal mt-10 gradient-border noise relative overflow-hidden rounded-3xl bg-charcoal/50 p-2 backdrop-blur-xl">
              <textarea
                value={idea}
                onChange={(e) => setIdea(e.target.value)}
                placeholder="e.g. An AI platform that turns startup ideas into investor-ready companies…"
                rows={4}
                className="w-full resize-none rounded-2xl bg-transparent px-5 py-4 text-lg text-white placeholder-white/25 focus:outline-none"
              />
              <div className="flex items-center justify-between px-4 pb-3">
                <div className="flex items-center gap-2 text-xs text-white/30">
                  <Zap className="h-3.5 w-3.5 text-electric" />
                  {idea.length} chars · 12 crews · 66 agents
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

            {/* Error */}
            {status === 'error' && error && (
              <div className="mt-8 flex items-start gap-3 rounded-2xl border border-red-500/20 bg-red-500/10 p-4">
                <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />
                <div>
                  <div className="text-sm font-medium text-red-300">Analysis failed</div>
                  <div className="mt-1 text-xs text-red-400/80">{error}</div>
                  <button
                    onClick={launch}
                    className="mt-3 flex items-center gap-1.5 text-xs text-red-300 hover:text-red-200"
                  >
                    <Rocket className="h-3.5 w-3.5" /> Retry
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Running ── */}
        {status === 'running' && (
          <div className="animate-fade-up flex min-h-[70vh] flex-col items-center justify-center">
            {/* Orbital animation */}
            <div className="relative mb-10 flex h-40 w-40 items-center justify-center">
              {/* Outer ring */}
              <div className="absolute inset-0 rounded-full border border-electric/20 animate-spin-slow" />
              <div className="absolute inset-3 rounded-full border border-violet/15 animate-spin-slower" />
              <div className="absolute inset-6 rounded-full border border-teal/10 animate-spin-slow" />
              {/* Core */}
              <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-electric to-violet shadow-[0_0_40px_rgba(45,127,249,0.5)]">
                <Brain className="h-8 w-8 text-white" />
              </div>
              {/* Orbiting dots */}
              {[0, 60, 120, 180, 240, 300].map((deg) => (
                <div
                  key={deg}
                  className="absolute h-2 w-2 rounded-full bg-electric/70 animate-spin-slow"
                  style={{
                    transformOrigin: '70px 70px',
                    transform: `rotate(${deg}deg) translateX(56px)`,
                    animationDelay: `${deg / 360}s`,
                  }}
                />
              ))}
            </div>

            <div className="text-center">
              <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-electric" />
                <span className="text-xs text-white/60">Mission in progress</span>
              </div>

              <h2 className="mt-4 text-2xl font-light text-white">
                Analysing <span className="text-gradient font-medium">"{idea.length > 55 ? idea.slice(0, 55) + '…' : idea}"</span>
              </h2>

              <p className="mt-4 text-sm text-white/50 transition-all duration-700 min-h-[1.5rem]">
                {LOADING_MESSAGES[msgIdx]}
              </p>
            </div>

            {/* Phase progress indicators */}
            <div className="mt-12 grid grid-cols-4 gap-2 sm:grid-cols-6 lg:grid-cols-12">
              {Array.from({ length: 12 }, (_, i) => (
                <div
                  key={i}
                  className="flex flex-col items-center gap-1"
                >
                  <div
                    className="h-1 w-full rounded-full"
                    style={{
                      background: msgIdx > i
                        ? 'linear-gradient(90deg, #2d7ff9, #8b5cf6)'
                        : msgIdx === i
                        ? 'rgba(45,127,249,0.5)'
                        : 'rgba(255,255,255,0.06)',
                      boxShadow: msgIdx === i ? '0 0 8px rgba(45,127,249,0.6)' : 'none',
                      animation: msgIdx === i ? 'shimmer 1.5s infinite' : 'none',
                      backgroundSize: msgIdx === i ? '200% 100%' : 'auto',
                    }}
                  />
                  <span className="font-mono text-[8px] text-white/20">{String(i + 1).padStart(2, '0')}</span>
                </div>
              ))}
            </div>

            <p className="mt-6 text-xs text-white/25">
              66 agents · 12 crews · This may take a few minutes
            </p>
          </div>
        )}

        {/* ── Done ── */}
        {status === 'done' && (
          <div className="flex min-h-[60vh] items-center justify-center animate-scale-in">
            <div className="gradient-border noise mx-auto max-w-md rounded-3xl bg-charcoal/50 p-8 text-center backdrop-blur-xl">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald to-teal shadow-[0_0_30px_rgba(16,185,129,0.4)]">
                <CheckCircle2 className="h-7 w-7 text-white" />
              </div>
              <h3 className="mt-6 text-2xl font-light text-white">Analysis Complete</h3>
              <p className="mt-2 text-sm text-white/50">Loading your investor report…</p>
              <Loader2 className="mx-auto mt-4 h-5 w-5 animate-spin text-emerald" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
