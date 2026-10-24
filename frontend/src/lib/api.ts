// ============================================================
// Startup Igniter — API client. Every call carries the Supabase access token.
// ============================================================

import { supabase } from './supabase';
import type {
  AnalysisDetail,
  BillingMe,
  ChatMessage,
  Experiment,
  Idea,
  IdeaDetail,
  IdeaListItem,
  IntegrationInfo,
  IntegrationProvider,
  Payment,
  PushedIssue,
  StreamEvent,
} from './types';

export const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:47000').replace(/\/$/, '');
const V1 = `${BASE_URL}/api/v1`;

/** Thrown for 402 responses so the UI can show an upgrade prompt instead of a generic error. */
export class PaywallError extends Error {
  constructor(
    message: string,
    readonly feature: string,
  ) {
    super(message);
    this.name = 'PaywallError';
  }
}

async function authHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function toError(res: Response): Promise<Error> {
  // Read as text first: a gateway error page is not JSON and would otherwise surface as a SyntaxError.
  const raw = await res.text().catch(() => '');
  let message = `HTTP ${res.status}`;
  try {
    const detail = (raw ? JSON.parse(raw) : null)?.detail;
    if (res.status === 402 && detail?.code === 'upgrade_required') return new PaywallError(detail.message, detail.feature);
    if (Array.isArray(detail)) message = detail.map((d: { msg?: string }) => d?.msg ?? JSON.stringify(d)).join('; ');
    else if (typeof detail === 'string') message = detail;
  } catch {
    if (raw) message = raw.slice(0, 300);
  }
  return new Error(message);
}

async function api<T>(path: string, init: RequestInit & { json?: unknown } = {}): Promise<T> {
  const { json, headers, ...rest } = init;
  const res = await fetch(`${V1}${path}`, {
    ...rest,
    headers: { ...(json !== undefined ? { 'Content-Type': 'application/json' } : {}), ...(await authHeaders()), ...headers },
    body: json !== undefined ? JSON.stringify(json) : rest.body,
  });
  if (!res.ok) throw await toError(res);
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

/** Read an NDJSON response, calling `onLine` per parsed object. Resolves when the stream ends. */
async function readNdjson<T>(res: Response, onLine: (obj: T) => void): Promise<void> {
  if (!res.ok || !res.body) throw await toError(res);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? ''; // the last piece may be a partial line
    for (const line of lines) if (line.trim()) onLine(JSON.parse(line) as T);
  }
}

// ─── Ideas ────────────────────────────────────────────────────

export const listIdeas = (archived = false) => api<IdeaListItem[]>(`/ideas?archived=${archived}`);
export const createIdea = (body: { idea_text: string; title?: string; github_repo?: string }) =>
  api<Idea>('/ideas', { method: 'POST', json: body });
export const getIdea = (id: string) => api<IdeaDetail>(`/ideas/${id}`);
export const updateIdea = (id: string, body: Partial<Pick<Idea, 'title' | 'idea_text' | 'archived' | 'github_repo'>>) =>
  api<Idea>(`/ideas/${id}`, { method: 'PATCH', json: body });
export const deleteIdea = (id: string) => api<void>(`/ideas/${id}`, { method: 'DELETE' });

// ─── Analyses ─────────────────────────────────────────────────

export const startAnalysis = (ideaId: string) =>
  api<{ analysis_id: string; version?: number; already_running?: boolean }>(`/ideas/${ideaId}/analyses`, { method: 'POST' });
export const getAnalysis = (id: string) => api<AnalysisDetail>(`/analyses/${id}`);
export const cancelAnalysis = (id: string) => api<{ cancelling: boolean }>(`/analyses/${id}/cancel`, { method: 'POST' });

/** Follow a run's progress. Replays what already happened, then goes live; safe to reconnect. */
export async function streamAnalysis(id: string, onEvent: (e: StreamEvent) => void, signal?: AbortSignal): Promise<void> {
  const res = await fetch(`${V1}/analyses/${id}/events`, { headers: await authHeaders(), signal });
  await readNdjson<StreamEvent>(res, onEvent);
}

/** Download the full report (PDF or Markdown) through the authenticated API. */
export async function downloadReport(id: string, format: 'pdf' | 'md', filename: string): Promise<void> {
  const res = await fetch(`${V1}/analyses/${id}/export?format=${format}`, { headers: await authHeaders() });
  if (!res.ok) throw await toError(res);
  const url = URL.createObjectURL(await res.blob());
  const a = Object.assign(document.createElement('a'), { href: url, download: `${filename}.${format}` });
  a.click();
  URL.revokeObjectURL(url);
}

export interface Rescan {
  since_version: number;
  new_repos: { full_name: string; url: string; description: string; stars: number }[];
  star_changes: { full_name: string; url: string; from: number; to: number }[];
  hn_total_before: number | null;
  hn_total_now: number;
  hn_recent: { title: string; url: string; points: number }[];
}
export const rescanIdea = (ideaId: string) => api<Rescan>(`/ideas/${ideaId}/rescan`, { method: 'POST' });

// ─── Experiments ──────────────────────────────────────────────

export const listExperiments = (ideaId: string) => api<Experiment[]>(`/ideas/${ideaId}/experiments`);
export const seedExperiments = (ideaId: string) => api<Experiment[]>(`/ideas/${ideaId}/experiments/seed`, { method: 'POST' });
export const addExperiment = (ideaId: string, body: { hypothesis: string; metric?: string }) =>
  api<Experiment>(`/ideas/${ideaId}/experiments`, { method: 'POST', json: body });
export const updateExperiment = (id: string, body: Partial<Pick<Experiment, 'status' | 'notes' | 'hypothesis' | 'metric'>>) =>
  api<Experiment>(`/experiments/${id}`, { method: 'PATCH', json: body });
export const deleteExperiment = (id: string) => api<void>(`/experiments/${id}`, { method: 'DELETE' });

// ─── Chat ─────────────────────────────────────────────────────

export const chatHistory = (ideaId: string) => api<ChatMessage[]>(`/ideas/${ideaId}/chat`);

export async function sendChat(
  ideaId: string,
  message: string,
  handlers: { onDelta: (text: string) => void; onMessage: (m: ChatMessage) => void },
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${V1}/ideas/${ideaId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(await authHeaders()) },
    body: JSON.stringify({ message }),
    signal,
  });
  await readNdjson<{ type: string; text?: string; message?: ChatMessage; error?: string }>(res, (e) => {
    if (e.type === 'delta' && e.text) handlers.onDelta(e.text);
    else if (e.type === 'message' && e.message) handlers.onMessage(e.message);
    else if (e.type === 'error') throw new Error(e.error);
  });
}

export const decideProposal = (messageId: string, action: 'accept' | 'dismiss') =>
  api<{ message: ChatMessage; idea: Pick<Idea, 'id' | 'title' | 'idea_text'> }>(`/chat/messages/${messageId}/proposal`, {
    method: 'POST',
    json: { action },
  });

// ─── Billing ──────────────────────────────────────────────────

export const billingMe = () => api<BillingMe>('/billing/me');
export const billingPayments = () => api<Payment[]>('/billing/payments');
export const createReportOrder = (analysisId: string) =>
  api<{ order_id: string; amount: number; currency: string; key_id: string }>('/billing/report-order', {
    method: 'POST',
    json: { analysis_id: analysisId },
  });
export const createSubscription = () =>
  api<{ subscription_id: string; key_id: string; amount: number; currency: string }>('/billing/subscribe', { method: 'POST' });
export const verifyPayment = (body: {
  razorpay_payment_id: string;
  razorpay_signature: string;
  razorpay_order_id?: string;
  razorpay_subscription_id?: string;
}) => api<{ ok: boolean; plan: 'free' | 'pro' }>('/billing/verify', { method: 'POST', json: body });
export const cancelSubscription = () => api<{ ok: boolean; pro_until: string | null }>('/billing/cancel', { method: 'POST' });
export const devActivate = (body: { kind: 'report' | 'pro'; analysis_id?: string }) =>
  api<{ ok: boolean }>('/billing/dev-activate', { method: 'POST', json: body });

// ─── Integrations ─────────────────────────────────────────────

export const listIntegrations = () => api<IntegrationInfo[]>('/integrations');
export const connectIntegration = (provider: IntegrationProvider, body: { token: string; label?: string; config?: Record<string, string> }) =>
  api<{ provider: string; label: string | null }>(`/integrations/${provider}`, { method: 'PUT', json: body });
export const disconnectIntegration = (provider: IntegrationProvider) => api<void>(`/integrations/${provider}`, { method: 'DELETE' });
export const pushGithub = (analysisId: string, body: { repo?: string; dry_run: boolean }) =>
  api<{ dry_run: boolean; repo: string; count?: number; issues?: PushedIssue[]; created?: { title: string; url: string }[]; failed?: { title: string; status: number }[] }>(
    `/analyses/${analysisId}/push/github`,
    { method: 'POST', json: body },
  );
export const pushMessage = (analysisId: string, provider: 'slack' | 'webhook' | 'notion') =>
  api<{ ok: boolean }>(`/analyses/${analysisId}/push/${provider}`, { method: 'POST' });

// ─── Health ───────────────────────────────────────────────────

export async function checkHealth(): Promise<boolean> {
  try {
    return (await fetch(`${BASE_URL}/health`)).ok;
  } catch {
    return false;
  }
}
