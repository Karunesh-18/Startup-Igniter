// Helpers shared by the analysis timeline and the results report:
// crew-key ↔ crew metadata, score normalisation, and result persistence.

import { CREWS, type Crew } from '@/data/crews';
import type { AnalysisResult, KnownCrewKey } from './types';

/** Result key for each crew, in pipeline order (index i ↔ CREWS[i]). Provisional on the backend side. */
export const CREW_KEYS: KnownCrewKey[] = [
  'idea_validation',
  'market_research',
  'research_patent',
  'feasibility',
  'business_planning',
  'product_development',
  'legal_compliance',
  'branding_marketing',
  'funding',
  'growth_scaling',
  'community',
  'reporting',
];

export interface CrewMeta {
  key: string;
  label: string;
  color: string;
  crew?: Crew;
}

const humanize = (s: string) => s.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase());

/** Metadata for a crew key; unknown keys get a humanised label and a neutral colour. */
export function crewMeta(key: string, label?: string): CrewMeta {
  const i = CREW_KEYS.indexOf(key as KnownCrewKey);
  const crew = i >= 0 ? CREWS[i] : undefined;
  return { key, label: crew?.name ?? label ?? humanize(key), color: crew?.color ?? '#94a3b8', crew };
}

/** Crew key for a CREWS id (1-based). */
export const crewKeyForId = (id: number) => CREW_KEYS[id - 1];

/**
 * Normalise a score to 0-100. The schemas mix scales: confidence is 0-1,
 * crews 1-3 score 0-10, crews 4-12 score 0-100.
 * ponytail: scale is guessed from magnitude; a genuine 0-100 score of ≤10 reads ×10. Send explicit scales from the backend if that bites.
 */
export function toPercent(v: number, key = ''): number {
  const scaled = key.includes('confidence') && v <= 1 ? v * 100 : v <= 10 ? v * 10 : v;
  return Math.max(0, Math.min(100, scaled));
}

type Obj = Record<string, unknown>;
const isObj = (v: unknown): v is Obj => typeof v === 'object' && v !== null && !Array.isArray(v);

/**
 * One headline 0-100 score for a crew result: an `overall_*` score if present,
 * else the mean of its top-level `*_score` fields, else its confidence.
 */
export function crewScore(result: unknown): number | null {
  if (!isObj(result)) return null;
  const entries = Object.entries(result).filter(
    (e): e is [string, number] => typeof e[1] === 'number' && e[0].endsWith('_score'),
  );
  const overall = entries.find(([k]) => k.startsWith('overall_'));
  if (overall) return toPercent(overall[1], overall[0]);
  const scores = entries.filter(([k]) => k !== 'confidence_score');
  if (scores.length) return scores.reduce((a, [k, v]) => a + toPercent(v, k), 0) / scores.length;
  const conf = entries.find(([k]) => k === 'confidence_score');
  return conf ? toPercent(conf[1], conf[0]) : null;
}

const SUMMARY_KEYS = ['executive_summary', 'overall_summary', 'summary', 'brand_positioning', 'architecture_overview', 'community_feedback_summary'];

/** A one-paragraph summary string from a crew result, for previews. */
export function crewSummary(result: unknown): string | null {
  if (!isObj(result)) return null;
  for (const k of SUMMARY_KEYS) if (typeof result[k] === 'string' && result[k]) return result[k] as string;
  for (const v of Object.values(result)) {
    if (isObj(v)) {
      const nested = crewSummary(v);
      if (nested) return nested;
    }
  }
  return null;
}

/** "$4.2B", "USD 350 million", "12.5bn" → number of dollars, or null if unparseable. */
export function parseMoney(s: string | undefined): number | null {
  if (!s) return null;
  const m = s.replace(/,/g, '').match(/(\d+(?:\.\d+)?)\s*(trillion|billion|million|thousand|tn|bn|mn|[tbmk])?\b/i);
  if (!m) return null;
  const mult: Record<string, number> = { t: 1e12, tn: 1e12, trillion: 1e12, b: 1e9, bn: 1e9, billion: 1e9, m: 1e6, mn: 1e6, million: 1e6, k: 1e3, thousand: 1e3 };
  return parseFloat(m[1]) * (m[2] ? mult[m[2].toLowerCase()] : 1);
}

// ─── Persistence (so /results/:id survives a refresh) ─────────

const storageKey = (id: string) => `si:result:${id}`;

export function saveResult(result: AnalysisResult) {
  try {
    sessionStorage.setItem(storageKey(result.project_id), JSON.stringify(result));
  } catch {
    // quota exceeded or storage disabled — the route falls back to the server cache
  }
}

export function loadResult(id: string): AnalysisResult | null {
  try {
    const raw = sessionStorage.getItem(storageKey(id));
    return raw ? (JSON.parse(raw) as AnalysisResult) : null;
  } catch {
    return null;
  }
}
