import { useEffect, useRef } from 'react';
import { useInView, useMotionValue, useReducedMotion, useSpring } from 'motion/react';

/**
 * Magic UI-style number ticker: springs from 0 to `value` once it scrolls
 * into view. Writes textContent directly, so no re-render per frame.
 */
export function NumberTicker({ value, decimals = 0, className }: { value: number; decimals?: number; className?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const reduce = useReducedMotion();
  const mv = useMotionValue(reduce ? value : 0);
  const spring = useSpring(mv, { damping: 40, stiffness: 120 });
  const inView = useInView(ref, { once: true, margin: '0px 0px -40px 0px' });

  useEffect(() => {
    if (inView) mv.set(value);
  }, [inView, mv, value]);

  useEffect(
    () =>
      spring.on('change', (v) => {
        if (ref.current) ref.current.textContent = v.toFixed(decimals);
      }),
    [spring, decimals],
  );

  return (
    <span ref={ref} className={className}>
      {(reduce ? value : 0).toFixed(decimals)}
    </span>
  );
}
