import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Check, Minus } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { subscribePro } from '@/lib/checkout';
import { formatINR } from '@/lib/format';
import { cn } from '@/lib/utils';
import { Button, buttonVariants } from '@/components/ui/button';
import { AppPage, ErrorNote, useBilling } from './shared';

const ROWS: { label: string; free: boolean | string; report: boolean | string; pro: boolean | string }[] = [
  { label: 'Readiness score and go / pivot / no-go verdict', free: true, report: true, pro: true },
  { label: 'Analyses', free: '3 total', report: 'Per report', pro: 'Unlimited' },
  { label: 'All 13 crews, risks, roadmap and legal checklist', free: false, report: true, pro: true },
  { label: 'Evidence ledger: every claim checked against sources', free: false, report: true, pro: true },
  { label: 'Skeptic debate and pre-mortem', free: false, report: true, pro: true },
  { label: 'PDF and Markdown export', free: false, report: true, pro: true },
  { label: 'AI co-founder chat that edits your idea', free: false, report: false, pro: true },
  { label: 'Experiments tracker and version-to-version score changes', free: false, report: false, pro: true },
  { label: 'GitHub issues, Slack, Notion and webhook export', free: false, report: false, pro: true },
];

function Cell({ v }: { v: boolean | string }) {
  if (typeof v === 'string') return <span className="text-sm text-white/80">{v}</span>;
  return v ? <Check className="mx-auto h-4 w-4 text-teal" aria-label="Included" /> : <Minus className="mx-auto h-4 w-4 text-white/20" aria-label="Not included" />;
}

export default function Pricing() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { billing, reload } = useBilling();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const report = billing ? formatINR(billing.prices.report_paise) : '₹299';
  const pro = billing ? formatINR(billing.prices.pro_paise) : '₹999';

  const goPro = async () => {
    if (!user) return navigate('/login', { state: { from: '/pricing' } });
    if (!billing) return;
    setBusy(true);
    setError(null);
    try {
      if (await subscribePro(billing, user.email)) {
        await reload();
        navigate('/billing');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'The payment could not be completed.');
    } finally {
      setBusy(false);
    }
  };

  const isPro = billing?.plan === 'pro';

  return (
    <AppPage wide>
      <div className="mx-auto max-w-2xl text-center">
        <h1 className="font-serif text-4xl text-white sm:text-6xl">Pay for what you use</h1>
        <p className="mt-4 text-white/60">Start free. Buy a single full report, or go Pro for everything. Prices include GST.</p>
      </div>

      <div className="mx-auto mt-10 max-w-3xl">
        <ErrorNote error={error} />
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        <section className="flex flex-col rounded-3xl border border-white/10 bg-charcoal/60 p-6">
          <h2 className="text-lg font-medium text-white">Free</h2>
          <p className="mt-3 font-serif text-5xl text-white">₹0</p>
          <p className="mt-2 text-sm text-white/50">Score and verdict for your first three ideas.</p>
          <Link to={user ? '/new' : '/login'} className={cn(buttonVariants({ variant: 'outline' }), 'mt-auto')}>
            {user ? 'Analyze an idea' : 'Sign up free'}
          </Link>
        </section>

        <section className="flex flex-col rounded-3xl border border-white/10 bg-charcoal/60 p-6">
          <h2 className="text-lg font-medium text-white">Full report</h2>
          <p className="mt-3 font-serif text-5xl text-white">
            {report}
            <span className="ml-1 text-base text-white/40">one time</span>
          </p>
          <p className="mt-2 text-sm text-white/50">Unlock the complete report for one analysis. No subscription.</p>
          <Link to={user ? '/app' : '/login'} className={cn(buttonVariants({ variant: 'outline' }), 'mt-auto')}>
            Unlock from a finished analysis
          </Link>
        </section>

        <section className="relative flex flex-col rounded-3xl border border-electric/50 bg-electric/[0.07] p-6 shadow-[0_0_60px_-20px_rgba(45,127,249,0.6)]">
          <span className="absolute -top-3 left-6 rounded-full bg-electric px-3 py-0.5 text-[11px] font-semibold text-white">Best value</span>
          <h2 className="text-lg font-medium text-white">Pro</h2>
          <p className="mt-3 font-serif text-5xl text-white">
            {pro}
            <span className="ml-1 text-base text-white/40">/ month</span>
          </p>
          <p className="mt-2 text-sm text-white/60">Unlimited analyses, the AI co-founder, experiments and integrations. Cancel any time.</p>
          <Button variant="shine" className="mt-auto" onClick={goPro} loading={busy} disabled={isPro}>
            {isPro ? 'You are on Pro' : 'Go Pro'}
          </Button>
        </section>
      </div>

      <div className="mt-12 overflow-x-auto rounded-2xl border border-white/[0.07]">
        <table className="w-full min-w-[34rem] text-left">
          <caption className="sr-only">What each plan includes</caption>
          <thead>
            <tr className="border-b border-white/[0.07] text-xs text-white/45">
              <th scope="col" className="px-4 py-3 font-normal">
                Feature
              </th>
              {['Free', 'Report', 'Pro'].map((h) => (
                <th key={h} scope="col" className="w-28 px-4 py-3 text-center font-normal">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ROWS.map((r) => (
              <tr key={r.label} className="border-b border-white/[0.04] last:border-0">
                <th scope="row" className="px-4 py-3 text-sm font-normal text-white/80">
                  {r.label}
                </th>
                {[r.free, r.report, r.pro].map((v, i) => (
                  <td key={i} className="px-4 py-3 text-center">
                    <Cell v={v} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-6 text-center text-xs text-white/35">Payments are processed by Razorpay in Indian rupees. AI-generated analysis; verify findings independently.</p>
    </AppPage>
  );
}
