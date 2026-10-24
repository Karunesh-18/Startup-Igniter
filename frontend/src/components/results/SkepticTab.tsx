import { FlaskConical, Skull, ThumbsDown, ThumbsUp, Waypoints } from 'lucide-react';
import type { AnalysisResult } from '@/lib/types';
import { Empty, SectionCard } from './primitives';

function Column({ title, items, color, icon: Icon }: { title: string; items: string[]; color: string; icon: typeof ThumbsUp }) {
  return (
    <section className="rounded-2xl border bg-white/[0.025] p-5" style={{ borderColor: `${color}40` }}>
      <h3 className="flex items-center gap-2 text-sm font-medium" style={{ color }}>
        <Icon className="h-4 w-4" aria-hidden="true" />
        {title}
      </h3>
      <ul className="mt-3 space-y-3">
        {items.map((t, i) => (
          <li key={i} className="text-sm leading-relaxed text-white/75">
            {t}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function SkepticTab({ result }: { result: AnalysisResult }) {
  const s = result.skeptic;
  if (!s) return <Empty what="Skeptic review" />;
  const risks = [...(s.top_risks ?? [])].sort((a, b) => b.likelihood * b.impact - a.likelihood * a.impact);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <Column title="The case for" items={s.bull_case ?? []} color="#10b981" icon={ThumbsUp} />
        <Column title="The case against" items={s.bear_case ?? []} color="#ef4444" icon={ThumbsDown} />
      </div>

      {s.pre_mortem && (
        <SectionCard title="Pre-mortem: it is three years later and this failed" icon={Skull} color="#ef4444">
          <p className="max-w-prose text-sm leading-relaxed text-white/75">{s.pre_mortem}</p>
        </SectionCard>
      )}

      {risks.length > 0 && (
        <SectionCard title="Top risks, worst first" icon={Waypoints} color="#fb923c">
          <ul className="divide-y divide-white/[0.06]">
            {risks.map((r, i) => (
              <li key={i} className="py-3 first:pt-0 last:pb-0">
                <p className="text-sm text-white">{r.risk}</p>
                <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs text-white/50">
                  <span>
                    Likelihood <b className="font-mono text-white/80">{r.likelihood}</b>
                  </span>
                  <span>
                    Impact <b className="font-mono text-white/80">{r.impact}</b>
                  </span>
                </div>
                <p className="mt-2 text-xs leading-relaxed text-white/60">
                  <span className="text-teal-300">Mitigation:</span> {r.mitigation}
                </p>
              </li>
            ))}
          </ul>
        </SectionCard>
      )}

      {(s.testable_hypotheses?.length ?? 0) > 0 && (
        <SectionCard title="Test these first" icon={FlaskConical} color="#8b5cf6">
          <ul className="space-y-3">
            {s.testable_hypotheses!.map((h, i) => (
              <li key={i} className="text-sm">
                <p className="text-white/85">{h.hypothesis}</p>
                <p className="mt-0.5 text-xs text-white/45">Measure: {h.metric}</p>
              </li>
            ))}
          </ul>
        </SectionCard>
      )}

      {(s.pivot_suggestions?.length ?? 0) > 0 && (
        <SectionCard title="If you pivot" icon={Waypoints} color="#2d7ff9">
          <ul className="space-y-2 text-sm text-white/75">
            {s.pivot_suggestions!.map((p, i) => (
              <li key={i}>• {p}</li>
            ))}
          </ul>
        </SectionCard>
      )}
    </div>
  );
}
