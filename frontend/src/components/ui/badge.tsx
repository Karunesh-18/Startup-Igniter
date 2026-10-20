import type { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  /** Any hex colour; tints background and text. */
  color?: string;
}

export function Badge({ color = '#2d7ff9', className, style, ...props }: BadgeProps) {
  return (
    <span
      className={cn('inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-medium', className)}
      style={{ background: `${color}1f`, color, ...style }}
      {...props}
    />
  );
}
