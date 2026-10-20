import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { AlertTriangle, ArrowLeft, Check, Loader2, X } from 'lucide-react';
import { runAnalysisStream } from '@/lib/api';
import { CREW_KEYS, crewMeta, crewScore, crewSummary, saveResult } from '@/lib/report';
import type { StreamEvent } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { BackgroundBeams } from '@/components/ui/background-beams';

const EXAMPLES = [
  'AI-powered legal contract reviewer for small businesses',
  'Carbon credit marketplace for regenerative agriculture',
  'Mental health companion app for Gen Z using voice AI',
  'Decentralized GPU marketplace for indie AI developers',
];

type Phase = 'idle' | 'running' | 'error';
type RowStatus = 'pending' | 'running' | 'done' | 'error';

interface Row {
  key: string;
  label: string;
  done: boolean;
  result?: unknown;
}

const initialRows = (): Row[] => CREW_KEYS.map((key) => ({ key, label: crewMeta(key).label, done: false }));

const fmtTime = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;

export default function AnalysisPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [idea, setIdea] = useState<string>((location.state as { idea?: string } | null)?.idea ?? '');
  const [phase, setPhase] = useState<Phase>('idle');
  const [error, setError] = useState<string | null>(null);
  const [rows, setRows] = useState<Row[]>(initialRows);
  const [elapsed, setElapsed] = useState(0);
  const abortRef = useRef<AbortController | null>(null);

  // Elapsed timer while a run is in flight.
  useEffect(() => {
    if (phase !== 'running') return;
    const started = Date.now();
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(id);
  }, [phase]);

  // Abort an in-flight run if the user navigates away.
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const onEvent = (ev: StreamEvent) => {
    if (ev.type === 'started') {
      // Order rows by the backend's crew list; labels it adds that we don't know become extra rows.
      setRows((prev) => {
        const byLabel = new Map(prev.map((r) => [r.label, r]));
        const ordered = ev.crews.map((label) => byLabel.get(label) ?? { key: label, label, done: false });
        return [...ordered, ...prev.filter((r) => !ev.crews.includes(r.label))];
      });
    } else if (ev.type === 'crew_complete') {
      setRows((prev) => {
        const i = prev.findIndex((r) => r.key === ev.crew || r.label === ev.label);
        const row = { key: ev.crew, label: ev.label || crewMeta(ev.crew).label, done: true, result: ev.result };
        return i >= 0 ? prev.map((r, j) => (j === i ? row : r)) : [...prev, row];
      });
    }
  };

  const launch = async () => {
    if (!idea.trim()) return;
    const controller = new AbortController();
    abortRef.current = controller;
    setRows(initialRows());
    setElapsed(0);
    setError(null);
    setPhase('running');
    try {
      const result = await runAnalysisStream({ idea_text: idea.trim(), mock_mode: false }, onEvent, controller.signal);
      saveResult(result);
      navigate(`/results/${encodeURIComponent(result.project_id)}`, { state: { result } });
    } catch (err) {
      if (controller.signal.aborted) {
        setPhase('idle');
        setError('Analysis cancelled. Crews that already finished are not saved.');
      } else {
        setPhase('error');
        setError(err instanceof Error ? err.message : 'Analysis failed. Check that the backend is running, then try again.');
      }
    } finally {
      abortRef.current = null;
    }
  };

  const cancel = () => abortRef.current?.abort();

  // The first unfinished row is the one in flight.
  const runningIdx = rows.findIndex((r) => !r.done);
  const statusOf = (i: number): RowStatus =>
    rows[i].done ? 'done' : i === runningIdx ? (phase === 'running' ? 'running' : phase === 'error' ? 'error' : 'pending') : 'pending';
  const doneCount = rows.filter((r) => r.done).length;
  const showTimeline = phase !== 'idle' || doneCount > 0;

  return (
    <div className="relative isolate min-h-screen overflow-hidden bg-void">
      <BackgroundBeams className="-z-10 opacity-40" />

      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-12">
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-white/50 transition-colors hover:text-white">
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Home
        </Link>

        <h1 className="mt-10 font-serif text-4xl leading-tight text-white sm:text-6xl">What are you building?</h1>
        <p className="mt-4 max-w-xl text-white/60">
          Describe the idea in one to three sentences. Twelve crews will work through it in order; you can watch each one finish.
        </p>

        <form
          className="mt-8 rounded-3xl border border-white/[0.12] bg-charcoal/70 p-2 backdrop-blur-xl"
          onSubmit={(e) => {
            e.preventDefault();
            launch();
          }}
        >
          <label htmlFor="idea" className="sr-only">
            Startup idea
          </label>
          <textarea
            id="idea"
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            disabled={phase === 'running'}
            placeholder="e.g. An app that matches home cooks with neighbours who want a weekly meal plan"
            rows={4}
            maxLength={5000}
            className="w-full resize-none rounded-2xl bg-transparent px-4 py-3 text-lg text-white placeholder-white/30 focus:outline-none disabled:opacity-60"
          />
          <div className="flex items-center justify-between gap-3 px-3 pb-2">
            <span className="text-xs text-white/35">{idea.length} / 5000</span>
            {phase === 'running' ? (
              <Button type="button" variant="danger" size="md" onClick={cancel}>
                <X className="h-4 w-4" aria-hidden="true" />
                Cancel
              </Button>
            ) : (
              <Button type="submit" variant="shine" size="md" disabled={!idea.trim()}>
                {phase === 'error' ? 'Retry analysis' : 'Start analysis'}
              </Button>
            )}
          </div>
        </form>

        {!showTimeline && (
          <div className="mt-6 flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                onClick={() => setIdea(ex)}
                className="rounded-full border border-white/10 px-3.5 py-1.5 text-xs text-white/60 transition-colors hover:border-white/25 hover:text-white"
              >
                {ex}
              </button>
            ))}
          </div>
        )}

        {error && (
          <div role="alert" className="mt-6 flex items-start gap-3 rounded-2xl border border-red-500/25 bg-red-500/10 p-4 text-sm">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" aria-hidden="true" />
            <span className="text-red-200">{error}</span>
          </div>
        )}

        {showTimeline && (
          <section className="mt-12" aria-label="Crew progress">
            <div className="flex items-baseline justify-between">
              <h2 className="text-lg font-medium text-white">
                {doneCount} of {rows.length} crews done
              </h2>
              <span className="font-mono text-sm tabular-nums text-white/50" aria-label="Elapsed time">
                {fmtTime(elapsed)}
              </span>
            </div>

            <ol className="mt-6" aria-live="polite">
              {rows.map((row, i) => {
                const status = statusOf(i);
                const meta = crewMeta(row.key, row.label);
                const score = crewScore(row.result);
                const summary = crewSummary(row.result);
                return (
                  <li key={row.key} className="relative flex gap-4 pb-6 last:pb-0">
                    {i < rows.length - 1 && (
                      <span
                        aria-hidden="true"
                        className={cn('absolute left-[11px] top-7 h-[calc(100%-1.75rem)] w-px', row.done ? 'bg-teal/50' : 'bg-white/10')}
                      />
                    )}
                    <span
                      className={cn(
                        'relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-[10px]',
                        status === 'done' && 'border-teal bg-teal text-void',
                        status === 'running' && 'border-electric text-electric',
                        status === 'error' && 'border-red-400 text-red-400',
                        status === 'pending' && 'border-white/15 text-white/30',
                      )}
                    >
                      {status === 'done' ? (
                        <Check className="h-3.5 w-3.5" aria-hidden="true" />
                      ) : status === 'running' ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                      ) : status === 'error' ? (
                        <X className="h-3.5 w-3.5" aria-hidden="true" />
                      ) : (
                        i + 1
                      )}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-baseline justify-between gap-3">
                        <span className={cn('text-sm', status === 'pending' ? 'text-white/40' : 'text-white')}>
                          {meta.label}
                          <span className="sr-only">: {status}</span>
                        </span>
                        {score != null && <span className="font-mono text-xs tabular-nums text-white/50">{Math.round(score)}/100</span>}
                      </div>
                      {status === 'running' && <p className="mt-1 text-xs text-electric-300">Working…</p>}
                      {summary && <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-white/50">{summary}</p>}
                    </div>
                  </li>
                );
              })}
            </ol>
          </section>
        )}
      </div>
    </div>
  );
}
