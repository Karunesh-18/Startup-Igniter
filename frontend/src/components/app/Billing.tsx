import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { billingPayments, cancelSubscription } from '@/lib/api';
import { formatDate, formatINR } from '@/lib/format';
import type { Payment } from '@/lib/types';
import { Button, buttonVariants } from '@/components/ui/button';
import { AppPage, ErrorNote, useBilling } from './shared';

export default function Billing() {
  const { billing, reload } = useBilling();
  const [payments, setPayments] = useState<Payment[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    billingPayments()
      .then(setPayments)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : 'Could not load payments.'));
  }, []);

  const cancel = async () => {
    if (!window.confirm('Cancel Pro? You keep access until the end of the period you have paid for.')) return;
    setBusy(true);
    try {
      await cancelSubscription();
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not cancel.');
    } finally {
      setBusy(false);
    }
  };

  if (!billing) return <AppPage>{error ? <ErrorNote error={error} /> : <Loader2 className="mx-auto mt-24 h-6 w-6 animate-spin text-electric" aria-label="Loading" />}</AppPage>;

  return (
    <AppPage>
      <h1 className="font-serif text-4xl text-white">Billing</h1>
      <div className="mt-4">
        <ErrorNote error={error} />
      </div>

      <section className="mt-6 rounded-2xl border border-white/[0.07] bg-charcoal/60 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-white/50">Current plan</p>
            <p className="mt-1 font-serif text-3xl text-white">{billing.plan === 'pro' ? 'Pro' : 'Free'}</p>
            {billing.plan === 'pro' && billing.pro_until && (
              <p className="mt-1 text-sm text-white/55">
                {billing.cancelling ? `Ends on ${formatDate(billing.pro_until)}` : `Renews on ${formatDate(billing.pro_until)} at ${formatINR(billing.prices.pro_paise)}`}
              </p>
            )}
            {billing.plan === 'free' && (
              <p className="mt-1 text-sm text-white/55">
                {Math.min(billing.analyses_used, billing.free_limit)} of {billing.free_limit} free analyses used
              </p>
            )}
          </div>
          {billing.plan === 'pro' && !billing.cancelling ? (
            <Button variant="danger" onClick={cancel} loading={busy}>
              Cancel Pro
            </Button>
          ) : (
            <Link to="/pricing" className={buttonVariants({ variant: 'shine' })}>
              {billing.cancelling ? 'Resume with Pro' : `Go Pro ${formatINR(billing.prices.pro_paise)}/mo`}
            </Link>
          )}
        </div>
      </section>

      <section className="mt-6">
        <h2 className="mb-3 text-sm text-white/55">Payments</h2>
        {payments?.length === 0 && <p className="rounded-xl border border-dashed border-white/15 px-4 py-8 text-center text-sm text-white/40">No payments yet.</p>}
        <ul className="space-y-2">
          {payments?.map((p) => (
            <li key={p.id} className="flex items-center justify-between gap-3 rounded-xl border border-white/[0.07] bg-charcoal/60 px-4 py-3 text-sm">
              <div>
                <p className="text-white">{p.kind === 'pro' ? 'Pro subscription' : 'Full report'}</p>
                <p className="text-xs text-white/40">{formatDate(p.paid_at ?? p.created_at)}</p>
              </div>
              <div className="text-right">
                <p className="font-mono text-white">{formatINR(p.amount_paise)}</p>
                <p className={p.status === 'paid' ? 'text-xs text-emerald-400' : 'text-xs text-white/40'}>{p.status}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </AppPage>
  );
}
