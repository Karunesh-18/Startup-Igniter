import { useCallback, useEffect, useState } from 'react';
import { Link, Navigate, useParams, useSearchParams } from 'react-router-dom';
import { AlertTriangle, ArrowLeft, Loader2, Lock } from 'lucide-react';
import { getAnalysis, getIdea } from '@/lib/api';
import { crewMeta } from '@/lib/report';
import { formatINR } from '@/lib/format';
import type { AnalysisDetail, Idea, KnownCrewKey } from '@/lib/types';
import { cn } from '@/lib/utils';
import { buttonVariants } from '@/components/ui/button';
import { Tabs, TabPanel } from '@/components/ui/tabs';
import { useBilling } from '@/components/app/shared';
import OverviewTab from './OverviewTab';
import IdeaTab from './IdeaTab';
import MarketTab from './MarketTab';
import PatentTab from './PatentTab';
import GenericCrew from './GenericCrew';
import SkepticTab from './SkepticTab';
import EvidenceTab from './EvidenceTab';
import ReportActions from './ReportActions';

// Report sections grouped the way an investor reads them.
const GROUPS: { key: string; label: string; crews: KnownCrewKey[]; special?: 'skeptic' | 'evidence' }[] = [
  { key: 'overview', label: 'Overview', crews: [] },
  { key: 'skeptic', label: 'Skeptic', crews: [], special: 'skeptic' },
  { key: 'evidence', label: 'Evidence', crews: [], special: 'evidence' },
  { key: 'validate', label: 'Validate', crews: ['idea_validation', 'feasibility'] },
  { key: 'market', label: 'Market', crews: ['market_research'] },
  { key: 'ip', label: 'IP', crews: ['research_patent'] },
  { key: 'build', label: 'Build', crews: ['product_development'] },
  { key: 'business', label: 'Business', crews: ['business_planning', 'legal_compliance', 'funding'] },
  { key: 'launch', label: 'Launch', crews: ['branding_marketing', 'growth_scaling', 'community'] },
  { key: 'report', label: 'Report', crews: ['reporting'] },
];

function CrewView({ crew, result }: { crew: KnownCrewKey; result: NonNullable<AnalysisDetail['result']> }) {
  if (crew === 'idea_validation') return <IdeaTab result={result} />;
  if (crew === 'market_research') return <MarketTab result={result} />;
  if (crew === 'research_patent') return <PatentTab result={result} />;
  const meta = crewMeta(crew);
  return <GenericCrew data={result[crew]} label={meta.label} color={meta.color} />;
}

function LockedPanel({ price }: { price: string }) {
  return (
    <div className="flex flex-col items-center rounded-3xl border border-dashed border-violet/40 bg-violet/[0.06] px-6 py-16 text-center">
      <Lock className="h-8 w-8 text-violet-300" aria-hidden="true" />
      <h2 className="mt-4 font-serif text-3xl text-white">This part of the report is locked</h2>
      <p className="mt-2 max-w-md text-sm text-white/60">
        The free preview shows the score and verdict. The full report has all 13 crews, the evidence behind every claim, the skeptic
        debate, and PDF export. Unlock this report for {price}, or go Pro for every report.
      </p>
      <Link to="/pricing" className={cn(buttonVariants({ variant: 'outline' }), 'mt-6')}>
        Compare plans
      </Link>
    </div>
  );
}

export default function ResultsPage() {
  const id = useParams().id ?? '';
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState<AnalysisDetail | null>(null);
  const [idea, setIdea] = useState<Idea | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [crewByGroup, setCrewByGroup] = useState<Record<string, KnownCrewKey>>({});
  const { billing, reload } = useBilling();

  const load = useCallback(async () => {
    try {
      const a = await getAnalysis(id);
      setData(a);
      getIdea(a.idea_id).then(setIdea).catch(() => undefined);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load this report.');
    }
  }, [id]);
  useEffect(() => {
    load();
  }, [load]);

  if (data?.status === 'running') return <Navigate to={`/analysis/${id}`} replace />;

  if (!data || !data.result) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-void px-4 text-center">
        {error || data ? (
          <>
            <AlertTriangle className="h-6 w-6 text-red-400" aria-hidden="true" />
            <p className="max-w-sm text-white/70">{error ?? data?.error ?? 'This report has no result. The analysis may have failed.'}</p>
            <Link to={data ? `/ideas/${data.idea_id}` : '/app'} className={buttonVariants()}>
              Back
            </Link>
          </>
        ) : (
          <Loader2 className="h-6 w-6 animate-spin text-electric" aria-label="Loading report" />
        )}
      </div>
    );
  }

  const result = data.result;
  const locked = Boolean(result.locked);
  const present = (k: KnownCrewKey) => result[k] != null;
  const tabs = GROUPS.map((g) => ({
    key: g.key,
    label: (
      <span className="inline-flex items-center gap-1.5">
        {g.label}
        {locked && g.key !== 'overview' && <Lock className="h-3 w-3 opacity-60" aria-label="locked" />}
      </span>
    ),
    disabled: !locked && (g.special === 'evidence' ? !result.ledger?.length && !result.sources?.length : g.special === 'skeptic' ? !result.skeptic : g.crews.length > 0 && !g.crews.some(present)),
  }));
  const requested = params.get('tab');
  const active = tabs.find((t) => t.key === requested && !t.disabled)?.key ?? 'overview';
  const group = GROUPS.find((g) => g.key === active)!;
  const crews = group.crews.filter(present);
  const crew = crews.includes(crewByGroup[active]) ? crewByGroup[active] : crews[0];
  const title = idea?.title ?? result.idea_text;

  return (
    <div className="min-h-screen bg-void">
      <header className="sticky top-0 z-40 border-b border-white/5 bg-void/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <Link to={`/ideas/${data.idea_id}`} className="flex items-center gap-2 text-sm text-white/55 transition-colors hover:text-white">
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            <span className="hidden sm:inline">Idea</span>
          </Link>
          <p className="min-w-0 flex-1 truncate text-center text-sm text-white/70" title={result.idea_text}>
            {title} <span className="text-white/35">· v{data.version}</span>
          </p>
          <ReportActions
            analysisId={id}
            title={title}
            unlocked={!locked}
            billing={billing}
            githubRepo={idea?.github_repo ?? ''}
            onUnlocked={() => {
              reload();
              load();
            }}
          />
        </div>
        <div className="mx-auto max-w-6xl px-4 pb-3 sm:px-6">
          <Tabs
            tabs={tabs}
            active={active}
            onChange={(k) => setParams(k === 'overview' ? {} : { tab: k }, { replace: true })}
            idPrefix="report"
            label="Report sections"
          />
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
        {result.mode === 'mock' && (
          <div role="alert" className="mb-6 rounded-2xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-100">
            <b>Placeholder data.</b> The AI model was not reachable, so this report was generated offline and does not assess your idea.
            Run the analysis again once the model is available.
          </div>
        )}
        {(result.failed_crews?.length ?? 0) > 0 && (
          <p role="status" className="mb-6 rounded-2xl border border-yellow-400/30 bg-yellow-400/10 px-4 py-3 text-sm text-yellow-100">
            Some sections could not be generated: {result.failed_crews!.map((k) => crewMeta(k).label).join(', ')}. The verdict and the other
            sections are unaffected. Re-run the analysis to try again.
          </p>
        )}
        <p className="mb-6 flex items-center gap-2 text-xs text-white/40">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-yellow-400/60" aria-hidden="true" />
          AI-generated. Verify findings independently before making investment or business decisions.
        </p>

        <TabPanel idPrefix="report" tabKey={active}>
          {active === 'overview' ? (
            <OverviewTab result={result} locked={locked} price={billing ? formatINR(billing.prices.report_paise) : '₹299'} />
          ) : locked ? (
            <LockedPanel price={billing ? formatINR(billing.prices.report_paise) : '₹299'} />
          ) : group.special === 'skeptic' ? (
            <SkepticTab result={result} />
          ) : group.special === 'evidence' ? (
            <EvidenceTab result={result} />
          ) : (
            <>
              {crews.length > 1 && (
                <div className="mb-6 flex flex-wrap gap-2" role="group" aria-label={`${group.label} crews`}>
                  {crews.map((k) => {
                    const meta = crewMeta(k);
                    return (
                      <button
                        key={k}
                        onClick={() => setCrewByGroup((s) => ({ ...s, [active]: k }))}
                        aria-pressed={k === crew}
                        className={cn(
                          'rounded-full border px-3.5 py-1.5 text-xs transition-colors',
                          k === crew ? 'border-white/30 text-white' : 'border-white/10 text-white/50 hover:text-white',
                        )}
                        style={k === crew ? { background: `${meta.color}26` } : undefined}
                      >
                        {meta.label}
                      </button>
                    );
                  })}
                </div>
              )}
              {crew && <CrewView crew={crew} result={result} />}
            </>
          )}
        </TabPanel>
      </main>
    </div>
  );
}
