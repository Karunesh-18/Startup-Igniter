import { useEffect, useState, type ComponentType } from 'react';
import { Github, Link2, Loader2, NotebookText, Slack } from 'lucide-react';
import { connectIntegration, disconnectIntegration, listIntegrations, PaywallError } from '@/lib/api';
import type { IntegrationInfo, IntegrationProvider } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { AppPage, ErrorNote, UpgradeCard } from './shared';

interface ProviderDef {
  id: IntegrationProvider;
  name: string;
  icon: ComponentType<{ className?: string }>;
  blurb: string;
  tokenLabel: string;
  tokenHint: string;
  extra?: { key: string; label: string };
}

const PROVIDERS: ProviderDef[] = [
  {
    id: 'github',
    name: 'GitHub',
    icon: Github,
    blurb: 'Turn the roadmap, risks and experiments into issues in your repo, after a preview.',
    tokenLabel: 'Personal access token',
    tokenHint: 'Needs "Issues: write" on the repository (fine-grained token) or the repo scope.',
  },
  {
    id: 'slack',
    name: 'Slack',
    icon: Slack,
    blurb: 'Post a verdict summary and a link to the report in a channel.',
    tokenLabel: 'Incoming webhook URL',
    tokenHint: 'https://hooks.slack.com/services/...',
  },
  {
    id: 'notion',
    name: 'Notion',
    icon: NotebookText,
    blurb: 'Create a page with the full report under a parent page you choose.',
    tokenLabel: 'Internal integration secret',
    tokenHint: 'Share the parent page with your integration first.',
    extra: { key: 'parent_page_id', label: 'Parent page ID' },
  },
  {
    id: 'webhook',
    name: 'Webhook',
    icon: Link2,
    blurb: 'POST the full report as JSON to any https endpoint when you push it.',
    tokenLabel: 'Endpoint URL',
    tokenHint: 'Must be https and publicly reachable.',
  },
];

const input = 'w-full rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white placeholder-white/30 focus:border-electric focus:outline-none';

function ProviderCard({ def, info, onChange }: { def: ProviderDef; info?: IntegrationInfo; onChange: () => void }) {
  const [open, setOpen] = useState(false);
  const [token, setToken] = useState('');
  const [extra, setExtra] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const Icon = def.icon;

  const connect = async () => {
    setBusy(true);
    setError(null);
    try {
      await connectIntegration(def.id, { token: token.trim(), config: def.extra ? { [def.extra.key]: extra.trim() } : undefined });
      setOpen(false);
      setToken('');
      setExtra('');
      onChange();
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Could not connect.'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="rounded-2xl border border-white/[0.07] bg-charcoal/60 p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/[0.06]">
            <Icon className="h-5 w-5 text-white" />
          </span>
          <div>
            <h2 className="font-medium text-white">{def.name}</h2>
            <p className="mt-1 text-sm text-white/55">{def.blurb}</p>
            {info && <p className="mt-2 text-xs text-emerald-400">Connected{info.label ? ` as ${info.label}` : ''}</p>}
          </div>
        </div>
        {info ? (
          <Button variant="outline" size="sm" onClick={() => disconnectIntegration(def.id).then(onChange)}>
            Disconnect
          </Button>
        ) : (
          <Button variant="outline" size="sm" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
            Connect
          </Button>
        )}
      </div>

      {open && !info && (
        <div className="mt-4 space-y-3">
          <label className="block text-xs text-white/50">
            {def.tokenLabel}
            <input type="password" autoComplete="off" value={token} onChange={(e) => setToken(e.target.value)} placeholder={def.tokenHint} className={`${input} mt-1.5`} />
          </label>
          {def.extra && (
            <label className="block text-xs text-white/50">
              {def.extra.label}
              <input value={extra} onChange={(e) => setExtra(e.target.value)} className={`${input} mt-1.5`} />
            </label>
          )}
          <p className="text-xs text-white/35">Stored encrypted. Used only when you push a report.</p>
          {error instanceof PaywallError ? <UpgradeCard message={error.message} /> : <ErrorNote error={error?.message ?? null} />}
          <Button size="sm" onClick={connect} loading={busy} disabled={token.trim().length < 8 || Boolean(def.extra && !extra.trim())}>
            Save connection
          </Button>
        </div>
      )}
    </section>
  );
}

export default function Integrations() {
  const [items, setItems] = useState<IntegrationInfo[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = () =>
    listIntegrations()
      .then(setItems)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : 'Could not load integrations.'));
  useEffect(() => {
    load();
  }, []);

  return (
    <AppPage>
      <h1 className="font-serif text-4xl text-white">Integrations</h1>
      <p className="mt-3 max-w-xl text-white/55">Send what the analysis found to the tools you already work in. Pushing is always an explicit action on a finished report.</p>
      <div className="mt-6 space-y-4">
        <ErrorNote error={error} />
        {items === null && !error && <Loader2 className="mx-auto mt-12 h-6 w-6 animate-spin text-electric" aria-label="Loading" />}
        {items && PROVIDERS.map((p) => <ProviderCard key={p.id} def={p} info={items.find((i) => i.provider === p.id)} onChange={load} />)}
      </div>
    </AppPage>
  );
}
