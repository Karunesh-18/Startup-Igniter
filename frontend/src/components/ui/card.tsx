import { useRef, type HTMLAttributes, type MouseEvent } from 'react';
import { cn } from '@/lib/utils';

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('rounded-2xl border border-white/[0.07] bg-charcoal/60 p-5 backdrop-blur-sm', className)} {...props} />;
}

/**
 * Card with a pointer-following glow (KokonutUI / Cult-UI style). The glow is
 * a radial gradient positioned from two CSS custom properties, so tracking
 * the pointer costs no React re-renders.
 */
export function SpotlightCard({
  className,
  color = '#2d7ff9',
  children,
  ...props
}: HTMLAttributes<HTMLDivElement> & { color?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const onMove = (e: MouseEvent<HTMLDivElement>) => {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    el.style.setProperty('--mx', `${e.clientX - r.left}px`);
    el.style.setProperty('--my', `${e.clientY - r.top}px`);
  };
  return (
    <div
      ref={ref}
      onMouseMove={onMove}
      className={cn(
        'group/spot relative isolate overflow-hidden rounded-2xl border border-white/[0.07] bg-charcoal/70 transition-colors duration-300 hover:border-white/15',
        className,
      )}
      {...props}
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10 opacity-0 transition-opacity duration-300 group-hover/spot:opacity-100"
        style={{ background: `radial-gradient(360px circle at var(--mx, 50%) var(--my, 50%), ${color}26, transparent 65%)` }}
      />
      {children}
    </div>
  );
}
