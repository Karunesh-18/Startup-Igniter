import { useState } from 'react';
import {
  ArrowLeft, Rocket, Lightbulb, Globe, FlaskConical, TrendingUp, ShieldCheck,
  Users, Target, AlertTriangle, CheckCircle2, Zap, Star, BarChart3, FileText,
  Brain, Layers, Award, ChevronRight, Download, Share2,
} from 'lucide-react';
import NeuralBackground from './NeuralBackground';
import type { AnalysisResult, CompetitorInfo } from '@/lib/types';

type Tab = 'overview' | 'idea' | 'market' | 'patent';

interface Props {
  result: AnalysisResult;
  onBack: () => void;
  onNewMission: () => void;
}

// ─── Utility components ────────────────────────────────────────

function ScoreBadge({ score, label, color }: { score: number; label: string; color: string }) {
  const pct = Math.min(Math.max(score, 0), 100);
  return (
    <div className="relative flex flex-col items-center">
      <svg className="h-28 w-28 -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
        <circle
          cx="50" cy="50" r="40" fill="none" strokeWidth="8"
          stroke={color}
          strokeDasharray={`${2 * Math.PI * 40}`}
          strokeDashoffset={`${2 * Math.PI * 40 * (1 - pct / 100)}`}
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 6px ${color})` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-white">{Math.round(pct)}</span>
        <span className="text-[10px] text-white/40">/100</span>
      </div>
      <span className="mt-2 text-xs text-white/60">{label}</span>
    </div>
  );
}

function StatCard({ label, value, sub, color = '#2d7ff9' }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] p-4">
      <div className="text-[10px] uppercase tracking-wider text-white/40">{label}</div>
      <div className="mt-1 text-xl font-semibold" style={{ color }}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-white/40">{sub}</div>}
    </div>
  );
}

function TagList({ items, color = '#2d7ff9', max = 6 }: { items: string[]; color?: string; max?: number }) {
  const [expanded, setExpanded] = useState(false);
  const list = expanded ? items : items.slice(0, max);
  return (
    <div className="flex flex-wrap gap-1.5">
      {list.map((t, i) => (
        <span
          key={i}
          className="rounded-full px-2.5 py-1 text-xs"
          style={{ background: `${color}18`, color, border: `1px solid ${color}33` }}
        >
          {t}
        </span>
      ))}
      {items.length > max && (
        <button
          onClick={() => setExpanded((e) => !e)}
          className="rounded-full px-2.5 py-1 text-xs text-white/40 border border-white/10 hover:text-white transition-colors"
        >
          {expanded ? 'Show less' : `+${items.length - max} more`}
        </button>
      )}
    </div>
  );
}

function SectionCard({ title, icon: Icon, color = '#2d7ff9', children }: {
  title: string;
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  color?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-white/[0.06] bg-white/[0.025] p-5">
      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg" style={{ background: `${color}22` }}>
          <Icon className="h-3.5 w-3.5" style={{ color }} />
        </div>
        <h3 className="text-sm font-medium text-white">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function RatingBar({ label, value, max = 10, color = '#2d7ff9' }: { label: string; value: number; max?: number; color?: string }) {
  const pct = Math.min(Math.max((value / max) * 100, 0), 100);
  return (
    <div className="flex items-center gap-3">
      <span className="w-44 text-xs text-white/60 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}, ${color}aa)` }}
        />
      </div>
      <span className="w-8 text-right font-mono text-xs text-white/50">{value.toFixed(1)}</span>
    </div>
  );
}

function TRLMeter({ level }: { level: number }) {
  const trlNames = ['', 'Basic Principles', 'Concept', 'Proof of Concept', 'Lab Validation', 'Relevant Env', 'Demo', 'Prototype', 'Complete System', 'Deployed'];
  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <span className="text-xs text-white/60">Technology Readiness Level</span>
        <span className="font-mono text-sm font-bold text-violet">TRL {level} — {trlNames[level] ?? 'Unknown'}</span>
      </div>
      <div className="flex gap-1">
        {Array.from({ length: 9 }, (_, i) => i + 1).map((n) => (
          <div
            key={n}
            className="flex-1 rounded"
            style={{
              height: 8 + n * 2,
              background: n <= level
                ? `linear-gradient(180deg, #8b5cf6, #6366f1)`
                : 'rgba(255,255,255,0.06)',
              boxShadow: n === level ? '0 0 8px #8b5cf680' : 'none',
            }}
          />
        ))}
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-white/30">
        <span>1 — Concept</span>
        <span>9 — Deployed</span>
      </div>
    </div>
  );
}

// ─── Tab Views ─────────────────────────────────────────────────

function OverviewTab({ result }: { result: AnalysisResult }) {
  const iv = result.idea_validation;
  const mr = result.market_research;
  const rp = result.research_patent;

  const ivScore = iv?.overall_validation_score ?? 0;
  const mrScore = mr?.overall_market_score ?? 0;
  const rpScore = rp?.overall_novelty_score ?? 0;

  const recs = result.strategic_recommendations ?? rp?.strategic_recommendations ?? [];

  return (
    <div className="space-y-6">
      {/* Score trio */}
      <div className="rounded-2xl border border-white/[0.06] bg-white/[0.025] p-6">
        <h3 className="mb-6 text-sm font-medium text-white/60 uppercase tracking-wider">Readiness Scores</h3>
        <div className="flex flex-wrap justify-around gap-8">
          <ScoreBadge score={ivScore * 10} label="Idea Validation" color="#2d7ff9" />
          <ScoreBadge score={mrScore * 10} label="Market Research" color="#14b8a6" />
          <ScoreBadge score={rpScore * 10} label="Research & Patent" color="#8b5cf6" />
          <ScoreBadge score={result.overall_readiness_score * 10} label="Overall Readiness" color="#fb923c" />
        </div>
      </div>

      {/* Executive summary */}
      {result.executive_summary && (
        <SectionCard title="Executive Summary" icon={FileText} color="#fb923c">
          <p className="text-sm leading-relaxed text-white/70">{result.executive_summary}</p>
        </SectionCard>
      )}

      {/* Key metrics row */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Category" value={iv?.category_classification?.primary_category ?? '—'} color="#2d7ff9" />
        <StatCard label="Innovation Level" value={iv?.innovation_scoring?.innovation_level ?? '—'} color="#6366f1" />
        <StatCard label="Market Stage" value={mr?.market_research?.market_stage ?? '—'} color="#14b8a6" />
        <StatCard label="TRL Level" value={`TRL ${rp?.technology_readiness?.trl_level ?? rp?.trl_level ?? '—'}`} color="#8b5cf6" />
      </div>

      {/* Strategic recommendations */}
      {recs.length > 0 && (
        <SectionCard title="Strategic Recommendations" icon={Target} color="#fb923c">
          <ul className="space-y-2">
            {recs.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-white/70">
                <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-orange" />
                {r}
              </li>
            ))}
          </ul>
        </SectionCard>
      )}
    </div>
  );
}

function IdeaValidationTab({ result }: { result: AnalysisResult }) {
  const iv = result.idea_validation;
  if (!iv) return <div className="py-16 text-center text-white/40">Idea Validation data not available.</div>;

  const ia = iv.idea_analysis;
  const pa = iv.problem_analysis;
  const ci = iv.customer_identification;
  const vp = iv.value_proposition;
  const cc = iv.category_classification;
  const is = iv.innovation_scoring;

  return (
    <div className="space-y-6">
      {/* Scores */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Validation Score" value={`${iv.overall_validation_score?.toFixed(1)}/10`} color="#2d7ff9" />
        <StatCard label="Problem Severity" value={pa?.problem_severity?.toUpperCase() ?? '—'} color={pa?.problem_severity === 'critical' ? '#ec4899' : '#fb923c'} />
        <StatCard label="Urgency Score" value={`${pa?.urgency_score?.toFixed(1) ?? '—'}/10`} color="#6366f1" />
        <StatCard label="Innovation Score" value={`${is?.overall_innovation_score?.toFixed(1) ?? '—'}/10`} color="#8b5cf6" />
      </div>

      {/* Summary */}
      {ia?.summary && (
        <SectionCard title="Idea Summary" icon={Lightbulb} color="#2d7ff9">
          <p className="text-sm leading-relaxed text-white/70">{ia.summary}</p>
          {ia.rationale && <p className="mt-2 text-xs leading-relaxed text-white/40">{ia.rationale}</p>}
        </SectionCard>
      )}

      {/* Scores breakdown */}
      <div className="grid gap-4 lg:grid-cols-2">
        <SectionCard title="Innovation Analysis" icon={Brain} color="#8b5cf6">
          <div className="space-y-3">
            <RatingBar label="Overall Innovation" value={is?.overall_innovation_score ?? 0} color="#8b5cf6" />
            <RatingBar label="Novelty" value={is?.novelty_score ?? 0} color="#8b5cf6" />
            <RatingBar label="Tech Innovation" value={is?.technology_innovation_score ?? 0} color="#8b5cf6" />
            <RatingBar label="Business Model" value={is?.business_model_innovation_score ?? 0} color="#8b5cf6" />
            <RatingBar label="Differentiation" value={is?.differentiation_score ?? 0} color="#8b5cf6" />
          </div>
        </SectionCard>

        <SectionCard title="Problem Severity" icon={AlertTriangle} color="#fb923c">
          <div className="space-y-3">
            <RatingBar label="Urgency" value={pa?.urgency_score ?? 0} color="#fb923c" />
            <RatingBar label="Confidence" value={pa?.confidence_score ?? 0} color="#fb923c" />
            <RatingBar label="Value Clarity" value={vp?.value_clarity_score ?? 0} color="#fb923c" />
            <RatingBar label="Customer Value" value={vp?.customer_value_score ?? 0} color="#fb923c" />
          </div>
        </SectionCard>
      </div>

      {/* Value proposition */}
      {vp && (
        <SectionCard title="Value Proposition" icon={Star} color="#6366f1">
          {vp.core_value_proposition && (
            <div className="mb-3 rounded-xl border border-indigo/20 bg-indigo/5 p-3">
              <p className="text-sm font-medium text-white">{vp.core_value_proposition}</p>
              {vp.unique_selling_proposition && (
                <p className="mt-1 text-xs text-white/50">{vp.unique_selling_proposition}</p>
              )}
            </div>
          )}
          {vp.functional_benefits?.length > 0 && (
            <>
              <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">Benefits</div>
              <TagList items={vp.functional_benefits} color="#6366f1" />
            </>
          )}
        </SectionCard>
      )}

      {/* Customer identification */}
      {ci && (
        <SectionCard title="Target Customers" icon={Users} color="#14b8a6">
          <div className="grid gap-4 sm:grid-cols-2">
            {ci.primary_customers?.length > 0 && (
              <div>
                <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">Primary</div>
                <TagList items={ci.primary_customers} color="#14b8a6" />
              </div>
            )}
            {ci.customer_segments?.length > 0 && (
              <div>
                <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">Segments</div>
                <TagList items={ci.customer_segments} color="#14b8a6" />
              </div>
            )}
            {ci.pain_points?.length > 0 && (
              <div className="sm:col-span-2">
                <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">Pain Points</div>
                <TagList items={ci.pain_points} color="#ec4899" max={8} />
              </div>
            )}
          </div>
          {ci.willingness_to_pay && (
            <div className="mt-3 text-xs text-white/50">
              <span className="text-white/30">Willingness to pay: </span>{ci.willingness_to_pay}
            </div>
          )}
        </SectionCard>
      )}

      {/* Category */}
      {cc && (
        <div className="grid gap-3 sm:grid-cols-3">
          <StatCard label="Industry" value={cc.industry ?? '—'} color="#2d7ff9" />
          <StatCard label="Business Model" value={cc.business_model ?? '—'} color="#6366f1" />
          <StatCard label="Revenue Model" value={cc.revenue_model ?? '—'} color="#14b8a6" />
        </div>
      )}

      {/* Strengths / Weaknesses */}
      <div className="grid gap-4 lg:grid-cols-2">
        {ia?.strengths?.length > 0 && (
          <SectionCard title="Strengths" icon={CheckCircle2} color="#10b981">
            <ul className="space-y-1.5">
              {ia.strengths.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-white/70">
                  <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald" />
                  {s}
                </li>
              ))}
            </ul>
          </SectionCard>
        )}
        {ia?.weaknesses?.length > 0 && (
          <SectionCard title="Weaknesses" icon={AlertTriangle} color="#fb923c">
            <ul className="space-y-1.5">
              {ia.weaknesses.map((w, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-white/70">
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-orange" />
                  {w}
                </li>
              ))}
            </ul>
          </SectionCard>
        )}
      </div>
    </div>
  );
}

function MarketResearchTab({ result }: { result: AnalysisResult }) {
  const mr = result.market_research;
  if (!mr) return <div className="py-16 text-center text-white/40">Market Research data not available.</div>;

  const ts = mr.tam_sam_som;
  const ia = mr.industry_analysis;
  const tr = mr.trend_analysis;
  const cd = mr.competitor_discovery;
  const cp = mr.customer_persona;
  const mra = mr.market_research;

  return (
    <div className="space-y-6">
      {/* TAM/SAM/SOM */}
      {ts && (
        <div className="rounded-2xl border border-teal/20 bg-teal/5 p-5">
          <h3 className="mb-4 text-sm font-medium uppercase tracking-wider text-teal">Market Sizing</h3>
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

function ResearchPatentTab({ result }: { result: AnalysisResult }) {
  const rp = result.research_patent;
  if (!rp) return <div className="py-16 text-center text-white/40">Research & Patent data not available.</div>;

  const pat = rp.patent_analysis;
  const rpa = rp.research_paper_analysis;
  const esa = rp.existing_solution_analysis;
  const iga = rp.innovation_gap_analysis;
  const trl = rp.technology_readiness;
  const ips = rp.ip_strategy;

  return (
    <div className="space-y-6">
      {/* Novelty Scores */}
      <div className="grid gap-3 sm:grid-cols-3">
        <StatCard label="Novelty Score" value={`${rp.overall_novelty_score?.toFixed(1) ?? '—'}/10`} color="#8b5cf6" />
        <StatCard label="IP Defensibility" value={`${ips?.ip_defensibility_score?.toFixed(1) ?? '—'}/10`} color="#6366f1" />
        <StatCard label="Academic Novelty" value={`${rpa?.academic_novelty_score?.toFixed(1) ?? '—'}/10`} color="#8b5cf6" />
      </div>

      {/* TRL Meter */}
      {trl?.trl_level != null && (
        <SectionCard title="Technology Readiness Level" icon={Zap} color="#8b5cf6">
          <TRLMeter level={trl.trl_level} />
          {trl.technical_feasibility_assessment && (
            <p className="mt-4 text-sm leading-relaxed text-white/70">{trl.technical_feasibility_assessment}</p>
          )}
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {trl.estimated_time_to_mvp_months > 0 && (
              <StatCard label="Est. Time to MVP" value={`${trl.estimated_time_to_mvp_months} months`} color="#8b5cf6" />
            )}
            <StatCard label="Engineering Complexity" value={trl.engineering_complexity ?? '—'} color="#6366f1" />
          </div>
          {trl.technology_dependencies?.length > 0 && (
            <div className="mt-3">
              <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">Key Dependencies</div>
              <TagList items={trl.technology_dependencies} color="#8b5cf6" />
            </div>
          )}
        </SectionCard>
      )}

      {/* Patent Analysis */}
      {pat && (
        <SectionCard title="Patent Landscape" icon={ShieldCheck} color="#6366f1">
          {pat.patent_landscape && (
            <p className="mb-3 text-sm leading-relaxed text-white/70">{pat.patent_landscape}</p>
          )}
          {pat.existing_patent_summary && (
            <p className="mb-3 text-sm leading-relaxed text-white/70">{pat.existing_patent_summary}</p>
          )}
          <div className="grid gap-3 sm:grid-cols-2 mb-4">
            {pat.patent_activity_level && (
              <StatCard label="Patent Activity" value={pat.patent_activity_level} color="#6366f1" />
            )}
            {pat.patentability_assessment && (
              <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] p-4">
                <div className="text-[10px] uppercase tracking-wider text-white/40">Patentability</div>
                <div className="mt-1 text-xs text-white/70">{pat.patentability_assessment}</div>
              </div>
            )}
          </div>
          {(pat.white_space_opportunities?.length ?? 0) > 0 && (
            <div className="mb-3">
              <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">White Space Opportunities</div>
              <TagList items={pat.white_space_opportunities ?? []} color="#10b981" />
            </div>
          )}
          {(pat.potential_patent_conflicts?.length ?? 0) > 0 && (
            <div>
              <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">Potential Conflicts</div>
              <TagList items={pat.potential_patent_conflicts ?? []} color="#fb923c" />
            </div>
          )}
        </SectionCard>
      )}

      {/* Innovation Gap */}
      {iga && (
        <SectionCard title="Innovation Gap Analysis" icon={Award} color="#10b981">
          <div className="mb-3">
            <RatingBar label="Overall Gap Score" value={iga.overall_gap_score ?? 0} color="#10b981" />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {iga.technical_gaps?.length > 0 && (
              <div>
                <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">Technical Gaps</div>
                <TagList items={iga.technical_gaps} color="#10b981" max={4} />
              </div>
            )}
            {iga.innovation_opportunities?.length > 0 && (
              <div>
                <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">Opportunities</div>
                <TagList items={iga.innovation_opportunities} color="#10b981" max={4} />
              </div>
            )}
          </div>
        </SectionCard>
      )}

      {/* IP Strategy */}
      {ips && (
        <SectionCard title="IP Strategy" icon={ShieldCheck} color="#2d7ff9">
          {ips.reasoning_summary && (
            <p className="mb-4 text-sm leading-relaxed text-white/70">{ips.reasoning_summary}</p>
          )}
          {ips.patent_strategy_recommendations?.length > 0 && (
            <div className="mb-3">
              <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">Patent Strategy</div>
              <ul className="space-y-1.5">
                {ips.patent_strategy_recommendations.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-white/60">
                    <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-electric" />
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {ips.open_source_strategy && (
            <div className="mt-3 rounded-xl bg-electric/5 border border-electric/10 p-3">
              <div className="text-[10px] uppercase tracking-wider text-white/30 mb-1">Open Source Strategy</div>
              <p className="text-xs text-white/60">{ips.open_source_strategy}</p>
            </div>
          )}
        </SectionCard>
      )}

      {/* Research Papers */}
      {rpa && (
        <SectionCard title="Academic Research Landscape" icon={FileText} color="#8b5cf6">
          {rpa.state_of_the_art_methods?.length > 0 && (
            <div className="mb-3">
              <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">State of the Art</div>
              <TagList items={rpa.state_of_the_art_methods} color="#8b5cf6" max={5} />
            </div>
          )}
          {rpa.emerging_research_trends?.length > 0 && (
            <div className="mb-3">
              <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">Emerging Trends</div>
              <TagList items={rpa.emerging_research_trends} color="#6366f1" max={5} />
            </div>
          )}
          {rpa.open_problems?.length > 0 && (
            <div>
              <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">Open Problems</div>
              <TagList items={rpa.open_problems} color="#fb923c" max={4} />
            </div>
          )}
        </SectionCard>
      )}

      {/* Existing Solutions */}
      {esa && (
        <SectionCard title="Existing Solution Landscape" icon={Layers} color="#ec4899">
          <div className="mb-3 flex items-center gap-2">
            <span className="text-xs text-white/40">Market Maturity:</span>
            <span className="rounded-full px-2.5 py-0.5 text-xs font-medium"
              style={{ background: '#ec489920', color: '#ec4899' }}
            >{esa.market_maturity}</span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {esa.existing_startups?.length > 0 && (
              <div>
                <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">Startups</div>
                <TagList items={esa.existing_startups} color="#ec4899" max={5} />
              </div>
            )}
            {esa.solution_gaps?.length > 0 && (
              <div>
                <div className="mb-2 text-[10px] uppercase tracking-wider text-white/30">Solution Gaps</div>
                <TagList items={esa.solution_gaps} color="#10b981" max={5} />
              </div>
            )}
          </div>
        </SectionCard>
      )}
    </div>
  );
}

// ─── Main Results Page ─────────────────────────────────────────

const TABS: { id: Tab; label: string; icon: React.ComponentType<{ className?: string }>; color: string }[] = [
  { id: 'overview', label: 'Overview', icon: Rocket, color: '#fb923c' },
  { id: 'idea', label: 'Idea Validation', icon: Lightbulb, color: '#2d7ff9' },
  { id: 'market', label: 'Market Research', icon: Globe, color: '#14b8a6' },
  { id: 'patent', label: 'Research & Patent', icon: FlaskConical, color: '#8b5cf6' },
];

export default function ResultsPage({ result, onBack, onNewMission }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('overview');

  const activeTabMeta = TABS.find((t) => t.id === activeTab)!;

  return (
    <div className="relative min-h-screen overflow-hidden bg-void">
      <div className="absolute inset-0 opacity-20">
        <NeuralBackground density={0.25} />
      </div>

      {/* Top bar */}
      <div className="sticky top-0 z-40 border-b border-white/5 bg-void/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-4">
            <button onClick={onBack} className="flex items-center gap-2 text-sm text-white/50 transition-colors hover:text-white">
              <ArrowLeft className="h-4 w-4" />
              <span className="hidden sm:inline">Back</span>
            </button>
            <div className="h-5 w-px bg-white/10" />
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-electric to-violet">
                <Rocket className="h-4 w-4 text-white" />
              </div>
              <div className="leading-none">
                <div className="text-sm font-semibold text-white">Analysis Complete</div>
                <div className="font-mono text-[9px] uppercase tracking-wider text-white/40">
                  Project · {result.project_id}
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Overall score pill */}
            <div className="hidden items-center gap-2 rounded-full border border-orange/30 bg-orange/10 px-3 py-1.5 sm:flex">
              <Star className="h-3.5 w-3.5 text-orange" />
              <span className="text-xs text-orange">
                Readiness {(result.overall_readiness_score * 10).toFixed(0)}/100
              </span>
            </div>
            <button
              onClick={onNewMission}
              className="btn-primary flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium"
            >
              <Zap className="h-3.5 w-3.5" />
              New Mission
            </button>
          </div>
        </div>

        {/* Tab bar */}
        <div className="mx-auto max-w-6xl overflow-x-auto">
          <div className="flex gap-1 px-6 pb-1">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className="flex shrink-0 items-center gap-1.5 rounded-full px-4 py-2 text-xs font-medium transition-all duration-200"
                  style={{
                    background: isActive ? `${tab.color}22` : 'transparent',
                    color: isActive ? tab.color : 'rgba(255,255,255,0.45)',
                    borderBottom: isActive ? `2px solid ${tab.color}` : '2px solid transparent',
                    borderRadius: 0,
                  }}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* AI disclaimer */}
      <div className="mx-auto max-w-6xl px-6 pt-4">
        <div className="flex items-center gap-2 rounded-xl border border-white/[0.05] bg-white/[0.02] px-4 py-2 text-xs text-white/30">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-yellow-400/50" />
          AI-generated — verify all findings independently before making investment or business decisions.
        </div>
      </div>

      {/* Tab content */}
      <div className="mx-auto max-w-6xl px-6 py-6">
        {activeTab === 'overview' && <OverviewTab result={result} />}
        {activeTab === 'idea' && <IdeaValidationTab result={result} />}
        {activeTab === 'market' && <MarketResearchTab result={result} />}
        {activeTab === 'patent' && <ResearchPatentTab result={result} />}
      </div>
    </div>
  );
}
