import { useEffect, useState } from 'react';
import { Loader2, Plus, Sparkles, Trash2 } from 'lucide-react';
import { addExperiment, deleteExperiment, listExperiments, PaywallError, seedExperiments, updateExperiment } from '@/lib/api';
import type { Experiment } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { ErrorNote, UpgradeCard } from './shared';

const STATUSES: { value: Experiment['status']; label: string; color: string }[] = [
  { value: 'open', label: 'Open', color: '#94a3b8' },
  { value: 'running', label: 'Running', color: '#2d7ff9' },
  { value: 'validated', label: 'Validated', color: '#10b981' },
  { value: 'invalidated', label: 'Invalidated', color: '#ef4444' },
];

export default function ExperimentsPanel({ ideaId, hasReport }: { ideaId: string; hasReport: boolean }) {
  const [items, setItems] = useState<Experiment[] | null>(null);
  const [locked, setLocked] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);

  const guard = async <T,>(fn: () => Promise<T>): Promise<T | undefined> => {
    setError(null);
    try {
      return await fn();
    } catch (e) {
      if (e instanceof PaywallError) setLocked(e.message);
      else setError(e instanceof Error ? e.message : 'Something went wrong.');
    }
  };

  useEffect(() => {
    listExperiments(ideaId)
      .then(setItems)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : 'Could not load experiments.'));
  }, [ideaId]);

  const seed = async () => {
    setBusy(true);
    const created = await guard(() => seedExperiments(ideaId));
    if (created) setItems((all) => [...(all ?? []), ...created]);
    setBusy(false);
  };
  const add = async () => {
    if (text.trim().length < 3) return;
    const e = await guard(() => addExperiment(ideaId, { hypothesis: text.trim() }));
    if (e) {
      setItems((all) => [...(all ?? []), e]);
      setText('');
    }
  };
  const setStatus = async (e: Experiment, status: Experiment['status']) => {
    const next = await guard(() => updateExperiment(e.id, { status }));
    if (next) setItems((all) => (all ?? []).map((x) => (x.id === e.id ? next : x)));
  };
  const remove = async (e: Experiment) => {
    await guard(() => deleteExperiment(e.id));
    setItems((all) => (all ?? []).filter((x) => x.id !== e.id));
  };

  if (items === null && !error) return <Loader2 className="mx-auto mt-12 h-5 w-5 animate-spin text-electric" aria-label="Loading" />;

  return (
    <div className="space-y-4 rounded-2xl border border-white/[0.07] bg-charcoal/60 p-4">
      <p className="text-sm text-white/55">
        Turn the report&apos;s riskiest assumptions into tests. Mark each as you learn; re-run the analysis to see how the verdict moves.
      </p>
      <ErrorNote error={error} />
      {locked && <UpgradeCard message={locked} />}

      <ul className="space-y-2">
        {(items ?? []).map((e) => (
          <li key={e.id} className="rounded-xl border border-white/[0.07] bg-white/[0.03] p-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm text-white">{e.hypothesis}</p>
                {e.metric && <p className="mt-1 text-xs text-white/45">Measure: {e.metric}</p>}
              </div>
              <button onClick={() => remove(e)} aria-label="Delete experiment" className="shrink-0 text-white/30 hover:text-red-400">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
            <div className="mt-3 flex flex-wrap gap-1.5" role="group" aria-label="Status">
              {STATUSES.map((s) => (
                <button
                  key={s.value}
                  onClick={() => setStatus(e, s.value)}
                  aria-pressed={e.status === s.value}
                  className="rounded-full border px-2.5 py-1 text-[11px] transition-colors"
                  style={
                    e.status === s.value
                      ? { background: `${s.color}26`, color: s.color, borderColor: `${s.color}66` }
                      : { color: 'rgba(255,255,255,0.45)', borderColor: 'rgba(255,255,255,0.1)' }
                  }
                >
                  {s.label}
                </button>
              ))}
            </div>
          </li>
        ))}
      </ul>
      {items?.length === 0 && !locked && <p className="py-4 text-center text-sm text-white/40">No experiments yet.</p>}

      <div className="flex flex-wrap gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && add()}
          placeholder="Add your own hypothesis"
          aria-label="New hypothesis"
          maxLength={1000}
          className="min-w-0 flex-1 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white placeholder-white/30 focus:border-electric focus:outline-none"
        />
        <Button size="md" variant="outline" onClick={add} disabled={text.trim().length < 3}>
          <Plus className="h-4 w-4" aria-hidden="true" />
          Add
        </Button>
        <Button size="md" onClick={seed} loading={busy} disabled={!hasReport} title={hasReport ? undefined : 'Run an analysis first'}>
          <Sparkles className="h-4 w-4" aria-hidden="true" />
          From report
        </Button>
      </div>
    </div>
  );
}
