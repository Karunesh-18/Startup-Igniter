import { useEffect, useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, Lock, Sparkles } from 'lucide-react';
import { billingMe, PaywallError } from '@/lib/api';
import { formatINR } from '@/lib/format';
import type { BillingMe, Verdict } from '@/lib/types';
import { cn } from '@/lib/utils';
import { buttonVariants } from '@/components/ui/button';

/** Page chrome for signed-in pages: clears the fixed nav and constrains width. */
export function AppPage({ children, wide = false }: { children: ReactNode; wide?: boolean }) {
  return (
    <main className={cn('mx-auto min-h-screen px-4 pb-20 pt-24 sm:px-6', wide ? 'max-w-6xl' : 'max-w-4xl')}>{children}</main>
  );
}

export function useBilling() {
  const [billing, setBilling] = useState<BillingMe | null>(null);
  const reload = () => billingMe().then(setBilling).catch(() => setBilling(null));
  useEffect(() => {
    reload();
  }, []);
  return { billing, reload };
}

const VERDICT: Record<Verdict, { label: string; color: string }> = {
  go: { label: 'Go', color: '#10b981' },
  pivot: { label: 'Pivot', color: '#fb923c' },
  'no-go': { label: 'No-go', color: '#ef4444' },
};

export function VerdictBadge({ verdict, className }: { verdict: Verdict | null | undefined; className?: string }) {
  if (!verdict) return null;
  const v = VERDICT[verdict];
  return (
    <span
      className={cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide', className)}
      style={{ background: `${v.color}22`, color: v.color }}
    >
      {v.label}
    </span>
  );
}
export const verdictColor = (v: Verdict | null | undefined) => (v ? VERDICT[v].color : '#94a3b8');

export function ErrorNote({ error }: { error: string | null }) {
  if (!error) return null;
  return (
    <div role="alert" className="flex items-start gap-3 rounded-2xl border border-red-500/25 bg-red-500/10 p-4 text-sm">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" aria-hidden="true" />
      <span className="text-red-200">{error}</span>
    </div>
  );
}

/** Turns a 402 into an upgrade card; any other error into a plain message. */
export function ApiErrorNote({ error }: { error: Error | null }) {
  if (!error) return null;
  if (error instanceof PaywallError) return <UpgradeCard message={error.message} />;
  return <ErrorNote error={error.message} />;
}

export function UpgradeCard({ message, report = false }: { message: string; report?: boolean }) {
  const { billing } = useBilling();
  return (
    <div className="flex flex-col items-start gap-4 rounded-2xl border border-violet/30 bg-violet/10 p-5 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex gap-3">
        <Lock className="mt-0.5 h-4 w-4 shrink-0 text-violet-300" aria-hidden="true" />
        <p className="text-sm text-white/80">{message}</p>
      </div>
      <Link to="/pricing" className={cn(buttonVariants({ size: 'sm' }), 'shrink-0')}>
        <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
        {report ? 'See options' : billing ? `Go Pro ${formatINR(billing.prices.pro_paise)}/mo` : 'See plans'}
      </Link>
    </div>
  );
}
