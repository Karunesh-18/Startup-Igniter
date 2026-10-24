import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Download, FileText, Github, Link2, Lock, NotebookText, Send, Slack } from 'lucide-react';
import { downloadReport, listIntegrations, pushGithub, pushMessage, PaywallError } from '@/lib/api';
import { payForReport } from '@/lib/checkout';
import { useAuth } from '@/lib/auth';
import { formatINR } from '@/lib/format';
import type { BillingMe, IntegrationProvider, PushedIssue } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { ApiErrorNote } from '@/components/app/shared';

const PUSH: { id: Exclude<IntegrationProvider, 'github'>; label: string; icon: typeof Slack }[] = [
  { id: 'slack', label: 'Slack', icon: Slack },
  { id: 'notion', label: 'Notion', icon: NotebookText },
  { id: 'webhook', label: 'Webhook', icon: Link2 },
];

function GithubDialog({ analysisId, defaultRepo, onClose }: { analysisId: string; defaultRepo: string; onClose: () => void }) {
  const [repo, setRepo] = useState(defaultRepo);
  const [issues, setIssues] = useState<PushedIssue[] | null>(null);
  const [created, setCreated] = useState<{ title: string; url: string }[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const preview = async () => {
    setBusy(true);
    setError(null);
    try {
      setIssues((await pushGithub(analysisId, { repo, dry_run: true })).issues ?? []);
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Preview failed.'));
    } finally {
      setBusy(false);
    }
  };
  const create = async () => {
    setBusy(true);
    setError(null);
    try {
      const r = await pushGithub(analysisId, { repo, dry_run: false });
      setCreated(r.created ?? []);
      if (r.failed?.length) setError(new Error(`${r.failed.length} issue(s) could not be created. Check the token's access to ${repo}.`));
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Could not create issues.'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div role="dialog" aria-modal="true" aria-label="Create GitHub issues" className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={onClose}>
      <div className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-white/10 bg-charcoal p-6" onClick={(e) => e.stopPropagation()}>
        <h2 className="font-serif text-2xl text-white">Create GitHub issues</h2>
        <p className="mt-1 text-sm text-white/50">Roadmap items, compliance tasks, risks and experiments from this report. You see the list before anything is created.</p>
        <div className="mt-4 flex gap-2">
          <input
            value={repo}
            onChange={(e) => setRepo(e.target.value)}
            placeholder="owner/repo"
            aria-label="Repository"
            className="min-w-0 flex-1 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white focus:border-electric focus:outline-none"
          />
          <Button variant="outline" onClick={preview} loading={busy && !issues} disabled={!repo.includes('/')}>
            Preview
          </Button>
        </div>
        <div className="mt-3">
          <ApiErrorNote error={error} />
        </div>
        {issues && !created && (
          <>
            <ul className="mt-4 max-h-64 space-y-1.5 overflow-y-auto text-sm text-white/75">
              {issues.map((i, n) => (
                <li key={n} className="rounded-lg bg-white/[0.04] px-3 py-2">
                  {i.title}
                </li>
              ))}
            </ul>
            <Button className="mt-4 w-full" variant="shine" onClick={create} loading={busy}>
              Create {issues.length} issues in {repo}
            </Button>
          </>
        )}
        {created && (
          <ul className="mt-4 space-y-1 text-sm">
            {created.map((c) => (
              <li key={c.url}>
                <a href={c.url} target="_blank" rel="noreferrer" className="text-electric-300 hover:underline">
                  {c.title}
                </a>
              </li>
            ))}
          </ul>
        )}
        <Button className="mt-4" variant="ghost" size="sm" onClick={onClose}>
          Close
        </Button>
      </div>
    </div>
  );
}

export default function ReportActions({
  analysisId,
  title,
  unlocked,
  billing,
  githubRepo,
  onUnlocked,
}: {
  analysisId: string;
  title: string;
  unlocked: boolean;
  billing: BillingMe | null;
  githubRepo: string;
  onUnlocked: () => void;
}) {
  const { user } = useAuth();
  const [menu, setMenu] = useState(false);
  const [connected, setConnected] = useState<IntegrationProvider[]>([]);
  const [ghOpen, setGhOpen] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (billing?.plan === 'pro') listIntegrations().then((l) => setConnected(l.map((i) => i.provider))).catch(() => undefined);
  }, [billing?.plan]);
  useEffect(() => {
    const close = (e: MouseEvent) => !ref.current?.contains(e.target as Node) && setMenu(false);
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  const run = async (key: string, fn: () => Promise<unknown>, ok?: string) => {
    setBusy(key);
    setError(null);
    setDone(null);
    try {
      await fn();
      if (ok) setDone(ok);
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Something went wrong.'));
    } finally {
      setBusy(null);
    }
  };

  const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 40) || 'report';
  const isPro = billing?.plan === 'pro';

  if (!unlocked) {
    return (
      <div className="flex flex-col items-end gap-2">
        <Button
          size="sm"
          variant="shine"
          loading={busy === 'unlock'}
          disabled={!billing}
          onClick={() =>
            run('unlock', async () => {
              if (billing && (await payForReport(billing, analysisId, user?.email))) onUnlocked();
            })
          }
        >
          <Lock className="h-3.5 w-3.5" aria-hidden="true" />
          Unlock full report {billing ? formatINR(billing.prices.report_paise) : ''}
        </Button>
        {error && <p role="alert" className="max-w-xs text-right text-xs text-red-300">{error.message}</p>}
      </div>
    );
  }

  return (
    <div className="relative flex items-center gap-2" ref={ref}>
      <Button size="sm" variant="outline" loading={busy === 'pdf'} onClick={() => run('pdf', () => downloadReport(analysisId, 'pdf', slug))}>
        <Download className="h-3.5 w-3.5" aria-hidden="true" />
        PDF
      </Button>
      <Button size="sm" variant="ghost" onClick={() => setMenu((m) => !m)} aria-expanded={menu} aria-haspopup="menu">
        <Send className="h-3.5 w-3.5" aria-hidden="true" />
        Send to
      </Button>
      {menu && (
        <div role="menu" className="absolute right-0 top-full z-50 mt-2 w-64 rounded-xl border border-white/10 bg-charcoal p-2 shadow-2xl">
          <button role="menuitem" className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-white/80 hover:bg-white/[0.06]" onClick={() => run('md', () => downloadReport(analysisId, 'md', slug))}>
            <FileText className="h-4 w-4" aria-hidden="true" />
            Markdown file
          </button>
          {!isPro ? (
            <p className="px-3 py-2 text-xs text-white/45">
              GitHub, Slack, Notion and webhooks are part of{' '}
              <Link to="/pricing" className="text-electric-300 hover:underline">
                Pro
              </Link>
              .
            </p>
          ) : (
            <>
              <button
                role="menuitem"
                disabled={!connected.includes('github')}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-white/80 hover:bg-white/[0.06] disabled:opacity-40"
                onClick={() => {
                  setMenu(false);
                  setGhOpen(true);
                }}
              >
                <Github className="h-4 w-4" aria-hidden="true" />
                GitHub issues
              </button>
              {PUSH.map((p) => (
                <button
                  key={p.id}
                  role="menuitem"
                  disabled={!connected.includes(p.id)}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-white/80 hover:bg-white/[0.06] disabled:opacity-40"
                  onClick={() => {
                    setMenu(false);
                    run(p.id, () => pushMessage(analysisId, p.id), `Sent to ${p.label}.`);
                  }}
                >
                  <p.icon className="h-4 w-4" aria-hidden="true" />
                  {p.label}
                </button>
              ))}
              <Link to="/integrations" className="block px-3 py-2 text-xs text-electric-300 hover:underline">
                Connect more
              </Link>
            </>
          )}
        </div>
      )}
      {ghOpen && <GithubDialog analysisId={analysisId} defaultRepo={githubRepo} onClose={() => setGhOpen(false)} />}
      {(error || done) && (
        <div className="absolute right-0 top-full mt-2 w-72">
          {error instanceof PaywallError || error ? <ApiErrorNote error={error} /> : <p className="rounded-xl bg-teal/15 px-3 py-2 text-xs text-teal-300">{done}</p>}
        </div>
      )}
    </div>
  );
}
