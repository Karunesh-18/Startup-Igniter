import { AlertTriangle, Brain, CheckCircle2, Lightbulb, Star, Users } from 'lucide-react';
import type { AnalysisResult } from '@/lib/types';
import { Empty, SectionCard, StatCard, TagList, RatingBar } from './primitives';

export default function IdeaValidationTab({ result }: { result: AnalysisResult }) {
  const iv = result.idea_validation;
  if (!iv) return <Empty what="Idea Validation" />;

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
