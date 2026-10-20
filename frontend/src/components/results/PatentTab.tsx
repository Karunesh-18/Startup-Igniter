import { Award, ChevronRight, FileText, Layers, ShieldCheck, Zap } from 'lucide-react';
import { TRLGauge } from './charts';
import type { AnalysisResult } from '@/lib/types';
import { Empty, SectionCard, StatCard, TagList, RatingBar } from './primitives';

const TRL_NAMES = ['', 'Basic principles', 'Concept', 'Proof of concept', 'Lab validation', 'Relevant environment', 'Demo', 'Prototype', 'Complete system', 'Deployed'];

export default function ResearchPatentTab({ result }: { result: AnalysisResult }) {
  const rp = result.research_patent;
  if (!rp) return <Empty what="Research & Patent" />;

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
          <div className="flex flex-col items-center gap-2 sm:flex-row sm:gap-6">
            <TRLGauge level={trl.trl_level} />
            <div className="text-center sm:text-left">
              <div className="text-lg text-white">{trl.trl_stage_name || TRL_NAMES[trl.trl_level] || `TRL ${trl.trl_level}`}</div>
              <div className="text-xs text-white/45">Technology readiness level</div>
            </div>
          </div>
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
