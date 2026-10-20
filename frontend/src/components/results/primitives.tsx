import { useState, type ComponentType, type CSSProperties, type ReactNode } from 'react';

// Small building blocks shared by every report tab.

export function StatCard({ label, value, sub, color = '#2d7ff9' }: { label: string; value: ReactNode; sub?: string; color?: string }) {
  return (
    <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] p-4">
      <div className="text-xs text-white/45">{label}</div>
      <div className="mt-1 break-words text-xl font-semibold" style={{ color }}>
        {value}
      </div>
      {sub && <div className="mt-0.5 text-xs text-white/40">{sub}</div>}
    </div>
  );
}

export function TagList({ items, color = '#2d7ff9', max = 6 }: { items: string[]; color?: string; max?: number }) {
  const [expanded, setExpanded] = useState(false);
  const list = expanded ? items : items.slice(0, max);
  return (
    <div className="flex flex-wrap gap-1.5">
      {list.map((t, i) => (
        <span key={i} className="rounded-full px-2.5 py-1 text-xs" style={{ background: `${color}18`, color, border: `1px solid ${color}33` }}>
          {t}
        </span>
      ))}
      {items.length > max && (
        <button
          onClick={() => setExpanded((e) => !e)}
          className="rounded-full border border-white/10 px-2.5 py-1 text-xs text-white/45 transition-colors hover:text-white"
        >
          {expanded ? 'Show less' : `+${items.length - max} more`}
        </button>
      )}
    </div>
  );
}

export function Label({ children }: { children: ReactNode }) {
  return <div className="mb-2 text-xs text-white/40">{children}</div>;
}

export function SectionCard({
  title,
  icon: Icon,
  color = '#2d7ff9',
  children,
}: {
  title: string;
  icon: ComponentType<{ className?: string; style?: CSSProperties }>;
  color?: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-white/[0.06] bg-white/[0.025] p-5">
      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg" style={{ background: `${color}22` }}>
          <Icon className="h-3.5 w-3.5" style={{ color }} />
        </div>
        <h3 className="text-sm font-medium text-white">{title}</h3>
      </div>
      {children}
    </section>
  );
}

/** Horizontal score bar. `value` is on a 0-`max` scale. */
export function RatingBar({ label, value, max = 10, color = '#2d7ff9' }: { label: string; value: number; max?: number; color?: string }) {
  const pct = Math.min(Math.max((value / max) * 100, 0), 100);
  return (
    <div className="flex items-center gap-3">
      <span className="w-36 shrink-0 text-xs text-white/60 sm:w-44">{label}</span>
      <div
        className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/5"
        role="meter"
        aria-label={label}
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
      >
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="w-10 text-right font-mono text-xs tabular-nums text-white/50">{value.toFixed(max > 10 ? 0 : 1)}</span>
    </div>
  );
}

export function Empty({ what }: { what: string }) {
  return <div className="py-16 text-center text-white/40">{what} data is not in this report.</div>;
}
