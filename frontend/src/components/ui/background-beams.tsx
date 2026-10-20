import { cn } from '@/lib/utils';

// Aceternity-style background beams, reduced to a handful of SVG curves with
// a travelling dash (the `beam-travel` keyframe in index.css). No JS loop.
const PATHS = [
  'M-380 -189C-380 -189 -312 216 152 343C616 470 684 875 684 875',
  'M-310 -269C-310 -269 -242 136 222 263C686 390 754 795 754 795',
  'M-240 -349C-240 -349 -172 56 292 183C756 310 824 715 824 715',
  'M-170 -429C-170 -429 -102 -24 362 103C826 230 894 635 894 635',
  'M-100 -509C-100 -509 -32 -104 432 23C896 150 964 555 964 555',
  'M-30 -589C-30 -589 38 -184 502 -57C966 70 1034 475 1034 475',
];

export function BackgroundBeams({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      className={cn('pointer-events-none absolute inset-0 h-full w-full', className)}
      viewBox="0 0 696 316"
      preserveAspectRatio="xMidYMid slice"
      fill="none"
    >
      <defs>
        <linearGradient id="beam-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#2d7ff9" stopOpacity="0" />
          <stop offset="0.5" stopColor="#8b5cf6" />
          <stop offset="1" stopColor="#14b8a6" stopOpacity="0" />
        </linearGradient>
      </defs>
      {PATHS.map((d, i) => (
        <g key={d}>
          <path d={d} stroke="rgba(255,255,255,0.05)" strokeWidth="0.5" />
          <path
            d={d}
            stroke="url(#beam-grad)"
            strokeWidth="1"
            pathLength={1}
            strokeDasharray="0.12 0.88"
            className="animate-beam-travel"
            style={{ animationDelay: `${i * 1.3}s`, animationDuration: `${7 + (i % 3) * 2}s` }}
          />
        </g>
      ))}
    </svg>
  );
}
