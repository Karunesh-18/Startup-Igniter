import { useEffect, useRef, useState } from 'react';

/** Animated counter that eases to a target value */
export function Counter({ to, suffix = '', duration = 1600, decimals = 0 }: { to: number; suffix?: string; duration?: number; decimals?: number }) {
  const [val, setVal] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const started = useRef(false);

  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !started.current) {
          started.current = true;
          const start = performance.now();
          const tick = (now: number) => {
            const p = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - p, 3);
            setVal(to * eased);
            if (p < 1) requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
        }
      },
      { threshold: 0.3 }
    );
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [to, duration]);

  return (
    <span ref={ref} className="tabular-nums">
      {val.toFixed(decimals)}
      {suffix}
    </span>
  );
}

/** Circular progress ring */
export function CircularProgress({
  value,
  size = 120,
  stroke = 8,
  color = '#2d7ff9',
  color2 = '#8b5cf6',
  label,
  sublabel,
}: {
  value: number;
  size?: number;
  stroke?: number;
  color?: string;
  color2?: string;
  label?: string;
  sublabel?: string;
}) {
  const [animated, setAnimated] = useState(0);
  const ref = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          const start = performance.now();
          const tick = (now: number) => {
            const p = Math.min((now - start) / 1200, 1);
            const eased = 1 - Math.pow(1 - p, 3);
            setAnimated(value * eased);
            if (p < 1) requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
        }
      },
      { threshold: 0.3 }
    );
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [value]);

  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (animated / 100) * circ;
  const id = `grad-${color}-${color2}`.replace(/[^a-z0-9]/gi, '');

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg ref={ref} width={size} height={size} className="-rotate-90">
        <defs>
          <linearGradient id={id} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={color} />
            <stop offset="100%" stopColor={color2} />
          </linearGradient>
        </defs>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={`url(#${id})`}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{ filter: `drop-shadow(0 0 6px ${color}88)` }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-2xl font-semibold text-white tabular-nums">{Math.round(animated)}{label?.includes('%') ? '%' : ''}</span>
        {sublabel && <span className="text-[10px] uppercase tracking-wider text-white/40">{sublabel}</span>}
      </div>
    </div>
  );
}

/** Radar chart */
export function RadarChart({
  data,
  size = 260,
  color = '#2d7ff9',
  color2 = '#ec4899',
}: {
  data: { label: string; value: number }[];
  size?: number;
  color?: string;
  color2?: string;
}) {
  const [progress, setProgress] = useState(0);
  const ref = useRef<SVGSVGElement>(null);
  const cx = size / 2;
  const cy = size / 2;
  const radius = size * 0.36;
  const levels = 4;

  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          const start = performance.now();
          const tick = (now: number) => {
            const p = Math.min((now - start) / 1200, 1);
            const eased = 1 - Math.pow(1 - p, 3);
            setProgress(eased);
            if (p < 1) requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
        }
      },
      { threshold: 0.3 }
    );
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);

  const points = data.map((d, i) => {
    const angle = (i / data.length) * Math.PI * 2 - Math.PI / 2;
    const r = (d.value / 100) * radius * progress;
    return { x: cx + Math.cos(angle) * r, y: cy + Math.sin(angle) * r, lx: cx + Math.cos(angle) * (radius + 18), ly: cy + Math.sin(angle) * (radius + 18), label: d.label, value: d.value };
  });

  const id = `radar-${color}-${color2}`.replace(/[^a-z0-9]/gi, '');

  return (
    <svg ref={ref} width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <defs>
        <radialGradient id={id}>
          <stop offset="0%" stopColor={color} stopOpacity="0.5" />
          <stop offset="100%" stopColor={color2} stopOpacity="0.15" />
        </radialGradient>
      </defs>
      {/* Grid rings */}
      {Array.from({ length: levels }).map((_, l) => {
        const rr = (radius / levels) * (l + 1);
        const pts = data.map((_, i) => {
          const a = (i / data.length) * Math.PI * 2 - Math.PI / 2;
          return `${cx + Math.cos(a) * rr},${cy + Math.sin(a) * rr}`;
        }).join(' ');
        return <polygon key={l} points={pts} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />;
      })}
      {/* Axes */}
      {data.map((_, i) => {
        const a = (i / data.length) * Math.PI * 2 - Math.PI / 2;
        return <line key={i} x1={cx} y1={cy} x2={cx + Math.cos(a) * radius} y2={cy + Math.sin(a) * radius} stroke="rgba(255,255,255,0.05)" />;
      })}
      {/* Data polygon */}
      <polygon
        points={points.map((p) => `${p.x},${p.y}`).join(' ')}
        fill={`url(#${id})`}
        stroke={color}
        strokeWidth="2"
        style={{ filter: `drop-shadow(0 0 8px ${color}66)` }}
      />
      {/* Points */}
      {points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="3" fill={color} stroke="#fff" strokeWidth="1" />
      ))}
      {/* Labels */}
      {points.map((p, i) => (
        <text
          key={i}
          x={p.lx}
          y={p.ly}
          textAnchor="middle"
          dominantBaseline="middle"
          className="fill-white/50"
          style={{ fontSize: 9, fontFamily: 'JetBrains Mono' }}
        >
          {p.label}
        </text>
      ))}
    </svg>
  );
}

/** Heatmap grid */
export function Heatmap({ rows = 7, cols = 12, color = '#2d7ff9' }: { rows?: number; cols?: number; color?: string }) {
  const [cells, setCells] = useState<number[]>([]);

  useEffect(() => {
    setCells(Array.from({ length: rows * cols }, () => Math.random()));
  }, [rows, cols]);

  return (
    <div className="grid gap-1" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
      {cells.map((c, i) => (
        <div
          key={i}
          className="aspect-square rounded-sm transition-all duration-500"
          style={{
            background: c > 0.1 ? hexToRgba(color, c * 0.9) : 'rgba(255,255,255,0.03)',
            animationDelay: `${i * 12}ms`,
          }}
        />
      ))}
    </div>
  );
}

/** Mini area chart with gradient fill */
export function AreaChart({ data, color = '#2d7ff9', color2 = '#8b5cf6', height = 80 }: { data: number[]; color?: string; color2?: string; height?: number }) {
  const [progress, setProgress] = useState(0);
  const ref = useRef<SVGSVGElement>(null);
  const width = 240;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          const start = performance.now();
          const tick = (now: number) => {
            const p = Math.min((now - start) / 1000, 1);
            setProgress(p);
            if (p < 1) requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
        }
      },
      { threshold: 0.3 }
    );
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);

  const pts = data.map((d, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((d - min) / range) * (height - 8) - 4;
    return { x, y: height - (height - y) * progress };
  });

  const path = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const areaPath = `${path} L ${width} ${height} L 0 ${height} Z`;
  const id = `area-${color}`.replace(/[^a-z0-9]/gi, '');

  return (
    <svg ref={ref} width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.4" />
          <stop offset="100%" stopColor={color2} stopOpacity="0" />
        </linearGradient>
        <linearGradient id={`${id}-line`} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={color} />
          <stop offset="100%" stopColor={color2} />
        </linearGradient>
      </defs>
      <path d={areaPath} fill={`url(#${id})`} />
      <path d={path} fill="none" stroke={`url(#${id}-line)`} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ filter: `drop-shadow(0 0 4px ${color}66)` }} />
    </svg>
  );
}

/** Horizontal gradient bar */
export function GradientBar({ value, color = '#2d7ff9', color2 = '#8b5cf6', height = 6 }: { value: number; color?: string; color2?: string; height?: number }) {
  const [w, setW] = useState(0);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const obs = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        const start = performance.now();
        const tick = (now: number) => {
          const p = Math.min((now - start) / 1000, 1);
          setW(value * (1 - Math.pow(1 - p, 3)));
          if (p < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      }
    }, { threshold: 0.3 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [value]);

  return (
    <div ref={ref} className="w-full overflow-hidden rounded-full bg-white/5" style={{ height }}>
      <div
        className="h-full rounded-full transition-all"
        style={{ width: `${w}%`, background: `linear-gradient(90deg, ${color}, ${color2})`, boxShadow: `0 0 8px ${color}66` }}
      />
    </div>
  );
}

function hexToRgba(hex: string, a: number) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${a})`;
}
