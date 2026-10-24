import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Check, Loader2, Search, ShieldCheck, X } from 'lucide-react';
import { cancelAnalysis, getAnalysis, streamAnalysis } from '@/lib/api';
import { crewMeta, crewScore, crewSummary } from '@/lib/report';
import type { StreamEvent } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { BackgroundBeams } from '@/components/ui/background-beams';
import { ErrorNote } from '@/components/app/shared';

type RowStatus = 'pending' | 'running' | 'done' | 'failed';
interface Row {
  key: string;
  label: string;
  status: RowStatus;
  agent?: string;
  agentsDone: number;
  result?: unknown;
}
type Stage = 'sources' | 'verify';
type Phase = 'connecting' | 'queued' | 'running' | 'failed' | 'cancelled';

const STAGES: Record<Stage, { label: string; icon: typeof Search; after: string | null }> = {
  sources: { label: 'Gathering research sources', icon: Search, after: 'idea_validation' },
  verify: { label: 'Checking claims against sources', icon: ShieldCheck, after: null },
};

/** "StartupIdeaAnalysis" -> "Startup Idea Analysis" */
const humanize = (s: string) => s.replace(/([a-z])([A-Z])/g, (_m, a: string, b: string) => `${a} ${b}`).replace(/Result$/, '').trim();
const fmtTime = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;

export default function AnalysisPage() {
  const id = useParams().id ?? '';
  const navigate = useNavigate();
  const [rows, setRows] = useState<Row[]>([]);
  const [stages, setStages] = useState<Partial<Record<Stage, 'running' | 'done'>>>({});
  const [phase, setPhase] = useState<Phase>('connecting');
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [ideaId, setIdeaId] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (phase !== 'running' && phase !== 'queued') return;
    const started = Date.now();
    const t = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(t);
  }, [phase]);

  const onEvent = useCallback(
    (ev: StreamEvent) => {
      switch (ev.type) {
        case 'queued':
          setPhase('queued');
          break;
        case 'started':
          setPhase('running');
          setRows(ev.keys.map((key, i) => ({ key, label: ev.crews[i], status: 'pending', agentsDone: 0 })));
          break;
        case 'crew_start':
          setRows((rs) => rs.map((r) => (r.key === ev.crew ? { ...r, status: 'running' } : r)));
          break;
        case 'agent':
          setRows((rs) =>
            rs.map((r) =>
              r.key !== ev.crew
                ? r
                : ev.status === 'start'
                  ? { ...r, agent: humanize(ev.agent) }
                  : { ...r, agentsDone: r.agentsDone + 1 },
            ),
          );
          break;
        case 'crew_complete':
          setRows((rs) => rs.map((r) => (r.key === ev.crew ? { ...r, status: 'done', agent: undefined, result: ev.result } : r)));
          break;
        case 'crew_failed':
          setRows((rs) => rs.map((r) => (r.key === ev.crew ? { ...r, status: 'failed', agent: undefined } : r)));
          break;
        case 'stage':
          setStages((s) => ({ ...s, [ev.stage]: 'running' }));
          if (ev.stage === 'verify') setStages((s) => ({ ...s, sources: 'done' }));
          break;
        case 'sources':
          setStages((s) => ({ ...s, sources: 'done' }));
          break;
        case 'complete':
          navigate(`/results/${id}`, { replace: true });
          break;
        case 'cancelled':
          setPhase('cancelled');
          break;
        case 'error':
          setPhase('failed');
          setError(ev.error);
          break;
      }
    },
    [id, navigate],
  );

  useEffect(() => {
    const controller = new AbortController();
    abortRef.current = controller;
    (async () => {
      try {
        const a = await getAnalysis(id);
        setIdeaId(a.idea_id);
        if (a.status === 'complete') return navigate(`/results/${id}`, { replace: true });
        if (a.status === 'failed') {
          setPhase('failed');
          return setError(a.error ?? 'The analysis failed.');
        }
        if (a.status === 'cancelled') return setPhase('cancelled');
        await streamAnalysis(id, onEvent, controller.signal);
        // The stream ended without a terminal event (e.g. server restart): re-check the stored status.
        const after = await getAnalysis(id);
        if (after.status === 'complete') navigate(`/results/${id}`, { replace: true });
        else if (after.status !== 'running') {
          setPhase(after.status === 'cancelled' ? 'cancelled' : 'failed');
          setError(after.error);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setPhase('failed');
          setError(err instanceof Error ? err.message : 'Lost connection to the server.');
        }
      }
    })();
    return () => controller.abort(); // leaving the page does not cancel the run; it keeps going server-side
  }, [id, navigate, onEvent]);

  const done = rows.filter((r) => r.status === 'done' || r.status === 'failed').length;
  const active = phase === 'running' || phase === 'queued' || phase === 'connecting';

  return (
    <div className="relative isolate min-h-screen overflow-hidden bg-void">
      <BackgroundBeams className="-z-10 opacity-40" />
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-12">
        <Link
          to={ideaId ? `/ideas/${ideaId}` : '/app'}
          className="inline-flex items-center gap-2 text-sm text-white/50 transition-colors hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          {ideaId ? 'Back to idea' : 'Your ideas'}
        </Link>

        <h1 className="mt-10 font-serif text-4xl leading-tight text-white sm:text-5xl">
          {phase === 'failed' ? 'The analysis stopped' : phase === 'cancelled' ? 'Analysis cancelled' : 'Analysing your idea'}
        </h1>
        <p className="mt-3 max-w-xl text-white/55">
          {active
            ? 'This takes several minutes. You can leave this page; the run continues and appears on your dashboard.'
            : phase === 'cancelled'
              ? 'Finished crews were not saved. Start a new run from the idea page.'
              : ''}
        </p>

        <div className="mt-6 space-y-4">
          <ErrorNote error={phase === 'failed' ? error : null} />
          {phase === 'queued' && (
            <p className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-white/70">
              Waiting for a free slot on the model servers. Your run starts automatically.
            </p>
          )}
        </div>

        {rows.length > 0 && (
          <section className="mt-10" aria-label="Crew progress">
            <div className="flex items-baseline justify-between">
              <h2 className="text-lg font-medium text-white">
                {done} of {rows.length} crews done
              </h2>
              <span className="font-mono text-sm tabular-nums text-white/50" aria-label="Elapsed time">
                {fmtTime(elapsed)}
              </span>
            </div>

            <ol className="mt-6" aria-live="polite">
              {rows.map((row, i) => {
                const meta = crewMeta(row.key, row.label);
                const score = crewScore(row.result);
                const summary = crewSummary(row.result);
                const stage = (Object.entries(STAGES) as [Stage, (typeof STAGES)[Stage]][]).find(([, s]) => s.after === row.key);
                return (
                  <li key={row.key}>
                    <div className="relative flex gap-4 pb-6">
                      {i < rows.length - 1 && (
                        <span
                          aria-hidden="true"
                          className={cn('absolute left-[11px] top-7 h-[calc(100%-1.75rem)] w-px', row.status === 'done' ? 'bg-teal/50' : 'bg-white/10')}
                        />
                      )}
                      <span
                        className={cn(
                          'relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-[10px]',
                          row.status === 'done' && 'border-teal bg-teal text-void',
                          row.status === 'running' && 'border-electric text-electric',
                          row.status === 'failed' && 'border-red-400 text-red-400',
                          row.status === 'pending' && 'border-white/15 text-white/30',
                        )}
                      >
                        {row.status === 'done' ? (
                          <Check className="h-3.5 w-3.5" aria-hidden="true" />
                        ) : row.status === 'failed' ? (
                          <X className="h-3.5 w-3.5" aria-hidden="true" />
                        ) : row.status === 'running' ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                        ) : (
                          i + 1
                        )}
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-baseline justify-between gap-3">
                          <span className={cn('text-sm', row.status === 'pending' ? 'text-white/40' : 'text-white')}>
                            {meta.label}
                            <span className="sr-only">: {row.status}</span>
                          </span>
                          {score != null && <span className="font-mono text-xs tabular-nums text-white/50">{Math.round(score)}/100</span>}
                        </div>
                        {row.status === 'running' && (
                          <p className="mt-1 text-xs text-electric-300">{row.agent ? `${row.agent}…` : 'Working…'}</p>
                        )}
                        {row.status === 'failed' && <p className="mt-1 text-xs text-red-300">Could not be generated; the rest of the report is unaffected.</p>}
                        {summary && <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-white/50">{summary}</p>}
                      </div>
                    </div>
                    {stage && stages[stage[0]] && <StageRow stage={stage[0]} state={stages[stage[0]]!} />}
                  </li>
                );
              })}
              {stages.verify && <StageRow stage="verify" state={stages.verify} last />}
            </ol>
          </section>
        )}

        {(active || phase === 'failed') && (
          <div className="mt-10 flex gap-3">
            {active && (
              <Button variant="danger" onClick={() => cancelAnalysis(id).catch(() => undefined)}>
                <X className="h-4 w-4" aria-hidden="true" />
                Cancel run
              </Button>
            )}
            {phase === 'failed' && ideaId && (
              <Link to={`/ideas/${ideaId}`} className="inline-flex h-10 items-center rounded-full border border-white/15 px-5 text-sm text-white/85 hover:border-white/30">
                Back to idea
              </Link>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function StageRow({ stage, state, last = false }: { stage: Stage; state: 'running' | 'done'; last?: boolean }) {
  const { label, icon: Icon } = STAGES[stage];
  return (
    <div className={cn('flex items-center gap-4 pb-6 pl-0', last && 'pb-0')}>
      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-violet/50 text-violet-300">
        {state === 'running' ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" /> : <Icon className="h-3.5 w-3.5" aria-hidden="true" />}
      </span>
      <span className="text-sm text-violet-300">
        {label}
        {state === 'done' && ' ✓'}
      </span>
    </div>
  );
}
