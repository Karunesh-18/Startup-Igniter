import { Gauge, HelpCircle, Link2, AlertTriangle } from 'lucide-react';
import type { AnalysisResult } from '@/lib/types';
import { NumberTicker } from '@/components/ui/number-ticker';
import { verdictColor } from '@/components/app/shared';

const VERDICT_TEXT = { go: 'Go', pivot: 'Pivot', 'no-go': 'No-go' } as const;
const VERDICT_SUB = {
  go: 'The evidence supports building this.',
  pivot: 'There is something here, but not as currently planned.',
  'no-go': 'Do not pursue this as described.',
} as const;

function Metric({ icon: Icon, label, value, hint }: { icon: typeof Gauge; label: string; value: string; hint: string }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-3.5">
      <div className="flex items-center gap-1.5 text-xs text-white/45">
        <Icon className="h-3.5 w-3.5" aria-hidden="true" />
        {label}
      </div>
      <div className="mt-1 text-lg font-semibold text-white">{value}</div>
      <div className="mt-0.5 text-[11px] leading-snug text-white/40">{hint}</div>
    </div>
  );
}

export default function VerdictHero({ result }: { result: AnalysisResult }) {
  const label = result.verdict?.label ?? null;
  const color = verdictColor(label);
  const score = Math.round(result.overall_readiness_score ?? 0);
  const g = result.grounding;

  return (
    <section className="overflow-hidden rounded-3xl border border-white/[0.08] bg-white/[0.025]" aria-label="Verdict">
      <div className="grid gap-0 lg:grid-cols-5">
        <div className="p-6 sm:p-8 lg:col-span-3">
          <p className="text-sm text-white/50">Verdict</p>
          <h2 className="mt-1 font-serif text-6xl leading-none sm:text-7xl" style={{ color }}>
            {label ? VERDICT_TEXT[label] : 'Not rated'}
          </h2>
          {label && <p className="mt-3 text-sm text-white/55">{VERDICT_SUB[label]}</p>}
          {result.verdict?.rationale && <p className="mt-5 max-w-prose text-sm leading-relaxed text-white/80">{result.verdict.rationale}</p>}

          {result.verdict?.would_change_my_mind && result.verdict.would_change_my_mind.length > 0 && (
            <div className="mt-6">
              <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-white/45">
                <HelpCircle className="h-3.5 w-3.5" aria-hidden="true" />
                What would change this verdict
              </p>
              <ul className="mt-2 space-y-1.5 text-sm text-white/70">
                {result.verdict.would_change_my_mind.map((w, i) => (
                  <li key={i} className="flex gap-2">
                    <span aria-hidden="true" style={{ color }}>
                      •
                    </span>
                    {w}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="border-t border-white/[0.06] p-6 sm:p-8 lg:col-span-2 lg:border-l lg:border-t-0">
          <p className="text-sm text-white/50">Readiness</p>
          <div className="mt-1 flex items-baseline gap-2">
            <NumberTicker value={score} className="font-serif text-7xl leading-none text-white" />
            <span className="text-lg text-white/40">/100</span>
          </div>
          {result.score_range && (
            <p className="mt-2 text-xs text-white/45">
              Likely range {Math.round(result.score_range.low)} to {Math.round(result.score_range.high)}
            </p>
          )}
          <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/5">
            <div className="h-full rounded-full" style={{ width: `${score}%`, background: color }} />
          </div>

          <div className="mt-6 grid grid-cols-2 gap-3">
            <Metric
              icon={Gauge}
              label="Confidence"
              value={result.confidence != null ? `${Math.round(result.confidence)}%` : 'n/a'}
              hint="Crew confidence blended with sourcing"
            />
            <Metric
              icon={Link2}
              label="Sourced"
              value={g?.score != null ? `${Math.round(g.score)}%` : 'n/a'}
              hint={g?.claims ? `${g.claims} claims checked against ${g.sources} sources` : 'No claims were checked'}
            />
          </div>
          {g && g.contradicted > 0 && (
            <p className="mt-3 flex items-center gap-1.5 text-xs text-red-300">
              <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />
              {g.contradicted} claim{g.contradicted > 1 ? 's' : ''} contradicted by a source
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
