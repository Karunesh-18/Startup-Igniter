import { BarChart3, Globe, Layers, TrendingUp, Users } from 'lucide-react';
import type { AnalysisResult, CompetitorInfo } from '@/lib/types';
import { parseMoney } from '@/lib/report';
import { MarketSizeBars } from './charts';
import { Empty, SectionCard, StatCard, TagList } from './primitives';

export default function MarketResearchTab({ result }: { result: AnalysisResult }) {
  const mr = result.market_research;
  if (!mr) return <Empty what="Market Research" />;

  const ts = mr.tam_sam_som;
  const ia = mr.industry_analysis;
  const tr = mr.trend_analysis;
  const cd = mr.competitor_discovery;
  const cp = mr.customer_persona;
  const mra = mr.market_research;

  // Chart only when all three figures parse ("$4.2B", "USD 350 million"…); the text figures always show.
  const sizes = ts && [
    { name: 'TAM', value: parseMoney(ts.tam_value), color: '#e8eaf6' },
    { name: 'SAM', value: parseMoney(ts.sam_value), color: '#14b8a6' },
    { name: 'SOM', value: parseMoney(ts.som_value), color: '#2d7ff9' },
  ];
  const chartable = sizes?.every((d) => d.value && d.value > 0) ? (sizes as { name: string; value: number; color: string }[]) : null;

  return (
    <div className="space-y-6">
      {/* TAM/SAM/SOM */}
      {ts && (
        <div className="rounded-2xl border border-teal/20 bg-teal/5 p-5">
          <h3 className="mb-4 text-sm font-medium text-teal">Market sizing</h3>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="text-center">
              <div className="text-3xl font-bold text-white">{ts.tam_value}</div>
              <div className="mt-1 text-xs text-white/40">TAM — Total Addressable Market</div>
              {ts.tam_description && <div className="mt-2 text-xs text-white/30">{ts.tam_description}</div>}
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-teal">{ts.sam_value}</div>
              <div className="mt-1 text-xs text-white/40">SAM — Serviceable Market</div>
              {ts.sam_description && <div className="mt-2 text-xs text-white/30">{ts.sam_description}</div>}
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-electric">{ts.som_value}</div>
              <div className="mt-1 text-xs text-white/40">SOM — Obtainable Market</div>
              {ts.som_description && <div className="mt-2 text-xs text-white/30">{ts.som_description}</div>}
            </div>
          </div>
          {chartable && (
            <div className="mt-5">
              <MarketSizeBars data={chartable} />
            </div>
          )}
          {ts.target_geographies?.length > 0 && (
            <div className="mt-4">
              <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">Target Geographies</div>
              <TagList items={ts.target_geographies} color="#14b8a6" />
            </div>
          )}
        </div>
      )}

      {/* Market Overview */}
      {mra?.market_overview && (
        <SectionCard title="Market Overview" icon={Globe} color="#14b8a6">
          <p className="text-sm leading-relaxed text-white/70">{mra.market_overview}</p>
          {mra.future_outlook && (
            <p className="mt-3 text-xs leading-relaxed text-white/40">
              <span className="text-white/30">Outlook: </span>{mra.future_outlook}
            </p>
          )}
        </SectionCard>
      )}

      {/* Industry + Trends */}
      <div className="grid gap-4 lg:grid-cols-2">
        {ia && (
          <SectionCard title="Industry Analysis" icon={BarChart3} color="#2d7ff9">
            <div className="grid grid-cols-2 gap-3 mb-3">
              {ia.industry_growth_rate && (
                <StatCard label="Growth Rate" value={ia.industry_growth_rate} color="#2d7ff9" />
              )}
              {ia.cagr_percentage > 0 && (
                <StatCard label="CAGR" value={`${ia.cagr_percentage}%`} color="#6366f1" />
              )}
            </div>
            {ia.market_drivers?.length > 0 && (
              <>
                <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">Market Drivers</div>
                <TagList items={ia.market_drivers} color="#2d7ff9" />
              </>
            )}
          </SectionCard>
        )}

        {tr && (
          <SectionCard title="Trend Analysis" icon={TrendingUp} color="#fb923c">
            <div className="mb-3">
              <span className="text-xs text-white/40">Trend Velocity: </span>
              <span className="text-sm font-medium text-orange">{tr.trend_velocity}</span>
            </div>
            {tr.technology_trends?.length > 0 && (
              <>
                <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">Technology Trends</div>
                <TagList items={tr.technology_trends} color="#fb923c" max={5} />
              </>
            )}
          </SectionCard>
        )}
      </div>

      {/* Competitive Landscape */}
      {cd && (
        <SectionCard title="Competitive Landscape" icon={Layers} color="#ec4899">
          <div className="grid grid-cols-3 gap-3 mb-4">
            <StatCard label="Competition" value={cd.competition_intensity ?? '—'} color="#ec4899" />
            <StatCard label="Fragmentation" value={cd.market_fragmentation ?? '—'} color="#ec4899" />
            <StatCard label="Barrier to Entry" value={cd.barrier_to_entry ?? '—'} color="#ec4899" />
          </div>

          {cd.direct_competitors?.length > 0 && (
            <div className="space-y-3">
              <div className="text-[10px] uppercase tracking-wider text-white/30">Direct Competitors</div>
              {cd.direct_competitors.map((c: CompetitorInfo, i: number) => (
                <div key={i} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-white">{c.name}</span>
                    <span className="text-xs text-white/30">{c.pricing_model}</span>
                  </div>
                  <p className="mt-1 text-xs text-white/50">{c.description}</p>
                  {c.strengths?.length > 0 && (
                    <TagList items={c.strengths.slice(0, 3)} color="#10b981" max={3} />
                  )}
                </div>
              ))}
            </div>
          )}

          {cd.market_leaders?.length > 0 && (
            <div className="mt-4">
              <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">Market Leaders</div>
              <TagList items={cd.market_leaders} color="#6366f1" />
            </div>
          )}
        </SectionCard>
      )}

      {/* Customer Persona */}
      {cp?.primary_persona && (
        <SectionCard title="Primary Customer Persona" icon={Users} color="#14b8a6">
          <div className="rounded-xl border border-teal/20 bg-teal/5 p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-teal/20 text-teal font-bold text-lg">
                {cp.primary_persona.persona_name?.charAt(0) ?? 'P'}
              </div>
              <div>
                <div className="text-sm font-semibold text-white">{cp.primary_persona.persona_name}</div>
                <div className="text-xs text-white/40">{cp.primary_persona.occupation} · {cp.primary_persona.age_range}</div>
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <div className="mb-1.5 text-[10px] uppercase tracking-wider text-white/30">Goals</div>
                <ul className="space-y-1">
                  {cp.primary_persona.goals?.slice(0, 4).map((g, i) => (
                    <li key={i} className="text-xs text-white/60">• {g}</li>
                  ))}
                </ul>
              </div>
              <div>
                <div className="mb-1.5 text-[10px] uppercase tracking-wider text-white/30">Frustrations</div>
                <ul className="space-y-1">
                  {cp.primary_persona.frustrations?.slice(0, 4).map((f, i) => (
                    <li key={i} className="text-xs text-white/60">• {f}</li>
                  ))}
                </ul>
              </div>
            </div>
            {cp.primary_persona.preferred_channels?.length > 0 && (
              <div className="mt-3">
                <div className="mb-1.5 text-[10px] uppercase tracking-wider text-white/30">Preferred Channels</div>
                <TagList items={cp.primary_persona.preferred_channels} color="#14b8a6" />
              </div>
            )}
          </div>
        </SectionCard>
      )}
    </div>
  );
}
