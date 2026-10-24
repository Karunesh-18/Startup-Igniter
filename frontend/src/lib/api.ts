// ============================================================
// Startup Igniter AI — API Client
// All backend communication goes through this module.
// ============================================================

import type { AnalysisResult, StreamEvent } from './types';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:47000').replace(/\/$/, '');

// ─── Core fetch wrapper ───────────────────────────────────────

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    // Spread `options` FIRST: a caller-supplied `options.headers` used to be
    // applied after this object's own `headers` key, silently overwriting
    // (not merging into) it and dropping Content-Type whenever a caller
    // passed custom headers. Merging here, last, fixes that.
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  });

  if (!res.ok) {
    // Read the error body as text first — a non-JSON error body (a 502/504
    // gateway page, an empty response) used to make `res.json()` throw a raw
    // `SyntaxError: Unexpected token '<'` that surfaced verbatim to the user
    // instead of a readable message.
    const raw = await res.text();
    let message = `HTTP ${res.status}`;
    try {
      const data = raw ? JSON.parse(raw) : null;
      // FastAPI 422 validation errors return `detail` as an array of
      // objects, not a string — stringifying it avoids "[object Object]".
      const detail = data?.detail ?? data?.error;
      if (Array.isArray(detail)) {
        message = detail.map((d: { msg?: string }) => d?.msg ?? JSON.stringify(d)).join('; ');
      } else if (detail) {
        message = detail;
      }
    } catch {
      if (raw) message = raw.slice(0, 300);
    }
    throw new Error(message);
  }

  return (await res.json()) as T;
}

// ─── Analysis endpoints ───────────────────────────────────────

export interface RunAnalysisPayload {
  idea_text: string;
  project_id?: string;
  mock_mode?: boolean;
}

/**
 * POST /api/v1/analysis/run
 * Submits a startup idea and runs all 3 AI crews (Crews 1-3).
 * This is a synchronous long-running call (4-8 min live, instant in mock mode).
 * Prefer `runAnalysisStream` for anything that shows progress to a user.
 */
export async function runAnalysis(payload: RunAnalysisPayload): Promise<AnalysisResult> {
  return apiFetch<AnalysisResult>('/api/v1/analysis/run', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * POST /api/v1/analysis/run/stream
 * Same pipeline as `runAnalysis`, but calls `onEvent` once per crew as it
 * completes (real backend-driven progress, not a cosmetic timer) and
 * resolves with the final result. Pass `signal` (from an AbortController)
 * to let the user cancel a long-running analysis — the backend stops
 * before starting the next crew when it sees the client disconnect.
 */
export async function runAnalysisStream(
  payload: RunAnalysisPayload,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<AnalysisResult> {
  const res = await fetch(`${BASE_URL}/api/v1/analysis/run/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  });

  if (!res.ok || !res.body) {
    const raw = await res.text().catch(() => '');
    throw new Error(raw || `HTTP ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let finalResult: AnalysisResult | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? ''; // last element may be an incomplete line — keep it for the next chunk

    for (const line of lines) {
      if (!line.trim()) continue;
      const event = JSON.parse(line) as StreamEvent;
      onEvent(event);
      if (event.type === 'result') finalResult = event.result;
      if (event.type === 'error') throw new Error(event.error);
    }
  }

  if (!finalResult) {
    throw new Error('Analysis stream ended without a result.');
  }
  return finalResult;
}

/**
 * GET /api/v1/analysis/{projectId}
 * Retrieve a previously completed analysis from the server cache.
 */
export async function getAnalysis(projectId: string): Promise<AnalysisResult> {
  return apiFetch<AnalysisResult>(`/api/v1/analysis/${projectId}`);
}

// ─── Health check ─────────────────────────────────────────────

export async function checkHealth(): Promise<boolean> {
  try {
    await apiFetch<{ status: string }>('/health');
    return true;
  } catch {
    return false;
  }
}
