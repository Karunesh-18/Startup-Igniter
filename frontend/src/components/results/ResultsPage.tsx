import { useEffect, useState } from 'react';
import { Link, useLocation, useParams, useSearchParams } from 'react-router-dom';
import { AlertTriangle, ArrowLeft, Loader2 } from 'lucide-react';
import { getAnalysis } from '@/lib/api';
import { crewMeta, loadResult, saveResult } from '@/lib/report';
import type { AnalysisResult, KnownCrewKey } from '@/lib/types';
import { cn } from '@/lib/utils';
import { buttonVariants } from '@/components/ui/button';
import { Tabs, TabPanel } from '@/components/ui/tabs';
import OverviewTab from './OverviewTab';
import IdeaTab from './IdeaTab';
import MarketTab from './MarketTab';
import PatentTab from './PatentTab';
import GenericCrew from './GenericCrew';

// Report sections grouped the way an investor reads them.
const GROUPS: { key: string; label: string; crews: KnownCrewKey[] }[] = [
  { key: 'overview', label: 'Overview', crews: [] },
  { key: 'validate', label: 'Validate', crews: ['idea_validation', 'feasibility'] },
  { key: 'market', label: 'Market', crews: ['market_research'] },
  { key: 'ip', label: 'IP', crews: ['research_patent'] },
  { key: 'build', label: 'Build', crews: ['product_development'] },
  { key: 'business', label: 'Business', crews: ['business_planning', 'legal_compliance', 'funding'] },
  { key: 'launch', label: 'Launch', crews: ['branding_marketing', 'growth_scaling', 'community'] },
  { key: 'report', label: 'Report', crews: ['reporting'] },
];

function CrewView({ crew, result }: { crew: KnownCrewKey; result: AnalysisResult }) {
  if (crew === 'idea_validation') return <IdeaTab result={result} />;
  if (crew === 'market_research') return <MarketTab result={result} />;
  if (crew === 'research_patent') return <PatentTab result={result} />;
  const meta = crewMeta(crew);
  return <GenericCrew data={result[crew]} label={meta.label} color={meta.color} />;
}

/** Result from navigation state, else sessionStorage, else the backend's cache. */
function useResult(id: string) {
  const state = (useLocation().state as { result?: AnalysisResult } | null)?.result;
  const [result, setResult] = useState<AnalysisResult | null>(() => (state?.project_id === id ? state : loadResult(id)));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (result) return;
    let live = true;
    getAnalysis(id)
      .then((r) => {
        if (!live) return;
        saveResult(r);
        setResult(r);
      })
      .catch((e: unknown) => live && setError(e instanceof Error ? e.message : 'Could not load this report.'));
    return () => {
      live = false;
    };
  }, [id, result]);

  return { result, error };
}

export default function ResultsPage() {
  const id = useParams().id ?? '';
  const { result, error } = useResult(id);
  const [params, setParams] = useSearchParams();
  const [crewByGroup, setCrewByGroup] = useState<Record<string, KnownCrewKey>>({});

  if (!result) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-void px-4 text-center">
        {error ? (
          <>
            <AlertTriangle className="h-6 w-6 text-red-400" aria-hidden="true" />
            <p className="max-w-sm text-white/70">
              This report isn&apos;t available. It may have expired from the server. Run the analysis again to get a new one.
            </p>
            <p className="font-mono text-xs text-white/35">{error}</p>
            <Link to="/analyze" className={buttonVariants()}>
              Analyze an idea
            </Link>
          </>
        ) : (
          <Loader2 className="h-6 w-6 animate-spin text-electric" aria-label="Loading report" />
        )}
      </div>
    );
  }

  const present = (k: KnownCrewKey) => result[k] != null;
  const tabs = GROUPS.map((g) => ({ key: g.key, label: g.label, disabled: g.crews.length > 0 && !g.crews.some(present) }));
  const requested = params.get('tab');
  const active = tabs.find((t) => t.key === requested && !t.disabled)?.key ?? 'overview';
  const group = GROUPS.find((g) => g.key === active)!;
  const crews = group.crews.filter(present);
  const crew = crews.includes(crewByGroup[active]) ? crewByGroup[active] : crews[0];

  return (
    <div className="min-h-screen bg-void">
      <header className="sticky top-0 z-40 border-b border-white/5 bg-void/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <Link to="/" className="flex items-center gap-2 text-sm text-white/55 transition-colors hover:text-white">
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            <span className="hidden sm:inline">Home</span>
          </Link>
          <p className="min-w-0 flex-1 truncate text-center text-sm text-white/70" title={result.idea_text}>
            {result.idea_text}
          </p>
          <Link to="/analyze" className={buttonVariants({ size: 'sm' })}>
            New analysis
          </Link>
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
        <p className="mb-6 flex items-center gap-2 text-xs text-white/40">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-yellow-400/60" aria-hidden="true" />
          AI-generated. Verify findings independently before making investment or business decisions.
        </p>

        <TabPanel idPrefix="report" tabKey={active}>
          {active === 'overview' ? (
            <OverviewTab result={result} />
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
