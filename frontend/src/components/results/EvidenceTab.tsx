import { useMemo, useState } from 'react';
import { CheckCircle2, HelpCircle, XCircle, ExternalLink, Github, Newspaper } from 'lucide-react';
import type { AnalysisResult, LedgerEntry } from '@/lib/types';
import { crewMeta } from '@/lib/report';
import { cn } from '@/lib/utils';
import { Empty, SectionCard } from './primitives';

const STATUS = {
  supported: { label: 'Supported', color: '#10b981', icon: CheckCircle2 },
  unsupported: { label: 'No source found', color: '#94a3b8', icon: HelpCircle },
  contradicted: { label: 'Contradicted', color: '#ef4444', icon: XCircle },
} as const;

type Filter = 'all' | LedgerEntry['status'];

function Entry({ e }: { e: LedgerEntry }) {
  const st = STATUS[e.status];
  const Icon = st.icon;
  return (
    <li className="py-3 first:pt-0 last:pb-0">
      <div className="flex items-start gap-3">
        <Icon className="mt-0.5 h-4 w-4 shrink-0" style={{ color: st.color }} aria-label={st.label} />
        <div className="min-w-0">
          <p className="text-sm text-white/85">{e.claim}</p>
          {e.quote && <blockquote className="mt-2 border-l-2 pl-3 text-xs italic leading-relaxed text-white/55" style={{ borderColor: `${st.color}66` }}>“{e.quote}”</blockquote>}
          {e.source && (
            <a href={e.source.url} target="_blank" rel="noreferrer" className="mt-1.5 inline-flex max-w-full items-center gap-1 truncate text-xs text-electric-300 hover:underline">
              <ExternalLink className="h-3 w-3 shrink-0" aria-hidden="true" />
              <span className="truncate">{e.source.title || e.source.url}</span>
            </a>
          )}
        </div>
      </div>
    </li>
  );
}

export default function EvidenceTab({ result }: { result: AnalysisResult }) {
  const [filter, setFilter] = useState<Filter>('all');
  const ledger = useMemo(() => result.ledger ?? [], [result.ledger]);
  const counts = useMemo(
    () => ({
      supported: ledger.filter((e) => e.status === 'supported').length,
      unsupported: ledger.filter((e) => e.status === 'unsupported').length,
      contradicted: ledger.filter((e) => e.status === 'contradicted').length,
    }),
    [ledger],
  );
  const groups = useMemo(() => {
    const m = new Map<string, LedgerEntry[]>();
    for (const e of ledger) if (filter === 'all' || e.status === filter) m.set(e.crew, [...(m.get(e.crew) ?? []), e]);
    return [...m.entries()];
  }, [ledger, filter]);

  if (!ledger.length && !(result.sources?.length ?? 0)) return <Empty what="Evidence" />;
  const gh = result.signals?.github ?? [];
  const hn = result.signals?.hacker_news;

  return (
    <div className="space-y-6">
      <p className="max-w-prose text-sm leading-relaxed text-white/60">
        After the crews finished, a verifier extracted their checkable claims and looked for a sentence in the gathered sources that states
        each one. A claim is only marked supported if the quote appears word for word in the source.
      </p>

      {ledger.length > 0 && (
        <>
          <div className="flex flex-wrap gap-2" role="group" aria-label="Filter claims">
            {(['all', 'supported', 'unsupported', 'contradicted'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                aria-pressed={filter === f}
                className={cn(
                  'rounded-full border px-3.5 py-1.5 text-xs transition-colors',
                  filter === f ? 'border-white/30 bg-white/10 text-white' : 'border-white/10 text-white/50 hover:text-white',
                )}
              >
                {f === 'all' ? `All ${ledger.length}` : `${STATUS[f].label} ${counts[f]}`}
              </button>
            ))}
          </div>

          {groups.map(([crew, entries]) => (
            <section key={crew} className="rounded-2xl border border-white/[0.06] bg-white/[0.025] p-5">
              <h3 className="mb-4 text-sm font-medium text-white" style={{ color: crewMeta(crew).color }}>
                {crewMeta(crew).label}
              </h3>
              <ul className="divide-y divide-white/[0.06]">
                {entries.map((e, i) => (
                  <Entry key={i} e={e} />
                ))}
              </ul>
            </section>
          ))}
        </>
      )}

      {gh.length > 0 && (
        <SectionCard title="Related projects on GitHub" icon={Github} color="#8b5cf6">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[30rem] text-left text-sm">
              <thead className="text-xs text-white/40">
                <tr>
                  <th className="pb-2 font-normal">Repository</th>
                  <th className="pb-2 text-right font-normal">Stars</th>
                  <th className="pb-2 text-right font-normal">Open issues</th>
                  <th className="pb-2 text-right font-normal">Last push</th>
                </tr>
              </thead>
              <tbody>
                {gh.map((r) => (
                  <tr key={r.full_name} className="border-t border-white/[0.05]">
                    <td className="py-2 pr-3">
                      <a href={r.url} target="_blank" rel="noreferrer" className="text-electric-300 hover:underline">
                        {r.full_name}
                      </a>
                      {r.archived && <span className="ml-2 text-[10px] text-white/40">archived</span>}
                      <p className="line-clamp-1 text-xs text-white/40">{r.description}</p>
                    </td>
                    <td className="py-2 text-right font-mono text-white/70">{r.stars.toLocaleString('en-IN')}</td>
                    <td className="py-2 text-right font-mono text-white/70">{r.open_issues}</td>
                    <td className="py-2 text-right text-xs text-white/50">{r.pushed_at?.slice(0, 10) ?? 'n/a'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>
      )}

      {hn && hn.stories.length > 0 && (
        <SectionCard title={`Hacker News · ${hn.total.toLocaleString('en-IN')} stories on “${hn.query}”`} icon={Newspaper} color="#fb923c">
          <ul className="space-y-2 text-sm">
            {hn.stories.map((s) => (
              <li key={s.url} className="flex justify-between gap-3">
                <a href={s.url} target="_blank" rel="noreferrer" className="min-w-0 truncate text-white/75 hover:text-white">
                  {s.title}
                </a>
                <span className="shrink-0 font-mono text-xs text-white/40">
                  {s.points} pts · {s.comments} comments
                </span>
              </li>
            ))}
          </ul>
        </SectionCard>
      )}

      {(result.sources?.length ?? 0) > 0 && (
        <details className="rounded-2xl border border-white/[0.06] bg-white/[0.025] p-5">
          <summary className="cursor-pointer text-sm text-white/70">All {result.sources!.length} sources gathered</summary>
          <ol className="mt-4 space-y-1.5 text-xs">
            {result.sources!.map((s) => (
              <li key={s.id} className="truncate">
                <span className="mr-2 font-mono text-white/30">[{s.id}]</span>
                <a href={s.url} target="_blank" rel="noreferrer" className="text-white/60 hover:text-white">
                  {s.title || s.url}
                </a>
              </li>
            ))}
          </ol>
        </details>
      )}
    </div>
  );
}
