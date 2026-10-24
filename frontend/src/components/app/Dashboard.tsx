import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Archive, ArrowRight, Lightbulb, Loader2, Plus } from 'lucide-react';
import { listIdeas } from '@/lib/api';
import { timeAgo } from '@/lib/format';
import type { IdeaListItem } from '@/lib/types';
import { cn } from '@/lib/utils';
import { buttonVariants } from '@/components/ui/button';
import { AppPage, ErrorNote, useBilling, VerdictBadge } from './shared';

function IdeaCard({ idea }: { idea: IdeaListItem }) {
  const latest = idea.latest;
  return (
    <Link
      to={`/ideas/${idea.id}`}
      className="group flex flex-col rounded-2xl border border-white/[0.07] bg-charcoal/60 p-5 transition-colors hover:border-white/20"
    >
      <div className="flex items-start justify-between gap-3">
        <h2 className="line-clamp-2 text-base font-medium text-white">{idea.title}</h2>
        {latest && <VerdictBadge verdict={latest.verdict} className="shrink-0" />}
      </div>
      <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-white/50">{idea.idea_text}</p>

      <div className="mt-5 flex items-end justify-between gap-3">
        {latest?.overall_score != null ? (
          <div>
            <span className="font-serif text-4xl leading-none text-white">{Math.round(latest.overall_score)}</span>
            <span className="ml-1 text-xs text-white/40">/100 · v{latest.version}</span>
          </div>
        ) : (
          <span className="text-sm text-white/40">{idea.running ? 'Analysis running…' : 'Not analysed yet'}</span>
        )}
        <span className="flex items-center gap-1 text-xs text-white/40">
          {idea.running && <Loader2 className="h-3 w-3 animate-spin text-electric" aria-hidden="true" />}
          {timeAgo(idea.updated_at)}
          <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
        </span>
      </div>
    </Link>
  );
}

export default function Dashboard() {
  const [ideas, setIdeas] = useState<IdeaListItem[] | null>(null);
  const [archived, setArchived] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { billing } = useBilling();

  useEffect(() => {
    setIdeas(null);
    listIdeas(archived)
      .then(setIdeas)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : 'Could not load your ideas.'));
  }, [archived]);

  return (
    <AppPage wide>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-serif text-4xl text-white sm:text-5xl">Your ideas</h1>
          {billing && (
            <p className="mt-2 text-sm text-white/50">
              {billing.plan === 'pro'
                ? 'Pro plan · unlimited analyses'
                : `${Math.min(billing.analyses_used, billing.free_limit)} of ${billing.free_limit} free analyses used`}
              {billing.plan === 'free' && (
                <>
                  {' · '}
                  <Link to="/pricing" className="text-electric-300 hover:underline">
                    Upgrade
                  </Link>
                </>
              )}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setArchived((a) => !a)}
            aria-pressed={archived}
            className={cn(
              'flex h-10 items-center gap-2 rounded-full border px-4 text-sm transition-colors',
              archived ? 'border-white/30 text-white' : 'border-white/10 text-white/55 hover:text-white',
            )}
          >
            <Archive className="h-4 w-4" aria-hidden="true" />
            Archived
          </button>
          <Link to="/new" className={buttonVariants({ variant: 'shine' })}>
            <Plus className="h-4 w-4" aria-hidden="true" />
            New idea
          </Link>
        </div>
      </div>

      <div className="mt-8">
        <ErrorNote error={error} />
        {!error && ideas === null && <Loader2 className="mx-auto mt-20 h-6 w-6 animate-spin text-electric" aria-label="Loading ideas" />}
        {ideas?.length === 0 && (
          <div className="mt-6 flex flex-col items-center rounded-3xl border border-dashed border-white/15 px-6 py-20 text-center">
            <Lightbulb className="h-8 w-8 text-electric" aria-hidden="true" />
            <h2 className="mt-4 font-serif text-2xl text-white">{archived ? 'Nothing archived' : 'Start with one idea'}</h2>
            <p className="mt-2 max-w-sm text-sm text-white/50">
              {archived
                ? 'Ideas you archive show up here.'
                : 'Describe it in a sentence or two. You get a verdict, the risks, and the evidence behind them.'}
            </p>
            {!archived && (
              <Link to="/new" className={cn(buttonVariants({ variant: 'shine' }), 'mt-6')}>
                Analyze an idea
              </Link>
            )}
          </div>
        )}
        {ideas && ideas.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {ideas.map((i) => (
              <IdeaCard key={i.id} idea={i} />
            ))}
          </div>
        )}
      </div>
    </AppPage>
  );
}
