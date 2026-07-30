// ============================================================
// Startup Igniter AI — API Client
// All backend communication goes through this module.
// ============================================================

import type { AnalysisResult } from './types';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '');

// ─── Core fetch wrapper ───────────────────────────────────────

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) {
    const message = data?.detail ?? data?.error ?? `HTTP ${res.status}`;
    throw new Error(message);
  }
  return data as T;
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
 */
export async function runAnalysis(payload: RunAnalysisPayload): Promise<AnalysisResult> {
  return apiFetch<AnalysisResult>('/api/v1/analysis/run', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
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
