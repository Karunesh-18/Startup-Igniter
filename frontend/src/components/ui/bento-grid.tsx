import type { HTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/utils';

/** Aceternity-style bento grid: a dense 4-column grid whose items opt into larger spans. */
export function BentoGrid({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4', className)} {...props} />;
}

export function BentoGridItem({
  className,
  title,
  description,
  header,
  icon,
  children,
}: {
  className?: string;
  title: ReactNode;
  description?: ReactNode;
  header?: ReactNode;
  icon?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <div className={cn('flex flex-col justify-between gap-4 rounded-2xl border border-white/[0.07] bg-charcoal/70 p-5', className)}>
      {header}
      <div>
        {icon}
        <div className="mt-3 text-base font-medium text-white">{title}</div>
        {description && <div className="mt-1 text-sm leading-relaxed text-white/55">{description}</div>}
        {children}
      </div>
    </div>
  );
}
