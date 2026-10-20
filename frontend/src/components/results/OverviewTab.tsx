import { ChevronRight, FileText, Target } from 'lucide-react';
import type { AnalysisResult } from '@/lib/types';
import { CREW_KEYS, crewMeta, crewScore, toPercent } from '@/lib/report';
import { NumberTicker } from '@/components/ui/number-ticker';
import { CrewRadar } from './charts';
import { SectionCard, StatCard } from './primitives';

export default function OverviewTab({ result }: { result: AnalysisResult }) {
  const iv = result.idea_validation;
  const mr = result.market_research;
  const rp = result.research_patent;
  const readiness = toPercent(result.reporting?.overall_readiness_score ?? result.overall_readiness_score ?? 0);
  const summary = result.executive_summary ?? result.reporting?.executive_summary;
  const recs = result.strategic_recommendations?.length
    ? result.strategic_recommendations
    : result.reporting?.key_recommendations ?? rp?.strategic_recommendations ?? [];

  const radar = CREW_KEYS.flatMap((key) => {
    const score = crewScore(result[key]);
    return score == null ? [] : [{ crew: crewMeta(key).crew?.short ?? key, score }];
  });

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-5">
        <section className="flex flex-col justify-between rounded-2xl border border-white/[0.06] bg-white/[0.025] p-6 lg:col-span-2">
          <h2 className="text-sm text-white/55">Overall readiness</h2>
          <div className="mt-6 flex items-baseline gap-2">
            <NumberTicker value={Math.round(readiness)} className="font-serif text-8xl leading-none text-white" />
            <span className="text-lg text-white/40">/100</span>
          </div>
          <div className="mt-6 h-1.5 overflow-hidden rounded-full bg-white/5">
            <div className="h-full rounded-full bg-electric" style={{ width: `${readiness}%` }} />
          </div>
          <p className="mt-3 text-xs text-white/40">Weighted from the crew scores. AI-generated; treat it as a starting point.</p>
        </section>

        <section className="rounded-2xl border border-white/[0.06] bg-white/[0.025] p-4 lg:col-span-3">
          <h2 className="px-2 pt-2 text-sm text-white/55">Score by crew</h2>
          {radar.length >= 3 ? (
            <CrewRadar data={radar} />
          ) : (
            <p className="px-2 py-16 text-center text-sm text-white/40">Needs at least three scored crews to chart.</p>
          )}
        </section>
      </div>

      {summary && (
        <SectionCard title="Executive summary" icon={FileText} color="#fb923c">
          <p className="max-w-prose text-sm leading-relaxed text-white/75">{summary}</p>
        </SectionCard>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Category" value={iv?.category_classification?.primary_category ?? '—'} color="#2d7ff9" />
        <StatCard label="Innovation level" value={iv?.innovation_scoring?.innovation_level ?? '—'} color="#6366f1" />
        <StatCard label="Market stage" value={mr?.market_research?.market_stage ?? '—'} color="#14b8a6" />
        <StatCard label="Technology readiness" value={`TRL ${rp?.technology_readiness?.trl_level ?? rp?.trl_level ?? '—'}`} color="#8b5cf6" />
      </div>

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
