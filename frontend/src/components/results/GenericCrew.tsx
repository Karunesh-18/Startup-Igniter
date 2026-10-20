import { toPercent } from '@/lib/report';
import { Empty, Label, RatingBar, TagList } from './primitives';

/**
 * Renders any crew result object by shape, not by field name, so crews 4-12
 * keep rendering while their schemas move:
 *   long string → paragraph · short string/number/bool → key/value
 *   `*_score` number or {name: number} map → score bars
 *   string[] → tags (short) or bullets (long) · object[] → cards · object → nested section
 */

type Obj = Record<string, unknown>;
const isObj = (v: unknown): v is Obj => typeof v === 'object' && v !== null && !Array.isArray(v);
const SKIP = new Set(['project_id', 'confidence_score', 'status']);

const humanize = (k: string) =>
  k
    .replace(/_/g, ' ')
    .replace(/\b(mvp|cac|ltv|kpis?|nda|ai|ml|ip)\b/gi, (m) => m.toUpperCase())
    .replace(/^\w/, (c) => c.toUpperCase());

const isEmpty = (v: unknown) =>
  v == null || v === '' || (Array.isArray(v) && v.length === 0) || (isObj(v) && Object.keys(v).length === 0);

const isScoreMap = (v: Obj) => Object.values(v).every((x) => typeof x === 'number');
const isShort = (v: unknown) => typeof v === 'number' || typeof v === 'boolean' || (typeof v === 'string' && v.length <= 80);

function Scalar({ value }: { value: unknown }) {
  if (typeof value === 'boolean') return <>{value ? 'Yes' : 'No'}</>;
  return <>{String(value)}</>;
}

function ScoreBars({ scores, color }: { scores: [string, number][]; color: string }) {
  return (
    <div className="space-y-3">
      {scores.map(([k, v]) => (
        <RatingBar key={k} label={humanize(k.replace(/_score$/, ''))} value={toPercent(v, k)} max={100} color={color} />
      ))}
    </div>
  );
}

function ObjectView({ data, color, depth }: { data: Obj; color: string; depth: number }) {
  const entries = Object.entries(data).filter(([k, v]) => !SKIP.has(k) && !isEmpty(v));
  const scores = entries.filter((e): e is [string, number] => typeof e[1] === 'number' && e[0].endsWith('_score'));
  const facts = entries.filter(([k, v]) => isShort(v) && !k.endsWith('_score'));
  const prose = entries.filter(([, v]) => typeof v === 'string' && v.length > 80) as [string, string][];
  const rest = entries.filter(([, v]) => typeof v === 'object');

  return (
    <div className="space-y-5">
      {scores.length > 0 && <ScoreBars scores={scores} color={color} />}

      {facts.length > 0 && (
        <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {facts.map(([k, v]) => (
            <div key={k} className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-3">
              <dt className="text-xs text-white/45">{humanize(k)}</dt>
              <dd className="mt-1 break-words text-sm text-white">
                <Scalar value={v} />
              </dd>
            </div>
          ))}
        </dl>
      )}

      {prose.map(([k, v]) => (
        <div key={k}>
          <Label>{humanize(k)}</Label>
          <p className="whitespace-pre-line text-sm leading-relaxed text-white/75">{v}</p>
        </div>
      ))}

      {rest.map(([k, v]) => (
        <div key={k} className={depth === 0 ? 'rounded-2xl border border-white/[0.06] bg-white/[0.025] p-5' : ''}>
          {depth === 0 ? <h3 className="mb-4 text-sm font-medium text-white">{humanize(k)}</h3> : <Label>{humanize(k)}</Label>}
          <Value value={v} color={color} depth={depth + 1} />
        </div>
      ))}
    </div>
  );
}

function Value({ value, color, depth }: { value: unknown; color: string; depth: number }) {
  if (Array.isArray(value)) {
    if (value.every((x) => typeof x === 'string')) {
      const items = value as string[];
      return items.every((s) => s.length <= 60) ? (
        <TagList items={items} color={color} max={10} />
      ) : (
        <ul className="space-y-1.5">
          {items.map((s, i) => (
            <li key={i} className="flex gap-2 text-sm leading-relaxed text-white/75">
              <span className="mt-2 h-1 w-1 shrink-0 rounded-full" style={{ background: color }} />
              {s}
            </li>
          ))}
        </ul>
      );
    }
    return (
      <div className="grid gap-3 md:grid-cols-2">
        {value.map((item, i) => (
          <div key={i} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
            {isObj(item) ? <ObjectView data={item} color={color} depth={depth + 1} /> : <Scalar value={item} />}
          </div>
        ))}
      </div>
    );
  }
  if (isObj(value)) {
    if (isScoreMap(value)) return <ScoreBars scores={Object.entries(value) as [string, number][]} color={color} />;
    return <ObjectView data={value} color={color} depth={depth} />;
  }
  return (
    <p className="text-sm text-white/75">
      <Scalar value={value} />
    </p>
  );
}

export default function GenericCrew({ data, label, color }: { data: unknown; label: string; color: string }) {
  if (!isObj(data)) return <Empty what={label} />;
  const confidence = typeof data.confidence_score === 'number' ? toPercent(data.confidence_score, 'confidence_score') : null;
  return (
    <div className="space-y-5">
      {confidence != null && <p className="text-xs text-white/45">Model confidence: {Math.round(confidence)}%</p>}
      <ObjectView data={data} color={color} depth={0} />
    </div>
  );
}
