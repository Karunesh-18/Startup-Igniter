import {
  Bar, BarChart, Cell, PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, RadialBar, RadialBarChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';

const AXIS = { fill: 'rgba(255,255,255,0.55)', fontSize: 11 };
const TOOLTIP = {
  contentStyle: { background: '#0a0c1a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, fontSize: 12 },
  itemStyle: { color: '#e8eaf6' },
  labelStyle: { color: 'rgba(255,255,255,0.6)' },
};

/** One 0-100 score per crew. */
export function CrewRadar({ data }: { data: { crew: string; score: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <RadarChart data={data} outerRadius="72%">
        <PolarGrid stroke="rgba(255,255,255,0.1)" />
        <PolarAngleAxis dataKey="crew" tick={AXIS} />
        <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
        <Radar dataKey="score" name="Score" stroke="#2d7ff9" fill="#2d7ff9" fillOpacity={0.25} strokeWidth={2} />
        <Tooltip {...TOOLTIP} formatter={(v) => [`${Math.round(Number(v))}/100`, 'Score']} />
      </RadarChart>
    </ResponsiveContainer>
  );
}

const fmtUsd = (n: number) =>
  n >= 1e12 ? `$${(n / 1e12).toFixed(1)}T` : n >= 1e9 ? `$${(n / 1e9).toFixed(1)}B` : n >= 1e6 ? `$${(n / 1e6).toFixed(1)}M` : `$${Math.round(n).toLocaleString()}`;

/** TAM / SAM / SOM as horizontal bars on a log scale (they differ by orders of magnitude). */
export function MarketSizeBars({ data }: { data: { name: string; value: number; color: string }[] }) {
  return (
    <ResponsiveContainer width="100%" height={150}>
      <BarChart data={data} layout="vertical" margin={{ left: 0, right: 16 }}>
        <XAxis type="number" scale="log" domain={['auto', 'auto']} hide />
        <YAxis type="category" dataKey="name" tick={AXIS} axisLine={false} tickLine={false} width={44} />
        <Tooltip {...TOOLTIP} cursor={{ fill: 'rgba(255,255,255,0.04)' }} formatter={(v) => [fmtUsd(Number(v)), 'Size']} />
        <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={22}>
          {data.map((d) => (
            <Cell key={d.name} fill={d.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Technology Readiness Level (1-9) as a half-ring gauge. */
export function TRLGauge({ level }: { level: number }) {
  return (
    <div className="relative h-[140px] w-[240px]">
      <RadialBarChart
        width={240}
        height={140}
        data={[{ value: level }]}
        cx={120}
        cy={128}
        startAngle={180}
        endAngle={0}
        innerRadius={92}
        outerRadius={112}
        barSize={14}
      >
        <PolarAngleAxis type="number" domain={[0, 9]} tick={false} />
        <RadialBar dataKey="value" fill="#8b5cf6" background={{ fill: 'rgba(255,255,255,0.06)' }} cornerRadius={7} />
      </RadialBarChart>
      <div className="absolute inset-x-0 bottom-2 text-center">
        <div className="font-mono text-3xl font-semibold text-white">{level}</div>
        <div className="text-xs text-white/45">of 9</div>
      </div>
    </div>
  );
}
