import { useCallback, useEffect, useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { Archive, ArrowDown, ArrowUp, Check, Github, Loader2, Lock, MessageSquare, Pencil, Play, Trash2, FlaskConical, X } from 'lucide-react';
import { deleteIdea, getIdea, startAnalysis, updateIdea } from '@/lib/api';
import { formatDate } from '@/lib/format';
import type { AnalysisSummary, IdeaDetail } from '@/lib/types';
import { cn } from '@/lib/utils';
import { Button, buttonVariants } from '@/components/ui/button';
import { Tabs, TabPanel } from '@/components/ui/tabs';
import { ApiErrorNote, AppPage, ErrorNote, VerdictBadge } from './shared';
import ChatPanel from './ChatPanel';
import ExperimentsPanel from './ExperimentsPanel';
import RescanPanel from './RescanPanel';

function VersionRow({ a, prev }: { a: AnalysisSummary; prev?: AnalysisSummary }) {
  const delta = a.overall_score != null && prev?.overall_score != null ? a.overall_score - prev.overall_score : null;
  const to = a.status === 'running' ? `/analysis/${a.id}` : a.status === 'complete' ? `/results/${a.id}` : undefined;
  const body = (
    <>
      <div className="flex items-center gap-3">
        <span className="w-8 font-mono text-xs text-white/40">v{a.version}</span>
        {a.status === 'complete' ? (
          <>
            <span className="font-serif text-2xl text-white">{Math.round(a.overall_score ?? 0)}</span>
            {delta != null && Math.round(delta) !== 0 && (
              <span className={cn('flex items-center text-xs', delta > 0 ? 'text-emerald-400' : 'text-red-400')}>
                {delta > 0 ? <ArrowUp className="h-3 w-3" aria-hidden="true" /> : <ArrowDown className="h-3 w-3" aria-hidden="true" />}
                {Math.abs(Math.round(delta))}
              </span>
            )}
            <VerdictBadge verdict={a.verdict} />
            {a.mode === 'mock' && <span className="rounded-full bg-red-500/15 px-2 py-0.5 text-[10px] text-red-300">MOCK DATA</span>}
          </>
        ) : a.status === 'running' ? (
          <span className="flex items-center gap-2 text-sm text-electric-300">
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            Running
          </span>
        ) : (
          <span className="text-sm text-white/40">{a.status === 'failed' ? 'Failed' : 'Cancelled'}</span>
        )}
      </div>
      <div className="flex items-center gap-3 text-xs text-white/40">
        {a.status === 'complete' && !a.unlocked && (
          <span className="flex items-center gap-1 text-violet-300">
            <Lock className="h-3 w-3" aria-hidden="true" />
            Preview
          </span>
        )}
        {a.grounding_score != null && <span>{Math.round(a.grounding_score)}% sourced</span>}
        <span>{formatDate(a.created_at)}</span>
      </div>
    </>
  );
  const cls = 'flex items-center justify-between gap-3 rounded-xl border border-white/[0.07] bg-charcoal/60 px-4 py-3';
  return to ? (
    <Link to={to} className={cn(cls, 'transition-colors hover:border-white/20')}>
      {body}
    </Link>
  ) : (
    <div className={cls} title={a.error ?? undefined}>
      {body}
    </div>
  );
}

export default function IdeaPage() {
  const id = useParams().id ?? '';
  const navigate = useNavigate();
  const notice = (useLocation().state as { notice?: string } | null)?.notice;
  const [idea, setIdea] = useState<IdeaDetail | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [running, setRunning] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');
  const [tab, setTab] = useState('chat');

  const load = useCallback(
    () =>
      getIdea(id)
        .then(setIdea)
        .catch((e: unknown) => setError(e instanceof Error ? e : new Error('Could not load this idea.'))),
    [id],
  );
  useEffect(() => {
    load();
  }, [load]);

  const run = async () => {
    setRunning(true);
    setError(null);
    try {
      const r = await startAnalysis(id);
      navigate(`/analysis/${r.analysis_id}`);
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Could not start the analysis.'));
      setRunning(false);
    }
  };

  const save = async () => {
    try {
      await updateIdea(id, { idea_text: draft.trim() });
      setEditing(false);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Could not save.'));
    }
  };

  if (!idea) {
    return (
      <AppPage>
        {error ? <ApiErrorNote error={error} /> : <Loader2 className="mx-auto mt-24 h-6 w-6 animate-spin text-electric" aria-label="Loading" />}
      </AppPage>
    );
  }

  const hasRun = idea.analyses.some((a) => a.status === 'running');

  return (
    <AppPage wide>
      <Link to="/app" className="text-sm text-white/50 transition-colors hover:text-white">
        ← Your ideas
      </Link>

      <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <h1 className="font-serif text-3xl leading-tight text-white sm:text-4xl">{idea.title}</h1>
          {idea.github_repo && (
            <a
              href={`https://github.com/${idea.github_repo}`}
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-flex items-center gap-1.5 text-xs text-white/50 hover:text-white"
            >
              <Github className="h-3.5 w-3.5" aria-hidden="true" />
              {idea.github_repo}
            </a>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            aria-label={idea.archived ? 'Unarchive idea' : 'Archive idea'}
            onClick={() => updateIdea(id, { archived: !idea.archived }).then(() => navigate('/app'))}
          >
            <Archive className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Delete idea"
            onClick={() => window.confirm('Delete this idea and all its reports? This cannot be undone.') && deleteIdea(id).then(() => navigate('/app'))}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
          <Button variant="shine" onClick={run} loading={running} disabled={hasRun}>
            <Play className="h-4 w-4" aria-hidden="true" />
            {idea.analyses.length ? 'Re-run analysis' : 'Run analysis'}
          </Button>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        {notice && !error && <ErrorNote error={notice} />}
        <ApiErrorNote error={error} />
        {idea.stale && (
          <p className="rounded-xl border border-yellow-400/25 bg-yellow-400/10 px-4 py-3 text-sm text-yellow-100">
            The idea changed after the last analysis. Re-run it to update the verdict.
          </p>
        )}
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-5">
        <div className="space-y-6 lg:col-span-2">
          <section className="rounded-2xl border border-white/[0.07] bg-charcoal/60 p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-sm text-white/55">The idea</h2>
              {!editing && (
                <button
                  onClick={() => {
                    setDraft(idea.idea_text);
                    setEditing(true);
                  }}
                  className="flex items-center gap-1 text-xs text-white/45 hover:text-white"
                >
                  <Pencil className="h-3 w-3" aria-hidden="true" />
                  Edit
                </button>
              )}
            </div>
            {editing ? (
              <>
                <textarea
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  rows={8}
                  maxLength={5000}
                  aria-label="Idea text"
                  className="mt-3 w-full resize-y rounded-xl border border-white/10 bg-white/[0.04] p-3 text-sm text-white focus:border-electric focus:outline-none"
                />
                <div className="mt-3 flex gap-2">
                  <Button size="sm" onClick={save} disabled={draft.trim().length < 10}>
                    <Check className="h-3.5 w-3.5" aria-hidden="true" />
                    Save
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>
                    <X className="h-3.5 w-3.5" aria-hidden="true" />
                    Cancel
                  </Button>
                </div>
              </>
            ) : (
              <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-white/80">{idea.idea_text}</p>
            )}
          </section>

          {idea.analyses.some((a) => a.status === 'complete') && <RescanPanel ideaId={id} />}

          <section aria-label="Report versions">
            <h2 className="mb-3 text-sm text-white/55">Report versions</h2>
            {idea.analyses.length === 0 ? (
              <p className="rounded-xl border border-dashed border-white/15 px-4 py-8 text-center text-sm text-white/40">
                No analysis yet. Run one to get a verdict.
              </p>
            ) : (
              <div className="space-y-2">
                {idea.analyses.map((a, i) => (
                  <VersionRow key={a.id} a={a} prev={idea.analyses.slice(i + 1).find((x) => x.status === 'complete')} />
                ))}
              </div>
            )}
          </section>
        </div>

        <div className="lg:col-span-3">
          <Tabs
            tabs={[
              { key: 'chat', label: 'AI co-founder' },
              { key: 'experiments', label: 'Experiments' },
            ]}
            active={tab}
            onChange={setTab}
            idPrefix="idea"
            label="Idea tools"
          />
          <div className="mt-4">
            <TabPanel idPrefix="idea" tabKey={tab}>
              {tab === 'chat' ? (
                <ChatPanel ideaId={id} onIdeaChanged={load} />
              ) : (
                <ExperimentsPanel ideaId={id} hasReport={idea.analyses.some((a) => a.status === 'complete')} />
              )}
            </TabPanel>
          </div>
          <p className="mt-3 flex items-center gap-4 text-xs text-white/30">
            <span className="flex items-center gap-1">
              <MessageSquare className="h-3 w-3" aria-hidden="true" />
              Chat and experiments are part of Pro
            </span>
            <span className="flex items-center gap-1">
              <FlaskConical className="h-3 w-3" aria-hidden="true" />
              Edits are proposals; nothing changes until you accept
            </span>
          </p>
          <Link to="/integrations" className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }), 'mt-2')}>
            Connect GitHub, Slack or Notion
          </Link>
        </div>
      </div>
    </AppPage>
  );
}

