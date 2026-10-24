import { useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { rescanIdea, type Rescan } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { ApiErrorNote } from './shared';

/** Pro: re-check GitHub and Hacker News and show what changed since the last report. */
export default function RescanPanel({ ideaId }: { ideaId: string }) {
  const [data, setData] = useState<Rescan | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      setData(await rescanIdea(ideaId));
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Rescan failed.'));
    } finally {
      setBusy(false);
    }
  };

  const nothing = data && !data.new_repos.length && !data.star_changes.length && data.hn_total_now === data.hn_total_before;

  return (
    <section className="rounded-2xl border border-white/[0.07] bg-charcoal/60 p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm text-white">Market watch</h2>
          <p className="mt-1 text-xs text-white/45">Check for new competing projects and press since your last report.</p>
        </div>
        <Button size="sm" variant="outline" onClick={run} loading={busy}>
          <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
          Check now
        </Button>
      </div>
      <div className="mt-3">
        <ApiErrorNote error={error} />
      </div>
      {data && (
        <div className="mt-4 space-y-3 text-sm">
          {nothing && <p className="text-white/55">No changes since v{data.since_version}.</p>}
          {data.new_repos.length > 0 && (
            <div>
              <p className="text-xs text-white/45">New projects</p>
              <ul className="mt-1 space-y-1">
                {data.new_repos.map((r) => (
                  <li key={r.full_name}>
                    <a href={r.url} target="_blank" rel="noreferrer" className="text-electric-300 hover:underline">
                      {r.full_name}
                    </a>{' '}
                    <span className="text-xs text-white/40">{r.stars.toLocaleString('en-IN')} stars</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {data.star_changes.length > 0 && (
            <div>
              <p className="text-xs text-white/45">Star changes</p>
              <ul className="mt-1 space-y-1">
                {data.star_changes.map((r) => (
                  <li key={r.full_name} className="text-white/75">
                    {r.full_name}: {r.from.toLocaleString('en-IN')} to {r.to.toLocaleString('en-IN')}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {data.hn_total_before != null && data.hn_total_now !== data.hn_total_before && (
            <p className="text-white/70">
              Hacker News stories on this topic: {data.hn_total_before.toLocaleString('en-IN')} to {data.hn_total_now.toLocaleString('en-IN')}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
