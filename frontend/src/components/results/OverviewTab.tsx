import { ChevronRight, FileText, Lock, Target } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { AnalysisResult } from '@/lib/types';
import { CREW_KEYS, crewMeta } from '@/lib/report';
import { cn } from '@/lib/utils';
import { buttonVariants } from '@/components/ui/button';
import { CrewRadar } from './charts';
import { SectionCard, StatCard } from './primitives';
import VerdictHero from './VerdictHero';

export default function OverviewTab({ result, locked = false, price }: { result: AnalysisResult; locked?: boolean; price: string }) {
  const iv = result.idea_validation;
  const mr = result.market_research;
  const rp = result.research_patent;
  const summary = result.executive_summary ?? result.reporting?.executive_summary;
  const recs = result.strategic_recommendations?.length
    ? result.strategic_recommendations
    : (result.reporting?.key_recommendations ?? rp?.strategic_recommendations ?? []);

  // Server-normalised 0-100 scores, one per crew.
  const radar = CREW_KEYS.flatMap((key) => {
    const score = result.crew_scores?.[key];
    return score == null ? [] : [{ crew: crewMeta(key).crew?.short ?? key, score }];
  });

  return (
    <div className="space-y-6">
      <VerdictHero result={result} />

      {locked && (
        <div className="flex flex-col items-start gap-4 rounded-2xl border border-violet/30 bg-violet/10 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex gap-3">
            <Lock className="mt-0.5 h-4 w-4 shrink-0 text-violet-300" aria-hidden="true" />
            <p className="text-sm text-white/80">{result.locked_note ?? 'This is the free preview.'} Unlock this report for {price}.</p>
          </div>
          <Link to="/pricing" className={cn(buttonVariants({ size: 'sm', variant: 'outline' }), 'shrink-0')}>
            See plans
          </Link>
        </div>
      )}

      <section className="rounded-2xl border border-white/[0.06] bg-white/[0.025] p-4">
        <h2 className="px-2 pt-2 text-sm text-white/55">Score by crew</h2>
        {radar.length >= 3 ? (
          <CrewRadar data={radar} />
        ) : (
          <p className="px-2 py-16 text-center text-sm text-white/40">Needs at least three scored crews to chart.</p>
        )}
      </section>

      {summary && (
        <SectionCard title="Executive summary" icon={FileText} color="#fb923c">
          <p className="max-w-prose text-sm leading-relaxed text-white/75">{summary}</p>
        </SectionCard>
      )}

      {!locked && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Category" value={iv?.category_classification?.primary_category ?? '—'} color="#2d7ff9" />
          <StatCard label="Innovation level" value={iv?.innovation_scoring?.innovation_level ?? '—'} color="#6366f1" />
          <StatCard label="Market stage" value={mr?.market_research?.market_stage ?? '—'} color="#14b8a6" />
          <StatCard label="Technology readiness" value={`TRL ${rp?.technology_readiness?.trl_level ?? rp?.trl_level ?? '—'}`} color="#8b5cf6" />
        </div>
      )}

      {recs.length > 0 && (
        <SectionCard title="Strategic recommendations" icon={Target} color="#fb923c">
          <ul className="space-y-2">
            {recs.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-white/75">
                <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-orange" aria-hidden="true" />
                {r}
              </li>
            ))}
          </ul>
        </SectionCard>
      )}
    </div>
  );
}
